import asyncio, json, os, time
from collections import deque
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
os.environ.setdefault("CACHING", "true")
DATASET = os.getenv("COGNEE_DATASET", "paylink")
SESSION_DATASET = f"{DATASET}-session"

import cognee
from cognee import SearchType
from cognee_init import init_cognee

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

clients: list[asyncio.Queue] = []

async def load_graph_from_cognee():
    """Load current graph from Cognee's relational memory tables."""
    try:
        nodes, edges = await cognee.get_memory_provenance_graph(include_memory=True)
    except Exception:
        return {"nodes": [], "links": []}

    graph_nodes = []
    for n in nodes:
        props = n.properties or {}
        name = props.get("name", n.id.split(":")[-1] if ":" in n.id else n.id)
        ntype = props.get("type", "Node")
        group_map = {"Decision": "decision", "File": "file", "Incident": "incident", "Metric": "metric", "TextDocument": "file"}
        group = "decision"
        for k, v in group_map.items():
            if k.lower() in ntype.lower():
                group = v
                break
        graph_nodes.append({"id": n.id, "name": name, "group": group, "val": 20})

    graph_links = []
    for e in edges:
        graph_links.append({"source": e.source, "target": e.target, "name": e.relation})

    return {"nodes": graph_nodes, "links": graph_links}

STATE: dict = {"nodes": [], "links": []}
search_latencies: deque = deque(maxlen=10)
search_total: int = 0
search_with_results: int = 0

async def notify_clients():
    data = json.dumps(STATE)
    for q in clients:
        await q.put(data)

@app.on_event("startup")
async def startup():
    await init_cognee()
    global STATE
    STATE = await load_graph_from_cognee()
    print(f"Loaded {len(STATE['nodes'])} nodes, {len(STATE['links'])} links from Cognee")
    static_dir = os.path.join(os.path.dirname(__file__), "dashboard", "out")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="dashboard")
        print(f"Serving static dashboard from {static_dir}")

@app.get("/api/graph")
async def get_graph():
    return STATE

@app.get("/api/stream")
async def sse_stream(request: Request):
    q = asyncio.Queue()
    clients.append(q)
    await q.put(json.dumps(STATE))
    async def gen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield f"data: {data}\n\n"
        finally:
            clients.remove(q)
    return StreamingResponse(gen(), media_type="text/event-stream")

class MemoryEvent(BaseModel):
    title: str
    rationale: str
    files: list[str]
    tags: list[str]
    supersedes: Optional[str] = None

@app.post("/api/webhook/remember")
async def webhook_remember(event: MemoryEvent):
    text = f"Decision: {event.title}\nRationale: {event.rationale}\nImpacted Files: {', '.join(event.files)}\nTags: {', '.join(event.tags)}"
    if event.supersedes:
        text += f"\nSupersedes: {event.supersedes}"

    await cognee.remember(text, dataset_name=DATASET)
    global STATE
    STATE = await load_graph_from_cognee()
    await notify_clients()
    return {"status": "success"}

@app.post("/api/notify")
async def notify():
    global STATE
    STATE = await load_graph_from_cognee()
    await notify_clients()
    return {"status": "notified"}

class SessionEvent(BaseModel):
    text: str

@app.post("/api/remember/session")
async def remember_session(event: SessionEvent):
    await cognee.remember(event.text, dataset_name=SESSION_DATASET)
    global STATE
    STATE = await load_graph_from_cognee()
    await notify_clients()
    return {"status": "session_remembered"}

@app.post("/api/remember/promote")
async def promote_session(event: SessionEvent):
    await cognee.remember(event.text, dataset_name=DATASET)
    global STATE
    STATE = await load_graph_from_cognee()
    await notify_clients()
    return {"status": "promoted"}

@app.get("/api/sessions")
async def list_sessions():
    return {"session_dataset": SESSION_DATASET, "permanent_dataset": DATASET}

@app.get("/api/search")
async def search(query: str = Query(...), mode: str = "GRAPH_COMPLETION", after: Optional[str] = None, before: Optional[str] = None):
    try:
        st = SearchType(mode)
    except ValueError:
        st = SearchType.GRAPH_COMPLETION
    kwargs = {"query_text": query, "query_type": st, "datasets": [DATASET]}
    if after or before:
        kwargs["datetime_filter"] = {k: v for k, v in {"after": after, "before": before}.items() if v}
    t0 = time.perf_counter()
    results = await cognee.recall(**kwargs)
    latency = time.perf_counter() - t0
    search_latencies.append(latency)
    global search_total, search_with_results
    search_total += 1
    if len(results) > 0:
        search_with_results += 1
    return {"results": [{"text": getattr(r, "text", str(r)), "score": getattr(r, "score", None)} for r in results], "mode": mode}

@app.get("/api/search/modes")
async def search_modes():
    return {"modes": [{"id": m.value, "name": m.value.replace("_", " ").title()} for m in SearchType]}

@app.get("/api/metrics")
async def metrics():
    nc = len(STATE["nodes"])
    ec = len(STATE["links"])
    groups: dict[str, int] = {}
    for n in STATE["nodes"]:
        g = n.get("group", "other")
        groups[g] = groups.get(g, 0) + 1
    avg_latency = round(sum(search_latencies) / len(search_latencies), 3) if search_latencies else None
    recall_precision = round(search_with_results / search_total, 2) if search_total > 0 else None
    return {
        "nodes": nc,
        "edges": ec,
        "memory_composition": groups,
        "search_latency_ms": avg_latency,
        "recall_precision": recall_precision,
    }

class ForgetPreview(BaseModel):
    query: str

class ForgetConfirm(BaseModel):
    query: str

last_preview: dict = {"time": 0.0, "query": ""}

@app.post("/api/forget/preview")
async def forget_preview(body: ForgetPreview):
    results = await cognee.recall(query_text=body.query, datasets=[DATASET])
    matches = []
    for r in results:
        text = getattr(r, "text", str(r))
        node_id = getattr(r, "dataset_id", text[:40])
        matches.append({"id": node_id, "text": text[:200]})
    global last_preview
    last_preview = {"time": time.time(), "query": body.query}
    return {"matches": matches, "count": len(matches), "preview_valid_seconds": 60}

@app.post("/api/forget/confirm")
async def forget_confirm(body: ForgetConfirm):
    if os.environ.get("COGNEE_FORGET_ENABLED", "false") != "true":
        return {"error": "Forget is disabled. Set COGNEE_FORGET_ENABLED=true to enable."}
    global last_preview
    if time.time() - last_preview["time"] > 60:
        return {"error": "Preview expired. Call /api/forget/preview first."}
    if body.query != last_preview["query"]:
        return {"error": "Query mismatch. Call /api/forget/preview with the same query."}

    await cognee.forget(dataset=DATASET)
    last_preview = {"time": 0.0, "query": ""}

    global STATE
    STATE = await load_graph_from_cognee()
    await notify_clients()
    return {"status": "forgotten", "dataset": DATASET}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
