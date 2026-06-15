# P0 Runtime Acceptance Artifact

This directory contains public-safe P0 acceptance outputs for the SCF Agent V3 runtime. It intentionally does not publish private runtime source, manuscript drafts, LaTeX, or PDFs.

## Artifact

- `results/p0_acceptance_results.json`: deterministic local acceptance results generated from the private runtime repository.
- `verify_p0_acceptance.py`: schema and threshold checker for the JSON artifact.

## Current Result

Generated on 2026-06-15 from the private runtime acceptance command:

```bash
python paper/experiments/p0-acceptance/p0_acceptance_suite.py
```

Summary:

| Diagnostic | Target | Result |
| --- | ---: | ---: |
| CLS long-session retention | >= 0.90 | 1.00 |
| Preparedness-success Pearson | >= 0.60 | 0.987 |
| Causal utility precision/recall | >= 0.70 / >= 0.70 | 1.00 / 1.00 |
| Physical ablation toggles | subsystem state changes | pass |
| End-to-end p95 latency | < 1000 ms | 0.303 ms |
| Real tool task suite | >= 0.80 | 1.00 |
| Stability success rate | >= 0.95 | 1.00 |

## Boundaries

These are local P0 runtime acceptance diagnostics, not production load tests and not official BFCL, ToolBench, API-Bank, APIBench, AgentBench, or TraceEval scores.
