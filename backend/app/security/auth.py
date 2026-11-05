"""Authentication, tenant context, rate limiting, and centralized RBAC."""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import case, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import db, get_db_session
from app.models.identity import (
    AuthSession,
    Organization,
    OrganizationMembership,
    RateLimitBucket,
    RefreshToken,
    User,
)

password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
bearer_scheme = HTTPBearer(auto_error=False)


class Role(str, Enum):
    OWNER = "organization_owner"
    ADMIN = "organization_admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    MANAGE_USERS = "manage_users"
    MANAGE_ORGANIZATION = "manage_organization"
    CREATE_RESEARCH = "create_research"
    VIEW_RESEARCH = "view_research"
    DELETE_RESEARCH = "delete_research"
    MANAGE_COMPETITORS = "manage_competitors"
    MANAGE_EVIDENCE = "manage_evidence"
    VIEW_STRATEGY_REPORTS = "view_strategy_reports"
    MANAGE_CONFIGURATION = "manage_configuration"


_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(Permission),
    Role.ADMIN: frozenset(
        {
            Permission.MANAGE_USERS,
            Permission.CREATE_RESEARCH,
            Permission.VIEW_RESEARCH,
            Permission.DELETE_RESEARCH,
            Permission.MANAGE_COMPETITORS,
            Permission.MANAGE_EVIDENCE,
            Permission.VIEW_STRATEGY_REPORTS,
        }
    ),
    Role.ANALYST: frozenset(
        {
            Permission.CREATE_RESEARCH,
            Permission.VIEW_RESEARCH,
            Permission.MANAGE_COMPETITORS,
            Permission.MANAGE_EVIDENCE,
            Permission.VIEW_STRATEGY_REPORTS,
        }
    ),
    Role.VIEWER: frozenset(
        {Permission.VIEW_RESEARCH, Permission.VIEW_STRATEGY_REPORTS}
    ),
}


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str
    session_id: str
    is_platform_admin: bool


@dataclass(frozen=True)
class OrganizationContext:
    user: AuthenticatedUser
    organization_id: str
    role: Role


def hash_password(password: str) -> str:
    if len(password) < 12 or len(password) > 256:
        raise ValueError("Password must contain between 12 and 256 characters.")
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, TypeError):
        return False


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def email_lookup_hash(email: str) -> str:
    key = get_settings().auth_email_lookup_key.get_secret_value()
    if len(key) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )
    normalized = email.strip().lower().encode("utf-8")
    return hmac.new(key.encode("utf-8"), normalized, hashlib.sha256).hexdigest()


def create_access_token(user_id: str, session_id: str) -> str:
    settings = get_settings()
    signing_key = settings.auth_jwt_signing_key.get_secret_value()
    if len(signing_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "sid": session_id,
            "jti": uuid4().hex,
            "iat": now,
            "exp": now + timedelta(minutes=settings.auth_access_token_minutes),
            "iss": "acis",
            "aud": "acis-api",
        },
        signing_key,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict:
    signing_key = get_settings().auth_jwt_signing_key.get_secret_value()
    if len(signing_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )
    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["HS256"],
            issuer="acis",
            audience="acis-api",
            options={"require": ["sub", "sid", "jti", "iat", "exp"]},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if not isinstance(claims.get("sub"), str) or not isinstance(
        claims.get("sid"), str
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims


async def enforce_rate_limit(
    request: Request,
    session: AsyncSession,
    *,
    identity: str,
    limit: int,
) -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=settings.rate_limit_window_seconds)
    bucket_key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    statement = (
        insert(RateLimitBucket)
        .values(bucket_key=bucket_key, window_start=now, request_count=1)
        .on_conflict_do_update(
            index_elements=[RateLimitBucket.bucket_key],
            set_={
                "window_start": case(
                    (RateLimitBucket.window_start < window_start, now),
                    else_=RateLimitBucket.window_start,
                ),
                "request_count": case(
                    (RateLimitBucket.window_start < window_start, 1),
                    else_=RateLimitBucket.request_count + 1,
                ),
            },
        )
        .returning(RateLimitBucket.request_count)
    )
    count = (await session.execute(statement)).scalar_one()
    await session.commit()
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Request rate limit exceeded.",
            headers={"Retry-After": str(settings.rate_limit_window_seconds)},
        )


def client_identity(request: Request) -> str:
    # Do not trust X-Forwarded-For here; configure trusted proxy handling separately.
    return request.client.host if request.client else "unknown"


async def require_bearer_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> HTTPAuthorizationCredentials:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(require_bearer_credentials),
    session: AsyncSession = Depends(get_db_session),
) -> AuthenticatedUser:
    claims = decode_access_token(credentials.credentials)
    await enforce_rate_limit(
        request,
        session,
        identity=f"user:{claims['sub']}",
        limit=get_settings().api_rate_limit_requests,
    )
    row = (
        await session.execute(
            select(User, AuthSession)
            .join(AuthSession, AuthSession.user_id == User.user_id)
            .where(
                User.user_id == claims["sub"],
                AuthSession.session_id == claims["sid"],
                User.is_active.is_(True),
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > datetime.now(timezone.utc),
            )
        )
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user, auth_session = row
    request.state.actor_user_id = user.user_id
    return AuthenticatedUser(
        user_id=user.user_id,
        email=user.email,
        session_id=auth_session.session_id,
        is_platform_admin=user.is_platform_admin,
    )


async def get_organization_context(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
    organization_id: str = Header(alias="X-Organization-ID", min_length=1, max_length=128),
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationContext:
    row = (
        await session.execute(
            select(OrganizationMembership.role)
            .join(
                Organization,
                Organization.organization_id == OrganizationMembership.organization_id,
            )
            .where(
                OrganizationMembership.user_id == user.user_id,
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.is_active.is_(True),
                Organization.is_active.is_(True),
            )
        )
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization membership is required.",
        )
    try:
        role = Role(row[0])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization role is invalid.",
        ) from exc
    request.state.organization_id = organization_id
    return OrganizationContext(user, organization_id, role)


def require_permission(
    permission: Permission,
) -> Callable[..., OrganizationContext]:
    async def dependency(
        context: OrganizationContext = Depends(get_organization_context),
    ) -> OrganizationContext:
        if permission not in _ROLE_PERMISSIONS[context.role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient organization permissions.",
            )
        return context

    return dependency


async def require_platform_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator permission is required.",
        )
    return user


def verify_csrf(request: Request, csrf_cookie: str | None, csrf_header: str | None) -> None:
    settings = get_settings()
    origin = request.headers.get("origin")
    if not origin or origin not in settings.backend_cors_origins:
        raise HTTPException(status_code=403, detail="Invalid request origin.")
    if (
        not csrf_cookie
        or not csrf_header
        or not hmac.compare_digest(csrf_cookie, csrf_header)
    ):
        raise HTTPException(status_code=403, detail="CSRF validation failed.")


__all__ = [
    "AuthenticatedUser",
    "OrganizationContext",
    "Permission",
    "Role",
    "create_access_token",
    "decode_access_token",
    "email_lookup_hash",
    "enforce_rate_limit",
    "get_current_user",
    "get_organization_context",
    "hash_password",
    "hash_refresh_token",
    "password_hasher",
    "require_permission",
    "require_platform_admin",
    "require_bearer_credentials",
    "verify_csrf",
    "verify_password",
]
