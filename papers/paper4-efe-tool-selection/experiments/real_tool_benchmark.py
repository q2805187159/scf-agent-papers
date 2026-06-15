"""Paper 4 local executable function-calling benchmark.

This benchmark is intentionally self-contained and safe to publish. It does not
import the closed-source runtime package. The goal is to move Paper 4 beyond
pure synthetic reward arms by evaluating online routing over executable tools
with JSON-style schemas, expected calls, concrete arguments, and exact-result
checking.

It is BFCL/APIBench-style in structure, not an official BFCL/APIBench score.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence, Tuple


ToolHandler = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    schema: Mapping[str, Any]
    handler: ToolHandler


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    family: str
    prompt: str
    expected_tool: str
    arguments: Mapping[str, Any]
    expected_result: Any


class Router:
    name = "router"

    def choose(self, task: TaskSpec, tools: Sequence[ToolSpec], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        raise NotImplementedError

    def update(self, task: TaskSpec, selected_tool: str, reward: float) -> None:
        return None


def _require(arguments: Mapping[str, Any], key: str) -> Any:
    if key not in arguments:
        raise ValueError(f"Missing required argument: {key}")
    return arguments[key]


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def calculator(arguments: Mapping[str, Any]) -> Mapping[str, float]:
    operation = _require(arguments, "operation")
    values = list(_require(arguments, "values"))
    if not values:
        raise ValueError("values must be non-empty")
    if operation == "sum":
        result = sum(values)
    elif operation == "product":
        result = math.prod(values)
    elif operation == "percentage":
        result = values[0] * values[1] / 100.0
    else:
        raise ValueError(f"Unsupported calculator operation: {operation}")
    return {"value": _round(result)}


def unit_convert(arguments: Mapping[str, Any]) -> Mapping[str, float]:
    value = float(_require(arguments, "value"))
    from_unit = _require(arguments, "from_unit")
    to_unit = _require(arguments, "to_unit")
    conversions = {
        ("celsius", "fahrenheit"): value * 9.0 / 5.0 + 32.0,
        ("fahrenheit", "celsius"): (value - 32.0) * 5.0 / 9.0,
        ("kilometer", "mile"): value * 0.621371,
        ("mile", "kilometer"): value / 0.621371,
        ("kilogram", "pound"): value * 2.20462,
        ("pound", "kilogram"): value / 2.20462,
    }
    key = (from_unit, to_unit)
    if key not in conversions:
        raise ValueError(f"Unsupported unit conversion: {from_unit} -> {to_unit}")
    return {"value": _round(conversions[key])}


def date_diff(arguments: Mapping[str, Any]) -> Mapping[str, int]:
    start = date.fromisoformat(str(_require(arguments, "start_date")))
    end = date.fromisoformat(str(_require(arguments, "end_date")))
    return {"days": abs((end - start).days)}


def text_stats(arguments: Mapping[str, Any]) -> Mapping[str, int]:
    text = str(_require(arguments, "text"))
    words = [token.strip(".,;:!?()[]{}\"'").lower() for token in text.split()]
    words = [token for token in words if token]
    return {
        "characters": len(text),
        "words": len(words),
        "unique_words": len(set(words)),
    }


def json_lookup(arguments: Mapping[str, Any]) -> Mapping[str, Any]:
    document = _require(arguments, "document")
    path = str(_require(arguments, "path")).split(".")
    value: Any = document
    for part in path:
        if isinstance(value, Mapping):
            value = value[part]
        elif isinstance(value, list):
            value = value[int(part)]
        else:
            raise ValueError(f"Cannot descend into path component: {part}")
    return {"value": value}


def ticket_ranker(arguments: Mapping[str, Any]) -> Mapping[str, List[str]]:
    tickets = list(_require(arguments, "tickets"))
    priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ranked = sorted(
        tickets,
        key=lambda ticket: (
            priority[str(ticket["priority"]).lower()],
            int(ticket.get("age_hours", 0)) * -1,
            str(ticket["id"]),
        ),
    )
    return {"ordered_ids": [str(ticket["id"]) for ticket in ranked]}


TOOLS: Sequence[ToolSpec] = (
    ToolSpec(
        name="calculator",
        description="Compute sums, products, and percentages.",
        schema={
            "type": "object",
            "properties": {
                "operation": {"enum": ["sum", "product", "percentage"]},
                "values": {"type": "array", "items": {"type": "number"}},
            },
            "required": ["operation", "values"],
        },
        handler=calculator,
    ),
    ToolSpec(
        name="unit_convert",
        description="Convert between temperature, distance, and mass units.",
        schema={
            "type": "object",
            "properties": {
                "value": {"type": "number"},
                "from_unit": {"type": "string"},
                "to_unit": {"type": "string"},
            },
            "required": ["value", "from_unit", "to_unit"],
        },
        handler=unit_convert,
    ),
    ToolSpec(
        name="date_diff",
        description="Compute absolute day distance between ISO dates.",
        schema={
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
            },
            "required": ["start_date", "end_date"],
        },
        handler=date_diff,
    ),
    ToolSpec(
        name="text_stats",
        description="Count characters, words, and unique words in text.",
        schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        handler=text_stats,
    ),
    ToolSpec(
        name="json_lookup",
        description="Read a dot-path value from a JSON-like object.",
        schema={
            "type": "object",
            "properties": {
                "document": {"type": "object"},
                "path": {"type": "string"},
            },
            "required": ["document", "path"],
        },
        handler=json_lookup,
    ),
    ToolSpec(
        name="ticket_ranker",
        description="Rank support tickets by priority and age.",
        schema={
            "type": "object",
            "properties": {
                "tickets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "priority": {"enum": ["critical", "high", "medium", "low"]},
                            "age_hours": {"type": "integer"},
                        },
                    },
                }
            },
            "required": ["tickets"],
        },
        handler=ticket_ranker,
    ),
)


def _expected(tool_name: str, arguments: Mapping[str, Any]) -> Any:
    by_name = {tool.name: tool for tool in TOOLS}
    return by_name[tool_name].handler(arguments)


def make_tasks() -> Sequence[TaskSpec]:
    raw_tasks = [
        (
            "math_sum_invoice",
            "math",
            "Add invoice line items 19.99, 4.50, and 7.25.",
            "calculator",
            {"operation": "sum", "values": [19.99, 4.5, 7.25]},
        ),
        (
            "math_discount",
            "math",
            "Find 15 percent of 240 for a discount calculation.",
            "calculator",
            {"operation": "percentage", "values": [240, 15]},
        ),
        (
            "math_batch_product",
            "math",
            "Multiply batch dimensions 12, 8, and 3.",
            "calculator",
            {"operation": "product", "values": [12, 8, 3]},
        ),
        (
            "unit_temp",
            "unit",
            "Convert 42 degrees Celsius to Fahrenheit.",
            "unit_convert",
            {"value": 42, "from_unit": "celsius", "to_unit": "fahrenheit"},
        ),
        (
            "unit_distance",
            "unit",
            "Convert 12.5 kilometers to miles.",
            "unit_convert",
            {"value": 12.5, "from_unit": "kilometer", "to_unit": "mile"},
        ),
        (
            "unit_weight",
            "unit",
            "Convert 180 pounds to kilograms.",
            "unit_convert",
            {"value": 180, "from_unit": "pound", "to_unit": "kilogram"},
        ),
        (
            "date_workshop_gap",
            "date",
            "How many days are between 2026-06-15 and 2026-08-29?",
            "date_diff",
            {"start_date": "2026-06-15", "end_date": "2026-08-29"},
        ),
        (
            "date_release_gap",
            "date",
            "Compute the day gap from 2026-01-01 to 2026-06-15.",
            "date_diff",
            {"start_date": "2026-01-01", "end_date": "2026-06-15"},
        ),
        (
            "date_review_window",
            "date",
            "Count days between 2026-09-10 and 2026-10-02.",
            "date_diff",
            {"start_date": "2026-09-10", "end_date": "2026-10-02"},
        ),
        (
            "text_brief",
            "text",
            "Count words and unique words in: tool learning needs real calls.",
            "text_stats",
            {"text": "tool learning needs real calls"},
        ),
        (
            "text_repeated",
            "text",
            "Analyze word counts for: route tools, learn tools, verify tools.",
            "text_stats",
            {"text": "route tools, learn tools, verify tools"},
        ),
        (
            "text_trace",
            "text",
            "Count text statistics for: exact traces make routing auditable.",
            "text_stats",
            {"text": "exact traces make routing auditable"},
        ),
        (
            "json_plan",
            "json",
            "Read user.plan.tier from the JSON profile.",
            "json_lookup",
            {"document": {"user": {"plan": {"tier": "pro"}}}, "path": "user.plan.tier"},
        ),
        (
            "json_latency",
            "json",
            "Read metrics.latency.p95 from the service JSON.",
            "json_lookup",
            {"document": {"metrics": {"latency": {"p95": 243}}}, "path": "metrics.latency.p95"},
        ),
        (
            "json_first_tool",
            "json",
            "Read tools.0.name from the tool registry JSON.",
            "json_lookup",
            {"document": {"tools": [{"name": "search"}, {"name": "code"}]}, "path": "tools.0.name"},
        ),
        (
            "ticket_incident",
            "ticket",
            "Rank these support tickets by urgency.",
            "ticket_ranker",
            {
                "tickets": [
                    {"id": "T3", "priority": "medium", "age_hours": 6},
                    {"id": "T1", "priority": "critical", "age_hours": 1},
                    {"id": "T2", "priority": "high", "age_hours": 3},
                ]
            },
        ),
        (
            "ticket_age",
            "ticket",
            "Order tickets, breaking ties by older age first.",
            "ticket_ranker",
            {
                "tickets": [
                    {"id": "A", "priority": "high", "age_hours": 2},
                    {"id": "B", "priority": "high", "age_hours": 9},
                    {"id": "C", "priority": "low", "age_hours": 20},
                ]
            },
        ),
        (
            "ticket_mixed",
            "ticket",
            "Rank a mixed incident queue.",
            "ticket_ranker",
            {
                "tickets": [
                    {"id": "P2", "priority": "low", "age_hours": 30},
                    {"id": "P0", "priority": "critical", "age_hours": 4},
                    {"id": "P1", "priority": "medium", "age_hours": 10},
                ]
            },
        ),
    ]

    return tuple(
        TaskSpec(
            task_id=task_id,
            family=family,
            prompt=prompt,
            expected_tool=tool_name,
            arguments=arguments,
            expected_result=_expected(tool_name, arguments),
        )
        for task_id, family, prompt, tool_name, arguments in raw_tasks
    )


class RandomRouter(Router):
    name = "random"

    def choose(self, task: TaskSpec, tools: Sequence[ToolSpec], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        return rng.choice(list(tools)).name, {}


class SchemaKeywordRouter(Router):
    name = "schema_keyword_router"

    KEYWORDS = {
        "calculator": ("add", "sum", "percent", "multiply", "discount", "dimensions"),
        "unit_convert": ("convert", "celsius", "fahrenheit", "kilometers", "pounds"),
        "date_diff": ("days", "date", "between", "gap"),
        "text_stats": ("words", "word", "text statistics", "count text"),
        "json_lookup": ("json", "read"),
        "ticket_ranker": ("tickets", "ticket", "urgency", "incident", "queue"),
    }

    def choose(self, task: TaskSpec, tools: Sequence[ToolSpec], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        prompt = task.prompt.lower()
        scores = {
            tool.name: float(sum(1 for token in self.KEYWORDS.get(tool.name, ()) if token in prompt))
            for tool in tools
        }
        best_score = max(scores.values())
        candidates = [name for name, score in scores.items() if score == best_score]
        return sorted(candidates)[0], scores


class ContextualEpsilonGreedyRouter(Router):
    def __init__(self, epsilon: float = 0.1):
        self.name = f"contextual_epsilon_{epsilon:.2f}"
        self.epsilon = epsilon
        self.attempts: Dict[Tuple[str, str], float] = {}
        self.rewards: Dict[Tuple[str, str], float] = {}

    def choose(self, task: TaskSpec, tools: Sequence[ToolSpec], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        if rng.random() < self.epsilon:
            return rng.choice(list(tools)).name, {}
        scores = {}
        for tool in tools:
            key = (task.family, tool.name)
            attempts = self.attempts.get(key, 0.0)
            scores[tool.name] = self.rewards.get(key, 0.0) / attempts if attempts else 0.5
        return _stable_argmax(scores), scores

    def update(self, task: TaskSpec, selected_tool: str, reward: float) -> None:
        key = (task.family, selected_tool)
        self.attempts[key] = self.attempts.get(key, 0.0) + 1.0
        self.rewards[key] = self.rewards.get(key, 0.0) + reward


class ContextualUCBRouter(Router):
    def __init__(self, c: float = 2.0):
        self.name = f"contextual_ucb_{c:.1f}"
        self.c = c
        self.attempts: Dict[Tuple[str, str], float] = {}
        self.rewards: Dict[Tuple[str, str], float] = {}

    def choose(self, task: TaskSpec, tools: Sequence[ToolSpec], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        total = sum(self.attempts.get((task.family, tool.name), 0.0) for tool in tools)
        for tool in tools:
            if self.attempts.get((task.family, tool.name), 0.0) == 0.0:
                return tool.name, {}
        scores = {}
        for tool in tools:
            key = (task.family, tool.name)
            attempts = self.attempts[key]
            mean = self.rewards.get(key, 0.0) / attempts
            scores[tool.name] = mean + self.c * math.sqrt(math.log(total + 1.0) / attempts)
        return _stable_argmax(scores), scores

    def update(self, task: TaskSpec, selected_tool: str, reward: float) -> None:
        key = (task.family, selected_tool)
        self.attempts[key] = self.attempts.get(key, 0.0) + 1.0
        self.rewards[key] = self.rewards.get(key, 0.0) + reward


class ContextualEFERouter(Router):
    def __init__(self, w_e: float = 0.45, discount: float | None = None):
        suffix = "discounted" if discount is not None else "static"
        self.name = f"contextual_efe_{suffix}_we_{w_e:.2f}"
        self.w_e = w_e
        self.w_p = 1.0 - w_e
        self.discount = discount
        self.attempts: Dict[Tuple[str, str], float] = {}
        self.rewards: Dict[Tuple[str, str], float] = {}

    def _decay_family(self, family: str) -> None:
        if self.discount is None:
            return
        for key in list(self.attempts):
            if key[0] == family:
                self.attempts[key] *= self.discount
                self.rewards[key] *= self.discount

    def choose(self, task: TaskSpec, tools: Sequence[ToolSpec], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        scores = {}
        for tool in tools:
            key = (task.family, tool.name)
            attempts = self.attempts.get(key, 0.0)
            rewards = self.rewards.get(key, 0.0)
            epistemic = 1.0 / (1.0 + attempts)
            pragmatic = rewards / attempts if attempts else 0.5
            scores[tool.name] = self.w_e * epistemic + self.w_p * pragmatic
        return _stable_argmax(scores), scores

    def update(self, task: TaskSpec, selected_tool: str, reward: float) -> None:
        self._decay_family(task.family)
        key = (task.family, selected_tool)
        self.attempts[key] = self.attempts.get(key, 0.0) + 1.0
        self.rewards[key] = self.rewards.get(key, 0.0) + reward


class GlobalEFERouter(ContextualEFERouter):
    def __init__(self, w_e: float = 0.45):
        super().__init__(w_e=w_e)
        self.name = f"global_efe_we_{w_e:.2f}"

    def choose(self, task: TaskSpec, tools: Sequence[ToolSpec], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        global_task = TaskSpec(
            task.task_id,
            "global",
            task.prompt,
            task.expected_tool,
            task.arguments,
            task.expected_result,
        )
        return super().choose(global_task, tools, rng)

    def update(self, task: TaskSpec, selected_tool: str, reward: float) -> None:
        global_task = TaskSpec(
            task.task_id,
            "global",
            task.prompt,
            task.expected_tool,
            task.arguments,
            task.expected_result,
        )
        super().update(global_task, selected_tool, reward)


def _stable_argmax(scores: Mapping[str, float]) -> str:
    best_score = max(scores.values())
    return sorted(name for name, score in scores.items() if score == best_score)[0]


def _score_margin(scores: Mapping[str, float]) -> float | None:
    if len(scores) < 2:
        return None
    ordered = sorted(scores.values(), reverse=True)
    return ordered[0] - ordered[1]


def make_routers() -> Sequence[Router]:
    return (
        SchemaKeywordRouter(),
        ContextualEFERouter(w_e=0.45),
        ContextualEFERouter(w_e=0.45, discount=0.98),
        ContextualEpsilonGreedyRouter(epsilon=0.10),
        ContextualUCBRouter(c=2.0),
        GlobalEFERouter(w_e=0.45),
        RandomRouter(),
    )


def make_sequence(tasks: Sequence[TaskSpec], trials: int, rng: random.Random) -> List[TaskSpec]:
    sequence: List[TaskSpec] = []
    while len(sequence) < trials:
        block = list(tasks)
        rng.shuffle(block)
        sequence.extend(block)
    return sequence[:trials]


def execute_tool(tool_name: str, arguments: Mapping[str, Any]) -> Tuple[bool, Any, str | None]:
    tool = {spec.name: spec for spec in TOOLS}[tool_name]
    try:
        return True, tool.handler(arguments), None
    except Exception as exc:  # noqa: BLE001 - experiment trace should record tool failure text.
        return False, None, str(exc)


def run_one_router(
    router: Router,
    tasks: Sequence[TaskSpec],
    trials: int,
    seed: int,
    trace_limit: int,
) -> Mapping[str, Any]:
    rng = random.Random(seed)
    sequence = make_sequence(tasks, trials, rng)
    traces = []
    exact_tool_hits = 0
    execution_successes = 0
    exact_result_hits = 0
    margins = []
    selected_tools = set()

    for step, task in enumerate(sequence):
        selected_tool, scores = router.choose(task, TOOLS, rng)
        selected_tools.add(selected_tool)
        executed, output, error = execute_tool(selected_tool, task.arguments)
        exact_tool = selected_tool == task.expected_tool
        exact_result = output == task.expected_result
        reward = 1.0 if exact_tool and exact_result else 0.0
        router.update(task, selected_tool, reward)

        exact_tool_hits += int(exact_tool)
        execution_successes += int(executed)
        exact_result_hits += int(exact_result)
        margin = _score_margin(scores)
        if margin is not None:
            margins.append(margin)

        if len(traces) < trace_limit:
            traces.append(
                {
                    "step": step,
                    "task_id": task.task_id,
                    "family": task.family,
                    "prompt": task.prompt,
                    "expected_call": {
                        "tool": task.expected_tool,
                        "arguments": task.arguments,
                    },
                    "selected_call": {
                        "tool": selected_tool,
                        "arguments": task.arguments,
                    },
                    "selected_correct_tool": exact_tool,
                    "execution_success": executed,
                    "exact_result": exact_result,
                    "reward": reward,
                    "tool_output": output,
                    "error": error,
                    "selector_scores": scores,
                }
            )

    return {
        "router": router.name,
        "exact_tool_rate": exact_tool_hits / trials,
        "execution_success_rate": execution_successes / trials,
        "exact_result_rate": exact_result_hits / trials,
        "reward": exact_result_hits,
        "unique_tools": len(selected_tools),
        "score_margin_mean": statistics.fmean(margins) if margins else None,
        "traces": traces,
    }


def summarize_runs(runs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    by_router: Dict[str, List[Mapping[str, Any]]] = {}
    for run in runs:
        by_router.setdefault(str(run["router"]), []).append(run)

    summary = {}
    for router, entries in by_router.items():
        exact = [float(entry["exact_tool_rate"]) for entry in entries]
        result = [float(entry["exact_result_rate"]) for entry in entries]
        execution = [float(entry["execution_success_rate"]) for entry in entries]
        rewards = [float(entry["reward"]) for entry in entries]
        unique_tools = [float(entry["unique_tools"]) for entry in entries]
        margins = [
            float(entry["score_margin_mean"])
            for entry in entries
            if entry["score_margin_mean"] is not None
        ]
        summary[router] = {
            "exact_tool_rate_mean": statistics.fmean(exact),
            "exact_tool_rate_std": statistics.pstdev(exact),
            "exact_result_rate_mean": statistics.fmean(result),
            "execution_success_rate_mean": statistics.fmean(execution),
            "reward_mean": statistics.fmean(rewards),
            "reward_std": statistics.pstdev(rewards),
            "unique_tools_mean": statistics.fmean(unique_tools),
            "score_margin_mean": statistics.fmean(margins) if margins else None,
        }
    return dict(sorted(summary.items(), key=lambda item: item[1]["exact_result_rate_mean"], reverse=True))


def tool_schema_payload() -> List[Mapping[str, Any]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "schema": tool.schema,
        }
        for tool in TOOLS
    ]


def run_benchmark(runs: int, trials: int, seed: int, trace_limit: int) -> Mapping[str, Any]:
    tasks = make_tasks()
    all_runs = []
    trace_samples = {}

    for run_idx in range(runs):
        for router in make_routers():
            result = run_one_router(
                router=router,
                tasks=tasks,
                trials=trials,
                seed=seed + run_idx,
                trace_limit=trace_limit,
            )
            all_runs.append({key: value for key, value in result.items() if key != "traces"})
            trace_samples.setdefault(str(result["router"]), result["traces"])

    return {
        "metadata": {
            "description": "Paper 4 local executable function-calling benchmark",
            "benchmark_type": "local_executable_function_calling",
            "positioning": (
                "BFCL/APIBench-style local artifact with executable Python tools; "
                "not an official BFCL, ToolBench, APIBench, or AgentBench score."
            ),
            "runs": runs,
            "trials_per_run": trials,
            "seed": seed,
            "num_tools": len(TOOLS),
            "num_task_templates": len(tasks),
        },
        "tools": tool_schema_payload(),
        "summary": summarize_runs(all_runs),
        "runs": all_runs,
        "trace_samples": trace_samples,
    }


def write_results(payload: Mapping[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "paper4_real_tool_benchmark.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def print_summary(payload: Mapping[str, Any], output_path: Path) -> None:
    print("Paper 4 local executable function-calling benchmark")
    print("=" * 72)
    print(f"Results: {output_path}")
    print()
    print(f"{'Router':38s} {'Exact tool':>10s} {'Exact result':>12s} {'Reward':>12s}")
    print("-" * 72)
    trials = int(payload["metadata"]["trials_per_run"])
    for router, row in payload["summary"].items():
        print(
            f"{router:38s} "
            f"{row['exact_tool_rate_mean'] * 100:9.1f}% "
            f"{row['exact_result_rate_mean'] * 100:11.1f}% "
            f"{row['reward_mean']:6.1f}/{trials:<5d}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Paper 4 executable function-calling benchmark.")
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--trials", type=int, default=240)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--trace-limit", type=int, default=12)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_benchmark(
        runs=args.runs,
        trials=args.trials,
        seed=args.seed,
        trace_limit=args.trace_limit,
    )
    output_path = write_results(payload, args.output_dir)
    print_summary(payload, output_path)


if __name__ == "__main__":
    main()
