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
    coherence_has_issues = do_full_coherence_eval(config, state, claude)
    if coherence_has_issues and state.coherence_history:
        latest = state.coherence_history[-1]
        if latest.overall == "CRITICAL":
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

    # 4. Comprehensive code quality enforcement
    if config.code_health_enforce_at_exit:
        from .code_quality import create_quality_tasks, run_all_quality_checks
        from .process_monitor import scan_file_line_counts

        scan_file_line_counts(state, config)
        run_all_quality_checks(state, config)
        pm = state.process_monitor

        # --- Blocking checks (hard gate) ---
        blocking_issues: list[str] = []

        # MONOLITH: exclude style files (.css/.scss/.less)
        style_exts = {".css", ".scss", ".less"}
        monolith_files = [
            (rel, lines)
            for rel, lines in pm.file_line_counts.items()
            if lines >= config.code_health_monolith_threshold
            and not any(rel.endswith(ext) for ext in style_exts)
        ]
        if monolith_files:
            for rel, lines in monolith_files:
                blocking_issues.append(
                    f"MONOLITH: {rel} ({lines} lines, max: {config.code_health_monolith_threshold})"
                )

        # LONG_FUNCTION: exclude files already flagged as monolithic
        monolith_rels = {rel for rel, _ in monolith_files}
        for rel, fns in pm.long_functions.items():
            if rel not in monolith_rels:
                for name, length in fns:
                    blocking_issues.append(
                        f"LONG_FUNCTION: {rel}::{name} ({length} lines, "
                        f"max: {config.code_health_max_function_lines})"
                    )

        # DUPLICATE
        for dup in pm.duplicate_blocks:
            blocking_issues.append(
                f"DUPLICATE: {dup['line_count']}-line block in {', '.join(dup['files'])}"
            )

        # DEBUG_ARTIFACT
        if pm.debug_artifact_count > 0:
            blocking_issues.append(
                f"DEBUG_ARTIFACT: {pm.debug_artifact_count} debug statement(s) in production code"
            )

        if blocking_issues:
            print(f"  EXIT GATE FAILED — {len(blocking_issues)} code quality issue(s):")
            for issue in blocking_issues[:10]:
                print(f"    {issue}")
            created = create_quality_tasks(state, config)
            if created:
                print(f"  Created {created} quality task(s)")
            return False

        # --- Non-blocking checks (informational) ---
        info_issues: list[str] = []
        if pm.missing_prd_files:
            info_issues.append(
                f"MISSING_STRUCTURE: {len(pm.missing_prd_files)} PRD file(s) not created"
            )
        if pm.test_source_ratio < config.code_health_min_test_ratio:
            info_issues.append(
                f"LOW_TEST_RATIO: {pm.test_source_ratio:.2f} (target: {config.code_health_min_test_ratio})"
            )
        if pm.todo_count > config.code_health_max_todo_count:
            info_issues.append(f"TODO_DEBT: {pm.todo_count} markers")

        if info_issues:
            print(f"  Code quality notes (non-blocking): {len(info_issues)}")
            for issue in info_issues:
                print(f"    {issue}")
            create_quality_tasks(state, config)

    print("  EXIT GATE PASSED — value verified")
    git_commit(config, state, f"telic-loop({config.sprint}): Exit gate passed — value verified")
    return True
