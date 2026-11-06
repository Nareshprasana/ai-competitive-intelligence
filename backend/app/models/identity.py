"""Authentication, organization, audit, and request-control models."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.security.crypto import EncryptedText


class Organization(Base):
    __tablename__ = "organizations"

    organization_id: Mapped[str] = mapped_column(sa.String(128), primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.true()
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    email: Mapped[str] = mapped_column(
        EncryptedText("users.email"), nullable=False
    )
    email_lookup_hash: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )
    password_hash: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.true()
    )
    is_platform_admin: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "email_lookup_hash", name="uq_users_email_lookup_hash"
        ),
    )


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    user_id: Mapped[str] = mapped_column(
        sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    organization_id: Mapped[str] = mapped_column(
        sa.ForeignKey("organizations.organization_id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.true()
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(back_populates="memberships")

    __table_args__ = (
        sa.Index("ix_organization_memberships_org_role", "organization_id", "role"),
    )


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    token_hash: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        sa.ForeignKey("organizations.organization_id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        EncryptedText("organization_invitations.email"), nullable=False
    )
    email_lookup_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    role: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    created_by: Mapped[str] = mapped_column(
        sa.ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    expires_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    accepted_at: Mapped[sa.DateTime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[sa.DateTime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    __table_args__ = (
        sa.Index("ix_organization_invitations_org", "organization_id"),
        sa.Index(
            "ix_organization_invitations_email_lookup",
            "organization_id",
            "email_lookup_hash",
        ),
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    session_id: Mapped[str] = mapped_column(sa.String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    expires_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[sa.DateTime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (sa.Index("ix_auth_sessions_user", "user_id"),)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        sa.ForeignKey("auth_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[sa.DateTime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    replaced_by_hash: Mapped[str | None] = mapped_column(
        sa.String(64), nullable=True
    )
    revoked_at: Mapped[sa.DateTime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    __table_args__ = (sa.Index("ix_refresh_tokens_session", "session_id"),)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(
        sa.BigInteger().with_variant(sa.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    actor_user_id: Mapped[str | None] = mapped_column(
        sa.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[str | None] = mapped_column(
        sa.ForeignKey("organizations.organization_id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    request_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(sa.String(16), nullable=False)
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    __table_args__ = (
        sa.Index("ix_audit_events_actor", "actor_user_id"),
        sa.Index("ix_audit_events_organization", "organization_id"),
        sa.Index("ix_audit_events_request", "request_id"),
        sa.Index("ix_audit_events_org_created", "organization_id", "created_at"),
    )


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"

    bucket_key: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    window_start: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False
    )
    request_count: Mapped[int] = mapped_column(sa.Integer, nullable=False)


__all__ = [
    "AuditEvent",
    "AuthSession",
    "Organization",
    "OrganizationInvitation",
    "OrganizationMembership",
    "RateLimitBucket",
    "RefreshToken",
    "User",
]
