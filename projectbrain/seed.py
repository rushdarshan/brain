import asyncio, os
import cognee
from cognee_init import init_cognee

DATASET = os.getenv("COGNEE_DATASET", "paylink")

seed_items = [
    # Meta-narrative: ProjectBrain's own development story
    {"title": "Adopt Cognee Cloud for memory backend", "rationale": "Local Kuzu + LanceDB required file-system persistence and didn't support remote access. Cognee Cloud provides a managed graph-vector store accessible from any environment.", "files": ["cognee_init.py"], "tags": ["infra", "memory"], "supersedes": None, "week": 1},
    {"title": "Build SSE streaming for live graph updates", "rationale": "Dashboard needs real-time updates when new knowledge is added. SSE is simpler than WebSocket for one-directional graph data streaming.", "files": ["api.py"], "tags": ["infra", "realtime"], "supersedes": None, "week": 1},
    {"title": "Ship force-directed graph dashboard", "rationale": "Knowledge graphs need visualization. react-force-graph-2d provides D3 force simulation with minimal configuration overhead.", "files": ["dashboard/src/components/GraphView.tsx"], "tags": ["ui", "visualization"], "supersedes": None, "week": 1},
    {"title": "Design session memory with promote pattern", "rationale": "Users need a scratch space for temporary context before promoting to permanent knowledge. Two-dataset architecture enables this without schema changes.", "files": ["api.py", "server.py"], "tags": ["memory", "ux"], "supersedes": None, "week": 2},
    {"title": "Implement CI/CD reviewer agent", "rationale": "Architectural decisions are useless if nobody enforces them. A GitHub Action that queries the knowledge graph can block PRs reintroducing deprecated patterns.", "files": ["reviewer_agent.py", ".github/workflows/projectbrain-review.yml"], "tags": ["ci", "enforcement"], "supersedes": None, "week": 2},
    {"title": "Switch to priority-ranked ideation for hackathon sprint", "rationale": "One week left. Need to prioritize wins over polish. Ranking by impact-to-effort ratio ensures the best ideas ship first.", "files": ["MASTER.md"], "tags": ["process", "planning"], "supersedes": None, "week": 2},
    {"title": "Deploy to Railway for public demo URL", "rationale": "Localhost demos don't work for judges. Railway provides free tier with Docker support and public HTTPS URLs.", "files": ["Dockerfile", "railway.json"], "tags": ["infra", "deploy"], "supersedes": None, "week": 2},
    {"title": "Knowledge graph now documents its own creation", "rationale": "Meta-narrative — the graph contains the story of how it was built. A user browsing the graph discovers the project's own development history as interconnected decisions.", "files": ["seed.py"], "tags": ["meta", "narrative"], "supersedes": None, "week": 2},

    # Week 1
    {"title": "Use MongoDB for transaction storage", "rationale": "Fast prototyping, flexible schema for early-stage money movement", "files": ["src/db/mongo.ts"], "tags": ["database"], "supersedes": None, "week": 1},
    {"title": "Use JWT for auth", "rationale": "Stateless auth, easy to implement for MVP", "files": ["src/auth/jwt.ts"], "tags": ["auth"], "supersedes": None, "week": 1},
    # Week 2
    {"title": "Adopt Tailwind over CSS modules", "rationale": "Faster development velocity with utility-first CSS", "files": ["src/components/ui"], "tags": ["styling"], "supersedes": None, "week": 2},
    # Week 3
    {"title": "Mongo transactions failing under concurrent writes", "rationale": "Incident #104: double-charge bug caused by MongoDB's eventual consistency model in money movement flow", "files": ["src/db/mongo.ts"], "tags": ["database", "incident"], "supersedes": None, "week": 3},
    {"title": "Migrate to Postgres for transaction storage", "rationale": "Need ACID guarantees for money movement. MongoDB's eventual consistency caused a double-charge bug. This supersedes the MongoDB decision.", "files": ["src/db/postgres.ts"], "tags": ["database", "critical"], "supersedes": "Use MongoDB for transaction storage", "week": 3},
    # Week 4
    {"title": "Build /v1/users endpoint", "rationale": "Initial user management API for the paylink platform", "files": ["src/api/v1/users.ts"], "tags": ["api"], "supersedes": None, "week": 4},
    {"title": "Use Prisma as ORM", "rationale": "Type safety with Postgres, great DX for schema migrations", "files": ["prisma/schema.prisma"], "tags": ["database"], "supersedes": None, "week": 4},
    # Week 5
    {"title": "Switch JWT to session-based auth", "rationale": "JWT revocation was impossible after a leaked token incident. Sessions allow server-side revocation.", "files": ["src/auth/session.ts"], "tags": ["auth", "security"], "supersedes": "Use JWT for auth", "week": 5},
    # Week 6
    {"title": "Deprecate /v1/users, ship /v2/users", "rationale": "v1 leaked PII in error responses. v2 adds proper input sanitization.", "files": ["src/api/v2/users.ts"], "tags": ["api", "security"], "supersedes": "Build /v1/users endpoint", "week": 6},
    {"title": "Add rate limiting via Redis", "rationale": "Prevent brute force attacks on API endpoints after the JWT leak incident", "files": ["src/middleware/rate_limit.ts"], "tags": ["infra"], "supersedes": None, "week": 6},
    # Week 7
    {"title": "Rotate to Groq for LLM calls, ditch OpenAI", "rationale": "Latency improvements and cost savings for AI-powered features", "files": ["src/ai/client.ts"], "tags": ["llm"], "supersedes": None, "week": 7},
    # Week 8
    {"title": "Postgres migration solid, zero double-charge incidents in 30 days", "rationale": "Stability confirmed. Postgres ACID guarantees eliminated the double-charge bug class.", "files": ["src/db/postgres.ts"], "tags": ["database", "metric"], "supersedes": None, "week": 8},
]

async def seed():
    await init_cognee()

    texts = []
    for item in seed_items:
        text = f"Decision: {item['title']}\nRationale: {item['rationale']}\nImpacted Files: {', '.join(item['files'])}\nTags: {', '.join(item['tags'])}\nWeek: {item['week']}"
        if item["supersedes"]:
            text += f"\nSupersedes: {item['supersedes']}"
        texts.append(text)

    print(f"Ingesting {len(texts)} decisions into dataset 'paylink'...")
    await cognee.remember(texts, dataset_name=DATASET)

    print("Seed complete. Run `python projectbrain/api.py` to start the dashboard backend.")

if __name__ == "__main__":
    asyncio.run(seed())
