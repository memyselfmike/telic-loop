# Loop V3: Architecture Reference

**Date**: 2026-02-15
**Companion documents**: V3_PRD.md (requirements), V3_PHASE1_PLAN.md / V3_PHASE2_PLAN.md / V3_PHASE3_PLAN.md (implementation)
**Prerequisite reading**: V3_VISION.md

---

## How to Use This Document

This is the **structural specification** of Loop V3. It defines the data model, agent roles, tools, and decision logic that all phases share.

When building a specific phase, load:
1. **This document** — the "what exists"
2. **V3_PRD.md** — the "what it must do" with acceptance criteria
3. **One Phase Plan** — the "how to build this part"

---

## Core Principles

### 1. Value Over Function
"Working code" is not the goal. "User gets the promised outcome" is the goal. Tests passing is a signal, not success. The VRC (Vision Reality Check) is the only real measure.

### 2. Don't Start What You Can't Finish
All true external blockers must be resolved *before* entering the delivery loop. If the PRD asks for something impossible, push back and descope — don't waste 50 iterations discovering it.

### 3. Separate Agents, Right Model for Each
The builder never grades its own work. Three distinct agent roles:
- **Builder** (Sonnet) — executes tasks, writes code/content
- **QC Agent** (Sonnet/Haiku) — checks correctness: tests, linting, types, regression
- **Evaluator** (Opus) — uses the deliverable as a real user, judges experience quality

Opus for every decision requiring judgment: planning, critique, course correction, evaluation. Sonnet for volume work: building, fixing, QC generation. Haiku for classification: triage, quick VRC.

### 4. Regression Is an Immune System
After every change, verify nothing broke. This runs constantly, not at phase boundaries. It's cheap (subprocess, not LLM) and non-negotiable.

### 5. The Loop Decides, Not the Phases
The inner loop is decision-driven. Each iteration asks "what should I do next?" based on current state — not "what phase am I in?" The loop can go from testing back to planning if that's what the situation demands.

### 6. Technology Agnostic
The algorithm knows about visions, plans, tasks, and verification. It does not know about React, FastAPI, or Docker. All technology specifics are discovered automatically from the Vision, PRD, and codebase.

### 7. Structured State, Rendered Views
JSON is the single source of truth. Agents never edit markdown plan files — they communicate through structured tool calls (`report_task_complete`, `manage_task`, `report_vrc`). Human-readable reports are generated from state on demand. This eliminates the dual-source-of-truth problem that plagued V2.

---

## Two-Phase Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PRE-LOOP                              │
│                                                         │
│  Qualify the work. Ensure it's achievable.              │
│                                                         │
│  1. Validate inputs (VISION.md, PRD.md exist)           │
│  2. Vision Refinement (interactive)                     │
│     ┌─→ 5-pass analysis (Opus)                          │
│     │   PASS → proceed                                  │
│     │   Issues found:                                   │
│     │     Classify HARD/SOFT                             │
│     │     Research alternatives for HARD (Researcher)    │
│     │     Present to human with recommendations          │
│     │     Human revises VISION.md                        │
│     └── Re-analyze (loop until consensus)               │
│  2b. Complexity Classification — single_run | multi_epic│
│  2c. Epic Decomposition (if multi_epic) — value blocks  │
│  3. Context Discovery (Opus) — derive sprint context    │
│  4. PRD Refinement (interactive)                        │
│     ┌─→ Feasibility critique (Opus)                     │
│     │   APPROVE/AMEND/DESCOPE → proceed                 │
│     │   REJECT:                                         │
│     │     Research feasible alternatives (Researcher)    │
│     │     Present to human with proposals                │
│     │     Human revises PRD                              │
│     └── Re-critique (loop until achievable)             │
│  5. Plan Generation (Opus) — tasks → structured state   │
│  6. Quality Gates (Opus) — CRAAP, CLARITY, VALIDATE,    │
│     CONNECT, BREAK, PRUNE, TIDY                         │
│  7. Blocker Resolution — resolve or descope ALL         │
│  8. Preflight — environment ready                       │
│  9. Initial VRC — baseline value assessment             │
│                                                         │
│  EXIT CONDITION: Plan is achievable, blockers resolved  │
│  NOTE: Vision/PRD issues are resolved interactively     │
│        during refinement sessions — the loop negotiates │
│        with the human until consensus, never exits      │
│        silently. Human can always Ctrl+C to abort.      │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              THE VALUE LOOP (per epic)                   │
│                                                         │
│  For multi_epic visions, this runs once per epic.       │
│  For single_run visions, this runs once (same as V3     │
│  without epic decomposition).                           │
│                                                         │
│  while not value_delivered:                             │
│    decision = decide_next_action(state)                 │
│                                                         │
│    match decision:                                      │
│      EXECUTE         → execute task (Builder agent)     │
│      QC              → run QC checks (QC agent)         │
│      FIX             → fix failing checks               │
│      CRITICAL_EVAL   → evaluate experience (Evaluator)  │
│      COURSE_CORRECT  → re-plan, restructure, descope    │
│      RESEARCH        → search web/docs for external kb  │
│      INTERACTIVE_PAUSE → human action needed            │
│      SERVICE_FIX     → fix broken services              │
│      COHERENCE_EVAL  → system-level coherence check     │
│      EXIT_GATE       → fresh-context final verification │
│                                                         │
│    process_monitor(state)  ← execution pattern check    │
│    coherence_quick(state)  ← structural health check    │
│    vrc = run_vrc(state)                                 │
│    if vrc.value_delivered:                              │
│      exit_result = run_exit_gate(state)                 │
│      if exit_result.pass: break                        │
│      else: gaps → new tasks, continue                  │
│    if vrc.stuck: escalate_or_descope()                  │
│                                                         │
│  VRC runs EVERY iteration — it is the heartbeat.        │
│                                                         │
│  EXIT: Exit gate passes (value verified with fresh      │
│        context) → generate delivery report              │
│  SAFETY VALVE: max_iterations or budget limit           │
│                                                         │
│  There is NO post-loop. The exit gate is inside the     │
│  loop. If it finds gaps, they become tasks and the      │
│  loop continues. The only output after exit is the      │
│  delivery report — a summary of verified value.         │
└───────────────────────────┬─────────────────────────────┘
                            │ (multi_epic only)
                            ▼
┌─────────────────────────────────────────────────────────┐
│              EPIC FEEDBACK CHECKPOINT                    │
│                                                         │
│  After each epic's exit gate passes:                    │
│                                                         │
│  1. Generate curated epic summary (what was delivered,  │
│     how it maps to vision, what comes next)             │
│  2. Present to human: Proceed / Adjust / Stop           │
│  3. Timeout auto-proceed (configurable, default 30 min) │
│                                                         │
│  PROCEED → refine next epic, begin its value loop       │
│  ADJUST  → re-plan next epic with human's context       │
│  STOP    → ship completed epics, generate final report  │
│  TIMEOUT → auto-proceed (loop keeps delivering)         │
│                                                         │
│  For single_run visions: this step is skipped entirely. │
└─────────────────────────────────────────────────────────┘
```

---

## File Structure

```
loop-v3/
├── main.py                      # Entry point: pre-loop → value loop (with exit gate)
├── config.py                    # LoopConfig (loop behavior, model routing)
├── state.py                     # LoopState, TaskState, VerificationState, VRCSnapshot
├── discovery.py                 # Context Discovery — derive sprint context
├── decision.py                  # Decision engine: "what should I do next?"
├── claude.py                    # Anthropic SDK wrapper, model routing
├── git.py                       # Git operations: branching, commits, safety, rollback
├── tools.py                     # Tool implementations + structured output handlers
├── render.py                    # Generate markdown artifacts from structured state
├── phases/
│   ├── __init__.py
│   ├── preloop.py               # Discovery, PRD critique, plan gen, quality gates, preflight
│   ├── execute.py               # Multi-turn task execution (Builder agent)
│   ├── qc.py                    # Quality control: tests, linting, regression (QC agent)
│   ├── critical_eval.py         # Critical evaluation (Evaluator agent)
│   ├── vrc.py                   # Vision Reality Check (the heartbeat)
│   ├── course_correct.py        # Re-planning, descoping, restructuring
│   ├── plan_health.py           # Mid-loop plan quality validation (Layer 2)
│   ├── process_monitor.py       # Execution pattern monitoring + strategy reasoning
│   ├── research.py              # External research: web search, synthesis
│   ├── pause.py                 # Interactive Pause: human action needed
│   ├── coherence.py             # System coherence evaluation (quick + full)
│   ├── epic.py                  # Epic decomposition + feedback checkpoint
│   └── exit_gate.py             # Fresh-context exit verification (inside the loop)
├── prompts/                     # Reasoning templates
│   ├── system.md                # Base system prompt
│   ├── vision_validate.md       # 5-pass Vision challenge
│   ├── epic_decompose.md        # Break complex vision into deliverable epics
│   ├── epic_feedback.md         # Generate curated epic summary for human
│   ├── discover_context.md      # "What is this project? What does it need?"
│   ├── prd_critique.md          # "Is this PRD achievable?"
│   ├── plan.md                  # Plan generation
│   ├── craap.md                 # CRAAP quality review
│   ├── clarity.md               # CLARITY ambiguity elimination
│   ├── validate.md              # VALIDATE completeness check
│   ├── connect.md               # CONNECT integration review
│   ├── break.md                 # BREAK adversarial pre-mortem
│   ├── prune.md                 # PRUNE simplification without compromise
│   ├── tidy.md                  # TIDY-FIRST codebase prep
│   ├── verify_blockers.md       # Blocker reclassification
│   ├── preflight.md             # Environment verification
│   ├── vrc.md                   # Vision Reality Check
│   ├── execute.md               # Task execution (Builder agent)
│   ├── generate_verifications.md # QC script generation
│   ├── critical_eval.md         # Critical evaluation (be the user)
│   ├── triage.md                # Failure root cause grouping
│   ├── fix.md                   # Fix agent with error context
│   ├── course_correct.md        # Re-planning / descoping
│   ├── plan_health_check.md     # Mid-loop quality sweep
│   ├── process_monitor.md       # Strategy Reasoner prompt
│   ├── coherence_eval.md        # System coherence evaluation (7 dimensions)
│   ├── research.md              # External research
│   ├── interactive_pause.md     # Human action instructions
│   └── exit_gate.md             # Fresh-context final verification
```

---

## Data Model

### LoopConfig (human-provided, minimal)

```python
@dataclass
class LoopConfig:
    """How the loop behaves. The human provides this (or accepts defaults)."""
    sprint: str
    sprint_dir: Path

    # Safety valves
    max_loop_iterations: int = 200     # hard ceiling
    max_fix_attempts: int = 5          # per root cause
    max_no_progress: int = 10          # iterations without progress → escalate
    token_budget: int = 0              # 0 = unlimited, else max total tokens

    # Model routing (the key architectural decision)
    model_reasoning: str = "claude-opus-4-6"
    model_execution: str = "claude-sonnet-4-5-20250929"
    model_triage: str = "claude-haiku-4-5-20251001"

    # Verification
    generate_verifications_after: int = 1  # generate verifications after N tasks complete
    regression_after_every_task: bool = True
    regression_timeout: int = 120          # seconds

    # Critical evaluation
    critical_eval_interval: int = 3
    critical_eval_on_all_pass: bool = True

    # Safety limits
    max_exit_gate_attempts: int = 3
    max_course_corrections: int = 5

    # Plan health (mid-loop quality validation)
    plan_health_after_n_tasks: int = 5

    # Epic feedback (multi_epic visions only)
    epic_feedback_timeout_minutes: int = 30  # 0 = wait forever, else auto-proceed after N min

    # Coherence evaluation (system-level emergent property detection)
    coherence_quick_interval: int = 5        # quick check every N tasks
    coherence_full_at_epic_boundary: bool = True  # full eval at epic boundaries + pre-exit-gate

    # Process Monitor (execution pattern degradation detection)
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

    # Reliability
    max_task_retries: int = 3

    # Derived paths
    @property
    def vision_file(self) -> Path: return self.sprint_dir / "VISION.md"
    @property
    def prd_file(self) -> Path: return self.sprint_dir / "PRD.md"
    @property
    def state_file(self) -> Path: return self.sprint_dir / ".loop_state.json"
    @property
    def plan_file(self) -> Path:
        """Human-readable plan — rendered from state, not a source of truth."""
        return self.sprint_dir / "IMPLEMENTATION_PLAN.md"
    @property
    def value_checklist(self) -> Path:
        """Human-readable checklist — rendered from state, not a source of truth."""
        return self.sprint_dir / "VALUE_CHECKLIST.md"
```

### SprintContext (discovered by pre-loop, never human-provided)

```python
@dataclass
class SprintContext:
    """
    What the loop is working on. Derived by Context Discovery (Opus),
    not manually configured. The loop examines Vision + PRD + codebase
    and figures out what it needs.
    """
    deliverable_type: str = "unknown"   # "software", "document", "data", "config", "hybrid"
    project_type: str = "unknown"       # "web_app", "cli", "api", "library", "report", etc.
    codebase_state: str = "greenfield"  # "greenfield", "brownfield", "non_code"
    environment: dict = field(default_factory=dict)
    services: dict = field(default_factory=dict)
    verification_strategy: dict = field(default_factory=dict)
    value_proofs: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
```

**Example — web app sprint:**
```python
SprintContext(
    deliverable_type="software", project_type="web_app", codebase_state="brownfield",
    environment={"tools_found": ["uv", "node"], "env_vars_found": ["DATABASE_URL"]},
    services={"postgres": {"port": 5432, "health_type": "tcp"},
              "backend": {"port": 8000, "health_url": "http://localhost:8000/health"}},
    verification_strategy={"test_frameworks": ["pytest:backend/tests"], "holistic_type": "browser"},
    value_proofs=["User can log in via Google OAuth", "User can send a chat message"],
)
```

**Example — document sprint:**
```python
SprintContext(
    deliverable_type="document", project_type="report", codebase_state="non_code",
    environment={"tools_found": ["python"]}, services={},
    verification_strategy={"holistic_type": "document_review", "criteria_source": "PRD"},
    value_proofs=["Report addresses all 5 research questions", "Each finding includes data"],
)
```

### State Dataclasses

```python
@dataclass
class VRCSnapshot:
    """A single Vision Reality Check result."""
    iteration: int
    timestamp: str
    deliverables_total: int
    deliverables_verified: int
    deliverables_blocked: int
    value_score: float              # 0.0 - 1.0
    gaps: list[dict]                # [{id, description, severity, suggested_task}]
    recommendation: str             # CONTINUE, COURSE_CORRECT, DESCOPE, SHIP_READY
    summary: str

@dataclass
class TaskState:
    """A single implementation task. Tasks live in structured state, rendered on demand."""
    task_id: str
    status: Literal["pending", "in_progress", "done", "blocked", "descoped"] = "pending"
    source: str = ""                # "plan", "critical_eval", "vrc", "exit_gate", "course_correction"
    created_at: str = ""
    completed_at: str = ""
    blocked_reason: str = ""
    # Rich fields (replaces IMPLEMENTATION_PLAN.md prose)
    description: str = ""
    value: str = ""
    prd_section: str = ""           # traceability: "§2.1"
    acceptance: str = ""
    dependencies: list[str] = field(default_factory=list)
    phase: str = ""                 # "foundation", "core", "integration", etc.
    epic_id: str = ""               # which epic this task belongs to (empty = all epics / single_run)
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
    category: str                   # determined by discovery, not hardcoded tiers
    status: Literal["pending", "passed", "failed", "blocked"] = "pending"
    script_path: str | None = None
    attempts: int = 0
    failures: list[FailureRecord] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)

    @property
    def last_error(self) -> str | None:
        return f"{self.failures[-1].stdout}\n{self.failures[-1].stderr}".strip() if self.failures else None

    @property
    def attempt_history(self) -> str:
        """Full history for fix agent — what was tried and what happened."""
        lines = []
        for f in self.failures:
            lines.append(f"--- Attempt {f.attempt} ---")
            if f.stderr: lines.append(f"Error: {f.stderr[:800]}")
            if f.stdout: lines.append(f"Output: {f.stdout[:400]}")
            if f.fix_applied: lines.append(f"Fix tried: {f.fix_applied}")
        return "\n".join(lines)

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
class Epic:
    """A deliverable value block within a multi_epic vision."""
    epic_id: str
    title: str
    value_statement: str          # "User can X" — independently demonstrable
    deliverables: list[str]
    completion_criteria: list[str]
    depends_on: list[str]         # previous epic IDs
    detail_level: str = "sketch"  # "full" for current/next epic, "sketch" for later
    status: Literal["pending", "in_progress", "completed", "skipped"] = "pending"
    task_sketch: list[str] = field(default_factory=list)
    feedback_response: str = ""   # "proceed" | "adjust" | "stop" | "timeout"
    feedback_notes: str = ""      # human's adjustment notes (if "adjust")

@dataclass
class CoherenceReport:
    """Result of a system-level coherence evaluation."""
    iteration: int
    mode: Literal["quick", "full"]
    timestamp: str
    dimensions: dict[str, dict]   # dimension_name → {status, findings, trend}
    overall: Literal["HEALTHY", "WARNING", "CRITICAL"]
    top_findings: list[dict] = field(default_factory=list)  # {dimension, severity, description, affected_files, suggested_action, leverage_level}

@dataclass
class RefinementRound:
    """One round of interactive refinement (vision or PRD)."""
    round_num: int
    timestamp: str
    analysis_result: dict           # full validation/critique result (preserved, not overwritten)
    hard_issues: list[dict]         # issues classified as HARD this round
    soft_issues: list[dict]         # issues classified as SOFT this round
    research_results: dict = field(default_factory=dict)  # issue_id → research findings
    human_action: str = ""          # "revised" | "acknowledged" | "" (pending)
    human_notes: str = ""           # any context from the human

@dataclass
class RefinementState:
    """
    Tracks interactive refinement session for resumability and audit trail.
    Both vision and PRD refinement use this structure.

    On crash: the loop checks status and round history to resume where it left off
    instead of restarting from scratch (avoiding re-running expensive Opus calls).
    """
    target: str = ""                # "vision" | "prd"
    status: str = "not_started"     # "not_started" | "analyzing" | "researching" | "awaiting_input" | "consensus"
    current_round: int = 0
    rounds: list[RefinementRound] = field(default_factory=list)
    acknowledged_soft_issues: list[str] = field(default_factory=list)  # issue IDs human accepted
    consensus_reason: str = ""      # "pass" | "acknowledged" | why we reached consensus

@dataclass
class PauseState:
    """Interactive Pause state. Exists only when the loop is paused for human action."""
    reason: str
    instructions: str
    verification: str = ""
    requested_at: str = ""

@dataclass
class ProcessMonitorState:
    """
    Process Meta-Reasoning state. Tracks execution metrics and triggers Strategy Reasoner.
    Distinct from Plan Health Check (task DEFINITIONS) and Course Correction (PLAN changes).
    Process Monitor changes the STRATEGY (how the loop works).
    """
    value_velocity_ema: float = 0.0
    token_efficiency_ema: float = 0.0
    cusum_efficiency: float = 0.0
    churn_counts: dict[str, int] = field(default_factory=dict)   # task_id → fail-fix-fail count
    error_hashes: dict[str, dict] = field(default_factory=dict)  # hash → {count, tasks}
    file_touches: dict[str, int] = field(default_factory=dict)   # filepath → touch count
    status: str = "GREEN"                                         # GREEN | YELLOW | RED
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
    label: str                      # "task:{task_id}", "qc_pass", "pre_loop_complete", "epic:{epic_id}"
    tasks_completed: list[str]      # task IDs completed at this point
    verifications_passing: list[str] # verification IDs passing at this point
    value_score: float              # VRC value score at this point (0.0 if pre-VRC)

@dataclass
class GitState:
    """
    Git operations state. Tracks branch, commits, checkpoints, and rollback history.

    The loop uses git as a safety net:
    - Feature branch created at sprint start (never works on protected branches)
    - Atomic commit after each task completion
    - Checkpoints recorded after each QC pass (known-good states)
    - Rollback to checkpoint available during course correction
    """
    branch_name: str = ""                   # e.g. "telic-loop/sprint-name-20260216-143022"
    original_branch: str = ""               # branch we started from (to return to)
    had_stashed_changes: bool = False        # did we stash uncommitted work?
    stash_ref: str = ""                     # git stash reference if stashed

    # Checkpoint tracking
    checkpoints: list[GitCheckpoint] = field(default_factory=list)
    last_commit_hash: str = ""              # most recent commit by the loop

    # Rollback tracking
    rollbacks: list[dict] = field(default_factory=list)  # [{from_hash, to_hash, reason, iteration, tasks_reverted}]

    # Safety
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
        """Find the most recent checkpoint where this task was completed."""
        for cp in reversed(self.checkpoints):
            if task_id in cp.tasks_completed:
                return cp
        return None

    def best_rollback_target(self, failed_task_ids: list[str]) -> GitCheckpoint | None:
        """Find the best checkpoint to roll back to — the most recent one
        that predates ALL of the failed tasks."""
        for cp in reversed(self.checkpoints):
            if not any(tid in cp.tasks_completed for tid in failed_task_ids):
                return cp
        return None
```

### LoopState (the single source of truth)

```python
@dataclass
class LoopState:
    sprint: str
    phase: Literal["pre_loop", "value_loop"] = "pre_loop"
    iteration: int = 0

    # Pre-loop gates
    gates_passed: set[str] = field(default_factory=set)

    # Sprint context (derived by Context Discovery)
    context: SprintContext = field(default_factory=SprintContext)

    # Task tracking
    tasks: dict[str, TaskState] = field(default_factory=dict)
    tasks_since_last_critical_eval: int = 0
    mid_loop_tasks_since_health_check: int = 0

    # Verification tracking (QC)
    verifications: dict[str, VerificationState] = field(default_factory=dict)
    verification_categories: list[str] = field(default_factory=list)

    # Regression baseline
    regression_baseline: set[str] = field(default_factory=set)

    # VRC history
    vrc_history: list[VRCSnapshot] = field(default_factory=list)

    # Progress tracking
    progress_log: list[dict] = field(default_factory=list)
    iterations_without_progress: int = 0

    # Interactive Pause (None = not paused)
    pause: PauseState | None = None

    # Process Monitor
    process_monitor: ProcessMonitorState = field(default_factory=ProcessMonitorState)

    # Git operations
    git: GitState = field(default_factory=GitState)

    # Epic tracking (multi_epic visions only; empty for single_run)
    vision_complexity: str = "single_run"   # "single_run" | "multi_epic"
    epics: list[Epic] = field(default_factory=list)
    current_epic_index: int = 0

    # Coherence tracking
    coherence_history: list[CoherenceReport] = field(default_factory=list)
    tasks_since_last_coherence: int = 0
    coherence_critical_pending: bool = False

    # Pre-loop refinement tracking (interactive sessions — resumable on crash)
    vision_refinement: RefinementState = field(default_factory=lambda: RefinementState(target="vision"))
    prd_refinement: RefinementState = field(default_factory=lambda: RefinementState(target="prd"))

    # Research tracking
    research_briefs: list[dict] = field(default_factory=list)
    research_attempted_for_current_failures: bool = False

    # Structured tool results (last report per agent type)
    agent_results: dict[str, Any] = field(default_factory=dict)

    # Exit gate
    exit_gate_attempts: int = 0

    # Token tracking
    total_tokens_used: int = 0

    # Key properties and methods (implementations in Phase 1 Plan)
    @property
    def latest_vrc(self) -> VRCSnapshot | None: ...
    @property
    def value_delivered(self) -> bool: ...
    def is_stuck(self, config: LoopConfig) -> bool: ...
    def record_progress(self, action: str, result: str, made_progress: bool): ...
    def gate_passed(self, gate_name: str) -> bool: ...
    def pass_gate(self, gate_name: str): ...
    def invalidate_tests(self): ...
    def add_task(self, task: TaskState): ...
    def add_regression_pass(self, verification_id: str): ...
    def save(self, path: Path): ...
    @classmethod
    def load(cls, path: Path) -> "LoopState": ...
```

**Note**: `LoopState.load()` uses `dacite.from_dict()` for safe nested dataclass reconstruction. See Phase 1 Plan §12 for the full implementation.

---

## Claude Wrapper

### Agent Roles (model routing)

```python
class AgentRole(Enum):
    """
    (model_config_attr, max_turns, thinking_effort, max_tokens)

    thinking_effort controls adaptive thinking (Opus 4.6+):
      "max"  → deep reasoning (planning, critique, course correction)
      "high" → strong reasoning (evaluation, research)
      None   → thinking disabled (Sonnet/Haiku execution roles)

    If max_tokens > 21333, session MUST use streaming.
    """
    REASONER   = ("model_reasoning",  40,  "max",    32768)
    EVALUATOR  = ("model_reasoning",  40,  "high",   32768)
    RESEARCHER = ("model_reasoning",  30,  "high",   16384)
    BUILDER    = ("model_execution",  60,  None,     16384)
    FIXER      = ("model_execution",  25,  None,     16384)
    QC         = ("model_execution",  30,  None,     16384)
    CLASSIFIER = ("model_triage",      5,  None,      4096)
```

### Claude Class

```python
STREAMING_THRESHOLD = 21333  # API requires streaming above this

class Claude:
    """Factory for creating sessions with model routing."""

    def __init__(self, config: LoopConfig, state: LoopState):
        self.config = config
        self.client = anthropic.Anthropic()  # auto-detects auth from environment
        self.beta_headers = ["web-fetch-2025-09-10"]
        self.state = state

    def session(self, role: AgentRole, system_extra: str = "") -> ClaudeSession:
        """Create a session. Model, turns, thinking, tokens derived from role."""
        model_attr, max_turns, thinking_effort, max_tokens = role.value
        system = load_prompt("system") + ("\n" + system_extra if system_extra else "")
        tools = get_tools_for_role(role)
        has_provider_tools = any(t.get("type", "").startswith("web_fetch") for t in tools)
        return ClaudeSession(
            client=self.client,
            model=getattr(self.config, model_attr),
            system=system,
            max_turns=max_turns,
            thinking_effort=thinking_effort,
            max_tokens=max_tokens,
            tools=tools,
            state=self.state,
            betas=self.beta_headers if has_provider_tools else None,
        )
```

### ClaudeSession

Multi-turn conversation with tool execution. Key behaviors:
- **Adaptive thinking**: When `thinking_effort` is set, passes `thinking={"type": "adaptive"}` + `output_config={"effort": thinking_effort}` to the API
- **Streaming**: Automatically enabled when `max_tokens > STREAMING_THRESHOLD` (21333)
- **Beta namespace**: When `betas` is set, uses `client.beta.messages` instead of `client.messages`
- **Provider tools**: `web_search` and `web_fetch` are server-side — results appear inline in `response.content`, NOT routed through `execute_tool()`
- **pause_turn**: When `response.stop_reason == "pause_turn"`, re-send conversation as-is (server-side tool loop hit its limit)
- **Token tracking**: Accumulates into `self.state.total_tokens_used` for budget tracking
- **task_source**: Provenance label for tasks created via `manage_task` — set by orchestrator, not agent

Full implementation: see Phase 1 Plan §3.

---

## Tools

### Execution Tools (shared by all agents)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `bash` | Execute shell command | `command`, `timeout` (default 120s) |
| `read_file` | Read file contents | `path`, `offset?`, `limit?` |
| `write_file` | Create or overwrite file | `path`, `content` |
| `edit_file` | Replace string in file | `path`, `old_string`, `new_string` |
| `glob_search` | Find files by pattern | `pattern`, `path?` |
| `grep_search` | Search file contents by regex | `pattern`, `path?`, `glob?` |

### Provider Tools (server-side, Anthropic-executed)

```python
PROVIDER_TOOLS = [
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 5},
    {"type": "web_fetch_20250910", "name": "web_fetch", "max_size": 100_000},
]
```

These are NOT dispatched by `execute_tool()`. The API executes them server-side; results appear inline in response content.

### Structured Output Tools (agent → orchestrator)

How agents communicate results. The orchestrator handles each call by updating LoopState directly — no parsing, no ambiguity.

| Tool | Used By | Required Fields | Purpose | Phase |
|------|---------|-----------------|---------|-------|
| `manage_task` | Planning, gates, CC, VRC, eval | `action`, `task_id` | Mutate plan | 1 |
| `report_task_complete` | Builder, Fixer | `task_id`, `files_created`, `files_modified` | Signal done | 1 |
| `report_discovery` | Discovery agent | `deliverable_type`, `project_type`, `codebase_state`, `value_proofs` | Sprint context | 1 |
| `report_critique` | PRD critique | `verdict`, `reason` | PRD feasibility | 1 |
| `report_triage` | Triage agent | `root_causes[]` | Group failures | 1 |
| `request_human_action` | Any agent | `action`, `instructions`, `blocked_task_id` | Pause for human | 1 |
| `report_vrc` | VRC agent | `value_score`, `deliverables_*`, `recommendation`, `summary` | Value check | 2 |
| `report_course_correction` | CC agent | `action`, `reason` | Declare correction | 2 |
| `report_eval_finding` | Evaluator | `severity`, `description`, `user_impact` | Experience issue | 3 |
| `report_research` | Research agent | `topic`, `findings`, `sources` | External knowledge | 3 |
| `report_vision_validation` | Vision validator | `verdict`, `issues[]`, `strengths[]`, `reason` | Vision quality | 3 |
| `report_strategy_change` | Strategy Reasoner | `pattern`, `cause`, `evidence[]`, `action`, `rationale`, `re_evaluate_after` | Process meta | 3 |
| `report_epic_decomposition` | Epic decomposer | `epic_count`, `epics[]`, `vision_too_large`, `rationale` | Epic planning | 3 |
| `report_epic_summary` | Epic summary gen | `epic_id`, `summary`, `vrc_snapshot` | Human checkpoint | 3 |
| `report_coherence` | Coherence evaluator | `mode`, `dimensions{}`, `overall`, `top_findings[]` | System health | 2/3 |

Full JSON schemas: see each Phase Plan.

### Tool Role Mapping

```python
def get_tools_for_role(role: AgentRole) -> list[dict]:
    """Return execution + provider tools appropriate for this role.
    Structured output tools are added separately per-prompt by the orchestrator."""
    match role:
        case AgentRole.RESEARCHER:  return EXECUTION_TOOLS + PROVIDER_TOOLS
        case AgentRole.EVALUATOR:   return READ_ONLY_TOOLS  # inspect but not modify
        case AgentRole.CLASSIFIER:  return []                # pure reasoning
        case _:                     return EXECUTION_TOOLS    # full filesystem
```

### Task Mutation Guardrails (Layer 1 — deterministic, zero LLM cost)

Every `manage_task` call passes through `validate_task_mutation()` before mutating state:
- **Missing fields** (CLARITY): description, value, acceptance required for "add"
- **Duplicate detection** (DRY): Jaccard word-set similarity >= 0.75 against existing tasks
- **Scope creep** (PRUNE): Mid-loop task ceiling (15 unfinished mid-loop tasks)
- **Invalid dependencies** (CONNECT): Referenced task must exist
- **Circular dependencies** (CONNECT): DFS cycle detection
- **Removal safety**: Cannot remove task with dependents

Full implementation: see Phase 1 Plan §8.

---

## Decision Engine

### Actions

```python
class Action(Enum):
    EXECUTE = "execute"
    GENERATE_QC = "generate_qc"
    RUN_QC = "run_qc"
    FIX = "fix"
    CRITICAL_EVAL = "critical_eval"
    COURSE_CORRECT = "course_correct"
    RESEARCH = "research"
    INTERACTIVE_PAUSE = "interactive_pause"
    SERVICE_FIX = "service_fix"
    COHERENCE_EVAL = "coherence_eval"
    EXIT_GATE = "exit_gate"
```

### Priority Order

`decide_next_action()` is **deterministic** — no LLM needed, pure state analysis:

| Priority | Condition | Action | Rationale |
|----------|-----------|--------|-----------|
| 0 | Paused for human action | INTERACTIVE_PAUSE | Don't burn tokens waiting |
| 1 | Services down (software only) | SERVICE_FIX | Nothing works without services |
| 2 | Stuck (N iterations no progress) | COURSE_CORRECT | Something fundamental is wrong |
| 3 | QC needs generating (enough tasks) | GENERATE_QC | Generate early for regression |
| 4 | QC checks failing | FIX → RESEARCH → COURSE_CORRECT | Fix before building more |
| 5 | Task blocked on human action | INTERACTIVE_PAUSE | Unblock the task |
| 6 | Pending tasks exist | EXECUTE | Build the next thing |
| 7 | QC checks pending (not run) | RUN_QC | Run generated checks |
| 8 | Critical eval due | CRITICAL_EVAL | Experience check every N tasks |
| 8b | Coherence eval due | COHERENCE_EVAL | System-level coherence check |
| 9 | All done + all passing | EXIT_GATE | Fresh-context final verification |
| fallback | None of the above | COURSE_CORRECT | Something unexpected |

**Key design choices:**
- QC generates EARLY so regression is meaningful from the start
- Builder, QC, and Evaluator are separate agents — builder never grades own work
- Research before course correction — when fixes exhausted, acquire new knowledge first
- Exit gate is inside the loop — if it fails, gaps become tasks and loop continues

Full implementation: see Phase 1 Plan §5.

---

## Rendered Views

JSON state is the single source of truth, but humans and LLM agents benefit from readable documents. The loop generates markdown from state on demand.

| Artifact | Generated From | When Rendered |
|----------|---------------|---------------|
| `IMPLEMENTATION_PLAN.md` | `state.tasks` | After pre-loop, quality gates, course correction |
| `VALUE_CHECKLIST.md` | `state.vrc_history` + `state.tasks` | After each full VRC |
| `DELIVERY_REPORT.md` | Full state | After exit gate passes or budget exhausted |

```
                    ┌──────────────────────┐
                    │   .loop_state.json   │  ← Single source of truth
                    └──────────┬───────────┘
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                     ▼
 IMPLEMENTATION_PLAN.md  VALUE_CHECKLIST.md   DELIVERY_REPORT.md
 (rendered snapshot)     (rendered snapshot)  (rendered snapshot)
```

**Critical rule**: Agents READ these files for context. Agents NEVER WRITE to them. All mutations go through structured tools → state → rendered on demand.

---

## Git Operations

Git is the loop's safety net and audit trail. Every change is tracked, every known-good state is checkpointed, and the loop can roll back when fixing forward is more expensive than reverting.

### Branch Management

At sprint start (before any work):

1. **Detect current branch** — if on a protected branch (main, master, develop, production, staging), refuse to work there
2. **Stash uncommitted changes** — `git stash push -m "telic-loop-auto-stash-{timestamp}"` preserves any in-progress work
3. **Create feature branch** — `telic-loop/{sprint}-{timestamp}` from current HEAD
4. **Record in state** — `state.git.branch_name`, `state.git.original_branch`, `state.git.had_stashed_changes`

### Safe Commits

The loop commits after every task completion and at key phase boundaries. Commits use **selective staging** — never `git add -A`.

**Staging rules:**
- Stage modified tracked files: `git add -u`
- Stage new files only from safe directories (derived from `SprintContext` — e.g., `src/`, `tests/`, sprint directory)
- **Sensitive file scan before commit**: check staged files against `state.git.sensitive_patterns`. If any match, unstage them and log a warning. Never commit `.env`, credentials, keys, or secrets
- **Auto-maintain `.gitignore`**: ensure common sensitive patterns are present

**Commit format:**
```
telic-loop({sprint}): {task_id} - {description}

Co-Authored-By: Telic-Loop <telic-loop@automated>
```

**Commit triggers:**

| When | Message Format | Creates Checkpoint? |
|------|---------------|-------------------|
| Pre-loop complete | `telic-loop({sprint}): Pre-loop complete — plan ready` | Yes |
| After task execution | `telic-loop({sprint}): {task_id} — {task_name}` | No (wait for QC) |
| After QC pass (all passing) | `telic-loop({sprint}): QC pass — all verifications green` | **Yes** |
| After service fix | `telic-loop({sprint}): Fixed services` | No |
| After course correction | `telic-loop({sprint}): Course correction — {action}` | Yes |
| After rollback | `telic-loop({sprint}): Rollback to {checkpoint_label}` | Yes (new baseline) |
| Exit gate pass | `telic-loop({sprint}): Exit gate passed — value verified` | Yes |
| Delivery complete | `telic-loop({sprint}): Delivery — {value_score:.0%} value` | Yes |

### Checkpoints (Known-Good States)

A **checkpoint** is a commit hash where the codebase is in a known-good state — all QC checks that existed at that point were passing. Checkpoints are the rollback targets.

Checkpoints are recorded in `state.git.checkpoints` as `GitCheckpoint` objects containing:
- The commit hash
- Which tasks were completed
- Which verifications were passing
- The VRC value score at that point

**Checkpoint creation rules:**
- Created after every **QC pass** where all existing verifications are green
- Created after **pre-loop completion** (clean starting point)
- Created after **course correction** (new baseline after restructuring)
- Created after **successful rollback** (the rollback target becomes the new baseline)
- NOT created after task execution alone (task may have introduced regressions not yet caught)

### Rollback (Course Correction Strategy)

When the course corrector determines that recent changes have made things worse — compounding regressions, cascading failures, architectural wrong turns — rolling back to a known-good checkpoint is often faster than trying to fix forward through the damage.

**When rollback is the right choice:**

| Signal | Why Rollback Wins |
|--------|------------------|
| 3+ tasks completed since last checkpoint, all introducing regressions | Undoing 3 broken commits is faster than debugging their interactions |
| Architectural wrong turn (e.g., wrong framework choice, wrong data model) | The foundation is wrong; fixing individual symptoms won't help |
| Cascading failures where each fix breaks something else | The codebase has drifted into an inconsistent state |
| Value score has dropped since last checkpoint | Recent work destroyed more value than it created |

**Rollback process:**

1. **Course Corrector diagnoses rollback** — identifies the checkpoint to roll back to and the tasks to revert, reports via `report_course_correction` with `action: "rollback"`
2. **Orchestrator validates** — checkpoint exists, commit hash is valid, tasks to revert are identified
3. **Git reset** — `git reset --hard {checkpoint_hash}` reverts the working tree
4. **State synchronization** — critical step:
   - Tasks completed after the checkpoint are reset to `"pending"` (with `retry_count` preserved so the loop knows they were attempted)
   - Verifications are reset to match the checkpoint's known-passing set
   - VRC history is preserved (rollback is visible in the value trajectory)
   - A `rollback` entry is appended to `state.git.rollbacks` with full context
   - Loop state is saved to disk
5. **Commit the rollback** — create a new commit recording the rollback itself (so the history is auditable)
6. **Re-plan** — the course corrector restructures the reverted tasks (split them, change approach, add research, etc.) before re-executing

**State synchronization detail:**

```python
def execute_rollback(state: LoopState, checkpoint: GitCheckpoint, reason: str):
    """Roll back git and synchronize loop state."""
    # 1. Git reset
    subprocess.run(["git", "reset", "--hard", checkpoint.commit_hash], check=True)

    # 2. Identify reverted tasks
    completed_task_ids = {t.task_id for t in state.tasks.values() if t.status == "done"}
    checkpoint_task_ids = set(checkpoint.tasks_completed)
    reverted_task_ids = completed_task_ids - checkpoint_task_ids

    # 3. Reset reverted tasks to pending (preserve retry_count)
    for task_id in reverted_task_ids:
        task = state.tasks[task_id]
        task.status = "pending"
        task.completed_at = ""
        task.files_created = []
        task.files_modified = []
        task.completion_notes = f"Rolled back at iteration {state.iteration}: {reason}"
        # retry_count preserved — loop knows this task was attempted before

    # 4. Reset verifications to checkpoint state
    for vid, v in state.verifications.items():
        if vid in checkpoint.verifications_passing:
            v.status = "passed"
        else:
            v.status = "pending"
            v.failures = []

    # 5. Update regression baseline
    state.regression_baseline = set(checkpoint.verifications_passing)

    # 6. Record rollback
    state.git.rollbacks.append({
        "from_hash": state.git.last_commit_hash,
        "to_hash": checkpoint.commit_hash,
        "to_label": checkpoint.label,
        "reason": reason,
        "iteration": state.iteration,
        "tasks_reverted": list(reverted_task_ids),
    })

    # 7. Update git state
    state.git.last_commit_hash = checkpoint.commit_hash

    # 8. Commit the rollback (new commit on top)
    git_commit(state, f"Rollback to {checkpoint.label}: {reason}")

    # 9. Save state
    state.save(config.state_file)
```

**Safety constraints:**
- Cannot roll back past the pre-loop checkpoint (plan structure depends on it)
- Cannot roll back to a checkpoint from a previous epic (epic boundaries are hard barriers)
- Maximum rollbacks per sprint: configurable (default 3) — repeated rollback suggests the plan itself is wrong, not the execution
- Rollback preserves `retry_count` so the loop doesn't infinitely retry the same tasks with the same approach — the course corrector must restructure them

### Non-Software Deliverables

For non-software deliverables (documents, configs), git operations still apply — document drafts are committed, checkpoints track known-good states, and rollback reverts to a previous draft. The same safety rules apply (no sensitive files, feature branch isolation).

---

## Prompt Index

| Prompt | Model | Structured Tools | Phase |
|--------|-------|------------------|-------|
| `system.md` | All | — | 1 |
| `discover_context.md` | Opus (REASONER) | `report_discovery` | 1 |
| `prd_critique.md` | Opus (REASONER) | `report_critique` | 1 |
| `plan.md` | Opus (REASONER) | `manage_task` | 1 |
| `craap.md` | Opus (REASONER) | `manage_task` | 1 |
| `clarity.md` | Opus (REASONER) | `manage_task` | 1 |
| `validate.md` | Opus (REASONER) | `manage_task` | 1 |
| `connect.md` | Opus (REASONER) | `manage_task` | 1 |
| `break.md` | Opus (REASONER) | `manage_task` | 1 |
| `prune.md` | Opus (REASONER) | `manage_task` | 1 |
| `tidy.md` | Opus (REASONER) | `manage_task` | 1 |
| `verify_blockers.md` | Opus (REASONER) | `manage_task` | 1 |
| `preflight.md` | Opus (REASONER) | — | 1 |
| `execute.md` | Sonnet (BUILDER) | `report_task_complete` | 1 |
| `generate_verifications.md` | Sonnet (QC) | (file tools) | 1 |
| `triage.md` | Haiku (CLASSIFIER) | `report_triage` | 1 |
| `fix.md` | Sonnet (FIXER) | (file tools) | 1 |
| `interactive_pause.md` | Opus (REASONER) | `request_human_action` | 1 |
| `vrc.md` | Opus (REASONER) / Haiku (CLASSIFIER) | `report_vrc`, `manage_task` | 2 |
| `course_correct.md` | Opus (REASONER) | `manage_task`, `report_course_correction` | 2 |
| `plan_health_check.md` | Opus (REASONER) | `manage_task` | 2 |
| `exit_gate.md` | Opus (REASONER) | `report_vrc`, `manage_task` | 2 |
| `vision_validate.md` | Opus (REASONER, 5 sessions) | `report_vision_validation` (PASS/NEEDS_REVISION, issues with HARD/SOFT severity) | 3 |
| `critical_eval.md` | Opus (EVALUATOR) | `report_eval_finding`, `manage_task` | 3 |
| `research.md` | Opus (RESEARCHER) | `report_research` + provider tools | 3 |
| `process_monitor.md` | Opus (REASONER) | `report_strategy_change` | 3 |
| `epic_decompose.md` | Opus (REASONER) | `report_epic_decomposition` | 3 |
| `epic_feedback.md` | Opus (REASONER) | `report_epic_summary` | 3 |
| `coherence_eval.md` | Opus (EVALUATOR) / Haiku (CLASSIFIER) | `report_coherence` | 2/3 |

---

## Key Differences from V2

| Aspect | V2 | V3 |
|--------|----|----|
| Goal | "Rewrite in Python for better testing" | "Vision-to-value delivery algorithm" |
| Architecture | Three phases (pre→value→post) | Two phases (pre→value with exit gate inside) |
| State | Agents edit markdown | JSON truth + structured tools |
| Config | Human writes sprint_config.py | Context Discovery derives everything |
| Deliverable | Software only | Any: software, documents, data, configs |
| VRC | 2 checkpoints per sprint | Every iteration (heartbeat) |
| Regression | End of sprint | After every task |
| QC separation | Builder runs own tests | Builder / QC / Evaluator are separate |
| Human blockers | Loop dies | Interactive Pause |
| Exit verification | Post-loop dead end | Exit gate inside loop |
| Course correction | None | Opus diagnoses + restructures |
| External knowledge | Training data only | Research agent + web search |
| Technology | Web app assumptions | Agnostic, discovered from context |
| Agent communication | Free text + regex | Structured tool calls |
| Human feedback | Vision at start only | Between-epic checkpoints (multi_epic) |
| System coherence | Not checked | Quick (every 5 tasks) + Full (epic boundaries) |
| Complex visions | Single monolithic run | Epic decomposition into value blocks |
