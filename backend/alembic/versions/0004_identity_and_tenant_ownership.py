"""Identity, organization ownership, audit, and rate-limit tables.

Revision ID: 0004_identity_and_tenant_ownership
Revises: 0003_competitors
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_identity_and_tenant_ownership"
down_revision: Union[str, None] = "0003_competitors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("organization_id"),
    )

    bind = op.get_bind()
    existing_orgs = set()
    for table in ("researches", "company_profiles", "competitors"):
        existing_orgs.update(
            row[0]
            for row in bind.execute(
                sa.text(f"SELECT DISTINCT organization_id FROM {table}")
            )
        )
    bind.execute(
        sa.text(
            "UPDATE evidence_claims AS evidence "
            "SET organization_id = profiles.organization_id "
            "FROM company_profiles AS profiles "
            "WHERE evidence.company_profile_id = profiles.id"
        )
    )
    for organization_id in sorted(existing_orgs):
        bind.execute(
            sa.text(
                "INSERT INTO organizations (organization_id, name) "
                "VALUES (:organization_id, :name)"
            ),
            {"organization_id": organization_id, "name": organization_id},
        )

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("email_lookup_hash", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "is_platform_admin", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email_lookup_hash", name="uq_users_email_lookup_hash"),
    )
    op.create_table(
        "organization_memberships",
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.organization_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "organization_id"),
    )
    op.create_index(
        "ix_organization_memberships_org_role",
        "organization_memberships",
        ["organization_id", "role"],
    )
    op.create_table(
        "organization_invitations",
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("email_lookup_hash", sa.String(64), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.organization_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.user_id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index(
        "ix_organization_invitations_org",
        "organization_invitations",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_invitations_email_lookup",
        "organization_invitations",
        ["organization_id", "email_lookup_hash"],
    )
    op.create_table(
        "auth_sessions",
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("ix_auth_sessions_user", "auth_sessions", ["user_id"])
    op.create_table(
        "refresh_tokens",
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_hash", sa.String(64), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["auth_sessions.session_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_session", "refresh_tokens", ["session_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("actor_user_id", sa.String(36), nullable=True),
        sa.Column("organization_id", sa.String(128), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(128), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.user_id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.organization_id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_actor", "audit_events", ["actor_user_id"])
    op.create_index(
        "ix_audit_events_organization",
        "audit_events",
        ["organization_id"],
    )
    op.create_index("ix_audit_events_request", "audit_events", ["request_id"])
    op.create_index(
        "ix_audit_events_org_created",
        "audit_events",
        ["organization_id", "created_at"],
    )
    op.create_table(
        "rate_limit_buckets",
        sa.Column("bucket_key", sa.String(64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("bucket_key"),
    )

    op.create_foreign_key(
        "fk_researches_organization",
        "researches",
        "organizations",
        ["organization_id"],
        ["organization_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_company_profiles_organization",
        "company_profiles",
        "organizations",
        ["organization_id"],
        ["organization_id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_company_profiles_id_org",
        "company_profiles",
        ["id", "organization_id"],
    )
    op.create_unique_constraint(
        "uq_company_profiles_company_org",
        "company_profiles",
        ["company_id", "organization_id"],
    )
    op.drop_constraint(
        "evidence_claims_company_profile_id_fkey",
        "evidence_claims",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_evidence_claims_profile_owner",
        "evidence_claims",
        "company_profiles",
        ["company_profile_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_evidence_claims_organization",
        "evidence_claims",
        "organizations",
        ["organization_id"],
        ["organization_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_competitors_organization",
        "competitors",
        "organizations",
        ["organization_id"],
        ["organization_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_competitor_evidence_organization",
        "competitor_evidence",
        "organizations",
        ["organization_id"],
        ["organization_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_competitor_evidence_organization",
        "competitor_evidence",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_competitors_organization", "competitors", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_evidence_claims_organization", "evidence_claims", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_evidence_claims_profile_owner", "evidence_claims", type_="foreignkey"
    )
    op.create_foreign_key(
        "evidence_claims_company_profile_id_fkey",
        "evidence_claims",
        "company_profiles",
        ["company_profile_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "uq_company_profiles_company_org",
        "company_profiles",
        type_="unique",
    )
    op.drop_constraint(
        "uq_company_profiles_id_org", "company_profiles", type_="unique"
    )
    op.drop_constraint(
        "fk_company_profiles_organization",
        "company_profiles",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_researches_organization", "researches", type_="foreignkey"
    )

    op.drop_table("rate_limit_buckets")
    op.drop_index("ix_audit_events_org_created", table_name="audit_events")
    op.drop_index("ix_audit_events_request", table_name="audit_events")
    op.drop_index("ix_audit_events_organization", table_name="audit_events")
    op.drop_index("ix_audit_events_actor", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_refresh_tokens_session", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_auth_sessions_user", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index(
        "ix_organization_invitations_org", table_name="organization_invitations"
    )
    op.drop_index(
        "ix_organization_invitations_email_lookup",
        table_name="organization_invitations",
    )
    op.drop_table("organization_invitations")
    op.drop_index(
        "ix_organization_memberships_org_role",
        table_name="organization_memberships",
    )
    op.drop_table("organization_memberships")
    op.drop_table("users")
    op.drop_table("organizations")
