---
date: 2026-07-02
topic: self-improving-cicd-gate-and-graph-evolution-slider
---

# Self-Improving CI/CD Gate + Graph Evolution Slider

## Problem Frame

The current CI/CD reviewer (`projectbrain/reviewer_agent.py`) is static — it checks 4 hardcoded keywords and never gets better. Developers can't teach it new deprecated patterns. The graph is also static — it loads at startup and only updates via SSE when new data is added, with no way to see how the knowledge evolved over time.

To win the Cognee hackathon, the project needs a **measurable self-improvement loop with before/after scores** — the proven winning pattern from past Cognee hackathons. The slider makes the "context rot" story visual and demo-compelling.

---

## Actors

- A1. **Developer**: Submits PRs that the reviewer checks. Can flag missed patterns via the dashboard.
- A2. **Reviewer Agent**: CI/CD script (`projectbrain/reviewer_agent.py`) that checks PR diffs against known deprecated patterns stored in Cognee. Computes a score.
- A3. **Dashboard User**: Views the score history trend and uses the graph evolution slider to see how knowledge grew over time.

---

## Key Flows

- F1. **PR Review with Scoring**
  - **Trigger:** A PR is opened or updated
  - **Actors:** A2 (Reviewer Agent)
  - **Steps:**
    1. GitHub Action runs `projectbrain/reviewer_agent.py` with the PR diff
    2. Agent queries Cognee for all nodes tagged `deprecated_pattern`
    3. Agent scans the diff for each known deprecated pattern
    4. Agent computes score = patterns caught / total deprecated patterns found in diff
    5. Agent stores the review result in Cognee as a node tagged `review_result` with score, timestamp, and list of patterns checked
  - **Outcome:** PR has a check run showing the score. Result is queryable by the dashboard.
  - **Covered by:** R1, R2, R3

- F2. **Flag Missed Pattern (Feedback Loop)**
  - **Trigger:** A developer spots a pattern the reviewer missed
  - **Actors:** A1 (Developer), A3 (Dashboard User)
  - **Steps:**
    1. Developer opens the dashboard
    2. They type a pattern name (e.g. "grpc") into a "Flag missed pattern" input
    3. Dashboard calls `POST /api/patterns/flag` which stores the new deprecated pattern in Coggee via `cognee.add()` + `cognee.cognify()`
    4. New pattern node appears in the graph in real-time via SSE
    5. The next review run queries Cognee again — now the new pattern is in the known list
  - **Outcome:** The reviewer learns the new pattern. Re-running the same review produces a higher score.
  - **Covered by:** R4, R5, R6

- F3. **View Score History**
  - **Trigger:** Dashboard user opens the review history panel
  - **Actors:** A3 (Dashboard User)
  - **Steps:**
    1. Dashboard fetches `GET /api/review/history`
    2. `api.py` queries Cognee for `review_result` nodes, returns them sorted by timestamp
    3. Dashboard renders a small trend chart (score vs time) and a table of recent results
  - **Outcome:** User sees the score improving over time as the reviewer learns new patterns.
  - **Covered by:** R7, R8

- F4. **Graph Evolution Slider**
  - **Trigger:** Dashboard user interacts with the slider
  - **Actors:** A3 (Dashboard User)
  - **Steps:**
    1. The slider UI precomputes graph snapshots from the seed data (weeks 1-8)
    2. User drags the slider — graph re-renders to show that week's state
    3. Nodes that appear in a later week fade in, superseded nodes change color
  - **Outcome:** User sees the knowledge graph grow from week 1 to week 8, observing decisions being made, superseded, and confirmed.
  - **Covered by:** R9, R10

---

## Requirements

**[Self-Improving CI/CD Gate]**

- R1. The reviewer agent (`projectbrain/reviewer_agent.py`) must query Cognee for known deprecated patterns instead of using hardcoded keyword lists.
- R2. The reviewer must compute a score = (deprecated patterns caught in the diff) / (total deprecated patterns present in the diff). Score is 0.0–1.0.
- R3. The reviewer must store each review result in Cognee as a node tagged `review_result`, containing the score, timestamp, and list of patterns checked.
- R4. The reviewer must exit with code 0 (approve) when the score is >= 0.5, and code 1 (reject) when < 0.5.
- R5. The dashboard must have a "Flag missed pattern" input that POSTs to a new endpoint.
- R6. `api.py` must expose `POST /api/patterns/flag` that stores the pattern name in Coggee via `cognee.add()` + `cognee.cognify()`, tagged as `deprecated_pattern`.
- R7. The dashboard must have a review history panel showing a score-over-time trend and a table of recent review results.
- R8. `api.py` must expose `GET /api/review/history` that queries Cognee for `review_result` nodes and returns them sorted by timestamp.

**[Graph Evolution Slider]**

- R9. The dashboard must have a slider control that moves through weeks 1-8, derived from the seed data in `projectbrain/seed.py`.
- R10. Moving the slider must re-render the force graph to show only nodes and edges present at that week. Nodes not yet added should not appear.

---

## Acceptance Examples

- AE1. **Covers R1, R2, R4.** Given a PR diff importing `import { MongoClient } from 'mongodb'` and import `import { createClient } from 'redis'`, and Cognee has `mongodb` but not `redis` as a known deprecated pattern: the reviewer catches `mongodb` at score 0.5, exits code 0. The developer flags `redis` via the dashboard. The next review of the same diff catches both at score 1.0.
- AE2. **Covers R5, R6.** Given the dashboard is open, the developer types "grpc" into the "Flag missed pattern" input and clicks submit. A new node appears in the graph tagged `deprecated_pattern` with name "grpc" within 2 seconds.
- AE3. **Covers R9, R10.** Given the seed data is loaded, the user drags the evolution slider from week 1 to week 8. At week 1, only 2 nodes (MongoDB, JWT) are visible. At week 3, the Postgres node has appeared and the MongoDB node now shows a SUPERSEDES edge. At week 8, all 18 nodes are visible with all supersedence edges.

---

## Success Criteria

- The demo can show: a PR scored 0.5 → feedback flagging the missed pattern → re-scored at 1.0, all within the dashboard view.
- A handoff to planning is clean — no product behavior decisions remain to be discovered.

---

## Scope Boundaries

- **Search quality dashboard** — not building. The 17 search modes are Cognee's feature, not a problem to solve. Focus on the self-improvement narrative.
- **Dynamic graph snapshots** — not building. The slider uses static seed data only. Dynamic snapshots across arbitrary graph changes are deferred indefinitely.
- **Weighted scoring** — not building. All patterns count equally. Simpler to explain in a demo.
- **PR comment feedback** — not building. The dashboard button is the feedback mechanism. PR comment support deferred indefinitely.
- **Demo seed data beyond week 8** — not building. 8 weeks is enough for the demo narrative.

---

## Key Decisions

- **Feedback via dashboard button**: Chosen over PR comments and MCP tools because it's the most visible in a demo — judges see the button click, see the graph update, see the score improve.
- **Scoring: pattern-match based**: Chosen over weighted severity scoring. Simpler to explain and compute. "Caught 2 of 3 bad patterns = 0.67" is immediately understood.
- **Score storage in Cognee**: Chosen over API endpoints or JSON files. The reviewer runs in CI (no api.py dependency). Cognee is the shared truth.
- **Slider: static snapshots from seed data**: Chosen over dynamic backend snapshots. No backend changes needed. ~30 min to build.
- **Threshold for rejection: score < 0.5**: Hard-coded threshold. Keeps the reviewer decisive and the demo clear.
- **Known patterns stored in Cognee with cognee.add()**: Not a formal "model upload" — just text nodes. Simpler, and the graph naturally shows new patterns appearing.

---

## Dependencies / Assumptions

- `cognee.add()` and `cognee.cognify()` can store and retrieve tagged nodes (`deprecated_pattern`, `review_result`).
- The repository has seed data with week annotations (`projectbrain/seed.py` has `week` on each item).
- The reviewer runs in GitHub Actions with Cognee access (already true — the current reviewer imports cognee).
- The slider can precompute per-week graph state from client-side seed data (no Cognee query needed for the slider).

---

## Outstanding Questions

### Resolve Before Planning

None — all product decisions are resolved above.

### Deferred to Planning

- [Affects R1][Technical] — Exact Cognee query to retrieve `deprecated_pattern` nodes. May need specific search mode or tag filter approach.
- [Affects R8][Technical] — Database format of `review_result` nodes and how to query/filter them from Cognee.
- [Affects R9][Needs research] — How to derive per-week graph snapshots from seed data on the frontend. The seed items have a `week` field but the mapping from seed text to graph nodes and edges needs to be reconstructed.
- [Affects R5][Technical] — Whether the dashboard's hardcoded `http://127.0.0.1:8000` API URL needs to be made configurable for the Railway deploy. (Already a known issue from the codebase scan.)

---

## Next Steps

`-> /ce-plan` for structured implementation planning.
