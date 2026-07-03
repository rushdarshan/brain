---
title: Fix critical bugs before Devpost submission
type: fix
status: active
date: 2026-07-02
---

# Fix critical bugs before Devpost submission

## Overview

During the explore session, 14 distinct issues were identified across the codebase. Some are already fixed in a `feat/cognee-v1-migration` worktree; others affect CI/CD, the dashboard, and API correctness. This plan applies the existing worktree fixes via patch and addresses all remaining disqualifying and high-impact bugs before the Jul 5, 2026 hackathon submission deadline.

---

## Problem Frame

The project has bugs at 3 severity levels:

- **P0 (disqualifying):** A judge testing the system will see immediate failures. `improve()` returns success but does nothing. CI/CD pipeline always fails at install. `forget()` either crashes or wipes the entire dataset.
- **P1 (demo-corrupting):** Dashboard displays static/hardcoded values as if they were live metrics. Search results have no link back to the graph. The track_review endpoint never increments.
- **P2 (credibility-eroding):** The "self-improvement" visual narrative is pure theater (hardcoded decay values). No live demo URL forces judges to clone and configure.

The worktree at `feat/cognee-v1-migration` already fixes P0-level API calls (`improve()` args, `remember()`/`recall()` migration, `search()` → `recall()`) and cleans stale metrics state. These need to reach master promptly.

---

## Requirements Trace

- R1. All Cognee v1.0 API calls use correct method signatures (`remember`, `recall`, `improve`, `forget`)
- R2. CI/CD pipeline installs cognee correctly and runs the reviewer agent on every PR
- R3. `forget()` removes specific memories — never silently wipes the entire dataset
- R4. Dashboard metrics display only live, accurate values — never hardcoded theater or stale fields
- R5. Search results include node provenance (node ID, dataset) so the dashboard can link results back to graph nodes
- R6. Live demo URL at Railway so judges can interact without local setup

---

## Scope Boundaries

- Fixing the `track_review` endpoint properly (it's being removed — reviews are tracked implicitly by the chat feedback workflow)
- Building before/after self-improvement score visualizations (deferred — requires runtime data collection)
- Recording the demo video or writing the Devpost entry (separate workflow — this plan is only code fixes)
- Dashboard MCP tool surface (buttons to call MCP tools from browser — separate feature, not a bug fix)

---

## Context & Research

### Relevant Code and Patterns

- `projectbrain/api.py` — 247 lines, FastAPI backend with 14 endpoints. Current master branch uses `cognee.add()`, `cognee.cognify()`, `cognee.search()`, `cognee.improve()` with wrong signatures. Worktree branch corrects all of these.
- `projectbrain/server.py` — 60 lines, FastMCP server with 5 tools. Worktree fixes `improve()` and removes stale `httpx` notify calls.
- `projectbrain/reviewer_agent.py` — 41 lines, PR review agent. Worktree fixes `search()` → `recall()` with `r.text` extraction.
- `projectbrain/seed.py` — 56 lines, seed data. Worktree fixes `add()+cognify()` → `remember()`.
- `projectbrain/dashboard/src/components/GraphView.tsx` — 329 lines, main dashboard component. Renders `review_accuracy` which is removed by worktree API fix.
- `.github/workflows/projectbrain-review.yml` — 31 lines, CI workflow. Uses `pip install cognee` which always fails.

### Institutional Learnings

- The `docs/ideation-pain-friction.md` document was produced in explore mode and documents all 14 issues in detail.
- The `feat/cognee-v1-migration` worktree covers 5 files with the core API migration. The branch is not committed — changes are unstaged.

### External References

- Cognee v1.2.2 is installed. API: `remember()`, `recall()`, `improve(dataset=..., build_truth_subspace=True)`, `forget(dataset=...)`.
- Cognee is published on GitHub only: `pip install git+https://github.com/topoteretes/cognee`
- Railway deployment: Dockerfile + railway.json already exist in `projectbrain/`, not yet deployed.

---

## Key Technical Decisions

- **Merge worktree by applying the diff to master** — The worktree contains unstaged changes. Rather than committing in the worktree and merging from the `feat/` branch, apply the same changes directly to master via patch. This avoids bringing untracked artifacts (`docs/`, `opencode.json`) into master.
- **Remove review_accuracy from dashboard** — The `track_review` endpoint has no downstream consumer and its metrics (`review_total`, `review_approved`) were never written correctly. Remove the endpoint and the dashboard display rather than fixing a feature nobody uses.
- **forget() preserves data by default** — The current API wipes the entire dataset. Change to require explicit `confirm=True` parameter and default to a no-op when called without it. Add a `forget_memory(memory_id)` path for per-node deletion using Cognee's `memory_id` parameter.

---

## Implementation Units

---

- U1. **Merge Cognee v1.0 API migration from worktree to master**

**Goal:** Apply the 5-file migration (api.py, server.py, seed.py, reviewer_agent.py, models.py) from the `feat/cognee-v1-migration` worktree to master, fixing all deprecated Cognee v0.4 API calls.

**Requirements:** R1

**Dependencies:** None

**Files:**
- Modify: `projectbrain/api.py`
- Modify: `projectbrain/server.py`
- Modify: `projectbrain/reviewer_agent.py`
- Modify: `projectbrain/seed.py`
- Create: `projectbrain/models.py`

**Approach:**
- Generate a patch from the worktree diff, apply to master branch
- Specifically: `git diff` in worktree → apply to master via `git apply` or manual application
- Verify each changed file still syntax-checks with `python -c "import ast; ast.parse(open('...').read())"`
- Do NOT bring over `docs/` or `opencode.json`
- Remove hardcoded Cognee Cloud API key from `projectbrain/cognee_init.py` (currently `os.environ.get("COGNEE_API_KEY", "<real-key>")` — the fallback is a live production key). Change to `os.environ["COGNEE_API_KEY"]` so it raises an error if unset. This prevents the production tenant from being exposed in every clone.

**Test scenarios:**
- Happy path: `python -c "import ast; ast.parse(open('projectbrain/api.py').read())"` succeeds for all 5 Python files (including new `models.py`)
- Happy path: `import cognee` then `cognee.remember`, `cognee.recall`, `cognee.improve`, `cognee.forget` all resolve
- Edge case: `GET /api/metrics` returns JSON without `review_accuracy`, `last_cognify`, or `memory_staleness` fields
- Edge case: `GET /api/search/modes` lists available SearchType values

**Verification:**
- All 5 Python files pass `ast.parse` (including new `models.py`)
- `api.py` starts without import errors (`python projectbrain/api.py` for 3 seconds then Ctrl+C)
- `server.py` same

---

- U2. **Fix CI/CD pipeline**

**Goal:** The GitHub Actions workflow installs cognee correctly and the reviewer agent can query the knowledge graph.

**Requirements:** R2

**Dependencies:** U1 (reviewer_agent.py must use correct API)

**Files:**
- Modify: `.github/workflows/projectbrain-review.yml`

**Approach:**
- Change `pip install cognee` to `pip install git+https://github.com/topoteretes/cognee`
- Also install `litellm` (same way — it's needed for Cognee LLM integration)
- Add `pip install python-dotenv` for .env loading
- Add `COGNEE_API_KEY` and `COGNEE_API_URL` as required secrets (alongside existing `GROQ_API_KEY`) — the reviewer agent needs all three to connect to Cognee Cloud
- Document all three required secrets (`GROQ_API_KEY`, `COGNEE_API_KEY`, `COGNEE_API_URL`) as comments at the top of the workflow file
- Add a CI step that validates required secrets are set before running the reviewer agent: `if: env.GROQ_API_KEY != '' && env.COGNEE_API_KEY != ''`

**Test scenarios:**
- Happy path: Workflow YAML is valid syntax (`python -c "import yaml; yaml.safe_load(open(...))"` — or just git add + push dry-run)
- Happy path: After merge, the next PR triggers the workflow and installs successfully

**Verification:**
- Workflow YAML is parseable
- Comment documents the required `GROQ_API_KEY` repository secret

---

- U3. **Fix forget() — safe API with per-node deletion support**

**Goal:** The `forget` MCP tool and REST endpoint never wipe the entire dataset unintentionally. Support per-memory deletion.

**Requirements:** R3

**Dependencies:** U1

**Files:**
- Modify: `projectbrain/server.py` (MCP `forget` tool)
- Modify: `projectbrain/api.py` (REST `/api/forget/confirm` endpoint)

**Approach:**
- **MCP tool (server.py):** Change `forget(node_id, cascade)` to `forget_memory(data_id, cascade=False)`. Pass `data_id` (a UUID string from the graph node) to `cognee.forget(data_id=UUID(data_id), cascade=cascade)` instead of `dataset=DATASET`. If `data_id` is empty, return error message instead of defaulting to dataset wipe. Cognee's `forget()` signature: `forget(*, data_id: UUID | None, dataset: str | None, ...)`.
- **REST API guard (api.py):** Add `COGNEE_FORGET_ENABLED` env var check to `/api/forget/confirm`. If `os.environ.get("COGNEE_FORGET_ENABLED", "false") != "true"`, return 403 with "Forget is disabled on this instance." This prevents accidental dataset wipes on the public Railway URL.
- **REST API (api.py):** The existing `/api/forget/confirm` already has a safety gate (preview + 60s expiry). Keep the cognee call as `forget(dataset=DATASET)` — dataset-level forget is an intentional admin action behind the preview/confirm flow. The REST endpoint is the "nuke" button with 2-step confirmation; the MCP tool is the "surgical" path.

**Patterns to follow:**
- Existing preview/confirm pattern in `api.py:209-243` (safety gate pattern)

**Test scenarios:**
- Happy path: `forget_memory(data_id="550e8400-e29b-41d4-a716-446655440000")` calls `cognee.forget(data_id=UUID(...))` without touching other data
- Error path: `forget_memory(data_id="")` returns error message, does not call cognee at all
- Error path: `forget_memory(data_id="not-a-uuid")` catches `ValueError` from `UUID()` and returns descriptive error
- Integration: Existing `/api/forget/preview` + `/api/forget/confirm` flow still works with dataset-level forget
- Edge case: Non-existent data_id returns appropriate error (cognee handles this)

**Verification:**
- MCP tool signature is `forget_memory(data_id: str, cascade: bool = False)`
- REST endpoint safety gate still requires preview before confirm

---

- U4. **Clean up dashboard stale metrics and remove theater**

**Goal:** Dashboard displays only live, accurate metrics. Hardcoded "hebbian decay" values and references to removed API fields are eliminated.

**Requirements:** R4

**Dependencies:** U1 (removes `review_accuracy` from API response)

**Files:**
- Modify: `projectbrain/dashboard/src/components/GraphView.tsx`

**Approach:**
- Remove line rendering `review_accuracy` from the metrics bar (line 193: `{metrics.review_accuracy && ...}`)
- Add null-safety for all metric fields — if API returns a field as `null` or `undefined`, don't render it instead of showing "NaN" or "undefined"
- Remove hardcoded "HEBBIAN_DECAY_RATE" and "RECALL_CONFIDENCE" text from the dashboard (if present — verify these are in GraphView.tsx or elsewhere)
- Reduce from 2 to 1 the number of places metric field names are defined: the API is the single source of truth; the dashboard reads what exists and renders what's present

**Test scenarios:**
- Edge case: API returns `{"nodes": 10, "edges": 5, "search_latency_ms": null, "recall_precision": null}` — dashboard renders nodes and edges, skips latency and recall gracefully
- Edge case: API returns empty object `{}` — dashboard does not crash
- Integration: After U1 merge, dashboard loads without console errors about missing `review_accuracy`

**Verification:**
- Dashboard loads without rendering "NaN%" or "undefined%" values
- No browser console errors from GraphView on page load

---

- U5. **Add search result provenance (node IDs)**

**Goal:** Search results include node and dataset identifiers so the dashboard can link results to graph nodes.

**Requirements:** R5

**Dependencies:** U1

**Files:**
- Modify: `projectbrain/api.py` (`/api/search` endpoint and `/api/forget/preview`)
- Modify: `projectbrain/dashboard/src/components/GraphView.tsx` (search result display)

**Approach:**
- In `api.py` `/api/search` response: add `node_id` and `dataset_id` fields from recall result attributes
- Cognee's recall returns `SearchResultItem` objects with `.id` (or `.dataset_id`) fields — use `getattr(r, "id", None)` and `getattr(r, "dataset_id", None)`
- In GraphView.tsx: add click handler on search results that focuses the graph on the matching node
- Use `react-force-graph-2d`'s `centerAt()` to pan the graph to the clicked node (preserves zoom level; use `zoomToFit()` only as fallback if the node is outside the current viewport)
- The graph node IDs match by `id` field — search result `node_id` maps to graph node `id`

**Patterns to follow:**
- Existing node click handler (`GraphView.tsx:147-149`) — use `graphRef.current.centerAt()` or `graphRef.current.zoomToFit()`
- Existing node detail panel (`GraphView.tsx:291-325`) — clicking a search result should open the same panel

**Test scenarios:**
- Happy path: Search "Postgres" → each result includes `node_id` field matching a graph node
- Happy path: Click a search result → graph pans to/centers on the corresponding node
- Integration: `GET /api/search?q=test` returns `[{"text": "...", "node_id": "uuid-123", "dataset_id": "paylink"}]`
- Edge case: Search result's `node_id` is not found in current graph → graph stays in place, no crash
- Edge case: `node_id` is `null` (old data before ID tracking) → search result renders without clickable link

**Verification:**
- API response for search includes `node_id` and `dataset_id` fields
- Dashboard search results are clickable and trigger graph navigation
- Node detail panel opens when a search result is clicked

---

- U6. **Deploy to Railway**

**Goal:** Live demo URL at Railway for judges to interact with.

**Requirements:** R6

**Dependencies:** U1, U3, U4

**Files:**
- Modify: `projectbrain/Dockerfile` (verify it builds with the current requirements.txt)
- Modify: `projectbrain/railway.json` (verify config)
- Create: `.env.production` template or update `.env.example`

**Approach:**
- Install Railway CLI (`npm i -g @railway/cli`)
- Login: `railway login`
- Link project: `railway init` or use existing project
- Set environment variables: `COGNEE_API_KEY`, `COGNEE_API_URL`, `COGNEE_DATASET=paylink`, `ENABLE_BACKEND_ACCESS_CONTROL=false`, `CACHING=true`, `COGNEE_FORGET_ENABLED=false`
- Deploy: `railway up`
- Test the live URL: verify `/api/metrics` returns data, `GET /api/search` works
- If Railway fails, document the exact error and switch to a local-demo fallback (`docker compose up`)

**Test scenarios:**
- Integration: `GET <railway-url>/api/metrics` returns 200 with valid JSON
- Integration: `GET <railway-url>/api/search?q=test` returns 200 with results
- Edge case: Railway free tier cold-start latency — verify the first request works after idle
- Fallback: If Railway fails, `docker compose up` documented as judge demo path

**Verification:**
- Live URL returns valid responses for all critical endpoints
- Dashboard at Railway URL renders and the force graph loads

---

## System-Wide Impact

- **API surface parity:** After U1, the REST API and MCP server both use Cognee v1.0 API. The worktree change to `models.py` is additive — no existing endpoints change their request/response shapes except `/api/metrics` (removes 3 fields) and `/api/search` (adds 2 fields).
- **CI/CD:** After U2, the workflow file documents the `GROQ_API_KEY` secret requirement. Any developer cloning the repo needs to set this in GitHub settings.
- **Dashboard:** After U4-U5, the dashboard is strictly forward-compatible with the reduced metrics response and gains new search interactivity.
- **Deletion safety:** After U3, the MCP `forget` tool is surgically safe. The REST endpoint retains its 2-step confirmation for dataset-level operations.
- **Unchanged invariants:** All existing API endpoints keep the same URL paths, HTTP methods, and success response shapes. Only `/api/metrics` loses 3 fields (additive removal), and `/api/search` gains 2 fields (additive addition).

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Worktree diff conflicts when applying to master | Since master hasn't changed (1 commit total), no conflicts expected. Verify with `git diff` before applying. |
| Cognee Cloud API key hardcoded in source | U1 removes the fallback default; after merge, API key is never committed. |
| Railway URL exposes unauthenticated forget endpoint | U3 adds `COGNEE_FORGET_ENABLED=false` guard; only enabled explicitly for demo. |
| Railway free tier times out or has cold-start issues | Test after deploy. If too slow, document `docker compose up` as fallback option for judges. |
| Dashboard shows stale cached data after API changes | Clear `.next/` cache and rebuild. Dashboard reads from API for all data — no hardcoded seed data on frontend. |
| CI secrets missing (COGNEE_API_KEY/URL) | U2 documents all 3 required secrets with a validation step. |

---

## Documentation / Operational Notes

- After U6, update `projectbrain/README.md` to include the live Railway URL at the top
- Set `GROQ_API_KEY`, `COGNEE_API_KEY`, and `COGNEE_API_URL` as GitHub repository secrets after U2
- Set `COGNEE_FORGET_ENABLED=false` on Railway to prevent forget endpoint from being called. Set to `true` only when the live demo intentionally demonstrates forget.
- The `.env.example` already documents `COGNEE_API_KEY`, `COGNEE_API_URL`, and `COGNEE_DATASET` — sufficient for Railway deployment

---

## Sources & References

- **Issue analysis:** `docs/ideation-pain-friction.md`
- **Related plan:** `docs/plans/2026-07-02-004-refactor-cognee-v1-migration-pipeline-plan.md`
- **Related branch:** `feat/cognee-v1-migration` (worktree at `.worktrees/feat/cognee-v1-migration/`)
- **Cognee install:** `pip install git+https://github.com/topoteretes/cognee`
