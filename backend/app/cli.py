"""Operator commands for bootstrap administration."""

import argparse
import asyncio
import getpass
import re
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from app.core.database import db
from app.models.identity import User
from app.security.auth import email_lookup_hash, hash_password


async def _bootstrap_admin(email: str, password: str) -> None:
    if not db.is_available:
        raise RuntimeError("DATABASE_URL must be configured to bootstrap an administrator.")
    normalized_email = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized_email):
        raise ValueError("A valid email address is required.")
    password_hash = hash_password(password)
    async with db.session_factory() as session:
        existing_admin = (
            await session.execute(
                select(User.user_id).where(User.is_platform_admin.is_(True)).limit(1)
            )
        ).scalar_one_or_none()
        if existing_admin is not None:
            raise RuntimeError("A platform administrator is already provisioned.")
        existing_user = (
            await session.execute(
                select(User.user_id).where(
                    User.email_lookup_hash == email_lookup_hash(normalized_email)
                )
            )
        ).scalar_one_or_none()
        if existing_user is not None:
            raise RuntimeError("An account with that email already exists.")
        session.add(
            User(
                user_id=str(uuid4()),
                email=normalized_email,
                email_lookup_hash=email_lookup_hash(normalized_email),
                password_hash=password_hash,
                is_platform_admin=True,
            )
        )
        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    bootstrap = subparsers.add_parser(
        "bootstrap-admin", help="Create the first platform administrator."
    )
    bootstrap.add_argument("--email", help="Administrator email; prompted if omitted.")
    args = parser.parse_args()

    email = args.email or input("Administrator email: ")
    password = getpass.getpass("Password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")
    try:
        asyncio.run(_bootstrap_admin(email, password))
    except (HTTPException, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    print("Platform administrator created.")


if __name__ == "__main__":
    main()
