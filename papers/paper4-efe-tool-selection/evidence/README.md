# Paper 4 Evidence Pack

Public-safe table-ready artifacts generated from the private SCF Agent V3 runtime.

This directory intentionally contains only sanitized CSV/JSON summaries and claim-boundary text. It does not include manuscript drafts, LaTeX sources, PDFs, private runtime source, raw local traces, or local machine paths.

## Contents

- `table1_baselines.*`: local fixture baseline summary.
- `table2_ablation.*`: local diagnostic ablation matrix.
- `table3_long_trace.*`: local long-trace scenario summary.
- `table4_counterfactual.*`: local counterfactual utility summary.
- `table5_official_status.*`: status of optional official-format local ingestion.
- `table6_real_efe.*`: categorical Dirichlet EFE local diagnostic decomposition.
- `table7_trace_replay_modes.*`: local exact/fast trace replay mode summary.
- `table8_bandit_comparison.*`: multi-seed local comparison against bandit-style baselines.
- `CLAIM_BOUNDARIES.md`: permitted and prohibited claim language.
- `evidence_pack_summary.json`: sanitized generation summary.

Current table row counts are 3 baseline rows, 8 ablation rows, 20 long-trace
rows, 1 counterfactual summary row, 3 official-format ingestion status rows,
53 EFE diagnostic rows, 2 trace replay mode rows, and 6 bandit-comparison rows.
The generated summary intentionally marks `paper4_ready` as `false`.

## Boundary

These artifacts support Paper 4 drafting, but they are not an official BFCL, ToolBench, API-Bank, APIBench, AgentBench, TraceEval, or leaderboard result. Paper 4 is not submitted or accepted.
