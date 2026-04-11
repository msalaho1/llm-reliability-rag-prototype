# Retrieval Service

Minimal retrieval-augmented answering service built with FastAPI. It uses a small handwritten corpus, lexical retrieval, one practical guardrail, and a very simple answer synthesizer that leans on the top-ranked snippet.

This service is intentionally small. The goal was to show a complete retrieval path with one endpoint, one guardrail, one ranking comparison, and enough operational thinking to justify the choices.

## What is here

- A 12-snippet local corpus in `data/corpus.json`
- A `POST /answer` endpoint in `src/app.py`
- Lexical retrieval with two scoring modes in `src/retriever.py`
- A denylist-based guardrail in `src/guardrails.py`
- API tests in `tests/test_api.py`

## Design summary

- Corpus size: 12 handwritten snippets
- Retrieval style: bag-of-words lexical matching
- Compared configs: `dot` versus `cosine`
- Default config: `cosine`, `top_k=3`
- Guardrail: block obvious secret-exfiltration queries
- Output style: answer plus supporting snippets

## API behavior

Request:

```json
{
	"query": "What should the responder do if several tenants are failing but the status page is still green?",
	"top_k": 3,
	"similarity_metric": "cosine"
}
```

Response shape:

- `answer`: naive answer synthesized from the top-ranked snippet
- `retrieved_snippets`: up to top-k ranked corpus matches with scores
- `guardrail`: whether the denylist guardrail triggered
- `retrieval_config`: effective retrieval settings
- `config_comparison`: quick comparison of dot-product versus cosine rankings for the same query

If the guardrail triggers, the service returns a refusal and skips retrieval.

## How to run

Install dependencies from the repository root:

```bash
pip install -r requirements.txt
```

Start the service from the `retrieval_service` directory:

```bash
uvicorn src.app:app --reload
```

Then send a request:

```bash
curl -X POST http://127.0.0.1:8000/answer \
	-H "Content-Type: application/json" \
	-d '{"query":"What should the responder do if several tenants are impacted but the status page is still green?","top_k":3,"similarity_metric":"cosine"}'
```

Run the tests:

```bash
python -m pytest tests/test_api.py
```

## Retrieval design

This service uses a bag-of-words retriever because the task asked for something scrappy but still production-minded. That keeps the stack simple, inspectable, and cheap to run.

Two index configurations were compared:

- `dot`: raw token overlap magnitude
- `cosine`: normalized token overlap

I chose `cosine` as the default because it reduces the tendency for longer snippets to win just because they contain more tokens. In a tiny handwritten corpus with short operational snippets, that normalization gave cleaner rankings for compact user questions.

In practice, the tradeoff is:

- `dot` is simpler and rewards raw overlap
- `cosine` is a better default when snippet length varies, even a little

The default retrieval configuration is:

- similarity metric: `cosine`
- top-k: `3`

`top_k=3` keeps the response small and usually gives enough supporting evidence without flooding the naive answer with loosely related snippets.

## Guardrail

The service includes one denylist-based guardrail that blocks obvious requests to reveal sensitive credentials or secrets. It triggers only when the query contains both:

- a sensitive target such as `password`, `token`, `secret`, or `api key`
- an exfiltration verb such as `show`, `reveal`, `print`, or `export`

Why this is practical:

- it is cheap to implement
- it is easy to explain to reviewers and operators
- it has a relatively high precision for obviously unsafe requests
- it prevents the prototype from becoming a secret-retrieval helper

This is not a complete safety layer, but it is a reasonable first guardrail for a lean service.

It is practical because the failure mode is obvious, the implementation cost is low, and the false-positive surface is smaller than broader keyword-only blocking.

## Monitoring suggestions

Two lightweight monitoring metrics I would ship first:

1. Request latency
Track median and p95 latency for `/answer` responses. This can be logged per request and aggregated in a metrics backend or even a simple structured log pipeline.

2. Retrieval hit rate
Track the percentage of requests where the top document score exceeds a minimum threshold, such as `0.2`. A falling hit rate is a quick signal for topic drift or corpus mismatch.

If I were extending this, I would also watch guardrail trigger frequency by topic and compare top document IDs over time to detect ranking drift.

## Validation status

The service was validated with API tests covering:

- health check response
- successful retrieval on a relevant operational query
- guardrail-triggered blocking on an obvious sensitive request

## Limitations

- The answer synthesis is intentionally naive and simply anchors to the top snippet.
- Lexical retrieval will miss good matches when query wording and snippet wording differ too much.
- The denylist guardrail only handles obvious secret-exfiltration requests.
- The corpus is tiny and handwritten, so it is suitable for a prototype, not a full retrieval benchmark.

## Submission framing

If I were taking this beyond an assessment, I would keep the service shape but replace the handwritten corpus and lexical-only ranking first. The current version is meant to show the retrieval structure, the tradeoffs, and a practical first safety layer without overbuilding the stack.
