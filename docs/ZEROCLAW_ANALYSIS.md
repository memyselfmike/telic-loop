# Zeroclaw Architecture Analysis: Learnings for Telic Loop V4

**Date:** 2026-03-04
**Source:** github.com/openagen/zeroclaw (cloned to `reference/zeroclaw/`)
**Purpose:** Extract architectural patterns from a successful lightweight autonomous agent for the next iteration of telic-loop

---

## 1. What Zeroclaw Is

Zeroclaw is a Rust-based autonomous agent framework (~210 source files) that has gained attention for reliably handling long-running processes with quality outputs. Despite its file count, the core agent loop is remarkably simple — roughly 50 lines of logic. The complexity lives in infrastructure (provider adapters, memory backends, security policies), not in decision-making.

### Core Loop (the entire algorithm)

```
for iteration in 0..max_tool_iterations:
    response = provider.chat(history, tool_specs)
    tool_calls = parse_response(response)
    if no tool_calls:
        return response       # LLM decided it's done
    results = execute_tools(tool_calls)
    history.append(results)
    # loop back — LLM decides what to do next
```

That's it. No decision engine. No phase handlers. No priority system. No state machine. The LLM itself decides what to do next through its prompts and available tools.

---

## 2. The Fundamental Architectural Difference

| Aspect | Telic Loop V3 | Zeroclaw |
|--------|--------------|----------|
| **Who decides what to do next?** | 260-line deterministic decision engine (P0-P9) | The LLM, via its system prompt and tool calls |
| **Recovery from errors** | Cascading subsystems (FIX→RESEARCH→COURSE_CORRECT→process monitor) | Error becomes text in conversation; LLM reads it and decides |
| **State management** | Monolithic JSON blob (~50 fields, 40+ interacting subsystems) | Conversation history + persistent memory store |
| **Extensibility** | Hardcoded phase handlers in Python | Trait implementations (Provider, Tool, Memory, Observer) |
| **Code quality enforcement** | 778-line code scanner creating cascading tasks | Not built-in — left to the LLM's judgment via prompts |
| **Stuck detection** | `no_progress_count` counter + process monitor + strategy reasoner | Max iterations hard cap; LLM sees repeated failures in history |
| **Security** | None | Approval gates, autonomy levels, credential scrubbing |

### The Key Insight

Telic Loop V3 tried to build intelligence *around* the LLM — a complex deterministic layer that decides what the LLM should do, monitors whether it's doing it right, and corrects it when it goes wrong. Each layer of monitoring created new failure modes that required new monitoring.

Zeroclaw builds intelligence *through* the LLM — it gives the LLM good tools, good prompts, and good guardrails, then lets the LLM drive. The system's job is infrastructure (tool execution, memory, security, history management), not decision-making.

---

## 3. Architecture Deep Dive

### 3.1 Agent Core (`src/agent/agent.rs` — 764 lines)

The `Agent` struct holds:
- Provider (LLM backend — OpenAI, Anthropic, Ollama, etc.)
- Tools registry (`Vec<Box<dyn Tool>>`)
- Memory (`Arc<dyn Memory>`)
- Security policy
- Config
- Optional observers (event hooks)

The `turn()` method is the main entry point — it loads memory context, builds the system prompt, and runs the tool-calling loop. Configuration via builder pattern (`AgentBuilder`).

### 3.2 Tool System (trait-driven)

```rust
pub trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn parameters_schema(&self) -> serde_json::Value;
    async fn execute(&self, args: Value) -> Result<ToolResult>;
    fn spec(&self) -> ToolSpec;  // For LLM registration
}
```

Tools are simple: name, description, JSON schema, execute function. Adding a new capability means implementing a trait and registering it — no cross-cutting changes to the core loop.

**Built-in tools:** shell, file_read, file_write, glob_search, memory_store/recall/forget, cron management, HTTP requests, browser, sub-agent delegation.

**Sub-agent delegation** (`delegate.rs` — 1,095 lines): Spawns child agents with depth limits (prevents infinite recursion), timeout enforcement (120s standard, 300s agentic), and tool filtering (delegates can't spawn more delegates).

### 3.3 Memory System (5 backends, same trait)

```rust
#[async_trait]
pub trait Memory: Send + Sync {
    async fn store(&self, key: &str, content: &str, category: MemoryCategory, session_id: Option<&str>) -> Result<()>;
    async fn recall(&self, query: &str, limit: usize, session_id: Option<&str>) -> Result<Vec<MemoryEntry>>;
    async fn get(&self, key: &str) -> Result<Option<MemoryEntry>>;
    async fn forget(&self, key: &str) -> Result<bool>;
    // ...
}
```

**Backends:** SQLite (hybrid vector+keyword search), Markdown (human-readable files), Postgres (enterprise), Lucid (external service with local fallback), None (disabled).

**Memory hygiene** — automatic 4-stage cleanup, throttled to once per 12 hours:
1. Archive daily logs (>7 days old)
2. Archive session files
3. Purge old archives (>30 days)
4. Prune conversation rows from SQLite

**Memory snapshots** — exports core memories to `MEMORY_SNAPSHOT.md` for Git visibility and cold-boot recovery. If `brain.db` is lost, the agent hydrates from the snapshot automatically.

**Memory during execution:**
- Before each prompt: `MemoryLoader` recalls up to 5 relevant memories, injects into system prompt
- During execution: LLM can call `memory_store`, `memory_recall`, `memory_forget` tools
- Auto-save: messages ≥20 chars saved to conversation category
- Legacy protection: filters out `assistant_resp*` keys to prevent re-injecting fabricated details

### 3.4 History Management

**Hard trimming:** When messages exceed `max_history_messages` (default 50), oldest non-system messages are removed.

**Compaction (summarization):** When history grows past threshold:
1. Extract oldest N messages
2. Truncate transcript to 12K chars
3. Summarizer LLM: "preserve preferences/decisions/facts, omit filler"
4. Summary capped at 2K chars
5. Replace compacted messages with single summary message
6. Fallback: deterministic truncation if summarizer fails

This is how zeroclaw handles long-running processes — not by managing state externally, but by keeping the conversation history manageable while preserving the essential context.

### 3.5 Security & Approval Gates

**Autonomy levels:** ReadOnly, Supervised, Full.

**Approval workflow (Supervised mode):**
1. Before risky tool execution → prompt user: `[Y]es / [N]o / [A]lways`
2. "Always" adds tool to session allowlist
3. `always_ask` config list overrides session allowlist
4. Denied tools return "Denied by user." as text — LLM sees this and adapts

**Credential scrubbing:** All tool outputs scanned for API keys, tokens, passwords before storage. First 4 chars preserved for context.

**Parallel vs sequential enforcement:** If any tool in a batch needs approval, the entire batch runs sequentially. Otherwise, parallel execution via `join_all()`.

### 3.6 Daemon Mode & Reliability

**Component supervision:** Each long-running component (gateway, channels, heartbeat, scheduler) runs in a supervised tokio task with:
- Exponential backoff on failure (2s → 4s → 8s → ... → 60s cap)
- Health marking at each cycle
- Restart count tracking
- State written to `daemon_state.json` every 5 seconds

**Heartbeat:** Reads `HEARTBEAT.md` for periodic tasks, executes them via the agent on a configurable interval (default 30 min).

**Cron scheduler:** Three schedule types (cron expression, one-shot, fixed interval), SQLite persistence, concurrent execution (default 4 parallel), retry with exponential backoff, output capped at 16KB.

---

## 4. Lessons for Telic Loop V4

### Lesson 1: Trust the LLM as Decision-Maker

**V3's mistake:** Building a deterministic decision engine (P0-P9) that tells the LLM what to do. This created a 260-line state machine surrounded by 4,241 lines of phase handlers, each with their own internal logic. The interaction effects between these subsystems are beyond human reasoning.

**Zeroclaw's approach:** The LLM reads the conversation history (including previous errors) and decides what to do next. The system provides tools and guardrails, not decisions.

**For V4:** Replace the decision engine with a well-crafted system prompt that describes the value delivery workflow. Give the LLM tools for: creating tasks, running verifications, checking progress, requesting help. Let it drive.

### Lesson 2: Errors Are Just Text

**V3's mistake:** Building cascading recovery mechanisms (FIX→RESEARCH→COURSE_CORRECT→process monitor→strategy reasoner). Each recovery layer has its own failure modes. SERVICE_FIX reporting "progress" masked stuck states for 13 iterations.

**Zeroclaw's approach:** When a tool fails, the error message becomes part of the conversation. The LLM sees "Error: mktemp not found" and reasons about it. No separate recovery subsystem needed.

**For V4:** Remove all automatic recovery mechanisms. When a verification fails, the LLM sees the failure output and decides whether to fix code, rewrite the test, or ask for help. Add a hard iteration cap as the only safety net.

### Lesson 3: Tools as the Interface, Not Phases

**V3's mistake:** Phase handlers (preloop, execute, qc, fix, critical_eval, exit_gate, etc.) that are called by the decision engine. Each phase is a monolithic function with its own state management.

**Zeroclaw's approach:** Everything is a tool. Shell commands, file operations, memory, even sub-agent delegation. The agent loop just calls `tool.execute()` and feeds the result back.

**For V4:** Express the value delivery workflow as a set of tools:
- `create_plan` — generate implementation plan from PRD
- `execute_task` — implement a single task
- `run_verification` — execute a QC script
- `check_progress` — report VRC score
- `mark_complete` — signal exit readiness
- `request_help` — pause for human input

The LLM calls these tools in whatever order makes sense for the current situation.

### Lesson 4: Trait-Driven Extensibility

**V3's mistake:** Hardcoded everything. Want to add Docker support? Modify 5 files. Want to change the QC approach? Rewrite the phase handler. Every change is cross-cutting.

**Zeroclaw's approach:** Provider, Memory, Tool, Observer, RuntimeAdapter are all traits. Adding a new LLM provider means implementing one trait. Adding a new tool means implementing one trait. No existing code changes.

**For V4:** Define traits for:
- `ValueVerifier` — how to check if value was delivered (browser eval, API tests, unit tests, manual check)
- `ProgressTracker` — how to measure progress (VRC-style scoring, test pass rate, checklist)
- `RecoveryStrategy` — what to do when stuck (ask human, try alternative, give up)

### Lesson 5: History Compaction, Not State Accumulation

**V3's mistake:** State grows monotonically via a JSON blob with 50+ fields. The loop state file for recipe-mgr-v2 was tracking every verification, every task, every fix attempt, every VRC score, every epic boundary. This state interacts in unpredictable ways.

**Zeroclaw's approach:** Conversation history IS the state. When it gets too long, summarize the old parts and keep the recent context. The LLM works from what it can see in the conversation.

**For V4:** Use conversation history as primary state. Persist only: task list, verification results, and VRC scores. Everything else (fix attempts, course corrections, research notes) lives in the conversation and gets compacted when the context fills up.

### Lesson 6: Hard Limits, Not Soft Monitors

**V3's mistake:** Soft limits with override mechanisms. The process monitor could override `max_fix_attempts` from 3 to 5. The research flag could reset. The `no_progress_count` could be masked by SERVICE_FIX reporting "progress."

**Zeroclaw's approach:** Hard caps. `max_tool_iterations` is a `for` loop bound — no overrides, no exceptions. Shell timeout is 120 seconds — process killed. Output cap is 16KB — truncated.

**For V4:** Set hard, non-overridable limits:
- Max iterations per task: 10 (not 3 with override to 5)
- Max total iterations per epic: 50
- Max total iterations per sprint: 200
- Max tokens per sprint: 2M
- When any limit is hit: stop and report, don't recover

### Lesson 7: Security Is Not Optional

**V3's mistake:** No approval gates. The loop runs fully autonomously with no safety checks on destructive operations. No credential scrubbing. No autonomy levels.

**Zeroclaw's approach:** Security by default. Approval gates for risky operations. Credential scrubbing on all tool output. Autonomy levels (ReadOnly/Supervised/Full).

**For V4:** Add approval gates for: deleting files, modifying configuration, running destructive shell commands. Scrub credentials from all state/logs. Default to Supervised mode.

### Lesson 8: Proper Daemon Architecture

**V3's mistake:** Auto-restart via crash log and shell wrapper. No health monitoring. No graceful degradation. No component isolation.

**Zeroclaw's approach:** Component supervision with exponential backoff, health registry, state file for external monitoring, graceful shutdown.

**For V4:** If the loop needs to run for hours, build proper supervision: health checks, backoff on repeated failures, state snapshots for recovery, external monitoring interface.

---

## 5. Proposed V4 Architecture (Sketch)

```
┌─────────────────────────────────────────────┐
│                  Agent Loop                  │
│                                              │
│  system_prompt = load_vision + load_prd      │
│                + load_memory + load_tools    │
│                                              │
│  for iteration in 0..max_iterations:         │
│      response = llm.chat(history, tools)     │
│      tool_calls = parse(response)            │
│      if no tool_calls: break                 │
│      results = execute(tool_calls)           │
│      history.append(results)                 │
│      if len(history) > threshold:            │
│          compact(history)                    │
│                                              │
│  return response                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│                   Tools                      │
│                                              │
│  plan_tasks(prd) → task list                 │
│  execute_task(task_id) → code changes        │
│  run_verification(script) → pass/fail        │
│  generate_verifications(tasks) → scripts     │
│  check_value(criteria) → VRC score           │
│  browser_eval(url, criteria) → findings      │
│  request_help(question) → human response     │
│  mark_epic_complete(epic_id) → gate result   │
│                                              │
│  + standard: shell, file_read, file_write,   │
│    git, memory_store, memory_recall          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│               Infrastructure                 │
│                                              │
│  Memory: SQLite with vector+keyword search   │
│  History: Compaction via summarization        │
│  Security: Approval gates, credential scrub  │
│  Limits: Hard caps on iterations/tokens      │
│  Supervision: Health checks, backoff         │
│  State: Minimal JSON (tasks + verifications) │
└─────────────────────────────────────────────┘
```

### Size Target

| Component | Lines (est.) |
|-----------|-------------|
| Agent loop | ~200 |
| Tools (8-10 domain tools) | ~800 |
| Memory + history management | ~400 |
| Security + approval | ~200 |
| State persistence (minimal) | ~150 |
| Prompts (system, tool descriptions) | ~500 |
| Config + CLI | ~200 |
| **Total** | **~2,500** |

Compare: V3 is 9,610 lines of code + 5,614 lines of prompts.

---

## 6. What V3 Got Right (Keep in V4)

Not everything in V3 was wrong. These concepts earned their keep:

| Concept | Why It Works | V4 Form |
|---------|-------------|---------|
| Vision + PRD as inputs | Clear human intent capture | System prompt context |
| Separate builder/QC agents | Builder-grades-own-homework solved | Separate tool calls or sub-agents |
| Git safety net | Branching, commits, checkpoints | Keep as infrastructure |
| Context discovery | Self-configuration from codebase | Memory-based, runs once |
| Critical evaluation | Browser-based UX eval is genuinely valuable | Tool: `browser_eval()` |
| Exit gate concept | Gaps become tasks, not dead ends | Tool: `check_exit_readiness()` |
| VRC scoring | Measuring value delivery progress | Tool: `check_value()` |

---

## 7. What to Explicitly Drop

| V3 Component | Lines | Why Drop |
|--------------|-------|----------|
| Decision engine (P0-P9) | 260 | LLM decides via prompts |
| Phase handlers | 4,241 | Replaced by tools |
| Code quality scanner | 778 | LLM's judgment via prompts |
| Process monitor | 377 | Hard limits instead |
| Coherence eval | 250 | Not actionable |
| 7 quality gates | 1,700 (prompts) | One quality check, not seven |
| Plan health checks | 75 | LLM monitors its own plan |
| VRC gap task creation | 50 | VRC scores, doesn't create work |
| Docker integration | 150 | Premature — no successful use |
| Research subsystem | 280 | LLM researches naturally via tools |
| Course correction subsystem | 300 | LLM course-corrects naturally |
| Fix cycle state machine | 200 | LLM manages fix attempts via conversation |

---

## 8. Risk Assessment

### What Could Go Wrong with V4

1. **LLM loops on the same fix** — Without a decision engine tracking fix attempts, the LLM might try the same failing approach repeatedly. Mitigation: hard iteration cap per task, and the LLM sees its own failures in history (compaction preserves error patterns).

2. **LLM forgets the plan** — After history compaction, the LLM might lose track of what it was doing. Mitigation: persistent task list accessible via tool; compaction preserves decisions and current state.

3. **Tool sprawl** — Adding tools is easy, which could lead to tool proliferation. Mitigation: enforce YAGNI — each tool must earn its place through e2e testing.

4. **Prompt engineering fragility** — More of the system's intelligence lives in prompts, making them critical. Mitigation: version prompts, test them against the same sprint inputs.

5. **Less deterministic** — V3's decision engine is deterministic and testable. V4's LLM-driven approach is inherently stochastic. Mitigation: hard limits provide deterministic safety bounds even when decisions are stochastic.

### What Should Go Right

1. **Fewer interaction effects** — No cascading subsystems means no cascading failures.
2. **Better error recovery** — The LLM can reason about errors in context, which is what LLMs are actually good at.
3. **Faster iteration** — Adding capabilities means adding a tool, not modifying 5 files.
4. **Lower token overhead** — No 150-200k token preloop tax.
5. **Actually deliverable-agnostic** — Tools don't assume web apps, ports, or uvicorn.
