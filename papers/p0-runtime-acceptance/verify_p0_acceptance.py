"""Verify the public P0 runtime acceptance result artifact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


RESULT_PATH = Path(__file__).resolve().parent / "results" / "p0_acceptance_results.json"

REQUIRED_METRICS = {
    "cls_long_session_retention",
    "preparedness_success_pearson",
    "causal_utility_key_block_detection",
    "physical_ablation_summary",
    "end_to_end_latency_p95_ms",
    "real_tool_task_suite",
    "stability_success_rate",
}


def load_payload(path: Path = RESULT_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(payload: Dict[str, Any]) -> Dict[str, Any]:
    tests = payload.get("tests", [])
    metrics = {test.get("metric") for test in tests}
    missing = sorted(REQUIRED_METRICS - metrics)
    failed = sorted(test.get("metric") for test in tests if not test.get("passed"))
    summary = payload.get("summary", {})
    ok = not missing and not failed and summary.get("all_passed") is True
    return {
        "ok": ok,
        "missing": missing,
        "failed": failed,
        "passed": summary.get("passed"),
        "total": summary.get("total"),
    }


def main() -> int:
    result = verify(load_payload())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
