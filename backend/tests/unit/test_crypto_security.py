"""Security and compatibility tests for encrypted database/checkpoint payloads."""

import base64
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from langgraph.checkpoint.base import CheckpointTuple
from langgraph.checkpoint.postgres import PostgresSaver
from pydantic import SecretStr

from app.core.checkpoint import AsyncPostgresSaver, _ENCRYPTED_INLINE_KEY
from app.graph.state import ResearchState
from app.security import crypto


def _settings(keys: dict[str, bytes], active_key_id: str) -> SimpleNamespace:
    encoded_keys = {
        key_id: base64.b64encode(key).decode("ascii")
        for key_id, key in keys.items()
    }
    return SimpleNamespace(
        data_encryption_keys=SecretStr(json.dumps(encoded_keys)),
        data_encryption_active_key_id=active_key_id,
    )


def _split_envelope(value: str) -> tuple[str, bytes]:
    prefix, version, key_id, payload = value.split(":", 3)
    assert (prefix, version) == ("acis", "v1")
    return key_id, base64.b64decode(payload, altchars=b"-_", validate=True)


def _join_envelope(key_id: str, packed: bytes) -> str:
    return "acis:v1:" + key_id + ":" + base64.urlsafe_b64encode(packed).decode()


def test_aes_gcm_uses_unique_12_byte_nonces_and_round_trips(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    nonces = iter((b"\x01" * 12, b"\x02" * 12))
    monkeypatch.setattr(crypto.os, "urandom", lambda size: next(nonces))
    plaintext = b"private customer research"

    first = crypto.encrypt_bytes(plaintext, associated_data=b"research.results")
    second = crypto.encrypt_bytes(plaintext, associated_data=b"research.results")
    _, first_packed = _split_envelope(first)
    _, second_packed = _split_envelope(second)

    assert len(first_packed[:12]) == 12
    assert first_packed[:12] != second_packed[:12]
    assert crypto.decrypt_bytes(first, associated_data=b"research.results") == plaintext
    assert crypto.decrypt_bytes(second, associated_data=b"research.results") == plaintext


@pytest.mark.parametrize("tamper_offset", [0, -1])
def test_ciphertext_or_nonce_modification_fails_authentication(monkeypatch, tamper_offset):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    encrypted = crypto.encrypt_bytes(b"secret", associated_data=b"field")
    key_id, packed = _split_envelope(encrypted)
    changed = bytearray(packed)
    changed[tamper_offset] ^= 0x01

    with pytest.raises(ValueError, match="integrity validation"):
        crypto.decrypt_bytes(_join_envelope(key_id, bytes(changed)), associated_data=b"field")


def test_wrong_associated_data_and_wrong_key_fail_safely(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    ciphertext = crypto.encrypt_text("confidential", associated_data="research.results")

    with pytest.raises(ValueError, match="integrity validation"):
        crypto.decrypt_text(ciphertext, associated_data="research.errors")

    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"b" * 32}, "k1"))
    with pytest.raises(ValueError, match="integrity validation"):
        crypto.decrypt_text(ciphertext, associated_data="research.results")


def test_unknown_key_id_fails_without_echoing_key_or_plaintext(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    ciphertext = crypto.encrypt_text("private marker", associated_data="field")
    _, packed = _split_envelope(ciphertext)

    with pytest.raises(crypto.EncryptionConfigurationError) as error:
        crypto.decrypt_text(_join_envelope("unknown-key", packed), associated_data="field")

    assert "private marker" not in str(error.value)
    assert "unknown-key" not in str(error.value)


def test_key_rotation_reads_old_key_and_writes_with_active_key(monkeypatch):
    old_key = b"a" * 32
    new_key = b"b" * 32
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"old": old_key}, "old"))
    old_ciphertext = crypto.encrypt_text("old record", associated_data="field")

    monkeypatch.setattr(
        crypto,
        "get_settings",
        lambda: _settings({"old": old_key, "new": new_key}, "new"),
    )
    new_ciphertext = crypto.encrypt_text("new record", associated_data="field")
    assert old_ciphertext.startswith("acis:v1:old:")
    assert new_ciphertext.startswith("acis:v1:new:")
    assert crypto.decrypt_text(old_ciphertext, associated_data="field") == "old record"

    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"new": new_key}, "new"))
    with pytest.raises(crypto.EncryptionConfigurationError):
        crypto.decrypt_text(old_ciphertext, associated_data="field")


def test_orm_encrypted_types_hide_plaintext_and_reject_plaintext_storage(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    secret_text = "sensitive evidence snippet"
    secret_json = {"research": "sensitive payload"}
    text_type = crypto.EncryptedText("evidence.raw_snippet")
    json_type = crypto.EncryptedJSON("research.results")

    stored_text = text_type.process_bind_param(secret_text, None)
    stored_json = json_type.process_bind_param(secret_json, None)

    assert secret_text not in stored_text
    assert "sensitive payload" not in stored_json
    assert text_type.process_result_value(stored_text, None) == secret_text
    assert json_type.process_result_value(stored_json, None) == secret_json
    with pytest.raises(ValueError):
        text_type.process_result_value(secret_text, None)
    with pytest.raises(ValueError):
        json_type.process_result_value('{"private":"plaintext"}', None)


def test_all_sensitive_orm_columns_use_encrypted_types(monkeypatch):
    from app.models.company import CompanyProfile, EvidenceClaim
    from app.models.competitor import Competitor, CompetitorEvidence
    from app.models.identity import OrganizationInvitation, User
    from app.models.research import Research

    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    models = (
        (Research, {"company_name", "industry", "research_question", "results", "errors"}),
        (CompanyProfile, {"profile", "source_references"}),
        (EvidenceClaim, {"claim", "raw_snippet"}),
        (Competitor, {"company_description", "profile", "source_references"}),
        (CompetitorEvidence, {"claim", "raw_snippet"}),
        (User, {"email"}),
        (OrganizationInvitation, {"email"}),
    )

    for model, expected_columns in models:
        for column_name in expected_columns:
            column_type = model.__table__.c[column_name].type
            assert isinstance(column_type, (crypto.EncryptedText, crypto.EncryptedJSON))
            value = "sensitive database marker"
            bound_value = column_type.process_bind_param(value, None)
            assert value not in bound_value
            assert bound_value.startswith("acis:v1:k1:")


def test_checkpoint_serializer_round_trips_langgraph_value_types(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    serializer = crypto.EncryptedCheckpointSerializer()
    values = [
        None,
        True,
        42,
        3.5,
        "private checkpoint",
        b"private bytes",
        bytearray(b"private bytearray"),
        ["nested", {"value": "private"}],
        datetime(2026, 11, 5, tzinfo=timezone.utc),
        ResearchState(
            research_id="res-checkpoint",
            organization_id="org-checkpoint",
            company_name="Private Co",
            industry="Private Market",
            research_question="Private question",
            evidence=[{"claim": "private claim"}],
        ),
    ]

    for value in values:
        value_type, payload = serializer.dumps_typed(value)
        assert value_type.startswith("acis-aesgcm-v1:")
        assert repr(value).encode() not in payload
        decoded = serializer.loads_typed((value_type, payload))
        assert decoded == value
        if isinstance(value, bytearray):
            assert isinstance(decoded, bytearray)


def test_checkpoint_serializer_rejects_unencrypted_payloads(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    with pytest.raises(ValueError, match="not encrypted"):
        crypto.EncryptedCheckpointSerializer().loads_typed(("msgpack", b"plaintext"))


def test_checkpointer_defaults_to_encryption_and_encrypts_pending_writes(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    saver = AsyncPostgresSaver(None)

    assert isinstance(saver.serde, crypto.EncryptedCheckpointSerializer)
    row = saver._dump_writes(
        "thread",
        "",
        "checkpoint",
        "task",
        "",
        [("private_channel", "secret pending write")],
    )[0]
    value_type, payload = row[-2:]
    assert value_type.startswith("acis-aesgcm-v1:")
    assert b"secret pending write" not in payload
    assert saver.serde.loads_typed((value_type, payload)) == "secret pending write"


def test_checkpointer_encrypts_checkpoint_values_and_metadata_and_reads_them(
    monkeypatch,
):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    saver = AsyncPostgresSaver(None)
    captured = {}

    def fake_put(_self, _config, checkpoint, metadata, _new_versions):
        captured["checkpoint"] = checkpoint
        captured["metadata"] = metadata
        return {"configurable": {"checkpoint_id": "id"}}

    monkeypatch.setattr(PostgresSaver, "put", fake_put)
    saver.put(
        {"configurable": {"thread_id": "org:one:research:one", "checkpoint_ns": ""}},
        {"id": "id", "channel_values": {"question": "secret channel value"}},
        {"step": 1, "private": "secret metadata"},
        {},
    )

    marker = captured["checkpoint"]["channel_values"]["question"][_ENCRYPTED_INLINE_KEY]
    encrypted_metadata = captured["metadata"]["__acis_encrypted_checkpoint_metadata__"]
    assert "secret channel value" not in marker["payload"]
    assert "secret metadata" not in encrypted_metadata

    def fake_get_tuple(_self, _config):
        return CheckpointTuple(
            {"configurable": {"thread_id": "org:one:research:one"}},
            captured["checkpoint"],
            captured["metadata"],
            None,
            [],
        )

    monkeypatch.setattr(PostgresSaver, "get_tuple", fake_get_tuple)
    restored = saver.get_tuple({"configurable": {"thread_id": "org:one:research:one"}})
    assert restored.checkpoint["channel_values"]["question"] == "secret channel value"
    assert restored.metadata == {"step": 1, "private": "secret metadata"}


def test_checkpoint_adapter_rejects_plaintext_channel_values(monkeypatch):
    monkeypatch.setattr(crypto, "get_settings", lambda: _settings({"k1": b"a" * 32}, "k1"))
    with pytest.raises(ValueError, match="not encrypted"):
        AsyncPostgresSaver(None)._unpack_value("question", "plaintext")
