"""finalize_research node: determines overall status and finalizes the run."""

from app.graph.nodes.base import run_node
from app.graph.state import ResearchState


async def _finalize_research(state: ResearchState) -> dict:
    has_errors = bool(state.errors)
    status = "failed" if has_errors else "completed"
    review_status = "failed" if has_errors else "reviewed"

    feedback = None
    if has_errors:
        failed_nodes = [e["node_name"] for e in state.errors]
        feedback = (
            "Research run completed with errors. Failed nodes: "
            + ", ".join(failed_nodes)
            + ". Review the execution_metadata and errors fields for details."
        )
    else:
        feedback = "All research nodes completed successfully (mock Phase 1 run)."

    return {
        "review_status": review_status,
        "errors": state.errors,  # preserve recorded errors
        "_metadata_details": {
            "overall_status": status,
            "error_count": len(state.errors),
            "final_report_present": state.final_report is not None,
        },
    }


async def finalize_research(state: ResearchState) -> dict:
    """Finalize the research run: set overall status based on recorded errors.

    Never reports success when a node has failed.
    """
    return await run_node(
        node_name="finalize_research",
        state=state,
        node_fn=_finalize_research,
        mock=True,
    )
