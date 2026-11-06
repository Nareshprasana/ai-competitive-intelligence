"""Seed a test user and organization in acis_test_db for real browser E2E auth tests."""

import asyncio
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Add parent directory to path so app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.identity import Organization, OrganizationMembership, User
from app.security.auth import email_lookup_hash, hash_password

TEST_DATABASE_URL = os.getenv("ACIS_TEST_DATABASE_URL") or "postgresql+asyncpg://acis_app:acis_dev_password@127.0.0.1:5432/acis_test_db"

TEST_USER_EMAIL = "analyst@real-auth-test.com"
TEST_USER_PASSWORD = "Password123!"
TEST_ORG_ID = "org-real-auth-test"
TEST_ORG_NAME = "Real Auth Test Corp"


async def seed():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with AsyncSession(engine) as session:
        # Check or create organization
        org = await session.get(Organization, TEST_ORG_ID)
        if not org:
            org = Organization(
                organization_id=TEST_ORG_ID,
                name=TEST_ORG_NAME,
                is_active=True,
            )
            session.add(org)

        # Check or create user
        lookup_hash = email_lookup_hash(TEST_USER_EMAIL)
        res = await session.execute(select(User).where(User.email_lookup_hash == lookup_hash))
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                user_id="user-real-auth-test",
                email=TEST_USER_EMAIL,
                email_lookup_hash=lookup_hash,
                password_hash=hash_password(TEST_USER_PASSWORD),
                is_active=True,
            )
            session.add(user)
        else:
            user.password_hash = hash_password(TEST_USER_PASSWORD)
            user.is_active = True

        await session.flush()

        # Check or create membership
        res_mem = await session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.user_id == user.user_id,
                OrganizationMembership.organization_id == TEST_ORG_ID,
            )
        )
        membership = res_mem.scalar_one_or_none()
        if not membership:
            membership = OrganizationMembership(
                user_id=user.user_id,
                organization_id=TEST_ORG_ID,
                role="analyst",
                is_active=True,
            )
            session.add(membership)
        else:
            membership.is_active = True

        await session.commit()
    await engine.dispose()
    print(f"Successfully seeded user {TEST_USER_EMAIL} into {TEST_ORG_ID}")


if __name__ == "__main__":
    asyncio.run(seed())
