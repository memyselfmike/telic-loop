"""Quality control: generate verifications, run tests, triage, fix (QC agent)."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def do_generate_qc(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """Generate QC verification scripts from the plan and context."""
    from ..claude import AgentRole, load_prompt
    from ..state import VerificationState

    session = claude.session(AgentRole.QC)
    prompt = load_prompt("generate_verifications",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PLAN=config.plan_file.read_text(encoding="utf-8") if config.plan_file.exists() else "",
        PRD=config.prd_file.read_text(encoding="utf-8") if config.prd_file.exists() else "",
        VISION=config.vision_file.read_text(encoding="utf-8") if config.vision_file.exists() else "",
        VERIFICATION_STRATEGY=json.dumps(state.context.verification_strategy, indent=2),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
    )
    session.send(prompt)

    # Discover generated scripts
    verify_dir = config.sprint_dir / ".loop" / "verifications"
    if verify_dir.exists():
        for category_dir in sorted(verify_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            if category not in state.verification_categories:
                state.verification_categories.append(category)
            for script in sorted(category_dir.iterdir()):
                if script.suffix not in (".sh", ".py"):
                    continue
                v_id = f"{category}/{script.stem}"
                if v_id not in state.verifications:
                    if sys.platform != "win32":
                        script.chmod(0o755)
                    state.verifications[v_id] = VerificationState(
                        verification_id=v_id,
                        category=category,
                        script_path=str(script),
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
        script_path=str(script_path),
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
                    stdout=stdout[:2000],
                    stderr=stderr[:2000],
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
    """Triage failures and fix them with the Fixer agent."""
    from ..claude import AgentRole, load_prompt
    from ..state import FailureRecord
    from .execute import run_regression, run_tests_parallel
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

    # Step 1: Triage (Haiku) for multiple failures
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

    # Step 2: Fix each root cause (Sonnet)
    any_fixed = False
    for rc in sorted(root_causes, key=lambda x: x.get("priority", 99)):
        session = claude.session(AgentRole.FIXER)
        affected = [failing[tid] for tid in rc["affected_tests"] if tid in failing]
        if not affected:
            continue

        failing_details = [
            {
                "verification_id": v.verification_id,
                "last_error": v.last_error,
                "attempt_history": v.attempt_history,
                "script": Path(v.script_path).read_text(encoding="utf-8") if v.script_path else "",
            }
            for v in affected
        ]
        prompt = load_prompt("fix",
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            ROOT_CAUSE=json.dumps({
                "cause": rc["cause"],
                "affected_tests": rc["affected_tests"],
                "fix_suggestion": rc.get("fix_suggestion", ""),
            }),
            FAILING_VERIFICATIONS=json.dumps(failing_details, indent=2),
            RESEARCH_CONTEXT=get_research_context(state),
        )
        session.send(prompt)

        # Verify fix by re-running affected tests
        for v in affected:
            v.attempts += 1
            results = run_tests_parallel([v], config.regression_timeout)
            exit_code, stdout, stderr = results.get(
                v.verification_id, (1, "", ""),
            )
            if exit_code == 0:
                v.status = "passed"
                state.add_regression_pass(v.verification_id)
                any_fixed = True
            else:
                v.failures.append(FailureRecord(
                    timestamp=datetime.now().isoformat(),
                    attempt=v.attempts,
                    exit_code=exit_code,
                    stdout=stdout[:2000],
                    stderr=stderr[:2000],
                    fix_applied=f"Fix for root cause: {rc['cause'][:200]}",
                ))

        # Check for regressions after fix
        if state.regression_baseline:
            regressions = run_regression(config, state)
            if regressions:
                print(f"  Fix caused {len(regressions)} regressions")

    return any_fixed


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
