# SCF Agent Paper Artifacts

Public, paper-adjacent artifacts for SCF Agent research.

This repository intentionally does **not** publish full manuscript drafts, LaTeX sources, PDFs, private runtime code, or local machine paths. It is an artifact-only repository for reproducible public experiments that can support future papers without exposing unpublished manuscripts prematurely.

## Included

- `papers/paper4-efe-tool-selection/experiments/real_tool_benchmark.py`: self-contained executable function-calling benchmark.
- `papers/paper4-efe-tool-selection/experiments/external_function_call_adapter.py`: normalized/BFCL-like/API-Bank-like JSONL adapter smoke test.
- `papers/paper4-efe-tool-selection/experiments/bfcl_subset_router.py`: run-time downloader and schema-routing diagnostic for official BFCL v3 simple rows.
- `papers/paper4-efe-tool-selection/experiments/fixtures/bfcl_api_bank_style_sample.jsonl`: small public fixture for adapter verification.
- `papers/paper4-efe-tool-selection/experiments/results/`: generated JSON result artifacts.
- `papers/p0-runtime-acceptance/`: public-safe P0 runtime acceptance result artifact and JSON verifier.

## Status

- Paper 1 is publicly posted as a ResearchGate preprint only.
  - DOI: `10.13140/RG.2.2.28965.05605`
  - Page: `https://www.researchgate.net/publication/407184214_SCF_Agent_V3_A_Neuroscience-Inspired_Cognitive_Architecture_for_Long-Horizon_AI_Agents`
  - Boundary: not venue-submitted, not peer-reviewed, and not accepted.
- Paper 4 is not submitted or accepted.
- This repository itself is not an archival preprint and should not be cited as a complete paper draft. Cite the ResearchGate DOI/page for Paper 1 instead.

## Reproduction

Local executable function-calling:

```bash
python papers/paper4-efe-tool-selection/experiments/real_tool_benchmark.py --runs 50 --trials 240 --seed 42 --trace-limit 12
```

External adapter smoke test:

```bash
python papers/paper4-efe-tool-selection/experiments/external_function_call_adapter.py --rounds 20 --seed 42 --trace-limit 12
python papers/paper4-efe-tool-selection/experiments/bfcl_subset_router.py --limit 100 --runs 10 --seed 42 --trace-limit 12
```

P0 runtime acceptance artifact verification:

```bash
python papers/p0-runtime-acceptance/verify_p0_acceptance.py
```

These are BFCL/API-Bank-style local artifacts and external schema-routing diagnostics. They are not official BFCL, ToolBench, API-Bank, APIBench, or AgentBench scores.

The BFCL subset runner omits prompt-level trace samples from JSON outputs by default. Use `--include-traces` only for local debugging when you explicitly want to inspect examples downloaded at run time.

The P0 runtime acceptance artifact contains result JSON only; it does not publish the private runtime source used to generate it.

## Repository Boundary

Do not add manuscript drafts, LaTeX sources, PDFs, private runtime code, local machine paths, credentials, or unpublished implementation internals to this repository.
