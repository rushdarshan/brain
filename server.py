import os
from uuid import UUID
from contextlib import asynccontextmanager
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
os.environ.setdefault("CACHING", "true")
DATASET = os.getenv("COGNEE_DATASET", "paylink")
SESSION_DATASET = f"{DATASET}-session"

from cognee_init import init_cognee
import cognee
from cognee import SearchType
from mcp.server.fastmcp import FastMCP

@asynccontextmanager
async def cognee_lifespan(app):
    await init_cognee()
    yield

mcp = FastMCP("ProjectBrain", lifespan=cognee_lifespan)

from cognee.infrastructure.engine import DataPoint

class Decision(DataPoint):
    title: str
    rationale: str
    files: list[str]
    tags: list[str]
    supersedes: str | None = None

@mcp.tool()
async def remember_decision(title: str, rationale: str, files: list[str], tags: list[str], supersedes: str | None = None) -> str:
    decision = Decision(
        title=title,
        rationale=rationale,
        files=files,
        tags=tags,
        supersedes=supersedes,
    )
    # Using the DataPoint structure directly instead of raw text strings
    await cognee.remember(decision, dataset_name=DATASET)
    return f"Remembered decision: {title}"

@mcp.tool()
async def recall_context(query: str, mode: str = "GRAPH_COMPLETION", session_id: str | None = None, scope: str = "all") -> str:
    try:
        st = SearchType(mode)
    except ValueError:
        st = SearchType.GRAPH_COMPLETION
    ds = [DATASET, SESSION_DATASET] if scope == "all" else [DATASET]
    kwargs = {"query_text": query, "query_type": st, "datasets": ds}
    if session_id:
        kwargs["session_id"] = session_id
    results = await cognee.recall(**kwargs)
    if results and isinstance(results[0], dict):
        return " ".join(r.get("text", "") for r in results if r.get("text"))
    return str(results)

@mcp.tool()
async def memify_feedback(decision_id: str, signal: str) -> str:
    if signal.lower() in ["confirm", "correct", "upvote"]:
        await cognee.improve(dataset=DATASET, build_truth_subspace=True)
        return f"Strengthened memory for decision {decision_id}."
    return "No feedback applied."

@mcp.tool()
async def promote_context(text: str) -> str:
    await cognee.remember(text, dataset_name=DATASET)
    return f"Promoted to permanent: {text[:60]}..."

@mcp.tool()
async def remember_snapshot(text: str, snapshot_id: str | None = None, tags: list[str] | None = None) -> str:
    metadata = f"[snapshot_id={snapshot_id or 'auto'}]" if snapshot_id else ""
    if tags:
        metadata += f"[tags={','.join(tags)}]"
    await cognee.remember(f"{metadata} {text}", dataset_name=DATASET)
    return f"Remembered snapshot{f' {snapshot_id}' if snapshot_id else ''}."

@mcp.tool()
async def forget(node_id: str = "", cascade: bool = True) -> str:
    if os.environ.get("COGNEE_FORGET_ENABLED", "false") != "true":
        return "Forget is disabled. Set COGNEE_FORGET_ENABLED=true to enable."
    kwargs = {}
    if node_id and node_id.strip():
        try:
            kwargs["data_id"] = UUID(node_id.strip())
        except ValueError:
            return f"Invalid node_id: {node_id}. Must be a valid UUID."
    else:
        kwargs["dataset"] = DATASET
    if not cascade:
        kwargs["memory_only"] = True
    await cognee.forget(**kwargs)
    return f"Forgot {f'node {node_id}' if node_id else f'dataset {DATASET}'}. Cascade: {cascade}."

if __name__ == "__main__":
    mcp.run()
