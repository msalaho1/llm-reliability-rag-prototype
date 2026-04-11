from __future__ import annotations

import argparse
import shlex
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scorer import average_similarity, score_result
from utils import load_json_file, save_json_file


DEFAULT_PROMPT_TEMPLATE = (
    "You are evaluating prompt reliability. Answer with exactly one short sentence.\n"
    "Question: {query}"
)


@dataclass
class ProviderResult:
    output: str
    latency_ms: float


class StubPromptProvider:
    def run(self, prompt: str, case: dict[str, Any], variant: dict[str, Any]) -> ProviderResult:
        start = time.perf_counter()
        output = self._answer(case["case_id"], variant["variant_id"])
        latency_ms = (time.perf_counter() - start) * 1000
        return ProviderResult(output=output, latency_ms=latency_ms)

    def _answer(self, case_id: str, variant_id: str) -> str:
        responses = {
            "syn-01": {
                "baseline": "Contractor password resets are completed within 4 business hours.",
                "paraphrase": "Contractor password resets are completed within 4 business hours.",
                "typo": "Contractor password resets are completed within 4 business hours.",
                "noise": "Contractor password resets are completed within 4 business hours.",
            },
            "syn-02": {
                "baseline": "A batch job is marked failed after 3 retries.",
                "compact": "A batch job is marked failed after 3 retries.",
            },
            "syn-03": {
                "baseline": "Vendor onboarding tickets go to the access operations queue.",
                "paraphrase": "Vendor onboarding requests should go to the access operations queue.",
            },
            "syn-04": {
                "baseline": "Sandbox logs are retained for 7 days.",
                "short": "Sandbox logs are retained for 7 days.",
            },
            "syn-05": {
                "baseline": "Escalate a blocked refund request after 2 unsuccessful processor attempts.",
                "reordered": "Escalate the blocked refund after 2 unsuccessful processor attempts.",
                "distractor": "Escalate the blocked refund request after the second failed processor attempt, ignoring unrelated billing-country changes.",
            },
            "real-01": {
                "baseline": "Billing operations owns duplicate invoice issues after plan downgrades.",
                "paraphrase": "Billing operations owns duplicate invoice issues after downgrades.",
            },
            "real-02": {
                "baseline": "Tickets merged more than 30 days ago should be recreated, not reopened.",
                "compact": "Tickets older than 30 days should be recreated, not reopened.",
            },
            "real-03": {
                "baseline": "Request account verification before processing a PII deletion request.",
                "paraphrase": "Request account verification before processing a PII deletion request.",
            },
            "real-04": {
                "baseline": "Open a severity 2 incident when multiple tenants are impacted despite a green status page.",
                "paraphrase": "Open a severity 2 incident if multiple tenants are impacted even when the status page remains green.",
            },
            "real-05": {
                "baseline": "Reject the security exception request until an expiration date is provided.",
                "paraphrase": "Reject the security exception request until an expiration date is provided.",
            },
        }
        return responses[case_id][variant_id]


class CommandPromptProvider:
    def __init__(self, command: str) -> None:
        self.command = shlex.split(command)

    def run(self, prompt: str, case: dict[str, Any], variant: dict[str, Any]) -> ProviderResult:
        start = time.perf_counter()
        completed = subprocess.run(
            self.command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        output = completed.stdout.strip()
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "No stderr returned."
            raise RuntimeError(
                f"Command provider failed for {case['case_id']}:{variant['variant_id']}: {stderr}"
            )
        return ProviderResult(output=output, latency_ms=latency_ms)


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[1]
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    default_output = project_root / "outputs" / f"results_{timestamp}.json"
    parser = argparse.ArgumentParser(description="Run the prompt reliability mini-harness.")
    parser.add_argument(
        "--dataset",
        default=str(project_root / "dataset" / "test_cases.json"),
        help="Path to the dataset JSON file.",
    )
    parser.add_argument(
        "--output",
        default=str(default_output),
        help="Path to write the results JSON.",
    )
    parser.add_argument(
        "--provider",
        choices=["stub", "command"],
        default="stub",
        help="How prompts should be executed.",
    )
    parser.add_argument(
        "--command",
        help="Command to execute when provider=command. The prompt is sent over stdin.",
    )
    parser.add_argument(
        "--prompt-template",
        default=DEFAULT_PROMPT_TEMPLATE,
        help="Prompt template with a {query} placeholder.",
    )
    return parser.parse_args()


def get_provider(args: argparse.Namespace) -> StubPromptProvider | CommandPromptProvider:
    if args.provider == "stub":
        return StubPromptProvider()
    if not args.command:
        raise ValueError("--command is required when --provider=command")
    return CommandPromptProvider(args.command)


def run_case(
    case: dict[str, Any],
    prompt_template: str,
    provider: StubPromptProvider | CommandPromptProvider,
) -> dict[str, Any]:
    scoring = case["scoring"]
    variant_results: list[dict[str, Any]] = []
    for variant in case["query_variants"]:
        prompt = prompt_template.format(query=variant["query"])
        provider_result = provider.run(prompt, case, variant)
        score = score_result(
            expected=case["expected_answer"],
            actual=provider_result.output,
            mode=scoring["mode"],
            pattern=scoring.get("pattern"),
        )
        variant_results.append(
            {
                "variant_id": variant["variant_id"],
                "label": variant["label"],
                "query": variant["query"],
                "prompt": prompt,
                "output": provider_result.output,
                "latency_ms": round(provider_result.latency_ms, 3),
                "score": round(score, 4),
                "passed": score >= scoring["threshold"],
            }
        )

    baseline_output = variant_results[0]["output"]
    consistency = average_similarity(
        baseline_output,
        [result["output"] for result in variant_results[1:]],
    )
    return {
        "case_id": case["case_id"],
        "source_type": case["source_type"],
        "test_type": case["test_type"],
        "description": case["description"],
        "expected_answer": case["expected_answer"],
        "scoring": scoring,
        "variant_results": variant_results,
        "consistency_score": round(consistency, 4),
        "all_variants_passed": all(result["passed"] for result in variant_results),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result["all_variants_passed"])
    all_variants = [
        variant
        for result in results
        for variant in result["variant_results"]
    ]
    passed_variants = sum(1 for variant in all_variants if variant["passed"])
    mean_consistency = (
        sum(result["consistency_score"] for result in results) / total_cases
        if total_cases
        else 0.0
    )
    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "case_pass_rate": round(passed_cases / total_cases, 4) if total_cases else 0.0,
        "total_variants": len(all_variants),
        "passed_variants": passed_variants,
        "variant_pass_rate": round(passed_variants / len(all_variants), 4) if all_variants else 0.0,
        "mean_consistency": round(mean_consistency, 4),
    }


def main() -> None:
    args = parse_args()
    dataset = load_json_file(args.dataset)
    provider = get_provider(args)
    results = [run_case(case, args.prompt_template, provider) for case in dataset["cases"]]
    payload = {
        "dataset_name": dataset["dataset_name"],
        "dataset_version": dataset["version"],
        "run_metadata": {
            "provider": args.provider,
            "command": args.command,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "prompt_template": args.prompt_template,
        },
        "summary": summarize(results),
        "results": results,
    }
    save_json_file(args.output, payload)
    print(f"Wrote evaluation results to {args.output}")
    print(payload["summary"])


if __name__ == "__main__":
    main()
