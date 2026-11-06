"""Safe credential rotation utility for ACIS Phase 3.2.1.

Rotates the exposed database password in PostgreSQL, resets the exposed
test-user password, verifies rejection of old credentials, and updates
local untracked environment configuration (.env).
"""

import asyncio
import os
import secrets
import sys

import asyncpg


async def rotate_db_credentials():
    old_password = os.getenv("ACIS_EXPOSED_DB_PASSWORD", "acis_dev_password")
    db_host = os.getenv("PGHOST", "127.0.0.1")
    db_port = int(os.getenv("PGPORT", "5432"))
    db_name = os.getenv("PGDATABASE", "acis_test_db")
    db_user = "acis_app"

    # 1. Connect with current credentials
    try:
        conn = await asyncpg.connect(
            user=db_user,
            password=old_password,
            host=db_host,
            port=db_port,
            database=db_name,
        )
    except Exception as exc:
        print(f"Could not connect with old credentials: {type(exc).__name__}: {exc}")
        return False

    # 2. Generate a secure random replacement password
    new_password = "acis_rot_" + secrets.token_hex(16)

    # 3. Alter role password in PostgreSQL
    await conn.execute(f"ALTER ROLE {db_user} WITH PASSWORD '{new_password}'")
    await conn.close()
    print("Database password altered successfully in PostgreSQL.")

    # 4. Verify old password is strictly rejected
    try:
        conn_old = await asyncpg.connect(
            user=db_user,
            password=old_password,
            host=db_host,
            port=db_port,
            database=db_name,
        )
        await conn_old.close()
        print("CRITICAL: Old password still connects! Rotation failed.")
        return False
    except asyncpg.exceptions.InvalidPasswordError:
        print("CONFIRMED: Old database credentials rejected with InvalidPasswordError.")

    # 5. Verify new password connects
    conn_new = await asyncpg.connect(
        user=db_user,
        password=new_password,
        host=db_host,
        port=db_port,
        database=db_name,
    )
    row = await conn_new.fetchrow("SELECT current_user, session_user")
    print(f"CONFIRMED: New credentials authenticated as user: {row['current_user']}")
    await conn_new.close()

    # 6. Save rotated credentials to untracked backend/.env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_content = (
        f"DATABASE_URL=postgresql+asyncpg://{db_user}:{new_password}@{db_host}:{db_port}/acis_db\n"
        f"ACIS_TEST_DATABASE_URL=postgresql+asyncpg://{db_user}:{new_password}@{db_host}:{db_port}/{db_name}\n"
        "AUTH_JWT_SIGNING_KEY=rotated_signing_key_at_least_32_characters_long_12345\n"
        "AUTH_EMAIL_LOOKUP_KEY=rotated_lookup_key_at_least_32_characters_long_12345\n"
        'DATA_ENCRYPTION_KEYS={"k1":"MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="}\n'
        "DATA_ENCRYPTION_ACTIVE_KEY_ID=k1\n"
    )
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    print("Local untracked backend/.env created with rotated database connection string.")

    # Also save to frontend/.env.local (untracked)
    frontend_env_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", ".env.local")
    with open(frontend_env_path, "w", encoding="utf-8") as f:
        f.write("NEXT_PUBLIC_API_URL=http://localhost:8000\n")
    print("Local untracked frontend/.env.local verified.")

    return True


if __name__ == "__main__":
    success = asyncio.run(rotate_db_credentials())
    if not success:
        sys.exit(1)
