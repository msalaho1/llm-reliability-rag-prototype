# Submission Notes

## Question 1: Prompt Reliability

I kept the prompt-reliability work intentionally small. The goal here was not to build a full eval framework, just to measure consistency across near-duplicate queries.

The dataset has 10 cases with a 50/50 split between synthetic cases and redacted real-world composites. That gave me a mix of controlled coverage and realistic workflow-style failures. I also made sure to include one explicit invariance case and one explicit perturbation case.

Scoring is intentionally simple: exact for strict answers, regex for rule-like answers, and a token-overlap semantic score when light paraphrasing is acceptable.

The checked-in sample run uses the stub provider. That validates the harness flow end to end without needing model credentials. If I had more time or a live endpoint handy, the next step would be to run the same harness against a real model through the command provider in `eval_harness/src/run_eval.py`.

## What I would ship first

- The hand-rolled dataset and the current CLI harness.
- Exact and regex scoring as the default gates.
- A deterministic output artifact in `eval_harness/outputs/` so regressions can be diffed in GitHub.
- A single real model adapter path using stdin/stdout, because it is the fastest integration point across providers.

## What I would add later

- Dataset growth driven by real failures from support logs, eval reviews, and on-call incidents.
- Pairwise consistency scoring across all variants, not just baseline-to-variant comparisons.
- LLM-as-judge or embedding-based semantic grading once there is evidence that token overlap is too brittle.
- CI thresholds, trend reporting, and flaky-run replay with repeated sampling when the model is non-deterministic.
- Structured metadata for severity, owner, and product area so failures can route to the right team.

## Question 2: Retrieval + Guardrails

For the retrieval task, I built a small FastAPI service around a handwritten 12-snippet corpus so the whole path stays easy to inspect.

I used a bag-of-words retriever instead of vector infrastructure because this prototype is tiny and lexical scoring is easier to reason about in that setting. The `POST /answer` endpoint returns a naive answer, the retrieved snippets, guardrail state, and the active retrieval config.

The guardrail is a denylist for obvious credential or secret-exfiltration requests. I picked that because it is cheap, understandable, and useful enough for a first pass.

I compared dot-product and cosine scoring on the same tokenized corpus and kept cosine as the default. In this small corpus it behaved better because it does less to reward longer snippets just for being longer. I also kept `top_k=3` as the default because it gives enough evidence without cluttering the response.

The service has lightweight tests covering health, normal retrieval behavior, and a guardrail-triggered block.

## What I would ship first for retrieval

- The current FastAPI service, local corpus, and lexical retrieval path.
- Cosine similarity with `top_k=3` as the default retrieval configuration.
- The denylist guardrail for obviously unsafe secret-retrieval requests.
- Request latency and retrieval hit rate as the first monitoring metrics.

## What I would add later for retrieval

- Better ranking with embeddings or hybrid retrieval once corpus size and query variety justify the complexity.
- Snippet chunking and richer metadata once documents are larger than short handcrafted notes.
- More nuanced guardrails for prompt injection, policy-sensitive topics, and abusive query patterns.
- Persistent metrics and dashboards for latency, hit rate, guardrail frequency, and ranking drift.
