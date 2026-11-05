"""Encrypt persisted research and checkpoint payloads with AES-256-GCM.

Revision ID: 0005_encrypt_sensitive_payloads
Revises: 0004_identity_and_tenant_ownership
"""

import json
import hashlib
import hmac
from typing import Any, Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.security.crypto import (
    encrypt_checkpoint_payload,
    encrypt_text,
    validate_encryption_configuration,
)
from app.core.config import get_settings

revision: str = "0005_encrypt_sensitive_payloads"
down_revision: Union[str, None] = "0004_identity_and_tenant_ownership"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FIELDS = (
    ("researches", "company_name", False, False),
    ("researches", "industry", False, False),
    ("researches", "research_question", False, False),
    ("researches", "results", True, True),
    ("researches", "errors", True, True),
    ("company_profiles", "profile", True, True),
    ("company_profiles", "source_references", True, True),
    ("evidence_claims", "claim", False, False),
    ("evidence_claims", "raw_snippet", False, True),
    ("competitors", "company_description", False, True),
    ("competitors", "profile", True, True),
    ("competitors", "source_references", True, True),
    ("competitor_evidence", "claim", False, False),
    ("competitor_evidence", "raw_snippet", False, True),
)


def _encode_field(value: Any, *, is_json: bool, associated_data: str) -> str:
    plaintext = (
        json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        if is_json
        else str(value)
    )
    return encrypt_text(plaintext, associated_data=associated_data)


def _encrypt_column(
    connection,
    *,
    table: str,
    column: str,
    is_json: bool,
    nullable: bool,
) -> None:
    encrypted_column = f"{column}__encrypted"
    op.add_column(table, sa.Column(encrypted_column, sa.Text(), nullable=True))
    last_id = 0
    while True:
        rows = connection.execute(
            sa.text(
                f'SELECT id, "{column}" FROM "{table}" '
                f'WHERE id > :last_id ORDER BY id LIMIT 200'
            ),
            {"last_id": last_id},
        ).all()
        if not rows:
            break
        for row_id, value in rows:
            last_id = row_id
            if value is None:
                continue
            encrypted = _encode_field(
                value,
                is_json=is_json,
                associated_data=f"{table}.{column}",
            )
            connection.execute(
                sa.text(
                    f'UPDATE "{table}" SET "{encrypted_column}" = :value WHERE id = :id'
                ),
                {"value": encrypted, "id": row_id},
            )
    op.drop_column(table, column)
    op.alter_column(
        table,
        encrypted_column,
        new_column_name=column,
        existing_type=sa.Text(),
        nullable=nullable,
    )


def _encrypt_identity_email(connection, *, table: str, primary_key: str) -> None:
    settings = get_settings()
    lookup_key = settings.auth_email_lookup_key.get_secret_value()
    if len(lookup_key) < 32:
        raise RuntimeError(
            "AUTH_EMAIL_LOOKUP_KEY must contain at least 32 characters to migrate user emails."
        )
    encrypted_column = "email__encrypted"
    op.add_column(table, sa.Column(encrypted_column, sa.Text(), nullable=True))
    for row in connection.execute(
        sa.text(f'SELECT "{primary_key}", email FROM "{table}"')
    ).all():
        row_id, email = row
        normalized_email = str(email).strip().lower()
        lookup_hash = hmac.new(
            lookup_key.encode("utf-8"),
            normalized_email.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        connection.execute(
            sa.text(
                f'UPDATE "{table}" SET email_lookup_hash = :lookup_hash, '
                f'"{encrypted_column}" = :encrypted WHERE "{primary_key}" = :id'
            ),
            {
                "lookup_hash": lookup_hash,
                "encrypted": _encode_field(
                    normalized_email,
                    is_json=False,
                    associated_data=f"{table}.email",
                ),
                "id": row_id,
            },
        )
    op.drop_column(table, "email")
    op.alter_column(
        table,
        encrypted_column,
        new_column_name="email",
        existing_type=sa.Text(),
        nullable=False,
    )


def _encrypt_existing_checkpoints(connection) -> None:
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    if "checkpoints" not in tables:
        return

    for row in connection.execute(
        sa.text(
            "SELECT thread_id, checkpoint_ns, checkpoint_id, checkpoint, metadata "
            "FROM checkpoints"
        )
    ).mappings():
        checkpoint = row["checkpoint"]
        channel_values = checkpoint.get("channel_values") or {}
        for channel, value in list(channel_values.items()):
            channel_values[channel] = {
                "__acis_encrypted_checkpoint_value__": {
                    "mode": "json-inline",
                    "payload": encrypt_text(
                        json.dumps(value, separators=(",", ":"), ensure_ascii=False),
                        associated_data=f"langgraph-checkpoint.inline:{channel}",
                    ),
                }
            }
        metadata = {
            "__acis_encrypted_checkpoint_metadata__": encrypt_text(
                json.dumps(row["metadata"], separators=(",", ":"), ensure_ascii=False),
                associated_data="langgraph-checkpoint.metadata",
            )
        }
        connection.execute(
            sa.text(
                "UPDATE checkpoints SET checkpoint = CAST(:checkpoint AS jsonb), "
                "metadata = CAST(:metadata AS jsonb) "
                "WHERE thread_id = :thread_id AND checkpoint_ns = :checkpoint_ns "
                "AND checkpoint_id = :checkpoint_id"
            ),
            {
                "checkpoint": json.dumps(checkpoint, separators=(",", ":")),
                "metadata": json.dumps(metadata, separators=(",", ":")),
                "thread_id": row["thread_id"],
                "checkpoint_ns": row["checkpoint_ns"],
                "checkpoint_id": row["checkpoint_id"],
            },
        )

    for table, blob_column, key_columns in (
        (
            "checkpoint_blobs",
            "blob",
            ("thread_id", "checkpoint_ns", "channel", "version"),
        ),
        (
            "checkpoint_writes",
            "blob",
            ("thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx"),
        ),
    ):
        if table not in tables:
            continue
        rows = connection.execute(
            sa.text(f'SELECT type, "{blob_column}", {", ".join(key_columns)} FROM "{table}"')
        ).all()
        for row in rows:
            value_type, payload, *key_values = row
            if payload is None or value_type in (None, "empty"):
                continue
            encrypted_type, encrypted_payload = encrypt_checkpoint_payload(
                value_type, bytes(payload)
            )
            where = " AND ".join(f'"{column}" = :{column}' for column in key_columns)
            params = dict(zip(key_columns, key_values))
            params.update({"type": encrypted_type, "blob": encrypted_payload})
            connection.execute(
                sa.text(
                    f'UPDATE "{table}" SET type = :type, "{blob_column}" = :blob '
                    f"WHERE {where}"
                ),
                params,
            )


def upgrade() -> None:
    validate_encryption_configuration()
    connection = op.get_bind()
    _encrypt_identity_email(
        connection, table="users", primary_key="user_id"
    )
    _encrypt_identity_email(
        connection,
        table="organization_invitations",
        primary_key="token_hash",
    )
    for table, column, is_json, nullable in _FIELDS:
        _encrypt_column(
            connection,
            table=table,
            column=column,
            is_json=is_json,
            nullable=nullable,
        )
    _encrypt_existing_checkpoints(connection)


def downgrade() -> None:
    raise RuntimeError(
        "Encrypted data cannot be safely downgraded to plaintext automatically. "
        "Restore a verified backup and perform an approved decryption migration."
    )
