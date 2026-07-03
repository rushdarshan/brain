# Pain & Friction Ideation — ProjectBrain

---

## 1. `improve()` Is a Silent No-Op That Invalidates "Best Use of Cognee"

**Summary:** `memify_feedback` calls `cognee.improve()` with zero arguments. Cognee's `improve()` requires either a `dataset` or a `memory_id` to act on. With neither provided, it resolves to a no-op — returns success, changes nothing. The "Best Use of Cognee" criterion (all 4 verbs working) is the project's headline claim and it is demonstrably false for `improve`. Any judge who runs the `memify_feedback` tool and then checks that a memory actually strengthened will find the system lying: a success message with zero effect.

- **warrant:** `direct: server.py:44-45` — `await cognee.improve()` with no args. Compare with Cognee docs: `improve()` requires target identification. README line 100 claims all 4 verbs mapped.
- **why_it_matters:** Shallowest check a judge can make. Reads the README claim, calls the tool, sees the contradiction. Instant disqualification from "Best Use of Cognee." Self-improvement is the #1 expectation gap flagged in prior external research.
- **meeting_test:** "Run `memify_feedback` with an upvote signal, then `recall_context` and observe no behavioral change in results — does the team accept this before demo day?"

---

## 2. `forget()` Passes a Node ID Where Cognee Expects a Dataset Name

**Summary:** `server.py:62` calls `await cognee.forget(dataset=node_id)`. The `forget` API's `dataset` parameter expects a dataset name string, not a node ID. If the dataset name doesn't exist, Cognee errors. If it happens to match (unlikely with UUID node IDs), it deletes an entire dataset instead of one node. Either outcome is catastrophic for a live demo: opaque traceback or silent data loss.

- **warrant:** `direct: server.py:60-63` — `forget(node_id: str)` maps user-facing node ID to `dataset=node_id`. Cross-reference with Cognee API: `forget()` accepts `dataset` (dataset name) or `memory_id` (specific memory ID). Neither matches a force-graph node ID.
- **why_it_matters:** Second verb in the "all 4 verbs" claim, also broken. Judges who test both `improve` and `forget` see two failures. The pattern suggests neither was tested against Cognee's actual API surface.
- **meeting_test:** "Call `forget` with a real node ID from the dashboard graph — does it error, delete everything, or actually remove one node?"

---

## 3. CI Pipeline Guaranteed to Fail — `pip install cognee` Resolves to Nothing

**Summary:** The CI workflow at `.github/workflows/projectbrain-review.yml:23` runs `pip install cognee`. Cognee is not published on PyPI — it's installable only from GitHub (`pip install git+https://github.com/topoteretes/cognee`). Every single CI run will fail at the dependency install step before the reviewer agent ever executes. The project's most differentiated feature (CI/CD memory gate) is permanently broken out of the box.

- **warrant:** `direct: projectbrain-review.yml:22-23` — `pip install cognee litellm`. External research confirms Cognee is GitHub-only package. No fallback or `pip install git+` in workflow.
- **why_it_matters:** If a judge opens the Actions tab on the GitHub repo, every run is red. The reviewer agent is called out in README (line 91) and judging criteria (Impact, Technical Excellence). A broken CI pipeline signals the project wasn't tested end-to-end.
- **meeting_test:** "Clone fresh, push a PR, check Actions tab — does the memory gate run, or does `pip install` fail immediately?"

---

## 4. "Hebbian Decay" Visual Is Pure Theater — All Values Are Hardcoded

**Summary:** The dashboard terminal overlay (`GraphView.tsx:141-143`) displays `HEBBIAN_DECAY_RATE: 0.05/day` and `RECALL_CONFIDENCE: 94%` as if they are live system metrics. They are static JSX text. Every node has `hotness: 0.8` and every edge has `decay: 0.8` hardcoded in `api.py:41,45`. No node ever ages, no connection ever weakens, no recall confidence is ever computed. The system's core visual metaphor — a decaying, self-pruning memory — is fictional.

- **warrant:** `direct: api.py:41,45` — all nodes get `"hotness": 0.8`, all edges get `"decay": 0.8`. `direct: GraphView.tsx:141-143` — overlay values are static text, not API-derived.
- **why_it_matters:** Judges who read the README's promise of "fading out deprecated patterns" and see the live dashboard will notice the metric never changes. The entire "memory as a living organism" narrative collapses when the numbers are frozen. This is a presentation-tier failure.
- **meeting_test:** "Open dashboard, watch metrics bar for 60 seconds while adding data — does recall_precision or any node hotness change?"

---

## 5. Dashboard Has No MCP Tool Surface — Judges Must Leave the Browser

**Summary:** The dashboard is a purely passive viewer. There is no button, form, or panel to call `remember_decision`, `memify_feedback`, `recall_context`, `promote_context`, or `forget`. A judge must set up a separate MCP-compatible client (Cursor, Claude Code) to exercise the system's 5 MCP tools. In a 3-5 minute demo, requiring an additional tool chain is fatal: most judges will interact only with the dashboard and never see what ProjectBrain actually *does*.

- **warrant:** `direct: page.tsx:1-26` — page exports a single `<GraphView>` component with no tool-triggering UI. `direct: GraphView.tsx:10-185` — all interactivity is search and passive graph rendering. No POST to `/api/webhook/remember`, no tool invocation surface.
- **why_it_matters:** The gap between what the README describes (5 MCP tools) and what the dashboard shows (1 force graph + 1 search box) is jarring. Judges see a static visualization, not a "memory system." The "Best Use of Cognee" criterion requires showing tool usage, which the dashboard actively prevents.
- **meeting_test:** "Give a judge the dashboard URL and nothing else — can they add a memory, search it, confirm it, and delete it from the browser?"

---

## 6. No Entry Friction: No `requirements.txt`, No `.env.example`, No Single-Command Start

**Summary:** A fresh clone has no `requirements.txt` (standard Python convention for enumerating dependencies), no `.env.example` (templated environment file), and no `docker-compose.yml` or `Makefile` for one-command startup. The README lists 4 manual shell commands across 2 terminal windows. Environment variables are documented only in the README table — a judge must read source to know `COGNEE_DATASET`, `ENABLE_BACKEND_ACCESS_CONTROL`, and their defaults. The dashboard's `npm install` and `npm run dev` are separate from Python setup, adding cognitive overhead.

- **warrant:** `direct: repo root` — no `requirements.txt`, no `.env.example`, no `start.sh`/`Makefile`/`docker-compose.yml`. `direct: README.md:39-52` — 4-step setup across 2 terminals. `direct: api.py:2-3` — env defaults set in code, not documented externally.
- **why_it_matters:** Hackathon judging is time-boxed. Every extra minute of setup is a minute of demo lost. The friction stack (no requirements.txt → manual pip install discovery, no .env.example → grep for env vars, two terminals → window management) cumulatively burns judge patience and signals incomplete DX polish.
- **meeting_test:** "Time a judge from 'git clone' to 'see the graph' — is it under 60 seconds with minimal documentation reading?"

---

## 7. Search Results Are Opaque Text Blobs — No Data Lineage, No Graph Backlink

**Summary:** `api.py:156` returns search results as `str(r)` — raw stringified Cognee output. The dashboard renders these as plain text in a scrollable list (`GraphView.tsx:171-178`) with no link back to the graph node that produced them. A judge who searches "postgres" sees text about the Postgres migration but can't click through to the corresponding blue graph node. Results are disconnected from the knowledge representation they came from.

- **warrant:** `direct: api.py:156` — `{"text": str(r), "score": getattr(r, "score", None)}`. No node ID, no dataset, no provenance. `direct: GraphView.tsx:170-178` — `r.text` rendered as `<p>`, no click handler to focus the graph on this node.
- **why_it_matters:** Graph-search duality is a Cognee differentiator (graph-vector hybrid). The dashboard breaks this link. A judge sees a graph they can't query and search results they can't trace. The two views feel like different systems, not one unified memory.
- **meeting_test:** "Search 'MongoDB' — can you click a result and highlight the MongoDB decision node on the graph? If not, what does search add that a grep doesn't?"

---

## 8. Seed Data Has No Narrative Arc — Judges Can't "Discover" the Story

**Summary:** The seed dataset (`seed.py:7-28`) is a flat chronological dump of 28 paylink decisions. There is no guided demo flow, no progressive reveal, and no "aha moment" built into the data. A judge opening the dashboard sees a dense force graph with all labels visible and must individually read each node to understand the MongoDB→Postgres migration story. The supersede chain exists in text ("Supersedes: Use MongoDB...") but is never surfaced structurally — no timeline view, no diff view, no "what changed between week 2 and week 3" visualization.

- **warrant:** `direct: seed.py:7-28` — all items `supersedes` fields are text strings embedded in freeform text, not structured relationships. `direct: api.py:43-46` — graph loading reads Cognee provenance but only extracts top-level `source/target/relation` — supersedes semantics are lost. `direct: GraphView.tsx` — no timeline control, no playback, no visualization of decision evolution.
- **why_it_matters:** The best demos tell stories. The seed data contains a compelling story (MongoDB disaster → Postgres migration → JWT leak → session auth) but the system doesn't surface it. A judge skimming the graph sees noise, not narrative. The project loses the "Presentation" and "Creativity" criteria because there's nothing to present.
- **meeting_test:** "Open the dashboard — in 10 seconds, can you tell me the project's most important decision evolution? If not, no judge will either."
