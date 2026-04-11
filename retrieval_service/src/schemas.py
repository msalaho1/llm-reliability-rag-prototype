from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class AnswerRequest(BaseModel):
    query: str = Field(min_length=1, description="User query to answer against the local corpus.")
    top_k: int = Field(default=3, ge=1, le=5)
    similarity_metric: Literal["cosine", "dot"] = "cosine"


class RetrievedSnippet(BaseModel):
    id: str
    title: str
    topic: str
    text: str
    score: float


class GuardrailResult(BaseModel):
    triggered: bool
    reason: str | None = None
    matched_term: str | None = None


class ConfigComparison(BaseModel):
    dot_top_3: list[str]
    cosine_top_3: list[str]
    recommended_metric: str
    rationale: str


class AnswerResponse(BaseModel):
    query: str
    answer: str
    retrieved_snippets: list[RetrievedSnippet]
    guardrail: GuardrailResult
    retrieval_config: dict[str, str | int]
    config_comparison: ConfigComparison
