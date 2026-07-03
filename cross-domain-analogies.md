# Cross-Domain Analogy: ProjectBrain Ideas

---

## 1. Mycelial Nutrient Propagation — decision weight diffusion

**Analogy:** Mycelium networks — when a fungus finds a nutrient source, signals propagate through the underground mycelial web. Adjacent nodes benefit; distant nodes feel a weaker signal.

**Idea:** When a pattern in permanent memory is successfully reused (no rollback, no regression in 30 days), propagate a "nutrient signal" through the decision graph — reinforcing related decisions at diminishing intensity. A pattern that feeds other patterns becomes more authoritative. A pattern that keeps failing starves its neighbors, lowering their confidence scores.

**Warrant:** `reasoned:` The current system has static weights. The analogy maps cleanly: decision graph = mycelial network, pattern reuse = nutrient discovery, confidence scores = nutrient concentration. Implementation is a BFS propagation with exponential decay — no new infra needed.

**Why it matters:** Patterns don't exist in isolation. A decision about "why we chose PostgreSQL over MongoDB" is reinforced every time someone chooses PostgreSQL for a new service. Without propagation, each decision lives or dies alone, and the graph never learns from its own success.

**Meeting test:** "I see the same decision keep resurfacing independently in different teams. Shouldn't repeated independent convergence on an answer strengthen it?"

---

## 2. Sleep-Memory Consolidation — nightly pattern extraction cron

**Analogy:** During sleep, the hippocampus replays the day's experiences to the neocortex, consolidating short-term memories into long-term ones. Without sleep, memories stay brittle and context-bound.

**Idea:** A daily cron job runs over session memory from the past 24h, clusters related entries, extracts decision-adjacent signals (rejected approaches, reasoning fragments, dead ends), and upserts them into permanent memory as low-confidence candidates — which human review can promote or demote. Session memory remains the fast, ephemeral store; permanent memory becomes the consolidated "cortex."

**Warrant:** `direct:` ProjectBrain already has two-tier memory (session/permanent) and real metrics. A cron that reads session, deduplicates against permanent, and upserts candidates via existing MCP tools requires no new database or API.

**Why it matters:** The biggest adoption barrier for knowledge-capture tools is the manual effort of documenting. If the system passively consolidates overnight — extracting the pattern from the session without the user doing anything — adoption goes from "remember to document" to "wake up and find it documented."

**Meeting test:** "I had a 3-hour debugging session. Tomorrow morning, the root cause and fix are already in permanent memory. I just confirm or dismiss."

---

## 3. Kintsugi / Golden Seams — making failure visible as teaching artifact

**Analogy:** Japanese kintsugi repairs broken pottery with gold lacquer, making the break visible and beautiful — the repair becomes the most valuable part of the object.

**Idea:** When a pattern is superseded or a decision is reversed, ProjectBrain doesn't delete or overwrite — it "golds the seam." The old decision stays in the graph with a visible link to the new one, annotated with why it was replaced, the cost of the failure, and the trigger (rollback, incident, performance regression). Each seam is surfaced in the dashboard as a teaching node, not a dead node.

**Warrant:** `direct:` The force-graph already renders nodes and edges. A seam is just a styled edge with metadata. The MCP `log_decision` tool already accepts metadata; adding a `supersedes` field and rendering it as a gold connector is a client-side change.

**Why it matters:** Orgs hide failures. Hidden failures repeat. If every reversed decision is rendered as a visible, citable, beautiful artifact, new team members navigate the graph and see not just "what we decided" but "what we decided then un-decided and why." That's the anti-fragile loop.

**Meeting test:** "Can I see, on the graph, every time our team reversed a major decision in the last quarter, and understand what changed?"

---

## 4. Fire Lookout + Controlled Burns — proactive low-severity surfacing

**Analogy:** Fire lookouts spot smoke early. Land managers set controlled burns to clear underbrush so natural fires stay manageable and don't become megafires.

**Idea:** ProjectBrain's CI/CD reviewer already blocks PRs that violate patterns. Controlled burns invert this: the system proactively generates "low-severity advisories" for patterns approaching violation. When a feature branch's dependency graph shows growing distance from an established pattern, the reviewer issues a yellow-level warning (not a block): "You're diverging from pattern X. Acknowledge or fix." This surfaces tech debt drift before it becomes a protocol-breaking change.

**Warrant:** `external:` The reviewer agent exists. Controlled burns require predictive scoring — detecting *approaching* divergence, not just *current* violation. This needs a distance metric between PR dependency graph and the decision graph, which is an algorithmic addition but no new infra.

**Why it matters:** The reviewer that only blocks at PR time is a check, not a coach. Controlled burns reduce surprise — teams see drift warnings at day 2 of a 3-week sprint, not at merge-block time. Fewer emotional firefights, more calm corrections.

**Meeting test:** "Why did no one warn me 5 days ago that I was drifting from the established pattern? I could have corrected then instead of rewriting 500 lines today."

---

## 5. Dark Matter Detection — surfacing implicit decisions via gravitational effects

**Analogy:** Dark matter is invisible — we detect it only by its gravitational effects on visible matter (galaxy rotation curves, gravitational lensing). We know it's there because things move as if it is.

**Idea:** Some of the most important organizational decisions leave no explicit trace — a meeting where a direction was agreed on Slack, a ticket that was closed without resolution, a comment thread where an alternative died. ProjectBrain detects these "dark decisions" by their gravitational effects on the visible decision graph: a PR that makes a choice without citing a precedent, a code review comment that references a conversation with no artifact, a pattern reversal without a logged superseding decision. The dashboard surfaces these as gravitational anomalies — "A decision appears to exist here but has no recorded artifact."

**Warrant:** `external:` Requires heuristics for detecting implicit decisions — git blame reversing a past pattern without a logged decision, PR comment analysis, meeting transcript ingestion. Some of these the current system can't yet consume (Slack, meetings). The detection layer is new, but the rendering infra (force-graph anomaly nodes) exists.

**Why it matters:** The most dangerous decisions are the invisible ones. If ProjectBrain can surface "there's a ghost pattern here — something changed but nothing is documented," it triggers the human to fill the gap. Over time, dark matter becomes visible matter.

**Meeting test:** "We had four PRs this month that all contradict established pattern X, but none of them logged a decision to abandon it. The system should flag that as an anomaly."

---

## 6. Tectonic Plate Theory — organizational fault line detection

**Analogy:** Earthquakes occur at fault lines where tectonic plates grind past each other. Stress accumulates slowly over years, then releases catastrophically in seconds. Seismologists map fault lines by tracking microseismic activity.

**Idea:** ProjectBrain maps "organizational fault lines" — pairs or groups of teams whose decisions consistently conflict. When Team A chooses pattern X and Team B chooses ~X (the inverse), the system logs a friction event. Over time, it builds a fault map: which teams have the highest decision friction, on which domains. Before a reorg or a cross-team initiative, leadership reviews the fault map to know where stress has accumulated.

**Warrant:** `reasoned:` This is a meta-analysis over the existing decision graph. Conflict detection is graph-theoretic — two decisions on the same domain with opposing values. The dashboard already renders the graph; a fault-line overlay is an additional visualization, not new data collection.

**Why it matters:** Reorgs fail when leadership doesn't know where the real friction lives. A fault map makes invisible organizational stress visible — leadership sees not just "these teams report friction" but "these teams made 47 conflicting decisions in the last 6 months on database choice alone."

**Meeting test:** "Before we restructure the platform team, show me which squads have the most accumulated decision conflict and on which technical domains."

---

## 7. Olfactory Pattern Recognition — broad-tuned fuzzy matching

**Analogy:** The human olfactory system has ~400 receptor types. Each receptor is broadly tuned to many molecules; a smell is recognized by the pattern of activation across all receptors, not by exact molecular match.

**Idea:** Instead of requiring exact keyword/pattern matches to surface past decisions, ProjectBrain implements "olfactory encoding": each decision is projected onto a set of fuzzy dimensions (e.g., architectural layer, tradeoff type, affected service category, team boundary, latency sensitivity). A new PR is encoded onto the same dimensions, and the system surfaces past decisions by similarity of activation pattern — not by shared keywords. A PR about "caching strategy for user profiles" would surface a past decision about "Redis vs Memcached" even if neither word "Redis" nor "cache" appears in the PR title.

**Warrant:** `reasoned:` The 17 search modes suggest embedding-based search might already exist or be close. Olfactory encoding = dimensionality reduction + similarity search. This is an algorithmic upgrade to search, not a new system — but the quality of dimensions requires careful design.

**Why it matters:** Exact-match recall is what makes knowledge bases fail. "I didn't know to search for Redis because I didn't know we had a Redis decision." Fuzzy pattern matching means the system volunteers past decisions before the user knows they exist.

**Meeting test:** "I opened a PR about session storage for a new service, and the system surfaced a 14-month-old decision about why we don't use Redis for stateful data. I would never have searched that."

---

## 8. Quantum Error Correction — redundant encoding of critical decisions

**Analogy:** Quantum error correction encodes one logical qubit across many physical qubits. A parity check detects when one physical qubit has drifted without collapsing the state. You correct the drift, and the logical qubit survives.

**Idea:** When a pattern is identified as "critical" (high fan-out, high rollback cost, cross-cutting), ProjectBrain encodes it redundantly across multiple contexts: the original PR, the design doc, the configuration file comment, the runbook. Each copy is a "physical qubit." Periodically, the system runs a "parity check" — comparing the copies for drift. If the PR says one thing and the runbook says another, the system flags the "qubit drift" and proposes which copy to correct. The logical decision survives even as individual artifacts evolve.

**Warrant:** `external:` Requires identifying critical patterns (fan-out analysis — graph-traversal, exists-ish), ingesting non-PR artifacts (design docs, runbooks — not yet wired), and running diff-based parity checks. New ingestion surface, but the concept is simple: compare all encodings of the same decision and flag disagreement.

**Why it matters:** Decisions decay because they're written once (the PR) and never revisited. Runbooks drift. READMEs drift. Configs drift. QEC means the decision stays coherent across all the places it's encoded, and the system surfaces drift without a human having to audit.

**Meeting test:** "Our runbook says to use the old deployment strategy, but our PR decision from 8 months ago chose the new one. The system caught the drift and asked us to reconcile."
