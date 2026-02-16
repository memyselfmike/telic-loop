"""Fresh-context exit verification (inside the loop)."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def do_exit_gate(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Run exit gate verification: coherence + regression sweep + fresh VRC + critical eval."""
    from ..git import git_commit
    from ..state import TaskState
    from .coherence import do_full_coherence_eval
    from .critical_eval import do_critical_eval
    from .execute import run_tests_parallel
    from .vrc import run_vrc

    state.exit_gate_attempts += 1
    print(f"\n  EXIT GATE (attempt #{state.exit_gate_attempts})")

    # Safety valve
    if state.exit_gate_attempts > config.max_exit_gate_attempts:
        print(f"  Max attempts ({config.max_exit_gate_attempts}) reached — partial report")
        return True

    # 0. Full coherence evaluation (catch cross-feature interaction issues)
    print("  Running full coherence evaluation...")
    coherence = do_full_coherence_eval(config, state, claude)
    if coherence and coherence.overall == "CRITICAL":
        print("  EXIT GATE FAILED — coherence CRITICAL")
        return False

    # 1. Full regression sweep
    print("  Running full regression sweep...")
    all_checks = [v for v in state.verifications.values() if v.script_path]
    results = run_tests_parallel(all_checks, config.regression_timeout * 2)

    final_passes = sum(1 for _, (code, _, _) in results.items() if code == 0)
    final_fails = sum(1 for _, (code, _, _) in results.items() if code != 0)
    print(f"  QC results: {final_passes} passed, {final_fails} failed")

    if final_fails > 0:
        print(f"  EXIT GATE FAILED — {final_fails} QC checks failing")
        for v_id, (code, stdout, stderr) in results.items():
            if code != 0:
                state.verifications[v_id].status = "failed"
        return False

    # 2. Fresh-context VRC (Opus, forced full)
    print("  Running fresh-context VRC...")
    fresh_vrc = run_vrc(config, state, claude, force_full=True)

    if fresh_vrc.recommendation != "SHIP_READY":
        print(f"  EXIT GATE FAILED — VRC says {fresh_vrc.recommendation}")
        print(f"  Gaps found: {len(fresh_vrc.gaps)}")
        for gap in fresh_vrc.gaps:
            if gap.get("suggested_task"):
                state.add_task(TaskState(
                    task_id=f"EG-{state.exit_gate_attempts}-{gap.get('id', 'gap')}",
                    source="exit_gate",
                    description=gap["suggested_task"],
                    value=gap.get("description", ""),
                    created_at=datetime.now().isoformat(),
                ))
        return False

    # 3. Final critical evaluation
    print("  Running final critical evaluation...")
    do_critical_eval(config, state, claude)

    new_tasks = [
        t for t in state.tasks.values()
        if t.source == "critical_eval" and t.status == "pending"
    ]
    if new_tasks:
        print(f"  EXIT GATE FAILED — critical eval found {len(new_tasks)} issues")
        return False

    print("  EXIT GATE PASSED — value verified")
    git_commit(config, state, f"telic-loop({config.sprint}): Exit gate passed — value verified")
    return True
