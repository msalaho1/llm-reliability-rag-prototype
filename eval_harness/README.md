# Eval Harness

This folder contains a small evaluation harness for prompt reliability on near-duplicate queries. The point is not broad model benchmarking. The narrower question is: if the same request is phrased a little differently, does the answer stay the same?

## What is here

- A hand-rolled 10-case dataset in `dataset/test_cases.json`
- A 50/50 split between synthetic cases and redacted real-world cases
- One explicit invariance test where answer-preserving noise should not matter
- One explicit perturbation test where distractors or instruction order may cause drift
- A CLI runner in `src/run_eval.py`
- Scoring utilities in `src/scorer.py`
- A sample run artifact in `outputs/sample_results.json`

## Folder structure

```text
eval_harness/
├── README.md
├── dataset/
│   └── test_cases.json
├── examples/
│   └── sample_results.json
├── outputs/
│   ├── .gitkeep
│   └── sample_results.json
└── src/
	├── run_eval.py
	├── scorer.py
	└── utils.py
```

## Dataset design

The dataset is organized around cases rather than individual prompts. Each case has one underlying decision boundary and a few nearby query variants.

Each case contains:

- `case_id`: stable identifier for reporting
- `source_type`: either `synthetic` or `redacted_real_world`
- `test_type`: whether the case is a baseline, invariance, or perturbation check
- `description`: plain-English explanation of what the case is probing
- `expected_answer`: the canonical target answer
- `scoring`: the rule used to judge outputs
- `query_variants`: multiple prompt variants that should map to the same answer

### Synthetic cases

The synthetic half of the dataset was generated with three rules:

1. Start from one atomic policy fact with a single owner, threshold, or action.
2. Create near-duplicate variants using paraphrase, typo, punctuation noise, or formatting noise.
3. Keep the expected answer short and stable so simple scoring remains useful.

These are useful because they are controlled. If one fails, it is usually easier to see what changed.

### Redacted real-world cases

The real-world half is still written as prompts in the file, but those prompts come from realistic issue patterns rather than being invented from scratch. They are redacted composites of common support, billing, privacy, and incident-management workflows.

That means:

- the failure mode is realistic
- the prompt text is rewritten and generalized
- sensitive names, identifiers, and internal labels are removed
- the decision boundary is preserved

Example: a case about identity verification for a deletion request is meant to reflect a common operational workflow, not a made-up toy prompt.

## Test types

The `test_type` field is just metadata that explains what kind of reliability behavior a case is meant to probe.

- `baseline`: ordinary near-duplicate rewording should keep the same answer
- `invariance`: superficial noise such as typos, punctuation, or casing must not change the answer
- `perturbation`: extra distractors or reordered instructions may cause drift, so this tests robustness under pressure

## How execution works

The runner in `src/run_eval.py` does the following:

1. Load the dataset JSON.
2. Pick a provider.
3. Format each query into a prompt template.
4. Run all variants for each case.
5. Score each output.
6. Compute a per-case consistency score.
7. Write the full result payload to JSON.

The default prompt template is intentionally simple:

```text
You are evaluating prompt reliability. Answer with exactly one short sentence.
Question: {query}
```

That keeps answer style fairly constrained so scoring is less noisy.

## Providers

The harness supports two execution modes.

### 1. Stub provider

The default `stub` provider returns deterministic hardcoded answers.

Use this when you want to validate the harness itself:

- dataset loading
- prompt formatting
- result writing
- scoring
- summary generation

It is useful for development, but it is not a real prompt-reliability run against a live model.

### 2. Command provider

The `command` provider lets the harness call an external script or wrapper over stdin/stdout.

Use this when you want to evaluate a real model or internal endpoint.

The external command must:

- read the full prompt from stdin
- call the model or service
- print only the final answer to stdout

This keeps the harness provider-agnostic and avoids hardwiring one SDK into the runner.

## Scoring

The scoring logic lives in `src/scorer.py`.

There are three scoring modes:

- `exact`: best for short policy answers where wording should remain highly stable
- `regex`: best when one key phrase or threshold matters more than full sentence shape
- `semantic`: lightweight token-overlap scoring for mild paraphrase tolerance

The harness also computes a `consistency_score`, which compares the baseline output against the non-baseline outputs for the same case.

That distinction matters:

- correctness asks whether the output matches the expected answer
- consistency asks whether outputs stay aligned across near-duplicate prompts

For this task, consistency is the main signal.

## How to run

From the repository root, run:

```bash
python eval_harness/src/run_eval.py
```

That writes a timestamped output file under `eval_harness/outputs/`.

To write to a fixed file instead:

```bash
python eval_harness/src/run_eval.py --output eval_harness/outputs/sample_results.json
```

To run against a real model wrapper:

```bash
python eval_harness/src/run_eval.py --provider command --command "python path/to/model_client.py"
```

You can also override the prompt template:

```bash
python eval_harness/src/run_eval.py --prompt-template "Answer in one sentence. Query: {query}"
```

## What the output means

The run output JSON contains three top-level sections:

- `run_metadata`: how the harness was run
- `summary`: aggregate pass rates and consistency
- `results`: per-case details

Inside each case result:

- `variant_results` stores the prompt, output, latency, score, and pass/fail for each variant
- `all_variants_passed` tells you whether the case stayed correct across every variant
- `consistency_score` summarizes how close non-baseline outputs were to the baseline answer

Example summary fields:

- `total_cases`: number of cases in the dataset
- `passed_cases`: number of cases where all variants passed
- `case_pass_rate`: share of fully passing cases
- `total_variants`: number of prompt variants run
- `passed_variants`: number of variants that passed scoring
- `variant_pass_rate`: share of passing variants
- `mean_consistency`: average consistency across all cases

## Current limitations

- The semantic scoring is intentionally lightweight and will miss some valid paraphrases.
- The stub provider is only for harness validation, not real model evaluation.
- The current consistency metric compares each variant to the baseline output, not all pairs.
- The dataset is intentionally small because this task asks for a mini-harness.

## What I would ship first and what I would add later

Ship first:

- the current dataset structure
- the CLI runner
- exact and regex scoring as default gates
- the command-based integration path for a real model

Ship later:

- more real failure-driven cases
- better semantic grading with embeddings or judge models
- repeated-run analysis for non-deterministic models
- CI thresholds and trend tracking

## Recommended next step

Use the stub provider first to validate the flow. After that, plug in a real model wrapper through `--provider command` and compare the real outputs against the sample artifact.
