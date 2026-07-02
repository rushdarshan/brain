import os
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
os.environ.setdefault("CACHING", "true")
DATASET = os.getenv("COGNEE_DATASET", "paylink")
SESSION_DATASET = f"{DATASET}-session"

import cognee
from cognee import SearchType
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("ProjectBrain")
API_URL = "http://127.0.0.1:8000"

@mcp.tool()
async def remember_decision(title: str, rationale: str, files: list[str], tags: list[str], supersedes: str | None = None) -> str:
    text = f"Decision: {title}\nRationale: {rationale}\nImpacted Files: {', '.join(files)}\nTags: {', '.join(tags)}"
    if supersedes:
        text += f"\nSupersedes: {supersedes}"
    await cognee.add(text, dataset_name=DATASET)
    await cognee.cognify(datasets=[DATASET])
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_URL}/api/notify", timeout=2.0)
    except Exception:
        pass
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
    results = await cognee.search(**kwargs)
    return str(results)

@mcp.tool()
async def memify_feedback(decision_id: str, signal: str) -> str:
    if signal.lower() in ["confirm", "correct", "upvote"]:
        await cognee.improve(dataset=DATASET)
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{API_URL}/api/track/review", timeout=2.0)
        except Exception:
            pass
        return f"Strengthened memory for decision {decision_id}."
    return "No feedback applied."

@mcp.tool()
async def promote_context(text: str) -> str:
    await cognee.add(text, dataset_name=DATASET)
    await cognee.cognify(datasets=[DATASET])
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_URL}/api/notify", timeout=2.0)
    except Exception:
        pass
    return f"Promoted to permanent: {text[:60]}..."

@mcp.tool()
async def forget(node_id: str, cascade: bool = True) -> str:
    await cognee.forget(dataset=DATASET, memory_only=not cascade)
    return f"Forgot memory for dataset {DATASET}. Cascade: {cascade}."

if __name__ == "__main__":
    mcp.run()
