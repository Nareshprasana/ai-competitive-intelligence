"""Authenticated encryption helpers for stored ACIS research data."""

import base64
import json
import os
import re
from typing import Any, Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings

_ENVELOPE_PREFIX = "acis:v1:"
_KEY_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_CHECKPOINT_PREFIX = "acis-aesgcm-v1:"


class EncryptionConfigurationError(RuntimeError):
    """Raised when the encryption keyring is missing or invalid."""


def _keyring() -> tuple[str, dict[str, bytes]]:
    settings = get_settings()
    try:
        encoded_keys = json.loads(settings.data_encryption_keys.get_secret_value())
    except (TypeError, json.JSONDecodeError) as exc:
        raise EncryptionConfigurationError(
            "DATA_ENCRYPTION_KEYS must be a JSON object of base64 keys."
        ) from exc
    if not isinstance(encoded_keys, dict) or not encoded_keys:
        raise EncryptionConfigurationError("No data-encryption keys are configured.")

    keys: dict[str, bytes] = {}
    for key_id, encoded_key in encoded_keys.items():
        if not isinstance(key_id, str) or not _KEY_ID_PATTERN.fullmatch(key_id):
            raise EncryptionConfigurationError("Invalid data-encryption key ID.")
        if not isinstance(encoded_key, str):
            raise EncryptionConfigurationError("Data-encryption keys must be base64 strings.")
        try:
            key = base64.b64decode(encoded_key, validate=True)
        except ValueError as exc:
            raise EncryptionConfigurationError(
                "Data-encryption keys must be valid base64."
            ) from exc
        if len(key) != 32:
            raise EncryptionConfigurationError(
                "AES-256-GCM keys must decode to exactly 32 bytes."
            )
        keys[key_id] = key

    active_key_id = settings.data_encryption_active_key_id
    if active_key_id not in keys:
        raise EncryptionConfigurationError(
            "DATA_ENCRYPTION_ACTIVE_KEY_ID must name a configured key."
        )
    return active_key_id, keys


def validate_encryption_configuration() -> None:
    """Validate configured keys without encrypting or logging their values."""
    _keyring()


def encrypt_bytes(value: bytes, *, associated_data: bytes) -> str:
    key_id, keys = _keyring()
    nonce = os.urandom(12)
    aad = associated_data + b"|" + key_id.encode()
    ciphertext = AESGCM(keys[key_id]).encrypt(nonce, value, aad)
    payload = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return f"{_ENVELOPE_PREFIX}{key_id}:{payload}"


def decrypt_bytes(value: str, *, associated_data: bytes) -> bytes:
    try:
        prefix, version, key_id, payload = value.split(":", 3)
    except ValueError as exc:
        raise ValueError("Invalid encrypted data envelope.") from exc
    if prefix != "acis" or version != "v1" or not _KEY_ID_PATTERN.fullmatch(key_id):
        raise ValueError("Invalid encrypted data envelope.")
    _, keys = _keyring()
    key = keys.get(key_id)
    if key is None:
        raise EncryptionConfigurationError(
            "A key required to decrypt stored data is unavailable."
        )
    try:
        packed = base64.b64decode(
            payload.encode("ascii"), altchars=b"-_", validate=True
        )
        nonce, ciphertext = packed[:12], packed[12:]
        if len(nonce) != 12 or not ciphertext:
            raise ValueError("Invalid encrypted data payload.")
        aad = associated_data + b"|" + key_id.encode()
        return AESGCM(key).decrypt(nonce, ciphertext, aad)
    except (InvalidTag, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("Encrypted data failed integrity validation.") from exc


def encrypt_text(value: str, *, associated_data: str) -> str:
    return encrypt_bytes(value.encode("utf-8"), associated_data=associated_data.encode())


def decrypt_text(value: str, *, associated_data: str) -> str:
    return decrypt_bytes(value, associated_data=associated_data.encode()).decode("utf-8")


def encrypt_checkpoint_payload(inner_type: str, payload: bytes) -> tuple[str, bytes]:
    envelope = encrypt_bytes(
        inner_type.encode() + b"\0" + payload,
        associated_data=f"langgraph-checkpoint:{inner_type}".encode(),
    )
    _, _, key_id, encoded_payload = envelope.split(":", 3)
    return f"{_CHECKPOINT_PREFIX}{key_id}:{inner_type}", encoded_payload.encode("ascii")


class EncryptedText(TypeDecorator[Optional[str]]):
    """Text column transparently encrypted with AES-256-GCM."""

    impl = Text
    cache_ok = True

    def __init__(self, associated_data: str) -> None:
        super().__init__()
        self.associated_data = associated_data

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        if value is None:
            return None
        return encrypt_text(value, associated_data=self.associated_data)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        if value is None:
            return None
        return decrypt_text(value, associated_data=self.associated_data)


class EncryptedJSON(TypeDecorator[Any]):
    """JSON value encrypted before it reaches the database driver."""

    impl = Text
    cache_ok = True

    def __init__(self, associated_data: str) -> None:
        super().__init__()
        self.associated_data = associated_data

    def process_bind_param(self, value: Any, dialect) -> Optional[str]:
        if value is None:
            return None
        serialized = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        return encrypt_text(serialized, associated_data=self.associated_data)

    def process_result_value(self, value: Optional[str], dialect) -> Any:
        if value is None:
            return None
        decrypted = decrypt_text(value, associated_data=self.associated_data)
        return json.loads(decrypted)


class EncryptedCheckpointSerializer:
    """Encrypt LangGraph checkpoint payloads while retaining their serializer type."""

    def __init__(self, inner: Optional[JsonPlusSerializer] = None) -> None:
        self._inner = inner or JsonPlusSerializer()

    def dumps_typed(self, value: Any) -> tuple[str, bytes]:
        value_type, payload = self._inner.dumps_typed(value)
        return encrypt_checkpoint_payload(value_type, payload)

    def loads_typed(self, data: tuple[str, bytes]) -> Any:
        value_type, payload = data
        if not isinstance(value_type, str) or not value_type.startswith(
            _CHECKPOINT_PREFIX
        ):
            raise ValueError("Checkpoint payload is not encrypted.")
        try:
            _, key_id, inner_type = value_type.split(":", 2)
        except (AttributeError, ValueError) as exc:
            raise ValueError("Invalid encrypted checkpoint type.") from exc
        try:
            encoded_payload = payload.decode("ascii")
        except (AttributeError, UnicodeDecodeError) as exc:
            raise ValueError("Invalid encrypted checkpoint payload.") from exc
        envelope = f"{_ENVELOPE_PREFIX}{key_id}:{encoded_payload}"
        decrypted = decrypt_bytes(
            envelope,
            associated_data=f"langgraph-checkpoint:{inner_type}".encode(),
        )
        actual_type, raw = decrypted.split(b"\0", 1)
        if actual_type.decode() != inner_type:
            raise ValueError("Checkpoint serialization type failed integrity validation.")
        return self._inner.loads_typed((inner_type, raw))


__all__ = [
    "EncryptedCheckpointSerializer",
    "EncryptedJSON",
    "EncryptedText",
    "EncryptionConfigurationError",
    "decrypt_bytes",
    "decrypt_text",
    "encrypt_bytes",
    "encrypt_checkpoint_payload",
    "encrypt_text",
    "validate_encryption_configuration",
]
