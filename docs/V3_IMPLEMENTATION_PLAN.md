# Loop V3: Vision-to-Value Algorithm

> **⚠ SUPERSEDED**: This monolithic plan has been split into authoritative Phase documents:
> - `V3_ARCHITECTURE.md` — structural specification (data model, tools, decision engine)
> - `V3_PHASE1_PLAN.md` — core infrastructure
> - `V3_PHASE2_PLAN.md` — value loop + VRC
> - `V3_PHASE3_PLAN.md` — advanced features (vision refinement, critical eval, research, etc.)
>
> Key design changes since this document:
> - Vision Validation → **Vision Refinement** (interactive collaborative negotiation, not pass/fail gate)
> - PRD REJECT → **PRD Refinement** (researches alternatives, negotiates with human)
> - Verdicts: PASS/CONDITIONAL/FAIL → **PASS/NEEDS_REVISION** with HARD/SOFT issue classification
> - Function: `validate_vision()` → `refine_vision()`
>
> This document is retained for historical context only. Do not use it as implementation reference.

**Date**: 2026-02-14
**Prerequisite reading**: `V2_FLOW.md` (current loop trace), `V3_DESIGN.md` (problem analysis)

---

## What This Is

A **value delivery algorithm**. Given a Vision and a PRD, it delivers the promised outcome to a human user — fully working, fully tested, ready to use without debugging.

This is not a software engineering tool. It is a closed-loop reasoning system that plans, implements, tests, course-corrects, and verifies until the value described in the Vision is real and usable. The output might be a web application, a data pipeline, a CLI tool, or a document — the algorithm is agnostic.

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
│  2. Vision Validation (5-pass) — challenge the Vision   │
│  3. Context Discovery (Opus) — derive sprint context    │
│  4. PRD Feasibility Critique (Opus) — push back hard    │
│  5. Plan Generation (Opus) — tasks → structured state   │
│  6. Quality Gates (Opus) — CRAAP, CLARITY, VALIDATE,    │
│     CONNECT, BREAK, PRUNE, TIDY                         │
│  7. Blocker Resolution — resolve or descope ALL         │
│  8. Preflight — environment ready                       │
│  9. Initial VRC — baseline value assessment             │
│                                                         │
│  EXIT CONDITION: Plan is achievable, blockers resolved  │
│  FAIL CONDITION: Vision flawed or PRD infeasible →      │
│                  report + exit                           │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    THE VALUE LOOP                        │
│                                                         │
│  Iterate until value is delivered.                      │
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
│      EXIT_GATE       → fresh-context final verification │
│                                                         │
│    process_monitor(state)  ← execution pattern check    │
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
└─────────────────────────────────────────────────────────┘
```

---

## File Structure

```
loop-v3/
├── main.py                      # Entry point: pre-loop → value loop (with exit gate)
├── config.py                    # LoopConfig (loop behavior, model routing)
├── state.py                     # LoopState, TaskState, VerificationState, VRCSnapshot
├── discovery.py                 # NEW: Context Discovery — derive sprint context from Vision+PRD+codebase
├── decision.py                  # Decision engine: "what should I do next?"
├── claude.py                    # Anthropic SDK wrapper, model routing
├── tools.py                     # Tool implementations for LLM agents
├── render.py                    # Generate markdown artifacts from structured state
├── phases/
│   ├── __init__.py
│   ├── preloop.py               # Discovery, PRD critique, plan gen, quality gates, preflight
│   ├── execute.py               # Multi-turn task execution (Builder agent)
│   ├── qc.py                    # Quality control: tests, linting, regression (QC agent)
│   ├── critical_eval.py         # Critical evaluation: use deliverable as real user (Evaluator agent)
│   ├── vrc.py                   # Vision Reality Check (the heartbeat)
│   ├── course_correct.py        # Re-planning, descoping, restructuring
│   ├── plan_health.py           # Mid-loop plan quality validation (Layer 2)
│   ├── process_monitor.py       # ProcessMonitorState, metric collectors, trigger evaluation, strategy reasoner
│   ├── research.py              # External research: web search, doc retrieval, synthesis
│   ├── pause.py                 # Interactive Pause: human action needed mid-loop
│   └── exit_gate.py             # Fresh-context exit verification (inside the loop)
├── prompts/                     # Reasoning templates (Opus consumes these)
│   ├── system.md                # Base system prompt
│   ├── vision_validate.md       # Vision Validation — 5-pass intent/outcome challenge
│   ├── discover_context.md      # NEW: "What is this project? What does it need?"
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
│   ├── critical_eval.md         # Critical evaluation (Evaluator agent — be the user)
│   ├── triage.md                # Failure root cause grouping
│   ├── fix.md                   # Fix agent with error context
│   ├── course_correct.md        # Re-planning / descoping
│   ├── plan_health_check.md     # Mid-loop quality sweep (DRY, SOLID, contradictions)
│   ├── process_monitor.md       # Strategy Reasoner prompt (Opus, RED trigger only)
│   ├── research.md              # External research — search web, synthesize findings
│   ├── interactive_pause.md     # Human action instructions
│   └── exit_gate.md             # Fresh-context final verification
```

---

## 1. Configuration

Configuration has two layers: **loop config** (how the algorithm behaves) and **sprint context** (what it's working on). The human provides only the loop config. The sprint context is **discovered automatically** by the pre-loop.

### Loop Config (human-provided, minimal)

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
    model_reasoning: str = "claude-opus-4-6"          # Planning, VRC, critique, course correction
    model_execution: str = "claude-sonnet-4-5-20250929"  # Execution, fixing, verification gen
    model_triage: str = "claude-haiku-4-5-20251001"      # Classification, simple checks

    # Verification
    generate_verifications_after: int = 1  # generate verifications after this many tasks complete
    regression_after_every_task: bool = True
    regression_timeout: int = 120          # total time budget for regression suite (seconds)

    # Critical evaluation
    critical_eval_interval: int = 3         # run critical evaluation every N tasks
    critical_eval_on_all_pass: bool = True   # run when all QC checks pass

    # Safety limits
    max_exit_gate_attempts: int = 3    # max times exit gate can run before forced partial report
    max_course_corrections: int = 5    # max course corrections per sprint

    # Plan health (mid-loop quality validation)
    plan_health_after_n_tasks: int = 5  # run health check after this many mid-loop tasks created

    # Process Monitor (execution pattern degradation detection)
    process_monitor_min_iterations: int = 5      # Don't run meta-reasoning before this
    process_monitor_cooldown: int = 5            # Min iterations between strategy changes
    process_monitor_ema_alpha: float = 0.3       # EMA smoothing factor
    # Trigger thresholds
    pm_plateau_patience: int = 5                 # Consecutive low-velocity iterations
    pm_plateau_threshold: float = 0.1            # Value velocity below this = plateau
    pm_efficiency_drop_pct: float = 50           # % drop from rolling average = collapse
    pm_churn_yellow: int = 2                     # Task fail-fix-fail count for YELLOW
    pm_churn_red: int = 3                        # Task fail-fix-fail count for RED
    pm_error_recurrence: int = 3                 # Same error hash N times = RED
    pm_category_cluster_pct: float = 60          # % of failures sharing root cause = YELLOW
    pm_budget_value_ratio: float = 2.0           # Budget/value ratio for RED
    pm_file_hotspot_pct: float = 50              # % of iterations touching same file = YELLOW

    # Reliability
    max_task_retries: int = 3          # max retries if agent doesn't call completion tool

    # Derived paths
    @property
    def vision_file(self) -> Path:
        return self.sprint_dir / "VISION.md"

    @property
    def prd_file(self) -> Path:
        return self.sprint_dir / "PRD.md"

    @property
    def state_file(self) -> Path:
        return self.sprint_dir / ".loop_state.json"

    # ── Rendered artifacts (generated FROM state, never edited by agents) ──

    @property
    def plan_file(self) -> Path:
        """Human-readable plan. Generated from state.tasks, not a source of truth."""
        return self.sprint_dir / "IMPLEMENTATION_PLAN.md"

    @property
    def value_checklist(self) -> Path:
        """Human-readable checklist. Generated from state + VRC history, not a source of truth."""
        return self.sprint_dir / "VALUE_CHECKLIST.md"
```

### Sprint Context (discovered automatically by pre-loop)

The sprint context is **derived, not provided**. The pre-loop's Context Discovery phase (see §4.3) examines the Vision, PRD, existing codebase, file structure, and environment to produce this. The human never writes it.

```python
@dataclass
class SprintContext:
    """
    What the loop is working on. Derived by Context Discovery (Opus),
    not manually configured. The loop examines Vision + PRD + codebase
    and figures out what it needs.
    """
    # What kind of deliverable is the Vision describing?
    deliverable_type: str = "unknown"   # "software", "document", "data", "config", "hybrid"
    project_type: str = "unknown"       # "web_app", "cli", "api", "library", "report", etc.

    # What exists already?
    codebase_state: str = "greenfield"  # "greenfield", "brownfield", "non_code"

    # What's in the environment?
    environment: dict = field(default_factory=dict)  # discovered tools, env vars, files

    # What services need running? (empty for non-software deliverables)
    services: dict = field(default_factory=dict)

    # How should value be verified?
    verification_strategy: dict = field(default_factory=dict)

    # Value proof targets (from VISION, surfaced by discovery)
    value_proofs: list[str] = field(default_factory=list)

    # What the discovery agent surfaced that it couldn't resolve
    unresolved_questions: list[str] = field(default_factory=list)
```

The discovery agent produces this by:
1. Reading the Vision and PRD
2. Scanning the codebase (if one exists) for languages, frameworks, existing tests
3. Checking the environment for available tools, env vars, running services
4. Determining what type of deliverable the Vision describes
5. Inferring the verification strategy from the deliverable type and project structure
6. Surfacing anything it can't determine — these become questions for the human

**Example: What discovery produces for a web app sprint:**
```python
SprintContext(
    deliverable_type="software",
    project_type="web_app",
    codebase_state="brownfield",
    environment={
        "tools_found": ["uv", "node", "npm", "docker"],
        "env_vars_found": ["DATABASE_URL", "REDIS_URL", "GEMINI_API_KEY"],
        "env_vars_missing": ["STRIPE_API_KEY"],
        "key_files": ["backend/app/main.py", "frontend/package.json"],
    },
    services={
        "postgres": {"port": 5432, "health_type": "tcp"},
        "redis": {"port": 6379, "health_type": "tcp"},
        "backend": {"port": 8000, "health_url": "http://localhost:8000/health"},
        "frontend": {"port": 3000, "health_url": "http://localhost:3000"},
    },
    verification_strategy={
        "test_frameworks": ["pytest:backend/tests", "playwright:frontend/e2e"],
        "holistic_entry": "http://localhost:3000",
        "holistic_type": "browser",
    },
    value_proofs=[
        "User can log in via Google OAuth",
        "User can send a chat message and get AI response",
    ],
)
```

**Example: What discovery produces for a document sprint:**
```python
SprintContext(
    deliverable_type="document",
    project_type="report",
    codebase_state="non_code",
    environment={"tools_found": ["python"]},
    services={},  # no services needed
    verification_strategy={
        "holistic_type": "document_review",
        "criteria_source": "PRD",  # verify against PRD sections
    },
    value_proofs=[
        "Report addresses all 5 research questions from the PRD",
        "Each finding includes supporting data",
        "Executive summary is actionable",
    ],
)
```

---

## 2. State Management

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
    gaps: list[dict]                # what's still missing — [{id, description, severity, suggested_task}]
    recommendation: str             # CONTINUE, COURSE_CORRECT, DESCOPE, SHIP_READY
    summary: str

@dataclass
class TaskState:
    """
    A single implementation task. This IS the plan — there is no separate
    IMPLEMENTATION_PLAN.md that agents edit. Tasks live here in structured
    state and are rendered to markdown for human readability on demand.
    """
    task_id: str
    status: Literal["pending", "in_progress", "done", "blocked", "descoped"] = "pending"
    source: str = ""                # "plan", "critical_eval", "vrc", "exit_gate", "course_correction"
    created_at: str = ""
    completed_at: str = ""
    blocked_reason: str = ""

    # ── Rich fields (replaces IMPLEMENTATION_PLAN.md prose) ──
    description: str = ""           # what to build
    value: str = ""                 # why it matters to the user
    prd_section: str = ""           # traceability: "§2.1"
    acceptance: str = ""            # how to verify it's done
    dependencies: list[str] = field(default_factory=list)  # task_ids that must complete first
    phase: str = ""                 # grouping: "foundation", "core", "integration", etc.
    files_expected: list[str] = field(default_factory=list)  # files to create/modify

    # ── Execution tracking ──
    retry_count: int = 0               # times agent failed to call report_task_complete

    # ── Completion metadata (populated by report_task_complete tool) ──
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    completion_notes: str = ""

    # ── Plan health tracking ──
    health_checked: bool = False      # True after Layer 2 plan health check has reviewed this task

@dataclass
class VerificationState:
    """
    Tracks a single verification. For software this is a test script.
    For documents this might be a criteria check. For data this might be
    an integrity validation. The loop is agnostic to what the verification
    actually does — it just knows pass/fail.
    """
    verification_id: str
    category: str                   # determined by discovery, not hardcoded tiers
    status: Literal["pending", "passed", "failed", "blocked"] = "pending"
    script_path: str | None = None  # executable verification (may be None for criteria checks)
    attempts: int = 0
    failures: list[FailureRecord] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)  # service/tool dependencies

    @property
    def last_error(self) -> str | None:
        if self.failures:
            f = self.failures[-1]
            return f"{f.stdout}\n{f.stderr}".strip()
        return None

    @property
    def attempt_history(self) -> str:
        """Full history for fix agent — what was tried and what happened."""
        lines = []
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
class FailureRecord:
    timestamp: str
    attempt: int
    exit_code: int
    stdout: str
    stderr: str
    fix_applied: str | None = None
    files_changed: list[str] = field(default_factory=list)

@dataclass
class PauseState:
    """Interactive Pause state. Exists only when the loop is paused for human action."""
    reason: str                     # what the human needs to do
    instructions: str               # step-by-step instructions
    verification: str = ""          # shell command to verify action was completed
    requested_at: str = ""          # ISO timestamp

@dataclass
class ProcessMonitorState:
    """
    Process Meta-Reasoning state. Tracks execution metrics every iteration
    and triggers an Opus Strategy Reasoner when degradation thresholds are crossed.

    Distinct from Plan Health Check (§11.1) — Plan Health checks task DEFINITIONS,
    Process Monitor checks EXECUTION PATTERNS.
    Distinct from Course Correction (§11) — CC changes the PLAN, PM changes the STRATEGY.
    """
    value_velocity_ema: float = 0.0          # EMA of VRC score delta per iteration
    token_efficiency_ema: float = 0.0         # EMA of VRC delta per token consumed
    cusum_efficiency: float = 0.0             # CUSUM of efficiency deviations
    churn_counts: dict[str, int] = field(default_factory=dict)  # task_id -> fail-fix-fail count
    error_hashes: dict[str, dict] = field(default_factory=dict) # hash -> {count, tasks}
    file_touches: dict[str, int] = field(default_factory=dict)  # filepath -> touch count
    status: str = "GREEN"                     # GREEN | YELLOW | RED
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
class LoopState:
    sprint: str
    phase: Literal["pre_loop", "value_loop"] = "pre_loop"
    iteration: int = 0

    # Pre-loop gates
    gates_passed: set[str] = field(default_factory=set)

    # Sprint context (derived by Context Discovery, not human-provided)
    context: SprintContext = field(default_factory=SprintContext)

    # Task tracking
    tasks: dict[str, TaskState] = field(default_factory=dict)
    tasks_since_last_critical_eval: int = 0
    mid_loop_tasks_since_health_check: int = 0  # triggers plan health check at threshold

    # Verification tracking (QC — tests, linting, type checks)
    verifications: dict[str, VerificationState] = field(default_factory=dict)
    verification_categories: list[str] = field(default_factory=list)  # ordered by priority

    # Regression baseline
    regression_baseline: set[str] = field(default_factory=set)  # verification IDs that have passed

    # VRC history — the heartbeat record
    vrc_history: list[VRCSnapshot] = field(default_factory=list)

    # Progress tracking (for stuck detection)
    progress_log: list[dict] = field(default_factory=list)  # [{iteration, action, result}]
    iterations_without_progress: int = 0

    # Interactive Pause state (None = not paused)
    pause: "PauseState | None" = None

    # Process Monitor state (tracks execution patterns and strategy)
    process_monitor: ProcessMonitorState = field(default_factory=ProcessMonitorState)

    # Research tracking
    research_briefs: list[dict] = field(default_factory=list)  # [{topic, findings, sources, iteration}]
    research_attempted_for_current_failures: bool = False      # reset when new failures appear

    # Structured tool results (populated by handlers, consumed by orchestrator).
    # Single dict keyed by report type. Handlers set agent_results["critique"],
    # agent_results["course_correction"], agent_results["triage"], etc.
    # Each entry is the last report from that agent type.
    agent_results: dict[str, Any] = field(default_factory=dict)
    # Expected keys and shapes:
    #   "critique":          {verdict, reason, amendments, descope_suggestions}
    #   "course_correction": {action, reason}
    #   "triage":            [{cause, affected_tests, priority, fix_suggestion}]

    # Exit gate tracking
    exit_gate_attempts: int = 0       # how many times exit gate has run

    # Token tracking
    total_tokens_used: int = 0

    def record_progress(self, action: str, result: str, made_progress: bool):
        self.progress_log.append({
            "iteration": self.iteration,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        if made_progress:
            self.iterations_without_progress = 0
        else:
            self.iterations_without_progress += 1

    def is_stuck(self, config: "LoopConfig") -> bool:
        return self.iterations_without_progress >= config.max_no_progress

    @property
    def latest_vrc(self) -> VRCSnapshot | None:
        return self.vrc_history[-1] if self.vrc_history else None

    @property
    def value_delivered(self) -> bool:
        vrc = self.latest_vrc
        return vrc is not None and vrc.recommendation == "SHIP_READY"

    def add_regression_pass(self, verification_id: str):
        """Mark a verification as part of the regression baseline."""
        self.regression_baseline.add(verification_id)

    def gate_passed(self, gate_name: str) -> bool:
        """Check if a quality gate has been passed."""
        return gate_name in self.gates_passed

    def pass_gate(self, gate_name: str):
        """Mark a quality gate as passed."""
        self.gates_passed.add(gate_name)

    def invalidate_tests(self):
        """Clear all verifications so they can be regenerated."""
        self.verifications.clear()
        self.regression_baseline.clear()
        self.gates_passed.discard("verifications_generated")

    def add_task(self, task: TaskState):
        """Add a task via structured tool call (not markdown editing)."""
        self.tasks[task.task_id] = task

    # NOTE: Rendering methods (render_plan_markdown, render_value_checklist,
    # render_delivery_report) live in render.py as pure functions taking
    # LoopState as input. LoopState stays a pure data container.
    # See §16 for rendering details.

    def save(self, path: Path):
        """Serialize state to JSON. Sets (gates_passed, regression_baseline)
        are converted to sorted lists for JSON compatibility."""
        data = asdict(self)
        # set → list for JSON serialization
        data["gates_passed"] = sorted(data["gates_passed"])
        data["regression_baseline"] = sorted(data["regression_baseline"])
        path.write_text(json.dumps(data, indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> "LoopState":
        """Deserialize state from JSON. Lists are restored to sets where needed."""
        data = json.loads(path.read_text())
        # list → set restoration
        data["gates_passed"] = set(data.get("gates_passed", []))
        data["regression_baseline"] = set(data.get("regression_baseline", []))
        return cls(**data)  # actual impl will use dacite or manual reconstruction
```

---

## 3. Claude Wrapper — Model Routing

The key architectural decision: Opus for reasoning, Sonnet for execution, Haiku for classification.

```python
class AgentRole(Enum):
    """
    Each role maps to (model_config_attr, max_turns, thinking_effort, max_tokens).

    thinking_effort controls adaptive thinking (Opus 4.6+):
      - "max"      → deep reasoning for planning, critique, course correction
      - "high"     → strong reasoning for evaluation, research
      - None       → thinking disabled (Sonnet/Haiku execution roles)

    max_tokens is per-response output limit. Roles that produce large outputs
    (planning, evaluation) get higher limits. If max_tokens > 21333, the
    session MUST use streaming (see ClaudeSession).

    Roles preserve semantic meaning (EVALUATOR vs REASONER) even when
    the underlying config is identical — they may diverge in the future
    and they make call sites self-documenting.
    """
    #                    model_attr        turns  thinking  max_tokens
    REASONER   = ("model_reasoning",  40,  "max",    32768)  # Planning, VRC, critique, course correction
    EVALUATOR  = ("model_reasoning",  40,  "high",   32768)  # Critical evaluation — be the user
    RESEARCHER = ("model_reasoning",  30,  "high",   16384)  # External research — web search, synthesis
    BUILDER    = ("model_execution",  60,  None,     16384)  # Execute tasks — writing code, content
    FIXER      = ("model_execution",  25,  None,     16384)  # Multi-turn fix conversations
    QC         = ("model_execution",  30,  None,     16384)  # QC — tests, verifications, linting
    CLASSIFIER = ("model_triage",      5,  None,      4096)  # Triage, categorization, simple checks


class Claude:
    """Factory for creating sessions with model routing.
    Holds a reference to LoopState so all sessions can dispatch structured tools.

    Authentication: The loop runs via Claude Max subscription (claude.ai),
    NOT a raw API key. The Anthropic SDK auto-detects auth from the
    environment (ANTHROPIC_API_KEY env var or ~/.anthropic/config).
    No explicit key validation is needed — the first API call will
    surface any auth issues immediately."""

    def __init__(self, config: LoopConfig, state: "LoopState"):
        self.config = config
        self.client = anthropic.Anthropic()  # auto-detects auth from environment
        # Beta header required for web_fetch server-side tool
        self.beta_headers = ["web-fetch-2025-09-10"]
        self.state = state  # shared reference — structured tools update this

    def session(self, role: AgentRole, system_extra: str = "") -> ClaudeSession:
        """Create a session for the given agent role.
        Model, max_turns, thinking effort, and max_tokens are derived from the role.
        All call sites use named roles: claude.session(AgentRole.BUILDER)"""
        model_attr, max_turns, thinking_effort, max_tokens = role.value
        system = load_prompt("system") + ("\n" + system_extra if system_extra else "")
        tools = get_tools_for_role(role)
        # Pass beta headers when session uses provider tools (web_fetch needs it)
        has_provider_tools = any(
            t.get("type", "").startswith("web_fetch") for t in tools
        )
        return ClaudeSession(
            client=self.client,
            model=getattr(self.config, model_attr),
            system=system,
            max_turns=max_turns,
            thinking_effort=thinking_effort,  # "max", "high", or None
            max_tokens=max_tokens,
            tools=tools,  # B2+O1: role-specific tool sets
            state=self.state,
            betas=self.beta_headers if has_provider_tools else None,
        )
```

### ClaudeSession with Adaptive Thinking

```python
# Streaming threshold: API requires streaming for max_tokens > 21333
STREAMING_THRESHOLD = 21333

class ClaudeSession:
    """Multi-turn conversation with tool execution.

    Supports adaptive thinking (Opus 4.6+), role-specific tool sets,
    and automatic streaming when max_tokens exceeds the API threshold.
    """

    def __init__(self, client, model, system, max_turns=30,
                 thinking_effort: str | None = None,
                 max_tokens: int = 16384,
                 tools: list[dict] | None = None,
                 state: "LoopState | None" = None,
                 betas: list[str] | None = None):
        self.client = client
        self.model = model
        self.system = system
        self.messages = []
        self.max_turns = max_turns
        self.thinking_effort = thinking_effort  # "max", "high", or None
        self.max_tokens = max_tokens
        self.tools = tools or []               # role-specific tool set
        self.state = state                      # needed for structured tool dispatch
        self.betas = betas                      # beta headers (e.g. web-fetch)
        self.use_streaming = max_tokens > STREAMING_THRESHOLD
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def send(self, user_message: str, task_source: str = "agent") -> str:
        """Send message, execute tools in a loop, return final text.

        task_source: Provenance label for tasks created via manage_task during
        this session. Set by the orchestrator: "plan", "critical_eval",
        "exit_gate", "vrc", "course_correction", etc."""
        self.messages.append({"role": "user", "content": user_message})

        for turn in range(self.max_turns):
            kwargs = dict(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system,
                messages=self.messages,
                tools=self.tools,
            )
            if self.betas:
                kwargs["betas"] = self.betas

            # Adaptive thinking for Opus reasoning roles (replaces deprecated
            # "enabled" + budget_tokens syntax). Effort level controls depth:
            #   "max"  — deep reasoning (planning, critique, course correction)
            #   "high" — strong reasoning (evaluation, research)
            #   None   — thinking disabled (Sonnet/Haiku execution)
            if self.thinking_effort:
                kwargs["thinking"] = {"type": "adaptive"}
                kwargs["output_config"] = {"effort": self.thinking_effort}

            # Use streaming when max_tokens > 21333 (API requirement)
            # When betas are active, use client.beta.messages namespace
            # (required for web_fetch and other beta features).
            api = self.client.beta.messages if self.betas else self.client.messages
            if self.use_streaming:
                response = self._send_streaming(api=api, **kwargs)
            else:
                response = api.create(**kwargs)

            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens
            # Aggregate into shared state for budget tracking
            if self.state:
                self.state.total_tokens_used += (
                    response.usage.input_tokens + response.usage.output_tokens
                )

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            # Handle pause_turn: server-side tool loop (web_search/web_fetch)
            # hit its iteration limit. Re-send the conversation as-is so the
            # server can continue the turn. No user message needed — just
            # loop back to the API call.
            if response.stop_reason == "pause_turn":
                continue

            # Execute tool calls (user-defined tools only — provider-defined
            # tools like web_search/web_fetch are executed server-side and
            # their results appear inline in response.content as
            # server_tool_use / web_search_tool_result blocks)
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input, self.state,
                                          task_source=task_source)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            if tool_results:
                self.messages.append({"role": "user", "content": tool_results})
            # If no user-defined tool calls but stop_reason != "end_turn",
            # it was a provider-defined tool (web_search/web_fetch) —
            # results are already in response.content, continue the loop.

        raise RuntimeError(f"Agent exceeded max_turns ({self.max_turns})")

    def _send_streaming(self, api=None, **kwargs) -> "Message":
        """Stream response and collect into a Message object.
        Required when max_tokens > 21333.
        api: either client.messages or client.beta.messages."""
        target = api or self.client.messages
        with target.stream(**kwargs) as stream:
            return stream.get_final_message()
```

---

## 4. Pre-Loop Phase — Qualify Before Committing

The pre-loop runs once. Its job: ensure the work is achievable before entering the delivery loop. If it's not achievable, report why and exit — don't waste iterations.

### 4.1 Input Validation

```python
def validate_inputs(config: LoopConfig) -> bool:
    """Check that VISION.md and PRD.md exist and are non-empty."""
    for f in [config.vision_file, config.prd_file]:
        if not f.exists():
            print(f"MISSING: {f}")
            return False
        if f.stat().st_size < 100:
            print(f"WARNING: {f} seems too short ({f.stat().st_size} bytes)")
    return True
```

### 4.2 Vision Validation (5-pass)

This is the first reasoning step after input validation. It challenges the Vision document before the loop commits to execution. It runs BEFORE Context Discovery — if the Vision is flawed, there is no point discovering context or building a plan around it.

Vision Validation uses 5 sequential Opus sessions, each with a different cognitive mode. Each pass produces a structured artifact consumed by the next. The framework draws on OKR Validation, JTBD Four Forces, Theory of Change, Assumption Mapping, Pre-Mortem, and AI Alignment frameworks.

- **If FAIL**: the loop reports findings and exits. A flawed Vision would waste the entire sprint.
- **If CONDITIONAL**: suggested revisions are presented to the human. After the human revises the Vision, Pass 5 re-runs to reassess.
- **If PASS**: proceed to Context Discovery.

```python
def validate_vision(config: LoopConfig, claude: Claude) -> dict:
    """
    5-pass Vision Validation. Challenges the Vision before committing to execution.

    Runs BEFORE Context Discovery — if the Vision is flawed, there's no point
    figuring out how to build it. This catches:
    - Goals that are activities, not outcomes
    - Broken causal chains (if we build X, then... why?)
    - Unacknowledged adoption barriers (anxiety, habit)
    - Kill-shot assumptions (critical AND unproven)
    - Unaddressed failure modes

    Returns the synthesis result. If FAIL, the loop reports findings and exits.
    If CONDITIONAL, suggested revisions are presented to the human.
    """
    vision = config.vision_file.read_text()
    prompt_template = load_prompt("vision_validate")

    # ── Pass 1: Extraction (faithful comprehension) ──
    session_p1 = claude.session(AgentRole.REASONER,
        system_extra="You are extracting a structured model from a Vision document. "
        "Do not judge or evaluate yet — just map what the Vision claims. "
        "Extract goals, causal chains, metrics, target user, and assumptions."
    )
    p1_result = session_p1.send(format_pass(prompt_template, "Pass 1", VISION=vision))

    # ── Pass 2: Force Analysis (adversarial empathy) ──
    session_p2 = claude.session(AgentRole.REASONER,
        system_extra="You are modeling the forces for and against adoption. "
        "Think like the target user, not the builder. Be honest about anxiety "
        "and habit — these are the forces that kill products."
    )
    p2_result = session_p2.send(format_pass(prompt_template, "Pass 2",
        VISION=vision, PASS_1_OUTPUT=p1_result))

    # ── Pass 3: Causal Audit (logical rigor) ──
    session_p3 = claude.session(AgentRole.REASONER,
        system_extra="You are auditing causal logic. Every If→Then link needs "
        "a mechanism (a 'because'). Every metric needs a gaming scenario check. "
        "Be rigorous — broken chains mean the Vision's logic doesn't hold."
    )
    p3_result = session_p3.send(format_pass(prompt_template, "Pass 3",
        VISION=vision, PASS_1_OUTPUT=p1_result, PASS_2_OUTPUT=p2_result))

    # ── Pass 4: Pre-Mortem (imaginative pessimism) ──
    session_p4 = claude.session(AgentRole.REASONER,
        system_extra="You are conducting a pre-mortem. The project has FAILED. "
        "It is 18 months later and the deliverable was abandoned. WHY? "
        "Generate specific, plausible failure scenarios. Cross-reference with "
        "kill-shot assumptions and leaps of faith from previous passes."
    )
    p4_result = session_p4.send(format_pass(prompt_template, "Pass 4",
        VISION=vision, PASS_2_OUTPUT=p2_result, PASS_3_OUTPUT=p3_result))

    # ── Pass 5: Synthesis (balanced judgment) ──
    session_p5 = claude.session(AgentRole.REASONER,
        system_extra="You are producing a balanced final assessment. "
        "Score the Vision on four dimensions: outcome-grounded, adoption-realistic, "
        "causally-sound, failure-aware. Be honest but fair — every Vision has "
        "assumptions; the question is whether they're acknowledged and manageable."
    )
    p5_result = session_p5.send(format_pass(prompt_template, "Pass 5",
        VISION=vision, PASS_1_OUTPUT=p1_result, PASS_2_OUTPUT=p2_result,
        PASS_3_OUTPUT=p3_result, PASS_4_OUTPUT=p4_result))

    # Result arrives via report_vision_validation tool call
    validation = state.agent_results.get("vision_validation")
    if not validation:
        # Fallback: parse from text
        validation = {"verdict": "CONDITIONAL", "reason": "Agent did not call reporting tool"}

    return validation
```

### 4.3 Context Discovery (NEW — Opus)

This is the step that makes the loop self-configuring. Instead of requiring a human-written sprint config, Opus examines the Vision, PRD, existing codebase, and environment to **derive** everything it needs.

```python
def discover_context(config: LoopConfig, claude: Claude) -> SprintContext:
    """
    Opus examines Vision + PRD + codebase + environment and derives
    the sprint context. The human never writes a sprint_config.py.

    Discovery determines:
    - What type of deliverable the Vision describes (software, document, data, etc.)
    - What project type it is (web_app, cli, report, etc.)
    - What codebase state exists (greenfield, brownfield, non_code)
    - What tools and services are available
    - How value should be verified
    - What value proof targets come from the Vision
    """
    session = claude.session(AgentRole.REASONER,
        system_extra="You are analyzing a project to understand what it is, "
        "what it needs, and how to verify that value has been delivered. "
        "Examine everything available — Vision, PRD, codebase, environment — "
        "and produce a complete sprint context. Be thorough and precise."
    )

    vision = config.vision_file.read_text()
    prd = config.prd_file.read_text()

    prompt = load_prompt("discover_context").format(
        VISION=vision,
        PRD=prd,
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )

    # The agent uses file tools to scan the codebase, bash to check
    # installed tools and env vars, and the report_discovery tool to
    # submit the structured SprintContext.
    response = session.send(prompt)

    context = claude.state.context  # populated by report_discovery tool handler
    if context.unresolved_questions:
        # Discovery couldn't determine everything — ask the human
        print(f"\n  DISCOVERY needs clarification:")
        for q in context.unresolved_questions:
            print(f"    ? {q}")
        # In interactive mode, prompt for answers.
        # In batch mode, proceed with best guesses and note the uncertainty.

    return context
```

Context Discovery replaces the manual sprint config. The loop figures out the "how" from the "what."

### 4.4 PRD Feasibility Critique (Opus)

Before generating a plan, Opus aggressively critiques the PRD — now with the benefit of the discovered context:

- Is this achievable with the tools and environment discovered?
- Are there implicit dependencies that aren't stated?
- Are any requirements contradictory?
- Is the scope reasonable?
- Does the deliverable type match what the Vision actually describes?

```python
def critique_prd(config: LoopConfig, state: LoopState, claude: Claude) -> dict:
    """
    Opus aggressively critiques the PRD before we commit to execution.
    Uses the discovered SprintContext to ground the critique in reality.

    This gate can:
    - APPROVE: PRD is achievable, proceed to planning
    - AMEND: PRD needs changes (Opus suggests specific amendments)
    - DESCOPE: PRD is too large, suggests what to cut
    - REJECT: PRD is infeasible (missing APIs, impossible requirements)

    Result arrives via report_critique structured tool call → handle_critique
    stores it in state.agent_results["critique"] (same pattern as VRC, research, etc.)
    """
    session = claude.session(AgentRole.REASONER,
        system_extra="You are a ruthlessly honest reviewer. "
        "Your job is to prevent wasted effort by catching infeasible "
        "requirements BEFORE work begins. Be aggressive in your critique."
    )

    prompt = load_prompt("prd_critique").format(
        VISION=config.vision_file.read_text(),
        PRD=config.prd_file.read_text(),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )

    response = session.send(prompt)
    # Result arrives via report_critique tool call → handle_critique sets state.agent_results["critique"]
    return state.agent_results["critique"]  # {verdict, reason, amendments, descope_suggestions}
```

If the PRD critique suggests amendments, those are applied and the critique re-runs. If it rejects, the loop reports why and exits cleanly.

### 4.5 Plan Generation (Opus)

Opus generates the plan, but unlike V2, the output is **structured tasks, not a markdown file**.

The plan agent uses the `manage_task` tool (action: "add") to create each task with typed fields (description, value, acceptance, dependencies, phase, files_expected). The orchestrator captures these tool calls and populates `state.tasks`. After all tasks are created, `render_plan_markdown(state)` generates IMPLEMENTATION_PLAN.md as a human-readable snapshot.

Key differences from V2:
1. Opus generates the plan (not Sonnet)
2. The plan includes a **verification strategy** — not just "what to build" but "how will we know it works"
3. Plan output is structured tool calls, not prose — eliminates parsing ambiguity
4. IMPLEMENTATION_PLAN.md is written once as a snapshot, never edited by agents during the value loop

### 4.6 Quality Gates (Opus)

All quality gates from V2, run in sequence with auto-remediation. Each uses Opus because these are reasoning tasks.

**Structured remediation**: When a gate finds issues, the gate agent uses the `manage_task` tool (action: add/modify/remove) to fix the plan — it never edits IMPLEMENTATION_PLAN.md directly. After each gate completes, the markdown is re-rendered from state.

| # | Gate | Purpose | Structured Tools Used |
|---|------|---------|----------------------|
| 1 | CRAAP | Critique, Risk, Analyse flow, Alignment, Perspective | `manage_task` |
| 2 | CLARITY | Eliminate ambiguity — two-developer test | `manage_task` (modify acceptance) |
| 3 | VALIDATE | Completeness — every requirement has tasks | `manage_task` (add gaps) |
| 4 | CONNECT | Integration — no island features | `manage_task` (add INT-* tasks) |
| 5 | BREAK | Adversarial pre-mortem — validate plan against reality (boundaries, runtime, edge cases, assumptions, kill chains) | `manage_task` |
| 6 | PRUNE | Simplification without compromise | `manage_task` |
| 7 | TIDY | Codebase preparation (Kent Beck) | `manage_task` (add PREP-* tasks) |
| 8 | Blocker Validation | Reclassify false "external" blockers | `manage_task` (modify unblock) |
| 9 | VRC-Initial | Baseline value assessment from the plan | `report_vrc` |
| 10 | Preflight | Environment ready for implementation | (deterministic, no tools) |

```python
QUALITY_GATES = [
    ("craap",     "craap",            "CRAAP Review"),
    ("clarity",   "clarity",          "CLARITY Protocol"),
    ("validate",  "validate",         "VALIDATE Sprint"),
    ("connect",   "connect",          "CONNECT Review"),
    ("break",     "break",            "BREAK"),
    ("prune",     "prune",            "PRUNE Review"),
    ("tidy",      "tidy",             "TIDY-FIRST"),
    ("blockers",  "verify_blockers",  "Blocker Validation"),
    ("vrc_init",  "vrc",              "Initial VRC"),
    ("preflight", "preflight",        "Preflight Check"),
]

def run_quality_gates(config, state, claude) -> bool:
    """Run all quality gates with auto-remediation. Returns True if all pass."""
    for gate_name, prompt_name, display_name in QUALITY_GATES:
        if state.gate_passed(gate_name):
            continue

        result = run_gate_with_remediation(
            gate_name, prompt_name, display_name,
            config, state, claude,
            max_retries=3,
        )

        # Gate agents modify state via structured tools — re-render markdown
        render_plan_snapshot(config, state)
        state.save(config.state_file)

        if not result.passed:
            print(f"  GATE FAILED: {display_name}")
            return False

    return True


def render_plan_snapshot(config: LoopConfig, state: LoopState):
    """Render IMPLEMENTATION_PLAN.md from structured state. One-way generation."""
    config.plan_file.write_text(render_plan_markdown(state))
```

### 4.7 Blocker Resolution

After quality gates, any remaining blockers are surfaced to the user as a **pre-conditions report**:

```
PRE-CONDITIONS REPORT
=====================
The following must be resolved before the loop can deliver value:

  [x] DATABASE_URL configured
  [x] Node.js installed
  [ ] GEMINI_API_KEY not found in environment
  [ ] Google OAuth credentials not configured

BLOCKED: 2 pre-conditions not met.

Options:
  1. Resolve the blockers and re-run
  2. Descope: Remove Gmail/Calendar features (reduces value to 60%)
```

The loop does NOT proceed until all pre-conditions are met (or the affected scope is explicitly descoped).

### 4.8 Pre-Loop Summary

```python
def run_preloop(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    The entire pre-loop phase. Returns True if we should enter the value loop.
    Returns False if the PRD is infeasible or blockers can't be resolved.
    """
    print("=" * 60)
    print("  PRE-LOOP: Qualifying the work")
    print("=" * 60)

    # Step 1: Inputs exist
    if not validate_inputs(config):
        return False

    # Step 2: Vision Validation (5-pass) — challenge the Vision before committing
    # If the Vision is flawed, there's no point discovering context or planning.
    if not state.gate_passed("vision_validated"):
        validation = validate_vision(config, claude)
        if validation["verdict"] == "FAIL":
            print(f"VISION FAILED VALIDATION: {validation['reason']}")
            if validation.get("critical_issues"):
                for issue in validation["critical_issues"]:
                    print(f"  - {issue}")
            print("Revise the Vision and re-run.")
            return False
        if validation["verdict"] == "CONDITIONAL":
            print(f"VISION CONDITIONAL: {validation['reason']}")
            if validation.get("suggested_revisions"):
                print("  Suggested revisions:")
                for rev in validation["suggested_revisions"]:
                    print(f"    - {rev}")
            print("  Revise the Vision, then re-run. Pass 5 will re-assess.")
            return False
        state.pass_gate("vision_validated")
        state.save(config.state_file)

    # Step 3: Context Discovery (Opus) — figure out what we're working with
    if not state.gate_passed("context_discovered"):
        state.context = discover_context(config, claude)
        state.pass_gate("context_discovered")
        state.save(config.state_file)

    # Step 4: PRD Critique (Opus) — aggressive feasibility check
    # Now informed by discovered context
    if not state.gate_passed("prd_critique"):
        critique = critique_prd(config, state, claude)
        if critique["verdict"] == "REJECT":
            print(f"PRD REJECTED: {critique['reason']}")
            print("Resolve the issues and re-run.")
            return False
        if critique["verdict"] == "AMEND":
            print(f"PRD amended: {critique['amendments']}")
            # Amendments are applied to PRD.md by the agent
        state.pass_gate("prd_critique")
        state.save(config.state_file)

    # Step 5: Generate plan (Opus)
    # Plan agent uses add_task tool calls → state.tasks is populated
    # Then we render IMPLEMENTATION_PLAN.md as a human-readable snapshot
    if not state.gate_passed("plan_generated"):
        generate_plan(config, state, claude)
        render_plan_snapshot(config, state)  # markdown from state
        state.pass_gate("plan_generated")
        state.save(config.state_file)

    # Step 6: Quality gates (Opus)
    if not run_quality_gates(config, state, claude):
        return False

    # Step 7: Blocker check
    if not check_blockers_resolved(config, state):
        print_preconditions_report(config, state)
        return False

    # Note: Environment preflight already runs as quality gate #9 (in Step 6).
    # No separate preflight step needed here.

    print("\n  PRE-LOOP COMPLETE — entering value delivery loop")
    state.phase = "value_loop"
    state.save(config.state_file)
    return True
```

---

## 5. The Value Loop — Decision-Driven Delivery

The heart of the algorithm. Unlike V2's phase-driven approach, this loop asks **"what should I do next?"** every iteration, based on current state.

### 5.1 The Decision Engine

```python
class Action(Enum):
    EXECUTE = "execute"                      # Execute next task (Builder agent)
    GENERATE_QC = "generate_qc"              # Generate QC checks (QC agent)
    RUN_QC = "run_qc"                        # Run QC suite — tests, lint, types (QC agent)
    FIX = "fix"                              # Fix failing QC checks
    CRITICAL_EVAL = "critical_eval"          # Evaluate experience as real user (Evaluator agent, Opus)
    COURSE_CORRECT = "course_correct"        # Re-plan, restructure
    RESEARCH = "research"                    # Search web/docs when built-in knowledge is insufficient
    INTERACTIVE_PAUSE = "interactive_pause"  # Human action needed — pause, instruct, verify, resume
    # Note: DESCOPE is handled within COURSE_CORRECT (§11, "descope" case).
    # It is not a top-level decision engine action — course correction decides when to descope.
    SERVICE_FIX = "service_fix"              # Fix broken services (software deliverables only)
    EXIT_GATE = "exit_gate"                  # Fresh-context final verification (inside the loop)


def decide_next_action(config: LoopConfig, state: LoopState) -> Action:
    """
    Deterministic decision engine. No LLM needed — pure state analysis.

    Priority order:
    0. Paused for human action → wait (don't burn tokens)
    1. Services down → fix services (only for software deliverables with services)
    2. Stuck → course correct (something fundamental is wrong)
    3. QC checks need generating (after enough tasks done) → generate early!
    4. Failing QC checks → fix (or research if fixes exhausted, then course correct)
    5. Task needs human action → interactive pause
    6. Pending tasks → execute next task (Builder agent)
    7. QC checks pending (not yet run) → run QC (QC agent)
    8. Time for critical evaluation → experience check (Evaluator agent)
    9. All tasks done + QC passing → exit gate (fresh-context verification)

    KEY DESIGN CHOICES:
    - QC generates EARLY (after generate_verifications_after tasks) so regression is meaningful
    - Builder, QC, and Evaluator are separate agents — builder never grades own work
    - Research before course correction — when fixes are exhausted, acquire new knowledge first
    - Exit gate is inside the loop — if it fails, gaps become tasks and loop continues
    """

    # Priority 0: If paused for human action, don't do anything
    if state.pause is not None:
        return Action.INTERACTIVE_PAUSE  # will check if human completed the action

    # Priority 1: Services must be running (only for deliverables that have services)
    if state.context.services and not all_services_healthy(config, state):
        return Action.SERVICE_FIX

    # Priority 2: Are we stuck?
    if state.is_stuck(config):
        return Action.COURSE_CORRECT

    done_count = len([t for t in state.tasks.values() if t.status == "done"])
    pending_tasks = [t for t in state.tasks.values() if t.status == "pending"]

    # Priority 3: Generate QC checks once enough work exists to verify against.
    if (not state.verifications
            and done_count >= config.generate_verifications_after
            and state.gate_passed("plan_generated")):
        return Action.GENERATE_QC

    # Priority 4: Fix failing QC checks BEFORE executing more tasks.
    failing = [v for v in state.verifications.values() if v.status == "failed"]
    if failing:
        fixable = [v for v in failing if v.attempts < config.max_fix_attempts]
        if fixable:
            return Action.FIX
        else:
            # Fix attempts exhausted — try research before course correction.
            # Maybe the knowledge is stale; search for current docs/issues.
            if not state.research_attempted_for_current_failures:
                return Action.RESEARCH
            return Action.COURSE_CORRECT  # research didn't help either

    # Priority 5: Task blocked on human action → interactive pause
    human_blocked = [t for t in state.tasks.values()
                     if t.status == "blocked" and t.blocked_reason.startswith("HUMAN_ACTION:")]
    if human_blocked:
        return Action.INTERACTIVE_PAUSE

    # Priority 6: Pending tasks remaining
    if pending_tasks:
        return Action.EXECUTE

    # Priority 7: QC checks pending (not yet run)
    pending_v = [v for v in state.verifications.values() if v.status == "pending"]
    if pending_v:
        return Action.RUN_QC

    # Priority 8: Critical evaluation due?
    # Inline check (single call site): after every N tasks, or when all QC
    # checks pass for the first time (no VRC has scored >= 0.9 yet).
    crit_eval_due = (
        state.tasks_since_last_critical_eval >= config.critical_eval_interval
        or (config.critical_eval_on_all_pass
            and all(v.status == "passed" for v in state.verifications.values() if v.status != "blocked")
            and state.verifications
            and not any(vrc.value_score >= 0.9 for vrc in state.vrc_history))
    )
    if crit_eval_due:
        return Action.CRITICAL_EVAL

    # Priority 9: All tasks done + QC passing → exit gate
    all_pass = all(v.status == "passed" for v in state.verifications.values() if v.status != "blocked")
    if all_pass and state.verifications and not pending_tasks:
        return Action.EXIT_GATE

    # Fallback
    return Action.COURSE_CORRECT
```

### 5.2 The Main Loop

```python
def run_value_loop(config: LoopConfig, state: LoopState, claude: Claude):
    """
    The closed value delivery loop.
    Iterates until exit gate confirms value delivered, or safety valve triggers.

    There is no post-loop. The exit gate is inside this loop. If it finds
    gaps, they become tasks and the loop continues. The only exit is
    verified value or budget exhaustion.
    """
    print("\n" + "=" * 60)
    print("  THE VALUE LOOP")
    print("=" * 60)

    for iteration in range(1, config.max_loop_iterations + 1):
        state.iteration = iteration

        # ── Budget check ──
        if config.token_budget and state.total_tokens_used > config.token_budget:
            print(f"TOKEN BUDGET EXHAUSTED ({state.total_tokens_used} tokens)")
            break

        # ── Decide what to do ──
        action = decide_next_action(config, state)
        print(f"\n── Iteration {iteration} ── Action: {action.value}")

        # ── Execute the action ──
        # Dispatch table replaces match block. All handlers share the same
        # signature: (config, state, claude) -> bool. EXIT_GATE is special-cased
        # because it's the only action that can terminate the loop.
        ACTION_HANDLERS = {
            Action.EXECUTE:          do_execute,
            Action.GENERATE_QC:      do_generate_qc,
            Action.RUN_QC:           do_run_qc,
            Action.FIX:              do_fix,
            Action.CRITICAL_EVAL:    do_critical_eval,
            Action.COURSE_CORRECT:   do_course_correct,
            Action.SERVICE_FIX:      do_service_fix,
            Action.RESEARCH:         do_research,
            Action.INTERACTIVE_PAUSE: do_interactive_pause,
            # Note: DESCOPE is handled within COURSE_CORRECT (§11, "descope" case)
        }

        if action == Action.EXIT_GATE:
            exit_passed = do_exit_gate(config, state, claude)
            if exit_passed:
                generate_delivery_report(config, state)
                print("\n  VALUE DELIVERED — exit gate passed")
                state.save(config.state_file)
                return  # only true exit
            progress = True  # exit gate created new tasks
        else:
            progress = ACTION_HANDLERS[action](config, state, claude)

        # ── Record progress ──
        state.record_progress(action.value, "progress" if progress else "no_progress", progress)

        # ── Process Monitor (execution pattern degradation detection) ──
        # Runs AFTER the iteration's action completes but BEFORE VRC heartbeat.
        # Layer 0+1 are free (metrics + thresholds). Layer 2 fires only on RED (~2-4 per sprint).
        if state.pause is None and action != Action.EXIT_GATE:
            maybe_run_strategy_reasoner(state, config, claude)

        # ── Plan Health Check (Layer 2) ──
        # After course correction: always run (highest-risk mutation).
        # After other actions: threshold-based (runs when enough mid-loop tasks accumulate).
        if action == Action.COURSE_CORRECT and progress:
            maybe_run_plan_health_check(config, state, claude, force=True)
        else:
            maybe_run_plan_health_check(config, state, claude)

        # ── VRC: The Heartbeat ──
        # Runs EVERY iteration (except during pause or after exit gate — don't burn tokens).
        # Exit gate runs its own fresh VRC, so skip the heartbeat VRC that iteration.
        # NOTE: run_vrc() appends to state.vrc_history internally (via tool handler
        # or fallback). Do NOT append again here — that would double-count.
        # Force full VRC after critical eval or course correction (important state
        # transitions deserve Opus-level judgment, not just Haiku metrics).
        force_full_vrc = action in (Action.CRITICAL_EVAL, Action.COURSE_CORRECT)
        if state.pause is None and action != Action.EXIT_GATE:
            vrc = run_vrc(config, state, claude, force_full=force_full_vrc)

            print(f"  VRC #{len(state.vrc_history)}: {vrc.value_score:.0%} value | "
                  f"{vrc.deliverables_verified}/{vrc.deliverables_total} deliverables | "
                  f"→ {vrc.recommendation}")

        # ── Persist state ──
        state.save(config.state_file)

    # Safety valve hit — generate report of what we managed to deliver
    print("\n  MAX ITERATIONS REACHED — generating partial delivery report")
    generate_delivery_report(config, state)
```

---

## 6. Task Execution (Builder Agent) + Continuous Regression

### 6.1 Execute a Task

```python
def do_execute(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Execute the next pending task. After completion, run regression.
    "Execute" not "implement" — the task might be writing code, writing a document,
    running a migration, configuring a system, or producing any other deliverable.
    Returns True if task completed successfully.
    """
    # Find next task (priority: tasks from critical_eval/exit_gate/vrc > plan tasks)
    task = pick_next_task(state)
    if not task:
        return False

    task.status = "in_progress"

    # Multi-turn execution session (Sonnet — Builder agent)
    # The builder executes tasks. A separate QC agent checks the work.
    session = claude.session(AgentRole.BUILDER)
    prompt = load_prompt("execute").format(
        TASK=format_task_from_state(task),   # render task fields for agent context
        PLAN_SUMMARY=render_plan_markdown(state),  # read-only context, not for editing
        PRD=config.prd_file.read_text(),
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )

    response = session.send(prompt)

    # The agent signals completion via report_task_complete tool call.
    # The tool handler populates task.files_created, task.files_modified,
    # task.completion_notes and sets task.status = "done".
    completed = task.status == "done"  # set by report_task_complete handler

    if not completed:
        # Agent didn't call report_task_complete — track retries.
        # Without a retry limit, a confused agent loops forever burning budget.
        task.retry_count = getattr(task, 'retry_count', 0) + 1
        if task.retry_count >= config.max_task_retries:
            print(f"  Task {task.task_id} failed after {task.retry_count} retries — blocking")
            task.status = "blocked"
            task.blocked_reason = "Agent failed to complete after max retries"
        else:
            task.status = "pending"  # will retry next iteration
            print(f"  Task {task.task_id} not completed (retry {task.retry_count}/{config.max_task_retries})")
        return False

    state.tasks_since_last_critical_eval += 1
    git_commit(f"loop-v3({config.sprint}): {task.task_id} - completed")

    # ── REGRESSION CHECK ──
    if config.regression_after_every_task and state.regression_baseline:
        regressions = run_regression(config, state)
        if regressions:
            print(f"  REGRESSION: {len(regressions)} tests broke after {task.task_id}")
            handle_regressions(regressions, task, config, state, claude)
            return False  # Progress negated by regression

    return True


def pick_next_task(state: LoopState) -> TaskState | None:
    """
    Pick the highest-priority pending task whose dependencies are all met.
    Tasks created by critical_eval, exit_gate, or VRC are higher priority
    than plan tasks — they represent discovered gaps in value delivery.
    """
    pending = [t for t in state.tasks.values() if t.status == "pending"]
    if not pending:
        return None

    # Filter out tasks whose dependencies haven't completed yet
    ready = [t for t in pending
             if all(state.tasks.get(dep, TaskState(task_id="")).status == "done"
                    for dep in (t.dependencies or []))]
    if not ready:
        return None  # all pending tasks are blocked on dependencies

    # Priority: exit_gate > critical_eval > vrc > course_correction > plan
    priority = {"exit_gate": 0, "critical_eval": 1, "vrc": 2, "course_correction": 3, "plan": 4}
    ready.sort(key=lambda t: priority.get(t.source, 99))
    return ready[0]
```

### 6.2 Continuous Regression

```python
def run_regression(config: LoopConfig, state: LoopState) -> list[str]:
    """
    Re-run all previously passing tests. Returns list of test IDs that now fail.
    This is CHEAP — subprocess execution, no LLM.
    """
    regressions = []

    tests_to_check = [
        state.verifications[tid] for tid in state.regression_baseline
        if tid in state.verifications and state.verifications[tid].script_path
    ]

    if not tests_to_check:
        return []

    # Run all in parallel (fast)
    results = asyncio.run(run_tests_parallel(tests_to_check, config.regression_timeout))

    for test_id, (exit_code, stdout, stderr) in results.items():
        if exit_code != 0:
            regressions.append(test_id)
            state.verifications[test_id].status = "failed"
            state.verifications[test_id].failures.append(FailureRecord(
                timestamp=datetime.now().isoformat(),
                attempt=state.verifications[test_id].attempts + 1,
                exit_code=exit_code,
                stdout=stdout[:2000],
                stderr=stderr[:2000],
                fix_applied=None,
            ))
            # Remove from baseline — it's no longer passing
            state.regression_baseline.discard(test_id)

    return regressions


def handle_regressions(regressions, causal_task, config, state, claude):
    """
    When a regression is detected, fix it immediately.
    The fix agent knows WHICH task caused the regression.
    """
    session = claude.session(AgentRole.FIXER)

    for test_id in regressions:
        test = state.verifications[test_id]
        prompt = load_prompt("fix").format(
            ROOT_CAUSE=f"Regression caused by implementing {causal_task.task_id}",
            ERROR_CONTEXT=test.last_error,
            TEST_SCRIPTS=Path(test.script_path).read_text() if test.script_path else "",
            AFFECTED_TESTS=test_id,
            FIX_SUGGESTION=f"The test {test_id} was passing before {causal_task.task_id} "
                           f"was implemented. The fix should preserve the new functionality "
                           f"while restoring the regression.",
            RESEARCH_CONTEXT=get_research_context(state),
        )

        response = session.send(prompt)

        # Re-run the regressed test
        exit_code, stdout, stderr = asyncio.run(
            run_test_script(test, config.regression_timeout // len(regressions))
        )

        if exit_code == 0:
            test.status = "passed"
            state.regression_baseline.add(test_id)
            print(f"    Regression fixed: {test_id}")
        else:
            print(f"    Regression persists: {test_id}")
```

### 6.3 Service Health + Fix (Software Deliverables Only)

For software deliverables that have services (web servers, databases, etc.), the loop must ensure they're running before any other work. Service health is the highest priority after interactive pause.

```python
def all_services_healthy(config: LoopConfig, state: LoopState) -> bool:
    """
    Check health of all services defined in SprintContext.services.
    Uses health_url (HTTP GET, expect 200) or health_type="tcp" (port open).
    Returns True if all services respond within timeout.
    """
    for name, service in state.context.services.items():
        if "health_url" in service:
            try:
                r = requests.get(service["health_url"], timeout=5)
                if r.status_code != 200:
                    return False
            except (requests.ConnectionError, requests.Timeout):
                return False
        elif service.get("health_type") == "tcp":
            port = service.get("port")
            if port and not is_port_open("localhost", port):
                return False
    return True


def do_service_fix(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Fix broken services. Uses the Builder agent to diagnose and restart.

    Strategy:
    1. Identify which services are down (from SprintContext.services)
    2. Builder agent reads service configs, logs, and startup scripts
    3. Agent fixes the issue (restart command, config fix, dependency install)
    4. Verify services are healthy after fix

    This is only for services the APPLICATION needs (postgres, redis, backend, frontend).
    Not for external services the loop can't control (third-party APIs).
    """
    session = claude.session(AgentRole.BUILDER)
    prompt = load_prompt("execute").format(
        TASK=f"Fix broken services. The following services need to be running:\n"
             + json.dumps(state.context.services, indent=2)
             + "\nDiagnose why they're down and fix them.",
        PLAN_SUMMARY="",
        PRD="",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
    )

    response = session.send(prompt)

    # Verify fix worked
    if all_services_healthy(config, state):
        git_commit(f"loop-v3({config.sprint}): Fixed broken services")
        return True

    return False
```

---

## 7. Quality Control (QC Agent) — Generate, Execute, Triage, Fix

### 7.1 Verification Generation

Verifications are generated from the plan and VISION. For software deliverables, these are executable test scripts. For documents, these might be criteria checkers. For data deliverables, these might be integrity validators. The categories and structure come from the discovered sprint context.

```python
def do_generate_qc(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Generate QC checks — test scripts, lint configs, type check commands.
    The QC agent writes them once; after that, execution is deterministic.

    QC categories are determined by the discovered context's
    verification_strategy, not hardcoded tiers. The QC agent is separate
    from the Builder — it checks the work, not does the work.
    """
    session = claude.session(AgentRole.QC)  # Sonnet — QC agent

    prompt = load_prompt("generate_verifications").format(
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PLAN=config.plan_file.read_text(),
        PRD=config.prd_file.read_text(),
        VISION=config.vision_file.read_text(),
        VERIFICATION_STRATEGY=json.dumps(state.context.verification_strategy, indent=2),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
    )

    response = session.send(prompt)

    # Discover generated verification scripts
    verify_dir = Path(".loop/verifications")
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
                if sys.platform != "win32":
                    script.chmod(0o755)

                state.verifications[v_id] = VerificationState(
                    verification_id=v_id,
                    category=category,
                    script_path=str(script),
                    requires=parse_requires(script),
                )

    state.pass_gate("verifications_generated")
    git_commit(f"loop-v3({config.sprint}): Generated verification scripts")
    return bool(state.verifications)
```

### 7.2 Verification Execution

```python
def do_run_qc(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Run pending QC checks by category. Categories gate each other —
    if health checks fail, don't run feature verifications.
    """
    progress = False

    for category in state.verification_categories:
        category_verifications = [
            v for v in state.verifications.values()
            if v.category == category and v.status == "pending"
        ]

        if not category_verifications:
            continue

        # Check if this category's dependencies are met
        if not category_deps_met(category, state, config):
            continue

        # Run all verifications in category in parallel
        results = asyncio.run(run_verifications_parallel(category_verifications, config.regression_timeout))

        passes = 0
        failures = 0

        for v_id, (exit_code, stdout, stderr) in results.items():
            v = state.verifications[v_id]
            v.attempts += 1

            if exit_code == 0:
                v.status = "passed"
                state.add_regression_pass(v_id)
                passes += 1
            else:
                v.status = "failed"
                v.failures.append(FailureRecord(
                    timestamp=datetime.now().isoformat(),
                    attempt=v.attempts,
                    exit_code=exit_code,
                    stdout=stdout[:2000],
                    stderr=stderr[:2000],
                ))
                failures += 1

        print(f"  {category}: {passes} passed, {failures} failed")

        if passes > 0:
            progress = True

        # New failures detected → reset research flag so research can
        # be attempted for these new problems (see §9.3)
        if failures > 0:
            state.research_attempted_for_current_failures = False

        # If this category has failures, don't proceed to next category
        if failures > 0:
            break

    return progress
```

### 7.3 Triage + Fix

```python
def do_fix(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Triage all current failures by root cause, then fix each root cause.
    One fix may resolve multiple test failures.
    """
    failing = {
        t.verification_id: t for t in state.verifications.values()
        if t.status == "failed" and t.attempts < config.max_fix_attempts
    }

    if not failing:
        return False

    # ── Step 1: Triage (Haiku — cheap classification) ──
    # Classifier calls report_triage → handle_triage sets state.agent_results["triage"]
    if len(failing) > 1:
        triage_failures(failing, config, state, claude)
        root_causes = state.agent_results.get("triage") or []
    else:
        test = next(iter(failing.values()))
        root_causes = [{"cause": test.last_error or "Unknown",
                        "affected_tests": [test.verification_id], "priority": 1}]

    # ── Step 2: Fix each root cause (Sonnet — multi-turn) ──
    any_fixed = False

    for rc in sorted(root_causes, key=lambda x: x.get("priority", 99)):
        print(f"  Root cause: {rc['cause']}")
        print(f"  Affects: {', '.join(rc['affected_tests'])}")

        # Inject research context if available (see §9.2)
        research_context = get_research_context(state)
        fixed = fix_root_cause(rc, state, config, claude, research_context=research_context)

        if fixed:
            any_fixed = True
            # Run regression after fix
            regressions = run_regression(config, state)
            if regressions:
                print(f"  Fix caused {len(regressions)} regressions — will address next iteration")

    return any_fixed
```

---

## 8. Critical Evaluation (Evaluator Agent) + Interactive Pause

### 8.1 Critical Evaluation — The Real User Test

This is what separates V3 from every other coding agent. QC checks correctness ("does it work?"). Critical evaluation checks experience ("is it good?"). A separate Opus agent — the Evaluator — is spawned with one job: **be the user**. The builder never grades its own homework.

```python
def do_critical_eval(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Critical evaluation. A separate Opus agent USES the deliverable the way
    a real user would, and critically evaluates the experience against the Vision.

    This is NOT running test scripts. This is NOT checking code quality.
    This is an agent actually EXPERIENCING the deliverable and judging:
    - Does it make sense? Is it intuitive?
    - Does the data flow correctly end-to-end?
    - Would a real user figure this out without documentation?
    - Does it deliver the EXPERIENCE the Vision promised, not just the function?

    Key difference from QC:
    - QC checks: "does this endpoint return 200?" / "does lint pass?"
    - Critical eval: "would anyone actually want to use this?"
    """
    state.tasks_since_last_critical_eval = 0  # reset counter

    # Opus — the Evaluator. Deliberately separate from the Builder.
    session = claude.session(AgentRole.EVALUATOR,
        system_extra="You are a demanding critical evaluator. Your job is to USE the "
        "deliverable exactly as the intended user would — not run tests, not check code, "
        "but actually EXPERIENCE it. Navigate the UI. Read the document. Run the tool. "
        "Be honest and demanding: does this deliver a GOOD experience that aligns with "
        "the Vision? Report everything: what works well, what's confusing, what's missing, "
        "what's unintuitive. The bar is excellence, not just correctness."
    )

    vision = config.vision_file.read_text()

    prompt = load_prompt("critical_eval").format(
        VISION=vision,
        TASK_SUMMARY=render_plan_markdown(state),
        VRC_HISTORY=format_vrc_history(state),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        VALUE_PROOFS=json.dumps(state.context.value_proofs, indent=2),
    )

    response = session.send(prompt)

    # ── Findings arrive via report_eval_finding tool calls ──
    # Critical/blocking findings automatically become CE-* tasks.
    new_tasks_created = len([
        t for t in state.tasks.values()
        if t.source == "critical_eval" and t.task_id.startswith(f"CE-{state.iteration}")
    ])

    if new_tasks_created > 0:
        print(f"  Critical evaluation created {new_tasks_created} new tasks")
        git_commit(f"loop-v3({config.sprint}): Critical evaluation — {new_tasks_created} issues found")
    else:
        print(f"  Critical evaluation: deliverable meets experience bar")

    return new_tasks_created > 0
```

### Critical Evaluation by Deliverable Type

The evaluator adapts to the deliverable — but always evaluates *experience*, not just function:

| Deliverable Type | What the Evaluator Does |
|---|---|
| `software` / `web_app` | Opens browser, navigates UI, completes workflows. Evaluates: intuitive? Clear? Error messages helpful? |
| `software` / `cli` | Runs tool with realistic inputs. Evaluates: output useful? Errors clear? Happy path natural? |
| `software` / `api` | Exercises endpoints as a consuming app. Evaluates: contract sensible? Responses useful? |
| `software` / `library` | Writes example code using the library. Evaluates: API ergonomic? Docs clear? |
| `document` / `report` | Reads as the intended audience. Evaluates: convincing? Actionable? Trustworthy? |
| `data` / `pipeline` | Provides input, examines output. Evaluates: serves downstream purpose? Quality sufficient? |
| `config` / `migration` | Applies config, uses the system. Evaluates: system actually behaves as intended? |

### 8.2 Interactive Pause — Human Action Needed

When the loop encounters something only a human can do, it pauses with purpose. This is not failure — it's structured collaboration.

```python
def do_interactive_pause(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Interactive Pause. The loop needs a human to do something it can't.

    Protocol:
    1. RECOGNIZE — identify the human-only action needed
    2. INSTRUCT — tell the human exactly what to do (clear, non-technical)
    3. WAIT — save state, pause execution (no token burn)
    4. VERIFY — when human signals done, verify the action worked
    5. RESUME — continue autonomous execution

    The loop front-loads work to minimize pause points. Build everything
    that doesn't need the token first. Group human actions together.
    """
    if state.pause is not None:
        # Resuming after pause — verify the human's action
        print(f"\n  Checking if human action was completed...")
        verification_passed = verify_human_action(state.pause.verification, config)

        if verification_passed:
            print(f"  Human action verified — resuming autonomous execution")
            for task in state.tasks.values():
                if task.status == "blocked" and task.blocked_reason.startswith("HUMAN_ACTION:"):
                    task.status = "pending"
                    task.blocked_reason = ""
            state.pause = None  # clear pause state
            return True
        else:
            print(f"  Action not yet completed or verification failed.")
            print(f"  Instructions: {state.pause.instructions}")
            print(f"  Press Enter when ready, or Ctrl+C to abort.")
            input()
            return False

    # First time — set up the pause
    human_blocked = [t for t in state.tasks.values()
                     if t.status == "blocked" and t.blocked_reason.startswith("HUMAN_ACTION:")]
    if not human_blocked:
        return False

    task = human_blocked[0]
    action_needed = task.blocked_reason.replace("HUMAN_ACTION:", "").strip()

    state.pause = PauseState(
        reason=action_needed,
        instructions=action_needed,
        verification=task.acceptance or "",
        requested_at=datetime.now().isoformat(),
    )

    print(f"\n  {'=' * 50}")
    print(f"  INTERACTIVE PAUSE — Human action needed")
    print(f"  {'=' * 50}")
    print(f"  {action_needed}")
    print(f"\n  Complete this action, then press Enter to continue.")

    state.save(config.state_file)
    input()
    return False  # will verify on next iteration


def verify_human_action(verification: str, config: LoopConfig) -> bool:
    """Run a verification check to confirm human action was completed."""
    if not verification:
        return True  # no verification defined — trust the human
    result = subprocess.run(verification, shell=True, capture_output=True, timeout=30)
    return result.returncode == 0
```

---

## 9. External Research (Research Agent) — Breaking Through the Knowledge Ceiling

When fix attempts are exhausted, the loop's built-in knowledge may be wrong or stale. Before course-correcting (which changes the plan), the loop tries to acquire the knowledge it's missing.

### 9.1 Research Execution

```python
def do_research(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    External research. When fix attempts are exhausted, the loop searches
    external sources for current documentation, known issues, and workarounds.

    The Research Agent is Opus with web search tools. It:
    1. Identifies the specific knowledge gap from failure history
    2. Searches broadly (web, docs, GitHub issues, changelogs)
    3. Synthesizes findings into an actionable research brief
    4. The brief is injected into the fix agent's context on next attempt

    If research finds actionable information, fix attempts are reset for
    affected verifications so the fix agent can retry with new knowledge.
    """
    # Gather failure context
    failing = {
        v.verification_id: v for v in state.verifications.values()
        if v.status == "failed" and v.attempts >= config.max_fix_attempts
    }

    if not failing:
        state.research_attempted_for_current_failures = True
        return False

    # Build research query from failure patterns
    failure_context = []
    for v_id, v in failing.items():
        failure_context.append({
            "verification": v_id,
            "last_error": v.last_error,
            "attempt_history": v.attempt_history,
            "attempts": v.attempts,
        })

    session = claude.session(AgentRole.RESEARCHER,
        system_extra="You are a research agent. Your job is to find CURRENT, "
        "ACCURATE information that the loop's built-in knowledge doesn't have. "
        "Search the web for: current library documentation, GitHub issues with "
        "the same error, changelogs showing breaking changes, Stack Overflow "
        "threads with workarounds, migration guides. Focus on what CHANGED — "
        "the loop's approach worked at some point in training data, so what's "
        "different now? Produce a focused, actionable research brief."
    )

    prompt = load_prompt("research").format(
        FAILURES=json.dumps(failure_context, indent=2),
        SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
        VISION_SUMMARY=config.vision_file.read_text()[:2000],
    )

    response = session.send(prompt)

    # Research findings arrive via report_research tool call
    if state.research_briefs and state.research_briefs[-1]["iteration"] == state.iteration:
        brief = state.research_briefs[-1]
        print(f"  Research found: {brief['topic']}")
        print(f"  Sources: {len(brief.get('sources', []))}")

        # Reset fix attempts for affected verifications so fixer can retry
        # with the research brief injected into its context
        for v_id in failing:
            state.verifications[v_id].attempts = 0  # allow retries with new knowledge

        state.research_attempted_for_current_failures = True
        return True
    else:
        print(f"  Research found no actionable information")
        state.research_attempted_for_current_failures = True

        # Last resort: ask human for insight
        if state.pause is None:
            print(f"\n  REQUESTING HUMAN INSIGHT")
            print(f"  The loop has exhausted both fixes and research.")
            print(f"  Current failures:")
            for v_id, v in failing.items():
                print(f"    - {v_id}: {v.last_error[:200] if v.last_error else 'unknown'}")
            print(f"\n  Can you provide any guidance? Press Enter to skip, or type insight:")
            insight = input().strip()
            if insight:
                state.research_briefs.append({
                    "topic": "Human insight",
                    "findings": insight,
                    "sources": ["human"],
                    "iteration": state.iteration,
                })
                # Reset fix attempts
                for v_id in failing:
                    state.verifications[v_id].attempts = 0
                return True

        return False
```

### 9.2 Research Brief Injection

When a fix agent runs after research, the research brief is included in its context:

```python
def get_research_context(state: LoopState) -> str:
    """Get all research briefs for the fix agent's context.
    Returns all briefs (not filtered per-verification) because research
    findings often apply across related failures."""
    if not state.research_briefs:
        return ""

    relevant = []
    for brief in state.research_briefs:
        relevant.append(
            f"## Research Brief: {brief['topic']}\n"
            f"Findings: {brief['findings']}\n"
            f"Sources: {', '.join(brief.get('sources', []))}\n"
        )

    if not relevant:
        return ""

    return (
        "\n\n--- EXTERNAL RESEARCH (apply this knowledge) ---\n"
        + "\n".join(relevant)
        + "\n--- END RESEARCH ---\n"
    )
```

The fix agent prompt (§7.3) includes `get_research_context()` so the fixer has access to current documentation and known workarounds that weren't in the LLM's training data.

### 9.3 Research State Reset

When new failures appear (different from what research was attempted for), the research flag resets:

```python
# In do_run_qc, after new failures are recorded:
if new_failures_detected:
    state.research_attempted_for_current_failures = False
```

---

## 10. VRC — The Heartbeat

VRC runs **every single iteration**. It's not a checkpoint — it's the loop's continuous awareness of where it stands relative to the VISION.

```python
def run_vrc(config: LoopConfig, state: LoopState, claude: Claude,
            force_full: bool = False) -> VRCSnapshot:
    """
    Vision Reality Check. Runs every iteration.

    Model routing follows Principle 3:
    - FULL VRC (every 5th iteration, first 3, after beta/course correction, exit gate):
      Uses OPUS — requires judgment about value delivery quality.
    - QUICK VRC (all other iterations):
      Uses HAIKU — just classifying metrics, no deep reasoning needed.
      "Tasks: 5/10, Tests: 3/8" → "CONTINUE" is a classification task.
    """
    # Only do a full VRC every 5 iterations, quick check otherwise
    # force_full=True used by exit gate (fresh-context VRC must always be full)
    is_full_vrc = force_full or (state.iteration % 5 == 0) or (state.iteration <= 3)

    # Opus for judgment (full VRC), Haiku for classification (quick VRC)
    if is_full_vrc:
        session = claude.session(AgentRole.REASONER,
            system_extra="You are evaluating progress toward VISION delivery. "
            "This is a FULL VRC — thoroughly assess value delivery quality."
        )
    else:
        session = claude.session(AgentRole.CLASSIFIER)  # Haiku — cheap metrics check

    # Build context from structured state (not from reading markdown files)
    context = build_vrc_context_from_state(config, state, full=is_full_vrc)

    prompt = load_prompt("vrc").format(
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        IS_FULL_VRC="FULL" if is_full_vrc else "QUICK",
        CONTEXT=context,
        ITERATION=state.iteration,
        PREVIOUS_VRC=format_latest_vrc(state),
    )

    # Capture count BEFORE send — tool handler may append during send()
    vrc_count_before = len(state.vrc_history)

    response = session.send(prompt)

    # ── VRC result arrives via report_vrc tool call ──
    # The agent calls report_vrc with structured fields:
    #   value_score, deliverables_verified, deliverables_total,
    #   gaps[], recommendation, summary
    # The tool handler creates the VRCSnapshot and any VRC-* tasks.
    # No free-text parsing needed.

    # Guard: if agent didn't call report_vrc, create a fallback snapshot
    # from metrics. This prevents crashes and ensures the heartbeat never skips.
    if len(state.vrc_history) == vrc_count_before:
        # Agent didn't call the tool — synthesize from state metrics
        done = len([t for t in state.tasks.values() if t.status == "done"])
        total = len(state.tasks) or 1
        snapshot = VRCSnapshot(
            iteration=state.iteration,
            timestamp=datetime.now().isoformat(),
            deliverables_total=total,
            deliverables_verified=done,
            deliverables_blocked=len([t for t in state.tasks.values() if t.status == "blocked"]),
            value_score=done / total,
            gaps=[],
            recommendation="CONTINUE",
            summary=f"Fallback VRC (agent didn't call report_vrc): {done}/{total} tasks done",
        )
        state.vrc_history.append(snapshot)

    return state.vrc_history[-1]


def build_vrc_context_from_state(config, state, full=False) -> str:
    """
    Build VRC context entirely from structured state.
    No markdown file reads — everything comes from state.tasks, state.verifications,
    state.progress_log, and state.vrc_history.
    """
    lines = []

    # Task progress
    done = len([t for t in state.tasks.values() if t.status == "done"])
    total = len(state.tasks)
    blocked = len([t for t in state.tasks.values() if t.status == "blocked"])
    lines.append(f"Tasks: {done}/{total} complete, {blocked} blocked")

    # Test results
    passed = len([t for t in state.verifications.values() if t.status == "passed"])
    failed = len([t for t in state.verifications.values() if t.status == "failed"])
    total_checks = len(state.verifications)
    lines.append(f"QC checks: {passed}/{total_checks} passing, {failed} failing")

    # Recent progress
    recent = state.progress_log[-5:] if state.progress_log else []
    if recent:
        lines.append("Recent actions:")
        for entry in recent:
            lines.append(f"  [{entry['iteration']}] {entry['action']}: {entry['result']}")

    # For full VRC, include task details + value proofs from state
    if full:
        lines.append("\n## Task Details:")
        for t in state.tasks.values():
            status_icon = {"done": "[x]", "blocked": "[B]", "descoped": "[~]"}.get(t.status, "[ ]")
            lines.append(f"  {status_icon} {t.task_id}: {t.description}")
            if t.value:
                lines.append(f"      Value: {t.value}")

        lines.append("\n## Value Proof Targets:")
        for proof in state.context.value_proofs:
            lines.append(f"  - {proof}")

    return "\n".join(lines)
```

### VRC Frequency Optimization

Full VRCs (Opus assesses value delivery quality) are expensive. Quick VRCs (Haiku classifies progress metrics) are cheap. The loop auto-calibrates:

| Situation | VRC Type |
|---|---|
| First 3 iterations | Full (establishing baseline) |
| Every 5th iteration | Full (periodic deep check) |
| After critical evaluation | Full (new information) |
| After course correction | Full (verify course correction helped) |
| All other iterations | Quick (metrics-based progress check) |

---

## 11. Course Correction

When the loop is stuck or the approach isn't working, it needs to fundamentally change strategy — not just retry the same thing.

```python
def do_course_correct(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Course correction. Opus analyzes WHY we're stuck and decides what to change.

    This can:
    - Restructure the plan (reorder tasks, split tasks, merge tasks)
    - Descope (remove unachievable deliverables)
    - Change approach (different implementation strategy)
    - Regenerate tests (if test approach is wrong)
    - Create new tasks to address discovered gaps
    - Flag for human intervention (if truly blocked)
    """
    session = claude.session(AgentRole.REASONER,
        system_extra="You are diagnosing WHY the value loop is stuck. "
        "Analyze the full history of attempts, identify the root cause, "
        "and recommend a concrete course correction. Be bold — if the "
        "approach is wrong, say so and suggest an alternative."
    )

    # Full history for diagnosis
    context = {
        "iteration": state.iteration,
        "iterations_without_progress": state.iterations_without_progress,
        "recent_progress": state.progress_log[-20:],
        "vrc_trend": [
            {"iteration": v.iteration, "score": v.value_score, "rec": v.recommendation}
            for v in state.vrc_history[-10:]
        ],
        "failing_tests": {
            t.verification_id: t.attempt_history
            for t in state.verifications.values() if t.status == "failed"
        },
        "blocked_tasks": {
            t.task_id: t.blocked_reason
            for t in state.tasks.values() if t.status == "blocked"
        },
    }

    prompt = load_prompt("course_correct").format(
        VISION=config.vision_file.read_text(),
        PLAN_SUMMARY=render_plan_markdown(state),  # rendered view, not source of truth
        STATE=json.dumps(context, indent=2),
    )

    # Clear stale result BEFORE sending — prevents reuse of a previous session's
    # correction if the agent fails to call report_course_correction this time.
    state.agent_results.pop("course_correction", None)

    response = session.send(prompt)

    # Result arrives via report_course_correction tool call → handle_course_correction
    # sets state.agent_results["course_correction"]. The agent also uses add_task/
    # manage_task (modify/remove) to apply plan changes during the session.
    correction = state.agent_results.get("course_correction")
    if not correction:
        return False

    # Post-correction bookkeeping (plan changes already applied by structured tools)
    match correction["action"]:
        case "restructure":
            state.iterations_without_progress = 0
            state.invalidate_tests()  # tests may need regenerating
            render_plan_snapshot(config, state)  # re-render markdown from state
            git_commit(f"loop-v3({config.sprint}): Course correction — restructured plan")
            return True

        case "descope":
            # Tasks already descoped via modify_task tool calls during session
            render_plan_snapshot(config, state)
            descoped = [t for t in state.tasks.values() if t.status == "descoped"]
            git_commit(f"loop-v3({config.sprint}): Descoped {len(descoped)} items")
            return True

        case "new_tasks":
            # Tasks already added via add_task tool calls during session
            render_plan_snapshot(config, state)
            git_commit(f"loop-v3({config.sprint}): Course correction — added new tasks")
            return True

        case "regenerate_tests":
            state.invalidate_tests()  # clears verifications, baseline, and gate flag
            return True

        case "escalate":
            print(f"\n  ESCALATION: {correction['reason']}")
            print(f"  Human intervention required.")
            return False

    return False  # no recognized correction action (stale result already cleared above)
```

### 11.1 Plan Health Check (Layer 2 — lightweight quality sweep for mid-loop mutations)

Pre-loop quality gates (CRAAP, CLARITY, VALIDATE, CONNECT, PRUNE) validate the original plan thoroughly. But mid-loop task creation — from course correction, critical eval, VRC, and exit gate — bypasses those gates. Layer 1 (deterministic guardrails in `handle_manage_task`) catches structural issues on every mutation. Layer 2 catches semantic issues that require LLM judgment: DRY violations, contradictions, SOLID principle breaches, and scope drift.

**When it runs:**
- After every course correction (always — course correction is the highest-risk mutation)
- When `mid_loop_tasks_since_health_check >= config.plan_health_after_n_tasks`

**What it checks (scoped to the delta, not the whole plan):**
- **DRY** (semantic): Do any new tasks semantically overlap with existing tasks? (Layer 1 catches lexical duplicates via Jaccard similarity; this catches semantic duplicates that use different wording.)
- **Contradictions**: Do any new tasks contradict or conflict with existing tasks?
- **SOLID**: Are new tasks well-scoped (single responsibility), not coupling unrelated concerns?
- **Dependency coherence**: Do dependencies form a sensible execution order? (Layer 1 validates existence and cycles; this checks semantic ordering.)
- **Scope drift**: Are new tasks traceable to the Vision, or are they gold-plating?

**What it does NOT do:**
- Re-run all 6 quality gates (too expensive)
- Validate the entire plan (only the delta)
- Block execution (it's advisory — it fixes or warns, doesn't halt)

```python
def maybe_run_plan_health_check(
    config: LoopConfig, state: LoopState, claude: Claude,
    force: bool = False
) -> None:
    """
    Layer 2: Lightweight Opus sweep of recently-created mid-loop tasks.
    Triggered after course correction or when enough mid-loop tasks accumulate.
    Scoped to the DELTA only — new/changed tasks since the last health check.
    """
    should_run = (
        force
        or state.mid_loop_tasks_since_health_check >= config.plan_health_after_n_tasks
    )
    if not should_run:
        return

    # Collect the delta: mid-loop tasks not yet health-checked
    mid_loop_tasks = [
        t for t in state.tasks.values()
        if t.source != "plan" and not getattr(t, "health_checked", False)
    ]
    if not mid_loop_tasks:
        state.mid_loop_tasks_since_health_check = 0
        return

    print(f"\n  PLAN HEALTH CHECK — reviewing {len(mid_loop_tasks)} mid-loop tasks")

    session = claude.session(AgentRole.REASONER,
        system_extra="You are a plan quality reviewer. Your job is to check "
        "recently-added tasks against the existing plan for quality issues. "
        "Be precise and specific. Only flag real problems — false positives waste iterations."
    )

    # Build context: delta tasks + existing plan summary
    delta_summary = "\n".join(
        f"  [{t.task_id}] (source: {t.source}) {t.description}\n"
        f"    value: {t.value}\n"
        f"    acceptance: {t.acceptance}\n"
        f"    deps: {t.dependencies}"
        for t in mid_loop_tasks
    )

    existing_summary = "\n".join(
        f"  [{t.task_id}] ({t.status}) {t.description}"
        for t in state.tasks.values()
        if t.source == "plan" and t.status not in ("descoped",)
    )

    prompt = load_prompt("plan_health_check").format(
        VISION_SUMMARY=config.vision_file.read_text()[:2000],  # first 2k chars
        EXISTING_TASKS=existing_summary,
        NEW_TASKS=delta_summary,
    )

    response = session.send(prompt)

    # The agent uses manage_task (modify/remove) to fix issues it finds.
    # It can:
    #   - Merge duplicate tasks (remove one, modify other to absorb scope)
    #   - Strengthen weak acceptance criteria (modify)
    #   - Fix broken dependencies (modify)
    #   - Flag scope drift in response text (advisory — orchestrator logs it)
    #
    # Tasks it doesn't fix are logged as warnings in progress_log.
    state.progress_log.append({
        "iteration": state.iteration,
        "action": "plan_health_check",
        "result": f"Reviewed {len(mid_loop_tasks)} mid-loop tasks",
    })

    # Mark reviewed tasks so they don't get re-checked
    for t in mid_loop_tasks:
        t.health_checked = True

    state.mid_loop_tasks_since_health_check = 0
    print(f"  Plan health check complete")
```

The health check is called from the main loop (see section 5.2): `force=True` after course correction, threshold-based after all other actions.

### 11.2 Process Monitor (Execution Pattern Degradation Detection)

Plan Health Check (§11.1) validates task **definitions** — DRY, SOLID, contradictions, scope drift. The Process Monitor validates **execution patterns** — is the loop making progress efficiently, or is it churning, plateauing, or burning budget without delivering value?

Course Correction (§11) changes **what** the loop works on. The Process Monitor changes **how** the loop works — test approach, fix strategy, execution order, triage method.

The Process Monitor has 3 layers:

**Layer 0: Metric Collectors** (runs every iteration, cost ~0)

```python
def update_process_metrics(state: LoopState, iteration_result):
    """
    Update execution pattern metrics. Runs every iteration after the action
    completes. Zero LLM cost — pure arithmetic on state data.
    """
    pm = state.process_monitor
    config = state._config  # injected reference

    # Value velocity: delta(VRC) per iteration
    vrc_scores = [v.value_score for v in state.vrc_history]
    vrc_delta = vrc_scores[-1] - vrc_scores[-2] if len(vrc_scores) >= 2 else 0
    pm.value_velocity_ema = (
        config.process_monitor_ema_alpha * vrc_delta
        + (1 - config.process_monitor_ema_alpha) * pm.value_velocity_ema
    )

    # Token efficiency: delta(VRC) per token
    tokens_this_iter = iteration_result.tokens_consumed
    efficiency = vrc_delta / max(tokens_this_iter, 1)
    pm.token_efficiency_ema = (
        config.process_monitor_ema_alpha * efficiency
        + (1 - config.process_monitor_ema_alpha) * pm.token_efficiency_ema
    )

    # CUSUM for efficiency
    target_efficiency = pm.token_efficiency_ema  # Use EMA as target
    pm.cusum_efficiency = max(0, pm.cusum_efficiency + (target_efficiency - efficiency))

    # Task churn: count fail->fix->fail transitions
    for task in state.tasks.values():
        if task.status == "failed" and getattr(task, "previous_status", None) == "in_progress":
            pm.churn_counts[task.task_id] = pm.churn_counts.get(task.task_id, 0) + 1

    # Error hash tracking
    if iteration_result.error:
        h = hash_error(iteration_result.error)
        if h not in pm.error_hashes:
            pm.error_hashes[h] = {"count": 0, "tasks": []}
        pm.error_hashes[h]["count"] += 1
        pm.error_hashes[h]["tasks"].append(iteration_result.task_id)

    # File touch tracking
    for f in iteration_result.files_modified:
        pm.file_touches[f] = pm.file_touches.get(f, 0) + 1
```

**Layer 1: Trigger Evaluation** (runs every iteration, cost ~0)

```python
def evaluate_process_triggers(state: LoopState, config: LoopConfig) -> str:
    """
    Evaluate whether execution patterns have degraded enough to invoke
    the Strategy Reasoner (Layer 2). Returns GREEN, YELLOW, or RED.
    Zero LLM cost — pure threshold checks on collected metrics.
    """
    pm = state.process_monitor
    iteration = state.iteration

    # Don't evaluate before minimum iterations
    if iteration < config.process_monitor_min_iterations:
        return "GREEN"

    # Don't evaluate during strategy change cooldown
    if iteration - pm.last_strategy_change_iteration < config.process_monitor_cooldown:
        return "GREEN"

    # Don't evaluate at 95%+ budget (not enough room to change strategy)
    budget_pct = (state.total_tokens_used / config.token_budget * 100) if config.token_budget else 0
    if budget_pct >= 95:
        return "GREEN"

    triggers = []

    # Plateau detection
    if pm.value_velocity_ema < config.pm_plateau_threshold:
        triggers.append(("plateau", "RED"))

    # Churn detection
    max_churn = max(pm.churn_counts.values(), default=0)
    if max_churn >= config.pm_churn_red:
        triggers.append(("churn", "RED"))
    elif max_churn >= config.pm_churn_yellow:
        triggers.append(("churn", "YELLOW"))

    # Error recurrence
    max_error = max((e["count"] for e in pm.error_hashes.values()), default=0)
    if max_error >= config.pm_error_recurrence:
        triggers.append(("error_recurrence", "RED"))

    # Budget-value divergence
    value_pct = (
        len([t for t in state.tasks.values() if t.status == "done"]) / max(len(state.tasks), 1) * 100
    )
    if budget_pct > 0 and value_pct > 0:
        ratio = budget_pct / value_pct
        if ratio >= config.pm_budget_value_ratio:
            triggers.append(("budget_divergence", "RED"))

    # File hotspot
    if pm.file_touches:
        max_touches = max(pm.file_touches.values())
        if max_touches > iteration * (config.pm_file_hotspot_pct / 100):
            triggers.append(("file_hotspot", "YELLOW"))

    # Determine overall status
    if any(level == "RED" for _, level in triggers):
        return "RED"
    elif any(level == "YELLOW" for _, level in triggers):
        return "YELLOW"
    return "GREEN"
```

**Layer 2: Strategy Reasoner** (Opus call, only on RED — estimated 2-4 per sprint)

```python
def maybe_run_strategy_reasoner(state: LoopState, config: LoopConfig, claude: Claude):
    """
    Process Meta-Reasoning Monitor. Runs after every iteration's action
    completes but before the VRC heartbeat.

    Three layers:
      Layer 0: Metric collection (every iteration, zero cost)
      Layer 1: Trigger evaluation (every iteration, zero cost)
      Layer 2: Strategy Reasoner (Opus, only on RED trigger — ~2-4 per sprint)

    When Layer 2 fires, it diagnoses WHY the process is degrading and
    recommends changes to HOW the loop executes — not WHAT it works on
    (that's Course Correction's job).
    """
    pm = state.process_monitor

    # Layer 0: Update metrics (always runs)
    update_process_metrics(state, state.last_iteration_result)

    # Layer 1: Evaluate triggers (always runs)
    new_status = evaluate_process_triggers(state, config)
    pm.status = new_status

    if new_status != "RED":
        return  # No LLM call needed

    # Layer 2: Invoke Strategy Reasoner (Opus)
    print(f"\n  PROCESS MONITOR — RED trigger, invoking Strategy Reasoner")

    session = claude.session(
        AgentRole.REASONER,
        system_extra=load_prompt("process_monitor",
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
            ITERATION=state.iteration,
            BUDGET_PCT=_budget_pct(state, config),
            CURRENT_STRATEGY=json.dumps(pm.current_strategy, indent=2),
            METRICS_DASHBOARD=format_metrics_dashboard(pm),
            TRIGGER_DETAILS=format_trigger_details(pm),
            EXECUTION_HISTORY=format_recent_history(state, window=10),
            CURRENT_TEST_APPROACH=pm.current_strategy["test_approach"],
            CURRENT_FIX_APPROACH=pm.current_strategy["fix_approach"],
            CURRENT_EXECUTION_ORDER=pm.current_strategy["execution_order"],
            CURRENT_MAX_FIX=pm.current_strategy["max_fix_attempts"],
            CURRENT_RESEARCH_TRIGGER=pm.current_strategy["research_trigger"],
            CURRENT_SCOPE=pm.current_strategy["scope_per_task"],
            CURRENT_TRIAGE=pm.current_strategy["error_triage"],
        ),
    )

    result = session.send(
        "Analyze the process metrics and recommend a strategy change.",
        tools=[report_strategy_change_tool],
    )

    # Apply strategy change if recommended
    if result.action == "STRATEGY_CHANGE":
        for dim, value in result.changes.items():
            pm.current_strategy[dim] = value
        pm.last_strategy_change_iteration = state.iteration
        pm.strategy_history.append({
            "iteration": state.iteration,
            "changes": result.changes,
            "reason": result.rationale,
            "pattern": result.pattern,
        })
        print(f"  Strategy changed: {result.changes}")
        print(f"  Reason: {result.rationale}")
    elif result.action == "ESCALATE":
        print(f"  Process Monitor ESCALATION: {result.rationale}")
    elif result.action == "CONTINUE":
        print(f"  Process Monitor: monitoring (re-evaluate after {result.re_evaluate_after} iterations)")
```

The Decision Engine reads `state.process_monitor.current_strategy` to determine execution parameters (max_fix_attempts, execution_order, etc.) rather than using hardcoded defaults.

---

## 12. Exit Gate — Fresh-Context Final Verification (Inside the Loop)

There is no post-loop. The exit gate is inside the value loop. When the decision engine believes all tasks are done and QC passes, it triggers the exit gate — a fresh-context, Opus-level scrutiny of the entire deliverable. If it passes, the loop exits. If it finds gaps, those become tasks and the loop continues.

```python
def do_exit_gate(config: LoopConfig, state: LoopState, claude: Claude) -> bool:
    """
    Exit gate — the only way out of the value loop.

    Fresh-context verification: Opus examines the entire deliverable against
    the Vision with no accumulated context bias. This is the most valuable
    check because it's done with clean eyes.

    If it passes → loop exits, delivery report generated.
    If it fails → gaps become tasks, loop continues.

    There is NO post-loop that can fail with no recourse. This gate IS
    inside the loop. It can fail as many times as needed.
    """
    state.exit_gate_attempts += 1
    print(f"\n  EXIT GATE (attempt #{state.exit_gate_attempts})")

    # Safety valve: don't loop forever on exit gate
    if state.exit_gate_attempts > config.max_exit_gate_attempts:
        print(f"  EXIT GATE: Max attempts ({config.max_exit_gate_attempts}) reached — generating partial report")
        return True  # force exit with partial delivery

    # 1. Full regression sweep (all QC checks)
    print("  Running full regression sweep...")
    all_checks = [v for v in state.verifications.values() if v.script_path]
    results = asyncio.run(run_tests_parallel(all_checks, config.regression_timeout * 2))

    final_passes = sum(1 for _, (code, _, _) in results.items() if code == 0)
    final_fails = sum(1 for _, (code, _, _) in results.items() if code != 0)
    print(f"  QC results: {final_passes} passed, {final_fails} failed")

    if final_fails > 0:
        print(f"  EXIT GATE FAILED — {final_fails} QC checks failing")
        # Mark them as failed so the decision engine picks them up
        for v_id, (code, stdout, stderr) in results.items():
            if code != 0:
                state.verifications[v_id].status = "failed"
        return False

    # 2. Fresh-context VRC (Opus, full — always full, exit gate demands it)
    # NOTE: run_vrc() appends to state.vrc_history internally (via tool handler
    # or fallback). Do NOT append again here — that would double-count.
    print("  Running fresh-context VRC...")
    fresh_vrc = run_vrc(config, state, claude, force_full=True)

    if fresh_vrc.recommendation != "SHIP_READY":
        print(f"  EXIT GATE FAILED — VRC says {fresh_vrc.recommendation}")
        print(f"  Gaps found: {len(fresh_vrc.gaps)}")
        # Gaps become tasks — loop continues
        for gap in fresh_vrc.gaps:
            if gap.get("suggested_task"):
                state.add_task(TaskState(
                    task_id=f"EG-{state.exit_gate_attempts}-{gap['id']}",
                    source="exit_gate",
                    description=gap["suggested_task"],
                    value=gap["description"],
                    created_at=datetime.now().isoformat(),
                ))
        return False

    # 3. Final critical evaluation (Opus — be the user one last time)
    print("  Running final critical evaluation...")
    do_critical_eval(config, state, claude)

    # Check if critical eval created new tasks
    new_tasks = [t for t in state.tasks.values()
                 if t.source == "critical_eval" and t.status == "pending"]
    if new_tasks:
        print(f"  EXIT GATE FAILED — critical evaluation found {len(new_tasks)} issues")
        return False

    # All three checks passed — value is verified
    print("  EXIT GATE PASSED — value verified with fresh context")
    git_commit(f"loop-v3({config.sprint}): Exit gate passed — value verified")
    return True


def generate_delivery_report(config: LoopConfig, state: LoopState):
    """Generate final delivery report — summary of already-verified value."""
    vrc = state.latest_vrc
    passed = len([v for v in state.verifications.values() if v.status == "passed"])
    total_v = len(state.verifications)

    report_lines = [
        f"# Delivery Report: {config.sprint}",
        f"",
        f"## Summary",
        f"- Value score: {vrc.value_score:.0%}" if vrc else "- Value score: N/A",
        f"- Tasks completed: {len([t for t in state.tasks.values() if t.status == 'done'])}/{len(state.tasks)}",
        f"- QC checks: {passed}/{total_v} passing",
        f"- Iterations: {state.iteration}",
        f"- Exit gate attempts: {state.exit_gate_attempts}",
        f"- Tokens used: {state.total_tokens_used:,}",
        f"",
        f"## Deliverables",
    ]

    for t in state.tasks.values():
        status = {"done": "DELIVERED", "descoped": "DESCOPED", "blocked": "BLOCKED"}.get(t.status, t.status)
        report_lines.append(f"- [{status}] {t.task_id}: {t.description}")
        if t.status == "descoped":
            report_lines.append(f"  Reason: {t.blocked_reason}")

    report_path = config.sprint_dir / "DELIVERY_REPORT.md"
    report_path.write_text("\n".join(report_lines))
    print(f"\n  Delivery report: {report_path}")

    git_commit(f"loop-v3({config.sprint}): Delivery complete — {vrc.value_score:.0%} value" if vrc else
               f"loop-v3({config.sprint}): Delivery complete")
```

---

## 13. The Complete Entry Point

```python
def main():
    sprint = sys.argv[1]

    config = load_loop_config(sprint)
    state = LoopState.load(config.state_file) if config.state_file.exists() else LoopState(sprint=sprint)
    claude = Claude(config, state)

    # ═══ PHASE 1: PRE-LOOP ═══
    if state.phase == "pre_loop":
        if not run_preloop(config, state, claude):
            print("\nPRE-LOOP FAILED — cannot proceed to value delivery.")
            print("Resolve the issues above and re-run.")
            sys.exit(1)

    # ═══ PHASE 2: THE VALUE LOOP (includes exit gate) ═══
    # There is no Phase 3. The exit gate is inside the value loop.
    # If the exit gate finds gaps, they become tasks and the loop continues.
    # The loop only exits when value is verified or budget is exhausted.
    if state.phase == "value_loop":
        run_value_loop(config, state, claude)

    # Exit code based on value delivery
    if state.value_delivered:
        sys.exit(0)   # success — exit gate passed
    elif state.latest_vrc and state.latest_vrc.value_score > 0.5:
        sys.exit(2)   # partial — some value delivered
    else:
        sys.exit(1)   # failure
```

---

## 14. Prompt Templates

### Key Change: Structured Tool Communication

All prompts in V3 instruct agents to communicate results via **structured tool calls**, not prose output. The prompt tells the agent which tools are available and what each does. The agent's free-text output is for reasoning/logging only — all actionable data flows through tools.

Example instruction in a prompt:
```markdown
When you find a gap, use the `manage_task` tool (action: "add") to create a new task.
Do NOT write task descriptions in your text output — use the tool.

When you're done, use the `report_vrc` tool to submit your assessment.
```

### New Prompts (V3-specific)

| Prompt | Model | Structured Tools | Purpose |
|--------|-------|------------------|---------|
| `vision_validate.md` | Opus (5 sessions) | `report_vision_validation` | 5-pass Vision challenge: extraction, force analysis, causal audit, pre-mortem, synthesis |
| `discover_context.md` | Opus | `report_discovery` | Examine Vision+PRD+codebase+environment, derive SprintContext |
| `prd_critique.md` | Opus | `report_critique` | Aggressively critique PRD feasibility before committing |
| `critical_eval.md` | Opus | `report_eval_finding`, `manage_task` | Critical evaluation — be the user, judge experience quality |
| `research.md` | Opus | `report_research` + provider tools (web) | External research — search for current docs, issues, workarounds |
| `interactive_pause.md` | Opus | `request_human_action` | Generate clear instructions for human actions |
| `exit_gate.md` | Opus | `report_vrc`, `manage_task` | Fresh-context final verification (inside the loop) |
| `course_correct.md` | Opus | `manage_task`, `report_course_correction` | Diagnose why the loop is stuck and recommend structural changes |
| `vrc.md` (rewritten) | Opus | `report_vrc`, `manage_task` | Continuous heartbeat — both full and quick modes |
| `plan_health_check.md` | Opus | `manage_task` | Lightweight quality sweep of mid-loop task mutations (DRY, SOLID, contradictions, scope drift) |
| `process_monitor.md` | Opus (REASONER) | `report_strategy_change` | Strategy Reasoner — diagnose process degradation and recommend strategy changes. Only invoked on RED trigger (~2-4 per sprint) |
| `break.md` | Opus | `manage_task` | Adversarial pre-mortem — validate plan against reality (boundaries, runtime, edge cases, assumptions, kill chains) |

### Migrated Prompts (from V2, adapted)

| Prompt | Model | Structured Tools | Changes |
|--------|-------|------------------|---------|
| `plan.md` | Opus | `manage_task` | Output is tool calls, not markdown. Added verification_strategy |
| `craap.md` | Opus | `manage_task` | Remediation via tools, not markdown edits |
| `clarity.md` | Opus | `manage_task` | Remediation via tools, not markdown edits |
| `validate.md` | Opus | `manage_task` | Gap-filling via tools, not markdown edits |
| `connect.md` | Opus | `manage_task` | Integration tasks via tools, not markdown edits |
| `prune.md` | Opus | `manage_task` | Simplification without compromise |
| `tidy.md` | Opus | `manage_task` | Prep tasks via tools, not markdown edits |
| `verify_blockers.md` | Opus | `manage_task` | Unblocking via tools |
| `preflight.md` | Opus | (none) | Deterministic check. Uses environment dict from SprintContext |
| `execute.md` | Sonnet | `report_task_complete` | Builder agent signals completion via tool, not by editing plan |
| `generate_verifications.md` | Sonnet | (file tools) | QC agent generates from verification_strategy, not hardcoded tiers |
| `triage.md` | Haiku | `report_triage` | No changes — already structured |
| `fix.md` | Sonnet | (file tools only) | Add `{RESEARCH_CONTEXT}` placeholder for research brief injection. Fix agent writes code, orchestrator re-runs tests to verify. |

---

## 15. Tools

Agents get two categories of tools: **execution tools** (interact with the filesystem/environment) and **structured output tools** (communicate results back to the orchestrator via typed JSON). This eliminates free-text parsing — the agent calls a tool with structured fields, and the orchestrator captures it directly into state.

### Execution Tools (filesystem + environment)

Available to all agents:

```python
EXECUTION_TOOLS = [
    {
        "name": "bash",
        "description": "Execute a shell command. Returns stdout, stderr, exit_code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to run"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 120},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read file contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "description": "Start line (0-indexed)"},
                "limit": {"type": "integer", "description": "Max lines to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file (creates or overwrites).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace a specific string in a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "glob_search",
        "description": "Find files matching a glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "description": "Directory to search in"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep_search",
        "description": "Search file contents with regex.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
                "glob": {"type": "string", "description": "File pattern filter"},
            },
            "required": ["pattern"],
        },
    },
]

# Provider-defined tools — web_search and web_fetch are NOT custom tools.
# They are Anthropic server-side tools (types: web_search_20250305, web_fetch_20250910).
# The API executes them server-side; results appear inline in response.content.
# They must be declared in the tools list but are NOT dispatched by execute_tool().
PROVIDER_TOOLS = [
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 5},
    {"type": "web_fetch_20250910", "name": "web_fetch", "max_size": 100_000},
]

# Read-only subset — Evaluator can inspect but not modify the deliverable
READ_ONLY_TOOLS = [t for t in EXECUTION_TOOLS if t["name"] in
    {"bash", "read_file", "glob_search", "grep_search"}]

def get_tools_for_role(role: AgentRole) -> list[dict]:
    """Return execution + provider tools appropriate for this role.
    Structured output tools are added separately per-prompt by the orchestrator."""
    match role:
        case AgentRole.RESEARCHER:
            # Full filesystem tools + web tools for external research
            return EXECUTION_TOOLS + PROVIDER_TOOLS
        case AgentRole.EVALUATOR:
            # Read-only: can inspect but not modify (prevents evaluator making changes)
            return READ_ONLY_TOOLS
        case AgentRole.CLASSIFIER:
            # No execution tools — classification is pure reasoning
            return []
        case _:
            # REASONER, BUILDER, FIXER, QC get full filesystem tools
            return EXECUTION_TOOLS
```

### Structured Output Tools (agent → orchestrator communication)

These are how agents communicate structured results. The orchestrator handles each tool call by updating `LoopState` directly — no parsing, no ambiguity.

```python
STRUCTURED_TOOLS = [
    # ── Plan management (used by planning + quality gate agents) ──
    # Single tool with action field replaces add_task, modify_task, remove_task.
    {
        "name": "manage_task",
        "description": "Add, modify, or remove a task in the implementation plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "modify", "remove"],
                },
                "task_id": {"type": "string", "description": "e.g. '1.3', 'INT-2', 'PREP-1'"},
                "reason": {"type": "string", "description": "Why this change is needed"},
                # Fields for "add":
                "description": {"type": "string", "description": "What to build (add/modify)"},
                "value": {"type": "string", "description": "Why it matters to the user (add)"},
                "prd_section": {"type": "string", "description": "Traceability: '§2.1'"},
                "acceptance": {"type": "string", "description": "How to verify it's done"},
                "dependencies": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Task IDs that must complete first",
                },
                "phase": {"type": "string", "description": "Grouping: 'foundation', 'core', etc."},
                "files_expected": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Files to create or modify",
                },
                # Fields for "modify":
                "field": {
                    "type": "string",
                    "enum": ["description", "value", "acceptance", "dependencies",
                             "phase", "status", "blocked_reason", "files_expected"],
                    "description": "Which field to change (modify only)",
                },
                "new_value": {"type": "string", "description": "New value, JSON for arrays (modify only)"},
            },
            "required": ["action", "task_id"],
        },
    },

    # ── Implementation completion (used by implement + fix agents) ──
    {
        "name": "report_task_complete",
        "description": "Signal that an implementation task is complete.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "files_created": {
                    "type": "array", "items": {"type": "string"},
                    "description": "New files created",
                },
                "files_modified": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Existing files modified",
                },
                "value_verified": {
                    "type": "string",
                    "description": "How you verified the task delivers its stated value",
                },
                "notes": {"type": "string", "description": "Any implementation notes"},
            },
            "required": ["task_id", "files_created", "files_modified"],
        },
    },

    # ── Critical evaluation (used by Evaluator agent) ──
    {
        "name": "report_eval_finding",
        "description": "Report an issue found during critical evaluation of the user experience.",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["critical", "blocking", "degraded", "polish"],
                    "description": "critical/blocking auto-create tasks",
                },
                "description": {"type": "string", "description": "What's wrong"},
                "user_impact": {"type": "string", "description": "How this affects the user"},
                "suggested_fix": {"type": "string", "description": "What should be done"},
                "evidence": {"type": "string", "description": "Error message, screenshot desc, etc."},
            },
            "required": ["severity", "description", "user_impact"],
        },
    },

    # ── VRC (used by VRC agent) ──
    {
        "name": "report_vrc",
        "description": "Submit a Vision Reality Check assessment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value_score": {
                    "type": "number", "minimum": 0, "maximum": 1,
                    "description": "0.0 to 1.0 — how much of the VISION value is delivered",
                },
                "deliverables_verified": {"type": "integer"},
                "deliverables_total": {"type": "integer"},
                "deliverables_blocked": {"type": "integer", "default": 0},
                "gaps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "description": {"type": "string"},
                            "severity": {"type": "string", "enum": ["critical", "blocking", "degraded", "polish"]},
                            "suggested_task": {"type": "string"},
                        },
                    },
                    "description": "Value gaps still remaining",
                },
                "recommendation": {
                    "type": "string",
                    "enum": ["CONTINUE", "COURSE_CORRECT", "DESCOPE", "SHIP_READY"],
                },
                "summary": {"type": "string"},
            },
            "required": ["value_score", "deliverables_verified", "deliverables_total",
                         "recommendation", "summary"],
        },
    },

    # ── Triage (used by triage agent) ──
    {
        "name": "report_triage",
        "description": "Report root cause grouping of test failures.",
        "input_schema": {
            "type": "object",
            "properties": {
                "root_causes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cause": {"type": "string"},
                            "affected_tests": {"type": "array", "items": {"type": "string"}},
                            "priority": {"type": "integer"},
                            "fix_suggestion": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["root_causes"],
        },
    },

    # ── Course Correction (used by course correction agent) ──
    {
        "name": "report_course_correction",
        "description": "Declare the type of course correction applied. Plan changes (add/modify/remove tasks) are made via their respective tools during the session; this tool declares what category of correction was performed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["restructure", "descope", "new_tasks", "regenerate_tests", "escalate"],
                    "description": "Type of correction: restructure (reorder/split), descope (remove), new_tasks (add), regenerate_tests (clear QC), escalate (human needed)",
                },
                "reason": {"type": "string", "description": "Why this correction was chosen"},
            },
            "required": ["action", "reason"],
        },
    },

    # ── Interactive Pause (used by any agent that discovers a human-only blocker) ──
    {
        "name": "request_human_action",
        "description": "Request a human action that the loop cannot perform itself (OAuth, API key, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "What the human needs to do"},
                "instructions": {"type": "string", "description": "Step-by-step instructions (non-technical)"},
                "verification_command": {
                    "type": "string",
                    "description": "Shell command to verify the action was completed (e.g., 'curl -s http://...')",
                },
                "blocked_task_id": {"type": "string", "description": "Task ID that's blocked on this action"},
            },
            "required": ["action", "instructions", "blocked_task_id"],
        },
    },

    # ── Research (used by research agent) ──
    {
        "name": "report_research",
        "description": "Submit research findings from external sources.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "What was researched"},
                "findings": {"type": "string", "description": "Actionable findings (what changed, current approach, workarounds)"},
                "sources": {
                    "type": "array", "items": {"type": "string"},
                    "description": "URLs or source descriptions",
                },
                "affected_verifications": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Verification IDs this research applies to",
                },
            },
            "required": ["topic", "findings", "sources"],
        },
    },

    # ── Context Discovery (used by discovery agent) ──
    {
        "name": "report_discovery",
        "description": "Submit discovered sprint context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deliverable_type": {
                    "type": "string",
                    "enum": ["software", "document", "data", "config", "hybrid"],
                },
                "project_type": {"type": "string", "description": "e.g. 'web_app', 'cli', 'report'"},
                "codebase_state": {
                    "type": "string",
                    "enum": ["greenfield", "brownfield", "non_code"],
                },
                "environment": {"type": "object", "description": "Discovered tools, env vars, files"},
                "services": {"type": "object", "description": "Services that need running (empty for non-software)"},
                "verification_strategy": {"type": "object", "description": "How to verify value"},
                "value_proofs": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Value proof targets from the Vision",
                },
                "unresolved_questions": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Questions that need human input",
                },
            },
            "required": ["deliverable_type", "project_type", "codebase_state", "value_proofs"],
        },
    },

    # ── Vision Validation (used by Vision Validation Pass 5 agent) ──
    {
        "name": "report_vision_validation",
        "description": "Report the result of Vision Validation (Pass 5 synthesis).",
        "input_schema": {
            "type": "object",
            "properties": {
                "verdict": {"type": "string", "enum": ["PASS", "CONDITIONAL", "FAIL"]},
                "outcome_grounded": {"type": "string", "enum": ["STRONG", "ADEQUATE", "WEAK", "CRITICAL"]},
                "adoption_realistic": {"type": "string", "enum": ["STRONG", "ADEQUATE", "WEAK", "CRITICAL"]},
                "causally_sound": {"type": "string", "enum": ["STRONG", "ADEQUATE", "WEAK", "CRITICAL"]},
                "failure_aware": {"type": "string", "enum": ["STRONG", "ADEQUATE", "WEAK", "CRITICAL"]},
                "critical_issues": {"type": "array", "items": {"type": "string"}},
                "suggested_revisions": {"type": "array", "items": {"type": "string"}},
                "kill_criteria": {"type": "array", "items": {"type": "string"}},
                "reason": {"type": "string"},
            },
            "required": ["verdict", "reason"],
        },
    },

    # ── Process Monitor (used by Strategy Reasoner agent) ──
    {
        "name": "report_strategy_change",
        "description": "Report process meta-reasoning findings and strategy change recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "enum": ["plateau", "churn", "efficiency_collapse",
                             "category_clustering", "budget_divergence", "file_hotspot"],
                    "description": "Primary degradation pattern identified",
                },
                "cause": {"type": "string", "description": "Root cause of the degradation"},
                "evidence": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Specific metrics supporting the diagnosis",
                },
                "action": {
                    "type": "string",
                    "enum": ["STRATEGY_CHANGE", "ESCALATE", "CONTINUE"],
                    "description": "STRATEGY_CHANGE (apply changes), ESCALATE (human needed), CONTINUE (wait and re-evaluate)",
                },
                "changes": {
                    "type": "object",
                    "description": "Strategy dimension changes to apply (for STRATEGY_CHANGE action)",
                },
                "rationale": {"type": "string", "description": "Why this change addresses the identified cause"},
                "re_evaluate_after": {
                    "type": "integer", "minimum": 3,
                    "description": "Iterations before next meta-reasoning check",
                },
            },
            "required": ["pattern", "cause", "evidence", "action", "rationale", "re_evaluate_after"],
        },
    },

    # ── PRD Critique (used by PRD critique agent) ──
    {
        "name": "report_critique",
        "description": "Submit PRD feasibility critique result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["APPROVE", "AMEND", "DESCOPE", "REJECT"],
                },
                "reason": {"type": "string"},
                "amendments": {
                    "type": "array", "items": {"type": "string"},
                    "description": "Specific changes needed (for AMEND verdict)",
                },
                "descope_suggestions": {
                    "type": "array", "items": {"type": "string"},
                    "description": "What to cut (for DESCOPE verdict)",
                },
            },
            "required": ["verdict", "reason"],
        },
    },
]
```

### Tool Dispatch

The orchestrator routes tool calls to handlers. Execution tools interact with the filesystem; structured tools update `LoopState`:

```python
def execute_tool(name: str, input: dict, state: LoopState,
                 task_source: str = "agent") -> str:
    """Dispatch a tool call. Structured tools update state directly.

    task_source: Set by the orchestrator to tag tasks created in this
    session with the correct provenance. The calling phase passes its
    source label ("plan", "critical_eval", "exit_gate", "vrc",
    "course_correction"). This is NOT part of the tool schema —
    agents don't set it. The orchestrator does.
    """
    match name:
        # Execution tools
        case "bash": return run_bash(input["command"], input.get("timeout", 120))
        case "read_file": return read_file(input["path"], input.get("offset"), input.get("limit"))
        case "write_file": return write_file(input["path"], input["content"])
        case "edit_file": return edit_file(input["path"], input["old_string"], input["new_string"])
        case "glob_search": return glob_search(input["pattern"], input.get("path"))
        case "grep_search": return grep_search(input["pattern"], input.get("path"), input.get("glob"))
        # NOTE: web_search and web_fetch are provider-defined tools — executed
        # server-side by Anthropic. They never reach execute_tool().

        # Structured output tools — update state, return confirmation
        case "manage_task": return handle_manage_task(input, state, task_source=task_source)
        case "report_task_complete": return handle_task_complete(input, state)
        case "report_eval_finding": return handle_eval_finding(input, state)
        case "report_vrc": return handle_vrc(input, state)
        case "report_triage": return handle_triage(input, state)
        case "request_human_action": return handle_human_action(input, state)
        case "report_research": return handle_research(input, state)
        case "report_course_correction": return handle_course_correction(input, state)
        case "report_strategy_change": return handle_strategy_change(input, state)
        case "report_discovery": return handle_discovery(input, state)
        case "report_critique": return handle_critique(input, state)
        case "report_vision_validation": return handle_vision_validation(input, state)

        case _: return f"Unknown tool: {name}"
```

### Task Mutation Guardrails (Layer 1 — deterministic, zero LLM cost)

Every `manage_task` call passes through deterministic validation before mutating state. This catches the issues that pre-loop quality gates (CRAAP, CLARITY, VALIDATE, CONNECT, PRUNE) would catch on the original plan — but cheaply, on every mutation, without re-running the full gate battery.

```python
# Similarity threshold for duplicate detection (0.0–1.0)
DUPLICATE_SIMILARITY_THRESHOLD = 0.75
# Max mid-loop tasks before requiring course correction justification
MID_LOOP_TASK_CEILING = 15

def validate_task_mutation(action: str, input: dict, state: LoopState) -> str | None:
    """
    Validate a manage_task call before applying it. Returns an error message
    string if validation fails (returned to the agent as tool_result error),
    or None if validation passes.

    This is Layer 1: deterministic guardrails. No LLM calls, runs on every
    manage_task invocation. Catches:
      - Missing required fields (CLARITY)
      - Duplicate/overlapping tasks (DRY/CRAAP)
      - Invalid dependencies (CONNECT)
      - Circular dependencies (CONNECT)
      - Scope creep (PRUNE)
    """
    task_id = input.get("task_id", "")

    if action == "add":
        # ── Required fields (CLARITY) ──
        missing = []
        if not input.get("description"):
            missing.append("description")
        if not input.get("value"):
            missing.append("value")
        if not input.get("acceptance"):
            missing.append("acceptance")
        if missing:
            return (f"Task {task_id} missing required fields: {', '.join(missing)}. "
                    f"Every task needs description, value, and acceptance criteria.")

        # ── Duplicate detection (DRY/CRAAP) ──
        new_desc = input["description"].lower()
        for existing in state.tasks.values():
            if existing.status in ("done", "descoped"):
                continue
            sim = _text_similarity(new_desc, existing.description.lower())
            if sim >= DUPLICATE_SIMILARITY_THRESHOLD:
                return (f"Task {task_id} appears to duplicate existing task "
                        f"{existing.task_id} (similarity {sim:.0%}): "
                        f"'{existing.description[:80]}'. "
                        f"Modify the existing task instead, or clarify how this differs.")

        # ── Scope creep check (PRUNE) ──
        mid_loop_tasks = [t for t in state.tasks.values()
                          if t.source != "plan" and t.status not in ("done", "descoped")]
        if len(mid_loop_tasks) >= MID_LOOP_TASK_CEILING:
            return (f"Mid-loop task ceiling ({MID_LOOP_TASK_CEILING}) reached — "
                    f"{len(mid_loop_tasks)} unfinished mid-loop tasks exist. "
                    f"Consider course correction to restructure rather than adding more tasks.")

        # ── Dependency validation (CONNECT) ──
        deps = input.get("dependencies", [])
        for dep_id in deps:
            if dep_id not in state.tasks:
                return (f"Task {task_id} depends on '{dep_id}' which doesn't exist. "
                        f"Available task IDs: {', '.join(sorted(state.tasks.keys())[:20])}")

    elif action == "modify":
        if task_id not in state.tasks:
            return f"Task {task_id} doesn't exist — cannot modify."

        field = input.get("field")
        new_value = input.get("new_value")

        if field == "dependencies":
            # Parse the new dependencies and check for circular deps
            import json as _json
            try:
                new_deps = _json.loads(new_value) if isinstance(new_value, str) else new_value
            except (ValueError, TypeError):
                new_deps = [new_value] if new_value else []

            for dep_id in new_deps:
                if dep_id not in state.tasks:
                    return f"Dependency '{dep_id}' doesn't exist."
                if _creates_circular_dep(task_id, dep_id, state):
                    return (f"Adding dependency {task_id} → {dep_id} creates a circular "
                            f"dependency chain. Restructure the dependency graph.")

    elif action == "remove":
        if task_id not in state.tasks:
            return f"Task {task_id} doesn't exist — cannot remove."
        # Check if other tasks depend on this one
        dependents = [t.task_id for t in state.tasks.values()
                      if task_id in (t.dependencies or [])]
        if dependents:
            return (f"Cannot remove {task_id} — tasks {', '.join(dependents)} depend on it. "
                    f"Update their dependencies first.")

    return None  # validation passed


def _text_similarity(a: str, b: str) -> float:
    """Cheap token-overlap similarity (Jaccard index on word sets).
    Good enough for catching obvious duplicates without NLP libraries."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _creates_circular_dep(task_id: str, new_dep_id: str, state: LoopState) -> bool:
    """DFS check: would adding task_id → new_dep_id create a cycle?"""
    visited = set()
    stack = [new_dep_id]
    while stack:
        current = stack.pop()
        if current == task_id:
            return True  # cycle detected
        if current in visited:
            continue
        visited.add(current)
        current_task = state.tasks.get(current)
        if current_task and current_task.dependencies:
            stack.extend(current_task.dependencies)
    return False


def handle_manage_task(input: dict, state: LoopState,
                      task_source: str = "agent") -> str:
    """Handle manage_task tool calls with validation guardrails.

    task_source is set by the ORCHESTRATOR (not the agent) based on which
    phase is calling. This ensures tasks have correct provenance for
    pick_next_task priority ordering and plan_health_check filtering.
    """
    action = input["action"]

    # Layer 1: deterministic validation
    error = validate_task_mutation(action, input, state)
    if error:
        return f"VALIDATION_ERROR: {error}"

    # Validation passed — apply the mutation
    match action:
        case "add":
            task = TaskState(
                task_id=input["task_id"],
                source=task_source,  # set by orchestrator, not agent
                description=input["description"],
                value=input.get("value", ""),
                acceptance=input.get("acceptance", ""),
                dependencies=input.get("dependencies", []),
                phase=input.get("phase", ""),
                files_expected=input.get("files_expected", []),
                prd_section=input.get("prd_section", ""),
                created_at=datetime.now().isoformat(),
            )
            state.add_task(task)
            state.mid_loop_tasks_since_health_check += 1
            return f"Task {task.task_id} added."

        case "modify":
            task = state.tasks[input["task_id"]]
            field, new_value = input["field"], input["new_value"]
            if field == "dependencies":
                import json as _json
                new_value = _json.loads(new_value) if isinstance(new_value, str) else new_value
            setattr(task, field, new_value)
            return f"Task {input['task_id']}.{field} updated."

        case "remove":
            del state.tasks[input["task_id"]]
            return f"Task {input['task_id']} removed."
```

---

## 16. Rendered Views — Human Readability from Structured State

JSON state is the single source of truth, but humans and LLM agents benefit from readable documents. The loop generates markdown artifacts on demand from state:

### Generated Artifacts

| Artifact | Generated From | When Rendered | Purpose |
|----------|---------------|---------------|---------|
| `IMPLEMENTATION_PLAN.md` | `state.tasks` | After pre-loop, after each quality gate, after course correction | Human review of the plan |
| `VALUE_CHECKLIST.md` | `state.vrc_history` + `state.tasks` | After each full VRC | Human review of value delivery status |
| `DELIVERY_REPORT.md` | Full state | After exit gate passes (or budget exhausted) | Final delivery summary |

### Rendering Functions (render.py)

All renderers are pure functions in `render.py` taking state as input. LoopState is a data container — it has no rendering methods.

```python
# render.py — pure functions, no state mutation
def render_plan_markdown(state: LoopState) -> str:
    """Generate IMPLEMENTATION_PLAN.md from state.tasks."""
    lines = [f"# Implementation Plan (rendered from state)\n"]
    lines.append(f"Generated: {datetime.now().isoformat()}\n")

    # Group tasks by phase
    phases = {}
    for t in state.tasks.values():
        phase = t.phase or "unphased"
        phases.setdefault(phase, []).append(t)

    for phase_name, tasks in phases.items():
        lines.append(f"\n## {phase_name.title()}\n")
        for t in sorted(tasks, key=lambda x: x.task_id):
            check = "x" if t.status == "done" else ("B" if t.status == "blocked" else " ")
            lines.append(f"- [{check}] **{t.task_id}**: {t.description}")
            if t.value:
                lines.append(f"  - Value: {t.value}")
            if t.acceptance:
                lines.append(f"  - Acceptance: {t.acceptance}")
            if t.dependencies:
                lines.append(f"  - Deps: {', '.join(t.dependencies)}")
            lines.append("")

    return "\n".join(lines)

def render_value_checklist(state: LoopState) -> str:
    """Generate VALUE_CHECKLIST.md from VRC history and task state."""
    ...

def render_delivery_report(config: LoopConfig, state: LoopState) -> str:
    """Generate DELIVERY_REPORT.md from full state."""
    ...
```

### The Flow

```
                    ┌──────────────────────┐
                    │   .loop_state.json   │  ← Single source of truth
                    │                      │
                    │  tasks: {...}         │
                    │  verifications: {...}  │
                    │  vrc_history: [...]   │
                    │  progress_log: [...]  │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                     │
          ▼                    ▼                     ▼
 IMPLEMENTATION_PLAN.md  VALUE_CHECKLIST.md   DELIVERY_REPORT.md
 (rendered snapshot)     (rendered snapshot)  (rendered snapshot)
```

### What Agents See vs What They Edit

| | Agents READ | Agents WRITE |
|---|---|---|
| VISION.md | Yes (input, never changes) | Never |
| PRD.md | Yes (may be amended in pre-loop) | Only via PRD critique |
| IMPLEMENTATION_PLAN.md | Yes (as context) | **Never** — use `manage_task` |
| VALUE_CHECKLIST.md | Never (context from state instead) | **Never** — use `report_vrc` |
| .loop_state.json | Never (orchestrator manages) | **Never** — use structured tools |
| Source code files | Yes | Yes (via file tools) |

### Why This Matters

V2's failure mode: VALIDATE agent reads IMPLEMENTATION_PLAN.md, adds a task by editing the markdown, but uses slightly wrong formatting. Later, the implement agent can't find the task because its `grep` pattern doesn't match. The task is silently skipped. Value is never delivered.

V3's approach: VALIDATE agent calls `manage_task(action="add", task_id="INT-3", description="...", value="...")`. The orchestrator adds it to `state.tasks["INT-3"]`. The implement agent picks it up from state. No formatting ambiguity, no grep failures, no silent skips.

---

## 17. Key Differences from Previous V3 Plan

| Aspect | Previous Plan | This Plan |
|--------|---------------|-----------|
| **Goal framing** | "Rewrite in Python for better testing" | "Vision-to-value delivery algorithm" |
| **Architecture** | Three phases (pre-loop→value loop→post-loop) | Two phases (pre-loop→value loop with exit gate inside) |
| **State management** | Agents edit IMPLEMENTATION_PLAN.md markdown | JSON is truth; agents use structured tools; markdown rendered from state |
| **Configuration** | Human writes sprint_config.py | Context Discovery derives everything from Vision+PRD+codebase |
| **Deliverable type** | Software only | Any deliverable: software, documents, data, configurations |
| **Pre-loop** | None (planning inside the loop) | Context Discovery + PRD critique + quality gates + blocker resolution |
| **VRC** | Two checkpoints (VRC-1, VRC-2) | Continuous heartbeat every iteration |
| **Regression** | Only between test tiers | After every task execution |
| **Quality checking** | Builder runs own tests | Separate agents: Builder (executes), QC (checks correctness), Evaluator (judges experience) |
| **Critical evaluation** | Not present | Opus agent uses the deliverable as a real user, judges experience quality |
| **Human interaction** | Loop dies on human-only blockers | Interactive Pause: instruct human, wait, verify, resume |
| **Exit verification** | Post-loop (dead end if fails) | Exit gate inside loop — if fails, gaps become tasks, loop continues |
| **Course correction** | Not present | Opus diagnoses stuck states and restructures |
| **Task creation** | Only during planning | Critical evaluation, exit gate, and VRCs can create tasks anytime (via `manage_task` tool) |
| **Agent communication** | Free text parsed with regex/grep | Structured tool calls with typed JSON schemas |
| **External knowledge** | None — relies solely on training data | Research agent searches web, reads current docs, synthesizes findings |
| **Technology** | Web app assumptions throughout | Fully agnostic — discovered from context, not configured |
| **Model routing** | Sonnet for everything | Opus for reasoning, Sonnet for execution, Haiku for triage |
| **Verification categories** | Hardcoded tiers 0-4 | Dynamic from discovered verification_strategy |
| **PRD critique** | Not present | Opus aggressively validates before committing |

---

## 18. Migration Checklist

### Foundation
- [ ] Scaffold Python project (`pyproject.toml`, package structure)
- [ ] Implement `config.py` (LoopConfig — loop behavior only, no sprint-specific config)
- [ ] Implement `state.py` (LoopState with SprintContext, rich TaskState, VerificationState, VRCSnapshot, render methods)
- [ ] Implement `discovery.py` (Context Discovery — derive SprintContext from Vision+PRD+codebase)
- [ ] Implement `claude.py` (SDK wrapper with Opus/Sonnet/Haiku routing)
- [ ] Implement `tools.py` — execution tools (bash, read, write, edit, glob, grep)
- [ ] Implement `tools.py` — structured output tools (manage_task, report_task_complete, report_vrc, report_eval_finding, report_triage, request_human_action, report_research, report_course_correction, report_strategy_change, report_critique, report_discovery, report_vision_validation)
- [ ] Implement `tools.py` — provider tool declarations (PROVIDER_TOOLS: web_search, web_fetch) and `get_tools_for_role()`
- [ ] Implement `tools.py` — tool dispatch with state mutation handlers
- [ ] Implement `render.py` (render_plan_markdown, render_value_checklist, render_delivery_report)

### Pre-Loop
- [ ] Implement `validate_vision()` in `phases/preloop.py` (5-pass Vision Validation)
- [ ] Create prompt: `vision_validate.md` (NEW — 5-pass intent/outcome challenge)
- [ ] Implement `phases/preloop.py` (input validation, context discovery, PRD critique, plan gen, quality gates)
- [ ] Create prompt: `system.md` (base system prompt — used by every agent session via `load_prompt("system")`)
- [ ] Create prompt: `discover_context.md` (NEW — derives sprint context)
- [ ] Create prompt: `prd_critique.md` (NEW — uses discovered context)
- [ ] Migrate prompt: `plan.md` (add verification_strategy, deliverable-type awareness)
- [ ] Migrate prompts: `craap.md`, `clarity.md`, `validate.md`, `connect.md`, `tidy.md`
- [ ] Create prompt: `prune.md` (NEW — simplification without compromise)
- [ ] Create prompt: `break.md` (NEW — adversarial pre-mortem, validate plan against reality)
- [ ] Migrate prompt: `verify_blockers.md`
- [ ] Migrate prompt: `preflight.md`

### Value Loop
- [ ] Implement `decision.py` (decision engine with all actions including EXIT_GATE, INTERACTIVE_PAUSE, CRITICAL_EVAL, RESEARCH)
- [ ] Implement `phases/execute.py` (Builder agent: multi-turn task execution + regression)
- [ ] Implement `phases/qc.py` (QC agent: verification generation, execution, triage, fix)
- [ ] Implement `phases/critical_eval.py` (Evaluator agent: use deliverable as real user, judge experience)
- [ ] Implement `phases/vrc.py` (continuous heartbeat)
- [ ] Implement `phases/course_correct.py` (re-planning, descoping)
- [ ] Implement `phases/research.py` (External research: web search, doc retrieval, synthesis, human insight fallback)
- [ ] Implement `phases/pause.py` (Interactive Pause: instruct, wait, verify, resume)
- [ ] Implement service health check + `do_service_fix` in `phases/execute.py` or `decision.py`
- [ ] Implement `phases/exit_gate.py` (fresh-context final verification — inside the loop)
- [ ] Rewrite prompt: `vrc.md` (full + quick modes)
- [ ] Create prompt: `critical_eval.md` (NEW — Evaluator agent: be the user, judge experience)
- [ ] Create prompt: `course_correct.md` (NEW)
- [ ] Create prompt: `research.md` (NEW — external research: identify gap, search, synthesize)
- [ ] Create prompt: `interactive_pause.md` (NEW — generate clear human instructions)
- [ ] Create prompt: `exit_gate.md` (NEW — fresh-context final verification)
- [ ] Create prompt: `plan_health_check.md` (NEW — lightweight mid-loop quality sweep)
- [ ] Implement `validate_task_mutation()` guardrails in `tools.py` (Layer 1 — deterministic)
- [ ] Implement `maybe_run_plan_health_check()` in `phases/plan_health.py` (Layer 2 — LLM sweep)
- [ ] Create `phases/process_monitor.py` with ProcessMonitorState, metric collectors, trigger evaluation, strategy reasoner
- [ ] Add process monitor config fields to LoopConfig (`process_monitor_*`, `pm_*`)
- [ ] Add ProcessMonitorState to LoopState
- [ ] Wire `maybe_run_strategy_reasoner()` into main loop (after action dispatch, before VRC heartbeat)
- [ ] Add `report_strategy_change` structured tool + `handle_strategy_change` handler
- [ ] Ensure Decision Engine reads `state.process_monitor.current_strategy` for execution parameters
- [ ] Create prompt: `process_monitor.md` (Strategy Reasoner — Opus, RED trigger only)
- [ ] Migrate prompt: `execute.md` (renamed from implement.md — output-agnostic, Builder agent)
- [ ] Rewrite prompt: `generate_verifications.md` (QC agent, verification_strategy-driven)
- [ ] Migrate prompts: `triage.md`, `fix.md`

### Integration
- [ ] Implement `main.py` (pre-loop → value loop with exit gate — no post-loop)
- [ ] Create example loop config (`example_loop_config.py` — minimal, just sprint name + overrides)
- [ ] Test on a small sprint end-to-end

### Dependencies
```toml
[project]
name = "loop-v3"
requires-python = ">=3.12"
dependencies = [
    "anthropic>=0.40.0",
    "requests>=2.31.0",   # service health checks (all_services_healthy)
]
```

---

## 19. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Vision is flawed (right execution, wrong outcome) | Entire sprint wasted | 5-pass Vision Validation before committing: extraction, force analysis, causal audit, pre-mortem, synthesis |
| Opus cost for continuous VRC | High token spend | Quick VRC mode (metrics only) on most iterations, full VRC every 5th |
| Critical evaluator makes destructive changes | Data loss | Evaluator agent gets read-only tools + specific verification commands |
| Interactive pause never resumes (human forgets) | Loop stuck | Timeout on pause; notify human; allow abort and descope |
| Exit gate loops forever (keeps finding issues) | Never exits | Max exit gate attempts (configurable, default 3); after max, generate partial report |
| Course correction loops (keeps restructuring) | Never converges | Max course corrections per sprint (configurable, default 5) |
| Mid-loop tasks bypass quality gates | DRY violations, contradictions, scope drift | Layer 1: deterministic guardrails on every manage_task (dupes, deps, fields). Layer 2: periodic Opus plan health sweep after course correction or N new tasks |
| Decision engine picks wrong action | Wasted iterations | Decision is deterministic and priority-ordered; VRC catches drift |
| Context window overflow in long sessions | Agent loses context | Track token count, summarize/restart sessions at 80% capacity |
| PRD critique too aggressive (rejects good PRDs) | Blocks valid work | Critique has "AMEND" option, not just "REJECT"; user can override |
| Regression suite grows too slow | Bottleneck on every task | Timeout budget for regression; parallel execution; skip if 0 tests |
| Technology-agnostic = too generic | Loses useful defaults | Context Discovery derives smart defaults; example configs for common project types |
| Research returns irrelevant results | Wasted tokens, wrong fix direction | Research brief reviewed by Opus for relevance; discard low-confidence findings |
| Web search unavailable or rate-limited | Research can't proceed | Graceful fallback to human insight; research is advisory, not blocking |
| Process Monitor overhead | Meta-reasoning costs more than it saves | Layered design: Layers 0-1 are free (arithmetic). Layer 2 fires 2-4 times per sprint (~$3-6, <5% overhead). Skip during first 5 iterations and after 95% budget. |
| Token budget exhausted mid-delivery | Incomplete value | Budget tracking in state; VRC frequency adapts; warn at 80% |
| Windows platform compatibility | `chmod` unavailable, shell syntax differs | Use `pathlib` for permissions; `subprocess.run(shell=False)` with list args; detect platform in preflight |
| Auth misconfiguration | First API call fails | Claude class surfaces auth errors immediately; document Claude Max setup in README |

---

## 20. Success Metrics

| Metric | V2 Baseline | V3 Target |
|--------|-------------|-----------|
| Manual debugging after loop | Hours | Zero |
| Time to detect broken service | ~15 iterations | 1 iteration (pre-check) |
| Fix agent success rate | ~20% (blind) | ~70% (with context + regression) |
| Regression detection | End of sprint (if at all) | After every task |
| Experience evaluation | Never (tests only) | Every 3 tasks (separate Evaluator agent) |
| Builder self-grading | Always (builder runs own tests) | Never (QC agent + Evaluator are separate) |
| Human blockers mid-loop | Loop dies or skips | Interactive Pause (instruct, verify, resume) |
| Final verification fails | Dead end (post-loop) | Exit gate inside loop — gaps become tasks |
| PRD feasibility check | Never | Before first line of code |
| VRC frequency | 2 per sprint | Every iteration |
| Course correction capability | None (human intervenes) | Automatic (Opus diagnoses + restructures) |
| Knowledge-limited fixes | Always (training data only) | Research agent acquires current knowledge when stale |
| Technology lock-in | Web app only | Any project type |
