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
from typing import Any, Optional

from langgraph.checkpoint.base import (
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
    RunnableConfig,
)
from langgraph.checkpoint.postgres import PostgresSaver


class AsyncPostgresSaver(PostgresSaver):
    """PostgresSaver with working async tuple methods for use with ``ainvoke``.

    Wraps the synchronous ``get_tuple``/``put``/``put_writes`` methods so
    LangGraph's async execution loop can checkpoint and resume runs.
    """

    # -- async read -------------------------------------------------------
    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return await asyncio.to_thread(super().get_tuple, config)

    # -- async write ------------------------------------------------------
    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return await asyncio.to_thread(
            super().put, config, checkpoint, metadata, new_versions
        )

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


__all__ = ["AsyncPostgresSaver"]
