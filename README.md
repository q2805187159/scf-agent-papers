# SCF Agent Paper Artifacts

Public, paper-adjacent artifacts for SCF Agent research.

This repository intentionally does **not** publish full manuscript drafts, LaTeX sources, PDFs, private runtime code, or local machine paths. It is an artifact-only repository for reproducible public experiments that can support future papers without exposing unpublished manuscripts prematurely.

## Included

- `papers/paper4-efe-tool-selection/experiments/real_tool_benchmark.py`: self-contained executable function-calling benchmark.
- `papers/paper4-efe-tool-selection/experiments/external_function_call_adapter.py`: normalized/BFCL-like/API-Bank-like JSONL adapter smoke test.
- `papers/paper4-efe-tool-selection/experiments/fixtures/bfcl_api_bank_style_sample.jsonl`: small public fixture for adapter verification.
- `papers/paper4-efe-tool-selection/experiments/results/`: generated JSON result artifacts.

## Status

- Paper 1 is not submitted or posted.
- Paper 4 is not submitted or accepted.
- This repository is not an archival preprint and should not be cited as a complete paper draft.

## Reproduction

Local executable function-calling:

```bash
python papers/paper4-efe-tool-selection/experiments/real_tool_benchmark.py --runs 50 --trials 240 --seed 42 --trace-limit 12
```

External adapter smoke test:

```bash
python papers/paper4-efe-tool-selection/experiments/external_function_call_adapter.py --rounds 20 --seed 42 --trace-limit 12
```

These are BFCL/API-Bank-style local artifacts. They are not official BFCL, ToolBench, API-Bank, APIBench, or AgentBench scores.

## Repository Boundary

Do not add manuscript drafts, LaTeX sources, PDFs, private runtime code, local machine paths, credentials, or unpublished implementation internals to this repository.
