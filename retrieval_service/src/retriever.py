from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "but",
    "for",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "when",
    "with",
}

SUPPORTED_METRICS = {"dot", "cosine"}


def tokenize(text: str) -> list[str]:
    normalized = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return [token for token in normalized.split() if token and token not in STOPWORDS]


def vectorize(text: str) -> Counter[str]:
    return Counter(tokenize(text))


def dot_score(query_vector: Counter[str], doc_vector: Counter[str]) -> float:
    return float(sum(query_vector[token] * doc_vector[token] for token in query_vector.keys() & doc_vector.keys()))


def cosine_score(query_vector: Counter[str], doc_vector: Counter[str]) -> float:
    numerator = dot_score(query_vector, doc_vector)
    if numerator == 0.0:
        return 0.0

    query_norm = math.sqrt(sum(value * value for value in query_vector.values()))
    doc_norm = math.sqrt(sum(value * value for value in doc_vector.values()))
    if query_norm == 0.0 or doc_norm == 0.0:
        return 0.0
    return numerator / (query_norm * doc_norm)


def score_document(query: str, document: dict[str, Any], similarity_metric: str) -> float:
    if similarity_metric not in SUPPORTED_METRICS:
        raise ValueError(f"Unsupported similarity metric: {similarity_metric}")

    query_vector = vectorize(query)
    document_vector = vectorize(str(document.get("text", "")))
    if similarity_metric == "dot":
        return dot_score(query_vector, document_vector)
    return cosine_score(query_vector, document_vector)


def retrieve(
    query: str,
    corpus: list[dict[str, Any]],
    top_k: int = 3,
    similarity_metric: str = "cosine",
) -> list[dict[str, Any]]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    ranked_documents = []
    for document in corpus:
        score = score_document(query, document, similarity_metric)
        if score <= 0:
            continue
        ranked_documents.append({**document, "score": round(score, 4)})

    ranked_documents.sort(key=lambda document: document["score"], reverse=True)
    return ranked_documents[:top_k]


def compare_configs(query: str, corpus: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "dot_top_3": [document["id"] for document in retrieve(query, corpus, top_k=3, similarity_metric="dot")],
        "cosine_top_3": [document["id"] for document in retrieve(query, corpus, top_k=3, similarity_metric="cosine")],
    }


def synthesize_answer(query: str, retrieved_documents: list[dict[str, Any]]) -> str:
    if not retrieved_documents:
        return "I could not find a relevant snippet in the local corpus for that question."

    top_document = retrieved_documents[0]
    supporting_titles = ", ".join(document["title"] for document in retrieved_documents[:2])
    return (
        f"Based on {supporting_titles}, the best answer is: {top_document['text']}"
    )
