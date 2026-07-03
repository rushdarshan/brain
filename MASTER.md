# ProjectBrain — Master Document

Single source of truth for Devpost entry, README, demo script, and submission. Everything derives from here.

---

## 1. Devpost Entry

### Title

ProjectBrain: Persistent Organizational Memory for AI Development

### Tagline

Stop AI amnesia. ProjectBrain turns your architectural decisions into a live, searchable knowledge graph that AI tools and CI/CD both respect.

### Description

ProjectBrain is a persistent memory layer that cures "Context Rot" — the phenomenon where AI assistants, teammates, and CI/CD pipelines drift dangerously far from the project's architectural truth.

Built on **Cognee's graph-vector hybrid store**, ProjectBrain:
- **Remembers** every architectural decision, incident, and metric as nodes in a knowledge graph, linked by relationships (SUPERSEDES, IMPACTS, CAUSES)
- **Searches** with 17 different modes (graph completion, keyword, similarity, chain-of-thought, and more) so you can query your organizational memory the way you think
- **Enforces** knowledge through a CI/CD reviewer agent that rejects PRs reintroducing superseded patterns
- **Visualizes** the entire memory as a live force-directed graph, updated in real-time via SSE
- **Sessions** let you experiment with context without polluting permanent memory, then promote what matters

**Architecture:** Three lightweight processes — an SSE-backed REST API (FastAPI, port 8000), an MCP server for IDE integration (Cursor, Claude Code, any MCP host), and a Next.js 16 dashboard — all wired to Cognee Cloud.

**The result:** Your AI tools never forget what your team decided last week. Your CI/CD never approves a PR that reintroduces a pattern you deprecated last month. Your dashboard shows you the living history of your project's architecture.

### Tech Used

- **Cognee Cloud** — graph-vector knowledge graph, 17 search modes, `add`/`cognify`/`search`/`improve`/`forget` verbs
- **FastAPI** — SSE streaming backend
- **FastMCP** — Model Context Protocol (MCP) server for IDE tool integration
- **Next.js 16** — React 19, App Router, force-directed graph dashboard
- **react-force-graph-2d** — D3 force simulation visualization
- **uvicorn** — ASGI server
- **Tailwind CSS 4** — Dashboard styling
- **Groq (llama-3.3-70b-versatile)** — LLM for graph completion search
- **GitHub Actions** — CI/CD reviewer agent

### Collaborators

Solo entry.

### Category Tags

Developer Tools, AI/ML, Open Source, Infrastructure

---

## 2. README Content

(Blocks ready for `README.md`. Current `README.md` should be overwritten with this content before submission.)

See the existing `README.md` — it's already strong. At submission time, update it from this section for freshness.

### Key changes to make in README before submission

- Update Architecture diagram to show Cognee Cloud (not local Kuzu/LanceDB)
- Add MASTER.md reference in Demo section
- Update judging criteria table if new features (graph makeover, meta-narrative, safety net) are implemented

---

## 3. Demo Script

**Total target:** 3:00–4:00 minutes
**Tool:** OBS Studio or Xbox Game Bar

| Time | Visual | Audio |
|------|--------|-------|
| 0:00–0:15 | Title card: "ProjectBrain — Persistent Organizational Memory" | *Background music fades in* |
| 0:15–0:45 | Dashboard opens at Railway URL. Seed data graph visible. | "This is ProjectBrain. It's a persistent memory layer for your codebase. Every architectural decision, every incident, every metric — it's all here as nodes in a knowledge graph. This graph updates in real-time." |
| 0:45–1:15 | Click a node → detail panel slides in. Show SUPERSEDES edge. | "Click any node to see its details. Notice this decision to use Postgres — it supersedes the earlier MongoDB decision. The graph captures both the decision and why it changed." |
| 1:15–1:45 | Switch search mode dropdown. Type a query. Show results. | "Search across modes — graph completion, keyword, similarity, chain-of-thought — all 17 Cognee search modes are available. This is how you query your organizational memory." |
| 1:45–2:15 | Switch to terminal. Run `demo_seed.py`. Graph grows live. | "Now let's see the memory grow. I'm adding new decisions one at a time. Watch the graph update with each entry — the SSE stream pushes updates to the dashboard in real-time." |
| 2:15–2:45 | Show PR with the reviewer_agent CI check (if ready) or show MCP tool via Cursor. | "ProjectBrain also enforces memory. The CI/CD reviewer agent checks every PR against the knowledge graph. Try reintroducing a deprecated pattern — it gets blocked. Or use the MCP tools directly from your IDE to remember decisions without leaving your editor." |
| 2:45–3:00 | Scroll metrics bar. Show node/edge counts, latency, memory composition. | "Real-time metrics show you graph health — node and edge counts, search latency, memory composition breakdown. Everything is live." |
| 3:00–3:15 | Closing card: GitHub repo + Cognee logo | "ProjectBrain: because your team's decisions should be the last thing your AI forgets. Built on Cognee for the WeMakeDevs × Cognee Hackathon." |

### Pro tips

- Pre-warm: start `api.py`, `seed.py`, and dashboard *before* recording
- If using Railway URL, make sure it resolves before the screen recording starts
- Use a large font in the terminal for `demo_seed.py`
- Record in 1080p, 30fps
- Add subtitles (YouTube auto-captions are fine)

---

## 4. Submission Checklist

### Before recording the demo video

- [ ] `api.py` starts without error
- [ ] `seed.py` runs and populates graph
- [ ] Dashboard renders at Railway URL (or localhost:3000)
- [ ] SSE stream works (graph is live)
- [ ] Search returns results for ~2 search modes
- [ ] Node click panel works (if D3 implemented)
- [ ] Edge filter works (if D3 implemented)
- [ ] `demo_seed.py` runs and graph grows incrementally (if D5 implemented)
- [ ] Metrics bar shows real data
- [ ] reviewer_agent.py passes (or skip if not needed for demo)

### Before Devpost submission

- [ ] Demo video recorded, rendered, uploaded to YouTube (unlisted) — URL saved
- [ ] README.md updated from MASTER.md section 2
- [ ] Devpost entry filled from MASTER.md section 1
- [ ] GitHub repo is public (or accessible to judges)
- [ ] Railway deployment is live and URL tested
- [ ] Tags selected: Developer Tools, AI/ML, Open Source, Infrastructure
- [ ] Collaborators confirmed
- [ ] "Built with Cognee" badge in README

### Final sanity checks

- [ ] Open incognito window, navigate to Railway URL — everything works
- [ ] Demo video plays through without glitches
- [ ] README renders on GitHub without broken links
- [ ] Devpost preview looks clean
- [ ] Submission submitted before Jul 5 deadline

---

*Generated 2026-07-02. Update before each recording/submission pass.*
