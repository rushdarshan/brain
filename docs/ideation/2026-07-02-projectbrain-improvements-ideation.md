---
date: 2026-07-02
topic: projectbrain-improvements
focus: winning the WeMakeDevs × Cognee Hangover Part AI hackathon
mode: repo-grounded
---

# Ideation: ProjectBrain — Winning Improvement Ideas

## Grounding Context

**Codebase:** Python (FastAPI, Cognee, MCP SDK) + Next.js 16 (React 19, Tailwind 4, react-force-graph). MCP server with 4 tools (remember, recall, memify_feedback, forget). Real-time SSE-pushed force-graph dashboard. CI/CD reviewer agent in `.github/workflows/`.

**Current gaps:**
- API state is hardcoded mock data (`api.py:20-41`), NOT driven by Cognee's real graph
- `server.py` stubs Cognee calls without proper initialization/config
- `improve()` and `forget()` are stubs — no real Cognee graph interaction
- Webhook failures silently caught (`server.py:35-36`) — dashboard goes stale
- CI/CD reviewer uses `if "mongodb" in code` keyword matching, not LLM reasoning over memory
- Seed data is unstructured text blobs, not typed Cognee DataPoints
- Dashboard metadata still says "Create Next App"
- No persistence — restart = data loss
- Decay loop simulates Hebbian pruning instead of using Cognee's built-in retention

**Winning pattern from past Cognee hackathons:** Two-tier memory (session + permanent) + self-improvement loop with reproducible before/after numbers. Winners showed concrete metrics (Cold Email Brain: 0.46→1.00, StudyAtlas: 0.3→0.8, PaperGraph: +40 nodes).

**Cognee differentiators vs competitors:** Graph free at every tier (vs Mem0 Pro $249/mo), 14 search modes including GRAPH_COMPLETION_COT for multi-hop reasoning, native MCP server, official Claude Code plugin, session memory, custom DataPoints (Pydantic models for controlled embedding).

## Ranked Ideas

### 1. Real Cognee Graph Drives Dashboard
**Description:** Replace `api.py`'s hardcoded `STATE` dict with live Cognee graph queries. The SSE stream pushes results from `cognee.search(mode=GRAPH_COMPLETION_COT)` instead of a mock decay loop. Dashboard nodes become real-time projections of actual graph state. The Hebbian decay loop is replaced by Cognee's native retention/pruning.

**Warrant:** `direct: api.py:20-41` — 9 nodes, 7 links are hardcoded. `direct: api.py:45-70` — decay loop is simulation, not Cognee.

**Rationale:** Without this, the entire dashboard is fake. Judges will ask "is this real?" — this makes the answer yes. Directly hits "Best Use of Cognee" + "Technical Excellence." Everything else depends on this being real.

**Downsides:** Requires Cognee initialization + provider config. Demo dataset must be re-ingested. Removes the current simulation (may break dashboard if Cognee isn't running).

**Confidence:** 100%
**Complexity:** High
**Status:** Explored

### 2. Self-Improvement Loop with Before/After Metrics
**Description:** Add `/api/metrics` endpoint tracking recall precision, review accuracy, and memory staleness. The dashboard shows a running delta: "Memory accuracy: 82% → 94% this session." Each feedback cycle (memify_feedback) writes a structured artifact and updates the scoreboard. Judges see the system improving in real time during a 3-minute demo.

**Warrant:** `external:` Past Cognee×Redis winners all showed concrete before/after numbers. `reasoned:` Without numbers, improvement claims are vibes — with numbers, the self-improvement loop is falsifiable.

**Rationale:** This is the single highest-ROI slide in any hackathon presentation. It proves the system works better over time rather than degrading. Every other project will show a feature; ProjectBrain shows a *compounding* feature.

**Downsides:** Needs ground-truth data to measure against. Metrics can be gamed if not careful.

**Confidence:** 95%
**Complexity:** Medium
**Status:** Explored

### 3. CI/CD Reviewer with GRAPH_COMPLETION_COT
**Description:** Replace `reviewer_agent.py`'s `if "mongodb" in code_snippet` with `cognee.search(query, search_mode=GRAPH_COMPLETION_COT)`. The reviewer asks "Is this PR introducing a pattern that was superseded?" Cognee walks the SUPERSEDES → DEPENDS_ON → IMPACTS graph chains to decide. Include cited memory nodes in the review output.

**Warrant:** `direct: reviewer_agent.py:12-26` — `if "mongodb" in diff_text.lower()` is the core logic. `direct:` Cognee has GRAPH_COMPLETION_COT search mode documented. `reasoned:` Multi-hop reasoning over graph edges is Cognee's headline differentiator.

**Rationale:** Keyword matching will embarrass the project in Q&A. Multi-hop reasoning is the feature that makes Cognee more than "RAG with extra steps." Demo: show keyword matcher failing on a novel deprecated pattern, then graph-backed reviewer catching it with cited graph path.

**Downsides:** Requires LLM inference per review (latency and token cost). May hallucinate on complex diffs. Higher risk than keyword approach.

**Confidence:** 90%
**Complexity:** Medium
**Status:** Explored

### 4. Structured DataPoints for Seed Data
**Description:** Replace `seed.py`'s unstructured text blobs with typed Cognee DataPoint objects defining `Decision(id, title, rationale, files, tags, supersedes, date)`. Each decision gets controlled embedding fields via `index_fields`. Cognee's ontology generation structures memory automatically. Ship ingest script.

**Warrant:** `direct: seed.py:12-38` — all entries are raw strings. `external:` Cognee DataPoint docs — Pydantic models controlling which fields get embedded, with dedup and versioning.

**Rationale:** Unstructured seed produces a noisy graph with low-quality search results. Structured DataPoints unlock all 14 search modes properly. Without this, every downstream Cognee feature (recall, search, graph traversal) produces worse results.

**Downsides:** Requires schema design upfront. DataPoint API has a learning curve.

**Confidence:** 95%
**Complexity:** Medium
**Status:** Explored

### 5. Time-Machine Graph Scrubber
**Description:** Dashboard gets a timeline slider reflecting the 8-week seed narrative. Drag to "Week 2" — MongoDB is golden. Drag to "Week 4" — Postgres appears, MongoDB fading. Drag to "Week 8" — MongoDB gone, Prisma established. Each position reflects versioned graph state via Cognee snapshots.

**Warrant:** `direct: seed.py` implies an 8-week timeline with causal progression (MongoDB → incident → Postgres → Prisma). `direct: api.py:45-70` already simulates time — extend to allow seeking. `reasoned:` Interactive demo elements outperform passive ones in judging.

**Rationale:** Time-scrubbing is the showstopper demo moment. Judge drags the slider themselves — interactive, memorable, and the data already exists as a narrative. The "paylink origin story" told in 5 seconds of interaction.

**Downsides:** Requires versioning graph state (snapshot per decision or event log). Non-trivial UX work for the slider + animation.

**Confidence:** 85%
**Complexity:** High
**Status:** Explored

### 6. Session-to-Permanent Memory Promotion
**Description:** Add Cognee session memory with an optional `session_id` parameter on `recall_context`. Session-level memory stores IDE conversation context. After N user confirmations (e.g., 3), auto-promote to permanent memory via `cognee.add()` in a different dataset. Dashboard color-codes nodes by session vs permanent.

**Warrant:** `external:` Cognee docs — session memory with `conversation_id` grouping. `external:` Two-tier memory (session + permanent) is the winning pattern from past Cognee hackathons.

**Rationale:** Single-tier memory is table stakes. Two-tier memory shows sophistication: the system knows the difference between "things we discussed" and "things we decided." This is the architecture judges reward.

**Downsides:** Tracks session state across IDE restarts. Promotion heuristics need tuning — too aggressive = noise in permanent, too conservative = nothing gets promoted.

**Confidence:** 80%
**Complexity:** Medium
**Status:** Explored

### 7. The Nudge — Proactive Memory Push
**Description:** Flip recall from pull to push. A file watcher monitors IDE saves, hashes diffs, and runs `cognee.recall()` on changed patterns automatically. When a match fires, SSE pushes an alert to the dashboard AND the IDE gets an MCP notification without being asked. Dashboard becomes an always-on radar.

**Warrant:** `direct: reviewer_agent.py:12` proves pattern detection works (keyword-based). `reasoned:` Push changes UX from "ask and receive" to "receive before you ask."

**Rationale:** Every other project does pull-based memory. Push is a UX differentiator that makes the system feel alive. Demo: "I typed `npm install mongodb` and before I could write the connection string, ProjectBrain pushed a toast warning about the migration."

**Downsides:** Needs file watcher integration (watchdog library or IDE plugin). Risk of notification fatigue. High implementation complexity for 5-day sprint.

**Confidence:** 75%
**Complexity:** High
**Status:** Explored

## Rejection Summary

| # | Idea | Reason Rejected |
|---|------|----------------|
| 1 | Slime Mold Routing | Too esoteric, implementation unclear, hard to demo |
| 2 | Grief Bot | Ethical sensitivity, outside hackathon scope |
| 3 | API-Behavior Prophet | Speculative, hard to demo convincingly in 3 min |
| 4 | Vicarious Cognee (keystroke tracking) | Privacy optics bad for hackathon demo |
| 5 | Memory Swap Meet (cross-team sharing) | Requires multiple teams simultaneously — can't demo solo |
| 6 | Slow Search Theater | Hurts UX — judges will hate 12-second wait times |
| 7 | 30-Second Self-Demo | Gimmicky, low leverage vs other ideas |
| 8 | Chess Opening Book / Transposition | Interesting but far from existing codebase patterns |
| 9 | Tidal Rhythms (predictive pre-warming) | Requires long data collection, impractical for 7-day sprint |
| 10 | Urban Zoning (memory clustering) | Clever analogy but low practical utility for judges |
| 11 | Pharmacokinetic Half-Life | Better to use Cognee's built-in retention rather than custom math |
| 12 | Branch-Parallel Memory Universes | High complexity for 5-day sprint, nice but risky |
| 13 | Counterfactual Engine | Very creative but unreliable to implement correctly in time |
| 14 | Causal Tree Visualization | Best parts absorbed into Time Machine idea (#5) |
| 15 | Design-Debt Radar | Interesting but secondary priority — nice-to-have |
| 16 | Meta-Compound Scoreboard | Metrics aspect covered by Self-Improvement Loop (#2) |
| 17 | Cold-Start Flex (zero persistence hero) | Novel but directly conflicts with persistence goals |
| 18 | The Amnesia Button | Absorbed into Real Cognee Graph (#1 — uses real forget()) |
| 19 | Muscle Memory (procedural) | Interesting but high risk and speculative |
| 20 | Adaptive Immune Memory | Framing only — absorbed into Self-Improvement Loop (#2) |
| 21 | Remove Decay Simulation | Absorbed into Real Cognee Graph (#1 — real pruning) |
| 22 | Kill-the-Reset | Absorbed into Session-Permanent Promotion (#6) |
| 23 | Stale-Dashboard Alarm | Low leverage vs the real Cognee graph fix (#1) |
