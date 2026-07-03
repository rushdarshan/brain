---
title: refactor: Migrate ProjectBrain from Cognee v0.4 legacy API to v1.0 with full feature pipeline
type: refactor
status: active
date: 2026-07-02
origin: docs/brainstorms/2026-07-02-cognee-v1-migration-pipeline-requirements.md
---

# refactor: Migrate ProjectBrain to Cognee v1.0 API with full feature pipeline

## Overview

Migrate all 24 legacy API call sites in 4 files from `add()+cognify()+search()` to `remember()+recall()`, then layer on 6 v1.0-only features in dependency order: always-on improve(), truth-subspace reranking, temporal evolution slider, custom Pydantic DataModels, NodeSets, and MCP pipeline expansion.

---

## Requirements Trace

- R1. Replace every `add()`+`cognify()` pair with `remember()` across api.py, server.py, reviewer_agent.py, seed.py.
- R2. Replace every `search()` with `recall()`, with correct SearchType mappings.
- R3. improve() fires after every mutation (automatic: `remember(self_improvement=True)` does this).
- R4. CI reviewer uses truth-subspace reranking instead of keyword substring match.
- R5. CI workflow scores PR diffs by truth-subspace angular distance.
- R6. Backend temporal-scoped endpoint + frontend evolution slider wired to live data.
- R7. Replace GraphView.tsx hardcoded SEED_ITEMS with live API calls; re-enable SSE.
- R8. Define Pydantic DecisionModel and ReviewResult; typed write paths.
- R9. Query by field instead of text-prefix scanning.
- R10. Single dataset + per-node NodeSet tags; eliminate SESSION_DATASET.
- R11. Routing via NodeSet filter on recall() instead of parallel dataset.
- R12. MCP tools cover temporal, NodeSet, truth-subspace queries.
- R13. Remove HTTP notify dance — MCP calls Cognee directly.

---

## Scope Boundaries

- No multi-tenant auth (NodeSets = tagging, not ACL).
- Existing seed data migrated to new schema but content unchanged.
- Dashboard UI preserved except evolution slider integration.
- REST endpoints preserved for backward compat.
- `forget()` API unchanged (already v1.0 compatible).
- `get_memory_provenance_graph()` unchanged (still works in v1.0).

---

## Context & Research

### Relevant Code and Patterns

- **api.py**: 12 legacy call sites (4x add+cognify, 3x search, 1x forget, 1x improve)
- **server.py**: 7 legacy call sites (2x add+cognify, 1x search, 1x improve, 1x forget)
- **reviewer_agent.py**: 3 legacy call sites (1x add+cognify, 1x search)
- **seed.py**: 2 legacy call sites (1x add+cognify)

### Key v1.0 API Findings

| Legacy | v1.0 | Notes |
|--------|------|-------|
| `add()`+`cognify()` | `remember()` | `self_improvement=True` (default) auto-runs improve() |
| `search()` | `recall()` | Returns `list[RecallResponse]` instead of raw graph results |
| `improve()` | `improve(build_truth_subspace=True, ...)` | Same function, enhanced kwargs |
| `forget()` | `forget()` | Same signature — no change needed |
| `SearchType.KEYWORD` | `SearchType.CHUNKS_LEXICAL` | KEYWORD removed in v1.0 (broken currently) |
| `SearchType.TRUTH_SUBSPACE` | N/A — not a SearchType | Truth subspace = automatic hybrid retriever reranking when centroids exist |

### Truth Subspace (not a SearchType)

Truth subspace is a built-in reranking mechanism, not a separate search type. When `improve(build_truth_subspace=True, session_ids=...)` runs, it builds centroid vectors from session learnings. After that, the hybrid retriever (`SearchType.HYBRID_COMPLETION`) automatically applies `truth_factor(node_coords, query_coords)` which multiplies each result's score by 0.75–1.25 based on angular distance from the truth centroid. No special SearchType needed — just use `HYBRID_COMPLETION` after building the subspace.

---

## Key Technical Decisions

- **One-pass migration**: All 24 call sites changed atomically, not gradual wrapper.
- **remember() self-improvement handles R3**: `remember(self_improvement=True)` (default) already fires improve() after every write. No separate improve() call needed in write paths. The explicit `improve()` in server.py:45 becomes a no-op enhancement target (add `build_truth_subspace=True, session_ids=...`).
- **No SearchType.KEYWORD**: `review_history` and `reviewer_agent.py` currently use `SearchType.KEYWORD` which doesn't exist in v1.0 (currently broken). Replace with `CHUNKS_LEXICAL` for same behavior.
- **NodeSets strategy**: Add-time `remember(data, node_set=["session"])` tagging. Query-time filtering via `node_name` parameter or `scope` — verify exact mechanism during U4.
- **SSE keepalive**: `/api/stream` stays, just needs to fire after `remember()` calls via `notify_clients()` (already wired).
- **REST endpoints preserved**: `/api/webhook/remember`, `/api/remember/session`, `/api/remember/promote`, `/api/search`, `/api/forget/*`, `/api/review/history` all keep their signatures — only internals change.

---

## Implementation Units

### Phase 1: Keystone Migration

- U1. **Replace all add()+cognify() with remember() across 4 files**

**Goal:** Every write path uses `cognee.remember()` instead of the legacy two-step pattern.

**Requirements:** R1, R3

**Dependencies:** None

**Files:**
- Modify: `projectbrain/api.py` (8 call sites)
- Modify: `projectbrain/server.py` (4 call sites)
- Modify: `projectbrain/reviewer_agent.py` (2 call sites)
- Modify: `projectbrain/seed.py` (2 call sites)

**Approach:**
- `add(data) + cognify(datasets=[DS])` → `remember(data, dataset_name=DS)` (self_improvement=True by default)
- Remove the standalone `cognify()` calls — `remember()` handles both ingest and graph building
- `remember()` is async and returns `RememberResult` object — no callers use the return value so migration is transparent
- Remove `last_cognify_time` update code — remember() sets no equivalent, track elapsed from `RememberResult` if needed

**Test scenarios:**
- Happy path: Each endpoint returns same status shape after write
- Edge case: Empty text passed to remember() — Cognee handles gracefullly
- Error path: Cognee Cloud unreachable — exceptions propagate, maintain current error handling
- Integration: After `remember()` in webhook_remember, `load_graph_from_cognee()` returns updated graph

**Verification:**
- No `cognee.add()` or `cognee.cognify()` calls remain in any file
- All write endpoints (webhook, session, promote, seed, flag, add_review, MCP tools) respond 200

---

- U2. **Replace all search() with recall() across 4 files**

**Goal:** Every read path uses `cognee.recall()` with correct SearchType mappings.

**Requirements:** R2

**Dependencies:** U1

**Files:**
- Modify: `projectbrain/api.py` (3 search call sites: L169, L222, L262)
- Modify: `projectbrain/server.py` (1 search call site: L39)
- Modify: `projectbrain/reviewer_agent.py` (1 search call site: L13)

**Approach:**
- `search(query_text=..., query_type=..., datasets=[DS])` → `recall(query_text=..., query_type=..., datasets=[DS])`
- Response format changes from raw graph results to `list[RecallResponse]`. Each result has `.search_result` (text), `.dataset_id`, `.dataset_name` instead of raw `str(r)`.
- Mapping changes:
  - `str(r)` → `r.search_result`
  - `getattr(r, "score", None)` → `getattr(r, "score", None)` (verify if RecallResponse has score)
  - `getattr(r, "id", text[:40])` → `r.dataset_id` or `r.search_result`
- `SearchType.KEYWORD` → `SearchType.CHUNKS_LEXICAL` (KEYWORD doesn't exist in v1.0)
- `/api/search` endpoint: `recall()` results returned directly with text/score extraction
- `/api/forget/preview`: extract text from recall results for match preview
- `/api/review/history`: recall with CHUNKS_LEXICAL, then filter/parse results the same way

**Test scenarios:**
- Happy path: `/api/search?q=test` returns same shape results
- Edge case: Empty query string — recall returns empty list
- Edge case: `SearchType.KEYWORD` removed — CHUNKS_LEXICAL returns equivalent results
- Integration: review_history endpoint still parses review_result: prefix correctly from recall response format

**Verification:**
- No `cognee.search()` calls remain
- All search/recall endpoints return valid JSON
- Search type dropdown in frontend shows all v1.0 SearchTypes (including TEMPORAL)

---

- U3. **Wire improve() always-on with truth-subspace building**

**Goal:** improve() fires after every mutation, building truth subspace for reranking.

**Requirements:** R3, R4

**Dependencies:** U1

**Files:**
- Modify: `projectbrain/server.py` (L42-52, memify_feedback tool)
- Modify: `projectbrain/api.py` (add improve() after webhook_remember and other write endpoints)

**Approach:**
- `remember(self_improvement=True)` (the default U1 migration) already fires improve() automatically after every write — R3 is already satisfied by U1
- The explicit `improve(dataset=DATASET)` in `memify_feedback` (server.py:45) becomes the enhanced version with truth subspace:
  ```python
  await cognee.improve(
      dataset=DATASET,
      build_truth_subspace=True,
  )
  ```
- For truth subspace to produce reranking signal, `improve()` needs `session_ids` (truth subspace is built from session learnings). The `memify_feedback` tool receives a `decision_id` — can look up associated session_id or run without sessions (stage 3 only)
- If no session context: `improve(build_truth_subspace=True)` without session_ids still enriches graph but skips truth subspace building (truth subspace requires session_ids). This is fine — the CI reviewer will still get improved recall results

**Test scenarios:**
- Happy path: After write, graph has more cross-links (verify via `load_graph_from_cognee()`)
- Edge case: improve() called without session_ids — still runs enrichment, truth subspace skipped gracefully

**Verification:**
- `cognee.improve` callable without error
- Graph node/edge count increases after write+improve cycle

---

### Phase 2: Structured Memory

- U4. **Define Pydantic DataModels for decisions and reviews**

**Goal:** Typed Pydantic models replace f-string text blobs. Query by field instead of text-prefix scanning.

**Requirements:** R8, R9

**Dependencies:** U1

**Files:**
- Create: `projectbrain/models.py`
- Modify: `projectbrain/api.py` (all write/read paths to use typed models)
- Modify: `projectbrain/server.py` (MCP tools to use typed data)
- Modify: `projectbrain/reviewer_agent.py` (store/fetch ReviewResult as typed model)
- Modify: `projectbrain/seed.py` (use DecisionModel)

**Approach:**
- Define `DecisionModel(BaseModel)` with fields: `title`, `rationale`, `files`, `tags`, `supersedes`, `week`, `decision_id`
- Define `ReviewResult(BaseModel)` with fields: `score`, `timestamp`, `patterns_checked`, `patterns_found`, `passed`
- Pass models via `remember(data=model.model_dump(), dataset_name=DS)` — Cognee accepts dicts/DataItems, models serialize to dict
- For reading: `recall()` returns results; deserialize `search_result` field back into models using `DecisionModel.model_validate_json()` or parse from text
- Remove text-prefix scanning in `review_history` — instead query by field or use structured recall

**Patterns to follow:**
- Existing Pydantic models in api.py: `MemoryEvent`, `SessionEvent`, `ForgetPreview`, `ForgetConfirm`, `FlagPattern`

**Test scenarios:**
- Happy path: Write DecisionModel → read back via recall → fields match
- Happy path: review_history returns parsed ReviewResult objects instead of text-prefix parsed JSON
- Error path: Malformed model data — Pydantic validation catches it

**Verification:**
- No f-string text blobs used for knowledge ingestion
- review_history endpoint returns field-structured data

---

- U5. **Consolidate to single dataset with NodeSets**

**Goal:** Replace DATASET+SESSION_DATASET parallel with one dataset + NodeSet tags.

**Requirements:** R10, R11

**Dependencies:** U4 (needs typed models for query fields)

**Files:**
- Modify: `projectbrain/api.py` (remove SESSION_DATASET, add node_set to remember calls)
- Modify: `projectbrain/server.py` (pass node_set to MCP tools)

**Approach:**
- Keep `DATASET="paylink"` as single dataset
- Remove `SESSION_DATASET = f"{DATASET}-session"` and all references
- Pass `node_set=["session"]` for transient writes, omit for permanent writes
- For recall filtering: use `datasets=[DATASET]` and post-filter or use `scope` parameter
- Note: NodeSet query-time filtering may need verification — `recall()` doesn't expose a `node_set` parameter directly. Fallback: keep SESSION_DATASET but tag both with `node_set` for new writes; migrate reads once query-time filtering is confirmed

**Test scenarios:**
- Happy path: Write with node_set=["session"] → recall fetches from same dataset
- Edge case: No node_set specified → default behavior (permanent)

**Verification:**
- `SESSION_DATASET` removed from codebase
- All writes go to `DATASET` only

---

### Phase 3: Advanced Features

- U6. **Truth-subspace CI reviewer**

**Goal:** reviewer_agent.py uses `recall(query_type=HYBRID_COMPLETION)` with truth-subspace reranking instead of `SearchType.KEYWORD` substring matching.

**Requirements:** R4, R5

**Dependencies:** U2, U3 (need improve() building truth subspace)

**Files:**
- Modify: `projectbrain/reviewer_agent.py` (search type, scoring algorithm)
- Modify: `.github/workflows/projectbrain-review.yml` (if scoring thresholds change)

**Approach:**
- Replace `search(query_type=SearchType.KEYWORD, ...)` with `recall(query_type=SearchType.HYBRID_COMPLETION, ...)`
- The hybrid retriever automatically applies `truth_factor()` from truth-subspace centroids when they exist, reranking results toward past validated knowledge
- Score calculation: if recall returns results with high truth-subspace alignment (nodes close to centroid), the PR diff shares patterns with past validated decisions → approved. If low alignment (novel patterns), flagged for review
- Current scoring: `score = (total - found) / total` where found = pattern matches. New scoring: use truth_factor scores from recall results
- Remove `SearchType.KEYWORD` import (no longer exists)

**Test scenarios:**
- Happy path: Known-deprecated pattern detected with high relevance score
- Edge case: No truth subspace built yet — HYBRID_COMPLETION falls back to standard search
- Error path: recall() times out — maintain current sys.exit(2) pattern

**Verification:**
- `SearchType.KEYWORD` removed from reviewer_agent.py
- `SearchType.HYBRID_COMPLETION` imported and used

---

- U7. **Temporal evolution slider**

**Goal:** Backend endpoint for time-windowed recall + frontend GraphView.tsx using live API data.

**Requirements:** R6, R7

**Dependencies:** U1, U2

**Files:**
- Modify: `projectbrain/api.py` (new `/api/evolution` endpoint)
- Modify: `projectbrain/dashboard/src/components/GraphView.tsx` (replace SEED_ITEMS, wire SSE)

**Approach:**
- New backend endpoint: `GET /api/evolution?start=<ISO>&end=<ISO>` calls `recall(query_type=SearchType.TEMPORAL)` with time-scoped query
- Temporal search in Cognee v1.0: `recall(query_text=..., query_type=SearchType.TEMPORAL, ...)` — uses time-aware retrieval
- Frontend: Remove hardcoded `SEED_ITEMS` array. GraphView fetches from `/api/graph` (existing) for full view, or from `/api/evolution` for time-windowed view
- Re-enable SSE connection: GraphView subscribes to `/api/stream` and updates on new graph data
- The evolution slider dispatches temporal queries; on each position change, fetch `/api/evolution` with the time window

**Test scenarios:**
- Happy path: `/api/evolution?start=W1&end=W4` returns graph state for weeks 1-4
- Edge case: No temporal data exists — returns empty graph
- Integration: Slider change triggers graph re-render without full page reload

**Verification:**
- GraphView.tsx has no hardcoded seed data
- SSE connection active and graph updates on new remembers

---

- U8. **MCP v1.0 pipeline expansion**

**Goal:** MCP tools cover full v1.0 surface. Remove HTTP notify dance.

**Requirements:** R12, R13

**Dependencies:** U1-U7

**Files:**
- Modify: `projectbrain/server.py` (all MCP tools)

**Approach:**
- Add temporal query tool: `recall_context(query, mode="TEMPORAL", ...)` accepts `SearchType.TEMPORAL`
- Add NodeSet-aware tool: `remember_decision(..., node_set=["permanent"])` passes node_set to remember()
- Add truth-subspace tool: `memify_feedback(..., build_truth_subspace=True)` triggers truth subspace build
- Remove `httpx.notify()` calls from each tool — MCP calls Cognee directly via import, no need to notify the REST server
- Existing REST endpoints preserved for backward compat (the REST server and MCP server can run independently)

**Test scenarios:**
- Happy path: MCP tool `remember_decision` writes via remember() without HTTP notify
- Happy path: `recall_context(query, mode="TEMPORAL")` returns time-aware results
- Integration: REST endpoints and MCP tools both write to same Cognee dataset

**Verification:**
- No `httpx.AsyncClient()` or `API_URL` references in server.py
- All MCP tools call `cognee.remember()` or `cognee.recall()` directly

---

## System-Wide Impact

- **Error propagation**: `remember()` raises on Cognee Cloud failure (same as add+cognify). Existing exception handling in endpoints should catch at the same boundary.
- **State lifecycle**: `remember(self_improvement=True)` takes longer than add+cognify because it runs improve() after cognify. Write endpoints may see higher latency.
- **API surface parity**: REST endpoints keep same signatures. Response format for `/api/search` changes slightly (recall response vs search response) — frontend consuming this endpoint needs verification.
- **Unchanged invariants**: `forget()` unchanged. `get_memory_provenance_graph()` unchanged. SSE streaming unchanged. CI workflow triggers unchanged.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `remember()` + `improve()` doubles latency per write | Acceptable for hackathon; optimize by setting `self_improvement=False` on high-frequency paths later |
| Recall response format differs from search — frontend breaks | Verify `/api/search` response shape matches frontend expectations |
| `SearchType.KEYWORD` broken in existing codebase (v1.0 removed it) | Already broken — CHUNKS_LEXICAL restores functionality |
| NodeSet query-time filtering unclear in v1.0 API | Fallback: keep SESSION_DATASET for reads, apply NodeSets for new writes only |
| Cloud client delegates to remote — local verification may differ from deployed behavior | Test locally with `connect()` disabled for unit testing; deploy to Railway for full verification |
| Seed data re-ingestion with new models duplicates existing paylink data | Truncate dataset via `cognee.forget(dataset=DATASET)` before re-seeding, or seed to a fresh dataset |

---

## Sources & References

- **Origin document:** `docs/brainstorms/2026-07-02-cognee-v1-migration-pipeline-requirements.md`
- **Ideation artifact:** `docs/ideation/2026-07-02-cognee-features-ideation.md`
- **Cognee v1.0 API source:** `cognee/api/v1/remember/remember.py`, `cognee/api/v1/recall/recall.py`, `cognee/api/v1/improve/improve.py`, `cognee/api/v1/forget/forget.py`
