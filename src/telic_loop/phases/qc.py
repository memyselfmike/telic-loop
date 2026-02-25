"""Quality control: generate verifications, run tests, triage, fix (QC agent)."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def _epic_scoped_plan(config: LoopConfig, state: LoopState) -> str:
    """Return plan scoped to current + prior epics. Full plan for single_run."""
    if state.vision_complexity != "multi_epic" or not state.epics:
        if config.plan_file.exists():
            return config.plan_file.read_text(encoding="utf-8")
        return ""

    # Build a filtered plan showing only current + prior epic tasks
    scoped_epic_ids = set()
    for i in range(min(state.current_epic_index + 1, len(state.epics))):
        scoped_epic_ids.add(state.epics[i].epic_id)

    lines = ["# Implementation Plan (current + prior epics)\n"]
    for tid, t in sorted(state.tasks.items()):
        if t.epic_id not in scoped_epic_ids and t.epic_id:
            continue  # Skip future epic tasks; keep untagged tasks
        check = "x" if t.status == "done" else " "
        lines.append(f"- [{check}] **{tid}**: {t.description}")
        if t.acceptance:
            lines.append(f"  - Acceptance: {t.acceptance}")
    return "\n".join(lines)


def _epic_scope_instruction(state: LoopState) -> str:
    """Generate EPIC_SCOPE instruction. Empty string for single_run."""
    if state.vision_complexity != "multi_epic" or not state.epics:
        return ""
    if state.current_epic_index >= len(state.epics):
        return ""

    current = state.epics[state.current_epic_index]
    prior = [state.epics[i] for i in range(state.current_epic_index)]

    lines = [
        "\n## EPIC SCOPE — Generate verifications ONLY for these epics:\n",
        f"**Current epic ({state.current_epic_index + 1}/{len(state.epics)}):** {current.title}",
        f"Deliverables: {', '.join(current.deliverables)}",
    ]
    if prior:
        lines.append("\n**Prior epics (include regression coverage):**")
        for ep in prior:
            lines.append(f"- {ep.title}: {', '.join(ep.deliverables)}")
    lines.append(
        "\n**DO NOT** generate tests for features in later epics. "
        "Those features have not been built yet and tests will always fail."
    )
    return "\n".join(lines)


def do_generate_qc(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Generate QC verification scripts from the plan and context."""
    from ..claude import AgentRole, load_prompt
    from ..state import VerificationState

    session = claude.session(AgentRole.QC)
    prompt = load_prompt("generate_verifications",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PLAN=_epic_scoped_plan(config, state),
        PRD=config.prd_file.read_text(encoding="utf-8") if config.prd_file.exists() else "",
        VISION=config.vision_file.read_text(encoding="utf-8") if config.vision_file.exists() else "",
        VERIFICATION_STRATEGY=json.dumps(state.context.verification_strategy, indent=2),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        EPIC_SCOPE=_epic_scope_instruction(state),
    )
    session.send(prompt)

    # Discover generated scripts.
    # Agents may write scripts in two layouts:
    #   1. Flat with prefix:  verifications/unit_api_test.sh
    #   2. Nested in subdirs: verifications/unit/api_test.sh
    # We support both — flat prefix is what the prompt instructs.
    verify_dir = config.sprint_dir / ".loop" / "verifications"
    known_categories = ("unit", "integration", "value")
    if verify_dir.exists():
        # Layout 1: flat files with category prefix (unit_xxx.sh)
        for script in sorted(verify_dir.iterdir()):
            if script.is_dir():
                continue
            if script.suffix not in (".sh", ".py", ".js"):
                continue
            # Parse category from prefix: "unit_api_test.sh" → category="unit"
            stem = script.stem
            category = ""
            for cat in known_categories:
                if stem.startswith(cat + "_"):
                    category = cat
                    break
            if not category:
                category = "value"  # default if no recognized prefix
            if category not in state.verification_categories:
                state.verification_categories.append(category)
            v_id = f"{category}/{stem}"
            if v_id not in state.verifications:
                if sys.platform != "win32":
                    script.chmod(0o755)
                state.verifications[v_id] = VerificationState(
                    verification_id=v_id,
                    category=category,
                    script_path=script.resolve().as_posix(),
                    requires=_parse_requires(script),
                )

        # Layout 2: nested subdirectories (unit/api_test.sh)
        for category_dir in sorted(verify_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            if category not in state.verification_categories:
                state.verification_categories.append(category)
            for script in sorted(category_dir.iterdir()):
                if script.suffix not in (".sh", ".py", ".js"):
                    continue
                v_id = f"{category}/{script.stem}"
                if v_id not in state.verifications:
                    if sys.platform != "win32":
                        script.chmod(0o755)
                    state.verifications[v_id] = VerificationState(
                        verification_id=v_id,
                        category=category,
                        script_path=script.resolve().as_posix(),
                        requires=_parse_requires(script),
                    )

    if not state.verifications:
        # Fallback: if agent generated nothing, create a build-output check
        # so the loop has at least one verification to track
        _create_build_verification(config, state)

    if state.verifications:
        state.pass_gate("verifications_generated")
    return bool(state.verifications)


def _create_build_verification(config: LoopConfig, state: LoopState) -> None:
    """Create a minimal build-output verification when no scripts were generated.

    Checks common build output directories for non-empty content.
    Ensures QC is never 0/0 — even the simplest project gets verified.
    """
    from ..state import VerificationState

    project_dir = config.effective_project_dir

    # Find a build output directory
    build_dirs = ["dist", "build", "out", "_site", ".next", ".output"]
    found_dir = None
    for d in build_dirs:
        candidate = project_dir / d
        if candidate.is_dir() and any(candidate.iterdir()):
            found_dir = candidate
            break

    if not found_dir:
        return  # No build output to verify

    # Create the verification script
    verify_dir = config.sprint_dir / ".loop" / "verifications" / "value"
    verify_dir.mkdir(parents=True, exist_ok=True)
    script_path = verify_dir / "build_output_check.sh"

    rel_dir = found_dir.relative_to(project_dir)
    script_content = f"""#!/usr/bin/env bash
# Verification: Build output exists and contains expected files
# Category: value
# Auto-generated fallback verification
set -euo pipefail

BUILD_DIR="{project_dir / rel_dir}"

echo "=== Build Output Verification ==="

if [ ! -d "$BUILD_DIR" ]; then
  echo "FAIL: Build output directory does not exist: $BUILD_DIR"
  exit 1
fi

FILE_COUNT=$(find "$BUILD_DIR" -type f | wc -l)
if [ "$FILE_COUNT" -eq 0 ]; then
  echo "FAIL: Build output directory is empty"
  exit 1
fi

echo "PASS: Build output exists with $FILE_COUNT files in {rel_dir}/"

# Check for index/entry point
if [ -f "$BUILD_DIR/index.html" ]; then
  echo "PASS: index.html found"
elif ls "$BUILD_DIR"/*.html 1>/dev/null 2>&1; then
  echo "PASS: HTML files found"
else
  echo "INFO: No HTML entry point (may be expected for non-web builds)"
fi

exit 0
"""
    script_path.write_text(script_content, encoding="utf-8")

    v_id = "value/build_output_check"
    state.verifications[v_id] = VerificationState(
        verification_id=v_id,
        category="value",
        script_path=script_path.resolve().as_posix(),
    )
    if "value" not in state.verification_categories:
        state.verification_categories.append("value")
    print("  Fallback: created build output verification")


def do_run_qc(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Run pending QC checks category-by-category."""
    from ..state import FailureRecord
    from .execute import run_tests_parallel

    progress = False
    for category in state.verification_categories:
        pending = [
            v for v in state.verifications.values()
            if v.category == category and v.status == "pending"
        ]
        if not pending:
            continue
        if not _category_deps_met(category, state):
            continue

        results = run_tests_parallel(pending, config.regression_timeout)
        for v_id, (exit_code, stdout, stderr) in results.items():
            v = state.verifications[v_id]
            v.attempts += 1
            if exit_code == 0:
                v.status = "passed"
                state.add_regression_pass(v_id)
                progress = True
            else:
                v.status = "failed"
                v.failures.append(FailureRecord(
                    timestamp=datetime.now().isoformat(),
                    attempt=v.attempts,
                    exit_code=exit_code,
                    stdout=(stdout or "")[:2000],
                    stderr=(stderr or "")[:2000],
                ))
                state.research_attempted_for_current_failures = False

        # Stop at first category with failures
        if any(
            v.status == "failed"
            for v in state.verifications.values()
            if v.category == category
        ):
            break

    return progress


def do_fix(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Triage failures and fix them with the Fixer agent.

    Returns True only if net passing count increased (not just any_fixed).
    Rolls back fixes that cause net regressions.
    """
    from ..claude import AgentRole, load_prompt
    from ..state import FailureRecord
    from .execute import run_tests_parallel, _resolve_script_path
    from .research import get_research_context

    failing = {
        v.verification_id: v
        for v in state.verifications.values()
        if v.status == "failed" and v.attempts < state.process_monitor.current_strategy.get(
            "max_fix_attempts", config.max_fix_attempts,
        )
    }
    if not failing:
        return False

    # Track net progress across entire do_fix call
    entry_passing = sum(
        1 for v in state.verifications.values() if v.status == "passed"
    )

    # Step 1: Triage (Haiku) for multiple failures
    # Capture just the IDs and errors — objects may go stale after session.send()
    failing_ids = list(failing.keys())
    if len(failing) > 1:
        triage_session = claude.session(AgentRole.CLASSIFIER)
        error_summary = "\n".join(
            f"- {v.verification_id}: {v.last_error[:200] if v.last_error else 'unknown'}"
            for v in failing.values()
        )
        triage_session.send(load_prompt("triage", FAILURES=error_summary))
        root_causes = state.agent_results.get("triage") or []
    else:
        test = next(iter(failing.values()))
        root_causes = [{
            "cause": test.last_error or "Unknown",
            "affected_tests": [test.verification_id],
            "priority": 1,
        }]

    # Step 2: Fix each root cause (Sonnet) with rollback protection
    project_dir = str(config.effective_project_dir)
    for rc in sorted(root_causes, key=lambda x: x.get("priority", 99) if isinstance(x, dict) else 99):
        if not isinstance(rc, dict):
            continue

        # Skip root causes that have been rolled back too many times
        cause_sig = _cause_signature(rc)
        if cause_sig in state.fix_rollback_causes:
            print(f"  Skipping rolled-back root cause: {cause_sig[:80]}")
            continue

        # Normalise: triage agents may use "affected_tests" or "verification_id"
        affected_ids = rc.get("affected_tests") or (
            [rc["verification_id"]] if "verification_id" in rc else failing_ids
        )
        # Fetch fresh references from state (may have been replaced by _sync_state)
        affected = [
            state.verifications[tid]
            for tid in affected_ids
            if tid in state.verifications
        ]
        if not affected:
            continue

        # --- Snapshot before fix ---
        snapshot = _snapshot_verifications(state)
        pre_fix_passing = sum(
            1 for s in snapshot["statuses"].values() if s == "passed"
        )

        # Build fix prompt and run fixer
        session = claude.session(AgentRole.FIXER)
        failing_details = []
        for v in affected:
            script_content = ""
            if v.script_path:
                try:
                    resolved_path = _resolve_script_path(v.script_path)
                    if resolved_path.exists():
                        script_content = resolved_path.read_text(encoding="utf-8")
                except Exception:
                    pass
            failing_details.append({
                "verification_id": v.verification_id,
                "last_error": v.last_error,
                "attempt_history": v.attempt_history,
                "script": script_content,
            })
        prompt = load_prompt("fix",
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            ROOT_CAUSE=json.dumps({
                "cause": rc.get("cause", "Unknown"),
                "affected_tests": affected_ids,
                "fix_suggestion": rc.get("fix_suggestion", rc.get("fix", "")),
            }),
            FAILING_VERIFICATIONS=json.dumps(failing_details, indent=2),
            RESEARCH_CONTEXT=get_research_context(state),
        )
        session.send(prompt)

        # Re-fetch verification objects — _sync_state replaced state.verifications
        # after session.send(), so old `affected` refs are stale.
        affected = [
            state.verifications[tid]
            for tid in affected_ids
            if tid in state.verifications
        ]

        # Re-run targeted tests to check if fix worked
        for v in affected:
            v.attempts += 1
            results = run_tests_parallel([v], config.regression_timeout)
            exit_code, stdout, stderr = results.get(
                v.verification_id, (1, "", ""),
            )
            if exit_code == 0:
                v.status = "passed"
                state.add_regression_pass(v.verification_id)
            else:
                v.failures.append(FailureRecord(
                    timestamp=datetime.now().isoformat(),
                    attempt=v.attempts,
                    exit_code=exit_code,
                    stdout=(stdout or "")[:2000],
                    stderr=(stderr or "")[:2000],
                    fix_applied=f"Fix for root cause: {rc.get('cause', 'Unknown')[:200]}",
                ))

        # --- Full suite re-run to detect cross-test breakage ---
        all_runnable = [
            v for v in state.verifications.values()
            if v.script_path
        ]
        if all_runnable:
            full_results = run_tests_parallel(all_runnable, config.regression_timeout)
            for v_id, (exit_code, stdout, stderr) in full_results.items():
                v = state.verifications.get(v_id)
                if not v:
                    continue
                if exit_code == 0:
                    v.status = "passed"
                    state.add_regression_pass(v_id)
                else:
                    v.status = "failed"
                    state.regression_baseline.discard(v_id)

        # --- Net improvement check ---
        post_fix_passing = sum(
            1 for v in state.verifications.values() if v.status == "passed"
        )
        net_change = post_fix_passing - pre_fix_passing

        if net_change < 0:
            # Net negative — rollback code changes and restore verification states
            print(f"  Rollback: fix caused net {net_change} change ({pre_fix_passing}→{post_fix_passing} passing)")
            subprocess.run(
                ["git", "checkout", "--", project_dir],
                check=False, capture_output=True,
            )
            subprocess.run(
                ["git", "clean", "-fd", "--", project_dir],
                check=False, capture_output=True,
            )
            _restore_verifications(state, snapshot)
            state.fix_rollback_causes.add(cause_sig)
            state.research_attempted_for_current_failures = False
        else:
            if net_change > 0:
                print(f"  Fix improved: {pre_fix_passing}→{post_fix_passing} passing (+{net_change})")

    # Return True only if net passing count increased
    exit_passing = sum(
        1 for v in state.verifications.values() if v.status == "passed"
    )
    return exit_passing > entry_passing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_requires(script: Path) -> list[str]:
    """Parse '# requires: category1, category2' from verification script header."""
    try:
        first_line = script.read_text(encoding="utf-8").split("\n", 1)[0]
    except Exception:
        return []
    if first_line.startswith("# requires:"):
        return [r.strip() for r in first_line.split(":", 1)[1].split(",")]
    return []


def _category_deps_met(category: str, state: LoopState) -> bool:
    """Check if a verification category's dependencies are met."""
    for v in state.verifications.values():
        if v.category == category:
            for req in v.requires:
                req_tests = [
                    t for t in state.verifications.values()
                    if t.category == req
                ]
                if not all(t.status == "passed" for t in req_tests):
                    return False
    return True


def _snapshot_verifications(state: LoopState) -> dict:
    """Capture verification statuses and regression baseline before a fix attempt."""
    return {
        "statuses": {vid: v.status for vid, v in state.verifications.items()},
        "regression_baseline": set(state.regression_baseline),
    }


def _restore_verifications(state: LoopState, snapshot: dict) -> None:
    """Restore verification statuses and regression baseline from a snapshot."""
    for vid, status in snapshot["statuses"].items():
        if vid in state.verifications:
            state.verifications[vid].status = status
    state.regression_baseline = snapshot["regression_baseline"]


def _cause_signature(rc: dict) -> str:
    """Generate a short signature for a root cause to track rollbacks."""
    cause = rc.get("cause", "Unknown") or "Unknown"
    # Truncate to first 120 chars for dedup — same root cause may have different details
    return cause[:120].strip()
