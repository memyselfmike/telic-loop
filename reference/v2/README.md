# Loop V2: Value-Driven Sprint Delivery

A closed-loop autonomous system that delivers production-ready, fully tested implementations that actually work for users.

## The Core Principle

> **"The loop cannot exit until the USER gets the VALUE they were promised."**

This isn't about code completion. It's about value delivery.

## What Makes This Different

| Traditional Loop | Loop V2 |
|------------------|---------|
| "Does code compile?" | "Can user achieve their goal?" |
| "Do tests pass?" | "Does user get the intended VALUE?" |
| "Is task marked done?" | "Is the workflow actually usable?" |
| Linear: plan → build → done | Closed-loop: plan → build → verify → fix → verify... |
| Exits when tasks complete | Exits when ALL value delivered |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LOOP V2 ARCHITECTURE                             │
│                                                                          │
│  ╔═══════════════════════════════════════════════════════════════════╗  │
│  ║  VISION REALITY CHECK (VRC) - Runs throughout                     ║  │
│  ║  "Can user get the VALUE for EVERY deliverable?"                  ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│                                                                          │
│  PHASE 0: Vision & PRD ──→ Human approves                               │
│       ↓                                                                  │
│  PHASE 1: Planning ──→ CRAAP → CLARITY → VALIDATE → CONNECT → TIDY     │
│       ↓                    └──── Loop until all gates pass ────┘        │
│       ↓                                                                  │
│      VRC: "Does this plan deliver ALL the value?"                       │
│       ↓                                                                  │
│  PHASE 2: Build ──→ Implement → Test → Verify Integration              │
│       ↓                └──── Loop until task passes ────┘               │
│       ↓                                                                  │
│      VRC: "Can user get partial value yet?"                             │
│       ↓                                                                  │
│  PHASE 3: Integration ──→ Discover gaps from VISION                     │
│       │                                                                  │
│       ├──→ Gaps found? ──→ Add tasks, return to PHASE 2                │
│       │                                                                  │
│       ↓                                                                  │
│      VRC: "Does user get VALUE for EVERY deliverable?"                  │
│       │                                                                  │
│       ├──→ No? ──→ Add value/UX tasks, return to PHASE 2               │
│       │                                                                  │
│       ↓                                                                  │
│  PHASE 4: Ship ──→ All value verified, ready for production            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Ensure your sprint has VISION.md, PRD.md, ARCHITECTURE.md
ls docs/sprints/1-mvp/

# 2. Run the loop
./loop-v2/loop.sh 1-mvp

# 3. The loop will:
#    - Generate implementation plan (with quality gates)
#    - Build all tasks (with test verification)
#    - Verify value delivery (VRC checkpoints)
#    - Loop until ALL value delivered
#    - Exit only when user can achieve VISION outcome
```

## The Value Checklist

Loop V2 generates and tracks a VALUE CHECKLIST from your VISION.md:

```markdown
| # | Deliverable | Value to User | Exists | Works | VALUE |
|---|-------------|---------------|--------|-------|-------|
| 1 | [Feature 1] | [Benefit 1] | [x] | [x] | [x] |
| 2 | [Feature 2] | [Benefit 2] | [x] | [x] | [x] |
| 3 | [Feature 3] | [Benefit 3] | [x] | [x] | [x] |
...

EXIT CRITERIA: ALL rows must have [x] in ALL columns.
```

## Key Concepts

### Greenfield vs Brownfield

Loop V2 automatically adapts to your codebase state:

| Scenario | Detection | Behavior |
|----------|-----------|----------|
| **GREENFIELD** | Minimal/no existing code | Plans all features from scratch, includes setup tasks |
| **BROWNFIELD** | Existing codebase | Searches before building, only creates tasks for gaps |

The loop detects this automatically and:
- **Greenfield**: Focuses on comprehensive planning and architecture
- **Brownfield**: Verifies what exists, only builds what's missing, never rewrites working code

### Vision Reality Check (VRC)

The VRC runs at checkpoints throughout the loop, asking:

1. **After planning**: "Does this plan deliver the VISION?"
2. **During build**: "Can user get partial value yet?"
3. **After build**: "Can user achieve full VISION outcome?"
4. **Before ship**: "Would YOU use this today?"

### Value vs Function

| Level | Question | Example |
|-------|----------|---------|
| Exists | Is there code? | Route file exists |
| Works | Does it run? | Returns 200 OK |
| Functions | Does it do the thing? | Returns data |
| **VALUE** | Does user get the benefit? | User achieves their goal |

**A feature that works but doesn't deliver value is NOT COMPLETE.**

### Quality Gates (Phase 1)

Before building, the plan goes through:

- **CRAAP**: Is the plan high quality?
- **CLARITY**: Is every task unambiguous?
- **VALIDATE**: Does plan cover all PRD requirements?
- **CONNECT**: Do pieces integrate with existing system?
- **TIDY**: Is codebase prepared for changes?

### Preflight Check (Before Building)

Before building, environment is verified:

- **Credentials**: All required API keys present
- **Services**: Database, Redis, dev server running
- **Dependencies**: External services reachable
- **Tiered Testing**: Determine which test tiers can run

### E2E Testing (Before Ship)

Browser-based testing with Playwright:

- **Implementation Verification**: Do features EXIST (not 404)?
- **Critical Path**: Core user flows work end-to-end
- **Integration**: Real APIs work (not stubs!)
- **Value Delivery**: User gets promised VALUE
- **UX Quality**: Intuitive, polished experience
- **Edge Cases**: Error handling, empty states

### Regression Detection (During Loop)

The loop includes automatic regression detection to prevent fixes from breaking other things:

**Triggers:**
- **Interval**: Every 5 fixes, re-verify all passing tests
- **Random Spot Check**: ~30% chance each iteration to verify 1-2 random tests
- **Completion**: Before declaring complete, full regression sweep
- **Manual**: Can be triggered on demand

**Random Spot Checks:**

Unlike interval-based checks, spot checks add unpredictability to catch regressions faster:

```bash
# Configuration in loop.sh
SPOT_CHECK_PROBABILITY=30   # 30% chance each iteration
SPOT_CHECK_COUNT=2          # Check 2 random passing tests
```

This prevents issues where regressions could hide until the next interval check, providing earlier detection without the overhead of running all tests every iteration.

**When regressions are detected:**
1. Test is reset from `[x]` to `[ ]` (pending)
2. Regression fix task is created (`REG-[test_id]`)
3. Loop continues to fix the regression
4. Cannot complete until all regressions resolved

**Output:**
```
REGRESSION_CHECK_PASSED     # All tests still passing
REGRESSION_DETECTED         # Some tests now failing (interval check)
SPOT_CHECK_PASSED           # Random tests verified
SPOT_CHECK_REGRESSION       # Random check found failure
```

### Security Gate (Before Ship)

Before shipping, code must pass security review:

- **OWASP Top 10**: All vulnerability categories checked
- **Dependency Audit**: npm/yarn/pip security audit
- **Code Patterns**: XSS, injection, path traversal scans
- **Secrets Check**: No hardcoded credentials

Security issues are **BLOCKING** - Critical/High must be fixed before ship.

## Directory Structure

```
loop-v2/
├── README.md           # This file
├── loop.sh             # Main orchestrator (~150 lines)
├── lib/                # Modular library functions
│   ├── _init.sh        # Bootstrap (defines LOOP_ROOT)
│   ├── config.sh       # Colors, paths, constants
│   ├── state.sh        # State management for resumability
│   ├── ui.sh           # Print functions (banner, status, etc.)
│   ├── docs.sh         # Document validation
│   ├── prompts.sh      # Prompt execution with retry
│   ├── metrics.sh      # Counting functions, value checks
│   ├── git.sh          # Git operations, sensitive file checks
│   ├── branch.sh       # Branch creation/switching
│   ├── services.sh     # Vision detection, service startup
│   └── tests.sh        # Test parsing, execution, regression
├── phases/             # Phase-specific orchestration
│   ├── planning.sh     # VRC, quality gates
│   ├── service-check.sh # Service readiness phase
│   ├── testing.sh      # Main test loop
│   └── completion.sh   # Final sweep, reporting
├── prompts/
│   ├── vrc.md          # Vision Reality Check
│   ├── plan.md         # Planning phase
│   ├── craap.md        # CRAAP review gate
│   ├── clarity.md      # CLARITY protocol gate
│   ├── validate.md     # Validation gate
│   ├── connect.md      # Integration check gate
│   ├── tidy.md         # Tidy-first prep
│   ├── preflight.md    # Environment verification
│   ├── service-readiness.md # Production-ready service startup
│   ├── implement.md    # Implementation agent
│   ├── test-task.md    # Test verification agent
│   ├── regression-check.md # Regression detection
│   ├── discover.md     # Gap discovery from VISION
│   ├── blocker-check.md # Blocker classification
│   ├── e2e-test.md     # Browser-based E2E testing
│   ├── security-check.md # OWASP security review
│   └── ship.md         # Final verification
├── scripts/
│   ├── extract-deliverables.sh  # Parse VISION for deliverables
│   ├── check-value.sh           # Verify value delivery
│   └── run-vrc.sh               # Run VRC checkpoint
└── docs/
    └── DESIGN.md       # Full design document
```

### Module Dependencies

The modules are sourced in a specific order to ensure dependencies are available:

```
_init.sh       ← First: defines LOOP_ROOT
    ↓
config.sh      ← Colors, paths, constants
    ↓
state.sh       ← Uses config colors
    ↓
ui.sh          ← Uses config colors, state vars
    ↓
docs.sh        ← Uses ui.sh print_status
    ↓
prompts.sh     ← Uses ui.sh, LOOP_ROOT
    ↓
metrics.sh     ← Uses ui.sh, file paths
    ↓
git.sh         ← Uses ui.sh, SPRINT vars
    ↓
branch.sh      ← Uses config, ui.sh, SPRINT
    ↓
services.sh    ← Uses ui.sh, file paths
    ↓
tests.sh       ← Uses ui.sh, prompts.sh, file paths
    ↓
phases/*.sh    ← Use all library functions
```

## Configuration

Loop V2 is project-agnostic. Configure via environment or arguments:

```bash
# Environment variables
export SPRINT_DIR="docs/sprints/1-mvp"
export VISION_FILE="$SPRINT_DIR/VISION.md"
export PRD_FILE="$SPRINT_DIR/PRD.md"
export ARCH_FILE="$SPRINT_DIR/ARCHITECTURE.md"

# Or pass sprint name
./loop-v2/loop.sh 1-mvp
```

## Exit Conditions

The loop exits when:

1. **All deliverables verified**: Every VISION promise has [x] Exists, Works, VALUE
2. **No gaps remaining**: VRC finds no blockers to user value
3. **Quality gates passed**: All planning gates green
4. **Human can use it**: Final VRC confirms "would YOU use this today?"

### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | FULL_SUCCESS | All value delivered |
| 2 | PARTIAL_SUCCESS | Non-blocked value delivered, some features blocked |
| 1 | ERROR | Loop failed |

The loop does NOT exit just because:
- Tasks are marked complete
- Tests pass
- Code compiles
- No errors in console

## Production-Ready Principle

> **"If a user has to run manual startup scripts, it's not production-ready."**

Loop V2 enforces production-readiness:
- All required services must auto-start with the application
- No manual intervention required to run the app
- Only EXTERNAL dependencies (credentials, auth) require human action

### Service Startup Classification

| Service Status | Classification | Loop Action |
|----------------|----------------|-------------|
| Service not running, app should start it | **ARCHITECTURE_GAP** | Create fix task, implement auto-startup |
| Service not running, needs credential | **EXTERNAL_BLOCKER** | Mark [B], document in BLOCKERS.md |
| Service running | **OK** | Continue with features |

**Example:**
- Chrome CDP not running → **ARCHITECTURE_GAP** → Loop implements auto-startup
- PRINTIFY_API_KEY missing → **EXTERNAL_BLOCKER** → Mark [B], document for human

## Blocker Handling

Loop V2 distinguishes between fixable and external blockers to prevent infinite loops:

### Blocker Types

| Type | Examples | Loop Action |
|------|----------|-------------|
| **FIXABLE_CODE** | Code bugs, missing files, test failures | Retry, implement fix |
| **FIXABLE_ARCHITECTURE** | Service not auto-starting, missing bootstrap | Create startup fix task |
| **EXTERNAL_CREDENTIAL** | Missing API keys, expired tokens | Mark [B], document, continue |
| **EXTERNAL_AUTH** | Requires browser login, OAuth | Mark [B], document, continue |
| **EXTERNAL_THIRD_PARTY** | Service down, rate limited | Mark [B], document, continue |

### Critical Classification Rule

**NEVER classify a service startup issue as EXTERNAL.**

| Scenario | WRONG | CORRECT |
|----------|-------|---------|
| Chrome CDP not running | ~~BLOCKED~~ | ARCHITECTURE_GAP (fix app startup) |
| Database not connected | ~~BLOCKED~~ | ARCHITECTURE_GAP (fix app startup) |
| Redis not initialized | ~~BLOCKED~~ | ARCHITECTURE_GAP (fix app startup) |
| Missing OPENAI_API_KEY | EXTERNAL | EXTERNAL (human must provide) |

### Course Correction

When external blockers are detected:

1. **Quarantine** affected tasks (marked `[B]` in plan)
2. **Calculate** deliverable vs blocked value percentage
3. **Continue** with remaining deliverables
4. **Exit** with PARTIAL_SUCCESS when non-blocked value is delivered
5. **Document** required human actions in `BLOCKERS.md`

### BLOCKERS.md

The loop creates this file when external blockers are found:

```markdown
# External Blockers

## Active External Blockers

| ID | Blocker | Affected | Human Action |
|----|---------|----------|--------------|
| B1 | Missing API key | Publishing | Add KEY to .env |

## Quarantined Deliverables

| Deliverable | Blocked By | Value Impact |
|-------------|------------|--------------|
| Publishing | B1 | 20% |

## Deliverable Value: 80%
```

## Security

Loop V2 includes mandatory security checks to prevent shipping vulnerable code.

### Security Check Points

| When | Type | Blocking? |
|------|------|-----------|
| Every 5 iterations | Periodic scan | No (creates tasks) |
| Before Phase 4 Ship | Full security gate | **Yes - must pass** |

### OWASP Top 10 Coverage

| ID | Vulnerability | Check |
|----|---------------|-------|
| A01 | Broken Access Control | Auth on all routes |
| A02 | Cryptographic Failures | No hardcoded secrets |
| A03 | Injection | Parameterized queries, no eval |
| A04 | Insecure Design | Rate limiting, validation |
| A05 | Security Misconfiguration | No debug in prod |
| A06 | Vulnerable Components | npm/yarn audit |
| A07 | Auth Failures | Secure sessions |
| A08 | Data Integrity | Input validation |
| A09 | Logging Failures | Security event logs |
| A10 | SSRF | URL validation |

### Severity Actions

| Severity | Loop Action |
|----------|-------------|
| Critical | **BLOCK** - Must fix immediately |
| High | **BLOCK** - Must fix before ship |
| Moderate | Create remediation task, continue |
| Low | Document, optional fix |

### Automated Checks

```bash
# Dependency vulnerabilities
npm audit --production

# Hardcoded secrets
grep -rniE "password|secret|key|token" src/ | grep -v process.env

# Injection patterns
grep -rniE "query\(.*\+|exec\(|eval\(" src/

# XSS patterns
grep -rn "dangerouslySetInnerHTML" frontend/src/
```

## Version Control

Loop V2 handles git safely and atomically:

### Branch Management

```
Start Loop
    ↓
On protected branch (main/master/develop)?
    ↓ YES                    ↓ NO
Stash uncommitted        Continue
changes
    ↓
Create new branch: loop-v2/{sprint}-{timestamp}
    ↓
Work on feature branch (never on protected)
```

### Commit Strategy

| Event | Commit |
|-------|--------|
| Task completed | Atomic commit per task |
| Phase completed | Phase checkpoint commit |
| Blockers found | Commit blocker documentation |

### Safety Features

- **Protected branches**: Never commits directly to main/master/develop
- **Auto-stash**: Stashes uncommitted changes before switching branches
- **Sensitive file protection**:
  - Auto-adds patterns to .gitignore
  - Refuses to commit `.env`, `*.key`, `*secret*`, `*credential*`
  - Unstages sensitive files if accidentally added
- **Atomic commits**: Each task gets its own commit for easy revert
- **Co-authored**: Commits tagged with `Co-Authored-By: Loop-V2`

### Commit Format

```
loop-v2({sprint}): Task X.X - [task description]

Co-Authored-By: Loop-V2 <loop-v2@automated>
```

## Philosophy

> "A bridge with no on-ramps or off-ramps delivers ZERO value, no matter how well-engineered the span."

Loop V2 ensures you build the on-ramps, the span, AND the off-ramps - the complete experience that delivers value to the user.

## License

MIT
