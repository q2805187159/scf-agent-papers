# Paper 4 Public Experiment Artifacts

This directory contains public-safe experiment artifacts for the Paper 4 tool-selection work. It intentionally excludes full manuscript drafts, LaTeX sources, and PDFs.

## Artifacts

- `experiments/real_tool_benchmark.py`: self-contained executable function-calling benchmark with six local tools and exact-result checking.
- `experiments/external_function_call_adapter.py`: adapter for normalized, BFCL-like, and API-Bank-like JSONL rows.
- `experiments/bfcl_subset_router.py`: optional BFCL-format schema-routing diagnostic; not an official BFCL score.
- `experiments/fixtures/bfcl_api_bank_style_sample.jsonl`: small smoke-test fixture.
- `experiments/results/`: generated JSON outputs.
- `evidence/`: sanitized Paper 4 table-ready evidence pack from the private runtime.

## Commands

```bash
python papers/paper4-efe-tool-selection/experiments/real_tool_benchmark.py --runs 50 --trials 240 --seed 42 --trace-limit 12
python papers/paper4-efe-tool-selection/experiments/external_function_call_adapter.py --rounds 20 --seed 42 --trace-limit 12
python papers/paper4-efe-tool-selection/experiments/bfcl_subset_router.py --limit 100 --runs 10 --seed 42 --trace-limit 12
```

The BFCL subset command writes summary metrics by default and omits prompt-level trace samples. Add `--include-traces` only for local debugging. If external data is unavailable, use the local fixture and evidence-pack artifacts instead.

## Boundaries

These artifacts are BFCL/API-Bank-style local diagnostics plus optional BFCL-format schema-routing diagnostics. They are not official BFCL, API-Bank, APIBench, ToolBench, AgentBench, TraceEval, or leaderboard scores. Paper 4 is not submitted or accepted.
