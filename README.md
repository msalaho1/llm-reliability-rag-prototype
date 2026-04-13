# llm-reliability-rag-prototype

A repo for two assessment tasks:

1. prompt reliability evaluation for duplicate queries
2. a minimal retrieval-augmented FastAPI service with one practical guardrail

The repo is intentionally narrow in scope. Each task has its own README so it can be reviewed on its own.

## Repository overview

### Question 1: Prompt Reliability Mini-Harness

This part is about answer consistency. The idea is to check whether the same request still gets the same decision when the wording changes a bit.

Included here:

- a 10 case hand rolled dataset
- a 50/50 split between synthetic and redacted real world cases
- exact, regex, and lightweight semantic scoring
- a stub backed runner plus a command based hook for a real LLM

Detailed documentation:

- [eval_harness/README.md]

Main files:

- [eval_harness/dataset/test_cases.json]
- [eval_harness/src/run_eval.py]
- [eval_harness/src/scorer.py]

Quick run:

```bash
python eval_harness/src/run_eval.py --output eval_harness/outputs/sample_results.json
```

### Question 2: Retrieval + Guardrails Lean FastAPI

This part is a minimal retrieval service over a handwritten corpus, plus one simple guardrail.

Included here:

- a 12 snippet local text corpus
- a FastAPI `POST /answer` endpoint
- lexical retrieval with dot-product and cosine comparison
- a denylist-based guardrail for obvious secret-exfiltration requests
- lightweight API tests

Detailed documentation:

- [retrieval_service/README.md]

Main files:

- [retrieval_service/data/corpus.json]
- [retrieval_service/src/app.py]
- [retrieval_service/src/retriever.py]
- [retrieval_service/src/guardrails.py]

Quick run:

```bash
cd retrieval_service
uvicorn src.app:app --reload
```

## Environment setup

Install dependencies from the repo root:

```bash
pip install -r requirements.txt
```

## Submission-oriented docs

There are also a couple of supporting docs for submission and the Loom walkthrough:

- [docs/submission_notes.md]
- [docs/loom_talking_points.md]

## Scope and tradeoffs

The general approach in both tasks was to keep things simple and easy to inspect:

- start with a small hand-rolled dataset instead of a bigger eval system
- use lexical retrieval before adding vector infrastructure
- add one practical guardrail before trying to cover every policy edge case
