import asyncio, sys, os
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
os.environ.setdefault("CACHING", "true")
DATASET = os.getenv("COGNEE_DATASET", "paylink")

import cognee
from cognee import SearchType

async def review_pr(code_snippet: str):
    print(f"REVIEWER AGENT: Analyzing PR snippet:\n---\n{code_snippet}\n---\n")

    keyword = None
    for kw in ["mongodb", "mongoclient", "jwt", "jsonwebtoken"]:
        if kw in code_snippet.lower():
            keyword = kw
            break

    if keyword:
        print(f"Detected '{keyword}' usage. Querying organizational memory with GRAPH_COMPLETION_COT...")
        results = await cognee.search(query_text=f"What decisions involved {keyword}? Was it superseded?", query_type=SearchType.GRAPH_COMPLETION_COT, datasets=[DATASET])
        result_text = str(results)

        if "supersede" in result_text.lower() or "postgres" in result_text.lower():
            print(f"\n[REJECTED] Memory indicates {keyword} was superseded. Graph path: {result_text[:500]}")
            sys.exit(1)
        else:
            print(f"\n[APPROVED] No superseding pattern found for {keyword}.")
            sys.exit(0)

    print("[APPROVED] No architectural violations detected.")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith(".diff"):
        with open(sys.argv[1]) as f:
            asyncio.run(review_pr(f.read()))
    else:
        if len(sys.argv) > 1 and sys.argv[1] == "good":
            asyncio.run(review_pr("import { Pool } from 'pg';\nconst pool = new Pool();"))
        else:
            asyncio.run(review_pr("import { MongoClient } from 'mongodb';\nconst client = new MongoClient(uri);"))
