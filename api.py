import asyncio, json, os, time
from collections import deque
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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

STATE: dict = {"nodes": [], "links": []}

async def load_graph_from_cognee():
    """Build graph state from seed items (Cognee Cloud has no local node enumerator)."""
    from seed import seed_items
    nodes, links, file_ids, node_ids = [], [], {}, {}
    for item in seed_items:
        nid = f"decision:{item['title'].lower().replace(' ', '-')}"
        node_ids[item['title']] = nid
        group = "incident" if "incident" in item.get("tags", []) else "decision"
        nodes.append({"id": nid, "name": item["title"], "group": group, "val": 20})
        for f in item.get("files", []):
            fid = f"file:{f.lower().replace('/', '-')}"
            if fid not in file_ids:
                file_ids[fid] = True
                nodes.append({"id": fid, "name": f, "group": "file", "val": 10})
            links.append({"source": nid, "target": fid, "name": "LINKS_TO"})
    for item in seed_items:
        if item.get("supersedes") and item["supersedes"] in node_ids:
            links.append({"source": node_ids[item["supersedes"]], "target": node_ids[item["title"]], "name": "SUPERSEDES"})
    return {"nodes": nodes, "links": links}
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
        from fastapi.responses import FileResponse
        @app.get("/", include_in_schema=False)
        async def serve_root():
            return FileResponse(os.path.join(static_dir, "index.html"))
        @app.get("/{path:path}", include_in_schema=False)
        async def serve_spa(path: str):
            file_path = os.path.join(static_dir, path or "index.html")
            resolved = os.path.abspath(file_path)
            if resolved.startswith(os.path.abspath(static_dir)) and os.path.isfile(resolved):
                return FileResponse(resolved)
            return FileResponse(os.path.join(static_dir, "index.html"))
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
async def search(q: str = Query(...), mode: str = "GRAPH_COMPLETION", after: Optional[str] = None, before: Optional[str] = None):
    try:
        st = SearchType(mode)
    except ValueError:
        st = SearchType.GRAPH_COMPLETION
    kwargs = {"query_text": q, "query_type": st, "datasets": [DATASET]}
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
    def rget(r, key, default=""):
        if isinstance(r, dict):
            return r.get(key, r.get("dataset_id" if key == "id" else key, default))
        return getattr(r, key, default)
    return {"results": [{"text": rget(r, "text", ""), "score": rget(r, "score", None), "node_id": rget(r, "id", None)} for r in results], "mode": mode}

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
    def rget(r, key, default=""):
        return r[key] if isinstance(r, dict) else getattr(r, key, default)
    for r in results:
        text = rget(r, "text", str(r))
        node_id = rget(r, "dataset_id", text[:40])
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

@app.post("/api/seed")
async def seed_graph():
    global STATE
    from seed import seed_items
    texts = []
    for item in seed_items:
        text = f"Decision: {item['title']}\nRationale: {item['rationale']}\nImpacted Files: {', '.join(item['files'])}\nTags: {', '.join(item['tags'])}\nWeek: {item['week']}"
        if item["supersedes"]:
            text += f"\nSupersedes: {item['supersedes']}"
        texts.append(text)
    await cognee.remember(texts, dataset_name=DATASET)
    STATE = await load_graph_from_cognee()
    await notify_clients()
    return {"status": "seeded", "count": len(texts), "dataset": DATASET}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
