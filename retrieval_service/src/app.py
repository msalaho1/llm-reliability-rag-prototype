from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI

try:
    from .guardrails import evaluate_guardrail, validate_query
    from .retriever import compare_configs, retrieve, synthesize_answer
    from .schemas import AnswerRequest, AnswerResponse, ConfigComparison, GuardrailResult, HealthResponse, RetrievedSnippet
except ImportError:
    from guardrails import evaluate_guardrail, validate_query
    from retriever import compare_configs, retrieve, synthesize_answer
    from schemas import AnswerRequest, AnswerResponse, ConfigComparison, GuardrailResult, HealthResponse, RetrievedSnippet

try:
    from ...eval_harness.src.utils import load_json_file
except ImportError:
    import json

    def load_json_file(path: str | Path) -> Any:
        with Path(path).open("r", encoding="utf-8") as file:
            return json.load(file)


CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "corpus.json"
CORPUS = load_json_file(CORPUS_PATH)
COMPARISON_RATIONALE = (
    "Cosine was selected over dot product because it normalizes for snippet length and produced "
    "more stable rankings for short operational queries in this handwritten corpus."
)

app = FastAPI(title="Lean Retrieval Service", version="0.1.0")


def get_health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return get_health()


@app.post("/answer", response_model=AnswerResponse)
def answer(request: AnswerRequest) -> AnswerResponse:
    query = validate_query(request.query)
    guardrail_state = evaluate_guardrail(query)
    if guardrail_state["triggered"]:
        return AnswerResponse(
            query=query,
            answer="I cannot help retrieve or summarize sensitive credentials or secrets.",
            retrieved_snippets=[],
            guardrail=GuardrailResult(**guardrail_state),
            retrieval_config={
                "similarity_metric": request.similarity_metric,
                "top_k": request.top_k,
            },
            config_comparison=ConfigComparison(
                **compare_configs(query, CORPUS),
                recommended_metric="cosine",
                rationale=COMPARISON_RATIONALE,
            ),
        )

    retrieved_documents = retrieve(
        query=query,
        corpus=CORPUS,
        top_k=request.top_k,
        similarity_metric=request.similarity_metric,
    )
    snippets = [RetrievedSnippet(**document) for document in retrieved_documents]
    return AnswerResponse(
        query=query,
        answer=synthesize_answer(query, retrieved_documents),
        retrieved_snippets=snippets,
        guardrail=GuardrailResult(**guardrail_state),
        retrieval_config={
            "similarity_metric": request.similarity_metric,
            "top_k": request.top_k,
        },
        config_comparison=ConfigComparison(
            **compare_configs(query, CORPUS),
            recommended_metric="cosine",
            rationale=COMPARISON_RATIONALE,
        ),
    )


if __name__ == "__main__":
    print(get_health().model_dump_json(indent=2))
