---
date: 2026-07-02
updated: 2026-07-04
topic: projectbrain-win
focus: now can we win
mode: repo-grounded
---

# Ideation: ProjectBrain — Now Can We Win?

## Grounding Context

**Codebase:** Python (FastAPI + Cognee SDK 1.2.2 + MCP SDK) + Next.js 16 dashboard (React 19, Tailwind 4, react-force-graph-2d). Cognee Cloud connected (tenant-760a20b9). MCP server with 4 tools (remember_decision, recall_context, memify_feedback, forget). Real-time SSE-pushed force-graph dashboard.

**Current state:** Cognee Cloud connected and working. 12 seed decisions ingested via `seed.py` → 164 nodes, 163 edges in Cognee Cloud. API running, metrics endpoint with real counters, search returning GRAPH_COMPLETION results. Session/permanent memory endpoints exist.

**Gaps confirmed live:** Dashboard is an unpolished starting point. No README. No demo video. No Devpost submission. Graph is near-complete connectivity (163 edges/164 nodes = hairball). `forget()` has no safety — one wrong call wipes the demo.

**External context:**
- Jun 29–Jul 5, 2026 hackathon. 2 days remaining.
- Two grand prize tracks: Best Use of Open Source (MacBook Neo/team) and Best Use of Cognee Cloud (iPhone 17/team)
- 6 judging criteria: Potential Impact, Creativity & Innovation, Technical Excellence, Best Use of Cognee, User Experience, Presentation Quality
- Past Cognee hackathon winners won on: self-improvement with before/after metrics, two-tier memory, demonstrated lifecycle API usage
- Winning pattern: show, don't just tell. Concrete numbers > feature lists. "Best Use of Cognee" is the highest-leverage criterion — most entrants use Cognee shallowly

## Ranked Ideas

### 1. Devpost-First: One Artifact Feeds All
**Description:** Write Devpost submission as the master document. README is extracted from it. Demo script is extracted from it. Presentation arc is the Devpost claims proven live. One writing cycle feeds 4 judging criteria with no redundancy.
**Warrant:** `reasoned:` Most teams write README, Devpost, and presentation as separate documents — 3x editing time, 3x drift risk. One source of truth with extraction markers eliminates overhead.
**Rationale:** The submission IS the project for a remote hackathon. If Devpost is weak, the project doesn't exist to judges. This is table stakes with a leverage multiplier.
**Downsides:** Requires maintaining one document with extraction markers. Minor friction vs totally separate docs.
**Confidence:** 95%
**Complexity:** Low
**Status:** Unexplored — needs YouTube video + Google Form

### 2. One-Button Cloud Deploy
**Description:** Deploy FastAPI (+ MCP server) to Railway and Next.js dashboard to Vercel. Live URL for judges instead of clone instructions. Setup = click + paste Cognee API key.
**Warrant:** `reasoned:` Every second of local-setup friction reduces the chance a judge tries the product. A live URL pre-fills the UX criterion because the experience begins at "click," not "install Python 3.11+."
**Rationale:** Most projects require local setup. One that works immediately at a URL wins UX by default. Also proves production-readiness for Impact criterion.
**Downsides:** Railway/Vercel free tier limits. Cognee API key handling on a public URL differs from local.
**Confidence:** 85%
**Complexity:** Medium
**Status:** ✅ DONE (Railway auto-deploy from master)

### 3. Graph Makeover: From Spiderweb to Signal
**Description:** Current 164-node, 163-edge graph is near-complete connectivity — a hairball. Add: edge-weight threshold slider, click-to-expand node detail panel (memory provenance), colored node-type legends. Turns existing data from confusing to impressive.
**Warrant:** `direct:` 163 edges / 164 nodes → near-1:1 ratio, every node connected to everything, zero information. `reasoned:` A knowledge graph that looks like noise undermines Technical Excellence and UX simultaneously. Fix is frontend filtering.
**Rationale:** The force graph is the first thing a judge sees. A 2-hour UI pass transforms it from "what am I looking at" to "wow, I can explore the decisions."
**Downsides:** Requires dashboard work. CSS + force graph params can be fiddly. Must consult Next.js docs per AGENTS.md.
**Confidence:** 90%
**Complexity:** Medium
**Status:** ✅ DONE (time slider, tabs, metrics history, all deployed)

### 4. Self-Referential Meta-Narrative
**Description:** Starting now, every decision about ProjectBrain in the final 2 days goes through `remember_decision`. The demo opens with the dashboard showing the hackathon's own decision graph. "We built a memory system. Then we used it to remember building itself."
**Warrant:** `direct:` The system works — MCP tools, graph, SSE stream. It just needs to be used. `reasoned:` Self-referential demos are the highest-memorability format in hackathons. Pre-empts "does this actually work?" by showing it working on itself.
**Rationale:** Every project demos their feature. Only one demos their own creation story through their own tool. The meta-narrative sticks in deliberation.
**Downsides:** Requires discipline to log decisions for 2 days. If you forget to remember, the graph has gaps.
**Confidence:** 95%
**Complexity:** Low (zero new code)
**Status:** ⚠️ PARTIAL — dashboard subtitle reads "A self-improving project memory..."; not maximized

### 5. Live Graph Growth Demo Flow
**Description:** Demo starts empty/minimal. As the presenter walks the narrative, decisions get added via MCP tools, and the force graph populates live via SSE. The graph growing IS the demo. Ends with 160+ nodes the judge watched appear.
**Warrant:** `direct:` SSE stream + MCP tools already work end-to-end. This is choreography, not new code. `reasoned:` A living graph that populates while the judge watches is what they describe to co-judges.
**Rationale:** The "wow" moment. Judges see a growth story live. Hits Creativity, UX, Best Use of Cognee, Technical simultaneously.
**Downsides:** Needs rehearsal. Screen capture must work. If SSE fails, graph doesn't grow.
**Confidence:** 85%
**Complexity:** Low (choreography, not code)
**Status:** ⚠️ PARTIAL — SSE + timeline work; no choreographed demo flow scripted

### 6. Forget Safety Net
**Description:** Soft-confirm on `forget()` showing impact ("This will erase {N} nodes..."). Dashboard undo toast. Prevents presenter from accidentally wiping the graph mid-demo.
**Warrant:** `direct:` `server.py:66-68` — forget has zero confirmation. One fat-fingered `forget()` in a live demo and the graph is gone. `reasoned:` Presenter sweating because they nuked their own demo is a common hackathon failure mode.
**Rationale:** 5 lines of code eliminates a catastrophic demo failure. Cheapest insurance policy.
**Downsides:** None meaningful.
**Confidence:** 99%
**Complexity:** Low (5 lines)
**Status:** ❌ NOT DONE — no soft-confirm, no undo toast

## Rejection Summary

| # | Idea | Reason Rejected |
|---|------|-----------------|
| 1 | Auto-Capture (file events auto-remember) | Too expensive for 2 days — needs file watcher + IDE plugin |
| 2 | Proactive Push (memory finds you) | Complex file-watch logic for 2-day sprint |
| 3 | Immune System Memory (hooks everywhere) | Too expensive for remaining time |
| 4 | Strip Everything, Ship Cognee Showcase | Too extreme — we have working code, don't delete it |
| 5 | Sell to Manager / Org Governance | Too big a pivot for 2 days |
| 6 | Circuit Breaker (halt agent on low confidence) | Complex, needs production data to calibrate |
| 7 | Gray-Matter Pruning | Background job risk, could break graph |
| 8 | Fog of War / Minimap | Cool viz but complex for remaining time |
| 9 | Compound Interest Dashboard | Nice-to-have, absorbed into Graph Makeover |
| 10 | Coach's Film Study / Session Tagging | Complex for 2-day sprint |
| 11 | Hippocampal Replay / Background Consolidation | Interesting but not implementable in 2 days |
| 12 | Speedrun Save States | Fun but too complex for 2-day sprint |
| 13 | Memory-as-Service Pivot | Too big — keep focus on IDE memory |
| 14 | Submit MCP as standalone pip package | Tightly coupled to FastAPI backend, extraction takes time |
| 15 | 1M-Node Firehose Demo | Cognee Cloud credit cost, demo doesn't need scale |
| 16 | 30-Second Blitz | Too compressed for hackathon judging format |
| 17 | The Anti-Demo (judge's own repo) | Too risky — live unscripted demo could fail |
| 18 | 10x-Time Polisher (test suite) | Low ROI — judges don't run tests |
| 19 | The Dead Demo (static graph) | Absorbed into Graph Makeover (#3) |
| 20 | Recency ≠ Memory (dedup) | Important but not a differentiator for judges |
| 21 | SSE Stream Subscriptions (dashboard fix) | Bug fix, not an idea — already needed |
| 22 | Auto-Generated Submission | Too complex (Puppeteer, session replay) vs Devpost-First (#1) |
| 23 | Delete MCP Server | Removes the MCP differentiator — bad idea |
| 24 | Self-Installing Extension | Too complex for 2 days |
| 25 | Cognee Architecture Diagram | Low-effort but absorbed into Devpost-First (#1) |
| 26 | The "Before" Demo | Good but absorbed into Live Graph Growth (#5) |
| 27 | Screencast MCP Integration | Part of Devpost-First (#1) content production |
| 28 | Real-Time Graph Growth | Kept as #5 |
| 29 | Consolidate 3 Files into 1 | Absorbed into Devpost-First (#1) |
