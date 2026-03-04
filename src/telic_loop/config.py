"""LoopConfig: loop behavior and model routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LoopConfig:
    """How the loop behaves. The human provides this (or accepts defaults)."""

    sprint: str
    sprint_dir: Path
    project_dir: Path | None = None  # None = same as sprint_dir

    # Safety valves
    max_iterations: int = 200
    max_fix_attempts: int = 3
    token_budget: int = 0  # 0 = unlimited
    max_exit_gate_attempts: int = 3
    max_crash_restarts: int = 3
    max_phase_crashes: int = 3        # Consecutive crashes before phase skip/halt
    retry_backoff_base: float = 1.0   # Exponential backoff base (seconds)
    retry_backoff_cap: float = 30.0   # Max backoff per retry (seconds)

    # Plan review
    max_plan_review_attempts: int = 2

    # Model routing
    model_reasoning: str = "claude-opus-4-6"
    model_execution: str = "claude-sonnet-4-5-20250929"

    # Per-role SDK timeouts (seconds)
    sdk_timeout_reasoning: int = 600   # 10 min — planning, review, eval
    sdk_timeout_building: int = 1800   # 30 min — code generation + tool calls

    # Browser evaluation (Critical Evaluator)
    browser_eval_headless: bool = False
    browser_eval_viewport: str = "1280x720"

    # Task granularity enforcement
    max_task_description_chars: int = 600
    max_files_per_task: int = 5

    # Post-delivery documentation
    generate_docs: bool = True

    def __post_init__(self) -> None:
        if self.max_iterations < 1:
            raise ValueError(f"max_iterations must be >= 1, got {self.max_iterations}")
        if self.max_fix_attempts < 1:
            raise ValueError(f"max_fix_attempts must be >= 1, got {self.max_fix_attempts}")
        if self.token_budget < 0:
            raise ValueError(f"token_budget must be >= 0, got {self.token_budget}")
        if self.max_task_description_chars < 100:
            raise ValueError(f"max_task_description_chars must be >= 100, got {self.max_task_description_chars}")
        if self.max_files_per_task < 1:
            raise ValueError(f"max_files_per_task must be >= 1, got {self.max_files_per_task}")
        if self.retry_backoff_base < 0:
            raise ValueError(f"retry_backoff_base must be >= 0, got {self.retry_backoff_base}")
        self.sprint_dir = Path(self.sprint_dir)

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
