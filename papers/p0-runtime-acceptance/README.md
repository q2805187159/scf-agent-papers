# P0 Runtime Acceptance Artifact

This directory contains public-safe P0 acceptance outputs for the SCF Agent V3 runtime. It intentionally does not publish private runtime source, manuscript drafts, LaTeX, or PDFs.

## Artifact

- `results/p0_acceptance_results.json`: deterministic local acceptance results generated from the private runtime repository.
- `verify_p0_acceptance.py`: schema and threshold checker for the JSON artifact.

## Current Result

Generated on 2026-06-17 from the private runtime acceptance command:

```bash
python paper/experiments/p0-acceptance/p0_acceptance_suite.py
```

Suite expanded from 7 to 9 diagnostics on 2026-06-16 and revalidated after runtime hardening on 2026-06-17:
- Added: prediction-error decay (docs/v3 experiment 1)
- Added: counterfactual causal utility key-block recovery (minimal TraceEval-style)
- Upgraded: preparedness-success correlation now uses real-tool-trace labels (replaced synthetic labels)

Summary:

| Diagnostic | Target | Result |
| --- | ---: | ---: |
| CLS long-session retention | >= 0.90 | 1.00 |
| Prediction-error decay (final/initial ratio) | <= 0.30 | 8.92e-06 |
| Preparedness-success Pearson (real-tool-trace) | >= 0.60 | 0.837 |
| Causal utility precision/recall (selection-based) | >= 0.70 / >= 0.70 | 1.00 / 1.00 |
| Counterfactual causal utility precision/recall | >= 0.70 / >= 0.70 | 1.00 / 1.00 |
| Physical ablation toggles | subsystem state changes | pass |
| End-to-end p95 latency | < 1000 ms | 234.861 ms |
| Real tool task suite | >= 0.80 | 1.00 |
| Stability success rate | >= 0.95 | 1.00 |

## Boundaries

These are local P0 runtime acceptance diagnostics, not production load tests and not official BFCL, ToolBench, API-Bank, APIBench, AgentBench, or TraceEval scores.
