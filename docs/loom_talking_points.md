# Loom Talking Points

## video flow

- 30 seconds: introduce the repo and explain that it contains two lean prototypes, one for prompt reliability and one for retrieval plus guardrails.
- 2 to 3 minutes: walk through Question 1.
- 2 to 3 minutes: walk through Question 2.
- 30 seconds: close with what would ship first versus later.

## Opening

- This repo has two small prototypes that came out of the assessment.
- Question 1 focuses on measuring prompt consistency across near-duplicate queries.
- Question 2 focuses on a minimal retrieval-augmented FastAPI service with one practical guardrail.
- I tried to keep both implementations lean and easy to inspect.

## Question 1: Prompt Reliability

### Problem framing

- The reliability problem is not generic model quality. It is answer stability when the same request is phrased slightly differently.
- That is why the harness is built around groups of near-duplicate queries instead of isolated prompts.

### What I built

- A 10-case hand-rolled dataset in `eval_harness/dataset/test_cases.json`.
- The split is 50 percent synthetic and 50 percent redacted real-world cases.
- Synthetic cases give controlled coverage.
- Redacted real-world cases reflect the kind of support, billing, privacy, and incident workflows that actually come up.
- The set includes one explicit invariance test and one explicit perturbation test.

### Architecture overview

- The runner is in `eval_harness/src/run_eval.py`.
- It loads the dataset, formats prompts, runs each query variant, scores the outputs, and writes a result artifact.
- The provider layer supports both a stub provider and a command-based provider for a real model.
- The stub is there to validate the harness flow without needing external model access.

### Evaluation approach

- Scoring lives in `eval_harness/src/scorer.py`.
- I used exact scoring for strict answers, regex for rule-based answers, and lightweight semantic overlap for paraphrase tolerance.
- I also compute a consistency score against the baseline answer for each case.

### Demo notes

- Show `eval_harness/dataset/test_cases.json` briefly.
- Show `eval_harness/src/run_eval.py` and point out the stub provider versus command provider.
- Show `eval_harness/outputs/sample_results.json` and explain that the committed run validates the harness itself.

### Limitations

- The checked-in sample run uses the stub provider, so it validates the harness but does not evaluate a real live model.
- The semantic scoring is intentionally simple and would likely need upgrading for broader production use.

## Question 2: Retrieval + Guardrails

### Problem framing

- The goal here was a minimal retrieval service, not a full RAG stack.
- I wanted something scrappy but still defensible: clear API shape, explicit ranking choice, and one practical safety rule.

### What I built

- A handwritten 12-snippet corpus in `retrieval_service/data/corpus.json`.
- A FastAPI app with `POST /answer` in `retrieval_service/src/app.py`.
- A lexical retriever and naive answer synthesizer in `retrieval_service/src/retriever.py`.
- A denylist-based guardrail in `retrieval_service/src/guardrails.py`.
- Tests in `retrieval_service/tests/test_api.py`.

### Architecture overview

- The request comes into `/answer` with `query`, `top_k`, and `similarity_metric`.
- The service validates the query, checks the guardrail, retrieves the top snippets, and synthesizes a simple answer from the strongest result.
- The response includes the answer, snippets, guardrail state, active config, and a comparison of dot-product versus cosine ranking.

### Design choices

- I used bag-of-words retrieval instead of embeddings because the corpus is tiny and the goal was inspectability.
- I compared dot-product versus cosine and selected cosine because it is less biased toward longer snippets.
- I kept `top_k=3` because it gives enough evidence without flooding the response.
- The guardrail blocks obvious secret-exfiltration requests because that is a cheap and practical first safety layer.

### Monitoring approach

- The first two metrics I would track are request latency and retrieval hit rate.
- Latency tells you if the service stays responsive.
- Hit rate tells you whether queries are still matching the corpus well or whether drift is appearing.

### Demo notes

- Show `retrieval_service/data/corpus.json` briefly.
- Show `retrieval_service/src/app.py` and `retrieval_service/src/retriever.py`.
- Mention that tests in `retrieval_service/tests/test_api.py` are passing.

### Limitations

- The answer synthesizer is intentionally naive.
- Lexical retrieval will miss semantically similar queries with low token overlap.
- The denylist guardrail only catches obvious cases.

## Closing

- For Question 1, I would ship the current harness first and then connect a live model through the command provider.
- For Question 2, I would ship the current service shape first and then upgrade retrieval quality and guardrails once usage patterns justify the extra complexity.
- The common theme across both tasks is starting with something observable, testable, and easy to evolve instead of overbuilding it upfront.