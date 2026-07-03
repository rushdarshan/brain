---
title: Self-Improving CI/CD Gate + Graph Evolution Slider
type: feat
status: active
date: 2026-07-02
origin: docs/brainstorms/2026-07-02-projectbrain-self-improving-cicd-slider-requirements.md
---

# Self-Improving CI/CD Gate + Graph Evolution Slider

## Overview

The CI/CD reviewer currently checks 4 hardcoded keywords and never learns. Two changes: (1) make it query Cognee for known deprecated patterns, score PRs, and store results so the dashboard can show improvement over time; (2) add a timeline slider to the dashboard so users can see the graph evolve through weeks 1-8 of seed data.

---

## Problem Frame

The reviewer agent (`projectbrain/reviewer_agent.py`) is static — hardcoded `["mongodb", "mongoclient", "jwt", "jsonwebtoken"]` keyword list, no scoring, no learning. The graph visualization has no temporal dimension — you can't see how knowledge evolved.

The winning Cognee hackathon pattern is a measurable self-improvement loop with before/after scores. This plan builds that loop and the visual hook (slider) to demonstrate it.

---

## Requirements Trace

- R1. Reviewer queries Cognee for known deprecated patterns
- R2. Reviewer computes score = caught / total deprecated patterns in diff
- R3. Reviewer stores result in Cognee tagged `review_result`
- R4. Reviewer exits 0 (approve) for score >= 0.5, 1 (reject) otherwise
- R5. Dashboard "Flag missed pattern" input
- R6. `POST /api/patterns/flag` stores pattern in Cognee tagged `deprecated_pattern`
- R7. Dashboard review history panel with score trend
- R8. `GET /api/review/history` returns sorted `review_result` nodes from Cognee
- R9. Dashboard evolution slider for weeks 1-8
- R10. Slider re-renders graph to show only nodes present at that week

**Origin actors:** A1 (Developer), A2 (Reviewer Agent), A3 (Dashboard User)
**Origin flows:** F1 (PR Review with Scoring), F2 (Flag Missed Pattern), F3 (View Score History), F4 (Graph Evolution Slider)
**Origin acceptance examples:** AE1 (learn redis pattern), AE2 (flag grpc pattern), AE3 (week 1→8 slider progression)

---

## Scope Boundaries

- **Search quality dashboard** — not building. 17 search modes are Cognee's feature, not a problem to solve.
- **Dynamic graph snapshots** — not building. Slider uses static seed data only.
- **Weighted scoring** — not building. All patterns count equally.
- **PR comment feedback** — not building. Dashboard button is the feedback mechanism.
- **Demo seed data beyond week 8** — not building. 8 weeks is enough for the demo narrative.

---

## Context & Research

### Relevant Code and Patterns

- `projectbrain/api.py:101-115` — existing `POST /api/webhook/remember` endpoint pattern. New endpoints follow the same `cognee.add()` + `cognee.cognify()` + reload graph + notify clients flow.
- `projectbrain/api.py:162-176` — existing `GET /api/search` endpoint. Pattern for querying Cognee and returning structured results.
- `projectbrain/api.py:24-48` — `load_graph_from_cognee()` function. Pattern for reading graph state from Cognee.
- `projectbrain/reviewer_agent.py:9-31` — current reviewer logic. Will be replaced by Cognee-based pattern matching.
- `projectbrain/seed.py:7-38` — `seed_items` list with `week` field (1-8) on each item. Source data for the slider.
- `projectbrain/dashboard/src/components/GraphView.tsx` — existing force graph component. Slider and new panels will be added here.

### Institutional Learnings

- The dashboard API URL is hardcoded to `http://127.0.0.1:8000` in `GraphView.tsx:8`. New API consumers (review history, flag pattern) should use the same constant.

---

## Key Technical Decisions

- **Patterns stored as Cognee text nodes**: A deprecated pattern is stored via `cognee.add("deprecated:DEPRECATED_PATTERN grpc", dataset_name=DATASET)` + `cognee.cognify()`. The reviewer searches for text containing `deprecated:` prefix to find known patterns. Simple, works with existing Cognee APIs.
- **Review results stored as Cognee text nodes**: A review result is stored via `cognee.add(f"review_result:score={score} timestamp={ts} patterns={json.dumps(checked)}")`. Search for `review_result:` prefix to retrieve history.
- **Slider data from seed_items array**: GraphView.tsx imports the seed data structure directly. Per-week snapshots computed client-side — no backend changes for U6.
- **Flag endpoint follows webhook pattern**: `POST /api/patterns/flag` mirrors the existing `/api/webhook/remember` — add text, cognify, reload graph, notify SSE clients.

---

## Open Questions

### Resolved During Planning

- **How to retrieve known patterns from Cognee**: Search with a dedicated prefix string (e.g., `"deprecated:"`). The reviewer searches Cognee for entries starting with this prefix and extracts pattern names from the results. No custom Cognee API needed.
- **How to structure review results**: Store as `cognee.add()` entries with a `review_result:` prefix, including score, timestamp, and checked patterns in the text body. The history endpoint searches for this prefix.

### Deferred to Implementation

- [Affects U2] Exact Cognee search type for retrieving patterns. KEYWORD mode likely works for prefix search. Verify during implementation.
- [Affects U1] Whether `cognee.search()` returns results sorted by time. If not, store timestamp in the text and sort client-side.
- [Affects U6] How to map seed_items to graph-like nodes (id, name, group, links) for per-week snapshots. This is a frontend data transformation — needs to simulate what Cognee would produce.

---

## Implementation Units

- U1. **[api.py — pattern management and review history endpoints]**

**Goal:** Two new endpoints: `POST /api/patterns/flag` to store a new deprecated pattern, and `GET /api/review/history` to return past review results.

**Requirements:** R6, R8

**Dependencies:** None

**Files:**
- Modify: `projectbrain/api.py`
- Test: `projectbrain/test_api.py` (new)

**Approach:**
- `POST /api/patterns/flag` receives `{pattern: "grpc"}`, calls `cognee.add(f"deprecated: grpc")` + `cognee.cognify()` with the permanent dataset, reloads graph, notifies SSE clients. Returns `{status: "flagged", pattern: "grpc"}`.
- `GET /api/review/history` searches Cognee with query `"review_result:"` using KEYWORD mode, parses results into structured objects `{score, timestamp, patterns_checked, passed}`, returns sorted by timestamp descending. Returns `{reviews: [...]}`.
- Both endpoints follow the existing patterns in api.py (pydantic models, async handlers, Cognee integration).

**Patterns to follow:**
- `api.py:101-115` (`POST /api/webhook/remember`) for the flag endpoint structure
- `api.py:162-176` (`GET /api/search`) for the history endpoint structure

**Test scenarios:**
- Happy path: POST a pattern → returns 200 with correct pattern name
- Happy path: GET review history with no results → returns empty `reviews` array
- Edge case: Empty pattern string → returns 400 or stores as-is (accept as-is — simplest)
- Edge case: GET review history with results → returns correctly parsed objects with score, timestamp, patterns_checked fields

**Verification:**
- `curl -X POST localhost:8000/api/patterns/flag -H "Content-Type: application/json" -d '{"pattern":"grpc"}'` returns 200
- `curl localhost:8000/api/review/history` returns JSON with reviews array
- Graph updates after flagging a pattern (new node visible via SSE)

---

- U2. **[reviewer_agent.py — Cognee-based scoring]**

**Goal:** Rewrite reviewer to query Cognee for known deprecated patterns, scan the diff, compute a score, and store the result in Cognee.

**Requirements:** R1, R2, R3, R4

**Dependencies:** None (independent of U1 — both read/write Cognee directly)

**Files:**
- Modify: `projectbrain/reviewer_agent.py`
- Test: `projectbrain/test_reviewer_agent.py` (new)

**Approach:**
- Remove hardcoded `["mongodb", "mongoclient", "jwt", "jsonwebtoken"]` list
- Query Cognee: `cognee.search(query_text="deprecated:", query_type=SearchType.KEYWORD, datasets=[DATASET])` → extracts pattern names from results
- Scan the PR diff text (lowercased) for each known pattern name (substring match)
- Score = number of matches found / number of known patterns present in diff
- Store result: `cognee.add(f"review_result:score={score} timestamp={time.time()} patterns_checked={str(patterns_checked)} passed={1 if score >= 0.5 else 0}")` + `cognee.cognify()`
- Score < 0.5 → exit code 1 (reject). Score >= 0.5 → exit code 0 (approve)
- Print detailed output: score, patterns checked, patterns found, decision

**Patterns to follow:**
- Existing reviewer structure (async function, `__main__` entry point)
- `api.py:162-176` Cognee search pattern with SearchType

**Test scenarios:**
- Happy path: Diff contains 2 of 3 known deprecated patterns → score = 0.67, exit 0
- Happy path: Diff contains no deprecated patterns → score = 1.0 (trivially, 0/0), exit 0
- Edge case: Cognee returns no known patterns → score = 1.0 (nothing to check), exit 0
- Edge case: Diff contains ALL known deprecated patterns → score = 0.0, exit 1
- Edge case: Case-insensitive matching — `MongoClient` vs `mongoclient`
- Integration: Result is queryable from Cognee after the run

**Verification:**
- `python reviewer_agent.py good` exits 0 with score 1.0
- `python reviewer_agent.py` (MongoClient default) exits 1 with score 0.0
- Cognee contains a `review_result:` entry after each run

---

- U3. **[Dashboard — Flag missed pattern input]**

**Goal:** A small input on the dashboard where the developer types a pattern name and clicks "Flag". POSTs to `POST /api/patterns/flag`.

**Requirements:** R5

**Dependencies:** U1

**Files:**
- Modify: `projectbrain/dashboard/src/components/GraphView.tsx`

**Approach:**
- Add a new state: `flagPattern` (string) and `flagStatus` (idle | loading | success | error)
- Render a compact input row below the metrics bar: input field + "Flag as deprecated" button
- On submit: POST to `/api/patterns/flag` with `{pattern: flagPattern}`, show confirmation
- On success: show a brief green "Pattern flagged" message that fades after 3 seconds
- On error: show red error message
- The graph already updates via SSE when the backend creates new node, so the user sees the new pattern appear in the graph

**Patterns to follow:**
- Existing fetch calls in GraphView.tsx (e.g., `fetch(`${API}/api/patterns/flag`, ...)`)
- Existing error/success state patterns in the component

**Test scenarios:**
- Happy path: Type "grpc", click Flag → POST succeeds, green confirmation shown
- Edge case: Empty input → button disabled or shows "Enter a pattern name"
- Edge case: Backend returns error → red error message shown
- Edge case: Duplicate pattern → backend handles gracefully, show "Already flagged"

**Verification:**
- Input renders below metrics bar
- Typing and clicking Flag produces a visible success/error response
- New pattern node appears in the graph (SSE push from backend)

---

- U4. **[Dashboard — Review history panel]**

**Goal:** A panel showing a simple score-over-time trend and a table of recent review results.

**Requirements:** R7

**Dependencies:** U1 (needs `/api/review/history` endpoint)

**Files:**
- Modify: `projectbrain/dashboard/src/components/GraphView.tsx`

**Approach:**
- Add `fetchReviewHistory()` that polls `GET /api/review/history` every 10 seconds
- Render a collapsible "Review History" section below or beside the graph
- Show a simple sparkline/bar chart of scores over time (use a tiny inline SVG — no chart library needed)
- Below the chart: a table with columns: Score | Patterns | Result (Pass/Fail) | Time
- Use CSS-only rendering for the chart: small colored bars proportional to score
- Auto-scrolls to latest entry

**Patterns to follow:**
- Existing metrics polling pattern in GraphView.tsx (`fetchMetrics` called on mount and via interval)
- Existing table/list rendering (search results panel pattern)

**Test scenarios:**
- Happy path: 5 review results returned → 5 rows rendered + chart with 5 bars
- Edge case: No review results yet → empty state "No reviews yet"
- Edge case: Backend down → hide panel or show "Backend unavailable"
- Edge case: Score 1.0 → full green bar. Score 0.0 → empty red bar

**Verification:**
- Review history section renders below the graph
- After running reviewer twice, two entries show in the table
- Score trend chart shows bars proportional to scores

---

- U5. **[GitHub Actions — score output capture]**

**Goal:** The CI workflow captures the reviewer's score output and makes it visible in the PR check run.

**Requirements:** F1 (score visibility in PR)

**Dependencies:** U2

**Files:**
- Modify: `projectbrain/.github/workflows/projectbrain-review.yml`

**Approach:**
- The reviewer already prints score/result to stdout. GitHub Actions captures this automatically in the step log.
- Add the reviewer's stdout output as a job summary using `$GITHUB_STEP_SUMMARY` so the score is visible on the PR's checks tab without clicking into logs.
- Append the score and decision to step summary: `echo "### Review Score: $SCORE" >> $GITHUB_STEP_SUMMARY`

**Patterns to follow:**
- Existing `.github/workflows/projectbrain-review.yml` structure

**Test scenarios:**
- Integration: PR opened → workflow runs → check run shows the score and decision in the summary

**Verification:**
- Trigger a PR → check the GitHub Actions run → summary tab shows score and pass/fail

---

- U6. **[Dashboard — Graph evolution slider]**

**Goal:** A slider control that moves through weeks 1-8, re-rendering the graph to show only nodes present at that week.

**Requirements:** R9, R10

**Dependencies:** None (frontend-only, no backend changes)

**Files:**
- Modify: `projectbrain/dashboard/src/components/GraphView.tsx`

**Approach:**
- Define a local `seedItems` array (copied inline from `projectbrain/seed.py` — same structure with `title`, `week`, `supersedes`)
- Add state: `sliderWeek` (default 8, range 1-8) and `showSlider` (boolean toggle)
- Derive per-week graph snapshots:
  - Filter `seedItems` by `week <= sliderWeek`
  - Map each item to a fake node: `{id: "seed-" + index, name: item.title, group: classify(item.tags), val: 20}`
  - Create edges for `supersedes` relationships between items
  - Older items fade in opacity, superseded items get a visual indicator
- Render a range input (`<input type="range">`) above the graph labeled "Timeline: Week {sliderWeek}"
- When GraphView loads live data from SSE, hide the slider (it's only for seed data visualization). Add a toggle "Show Evolution" that switches between live graph and seed slider view.

**Patterns to follow:**
- Existing `useMemo` derivations in GraphView.tsx (edgeTypes, groupCounts — same pattern)
- Existing ForceGraph2D rendering pattern (graphData is the source of truth)

**Test scenarios:**
- Happy path: Slider at week 1 → shows 5 nodes (3 meta + 2 paylink). Week 3 → shows 9 nodes (3 meta + 6 paylink). Week 8 → shows all 18 nodes.
- Edge case: Supersedes edge appears at week 3 (Postgres supersedes MongoDB)
- Edge case: Toggle between "Live" and "Evolution" modes — live mode shows SSE data, evolution mode shows seed snapshots
- Edge case: Slider at minimum (1) → only week 1 items visible. Slider at maximum (8) → everything visible.

**Verification:**
- Slider renders and is draggable
- Moving the slider from 1 to 8 shows progressively more nodes
- Supersedes edges appear at the correct weeks
- Toggle switches correctly between live SSE data and seed slider view

---

## System-Wide Impact

- **Interaction graph:** `POST /api/patterns/flag` triggers SSE push to all dashboard clients. If the dashboard is not open, the push is a no-op (clients list is empty).
- **Error propagation:** Cognee search failures in the reviewer flow cause exit code 2 (unexpected error) to distinguish from rejected (exit 1). The reviewer prints the error for debugging.
- **API surface parity:** The existing `POST /api/webhook/remember` and `POST /api/remember/session` endpoints are unchanged. New endpoints follow the same error handling patterns (no try/except — let FastAPI return 500).
- **Unchanged invariants:** The existing review metrics (`review_total`, `review_approved` in api.py) are separate from the new Cognee-stored review results. Old metrics tracking is untouched.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `cognee.search()` with KEYWORD mode may not support prefix matching | Fallback: store patterns and review results in a dedicated dataset and fetch via `get_memory_provenance_graph()` or iterate all entries. Verify during U2 implementation. |
| Seed item → graph node mapping on frontend won't match actual Cognee node render | The slider is a visualization aid, not a debug view. Accept visual differences. The live graph (SSE) always shows the real Cognee state. |
| Reviewer stores results in Cognee but CI network can't reach Cognee Cloud | The current reviewer already connects to Cognee in CI. Same network setup. If it fails, the reviewer exits code 2 (error) and the PR check shows a failure. |
| Score 0/0 edge case (no deprecated patterns in diff) | Trivially score 1.0 — no violations to catch. The reviewer prints "No deprecated patterns found — score: 1.0". |

---

## Documentation / Operational Notes

- Add a "Self-Improving CI/CD" section to `projectbrain/README.md` describing the scoring flow and how to flag patterns.
- Update demo script in `projectbrain/MASTER.md` to include the before/after scoring demo.
- The `projectbrain/.github/workflows/projectbrain-review.yml` workflow already sets `COGNEE_API_KEY` and `COGNEE_API_URL` as repo secrets. Verify they're configured.

---

## Sources & References

- **Origin document:** `docs/brainstorms/2026-07-02-projectbrain-self-improving-cicd-slider-requirements.md`
- Related code: `projectbrain/reviewer_agent.py`, `projectbrain/api.py`, `projectbrain/dashboard/src/components/GraphView.tsx`
- External: [Cognee Hackathon winning pattern — self-improvement with before/after scores]
