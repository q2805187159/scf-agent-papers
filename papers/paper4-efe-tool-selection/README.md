# Paper 4 Public Experiment Artifacts

This directory contains public-safe experiment artifacts for the Paper 4 tool-selection work. It intentionally excludes full manuscript drafts, LaTeX sources, and PDFs.

## Artifacts

- `experiments/real_tool_benchmark.py`: self-contained executable function-calling benchmark with six local tools and exact-result checking.
- `experiments/external_function_call_adapter.py`: adapter for normalized, BFCL-like, and API-Bank-like JSONL rows.
- `experiments/bfcl_subset_router.py`: run-time downloader for official BFCL v3 simple rows, reformulated as a schema-routing diagnostic.
- `experiments/fixtures/bfcl_api_bank_style_sample.jsonl`: small smoke-test fixture.
- `experiments/results/`: generated JSON outputs.

## Commands

```bash
python papers/paper4-efe-tool-selection/experiments/real_tool_benchmark.py --runs 50 --trials 240 --seed 42 --trace-limit 12
python papers/paper4-efe-tool-selection/experiments/external_function_call_adapter.py --rounds 20 --seed 42 --trace-limit 12
python papers/paper4-efe-tool-selection/experiments/bfcl_subset_router.py --limit 100 --runs 10 --seed 42 --trace-limit 12
```

The BFCL subset command writes summary metrics by default and omits prompt-level trace samples. Add `--include-traces` only for local debugging.

## Boundaries

These artifacts are BFCL/API-Bank-style local diagnostics plus a BFCL subset schema-routing diagnostic. They are not official BFCL, API-Bank, APIBench, ToolBench, or AgentBench scores.
