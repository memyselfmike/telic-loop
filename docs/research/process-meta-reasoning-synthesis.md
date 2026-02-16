# Process Meta-Reasoning Research Synthesis

**Date**: 2026-02-15
**Context**: Designing Gap 2 (Process Meta-Reasoning) for Loop V3

## Key Frameworks Studied

1. **Reflexion** (Shinn et al., NeurIPS 2023) — Episodic memory of verbal self-reflections. Caps at 3 failures. +8% over simple retry. Limitation: task-level only, no cross-task pattern detection.
2. **LATS** (ICML 2024) — Tree search over trajectories. Dual value function (LM score + self-consistency). Limitation: single-problem scope.
3. **Self-Refine** (Madaan et al., NeurIPS 2023) — Generate → Feedback → Refine loop. +20% average. Key: feedback must have localization + instruction.
4. **CRITIC** (Gou et al., 2023) — External tool verification. Key insight: LLMs are bad at self-verification; use external data.
5. **Bayesian Meta-Reasoning** (Qi et al., ICML 2025) — System 1/System 2 model. LLMs should reflect on HOW they reason, not just WHAT.
6. **VOC (Value of Computation)** (De Sabbata et al., 2024) — Only compute if expected improvement > cost. Reduces tokens 20-37%.

## Core Design Principles

1. **Compute metrics, not opinions** — Monitor computes numerical metrics from execution data, not LLM self-assessment
2. **Tiered triggers** — Most checks are arithmetic (free). LLM only on RED threshold
3. **Bounded meta-levels** — Exactly one level. Nothing reasons about the monitor
4. **Cheap by default** — Per-iteration cost ~0. LLM invoked 2-4 times per sprint (~2-4% overhead)

## Process Health Metrics

| Metric | What It Measures | Degradation Signal |
|--------|-----------------|-------------------|
| Value velocity | VRC delta per iteration | Declining EMA |
| Token efficiency | VRC delta per token | Rising cost per progress |
| Fix convergence | Are fixes working? | Same error hash after fix |
| Task churn | State oscillation | Fails → fixes → fails |
| Error clustering | Failure patterns | >60% share root cause |
| File concentration | Effort distribution | Same files touched repeatedly |
| Budget-value alignment | Effort vs value | Budget 2x ahead of value |

## Trigger Thresholds

- GREEN: All metrics within bounds → no action
- YELLOW: Approaching threshold → log warning, increase monitoring
- RED: Threshold crossed → invoke Strategy Reasoner (Opus)

Minimum interval between LLM invocations: 5 iterations or 10% budget

## Strategy Changes (distinct from Plan Changes)

| Category | Example |
|----------|---------|
| Test approach | bash → pytest for API endpoints |
| Fix approach | targeted edits → function refactoring |
| Execution order | priority → dependency ordering |
| Scope reduction | full implementation → MVP + TODO |
| Research timing | after 3 failures → before first attempt |
| Escalation threshold | lower "ask for help" bar |

## Anti-Patterns

1. Don't meta-reason on easy problems (hurts performance)
2. Don't meta-reason in first 5 iterations (insufficient data)
3. Don't meta-reason right after a strategy change (give it time)
4. Don't meta-reason at 95%+ budget (spend remaining on execution)
5. Don't meta-reason without actionable alternatives

## Sources

- Reflexion (NeurIPS 2023), Self-Refine (NeurIPS 2023), LATS (ICML 2024), CRITIC (2023)
- Bayesian Meta-Reasoning (ICML 2025), VOC for LLMs (De Sabbata 2024)
- SPC/CUSUM (industrial process control), Code Churn (LinearB, Opsera)
- Multi-Armed Bandits, AutoML algorithm selection
- Russell & Wefald (Principles of Metareasoning, 1991)
