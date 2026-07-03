"""Cognee initialization — run once before seed.py or api.py."""

import os

os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
os.environ.setdefault("CACHING", "true")

import cognee

COGNEE_API_KEY = os.environ["COGNEE_API_KEY"]
COGNEE_API_URL = os.environ.get("COGNEE_API_URL", "https://tenant-760a20b9-b8d7-42f0-9007-edf92f8817ff.aws.cognee.ai")


async def init_cognee():
    await cognee.serve(url=COGNEE_API_URL, api_key=COGNEE_API_KEY)
    print(f"Cognee initialized: cloud={COGNEE_API_URL}")
