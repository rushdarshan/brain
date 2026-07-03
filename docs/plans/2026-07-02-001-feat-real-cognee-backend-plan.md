# Plan: ProjectBrain — Real Cognee Backend

**Date:** 2026-07-02
**Author:** ce-plan (orchestrator)
**Status:** Draft

## Origin

- `docs/brainstorms/2026-07-02-projectbrain-real-cognee-backend-requirements.md`

## Goal

Wire ProjectBrain to Cognee's real graph-vector backend across all 7 improvement ideas, prioritizing #1 (write-through cache). Ship a demo-ready submission by Jul 5, 2026.

## Scope

### In Scope

1. Dashboard mode selector + search — user picks any of 17 Cognee search modes from a dropdown, types a query, sees results
2. Dashboard SSE reconnection — auto-reconnect with exponential backoff, stale-data warning banner
3. Dashboard metadata panel — model used, node/edge counts, last cognify timestamp
4. Session memory — two-tier (session → permanent) with promote/demote API
5. Real metrics — node/edge counts, search latency percentile, memory composition breakdown
6. Dataset configuration — env var instead of hardcoded "paylink"
7. README rework — architecture diagram, setup, usage, judging criteria mapping
8. Demo video — screencast showing the complete flow
9. Submission — Devpost + blog post

### Out of Scope

- Multi-user auth (already disabled via `ENABLE_BACKEND_ACCESS_CONTROL=false`)
- User authentication / login system
- Mobile app
- Production deployment
- Unit tests (YAGNI for hackathon; demo is the deliverable)
- `reviewer_agent.py` expansion (already works for CI demo)

## Implementation Plan

### Dependencies Map

```
D1 (mode selector) ──► D2 (search UI) ──► D4 (metadata panel)
                         │
D3 (SSE reconnect) ──────┤
                         │
D6 (metrics real) ───────┤
                         │
D5 (session memory) ─────┼──► D7 (dataset config)
                         │
                         ▼
                    D8 (README) ──► D9 (demo video) ──► D10 (submission)
```

### Phase D1 — Dashboard Mode Selector + Search

**Goal:** User can pick any of 17 Cognee search modes from a dropdown and search the knowledge graph.

**Files to change:**
- `projectbrain\dashboard\src\components\GraphView.tsx` — Add mode selector dropdown, search input, results panel
- `projectbrain\dashboard\src\app\page.tsx` — If layout changes needed

**Contracts:**
- `GET /api/search/modes` returns `{ modes: [{ name: "GRAPH_COMPLETION", description: "..." }, ...] }`
- `GET /api/search?q=...&mode=GRAPH_COMPLETION` returns results array
- Mode selector dropdown fetched from `/api/search/modes` on mount
- Search input debounced 300ms
- Results rendered below the graph in a scrollable panel

**Edge cases:**
- Empty query → no search performed, mode selector still shows
- Backend down → dropdown shows "Backend unavailable" state
- No results → "No results found" message
- Long results → truncated with "Show more" expand

**Ponytail notes (pre-existing in api.py):**
- Mode descriptions are hardcoded strings, not dynamic from Cognee. Good enough for demo. Add from Cognee docs if time allows.

**Verification:**
- `npm run dev` starts without errors
- Mode selector renders with 17 options
- Each mode option returns results (or valid empty state)
- Graph View still renders alongside search

---

### Phase D2 — Dashboard SSE Reconnection + Stale-Data Warning

**Goal:** Dashboard automatically reconnects on SSE drop and shows a warning when graph data may be stale.

**Files to change:**
- `projectbrain\dashboard\src\components\GraphView.tsx`

**Contracts:**
- SSE `EventSource` reconnects with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- After reconnect, fetches fresh graph via `GET /api/graph`
- Warning banner shown when: (a) SSE disconnected > 5s, (b) last graph update > current session start
- Banner auto-dismisses on successful reconnect + data refresh
- Tooltip on banner explains what stale data means

**Edge cases:**
- Backend restarts → reconnect, refetch graph, dismiss banner
- Backend stays down → banner persists, polling every 30s
- First load (no prior SSE) → no banner

**Ponytail notes:**
- Using built-in `EventSource` reconnection behavior is enough; we add the banner as UX signal
- No need for WebSocket upgrade — SSE works fine for this use case

**Verification:**
- Stop `api.py` → banner appears within 5+1s
- Restart `api.py` → banner disappears within reconnect interval
- Graph data reloads on reconnect

---

### Phase D3 — Dashboard Metadata Panel

**Goal:** Show model info, node/edge counts, and last cognify timestamp in a sidebar or HUD overlay.

**Files to change:**
- `projectbrain\dashboard\src\components\GraphView.tsx` — Add metadata panel
- No API changes needed — `GET /api/metrics` already returns this data

**Endpoint contract** (already exists in `api.py`):
```json
{
  "llm_model": "groq/llama-3.3-70b-versatile",
  "embedding_model": "BAAI/bge-small-en-v1.5",
  "total_nodes": 42,
  "total_edges": 67,
  "last_cognify": "2026-07-02T12:00:00Z"
}
```

**Edge cases:**
- Metrics endpoint returns 200 with zero counts (no seed yet) → display "0 nodes, 0 edges"
- `last_cognify` null → display "Never"

**Verification:**
- Panel renders with correct data
- Zero-state displays correctly
- Data updates when graph changes

---

### Phase D4 — Session Memory

**Goal:** Two-tier memory that promotes session-level context to permanent knowledge.

**Files to change:**
- `projectbrain\api.py` — Add session context add/cognify, promote/demote endpoints
- `projectbrain\server.py` — Add `promote_context` tool
- `projectbrain\dashboard\src\components\GraphView.tsx` — Optional: session indicator

**New endpoints:**
- `POST /api/remember/session` — add content to session dataset, cognify
- `POST /api/remember/promote` — copy session item to permanent dataset, cognify
- `DELETE /api/remember/session/{id}` — demote/forget
- `GET /api/sessions` — list session vs permanent memories with counts

**Contracts:**
- Uses two datasets: `"paylink"` (permanent) and `"paylink-session"` (session)
- Session data shown with different color/style in graph
- Promote copies node text from session to permanent dataset, cognifies both
- Session dataset cleared on `server.py` restart (YAGNI: explicit clear endpoint)

**Edge cases:**
- Session dataset doesn't exist yet → create on first session add
- Promote targets a node that was already cognified → `cognee.add()` + `cognee.cognify()` handles dedup at text level
- Session node forgotten → `cognee.forget()` on the session item only

**Ponytail notes:**
- No separate DB for session metadata; graph node attributes carry session_id
- `cognee.add()` on the same text is idempotent (Cognee deduplicates by content hash)

**Verification:**
- Add item to session → graph shows new node in session color
- Promote session item → permanent dataset grows
- Demote/forget → node removed from graph view
- Server restart → session items gone, permanent items remain

---

### Phase D5 — Real Metrics

**Goal:** Replace hardcoded stub values in `/api/metrics` with live data from Cognee.

**Files to change:**
- `projectbrain\api.py` — Compute real metrics from graph state

**New computations:**
- `total_nodes` = `len(nodes)` from `get_memory_provenance_graph()`
- `total_edges` = `len(edges)` from same
- `memory_composition` = breakdown by node group (decision/incident/metric/file)
- `search_latency_ms` = recent search latency (rolling 10-window, stored in deque)
- `node_type_breakdown` = count per node type

**Edge cases:**
- No data seeded → all counts return 0, `last_cognify` null
- No searches performed → latency shows "N/A"

**Ponytail notes:**
- Rolling latency window stored in memory (module-level deque) — resets on restart. Good enough for demo.
- No persistent metrics store needed.

**Verification:**
- After seed: metrics show correct node/edge counts from actual graph
- After search: latency values appear
- After server restart: counts still match seed data (from graph), latency deque resets

---

### Phase D6 — Dataset Configuration

**Goal:** `"paylink"` dataset name configurable via env var instead of hardcoded.

**Files to change:**
- `projectbrain\api.py` — `DATASET_NAME = os.getenv("COGNEE_DATASET", "paylink")`
- `projectbrain\server.py` — Same
- `projectbrain\seed.py` — Same
- `projectbrain\reviewer_agent.py` — Same

**Contracts:**
- `COGNEE_DATASET` env var used everywhere; defaults to `"paylink"`
- Session dataset derived: `f"{DATASET_NAME}-session"`

**Edge cases:**
- Empty string → falls back to default
- Special characters → Cognee's own validation handles it

**Verification:**
- No env var set → uses "paylink" everywhere
- `$env:COGNEE_DATASET="testbrain"` → uses "testbrain" everywhere
- Session dataset becomes "testbrain-session"

---

### Phase D7 — README Rework

**Goal:** README that maps to all 6 judging criteria with clear setup, architecture, and demo instructions.

**Files to change:**
- `README.md` (create or overwrite)

**Sections:**
1. What is ProjectBrain — one-liner value prop
2. Architecture — ASCII diagram of api.py + server.py + dashboard + Cognee stores
3. Quick Start — 3-command setup
4. Features mapped to judging criteria (table)
5. What Cognee powers — graph, search, memory, feedback
6. Demo script — step-by-step what to show
7. Tech stack — one-liner per component

**Ponytail notes:**
- No CI for README rendering; review in editor or GitHub

**Verification:**
- README renders without broken links on GitHub
- Setup instructions work when followed cold

---

### Phase D8 — Demo Video

**Goal:** 3-4 minute screencast showing the complete flow.

**Approach:**
1. Start `api.py`, `seed.py`, `dashboard`
2. Show graph visualization with seed data
3. Search across modes (show 2-3 modes)
4. Session memory: add session item, promote to permanent
5. Show metrics panel updating
6. Show reviewer agent CI gate

**Tooling:** OBS Studio or built-in screen recorder (Xbox Game Bar on Windows).

**Verification:**
- Video plays, audio clear
- All 6 judging criteria visibly demonstrated
- Under 5 minutes

---

### Phase D9 — Submission

**Goal:** Devpost submission + optional blog post.

**Approach:**
1. Fill Devpost template: title, description, tech used, collaborators
2. Upload demo video to YouTube/Vimeo (unlisted)
3. Write brief blog post for projectbrain.dev or similar
4. Tag with Cognee, hackathon

**Verification:**
- Devpost link works
- Video link accessible
- Blog post readable

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Groq API key not set | High | Critical | Clear `.env.example` with instructions; first-time setup check in scripts |
| Cognee version breaking change | Low | High | Pinned to 1.2.2 in requirements; avoid edge APIs |
| Dashboard Next.js 16 breaking change | Medium | Medium | Consult `node_modules/next/dist/docs/` per AGENTS.md before any change |
| Dashboard mode selector has too many modes (17) | Medium | Low | Start with compact dropdown; scroll if needed |
| SSE + search state conflicts in UI | Low | Medium | Search results panel separate from graph; graph updates via SSE independently |
| Demo video too long | Medium | Medium | Script beforehand, time each segment |
| Session memory demo confusing | Medium | Low | Clear visual distinction (different colors) + tooltip explaining promote |

## Deferred Questions

1. **Promote UX in dashboard** — Should promote be a button on each session node, or a bulk "promote all" action? → **Decision: button per node** (simpler, more intuitive). Bulk promote if time allows.
2. **Dataset env var name** → `COGNEE_DATASET` consistent with Cognee's own `COGNEE_*` convention.
3. **Video hosting** → YouTube unlisted (free, reliable). Vimeo backup.
