"""LoopConfig: loop behavior and model routing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoopConfig:
    """How the loop behaves. The human provides this (or accepts defaults)."""

    sprint: str
    sprint_dir: Path
    project_dir: Path | None = None  # None = same as sprint_dir

    # Safety valves
    max_loop_iterations: int = 200
    max_fix_attempts: int = 5
    max_no_progress: int = 10
    token_budget: int = 0  # 0 = unlimited

    # Model routing
    model_reasoning: str = "claude-opus-4-6"
    model_execution: str = "claude-sonnet-4-5-20250929"
    model_triage: str = "claude-haiku-4-5-20251001"

    # Verification
    generate_verifications_after: int = 1
    regression_after_every_task: bool = True
    regression_timeout: int = 120  # seconds

    # Critical evaluation
    critical_eval_interval: int = 3
    critical_eval_on_all_pass: bool = True

    # Browser evaluation (Critical Evaluator)
    browser_eval_headless: bool = False       # False = headed (dev), True = headless (CI)
    browser_eval_viewport: str = "1280x720"   # Playwright viewport size

    # Safety limits
    max_exit_gate_attempts: int = 3
    max_course_corrections: int = 5

    # Plan health
    plan_health_after_n_tasks: int = 5

    # Epic feedback
    epic_feedback_timeout_minutes: int = 30

    # Coherence evaluation
    coherence_quick_interval: int = 5
    coherence_full_at_epic_boundary: bool = True

    # Process Monitor
    process_monitor_min_iterations: int = 5
    process_monitor_cooldown: int = 5
    process_monitor_ema_alpha: float = 0.3
    pm_plateau_patience: int = 5
    pm_plateau_threshold: float = 0.1
    pm_efficiency_drop_pct: float = 50
    pm_churn_yellow: int = 2
    pm_churn_red: int = 3
    pm_error_recurrence: int = 3
    pm_category_cluster_pct: float = 60
    pm_budget_value_ratio: float = 2.0
    pm_file_hotspot_pct: float = 50

    # Code health enforcement
    code_health_monolith_threshold: int = 500   # lines — files at/above this get refactoring tasks
    code_health_max_file_lines: int = 400       # target max lines after refactoring
    code_health_enforce_at_exit: bool = True     # hard gate: block exit if monoliths remain
    code_health_max_function_lines: int = 50    # LONG_FUNCTION threshold
    code_health_duplicate_min_lines: int = 8    # DUPLICATE block minimum
    code_health_min_test_ratio: float = 0.5     # LOW_TEST_RATIO threshold
    code_health_max_todo_count: int = 5         # TODO_DEBT threshold
    code_health_max_duplicate_tasks: int = 5    # cap on DEDUP tasks created

    # Reliability
    max_task_retries: int = 3
    max_rollbacks_per_sprint: int = 3

    # Derived paths
    @property
    def effective_project_dir(self) -> Path:
        """Where application source code lives."""
        return self.project_dir if self.project_dir is not None else self.sprint_dir

    @property
    def vision_file(self) -> Path:
        return self.sprint_dir / "VISION.md"

    @property
    def prd_file(self) -> Path:
        return self.sprint_dir / "PRD.md"

    @property
    def state_file(self) -> Path:
        return self.sprint_dir / ".loop_state.json"

    @property
    def plan_file(self) -> Path:
        return self.sprint_dir / "IMPLEMENTATION_PLAN.md"

    @property
    def value_checklist(self) -> Path:
        return self.sprint_dir / "VALUE_CHECKLIST.md"
