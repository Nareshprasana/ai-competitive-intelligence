"""Async-compatible LangGraph PostgreSQL checkpointer adapter.

``langgraph-checkpoint-postgres`` ships a synchronous ``PostgresSaver`` whose
async methods (``aget_tuple``/``aput``/``aput_writes``) raise
``NotImplementedError`` in this version. LangGraph's ``ainvoke`` calls those
async methods, so we provide a thin adapter that runs the working sync methods
in a thread executor.

Usage::

    from app.core.checkpoint import AsyncPostgresSaver

    saver = AsyncPostgresSaver.from_conn_string(DATABASE_URL_PSYCOPG)
    await saver.setup()  # creates the checkpoints table
    graph = builder.compile(checkpointer=saver)
    await graph.ainvoke(state, config={"configurable": {"thread_id": "..."}})

The checkpointer stores LangGraph checkpoint state in a dedicated
``checkpoints`` / ``checkpoint_writes`` table chain, SEPARATE from the business
``researches`` table used by :class:`app.repositories.research.ResearchRepository`.
"""

import asyncio
import base64
import json
from typing import Any, Optional

from langgraph.checkpoint.base import (
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
    RunnableConfig,
)
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.serde.base import SerializerProtocol

from app.security.crypto import EncryptedCheckpointSerializer
from app.security.crypto import decrypt_text, encrypt_text

_ENCRYPTED_INLINE_KEY = "__acis_encrypted_checkpoint_value__"
_ENCRYPTED_METADATA_KEY = "__acis_encrypted_checkpoint_metadata__"


class AsyncPostgresSaver(PostgresSaver):
    """PostgresSaver with working async tuple methods for use with ``ainvoke``.

    Wraps the synchronous ``get_tuple``/``put``/``put_writes`` methods so
    LangGraph's async execution loop can checkpoint and resume runs.
    """

    def __init__(
        self, conn: Any, pipe: Any = None, serde: SerializerProtocol | None = None
    ) -> None:
        super().__init__(
            conn,
            pipe=pipe,
            serde=serde if serde is not None else EncryptedCheckpointSerializer(),
        )

    # -- async read -------------------------------------------------------
    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return await asyncio.to_thread(self.get_tuple, config)

    # -- async write ------------------------------------------------------
    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Any,
        task_id: str = "",
        task_path: str = "",
    ) -> None:
        return await asyncio.to_thread(
            super().put_writes, config, writes, task_id, task_path
        )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        encrypted_checkpoint = checkpoint.copy()
        encrypted_checkpoint["channel_values"] = {
            channel: self._pack_value(channel, value)
            for channel, value in checkpoint["channel_values"].items()
        }
        encrypted_metadata = {
            _ENCRYPTED_METADATA_KEY: encrypt_text(
                json.dumps(metadata, separators=(",", ":"), ensure_ascii=False),
                associated_data="langgraph-checkpoint.metadata",
            )
        }
        return super().put(
            config, encrypted_checkpoint, encrypted_metadata, new_versions
        )

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        checkpoint_tuple = super().get_tuple(config)
        if checkpoint_tuple is None:
            return None

        checkpoint = dict(checkpoint_tuple.checkpoint)
        checkpoint["channel_values"] = {
            channel: self._unpack_value(channel, value)
            for channel, value in checkpoint.get("channel_values", {}).items()
        }
        metadata = checkpoint_tuple.metadata
        if isinstance(metadata, dict) and _ENCRYPTED_METADATA_KEY in metadata:
            restored_metadata = json.loads(
                decrypt_text(
                    metadata[_ENCRYPTED_METADATA_KEY],
                    associated_data="langgraph-checkpoint.metadata",
                )
            )
            metadata = {
                **{
                    key: value
                    for key, value in metadata.items()
                    if key != _ENCRYPTED_METADATA_KEY
                },
                **restored_metadata,
            }
        return checkpoint_tuple._replace(checkpoint=checkpoint, metadata=metadata)

    def _pack_value(self, channel: str, value: Any) -> dict[str, Any]:
        value_type, payload = self.serde.dumps_typed(value)
        return {
            _ENCRYPTED_INLINE_KEY: {
                "mode": "typed",
                "type": value_type,
                "payload": base64.b64encode(payload).decode("ascii"),
            }
        }

    def _unpack_value(self, channel: str, value: Any) -> Any:
        if not isinstance(value, dict) or _ENCRYPTED_INLINE_KEY not in value:
            raise ValueError("Checkpoint channel value is not encrypted.")
        encrypted = value[_ENCRYPTED_INLINE_KEY]
        if not isinstance(encrypted, dict):
            raise ValueError("Invalid encrypted checkpoint channel value.")
        if encrypted.get("mode") == "typed":
            payload = base64.b64decode(encrypted["payload"], validate=True)
            return self.serde.loads_typed((encrypted["type"], payload))
        if encrypted.get("mode") == "json-inline":
            return json.loads(
                decrypt_text(
                    encrypted["payload"],
                    associated_data=f"langgraph-checkpoint.inline:{channel}",
                )
            )
        raise ValueError("Unsupported encrypted checkpoint value.")


__all__ = ["AsyncPostgresSaver"]
