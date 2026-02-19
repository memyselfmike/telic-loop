"""LoopState, TaskState, VerificationState, VRCSnapshot and related dataclasses."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Leaf dataclasses (no forward refs)
# ---------------------------------------------------------------------------

@dataclass
class FailureRecord:
    timestamp: str
    attempt: int
    exit_code: int
    stdout: str
    stderr: str
    fix_applied: str | None = None
    files_changed: list[str] = field(default_factory=list)


@dataclass
class VRCSnapshot:
    """A single Vision Reality Check result."""
    iteration: int
    timestamp: str
    deliverables_total: int
    deliverables_verified: int
    deliverables_blocked: int
    value_score: float  # 0.0 – 1.0
    gaps: list[dict] = field(default_factory=list)
    recommendation: str = "CONTINUE"  # CONTINUE | COURSE_CORRECT | DESCOPE | SHIP_READY
    summary: str = ""


@dataclass
class TaskState:
    """A single implementation task."""
    task_id: str
    status: Literal["pending", "in_progress", "done", "blocked", "descoped"] = "pending"
    source: str = ""  # plan | critical_eval | vrc | exit_gate | course_correction
    created_at: str = ""
    completed_at: str = ""
    blocked_reason: str = ""
    # Rich fields
    description: str = ""
    value: str = ""
    prd_section: str = ""
    acceptance: str = ""
    dependencies: list[str] = field(default_factory=list)
    phase: str = ""
    epic_id: str = ""
    files_expected: list[str] = field(default_factory=list)
    # Execution tracking
    retry_count: int = 0
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    completion_notes: str = ""
    health_checked: bool = False


@dataclass
class VerificationState:
    """Tracks a single verification (test, criteria check, integrity validation)."""
    verification_id: str
    category: str
    status: Literal["pending", "passed", "failed", "blocked"] = "pending"
    script_path: str | None = None
    attempts: int = 0
    failures: list[FailureRecord] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)

    @property
    def last_error(self) -> str | None:
        if not self.failures:
            return None
        f = self.failures[-1]
        return f"{f.stdout}\n{f.stderr}".strip()

    @property
    def attempt_history(self) -> str:
        lines: list[str] = []
        for f in self.failures:
            lines.append(f"--- Attempt {f.attempt} ---")
            if f.stderr:
                lines.append(f"Error: {f.stderr[:800]}")
            if f.stdout:
                lines.append(f"Output: {f.stdout[:400]}")
            if f.fix_applied:
                lines.append(f"Fix tried: {f.fix_applied}")
        return "\n".join(lines)


@dataclass
class Epic:
    """A deliverable value block within a multi_epic vision."""
    epic_id: str
    title: str
    value_statement: str
    deliverables: list[str] = field(default_factory=list)
    completion_criteria: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    detail_level: str = "sketch"  # full | moderate | sketch
    status: Literal["pending", "in_progress", "completed", "skipped"] = "pending"
    task_sketch: list[str] = field(default_factory=list)
    feedback_response: str = ""
    feedback_notes: str = ""


@dataclass
class CoherenceReport:
    """Result of a system-level coherence evaluation."""
    iteration: int
    mode: Literal["quick", "full"]
    timestamp: str
    dimensions: dict[str, dict] = field(default_factory=dict)
    overall: Literal["HEALTHY", "WARNING", "CRITICAL"] = "HEALTHY"
    top_findings: list[dict] = field(default_factory=list)


@dataclass
class RefinementRound:
    """One round of interactive refinement (vision or PRD)."""
    round_num: int
    timestamp: str
    analysis_result: dict = field(default_factory=dict)
    hard_issues: list[dict] = field(default_factory=list)
    soft_issues: list[dict] = field(default_factory=list)
    research_results: dict = field(default_factory=dict)
    human_action: str = ""
    human_notes: str = ""


@dataclass
class RefinementState:
    """Tracks interactive refinement session for resumability and audit trail."""
    target: str = ""  # vision | prd
    status: str = "not_started"
    current_round: int = 0
    rounds: list[RefinementRound] = field(default_factory=list)
    acknowledged_soft_issues: list[str] = field(default_factory=list)
    consensus_reason: str = ""


@dataclass
class PauseState:
    """Interactive Pause state."""
    reason: str
    instructions: str
    verification: str = ""
    requested_at: str = ""


@dataclass
class ProcessMonitorState:
    """Process Meta-Reasoning state."""
    value_velocity_ema: float = 0.0
    token_efficiency_ema: float = 0.0
    cusum_efficiency: float = 0.0
    churn_counts: dict[str, int] = field(default_factory=dict)
    error_hashes: dict[str, dict] = field(default_factory=dict)
    file_touches: dict[str, int] = field(default_factory=dict)
    file_line_counts: dict[str, int] = field(default_factory=dict)
    file_line_counts_prev: dict[str, int] = field(default_factory=dict)
    code_health_warnings: list[str] = field(default_factory=list)
    long_functions: dict[str, list[tuple[str, int]]] = field(default_factory=dict)
    duplicate_blocks: list[dict] = field(default_factory=list)
    missing_prd_files: list[str] = field(default_factory=list)
    test_source_ratio: float = 0.0
    todo_count: int = 0
    debug_artifact_count: int = 0
    status: str = "GREEN"
    last_strategy_change_iteration: int = 0
    current_strategy: dict = field(default_factory=lambda: {
        "test_approach": "pytest",
        "fix_approach": "targeted",
        "execution_order": "dependency",
        "max_fix_attempts": 5,
        "research_trigger": "after_3_failures",
        "scope_per_task": "full",
        "error_triage": "individual",
    })
    strategy_history: list[dict] = field(default_factory=list)


@dataclass
class GitCheckpoint:
    """A known-good git commit that the loop can roll back to."""
    commit_hash: str
    timestamp: str
    label: str
    tasks_completed: list[str] = field(default_factory=list)
    verifications_passing: list[str] = field(default_factory=list)
    value_score: float = 0.0


@dataclass
class GitState:
    """Git operations state."""
    branch_name: str = ""
    original_branch: str = ""
    had_stashed_changes: bool = False
    stash_ref: str = ""
    checkpoints: list[GitCheckpoint] = field(default_factory=list)
    last_commit_hash: str = ""
    rollbacks: list[dict] = field(default_factory=list)
    sensitive_patterns: list[str] = field(default_factory=lambda: [
        ".env", ".env.*", "*.pem", "*.key", "*secret*",
        "*credential*", "*password*", "*.p12", "*.pfx",
    ])
    protected_branches: list[str] = field(default_factory=lambda: [
        "main", "master", "develop", "production", "staging",
    ])

    @property
    def latest_checkpoint(self) -> GitCheckpoint | None:
        return self.checkpoints[-1] if self.checkpoints else None

    def checkpoint_for_task(self, task_id: str) -> GitCheckpoint | None:
        for cp in reversed(self.checkpoints):
            if task_id in cp.tasks_completed:
                return cp
        return None

    def best_rollback_target(self, failed_task_ids: list[str]) -> GitCheckpoint | None:
        for cp in reversed(self.checkpoints):
            if not any(tid in cp.tasks_completed for tid in failed_task_ids):
                return cp
        return None


@dataclass
class SprintContext:
    """Derived by Context Discovery — never human-provided."""
    deliverable_type: str = "unknown"
    project_type: str = "unknown"
    codebase_state: str = "greenfield"
    environment: dict = field(default_factory=dict)
    services: dict = field(default_factory=dict)
    verification_strategy: dict = field(default_factory=dict)
    value_proofs: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LoopState — the single source of truth
# ---------------------------------------------------------------------------

@dataclass
class LoopState:
    sprint: str
    phase: Literal["pre_loop", "value_loop"] = "pre_loop"
    iteration: int = 0

    # Pre-loop gates
    gates_passed: set[str] = field(default_factory=set)

    # Sprint context
    context: SprintContext = field(default_factory=SprintContext)

    # Task tracking
    tasks: dict[str, TaskState] = field(default_factory=dict)
    tasks_since_last_critical_eval: int = 0
    mid_loop_tasks_since_health_check: int = 0

    # Verification tracking
    verifications: dict[str, VerificationState] = field(default_factory=dict)
    verification_categories: list[str] = field(default_factory=list)

    # Regression baseline
    regression_baseline: set[str] = field(default_factory=set)

    # VRC history
    vrc_history: list[VRCSnapshot] = field(default_factory=list)

    # Progress tracking
    progress_log: list[dict] = field(default_factory=list)
    iterations_without_progress: int = 0

    # Interactive Pause
    pause: PauseState | None = None

    # Process Monitor
    process_monitor: ProcessMonitorState = field(default_factory=ProcessMonitorState)

    # Git operations
    git: GitState = field(default_factory=GitState)

    # Epic tracking
    vision_complexity: str = "single_run"
    epics: list[Epic] = field(default_factory=list)
    current_epic_index: int = 0

    # Coherence tracking
    coherence_history: list[CoherenceReport] = field(default_factory=list)
    tasks_since_last_coherence: int = 0
    coherence_critical_pending: bool = False

    # Pre-loop refinement tracking
    vision_refinement: RefinementState = field(
        default_factory=lambda: RefinementState(target="vision")
    )
    prd_refinement: RefinementState = field(
        default_factory=lambda: RefinementState(target="prd")
    )

    # Research tracking
    research_briefs: list[dict] = field(default_factory=list)
    research_attempted_for_current_failures: bool = False

    # Structured tool results
    agent_results: dict[str, Any] = field(default_factory=dict)

    # Exit gate
    exit_gate_attempts: int = 0

    # Task granularity limits (populated from config at loop start)
    max_task_description_chars: int = 600
    max_files_per_task: int = 5

    # Token tracking
    total_tokens_used: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    # ----- Properties -----

    @property
    def latest_vrc(self) -> VRCSnapshot | None:
        return self.vrc_history[-1] if self.vrc_history else None

    @property
    def value_delivered(self) -> bool:
        vrc = self.latest_vrc
        return vrc is not None and vrc.recommendation == "SHIP_READY"

    # ----- Methods -----

    def record_progress(
        self, action: str, result: str, made_progress: bool,
        input_tokens: int = 0, output_tokens: int = 0,
        duration_sec: float = 0.0,
    ) -> None:
        self.progress_log.append({
            "iteration": self.iteration,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_sec": duration_sec,
        })
        if made_progress:
            self.iterations_without_progress = 0
        else:
            self.iterations_without_progress += 1

    def is_stuck(self, config) -> bool:
        return self.iterations_without_progress >= config.max_no_progress

    def progress_log_count(self, action: str) -> list[dict]:
        return [e for e in self.progress_log if e.get("action") == action]

    def gate_passed(self, name: str) -> bool:
        return name in self.gates_passed

    def pass_gate(self, name: str) -> None:
        self.gates_passed.add(name)

    def add_task(self, task: TaskState) -> None:
        existing = self.tasks.get(task.task_id)
        if existing and existing.status in ("done", "in_progress"):
            # Don't overwrite completed or in-progress tasks
            return
        self.tasks[task.task_id] = task

    def add_regression_pass(self, vid: str) -> None:
        self.regression_baseline.add(vid)

    def invalidate_tests(self) -> None:
        self.verifications.clear()
        self.regression_baseline.clear()
        self.gates_passed.discard("verifications_generated")

    # ----- Persistence -----

    def save(self, path: Path) -> None:
        """Atomic state save: write to .tmp then rename."""
        data = asdict(self)
        # Convert sets to sorted lists for JSON
        data["gates_passed"] = sorted(data["gates_passed"])
        data["regression_baseline"] = sorted(data["regression_baseline"])

        def _serialize(obj: object) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Path):
                return str(obj)
            if isinstance(obj, set):
                return sorted(obj)
            raise TypeError(f"Cannot serialize {type(obj).__name__}: {obj!r}")

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(data, indent=2, default=_serialize))
        tmp_path.replace(path)  # atomic on POSIX; near-atomic on Windows NTFS

    @classmethod
    def load(cls, path: Path) -> LoopState:
        from dacite import Config, from_dict
        data = json.loads(path.read_text())
        # Normalize VRC gaps: agents sometimes report strings instead of dicts
        for vrc in data.get("vrc_history", []):
            gaps = vrc.get("gaps", [])
            if gaps and isinstance(gaps[0], str):
                vrc["gaps"] = [{"description": g, "severity": "degraded"} for g in gaps]
        # Normalize process_monitor.long_functions: JSON serializes tuples as lists
        pm = data.get("process_monitor", {})
        if "long_functions" in pm and isinstance(pm["long_functions"], dict):
            pm["long_functions"] = {
                k: [tuple(fn) for fn in v]
                for k, v in pm["long_functions"].items()
            }
        return from_dict(
            data_class=cls,
            data=data,
            config=Config(
                cast=[Literal, set, tuple],
                strict=False,
            ),
        )
