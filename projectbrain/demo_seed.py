"""Live graph growth demo — posts decisions one at a time, graph grows via SSE."""

import argparse, asyncio, httpx, sys

API = "http://127.0.0.1:8000"

entries = [
    {"title": "Add WebSocket fallback for SSE", "rationale": "Some corporate proxies block SSE. WebSocket fallback ensures memory is always accessible.", "files": ["api.py"], "tags": ["infra", "resilience"], "supersedes": None},
    {"title": "Cache frequent searches in Redis", "rationale": "GRAPH_COMPLETION_COT searches take 2-3s. Caching top-10 queries reduces p95 latency by 60%.", "files": ["api.py"], "tags": ["performance", "cache"], "supersedes": None},
    {"title": "Support multi-user workspaces", "rationale": "Team adoption requires per-user namespacing. Each team gets an isolated dataset under the same Cognee Cloud tenant.", "files": ["api.py", "server.py"], "tags": ["auth", "multi-tenant"], "supersedes": None},
    {"title": "Export graph as JSON for external tools", "rationale": "Data teams want to import the knowledge graph into Tableau and Grafana. JSON export endpoint enables this.", "files": ["api.py"], "tags": ["api", "data"], "supersedes": None},
    {"title": "Add vector similarity search to CI reviewer", "rationale": "Keyword matching misses semantically similar deprecations. Vector search catches 'database-as-queue' patterns even when the specific library name differs.", "files": ["reviewer_agent.py"], "tags": ["ci", "search"], "supersedes": None},
    {"title": "Notify Slack on deprecation violations", "rationale": "Developers should know immediately when a PR introduces a deprecated pattern. Slack webhook integration closes the feedback loop.", "files": ["reviewer_agent.py"], "tags": ["ci", "notifications"], "supersedes": None},
    {"title": "Batch cognify for faster graph rebuilds", "rationale": "Cognifying 50+ items individually is slow. Batch processing groups items by topic and cognifies once.", "files": ["api.py"], "tags": ["performance", "memory"], "supersedes": None},
    {"title": "Add rate limiting to remember endpoint", "rationale": "Prevent accidental or malicious memory flooding. 10 requests/minute per IP is a sane default.", "files": ["api.py"], "tags": ["security", "infra"], "supersedes": None},
    {"title": "Dashboard dark mode toggle", "rationale": "Developer tools should respect OS preferences. Auto-detects system theme with manual override.", "files": ["dashboard/src/app/page.tsx"], "tags": ["ui", "ux"], "supersedes": None},
    {"title": "Auto-tag decisions with LLM", "rationale": "Users forget to tag decisions. An LLM pass over the rationale generates relevant tags automatically on ingest.", "files": ["api.py"], "tags": ["llm", "automation"], "supersedes": None},
]

async def main():
    parser = argparse.ArgumentParser(description="Demo seeding")
    parser.add_argument("--count", type=int, default=len(entries), help="Number of entries to seed")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between entries")
    args = parser.parse_args()

    selected = entries[:args.count]
    print(f"Demo seeding {len(selected)} entries every {args.delay}s...")
    print()

    async with httpx.AsyncClient() as client:
        for i, entry in enumerate(selected, 1):
            try:
                r = await client.post(f"{API}/api/webhook/remember", json=entry, timeout=30.0)
                if r.status_code == 200:
                    print(f"  [{i}/{len(selected)}] Added: {entry['title']}")
                else:
                    print(f"  [{i}/{len(selected)}] FAILED ({r.status_code}): {entry['title']}")
            except httpx.RequestError as e:
                print(f"  [{i}/{len(selected)}] ERROR: {e}")
                print("Is the API server running?")
                sys.exit(1)
            if i < len(selected):
                await asyncio.sleep(args.delay)

    print()
    print("Done. Graph updated in real-time via SSE.")

if __name__ == "__main__":
    asyncio.run(main())
