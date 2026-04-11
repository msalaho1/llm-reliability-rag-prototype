from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "after",
    "before",
    "for",
    "is",
    "of",
    "or",
    "the",
    "to",
    "when",
    "with",
}


def normalize_text(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value.strip().lower())
    return re.sub(r"[^a-z0-9 ]", "", collapsed)


def tokenize(value: str) -> list[str]:
    normalized = normalize_text(value)
    return [token for token in normalized.split() if token and token not in STOPWORDS]


def exact_score(expected: str, actual: str) -> float:
    return 1.0 if normalize_text(expected) == normalize_text(actual) else 0.0


def regex_score(pattern: str, actual: str) -> float:
    return 1.0 if re.search(pattern, actual, flags=re.IGNORECASE) else 0.0


def semantic_score(expected: str, actual: str) -> float:
    expected_tokens = Counter(tokenize(expected))
    actual_tokens = Counter(tokenize(actual))
    if not expected_tokens and not actual_tokens:
        return 1.0
    if not expected_tokens or not actual_tokens:
        return 0.0

    overlap = sum((expected_tokens & actual_tokens).values())
    total = sum(expected_tokens.values()) + sum(actual_tokens.values())
    return (2 * overlap) / total


def similarity_score(left: str, right: str) -> float:
    return semantic_score(left, right)


def average_similarity(baseline: str, variants: Iterable[str]) -> float:
    comparisons = [similarity_score(baseline, value) for value in variants]
    if not comparisons:
        return 1.0
    return sum(comparisons) / len(comparisons)


def score_result(expected: str, actual: str, mode: str, pattern: str | None = None) -> float:
    if not expected:
        return 1.0 if not actual else 0.0

    if mode == "exact":
        return exact_score(expected, actual)
    if mode == "regex":
        if not pattern:
            raise ValueError("Regex scoring requires a pattern.")
        return regex_score(pattern, actual)
    if mode == "semantic":
        return semantic_score(expected, actual)

    raise ValueError(f"Unsupported scoring mode: {mode}")
