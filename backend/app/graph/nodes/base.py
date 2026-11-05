"""Shared helpers for graph node execution: timing, metadata, error recording."""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.graph.state import ResearchState

logger = get_logger("app.graph.nodes.base")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_metadata(
    *,
    node_name: str,
    status: str,
    started_at: str,
    completed_at: str,
    duration_ms: float,
    mock: bool = True,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "node_name": node_name,
        "status": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": round(duration_ms, 4),
        "mock": mock,
        "details": details or {},
    }


async def run_node(
    *,
    node_name: str,
    state: ResearchState,
    node_fn,
    mock: bool = True,
) -> Dict[str, Any]:
    """Execute a node function, recording metadata and errors.

    Returns a partial state update dict. Execution metadata is always appended.
    On success, the node's update is merged with ``status="completed"`` metadata.
    On failure, an error entry and ``status="failed"`` metadata are appended so
    the graph never reports success for a failed node.
    """
    started_at = utc_now_iso()
    start = time.perf_counter()
    try:
        update = await node_fn(state) or {}
        if not isinstance(update, dict):
            update = {}
        duration_ms = (time.perf_counter() - start) * 1000
        completed_at = utc_now_iso()
        metadata = make_metadata(
            node_name=node_name,
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            mock=mock,
            details=update.pop("_metadata_details", None),
        )
        result: Dict[str, Any] = dict(update)
        result["execution_metadata"] = [metadata]
        # No new errors on success.
        result["errors"] = []
        return result
    except Exception as exc:  # noqa: BLE001 - capture and record, never crash graph
        duration_ms = (time.perf_counter() - start) * 1000
        completed_at = utc_now_iso()
        metadata = make_metadata(
            node_name=node_name,
            status="failed",
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            mock=mock,
            details={"exception": type(exc).__name__},
        )
        logger.error(
            "Graph node failed node=%s error_type=%s",
            node_name,
            type(exc).__name__,
        )
        error_entry = {
            "node_name": node_name,
            "error": "The operation could not be completed.",
            "details": {"exception": type(exc).__name__},
            "timestamp": completed_at,
        }
        return {
            "execution_metadata": [metadata],
            "errors": [error_entry],
        }
