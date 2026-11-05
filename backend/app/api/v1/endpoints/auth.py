"""Authentication and organization administration endpoints."""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.models.identity import (
    AuthSession,
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    RefreshToken,
    User,
)
from app.schemas.auth import (
    Credentials,
    ExistingUserInvitationAcceptance,
    InvitationAcceptance,
    InvitationRequest,
    InvitationResponse,
    OrganizationCreatedResponse,
    OrganizationRequest,
    TokenResponse,
)
from app.security.auth import (
    AuthenticatedUser,
    OrganizationContext,
    Permission,
    Role,
    client_identity,
    create_access_token,
    email_lookup_hash,
    enforce_rate_limit,
    get_current_user,
    hash_password,
    hash_refresh_token,
    require_permission,
    require_platform_admin,
    verify_csrf,
    verify_password,
)

public_router = APIRouter()
protected_router = APIRouter()

_REFRESH_COOKIE = "acis_refresh_token"
_CSRF_COOKIE = "acis_csrf_token"


def _set_auth_cookies(response: Response, refresh_token: str) -> str:
    settings = get_settings()
    csrf_token = secrets.token_urlsafe(32)
    cookie_options = {
        "secure": settings.auth_cookie_secure,
        "samesite": "strict",
        "path": "/api/v1/auth",
    }
    response.set_cookie(
        _REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        max_age=settings.auth_refresh_token_days * 24 * 60 * 60,
        **cookie_options,
    )
    response.set_cookie(
        _CSRF_COOKIE,
        csrf_token,
        httponly=False,
        max_age=settings.auth_refresh_token_days * 24 * 60 * 60,
        **cookie_options,
    )
    return csrf_token


def _clear_auth_cookies(response: Response) -> None:
    secure = get_settings().auth_cookie_secure
    response.delete_cookie(
        _REFRESH_COOKIE,
        path="/api/v1/auth",
        httponly=True,
        secure=secure,
        samesite="strict",
    )
    response.delete_cookie(
        _CSRF_COOKIE,
        path="/api/v1/auth",
        secure=secure,
        samesite="strict",
    )


async def _create_session(
    session: AsyncSession, user_id: str
) -> tuple[str, str, int]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    session_id = str(uuid4())
    expires_at = now + timedelta(days=settings.auth_refresh_token_days)
    session.add(
        AuthSession(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
        )
    )
    refresh_token = secrets.token_urlsafe(48)
    session.add(
        RefreshToken(
            token_hash=hash_refresh_token(refresh_token),
            session_id=session_id,
            expires_at=expires_at,
        )
    )
    access_token = create_access_token(user_id, session_id)
    await session.flush()
    return access_token, refresh_token, settings.auth_access_token_minutes * 60


def _check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin or origin not in get_settings().backend_cors_origins:
        raise HTTPException(status_code=403, detail="Invalid request origin.")


@public_router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: Credentials,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    _check_origin(request)
    await enforce_rate_limit(
        request,
        session,
        identity=f"login:{client_identity(request)}",
        limit=get_settings().auth_rate_limit_requests,
    )
    email_hash = email_lookup_hash(body.email)
    await enforce_rate_limit(
        request,
        session,
        identity=f"login-account:{email_hash}",
        limit=get_settings().auth_rate_limit_requests,
    )
    user = (
        await session.execute(
            select(User).where(
                User.email_lookup_hash == email_hash
            )
        )
    ).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(
        user.password_hash, body.password
    ):
        await session.rollback()
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    request.state.actor_user_id = user.user_id
    access_token, refresh_token, expires_in = await _create_session(
        session, user.user_id
    )
    await session.commit()
    csrf_token = _set_auth_cookies(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        csrf_token=csrf_token,
    )


@public_router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    csrf_cookie: str | None = Cookie(default=None, alias=_CSRF_COOKIE),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    verify_csrf(request, csrf_cookie, csrf_header)
    await enforce_rate_limit(
        request,
        session,
        identity=f"refresh:{client_identity(request)}",
        limit=get_settings().auth_rate_limit_requests,
    )
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is required.")
    token_hash = hash_refresh_token(refresh_token)
    record = (
        await session.execute(
            select(RefreshToken, AuthSession, User)
            .join(AuthSession, AuthSession.session_id == RefreshToken.session_id)
            .join(User, User.user_id == AuthSession.user_id)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update(of=RefreshToken)
        )
    ).first()
    if record is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    old_token, auth_session, user = record
    now = datetime.now(timezone.utc)
    if (
        old_token.used_at is not None
        or old_token.revoked_at is not None
        or old_token.expires_at <= now
        or auth_session.revoked_at is not None
        or auth_session.expires_at <= now
    ):
        auth_session.revoked_at = now
        await session.execute(
            RefreshToken.__table__.update()
            .where(RefreshToken.session_id == auth_session.session_id)
            .values(revoked_at=now)
        )
        await session.commit()
        raise HTTPException(status_code=401, detail="Refresh token is invalid or revoked.")
    if not user.is_active:
        auth_session.revoked_at = now
        await session.execute(
            RefreshToken.__table__.update()
            .where(RefreshToken.session_id == auth_session.session_id)
            .values(revoked_at=now)
        )
        await session.commit()
        raise HTTPException(status_code=401, detail="User account is inactive.")

    next_refresh = secrets.token_urlsafe(48)
    next_hash = hash_refresh_token(next_refresh)
    old_token.used_at = now
    old_token.replaced_by_hash = next_hash
    session.add(
        RefreshToken(
            token_hash=next_hash,
            session_id=auth_session.session_id,
            expires_at=auth_session.expires_at,
        )
    )
    access_token = create_access_token(user.user_id, auth_session.session_id)
    await session.commit()
    csrf_token = _set_auth_cookies(response, next_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=get_settings().auth_access_token_minutes * 60,
        csrf_token=csrf_token,
    )


@public_router.post("/auth/invitations/accept", status_code=201)
async def accept_invitation(
    body: InvitationAcceptance,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    await enforce_rate_limit(
        request,
        session,
        identity=f"invite:{client_identity(request)}",
        limit=get_settings().auth_rate_limit_requests,
    )
    now = datetime.now(timezone.utc)
    invitation = (
        await session.execute(
            select(OrganizationInvitation)
            .where(OrganizationInvitation.token_hash == hash_refresh_token(body.token))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if (
        invitation is None
        or invitation.email_lookup_hash != email_lookup_hash(body.email)
        or invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or invitation.expires_at <= now
    ):
        raise HTTPException(status_code=400, detail="Invitation is invalid or expired.")
    existing = (
        await session.execute(
            select(User).where(
                User.email_lookup_hash == email_lookup_hash(body.email)
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="An account already exists; sign in to accept this invitation.",
        )
    try:
        role = Role(invitation.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invitation role is invalid.") from exc
    user = User(
        user_id=str(uuid4()),
        email=body.email,
        email_lookup_hash=email_lookup_hash(body.email),
        password_hash=hash_password(body.password),
    )
    session.add(user)
    session.add(
        OrganizationMembership(
            user_id=user.user_id,
            organization_id=invitation.organization_id,
            role=role.value,
        )
    )
    invitation.accepted_at = now
    request.state.actor_user_id = user.user_id
    request.state.organization_id = invitation.organization_id
    await session.commit()
    return {"status": "accepted"}


@protected_router.post("/auth/invitations/accept-existing")
async def accept_invitation_existing(
    body: ExistingUserInvitationAcceptance,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    invitation = (
        await session.execute(
            select(OrganizationInvitation)
            .where(OrganizationInvitation.token_hash == hash_refresh_token(body.token))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if (
        invitation is None
        or invitation.email_lookup_hash != email_lookup_hash(user.email)
        or invitation.accepted_at is not None
        or invitation.revoked_at is not None
        or invitation.expires_at <= now
    ):
        raise HTTPException(status_code=400, detail="Invitation is invalid or expired.")
    try:
        role = Role(invitation.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invitation role is invalid.") from exc
    existing_membership = await session.get(
        OrganizationMembership, (user.user_id, invitation.organization_id)
    )
    if existing_membership is not None:
        raise HTTPException(status_code=409, detail="User is already a member.")
    session.add(
        OrganizationMembership(
            user_id=user.user_id,
            organization_id=invitation.organization_id,
            role=role.value,
        )
    )
    invitation.accepted_at = now
    await session.commit()
    return {"status": "accepted"}


@protected_router.post(
    "/organizations",
    response_model=OrganizationCreatedResponse,
    status_code=201,
)
async def create_organization(
    body: OrganizationRequest,
    user: AuthenticatedUser = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationCreatedResponse:
    if await session.get(Organization, body.organization_id) is not None:
        raise HTTPException(status_code=409, detail="Organization already exists.")
    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session.add(
        Organization(
            organization_id=body.organization_id,
            name=body.name,
        )
    )
    session.add(
        OrganizationInvitation(
            token_hash=hash_refresh_token(raw_token),
            organization_id=body.organization_id,
            email=body.owner_email,
            email_lookup_hash=email_lookup_hash(body.owner_email),
            role=Role.OWNER.value,
            created_by=user.user_id,
            expires_at=expires_at,
        )
    )
    await session.commit()
    return OrganizationCreatedResponse(
        organization_id=body.organization_id,
        name=body.name,
        owner_invitation=InvitationResponse(
            organization_id=body.organization_id,
            email=body.owner_email,
            role=Role.OWNER,
            token=raw_token,
            expires_at=expires_at.isoformat(),
        ),
    )


@protected_router.post(
    "/organizations/{organization_id}/invitations",
    response_model=InvitationResponse,
    status_code=201,
)
async def create_platform_invitation(
    organization_id: str,
    body: InvitationRequest,
    user: AuthenticatedUser = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_db_session),
) -> InvitationResponse:
    if body.role == Role.OWNER:
        raise HTTPException(status_code=400, detail="Owner invitations are not supported.")
    if await session.get(Organization, organization_id) is None:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return await _create_invitation(
        organization_id=organization_id,
        body=body,
        creator_id=user.user_id,
        session=session,
    )


@protected_router.post("/auth/logout", status_code=204)
async def logout(
    response: Response,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    now = datetime.now(timezone.utc)
    auth_session = await session.get(AuthSession, user.session_id)
    if auth_session is not None:
        auth_session.revoked_at = now
        await session.execute(
            RefreshToken.__table__.update()
            .where(RefreshToken.session_id == user.session_id)
            .values(revoked_at=now)
        )
        await session.commit()
    _clear_auth_cookies(response)
    response.status_code = 204
    return response


@protected_router.get("/auth/organizations")
async def list_user_organizations(
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict[str, str]]:
    rows = (
        await session.execute(
            select(
                Organization.organization_id,
                Organization.name,
                OrganizationMembership.role,
            )
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Organization.organization_id,
            )
            .where(
                OrganizationMembership.user_id == user.user_id,
                OrganizationMembership.is_active.is_(True),
                Organization.is_active.is_(True),
            )
            .order_by(Organization.name)
        )
    ).all()
    return [
        {"organization_id": row[0], "name": row[1], "role": row[2]}
        for row in rows
    ]


@protected_router.post(
    "/auth/invitations",
    response_model=InvitationResponse,
    status_code=201,
)
async def create_organization_invitation(
    body: InvitationRequest,
    context: OrganizationContext = Depends(
        require_permission(Permission.MANAGE_USERS)
    ),
    session: AsyncSession = Depends(get_db_session),
) -> InvitationResponse:
    if body.role == Role.OWNER:
        raise HTTPException(status_code=400, detail="Owner invitations are not supported.")
    return await _create_invitation(
        organization_id=context.organization_id,
        body=body,
        creator_id=context.user.user_id,
        session=session,
    )


async def _create_invitation(
    *,
    organization_id: str,
    body: InvitationRequest,
    creator_id: str,
    session: AsyncSession,
) -> InvitationResponse:
    now = datetime.now(timezone.utc)
    raw_token = secrets.token_urlsafe(48)
    expires_at = now + timedelta(days=7)
    session.add(
        OrganizationInvitation(
            token_hash=hash_refresh_token(raw_token),
            organization_id=organization_id,
            email=body.email,
            email_lookup_hash=email_lookup_hash(body.email),
            role=body.role.value,
            created_by=creator_id,
            expires_at=expires_at,
        )
    )
    await session.commit()
    return InvitationResponse(
        organization_id=organization_id,
        email=body.email,
        role=body.role,
        token=raw_token,
        expires_at=expires_at.isoformat(),
    )


__all__ = ["protected_router", "public_router"]
