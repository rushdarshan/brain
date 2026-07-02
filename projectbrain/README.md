# ProjectBrain

> *RAG gives your AI a library card. Cognee gives it a memory. ProjectBrain gives it a conscience.*

**ProjectBrain** is a persistent memory layer for your codebase, built on [Cognee](https://github.com/topoteretes/cognee) and the Model Context Protocol (MCP). It cures "Context Rot" by remembering your architectural decisions, fading out deprecated patterns, and enforcing rules across your team.

Built for the **WeMakeDevs × Cognee "Hangover Part AI" Hackathon** (Jun 29 – Jul 5, 2026).

## Architecture

```
┌──────────────────┐     SSE /api/stream      ┌──────────────────┐
│  api.py          │◄────────────────────────►│  Next.js         │
│  FastAPI + SSE   │   HTTP /api/graph,/search │  Dashboard       │
│  Port 8000       │                          │  Port 3000       │
└─────┬────────────┘                          └──────────────────┘
      │ HTTP /api/notify (SSE push trigger)
      │
┌─────▼────────────┐
│  server.py       │  MCP server (FastMCP)
│  Port N/A (stdio)│  Tools: remember_decision, recall_context,
│                   │  promote_context, memify_feedback, forget
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Cognee (1.2.2)                             │
│  ├─ Kuzu (embedded graph DB)                │
│  ├─ LanceDB (embedded vector store)         │
│  └─ Groq LLM (llama-3.3-70b-versatile)     │
│     + fastembed (BAAI/bge-small-en-v1.5)     │
└─────────────────────────────────────────────┘
```

**Two datasets:** `paylink` (permanent knowledge) and `paylink-session` (session context, cleared on restart). Session items can be promoted to permanent via the MCP tool or API.

## Quickstart

```bash
# 1. Set your Groq API key
$env:GROQ_API_KEY = "gsk_..."

# 2. Seed the knowledge graph with sample data
cd projectbrain
python seed.py

# 3. Start the backend (SSE + REST API)
python api.py

# 4. Start the dashboard (separate terminal)
cd dashboard
npm run dev
```

**Environment variables:**

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Required. Get one at console.groq.com |
| `COGNEE_DATASET` | `paylink` | Dataset name for permanent knowledge |
| `ENABLE_BACKEND_ACCESS_CONTROL` | `false` | Must be false for single-user mode |

## Features

### Dashboard (`localhost:3000`)
- **Force-directed graph** — real-time visualization of knowledge nodes and relationships via SSE
- **17 search modes** — dropdown selector for all Cognee `SearchType` modes (GRAPH_COMPLETION, GRAPH_COMPLETION_COT, KEYWORD, SIMILARITY, etc.)
- **Search panel** — query the knowledge graph, results shown below the graph
- **Metrics bar** — node/edge counts, memory composition, search latency, recall/review accuracy
- **SSE auto-reconnect** — stale-data warning banner on disconnect

### MCP Server (stdio)
Connect to Cursor, Claude Code, or any MCP-compatible IDE:

- `remember_decision` — ingest a decision into permanent memory
- `recall_context(scope: "all"|"permanent")` — search memory with dataset scope
- `promote_context` — move session context to permanent
- `memify_feedback` — strengthen/confirm a decision
- `forget` — remove a node

### REST API (`localhost:8000`)
- `GET /api/graph` — current knowledge graph
- `GET /api/stream` — SSE stream of graph updates
- `GET /api/search?q=...&mode=...` — search with any of 17 modes
- `GET /api/search/modes` — list available search modes
- `GET /api/metrics` — live metrics (node/edge counts, composition, latency)
- `POST /api/remember/session` — add to session memory
- `POST /api/remember/promote` — promote session to permanent

### CI/CD Reviewer Agent
`reviewer_agent.py` runs as a GitHub Action on every PR. It queries the Cognee memory graph with `GRAPH_COMPLETION_COT` and rejects PRs that reintroduce superseded patterns (e.g., MongoDB, JWT). Exit code 0 = approved, 1 = rejected.

## Judging Criteria

| Criteria | How ProjectBrain delivers |
|---|---|
| **Impact** | Stops AI amnesia and architectural regression across the entire engineering team |
| **Creativity** | First of its kind: organizational memory wired directly into AI tools via MCP + CI/CD enforcement |
| **Technical Excellence** | Three-process architecture (SSE backend + MCP server + dashboard) over Cognee's graph-vector hybrid store |
| **Best Use of Cognee** | Maps all 4 verbs (add→cognify, search, improve, forget) across the full 17-mode search spectrum; dual-dataset session memory |
| **UX** | Developer never leaves IDE. MCP tools + real-time dashboard with zero-config SSE streaming |
| **Presentation** | This README, a 3-minute demo video, and a writeup of the architecture and results |

## Tech Stack

- **Cognee 1.2.2** — graph-vector memory, 17 search modes, Kuzu + LanceDB embedded
- **FastAPI** — SSE streaming backend
- **MCP (FastMCP)** — IDE tool integration
- **Next.js 16** — real-time force-directed graph dashboard
- **React Force Graph 2D** — D3 force simulation visualization
- **Groq (llama-3.3-70b-versatile)** — LLM for graph completion search
- **GitHub Actions** — CI/CD reviewer agent

## Demo

1. Open `localhost:3000` — seed data visible as a force-directed graph
2. Pick a search mode from the dropdown, type a query — results appear below the graph
3. Use the MCP tools via Cursor/Claude Code to `remember_decision` — graph updates in real-time via SSE
4. Add session context, then `promote_context` to permanent
5. Metrics bar shows node/edge counts, latency, and memory composition
6. CI/CD reviewer blocks PRs with deprecated patterns

## License

MIT
