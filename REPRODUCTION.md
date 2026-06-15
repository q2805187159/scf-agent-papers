# Reproduction Guide

Last updated: 2026-06-15

This repository is artifact-only. It intentionally excludes LaTeX sources and manuscript PDFs.

## Local Executable Function Calling

Run from repository root:

```bash
python papers/paper4-efe-tool-selection/experiments/real_tool_benchmark.py --runs 50 --trials 240 --seed 42 --trace-limit 12
```

Expected summary:

| Router | Exact result | Reward mean |
| --- | ---: | ---: |
| schema keyword router | 100.0% | 240.0 / 240 |
| contextual EFE | 87.5% | 210.0 / 240 |
| contextual epsilon-greedy(0.1) | 86.2% | 206.8 / 240 |
| contextual UCB | 45.0% | 108.0 / 240 |
| random | 16.6% | 39.8 / 240 |
| global EFE | 14.6% | 35.1 / 240 |

The output JSON is written to:

```text
papers/paper4-efe-tool-selection/experiments/results/paper4_real_tool_benchmark.json
```

## External Adapter Smoke Test

Run from repository root:

```bash
python papers/paper4-efe-tool-selection/experiments/external_function_call_adapter.py --rounds 20 --seed 42 --trace-limit 12
```

Expected summary:

| Router | Exact result | Reward mean |
| --- | ---: | ---: |
| schema keyword router | 100.0% | 240.0 / 240 |
| contextual EFE | 87.5% | 210.0 / 240 |
| contextual epsilon-greedy(0.1) | 86.2% | 207.0 / 240 |
| contextual UCB | 45.0% | 108.0 / 240 |
| random | 15.8% | 38.0 / 240 |
| global EFE | 13.8% | 33.0 / 240 |

## BFCL Subset Schema Routing

Run from repository root:

```bash
python papers/paper4-efe-tool-selection/experiments/bfcl_subset_router.py --limit 100 --runs 10 --seed 42 --trace-limit 12
```

This downloads official BFCL v3 simple rows and possible answers at run time, then reformulates the first 100 rows as a schema-routing diagnostic over a 92-function candidate pool. This is not an official BFCL score.

Expected summary:

| Router | Exact tool | Reward mean |
| --- | ---: | ---: |
| schema-conditioned EFE static | 78.4% | 78.4 / 100 |
| schema-conditioned EFE discounted | 77.3% | 77.3 / 100 |
| schema overlap router | 77.0% | 77.0 / 100 |
| contextual epsilon-greedy(0.1) | 0.7% | 0.7 / 100 |
| UCB | 0.7% | 0.7 / 100 |
| history-only EFE | 0.6% | 0.6 / 100 |
| random | 0.3% | 0.3 / 100 |

## Claim Boundaries

- Do not claim Paper 4 is submitted, accepted, or workshop-ready.
- Do not claim EFE is generally superior to all baselines.
- Do not describe the local function-calling benchmark, external adapter, or BFCL subset schema-routing diagnostic as an official BFCL, ToolBench, API-Bank, APIBench, or AgentBench score.
- Do not describe simulated routing as a real external-agent benchmark.
