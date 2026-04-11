from __future__ import annotations

import re

DENYLIST_TERMS = {
    "api key",
    "apikey",
    "password",
    "private key",
    "secret",
    "token",
}

EXFILTRATION_VERBS = {
    "dump",
    "export",
    "leak",
    "print",
    "reveal",
    "share",
    "show",
}


def validate_query(query: str) -> str:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Query must not be empty.")

    return cleaned_query


def evaluate_guardrail(query: str) -> dict[str, str | bool | None]:
    normalized = re.sub(r"\s+", " ", query.strip().lower())
    matched_term = next((term for term in DENYLIST_TERMS if term in normalized), None)
    matched_verb = next((verb for verb in EXFILTRATION_VERBS if verb in normalized), None)

    if matched_term and matched_verb:
        return {
            "triggered": True,
            "reason": "blocked_sensitive_request",
            "matched_term": matched_term,
        }

    return {
        "triggered": False,
        "reason": None,
        "matched_term": None,
    }
