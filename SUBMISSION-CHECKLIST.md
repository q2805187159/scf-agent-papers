# Paper Posting and Submission Checklist

Last updated: 2026-06-17

Paper 1 has been publicly posted as a ResearchGate preprint. Paper 4 is not submitted or posted yet. This checklist reflects the current route:

- Paper 1: ResearchGate preprint v0.1 is public under DOI `10.13140/RG.2.2.28965.05605`; continue strengthening the manuscript and experiments before any venue submission. arXiv is not the current route because endorsement/access is unavailable.
- Paper 1 page: `https://www.researchgate.net/publication/407184214_SCF_Agent_V3_A_Neuroscience-Inspired_Cognitive_Architecture_for_Long-Horizon_AI_Agents`
- Paper 4: prepare for the NeurIPS 2026 tool-learning / agent tool-use workshop direction. Verify the exact official workshop name, template, page limit, anonymity rule, and deadline before submission.

## Global Gates

- [ ] All paper numbers reproduced from current isolated scripts.
- [ ] Figures regenerated from current scripts.
- [ ] Statistical tests run in a locked environment with `scipy`.
- [ ] LaTeX compiles without errors in a real TeX environment or Overleaf.
- [ ] Limitations updated after final result regeneration.
- [ ] No arXiv ID, accepted status, submitted status, or platform DOI beyond the recorded ResearchGate DOI is claimed before it actually exists.
- [ ] Deleted stale reports and old draft snapshots are not recreated.

## Paper 1 Preprint Gates

Current state:

- Exp1 predictive coding passes the diagnostic target.
- Exp2 EFE result is promising in the seeded diagnostic: EFE 72.1 +/- 25.4 versus epsilon-greedy 53.4 +/- 19.4, p=0.0025.
- Exp3 CLS retention currently recalls 50/50 facts with 100.0% final retention.
- Exp4 legacy mock suite is saturated: SCF 100.0%, baseline 100.0%; treat it as a smoke test only.
- Exp4 harder diagnostic is now available: SCF 75.6%, baseline 34.6% over 78 rubric-graded tasks, mean score 0.903 versus 0.571, with channel-level ablations.

Required before any revised preprint version or venue submission:

- [ ] Re-run Paper 1 after any code change and archive the latest JSON result file.
- [ ] Confirm every figure used by the private manuscript source comes from the latest run.
- [ ] Confirm the abstract does not claim baseline superiority in Exp4.
- [ ] Confirm the manuscript says "ResearchGate preprint" or "manuscript draft", not "accepted" or "submitted".
- [ ] Prepare a private manuscript source bundle when a venue submission target is selected.
- [ ] Remove any venue/platform-specific language until the author selects the actual target.

Recommended strengthening before venue submission:

- [ ] Replace the current harder diagnostic with external/non-mock tool tasks before making broad superiority claims.
- [ ] Convert the current channel-level ablations into physical component-removal ablations if the paper needs stronger causal evidence.
- [ ] Add a harder CLS stress test beyond the current 50-fact diagnostic.

## Paper 4 Workshop Gates

Current state:

- Primary 30-run baseline ranks EFE third.
- Optimized single-run diagnostic favors EFE but is not primary evidence.
- 10-tool scalability is weak for EFE.
- Theory diagnostics do not establish convergence/proof claims.
- Simulated routing shows diversity but not success advantage.
- Local executable function-calling now exists as a BFCL-style artifact, but it is not an official BFCL, ToolBench, API-Bank, or AgentBench score.
- The public sanitized evidence pack now contains 8 table-ready CSV/JSON artifacts, including 53 categorical EFE local diagnostic rows, 20 local long-trace scenarios, trace replay mode diagnostics, and a 5-seed bandit-style comparison. The generated evidence summary still marks `paper4_ready` as `false`.

Required before NeurIPS 2026 workshop submission:

- [ ] Verify the official workshop name and deadline.
- [ ] Convert the private Paper 4 manuscript source to the workshop template once available.
- [ ] Keep the thesis mixed/diagnostic: static settings favor simple baselines, while contextual non-stationarity is the current positive niche.
- [ ] Preserve the epistemic-only/pragmatic-only sensitivity table in the final manuscript.
- [ ] Preserve the contextual routing and non-stationary tool-quality task if claiming tool-learning relevance.
- [ ] Add the contextual shift diagnostic to the final Paper 4 evidence table.
- [ ] Preserve the local executable function-calling benchmark or replace it with an official BFCL/API-Bank/ToolBench-compatible adapter before submission.
- [ ] Keep simulated routing labeled as simulated routing unless real external tools are executed.
- [ ] Rebuild all tables from result JSON files.

## Prohibited Claims

- [ ] "Accepted" / "submitted" before real submission.
- [ ] Platform DOI beyond the recorded ResearchGate DOI before it exists.
- [ ] "arXiv preprint" while arXiv is not the selected route.
- [ ] "EFE significantly outperforms all baselines."
- [ ] "Paper 4 has proven O(log T) regret."
- [ ] "Real agent benchmark" for the simulated routing script.
- [ ] "Official BFCL/API-Bank/ToolBench result" for the local executable function-calling benchmark.
- [ ] "Paper ready" or "workshop ready" without passing the gates above.

## Minimum Verification Before Any Final Draft

```bash
python -m pytest tests -q
python -m py_compile paper/experiments/run_paper1_experiments.py paper/experiments/run_paper4_experiments.py
python paper/experiments/run_paper1_experiments.py --check
python paper/experiments/run_paper4_experiments.py --list
```
# Submission Boundary Note

This public repository is artifact-only. It intentionally excludes full manuscript drafts, LaTeX sources, and PDFs until the author explicitly decides to publish a preprint or a camera-ready version.
