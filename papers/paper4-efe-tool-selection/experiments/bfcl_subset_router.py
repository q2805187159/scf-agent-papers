"""BFCL subset schema-routing diagnostic for Paper 4.

This runner downloads or reads a small subset of the official Berkeley Function
Calling Leaderboard dataset, then turns it into a schema-routing problem:
given a user prompt and a global pool of BFCL function schemas, select the
expected function name.

The official dataset source is:
``gorilla-llm/Berkeley-Function-Calling-Leaderboard``

This is not an official BFCL score. BFCL evaluates generated function calls
with benchmark-specific AST/execution rules. This script only asks whether a
tool router can select the expected function schema from an externally sourced
BFCL subset.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


HF_BASE_URL = (
    "https://huggingface.co/datasets/"
    "gorilla-llm/Berkeley-Function-Calling-Leaderboard/resolve/main"
)
DEFAULT_INPUT_PATH = "BFCL_v3_simple.json"
DEFAULT_ANSWER_PATH = "possible_answer/BFCL_v3_simple.json"


@dataclass(frozen=True)
class BFCLFunction:
    name: str
    description: str
    parameters: Mapping[str, Any]


@dataclass(frozen=True)
class BFCLTask:
    task_id: str
    prompt: str
    expected_tool: str
    category: str


class BFCLRouter:
    name = "router"

    def choose(
        self,
        task: BFCLTask,
        tools: Sequence[BFCLFunction],
        rng: random.Random,
    ) -> Tuple[str, Dict[str, float]]:
        raise NotImplementedError

    def update(self, task: BFCLTask, selected_tool: str, reward: float) -> None:
        return None


def _proxy_opener() -> urllib.request.OpenerDirector:
    proxies = {}
    for scheme, env_name in (("http", "HTTP_PROXY"), ("https", "HTTPS_PROXY")):
        proxy = os.environ.get(env_name) or os.environ.get(env_name.lower())
        if proxy:
            proxies[scheme] = proxy
    return urllib.request.build_opener(urllib.request.ProxyHandler(proxies))


def _read_text(path_or_url: str, timeout: int) -> str:
    path = Path(path_or_url)
    if path.exists():
        return path.read_text(encoding="utf-8")
    if path_or_url.startswith(("http://", "https://")):
        url = path_or_url
    else:
        url = f"{HF_BASE_URL}/{path_or_url.lstrip('/')}"
    with _proxy_opener().open(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


def iter_jsonl(text: str) -> Iterable[Mapping[str, Any]]:
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError(f"JSONL row {line_number} is not an object")
        yield payload


def _prompt_from_question(question: Any) -> str:
    if isinstance(question, str):
        return question
    if isinstance(question, Sequence):
        parts = []
        for turn in question:
            if isinstance(turn, Sequence) and not isinstance(turn, (str, bytes)):
                for message in turn:
                    if isinstance(message, Mapping):
                        content = message.get("content")
                        if content:
                            parts.append(str(content))
            elif isinstance(turn, Mapping):
                content = turn.get("content")
                if content:
                    parts.append(str(content))
        return "\n".join(parts)
    return str(question)


def _expected_from_answer(answer: Mapping[str, Any]) -> str | None:
    ground_truth = answer.get("ground_truth")
    if not isinstance(ground_truth, Sequence) or isinstance(ground_truth, str) or not ground_truth:
        return None
    first = ground_truth[0]
    if not isinstance(first, Mapping) or not first:
        return None
    return str(next(iter(first.keys())))


def load_bfcl_subset(
    input_path: str,
    answer_path: str,
    limit: int,
    timeout: int,
) -> Tuple[List[BFCLTask], List[BFCLFunction], Mapping[str, Any]]:
    input_records = list(iter_jsonl(_read_text(input_path, timeout)))
    answer_records = list(iter_jsonl(_read_text(answer_path, timeout)))
    answers = {
        str(record["id"]): _expected_from_answer(record)
        for record in answer_records
        if "id" in record
    }

    tasks: List[BFCLTask] = []
    functions_by_name: Dict[str, BFCLFunction] = {}
    skipped = []
    for record in input_records:
        task_id = str(record.get("id", ""))
        expected = answers.get(task_id)
        functions = record.get("function") or []
        if not expected or not isinstance(functions, Sequence):
            skipped.append({"id": task_id, "reason": "missing expected function or schema"})
            continue
        for fn in functions:
            if not isinstance(fn, Mapping) or "name" not in fn:
                continue
            functions_by_name[str(fn["name"])] = BFCLFunction(
                name=str(fn["name"]),
                description=str(fn.get("description", "")),
                parameters=fn.get("parameters") if isinstance(fn.get("parameters"), Mapping) else {},
            )
        if expected not in functions_by_name:
            skipped.append({"id": task_id, "reason": f"expected function not in schema: {expected}"})
            continue
        tasks.append(
            BFCLTask(
                task_id=task_id,
                prompt=_prompt_from_question(record.get("question")),
                expected_tool=expected,
                category=str(record.get("category") or "bfcl_simple"),
            )
        )
        if len(tasks) >= limit:
            break

    return tasks, sorted(functions_by_name.values(), key=lambda fn: fn.name), {
        "input_records": len(input_records),
        "answer_records": len(answer_records),
        "skipped_preview": skipped[:20],
    }


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split()
        if len(token) > 1
    }


class RandomBFCLRouter(BFCLRouter):
    name = "random"

    def choose(self, task: BFCLTask, tools: Sequence[BFCLFunction], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        return rng.choice(list(tools)).name, {}


class SchemaOverlapRouter(BFCLRouter):
    name = "schema_overlap_router"

    def choose(self, task: BFCLTask, tools: Sequence[BFCLFunction], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        scores = _schema_overlap_scores(task, tools)
        return _stable_argmax(scores), scores


def _schema_overlap_scores(task: BFCLTask, tools: Sequence[BFCLFunction]) -> Dict[str, float]:
    prompt_tokens = _tokens(task.prompt)
    scores = {}
    for tool in tools:
        tool_tokens = _tokens(f"{tool.name} {tool.description} {json.dumps(tool.parameters, sort_keys=True)}")
        scores[tool.name] = float(len(prompt_tokens & tool_tokens))
    return scores


class ContextualEpsilonRouter(BFCLRouter):
    def __init__(self, epsilon: float = 0.1):
        self.name = f"contextual_epsilon_{epsilon:.2f}"
        self.epsilon = epsilon
        self.attempts: Dict[Tuple[str, str], float] = {}
        self.rewards: Dict[Tuple[str, str], float] = {}

    def choose(self, task: BFCLTask, tools: Sequence[BFCLFunction], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        if rng.random() < self.epsilon:
            return rng.choice(list(tools)).name, {}
        scores = {}
        for tool in tools:
            key = (task.category, tool.name)
            attempts = self.attempts.get(key, 0.0)
            scores[tool.name] = self.rewards.get(key, 0.0) / attempts if attempts else 0.5
        return _stable_argmax(scores), scores

    def update(self, task: BFCLTask, selected_tool: str, reward: float) -> None:
        key = (task.category, selected_tool)
        self.attempts[key] = self.attempts.get(key, 0.0) + 1.0
        self.rewards[key] = self.rewards.get(key, 0.0) + reward


class ContextualEFERouter(BFCLRouter):
    def __init__(self, w_e: float = 0.45, discount: float | None = None):
        suffix = "discounted" if discount is not None else "static"
        self.name = f"contextual_efe_{suffix}_we_{w_e:.2f}"
        self.w_e = w_e
        self.w_p = 1.0 - w_e
        self.discount = discount
        self.attempts: Dict[Tuple[str, str], float] = {}
        self.rewards: Dict[Tuple[str, str], float] = {}

    def _decay_category(self, category: str) -> None:
        if self.discount is None:
            return
        for key in list(self.attempts):
            if key[0] == category:
                self.attempts[key] *= self.discount
                self.rewards[key] *= self.discount

    def choose(self, task: BFCLTask, tools: Sequence[BFCLFunction], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        scores = {}
        for tool in tools:
            key = (task.category, tool.name)
            attempts = self.attempts.get(key, 0.0)
            rewards = self.rewards.get(key, 0.0)
            epistemic = 1.0 / (1.0 + attempts)
            pragmatic = rewards / attempts if attempts else 0.5
            scores[tool.name] = self.w_e * epistemic + self.w_p * pragmatic
        return _stable_argmax(scores), scores

    def update(self, task: BFCLTask, selected_tool: str, reward: float) -> None:
        self._decay_category(task.category)
        key = (task.category, selected_tool)
        self.attempts[key] = self.attempts.get(key, 0.0) + 1.0
        self.rewards[key] = self.rewards.get(key, 0.0) + reward


class SchemaConditionedEFERouter(ContextualEFERouter):
    def __init__(self, w_schema: float = 0.85, w_e: float = 0.10, discount: float | None = None):
        super().__init__(w_e=w_e, discount=discount)
        suffix = "discounted" if discount is not None else "static"
        self.name = f"schema_conditioned_efe_{suffix}"
        self.w_schema = w_schema
        self.w_e = w_e
        self.w_p = max(0.0, 1.0 - w_schema - w_e)

    def choose(self, task: BFCLTask, tools: Sequence[BFCLFunction], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        schema_scores = _schema_overlap_scores(task, tools)
        max_schema = max(schema_scores.values()) or 1.0
        scores = {}
        for tool in tools:
            key = (task.category, tool.name)
            attempts = self.attempts.get(key, 0.0)
            rewards = self.rewards.get(key, 0.0)
            epistemic = 1.0 / (1.0 + attempts)
            pragmatic = rewards / attempts if attempts else 0.5
            schema_prior = schema_scores[tool.name] / max_schema
            scores[tool.name] = (
                self.w_schema * schema_prior
                + self.w_e * epistemic
                + self.w_p * pragmatic
            )
        return _stable_argmax(scores), scores


class UCBRouter(BFCLRouter):
    def __init__(self, c: float = 2.0):
        self.name = f"ucb_{c:.1f}"
        self.c = c
        self.attempts: Dict[str, float] = {}
        self.rewards: Dict[str, float] = {}

    def choose(self, task: BFCLTask, tools: Sequence[BFCLFunction], rng: random.Random) -> Tuple[str, Dict[str, float]]:
        total = sum(self.attempts.get(tool.name, 0.0) for tool in tools)
        for tool in tools:
            if self.attempts.get(tool.name, 0.0) == 0.0:
                return tool.name, {}
        scores = {}
        for tool in tools:
            attempts = self.attempts[tool.name]
            mean = self.rewards.get(tool.name, 0.0) / attempts
            scores[tool.name] = mean + self.c * math.sqrt(math.log(total + 1.0) / attempts)
        return _stable_argmax(scores), scores

    def update(self, task: BFCLTask, selected_tool: str, reward: float) -> None:
        self.attempts[selected_tool] = self.attempts.get(selected_tool, 0.0) + 1.0
        self.rewards[selected_tool] = self.rewards.get(selected_tool, 0.0) + reward


def _stable_argmax(scores: Mapping[str, float]) -> str:
    best = max(scores.values())
    return sorted(name for name, score in scores.items() if score == best)[0]


def make_routers() -> Sequence[BFCLRouter]:
    return (
        SchemaOverlapRouter(),
        SchemaConditionedEFERouter(w_schema=0.85, w_e=0.10),
        SchemaConditionedEFERouter(w_schema=0.85, w_e=0.10, discount=0.98),
        ContextualEFERouter(w_e=0.45),
        ContextualEFERouter(w_e=0.45, discount=0.98),
        ContextualEpsilonRouter(epsilon=0.10),
        UCBRouter(c=2.0),
        RandomBFCLRouter(),
    )


def make_sequence(tasks: Sequence[BFCLTask], trials: int, rng: random.Random) -> List[BFCLTask]:
    sequence: List[BFCLTask] = []
    while len(sequence) < trials:
        block = list(tasks)
        rng.shuffle(block)
        sequence.extend(block)
    return sequence[:trials]


def run_one_router(
    router: BFCLRouter,
    tasks: Sequence[BFCLTask],
    tools: Sequence[BFCLFunction],
    trials: int,
    seed: int,
    trace_limit: int,
) -> Mapping[str, Any]:
    rng = random.Random(seed)
    exact_hits = 0
    traces = []
    for step, task in enumerate(make_sequence(tasks, trials, rng)):
        selected_tool, scores = router.choose(task, tools, rng)
        exact = selected_tool == task.expected_tool
        reward = 1.0 if exact else 0.0
        router.update(task, selected_tool, reward)
        exact_hits += int(exact)
        if len(traces) < trace_limit:
            traces.append(
                {
                    "step": step,
                    "task_id": task.task_id,
                    "prompt": task.prompt,
                    "expected_tool": task.expected_tool,
                    "selected_tool": selected_tool,
                    "exact_tool": exact,
                    "reward": reward,
                    "selector_scores_preview": dict(list(scores.items())[:20]),
                }
            )
    return {
        "router": router.name,
        "exact_tool_rate": exact_hits / trials,
        "reward": exact_hits,
        "traces": traces,
    }


def summarize_runs(runs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for run in runs:
        grouped.setdefault(str(run["router"]), []).append(run)
    summary = {}
    for router, entries in grouped.items():
        exact = [float(entry["exact_tool_rate"]) for entry in entries]
        rewards = [float(entry["reward"]) for entry in entries]
        summary[router] = {
            "exact_tool_rate_mean": statistics.fmean(exact),
            "exact_tool_rate_std": statistics.pstdev(exact),
            "reward_mean": statistics.fmean(rewards),
            "reward_std": statistics.pstdev(rewards),
        }
    return dict(sorted(summary.items(), key=lambda item: item[1]["exact_tool_rate_mean"], reverse=True))


def run_benchmark(
    input_path: str,
    answer_path: str,
    limit: int,
    runs: int,
    trials: int,
    seed: int,
    trace_limit: int,
    include_traces: bool,
    timeout: int,
) -> Mapping[str, Any]:
    tasks, tools, load_metadata = load_bfcl_subset(
        input_path=input_path,
        answer_path=answer_path,
        limit=limit,
        timeout=timeout,
    )
    if not tasks:
        raise ValueError("No BFCL tasks loaded")
    effective_trials = trials or len(tasks)
    all_runs = []
    trace_samples = {}
    effective_trace_limit = trace_limit if include_traces else 0
    for run_idx in range(runs):
        for router in make_routers():
            result = run_one_router(
                router=router,
                tasks=tasks,
                tools=tools,
                trials=effective_trials,
                seed=seed + run_idx,
                trace_limit=effective_trace_limit,
            )
            all_runs.append({key: value for key, value in result.items() if key != "traces"})
            if include_traces:
                trace_samples.setdefault(str(result["router"]), result["traces"])
    payload: Dict[str, Any] = {
        "metadata": {
            "description": "Paper 4 BFCL subset schema-routing diagnostic",
            "benchmark_type": "bfcl_subset_schema_routing",
            "positioning": (
                "Uses official BFCL v3 JSONL rows as an external schema-routing "
                "diagnostic. This is not an official BFCL score."
            ),
            "dataset": "gorilla-llm/Berkeley-Function-Calling-Leaderboard",
            "input_path": input_path,
            "answer_path": answer_path,
            "limit": limit,
            "loaded_tasks": len(tasks),
            "candidate_tools": len(tools),
            "runs": runs,
            "trials_per_run": effective_trials,
            "seed": seed,
            "include_traces": include_traces,
            "trace_limit": effective_trace_limit,
            "trace_policy": (
                "Prompt-level BFCL examples are omitted by default. Use --include-traces "
                "for local debugging only."
            ),
            **load_metadata,
        },
        "summary": summarize_runs(all_runs),
        "runs": all_runs,
    }
    if include_traces:
        payload["trace_samples"] = trace_samples
    return payload


def write_results(payload: Mapping[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "paper4_bfcl_subset_router.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def print_summary(payload: Mapping[str, Any], output_path: Path) -> None:
    print("Paper 4 BFCL subset schema-routing diagnostic")
    print("=" * 78)
    print(f"Results: {output_path}")
    print(
        f"Dataset: {payload['metadata']['dataset']} | "
        f"tasks={payload['metadata']['loaded_tasks']} | "
        f"candidate_tools={payload['metadata']['candidate_tools']}"
    )
    print("This is not an official BFCL score.")
    print()
    print(f"{'Router':38s} {'Exact tool':>12s} {'Reward':>12s}")
    print("-" * 78)
    trials = int(payload["metadata"]["trials_per_run"])
    for router, row in payload["summary"].items():
        print(f"{router:38s} {row['exact_tool_rate_mean'] * 100:11.1f}% {row['reward_mean']:6.1f}/{trials:<5d}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Paper 4 BFCL subset schema-routing diagnostic.")
    parser.add_argument("--input", default=DEFAULT_INPUT_PATH)
    parser.add_argument("--answers", default=DEFAULT_ANSWER_PATH)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--trials", type=int, default=0, help="0 means one pass over loaded tasks.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--trace-limit", type=int, default=12)
    parser.add_argument(
        "--include-traces",
        action="store_true",
        help=(
            "Persist prompt-level trace samples. Disabled by default so public result "
            "artifacts do not bundle external benchmark examples."
        ),
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_benchmark(
        input_path=args.input,
        answer_path=args.answers,
        limit=args.limit,
        runs=args.runs,
        trials=args.trials,
        seed=args.seed,
        trace_limit=args.trace_limit,
        include_traces=args.include_traces,
        timeout=args.timeout,
    )
    output_path = write_results(payload, args.output_dir)
    print_summary(payload, output_path)


if __name__ == "__main__":
    main()
