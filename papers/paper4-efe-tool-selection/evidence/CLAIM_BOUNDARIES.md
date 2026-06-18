
# Claim Boundaries for Paper4 Tool-Learning Evidence

## CAN Claim (Safe)

1. **Local Diagnostic Results**:
   - 20 local fixtures covering diverse domains
   - 40 BFCL-compatible tasks (official_compatible_subset format)
   - 53 categorical Dirichlet EFE local diagnostic scenarios across 10 scenario families
   - 20 local multi-turn long-trace scenarios (5-20 turns each) with computed same-domain tool selection
   - 124 total turns across long-trace evaluation
   - 40 counterfactual interventions with critical/non-critical utility metrics
   - 8 ablation conditions tested across 3 seeds, including 7 required ablations plus an executive-control extension
   - 5-seed local bandit comparison over EFE, epsilon-greedy, UCB, Thompson, schema-match, and affordance-weighted selectors

2. **Methodological**:
   - BFCL-compatible format (structure matches BFCL simple)
   - Non-placeholder feature computation (schema overlap, domain relevance, history prior)
   - Trace capture and replay system implemented
   - Executive Control metadata in traces
   - Multiple seeds for statistical validation (no cherry-picking)

3. **Architecture**:
   - CLS memory system vs SimpleMemory comparison
   - EFE-based tool selection vs UCB baseline
   - Preparedness scoring impact measured
   - Causal utility tracking implemented
   - Ablation local diagnostic records component-toggle effects through TurnOrchestrator with mock tools
   - Runtime EFE selector uses a categorical Dirichlet outcome belief with risk, ambiguity, and expected-information-gain decomposition
   - Trace replay mode diagnostics compare exact replay with fast context-block-removal replay over stored ExecutionTrace objects

4. **Official-Format Ingestion Bridge**:
   - Optional loader for user-supplied BFCL/API-Bank/ToolBench-style JSONL files
   - Local normalization into the internal BenchmarkTask schema
   - Local selector/executor evaluation only when the user supplies files

## CANNOT Claim (Unsafe - Will Be Rejected)

1. **Official Benchmark Claims**:
   - [NO] Official BFCL benchmark results
   - [NO] Official ToolBench evaluation
   - [NO] Official API-Bank results
   - [NO] AgentBench official scores
   - [NO] TraceEval official results
   - [NO] Official leaderboard result from local evaluation
   - [NO] Leaderboard rankings or submissions

2. **Paper Status**:
   - [NO] NeurIPS 2026 accepted/submitted
   - [NO] Workshop accepted/confirmed
   - [NO] Peer-reviewed results
   - [NO] 80% acceptance rate or any probability estimates

3. **System Maturity**:
   - [NO] SOTA (state-of-the-art) claims
   - [NO] Production-ready system
   - [NO] 100% validated
   - [NO] Real-world deployment results
   - [NO] Formal regret proof or complete biological active-inference model
   - [NO] Claiming legacy count-proxy experiments are the real categorical EFE implementation

4. **Data Provenance**:
   - [NO] Using official BFCL/ToolBench/API-Bank data unless the user has manually supplied a local source file
   - [NO] Official benchmark environment
   - [NO] Official scores from locally supplied data
   - [NO] Long-trace scenarios are real external tool traces (they are local diagnostics with a bounded local executor)

## Recommended Phrasing

### Good Examples:
- "We evaluate on 40 tasks in BFCL-compatible format"
- "Local diagnostic results show X% accuracy"
- "Tested with official_compatible_subset (not official submission)"
- "Ablation study demonstrates component Y contributes Z"
- "Long-trace local diagnostics generate replayable traces from a computed local selector and bounded executor"
- "The ingestion bridge can locally evaluate user-supplied official-format JSONL files, but these are not official submissions"
- "A local diagnostic distinguishes categorical EFE behavior from UCB/count-proxy behavior in bounded scenarios"
- "Multi-seed local bandit comparison reports reward, pseudo-regret, safety, and nonstationary recovery diagnostics"
- "Trace replay mode diagnostics are local ExecutionTrace replays, not official TraceEval results"

### Bad Examples (Avoid):
- "We achieve X% on BFCL benchmark" (implies official)
- "Our system ranks #N on leaderboard" (no submission)
- "SOTA performance" (no official comparison)
- "Workshop-ready paper" (not confirmed)
- "Long-trace results are real-world tool traces" (they are not)
- "We prove EFE regret bounds" (not proven)

## Evidence Type Classification

All results must be labeled as one of:
- `local_fixture`: 20 hand-crafted tasks
- `local_diagnostic`: Internal evaluation
- `official_compatible_subset`: Format-compatible but not official data
- `official_user_supplied_local_evaluation`: user-supplied file evaluated locally, not an official submission
- `trace_replay_local_diagnostic`: local replay-mode summaries over stored ExecutionTrace files
- Never: `benchmark_official`, `leaderboard`, `official_submission`
