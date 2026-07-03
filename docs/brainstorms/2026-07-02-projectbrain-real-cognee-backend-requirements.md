---
date: 2026-07-02
topic: projectbrain-real-cognee-backend
---

# ProjectBrain — Real Cognee Backend Requirements

## Problem Frame

ProjectBrain's dashboard and CI/CD agent currently run on hardcoded mock data — a Python dict in `api.py` with 9 simulated nodes and a `while True` decay loop. The MCP server stubs Cognee calls without proper initialization. This means every visual in the demo is fake, and Cognee's actual graph-vector capabilities (14 search modes, session memory, custom DataPoints, feedback loops) are unused. The hackathon judges' rubric explicitly weights "Best Use of Cognee" — a project that simulates rather than uses the platform cannot score here.

The goal is to wire ProjectBrain to Cognee's real graph-vector store: the dashboard shows live memory, the CI/CD agent reasons over the graph using `GRAPH_COMPLETION_COT`, and the system demonstrates all 4 Cognee lifecycle verbs with measurable self-improvement.

---

## Actors

- A1. **Developer**: Uses the MCP-connected IDE (Cursor/Claude Code) to remember and recall decisions
- A2. **CI/CD Reviewer**: Automated agent that checks PR diffs against Cognee's memory graph
- A3. **Dashboard Viewer**: Views the live force-graph visualization and self-improvement metrics
- A4. **Cognee Engine**: The graph-vector hybrid store that persists, indexes, and retrieves memory

---

## Key Flows

- F1. **Remember a decision**
  - **Trigger:** Developer runs `remember_decision` MCP tool
  - **Actors:** A1, A3, A4
  - **Steps:** (1) Developer calls tool with title, rationale, files, tags (2) MCP server writes to Cognee via `cognee.add()` as a structured DataPoint (3) Write-through cache updates in-memory STATE (4) SSE pushes new node to dashboard
  - **Outcome:** Decision is visible in the force graph and searchable via `recall`
  - **Covered by:** R1, R2, R3, R6, R7

- F2. **Recall context with graph traversal**
  - **Trigger:** Developer or CI/CD agent calls `recall_context`
  - **Actors:** A1, A2, A4
  - **Steps:** (1) Query sent to Cognee with a search mode (default `GRAPH_COMPLETION_COT`) (2) Cognee traverses graph edges (SUPERSEDES, DEPENDS_ON, IMPACTS) (3) Results include cited graph paths with confidence (4) Agent uses results to inform response or block a PR
  - **Outcome:** Recall returns structured, graph-grounded context with source citations
  - **Covered by:** R13, R15, R16

- F3. **CI/CD review with memory**
  - **Trigger:** PR pushed to GitHub; workflow triggers review
  - **Actors:** A2, A4
  - **Steps:** (1) Workflow runs reviewer agent with diff (2) Agent queries Cognee with `GRAPH_COMPLETION_COT` for superseded patterns (3) Cognee walks graph edges to find related decisions (4) Agent returns pass/fail with cited graph path
  - **Outcome:** PR is approved or blocked based on organizational memory, not keywords
  - **Covered by:** R15, R16, R17

- F4. **Self-improvement feedback loop**
  - **Trigger:** User confirms or corrects a recall result
  - **Actors:** A1, A4
  - **Steps:** (1) User sends `memify_feedback` with signal (confirm/correct) (2) MCP server calls `cognee.improve()` to strengthen edges (3) Metric is logged to `/api/metrics` (4) Dashboard shows updated confidence delta
  - **Outcome:** The system measurably improves over time; judges see before/after numbers
  - **Covered by:** R2, R18, R19

---

## Requirements

**[Cognee Backend Infrastructure]**
- R1. `server.py` must initialize Cognee with configurable LLM provider (Groq for demo speed, OpenAI fallback), embedding provider, and engine defaults (Kuzu + LanceDB embedded — zero infra)
- R2. Add `scripts/cognee_init.py` that runs `cognee.add()` for seed data and `cognee.cognify()` on first launch, idempotently
- R3. Add proper error handling and logging for all Cognee API calls — no silent failures. Webhook failures must surface in tool output text

**[Structured DataPoints & Seed Data]**
- R4. Define typed Cognee DataPoint models: `Decision` (title, rationale, files, tags, supersedes, date), `Incident` (description, severity, date, resolved_by), `Metric` (name, value, trend, date)
- R5. Rewrite `seed.py` to use typed DataPoints with explicit relationships (IMPACTS, SUPERSEDES, DEPENDS_ON) instead of unstructured text. Preserve the 8-week "paylink" narrative
- R6. Seed data must be a one-command operation: `python scripts/seed.py` — no manual Cognee CLI steps

**[Write-Through Cache Backend]**
- R7. Replace `api.py`'s hardcoded `STATE` dict with a write-through cache: on startup, load graph from Cognee; on every `remember`, write to both Cognee (via `cognee.add()`) and in-memory cache
- R8. Remove the simulated Hebbian decay loop (`api.py:45-70`). Cognee's native retention/pruning handles decay
- R9. SSE endpoint (`/api/stream`) pushes real-time graph state changes pulled from actual Cognee data. Dashboard updates are event-driven, not polled
- R10. Add dashboard reconnection handling: if SSE connection drops, show "reconnecting..." indicator and auto-retry. If the MCP server is unreachable, the dashboard shows stale data with a timestamp warning

**[Graph Query & 14 Search Modes]**
- R11. Add `/api/graph` endpoint that returns Cognee's current graph state (nodes = entities, edges = relationships) serialized as JSON. Dashboard renders this data instead of hardcoded fixtures
- R12. Add `/api/search` endpoint that accepts a `query` string and optional `search_mode` parameter. Wire all 14 Cognee `SearchType` modes. Default to `GRAPH_COMPLETION` for general use
- R13. Add `/api/search/modes` endpoint that returns available search modes with descriptions, so the dashboard can render a mode selector

**[Session-to-Permanent Memory]**
- R14. `recall_context` accepts an optional `session_id` parameter. When provided, Cognee's session memory scopes the query to conversational context
- R15. After N confirmations (configurable, default 3) via `memify_feedback` on the same session, the memory fragment is promoted to permanent storage. Dashboard color-codes session nodes vs permanent nodes

**[CI/CD Reviewer with GRAPH_COMPLETION_COT]**
- R16. Replace `reviewer_agent.py` keyword matching with `cognee.search(mode=GRAPH_COMPLETION_COT)`. The reviewer asks "Is this PR introducing a pattern that was superseded?" and Cognee walks the graph edges
- R17. Review output must include the cited graph path — which SUPERSEDES/DEPENDS_ON chain led to the finding — so the developer can verify
- R18. Keep keyword-based fallback for when Cognee returns empty results (network offline, no memory seeded)

**[Self-Improvement Metrics]**
- R19. Add `/api/metrics` endpoint: recall precision (returned relevant nodes / total returned), review accuracy (correct flags / total flags), memory staleness (nodes below hotness threshold / total nodes)
- R20. Dashboard shows a "Compound Score" panel: "12 decisions · 47 edges · 94% recall precision · +22% this session"

**[Demo & Submission Polish]**
- R21. Fix dashboard metadata: title "ProjectBrain — Memory for AI IDEs", description with Cognee attribution
- R22. Rework `README.md` with: hero GIF of the real force graph, one-command setup, Cognee lifecycle section mapping each verb to a UI element, link to demo video
- R23. Record a 2-3 minute demo video showing: (1) MCP server startup, (2) remembering a decision, (3) dashboard graph updating in real time, (4) recall with graph traversal, (5) CI/CD reviewer blocking a superseded pattern, (6) compound score improving after feedback

---

## Acceptance Examples

- AE1. **Covers R1, R5, R11.** Given Cognee is installed and configured, when the user runs `python scripts/seed.py`, then visits the dashboard at `localhost:3000`, the force graph shows named nodes (not a blank canvas) with edges between decisions and files.
- AE2. **Covers R7, R8, R10.** Given the dashboard is connected, when the user runs `python api.py && python server.py`, the SSE indicator shows "connected". When the user triggers `remember_decision` via MCP, a new node appears in the dashboard graph within 2 seconds without refreshing.
- AE3. **Covers R16, R18.** Given Cognee is seeded with the "paylink" narrative, when a PR contains `import { MongoClient }`, the reviewer agent outputs a denial citing the SUPERSEDES chain from MongoDB to Postgres, referencing incident #104.
- AE4. **Covers R19, R20.** Given the system has processed 5+ recall queries and 3+ memify_feedback calls, when the user visits the dashboard metrics panel, it shows a recall precision higher than when it started (e.g., "87% → 94%").

---

## Success Criteria

- The dashboard force graph displays nodes and edges retrieved from Cognee's actual graph store, not hardcoded mock data
- A 3-minute demo video shows the full Cognee lifecycle (remember → recall → improve → forget) with the dashboard graph updating in real time
- The CI/CD reviewer catches a deprecated pattern by traversing Cognee's graph (not keyword matching) and outputs a cited graph path
- The compound score on the dashboard measurably improves during the demo (before/after numbers visible)
- All project files use repo-relative paths — no absolute paths in config or docs

---

## Scope Boundaries

- **The demo narrative stays as the fictional "paylink" repo** — no real project data needed
- **Cognee runs embedded** (Kuzu + LanceDB + SQLite) — no Docker or cloud infra for the demo
- **No authentication or multi-user support** — single-user demo only
- **No git integration beyond the CI/CD workflow** — auto-commit detection is deferred
- **No Slack/Linear/Jira ingestion** — manual entry via MCP tool for the demo
- **The "Nudge" proactive push idea is deferred** — pull-based recall is sufficient for this sprint

---

## Key Decisions

- **Approach:** Write-through cache (in-memory STATE backed by Cognee) rather than pure Cognee-native backend. Keeps SSE real-time performance while making the graph real
- **Search mode scope:** All 14 modes wired to `/api/search` endpoint. Dashboard includes a mode selector dropdown. Default mode: `GRAPH_COMPLETION`
- **Session memory:** Opt-in via `session_id` parameter. Promotion to permanent after 3 confirmations
- **CI/CD reviewer:** GRAPH_COMPLETION_COT as primary, keyword fallback. Cited graph path in output

---

## Dependencies / Assumptions

- Cognee `pip` package is installable and supports the 14 search modes, DataPoints, and session memory as documented
- Kuzu + LanceDB embedded stores work on the demo machine without additional setup
- The MCP SDK (`mcp`) supports FastMCP and stdio transport as currently used
- `react-force-graph-2d` works with Next.js 16 client components (already verified)
- The hackathon timeline (Jul 2-5) allows 3-4 focused build days

---

## Outstanding Questions

### Resolve Before Planning

None. All product decisions resolved.

### Deferred to Planning

- [Affects R1][Technical] Which specific Groq model and API key should be set as the default Cognee LLM provider?
- [Affects R4][Technical] Exact field schema for `Decision`, `Incident`, and `Metric` DataPoint models — need to verify Cognee's DataPoint API version compatibility
- [Affects R12][Needs research] Which Cognee `SearchType` modes require additional configuration vs work out of the box?
- [Affects R16][Technical] How to pass the PR diff to the Cognee review agent in the GitHub Actions workflow environment
- [Affects R23][Technical] Screen recording tool and format for the demo video

---

## Next Steps

`-> /ce-plan` for structured implementation planning
