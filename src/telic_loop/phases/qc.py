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
        PLAN=config.plan_file.read_text() if config.plan_file.exists() else "",
        PRD=config.prd_file.read_text() if config.prd_file.exists() else "",
        VISION=config.vision_file.read_text() if config.vision_file.exists() else "",
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

    state.pass_gate("verifications_generated")
    return bool(state.verifications)


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
        if v.status == "failed" and v.attempts < config.max_fix_attempts
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
                "script": Path(v.script_path).read_text() if v.script_path else "",
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
        first_line = script.read_text().split("\n", 1)[0]
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
