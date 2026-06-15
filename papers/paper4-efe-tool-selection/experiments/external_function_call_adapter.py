"""External function-call dataset adapter for Paper 4.

This script is a public-safe bridge from external tool-learning dataset shapes
to the local executable benchmark used by Paper 4. It accepts normalized
JSONL, BFCL-like JSONL, and API-Bank-like JSONL, then evaluates only examples
whose expected tool is implemented by ``real_tool_benchmark.py``.

It is not an official BFCL, API-Bank, ToolBench, or AgentBench evaluator. The
purpose is to make the artifact structurally compatible with external
function-calling data while preserving an executable, reproducible local smoke
test.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from real_tool_benchmark import (  # noqa: E402
    TOOLS,
    TaskSpec,
    execute_tool,
    make_routers,
    run_one_router,
    summarize_runs,
    tool_schema_payload,
)


KNOWN_TOOL_NAMES = {tool.name for tool in TOOLS}
API_NAME_MAP = {
    "Calculator": "calculator",
    "UnitConvert": "unit_convert",
    "UnitConverter": "unit_convert",
    "DateDiff": "date_diff",
    "DateDifference": "date_diff",
    "TextStats": "text_stats",
    "TextStatistics": "text_stats",
    "JsonLookup": "json_lookup",
    "JSONLookup": "json_lookup",
    "TicketRanker": "ticket_ranker",
    "TicketRanking": "ticket_ranker",
}


@dataclass(frozen=True)
class ExternalExample:
    case_id: str
    source_format: str
    prompt: str
    family: str
    expected_tool: str
    arguments: Mapping[str, Any]
    tools: Sequence[Mapping[str, Any]]


def _as_prompt(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Sequence):
        parts = []
        for item in value:
            if isinstance(item, Mapping):
                content = item.get("content") or item.get("text")
                if content:
                    parts.append(str(content))
            elif item:
                parts.append(str(item))
        return "\n".join(parts)
    if value is None:
        return ""
    return str(value)


def _tool_name(name: Any) -> str:
    text = str(name)
    if text in API_NAME_MAP:
        return API_NAME_MAP[text]
    text = re.sub(r"[^0-9A-Za-z]+", "_", text).strip("_").lower()
    return API_NAME_MAP.get(text, text)


def _extract_tools(record: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    raw_tools = (
        record.get("tools")
        or record.get("function")
        or record.get("functions")
        or record.get("api_list")
        or []
    )
    normalized = []
    for raw_tool in raw_tools:
        if not isinstance(raw_tool, Mapping):
            continue
        name = _tool_name(raw_tool.get("name") or raw_tool.get("api_name"))
        schema = (
            raw_tool.get("schema")
            or raw_tool.get("parameters")
            or raw_tool.get("input_parameters")
            or {}
        )
        normalized.append(
            {
                "name": name,
                "description": str(raw_tool.get("description", "")),
                "schema": schema,
            }
        )
    return normalized or tool_schema_payload()


def _literal_from_ast(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_literal_from_ast(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_literal_from_ast(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _literal_from_ast(key): _literal_from_ast(value)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _literal_from_ast(node.operand)
        if isinstance(value, (int, float)):
            return -value
    raise ValueError(f"Unsupported API call literal: {ast.dump(node)}")


def parse_api_bank_call(call_text: str) -> Tuple[str, Mapping[str, Any]]:
    expression = ast.parse(call_text.strip(), mode="eval").body
    if not isinstance(expression, ast.Call):
        raise ValueError(f"Expected function call expression, got: {call_text}")
    if not isinstance(expression.func, ast.Name):
        raise ValueError(f"Expected simple API name, got: {call_text}")
    arguments = {
        keyword.arg: _literal_from_ast(keyword.value)
        for keyword in expression.keywords
        if keyword.arg is not None
    }
    return _tool_name(expression.func.id), arguments


def _extract_expected_call(record: Mapping[str, Any]) -> Tuple[str, Mapping[str, Any]]:
    expected_call = record.get("expected_call")
    if isinstance(expected_call, Mapping):
        return _tool_name(expected_call.get("tool") or expected_call.get("name")), dict(
            expected_call.get("arguments") or expected_call.get("parameters") or {}
        )

    ground_truth = record.get("ground_truth")
    if isinstance(ground_truth, Sequence) and not isinstance(ground_truth, str):
        ground_truth = ground_truth[0] if ground_truth else None
    if isinstance(ground_truth, Mapping):
        return _tool_name(ground_truth.get("tool") or ground_truth.get("name")), dict(
            ground_truth.get("arguments") or ground_truth.get("parameters") or {}
        )

    api_call = record.get("api_call") or record.get("request") or record.get("target")
    if isinstance(api_call, str):
        return parse_api_bank_call(api_call)

    raise ValueError("No expected_call, ground_truth, or API-Bank-style api_call found")


def normalize_record(record: Mapping[str, Any], row_number: int) -> ExternalExample:
    prompt = _as_prompt(
        record.get("prompt")
        or record.get("question")
        or record.get("context")
        or record.get("conversation")
        or record.get("messages")
    )
    expected_tool, arguments = _extract_expected_call(record)
    return ExternalExample(
        case_id=str(record.get("id") or record.get("case_id") or f"row_{row_number}"),
        source_format=str(record.get("source_format") or record.get("format") or "unknown_jsonl"),
        prompt=prompt,
        family=str(record.get("family") or record.get("category") or expected_tool),
        expected_tool=expected_tool,
        arguments=arguments,
        tools=_extract_tools(record),
    )


def iter_jsonl(path: Path) -> Iterable[Tuple[int, Mapping[str, Any]]]:
    for row_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError(f"JSONL row {row_number} is not an object")
        yield row_number, payload


def make_tasks_from_examples(
    examples: Sequence[ExternalExample],
) -> Tuple[List[TaskSpec], List[Mapping[str, Any]]]:
    tasks: List[TaskSpec] = []
    skipped = []
    for example in examples:
        if example.expected_tool not in KNOWN_TOOL_NAMES:
            skipped.append(
                {
                    "case_id": example.case_id,
                    "reason": f"unsupported expected tool: {example.expected_tool}",
                    "source_format": example.source_format,
                }
            )
            continue
        executed, expected_result, error = execute_tool(example.expected_tool, example.arguments)
        if not executed:
            skipped.append(
                {
                    "case_id": example.case_id,
                    "reason": f"expected tool failed during fixture execution: {error}",
                    "source_format": example.source_format,
                }
            )
            continue
        tasks.append(
            TaskSpec(
                task_id=example.case_id,
                family=example.family,
                prompt=example.prompt,
                expected_tool=example.expected_tool,
                arguments=example.arguments,
                expected_result=expected_result,
            )
        )
    return tasks, skipped


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def run_adapter(input_path: Path, rounds: int, seed: int, trace_limit: int) -> Mapping[str, Any]:
    examples = [normalize_record(record, row_number) for row_number, record in iter_jsonl(input_path)]
    tasks, skipped = make_tasks_from_examples(examples)
    if not tasks:
        raise ValueError("No executable examples remained after adapter normalization")

    trials = len(tasks) * rounds
    all_runs = []
    trace_samples: Dict[str, Any] = {}
    for router in make_routers():
        result = run_one_router(
            router=router,
            tasks=tasks,
            trials=trials,
            seed=seed,
            trace_limit=trace_limit,
        )
        all_runs.append({key: value for key, value in result.items() if key != "traces"})
        trace_samples[str(result["router"])] = result["traces"]

    return {
        "metadata": {
            "description": "Paper 4 external function-call adapter smoke test",
            "benchmark_type": "external_function_call_adapter",
            "positioning": (
                "Adapter for normalized, BFCL-like, and API-Bank-like JSONL. "
                "This is a compatibility smoke test, not an official benchmark score."
            ),
            "input_path": _display_path(input_path),
            "rounds": rounds,
            "trials": trials,
            "seed": seed,
            "records": len(examples),
            "executable_records": len(tasks),
            "skipped_records": len(skipped),
            "supported_formats": [
                "normalized prompt/tools/expected_call JSONL",
                "BFCL-like question/function/ground_truth JSONL",
                "API-Bank-like context/api_list/api_call JSONL",
            ],
        },
        "summary": summarize_runs(all_runs),
        "runs": all_runs,
        "trace_samples": trace_samples,
        "skipped": skipped,
        "normalized_samples": [
            {
                "case_id": task.task_id,
                "family": task.family,
                "prompt": task.prompt,
                "expected_call": {
                    "tool": task.expected_tool,
                    "arguments": task.arguments,
                },
                "expected_result": task.expected_result,
            }
            for task in tasks[: min(12, len(tasks))]
        ],
    }


def write_results(payload: Mapping[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "paper4_external_adapter_smoke.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def print_summary(payload: Mapping[str, Any], output_path: Path) -> None:
    print("Paper 4 external function-call adapter smoke test")
    print("=" * 78)
    print(f"Results: {output_path}")
    print(
        "Records: "
        f"{payload['metadata']['executable_records']} executable, "
        f"{payload['metadata']['skipped_records']} skipped"
    )
    print()
    print(f"{'Router':38s} {'Exact tool':>10s} {'Exact result':>12s} {'Reward':>12s}")
    print("-" * 78)
    trials = int(payload["metadata"]["trials"])
    for router, row in payload["summary"].items():
        print(
            f"{router:38s} "
            f"{row['exact_tool_rate_mean'] * 100:9.1f}% "
            f"{row['exact_result_rate_mean'] * 100:11.1f}% "
            f"{row['reward_mean']:6.1f}/{trials:<5d}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Paper 4 external function-call adapter.")
    parser.add_argument(
        "--input",
        type=Path,
        default=EXPERIMENT_DIR / "fixtures" / "bfcl_api_bank_style_sample.jsonl",
        help="JSONL file in normalized, BFCL-like, or API-Bank-like format.",
    )
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--trace-limit", type=int, default=12)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=EXPERIMENT_DIR / "results",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_adapter(
        input_path=args.input,
        rounds=args.rounds,
        seed=args.seed,
        trace_limit=args.trace_limit,
    )
    output_path = write_results(payload, args.output_dir)
    print_summary(payload, output_path)


if __name__ == "__main__":
    main()
