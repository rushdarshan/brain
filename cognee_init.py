"""Cognee initialization — run once before seed.py or api.py."""

import os

os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
os.environ.setdefault("CACHING", "true")

# Embedding provider: FastEmbed (local CPU, no API key needed)
os.environ.setdefault("EMBEDDING_PROVIDER", "fastembed")
os.environ.setdefault("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
os.environ.setdefault("EMBEDDING_DIMENSIONS", "384")

# LLM provider: Groq (via OpenAI-compatible adapter) — set LLM_API_KEY in Railway env
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL", "groq/llama-3.3-70b-versatile")
os.environ.setdefault("LLM_ENDPOINT", "https://api.groq.com/openai/v1")

import cognee

COGNEE_API_KEY = os.environ.get("COGNEE_API_KEY", "")
COGNEE_API_URL = os.environ.get("COGNEE_API_URL", "https://tenant-760a20b9-b8d7-42f0-9007-edf92f8817ff.aws.cognee.ai")


async def init_cognee():
    await cognee.serve(url=COGNEE_API_URL, api_key=COGNEE_API_KEY)
    print(f"Cognee initialized: cloud={COGNEE_API_URL}")
