from datetime import datetime
from pydantic import BaseModel


class DecisionModel(BaseModel):
    title: str
    rationale: str
    files: list[str]
    tags: list[str]
    supersedes: str | None = None
    week: int


class ReviewResult(BaseModel):
    score: float
    timestamp: float
    patterns_checked: list[str]
    patterns_found: list[str]
    passed: bool
