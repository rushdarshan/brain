---
date: 2026-07-02
topic: cognee-features
focus: Which unused Cognee features (improve(), truth-subspace reranking, temporal mode, NodeSets, custom DataModels, MCP server) to exploit in ProjectBrain
mode: repo-grounded
---

# Ideation: Exploiting Unused Cognee Features in ProjectBrain

## Grounding Context

**Codebase Context:** ProjectBrain — Python backend (FastAPI + Cognee v0.4 legacy API), Next.js/React frontend (dashboard with D3 force-graph). Key files: `server.py` (Cognee init, 5 MCP tools on legacy API), `api.py` (15 REST endpoints), `reviewer_agent.py` (34-line keyword matcher), `GraphView.tsx` (evolution slider using hardcoded SEED_ITEMS), `seed.py` (weeks 1-8 seed data).

**Defects found:**
- `server.py:44-45`: `improve()` called but silently no-ops on v0.4 pipeline
- `api.py:176`: `getattr(r, "score", None)` — no reranking engine wired, all scores None
- `reviewer_agent.py:21-24`: `"deprecated:"` text-prefix parsing, no schema
- `api.py:262-271`: O(n) scan checking `startswith("review_result:")` + json.loads with `except: pass`
- `GraphView.tsx:67`: SSE stream killed when evolution mode enabled
- `server.py:23-26,47-49,59-62`: HTTP notify dance to api.py, all wrapped in `try/except Exception: pass`
- 8 call sites of `cognee.add()+cognify()` across `server.py`, `api.py`, `reviewer_agent.py`, `seed.py` — all legacy v0.4 API

**6 unused Cognee v1.0 features:** improve(), truth-subspace reranking, temporal mode (SearchType.TEMPORAL), NodeSets, Custom DataModels, MCP server. All require migration to v1.0 API.

**External context:** Cognee docs confirm improve() enriches graphs, bridges session memory, applies feedback weights, builds global context index. Truth-subspace, temporal mode, NodeSets, and DataModels all have confirmed implementation patterns in v1.0 API.

## Ranked Ideas

### 1. Migrate legacy API to v1.0 remember()+recall()+improve()
**Description:** Replace every `cognee.add()+cognify()` with `cognee.remember()`, every `cognee.search()` with `cognee.recall()`, and wire `cognee.improve()` into the feedback path. This is the keystone for ALL 6 unused features — zero of them work without it. ~30 lines changed across 8 call sites in 4 files.
**Warrant:** `direct:` 8 call sites of cognee.add/cognify across server.py, api.py, reviewer_agent.py, seed.py; server.py:44-45 calls improve() which silently no-ops on v0.4 pipeline
**Rationale:** Every unused feature is gated behind this migration. One focused commit unlocks the entire Cognee v1.0 feature surface. Current approach (add()+cognify()+search()) is the v0.4 API that v1.0 deprecated.
**Downsides:** Requires updating all call sites simultaneously; need to verify remember()+recall() signatures match current pattern; may need to update data format for v1.0 ingestion
**Confidence:** 95%
**Complexity:** Medium — mechanical changes across 4 files, but each call site is a 2-line replace. Testing required.
**Status:** Explored

### 2. Wire improve() as the auto-enrichment engine (always-on)
**Description:** Run `improve()` after every mutation, not just on manual upvote. This enriches the graph with summary nodes, bridges session→permanent memory via feedback weights, and builds the global context index. improve() directly replaces the entire manual auto-review loop the project was built for.
**Warrant:** `direct:` server.py:44-45 calls improve() inside memify_feedback but it silently no-ops on v0.4; `reasoned:` Cognee docs confirm improve() enriches graphs, bridges session memory, applies feedback weights, builds global context index — precisely what ProjectBrain's manual loop does
**Rationale:** This is the #1 highest-leverage feature. improve() IS the "self-improving knowledge graph" the entire project thesis claims. Currently the thesis is theater — improve() is wired to a single MCP tool that fires only on manual upvote.
**Downsides:** Must be paired with migration (idea #1); improve() adds latency per operation if synchronous; unclear whether multiple rapid improve() calls compound or conflict
**Confidence:** 90%
**Complexity:** Medium — depends on idea #1; after that, adding `await cognee.improve()` to the mutation handler is ~3 lines
**Status:** Explored

### 3. Truth-subspace reranking replaces keyword reviewer_agent
**Description:** Replace the 34-line keyword matcher with truth-subspace reranked recall. The CI reviewer becomes: `cognee.recall(diff_text, search_type=SearchType.TRUTH_SUBSPACE)` → score by proximity to the truth centroid (weighted center of confirmed decisions). Catches novel anti-patterns that share zero vocabulary with past deprecations.
**Warrant:** `direct:` reviewer_agent.py:10-28 — keyword matching is the weakest part, cannot detect semantic similarity; api.py:176 — `getattr(r, "score", None)` returns no scores because no reranker is wired
**Rationale:** Keyword matching has zero generalization — adding a new deprecation pattern requires code change. Truth-subspace reranking makes scoring semantic by default. Combined with improve(), the feedback flywheel becomes: improve() feeds subspace → subspace ranks results → ranked results get confirms → stronger improve().
**Downsides:** Truth-subspace is experimental in some Cognee builds; may not work with installed version. Threshold calibration needed for CI pass/fail.
**Confidence:** 80%
**Complexity:** Medium — depends on idea #1 for v1.0 API. Reviewer_agent logic change is ~15 lines; CI integration (GitHub Actions workflow) is the harder part.
**Status:** Explored

### 4. Temporal mode makes the evolution slider query the live graph
**Description:** Replace the hardcoded SEED_ITEMS constant and SSE-stream kill with real temporal queries: `cognee.recall(temporal_range=(start, end))`. The evolution slider becomes a time machine over real artifact history. Seed.py becomes a one-time import instead of the slider's data source.
**Warrant:** `direct:` GraphView.tsx:67 — `if (showEvolution) return;` kills SSE; GraphView.tsx:17-38 — SEED_ITEMS hardcoded constant; seed.py:40-50 — week embedded as text field
**Rationale:** The evolution slider is the dashboard's most visually prominent feature but is completely disconnected from the live graph. Temporal mode makes it show actual graph state at each time window — new decisions automatically appear in the correct week.
**Downsides:** Requires idea #1 (v1.0 API) + Cognee's temporal mode to index timestamps. GraphView.tsx refactor to load from API instead of constant. Per-slider-position requests may need batching.
**Confidence:** 75%
**Complexity:** High — touches backend (new temporal API endpoint) and frontend (replace SEED_ITEMS with API calls, re-enable SSE during evolution mode)
**Status:** Explored

### 5. Custom DataModels replace all text-prefix hacks
**Description:** Define Pydantic `DecisionModel(title, rationale, files, tags, supersedes, week)` and `ReviewResult(score, patterns_checked, passed)` typed nodes. Every write instantiates the schema instead of building f-string text blobs. No more `"review_result:" + json.dumps()`, no more `"deprecated:" + text`, no more `"Week: 3"` substring parsing.
**Warrant:** `direct:` api.py:262-271 — entire review_history endpoint scans all nodes checking startswith("review_result:") + json.loads with pass-on-error; reviewer_agent.py:37-38 — json.dumps into text field; seed.py:43-48 — f-string text blob building
**Rationale:** Currently the graph is an opaque string store — you cannot query "all decisions with severity > 5" or "decisions impacting api.py" because fields are buried in unstructured text. Custom DataModels make the graph introspectable by field and eliminate an entire class of parse-error bugs.
**Downsides:** Requires idea #1 (v1.0 API supports DataModels). Migration of existing data (weeks 1-8 seed + any existing review results) to new schema. Changes MCP tool and REST endpoint signatures (breaking change).
**Confidence:** 85%
**Complexity:** Medium-High — schema definition is ~20 lines; migration of all read/write paths in api.py, server.py, reviewer_agent.py, and seed.py
**Status:** Explored

### 6. NodeSets replace the two-dataset architecture and text-prefix tagging
**Description:** Replace DATASET+SESSION_DATASET with a single dataset + per-node NodeSet tags (session/permanent, security/database/auth, active/superseded). Eliminate 4 duplicate endpoints, the promote_context tool, and the scope-switching complexity. Edge filter in GraphView becomes a server-side NodeSet query instead of O(n) JS post-filter.
**Warrant:** `direct:` api.py:13-14 — SERVER_DATASET and SESSION_DATASET; duplicate /remember/session, /remember/promote endpoints; GraphView.tsx:360-369 — edge filter is O(n) JS post-filter (cosmetic only)
**Rationale:** The current two-dataset model is a manual hardcoded approximation of what NodeSets provide natively. Every new category requires new env vars + endpoints. NodeSets let each node join multiple sets, so improve() discovers cross-category relationships.
**Downsides:** Requires ideas #1 and #5. Migration of all existing dataset references. Breaking change to MCP tool and endpoint signatures.
**Confidence:** 70%
**Complexity:** High — requires ideas #1 and #5 first; touches all data ingestion paths, both API layers, and the dashboard edge filter
**Status:** Explored

### 7. MCP server as the primary agent interface with full v1.0 pipeline
**Description:** Expand the MCP server from 5 CRUD tools to full v1.0 surface: temporal, NodeSet, truth-subspace, improve, graph-snapshot tools. The REST API (FastAPI) shrinks to serving only the static dashboard. MCP calls Cognee directly instead of the current pattern (MCP → Cognee, HTTP-notify → REST → Cognee again).
**Warrant:** `direct:` server.py:15-68 — 5 MCP tools all use legacy API; server.py:23-26,47-49,59-62 — HTTP notifications to api.py (duplicate work wrapped in silently-failing HTTP); `reasoned:` every v1.0 feature (temporal, NodeSets, subspaces, improve) has an async API callable from MCP handlers
**Rationale:** Currently MCP is a sidecar that duplicates REST functionality. Making MCP the primary agent interface with direct Cognee calls eliminates the notify-dance (12 lines of try/except/pass), reduces latency (no HTTP hop), and gives LLM clients the full pipeline without HTTP ceremony.
**Downsides:** Requires ideas 1-6 (MCP is the delivery layer). Breaking change to existing MCP tool signatures.
**Confidence:** 65%
**Complexity:** High — depends on all previous ideas. Pure additive beyond those, but server.py refactor is ~50 lines of deletion.
**Status:** Explored

## Dependency Chain
```
1. v1.0 API migration (keystone)
├── 2. improve() always-on
├── 3. Truth-subspace reviewer
├── 4. Temporal evolution slider
├── 5. Custom DataModels
│   └── 6. NodeSets (depends on 1+5)
└── 7. MCP v1.0 pipeline (depends on all)
```

Start at #1. Each subsequent idea becomes unlockable once #1 is done.

## Rejection Summary

| # | Idea | Frame | Reason Rejected |
|---|------|-------|----------------|
| 1 | Prerequisite-Tree Retrieval via Truth-Subspace | F5 | Too speculative; Cognee subspace doesn't support DAG prerequisite enforcement |
| 2 | Transit-Timetable Temporal Mode | F5 | "Predict next access time" requires building a prediction model, not available |
| 3 | Kanban-Pull NodeSets | F5 | NodeSets don't provide pre-fetch mechanisms |
| 4 | Portfolio-Rebalancing via improve()+NodeSets | F5 | Periodic maintenance not available in Cognee |
| 5 | Mycelium MCP Network | F5 | Multi-agent exchange doesn't exist in Cognee's MCP |
| 6 | Zoning Ordinances via Custom DataModels | F5 | DataModels don't enforce relationship-type constraints |
| 7 | Editorial-Gate via Custom DataModels | F5 | Duplicates stronger #5 with less actionable framing |
| 8 | Immune-System Memory via improve() | F5 | Duplicates "always-on improve()" with biological framing |
| 9 | Forget Is a Lie (Temporal Tombstones) | F6 | Temporal mode already provides versioned nodes |
| 10 | NodeSets as Auth Boundaries (100 Agents) | F6 | NodeSets don't provide auth; requires multi-tenant infra |
| 11 | Dashboard Amnesty (Delete FastAPI) | F6 | Unrealistic; better captured by idea #7 |
| 12 | Truth-Subspace Scores Drive Graph Viz | F3 | Low impact for effort; cosmetic only |
| 13 | Graph Improvements as First-Class Nodes | F2 | Cognee improve() doesn't materialize visible nodes |
| 14 | MCP Shovel not Telescope | F1 | Fix is implementing other features; covered by #7 |
| 15 | Auto-forget via improve()+temporal | F2 | Overlaps with temporal tombstones (#9) and slider (#4) |
