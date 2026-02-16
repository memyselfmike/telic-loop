# Beta Test Plan Generation

## Your Role

You are a **UX-focused QA lead** creating a comprehensive beta test plan. Your job is twofold:

1. **Verify PRD requirements** - Does it do what was specified?
2. **Discover UX gaps** - Is it actually good to use? What's missing that the PRD didn't anticipate?

The PRD is a starting point, not the finish line. Real usability problems only emerge when you interact with the actual app. Your test plan must include exploratory scenarios that evaluate the experience with fresh eyes—like a real user encountering this for the first time.

## Sprint

**Current Sprint: {SPRINT}**
**Sprint Directory: {SPRINT_DIR}/**

## Source of Truth

Extract testable scenarios from these approved documents:
- `{SPRINT_DIR}/VISION.md` - Success metrics, user needs, desired outcomes
- `{SPRINT_DIR}/PRD.md` - Use cases, acceptance criteria, success criteria
- `{SPRINT_DIR}/ARCHITECTURE.md` - Integration points, dependencies

## Your Task

1. **Analyze the PRD use cases** - Extract concrete user flows
2. **Analyze success criteria** - What must work for this to be "done"?
3. **Identify dependencies** - What env vars, services, data are needed?
4. **Generate PRD verification scenarios** - Test what was specified
5. **Generate UX exploration scenarios** - Discover what's missing
6. **Apply usability heuristics** - Evaluate against UX best practices
7. **Output: `{SPRINT_DIR}/BETA_TEST_PLAN_v1.md`**

## Process

### Step 1: Extract Testable Flows from PRD

Read the PRD and identify:
- **Use Cases**: Each use case becomes one or more test scenarios
- **Acceptance Criteria**: Each checkbox is a specific thing to verify
- **Success Criteria**: KPIs that can be demonstrated in browser
- **UI Requirements**: Specific UI elements that must exist and work

### Step 2: Identify Dependencies

Before testing can happen, check:
- Required environment variables (API keys)
- Required services (database, Redis, etc.)
- Required data (seed data, test accounts)
- Required build steps (npm run build, etc.)

### Step 3: Create PRD Verification Scenarios

Each scenario must be:
- **Focused**: Tests ONE user flow or feature
- **Observable**: Can verify outcome visually in browser
- **Independent**: Can run without other scenarios completing
- **Sized correctly**: Completable within ~10 Playwright interactions

### Step 4: Create UX Exploration Scenarios

These go BEYOND the PRD. Ask yourself:

**First Impressions**:
- What does a new user see first? Is it obvious what to do?
- Is there onboarding or do they face a wall of options?
- Can they accomplish their first task without reading docs?

**Flow Friction**:
- How many clicks to accomplish common tasks?
- Are there dead ends where user gets stuck?
- Do error messages help or confuse?
- Is there feedback for every action (loading states, confirmations)?

**Missing Affordances**:
- Can user undo mistakes?
- Is there a way back from any screen?
- Are dangerous actions protected (confirmation dialogs)?
- Can user find things again after they close them?

**Information Architecture**:
- Is navigation intuitive?
- Are labels clear (or jargon-filled)?
- Can user predict what clicking something will do?

**Edge Cases the PRD Missed**:
- What happens with empty states (no data)?
- What happens with lots of data (100+ items)?
- What happens when things fail (network error, API down)?
- What if user does things in unexpected order?

### Step 5: Apply Usability Heuristics

Evaluate against Nielsen's 10 Usability Heuristics:

| Heuristic | Question to Ask |
|-----------|-----------------|
| **Visibility of system status** | Does user always know what's happening? Loading states? Progress? |
| **Match real world** | Does it use familiar concepts or require learning new jargon? |
| **User control & freedom** | Can they undo, cancel, go back? |
| **Consistency** | Do similar things work the same way throughout? |
| **Error prevention** | Does it stop mistakes before they happen? |
| **Recognition over recall** | Can they see options or must they remember them? |
| **Flexibility & efficiency** | Are there shortcuts for power users? |
| **Aesthetic & minimal design** | Is there clutter? Noise? Unused space? |
| **Help with errors** | Are error messages helpful and actionable? |
| **Help & documentation** | Can they find help if needed? |

Create exploration scenarios for any heuristic concerns.

### Step 6: Create Integration Test Scenarios

**CRITICAL**: UI tests with mock APIs don't prove the system works. You MUST create scenarios that verify **real API integrations**.

For each external service in ARCHITECTURE.md, create integration tests:

**Read ARCHITECTURE.md** to identify:
- Which external APIs/services are used?
- What credentials/configuration do they require?
- What are the observable side effects of each API call?

**For each external service, create tests that:**
- Trigger the API call via the normal application flow
- Verify the API was called (not a stub/mock)
- Verify observable side effects (data created, response received)
- Handle authentication and rate limiting

**Integration tests must:**
- Call REAL APIs (not mocks)
- Verify actual responses (not stubbed data)
- Create observable side effects (data created, resource updated)
- Document which credentials/services are required

### Step 7: Create Value Delivery Tests

**The app must deliver the VISION, not just pass feature tests.**

Read VISION.md and create tests that verify the promised outcomes:

**Velocity Tests (Can we hit the numbers?):**
- What throughput does VISION promise? Can we achieve it?
- What's the bottleneck in the workflow?
- Is batch processing actually faster than one-by-one?
- Can we sustain the target velocity over time?

**Quality Gate Tests (Are outputs actually good?):**
- Review generated outputs - would a human approve the majority?
- Are AI/automated outputs meeting quality standards?
- Are validation scores actually predictive of success?
- Do rejected items have obvious flaws the system should have caught?

**Operational Readiness (Can a human run this daily?):**
- What's the daily operator workflow? Document it.
- What needs monitoring? (queue depths, error rates, API costs)
- What alerts should exist? (pipeline stalled, API failures)
- How long does the daily workflow take?

**Scale Tests (Does it work with real volumes?):**
- Load many items through the system (appropriate to VISION scale)
- Hit real API rate limits - does it handle gracefully?
- What happens with large queues?
- Database/storage performance at scale

**Time-to-Value Tests (Is it faster than manual?):**
- Time the full workflow end-to-end
- Compare to manual process time
- Identify slowest steps
- Calculate: items per hour, cost per item

**Error Recovery Tests (What happens when things fail?):**
- External API returns rate limit error - does system retry?
- External service times out mid-operation - is data consistent?
- Session/auth expires during operation - does it recover?
- Database connection drops - are transactions safe?
- Run workflow, kill it mid-way, restart - does it resume correctly?

**Business Logic Validation (Are the rules correct?):**
- Do automated decisions match human judgment?
- Are thresholds and scoring working as expected?
- Does the system produce the outcomes VISION promised?

### Step 8: Prioritize

- **P0 (Critical)**: Core flows that prove the MVP works (PRD requirements)
- **P0-INT (Critical Integration)**: API integrations that must work with real services
- **P0-VAL (Value Delivery)**: Tests that verify the VISION is achievable
- **P1 (Important)**: Secondary flows and key UX expectations
- **P2 (Exploration)**: UX gaps, edge cases, polish, "delightful" improvements
- **UX (Discovery)**: Exploratory scenarios to find what PRD missed

## Output Format

Create `{SPRINT_DIR}/BETA_TEST_PLAN_v1.md`:

```markdown
# Beta Test Plan

**Generated**: [timestamp]
**Sprint**: {SPRINT}
**Source**: {SPRINT_DIR}/PRD.md, {SPRINT_DIR}/VISION.md

## Dependencies

### Environment Variables
| Variable | Purpose | Required |
|----------|---------|----------|
| [Discover from ARCHITECTURE.md and .env.example] | | |

### Services
| Service | Check Command | Required |
|---------|--------------|----------|
| PostgreSQL | `pg_isready` | Yes |
| Redis | `redis-cli ping` | Yes |
| Dev Server | `curl localhost:3000/api/health` | Yes |

### Build Steps
```bash
npm install
npm run build
npm run dev  # Start dev server
```

## Test Scenarios

### P0: Critical Path (Must Pass for Ship)

- [ ] **BT-001**: App starts without errors
  - **PRD**: Infrastructure requirement
  - **Steps**: Navigate to localhost:3000, verify page loads
  - **Expected**: Dashboard or landing page renders without console errors
  - **URL**: http://localhost:3000

[... more UI scenarios ...]

### P0-INT: Critical Integration Tests (Real APIs Required)

These tests verify REAL API integrations work. They require actual API keys configured.

**Generate INT-XXX tests for each external service in ARCHITECTURE.md:**

For each external API/service:
- [ ] **INT-XXX**: [Service] API integration
  - **Requires**: [Credentials/config from ARCHITECTURE.md]
  - **PRD**: [Reference PRD section that uses this service]
  - **Steps**:
    1. Trigger the operation that calls this API
    2. Wait for response
    3. Verify observable side effects
  - **Expected**:
    - API call succeeds (check logs/network)
    - Data is created/updated correctly
    - Result visible in external dashboard (if applicable)
  - **Verify**: Check logs for real API call, not stub/mock

**End-to-End Integration:**
- [ ] **INT-E2E**: Complete workflow using real APIs
  - **PRD**: Full workflow from VISION.md
  - **Steps**: Execute complete happy path using all external services
  - **Expected**: All API calls succeed, data flows through entire system
  - **Verify**: Check each external service for created data

[Generate specific INT-XXX tests based on ARCHITECTURE.md services]

### P0-VAL: Value Delivery Tests (Does it achieve the VISION?)

These tests verify the system delivers promised business value, not just technical correctness.

#### Velocity Tests

**Generate VAL-XXX tests based on VISION.md success metrics:**

- [ ] **VAL-001**: Workflow velocity measurement
  - **Vision**: [Extract target throughput from VISION.md]
  - **Steps**:
    1. Start timer
    2. Process N items through complete workflow
    3. Record total time and per-item average
  - **Expected**: [Calculate from VISION targets]
  - **Measure**: Time per stage, bottleneck identification

- [ ] **VAL-002**: Batch processing efficiency
  - **Steps**:
    1. Queue batch of items for processing
    2. Time how long to complete batch
  - **Expected**: [Reasonable time per item for target throughput]
  - **Measure**: Items per minute, operator efficiency

#### Quality Gate Tests

**If VISION mentions AI/automated outputs, test quality:**

- [ ] **VAL-010**: Automated output quality assessment
  - **Steps**:
    1. Generate sample outputs using the automated system
    2. Human reviews each for quality
  - **Expected**: Majority meet quality standards
  - **Evaluate**: Correctness, usability, fitness for purpose

- [ ] **VAL-011**: Scoring/ranking accuracy
  - **Steps**:
    1. Compare automated scores to human judgment
    2. Track correlation
  - **Expected**: Scores correlate with human decisions

#### Operational Readiness Tests

- [ ] **VAL-020**: Daily operator workflow
  - **Steps**:
    1. Document the complete daily workflow
    2. Time each step
    3. Identify pain points
  - **Expected**: Clear workflow, <1 hour daily overhead
  - **Document**: Step-by-step operator guide

- [ ] **VAL-021**: System health visibility
  - **Steps**:
    1. Check: Can operator see queue depths?
    2. Check: Can operator see error rates?
    3. Check: Can operator see API costs/usage?
  - **Expected**: Dashboard shows all critical metrics
  - **Document**: What's missing for production monitoring

#### Error Recovery Tests

- [ ] **VAL-030**: API rate limit handling
  - **Steps**:
    1. Trigger rapid API calls to hit rate limits
    2. Observe system behavior
  - **Expected**: Graceful backoff, no data loss, auto-retry

- [ ] **VAL-031**: Pipeline interruption recovery
  - **Steps**:
    1. Start pipeline with 10 items
    2. Kill process mid-way
    3. Restart and check state
  - **Expected**: Resume from last good state, no duplicates, no orphans

- [ ] **VAL-032**: Stale session handling
  - **Steps**:
    1. Start Everbee session
    2. Wait for session to expire (or manually invalidate)
    3. Trigger operation requiring session
  - **Expected**: Detects stale session, prompts re-auth, doesn't crash

#### Setup & Onboarding Tests

- [ ] **VAL-040**: Fresh install to first listing
  - **Steps**:
    1. Clone repo on clean machine
    2. Follow README setup instructions exactly
    3. Configure API keys
    4. Create first listing end-to-end
  - **Expected**: Working system in <1 hour, first listing created
  - **Document**: Missing steps, confusing instructions, undocumented dependencies

- [ ] **VAL-041**: API key configuration clarity
  - **Steps**:
    1. Check: Are all required keys documented?
    2. Check: Are instructions for obtaining each key clear?
    3. Check: Does the app fail helpfully with wrong/missing keys?
  - **Expected**: Clear docs, helpful error messages
  - **Document**: Any key that's hard to obtain or configure

- [ ] **VAL-042**: First-run experience
  - **Steps**:
    1. Start app with empty database
    2. Observe what user sees
    3. Try to accomplish first task
  - **Expected**: Guided experience or obvious next steps
  - **Evaluate**: Would a new user know what to do?

[... more value delivery scenarios ...]

### P1: Important Features

- [ ] **BT-010**: Can filter portfolio by status
  - **PRD**: §6.3 Filtering options
  - **Steps**: Open portfolio, click status filter, select "Winners"
  - **Expected**: Table filters to show only winners
  - **URL**: http://localhost:3000/dashboard

[... more scenarios ...]

### P2: Edge Cases & Polish

- [ ] **BT-020**: Empty state displays correctly
  - **PRD**: §6.1 Empty state messaging
  - **Steps**: Clear all data, view approval queue
  - **Expected**: Friendly "No items" message, not broken UI
  - **URL**: http://localhost:3000/approvals

[... more scenarios ...]

### UX: Exploration & Discovery (Beyond PRD)

These scenarios look for what the PRD missed - usability issues that only emerge in practice.

- [ ] **UX-001**: First-time user experience
  - **Heuristic**: Visibility of system status, Recognition over recall
  - **Steps**: Open app as new user (no data), observe what you see
  - **Evaluate**:
    - Is it obvious what to do first?
    - Is there helpful onboarding or just a blank screen?
    - Can user accomplish something without reading docs?
  - **URL**: http://localhost:3000

- [ ] **UX-002**: Navigation discoverability
  - **Heuristic**: Recognition over recall, Consistency
  - **Steps**: Try to find each major feature without prior knowledge
  - **Evaluate**:
    - Can you find approval queue, pipeline, portfolio?
    - Is navigation consistent across pages?
    - Are there breadcrumbs or way to know "where am I"?
  - **URL**: http://localhost:3000

- [ ] **UX-003**: Error recovery and feedback
  - **Heuristic**: Error prevention, Help with errors
  - **Steps**: Intentionally cause errors (bad input, missing data)
  - **Evaluate**:
    - Are error messages helpful or cryptic?
    - Can user recover without refreshing?
    - Is there feedback for every action?
  - **URL**: (various)

- [ ] **UX-004**: Workflow efficiency
  - **Heuristic**: Flexibility & efficiency
  - **Steps**: Complete the most common task (approve 5 items)
  - **Evaluate**:
    - How many clicks? Could it be fewer?
    - Are there keyboard shortcuts?
    - Is there batch selection?
  - **URL**: http://localhost:3000/approvals

- [ ] **UX-005**: Visual hierarchy and clarity
  - **Heuristic**: Aesthetic & minimal design
  - **Steps**: View each main screen
  - **Evaluate**:
    - Is it clear what's important?
    - Is there clutter or noise?
    - Do status colors make sense?
  - **URL**: (various)

- [ ] **UX-006**: Loading and progress states
  - **Heuristic**: Visibility of system status
  - **Steps**: Trigger slow operations (API calls, data loading)
  - **Evaluate**:
    - Is there a loading indicator?
    - Does user know something is happening?
    - Is progress shown for long operations?
  - **URL**: (various)

- [ ] **UX-007**: Undo and escape routes
  - **Heuristic**: User control & freedom
  - **Steps**: Make changes, then try to undo or go back
  - **Evaluate**:
    - Can you undo an approval? A rejection?
    - Is there always a way back?
    - Are destructive actions confirmed?
  - **URL**: (various)

[... add more based on specific app features ...]

## Blockers

Any issues preventing testing:
| Blocker | Impact | User Action Required |
|---------|--------|---------------------|
| (none yet) | | |

## Coverage Summary

### PRD Coverage
| PRD Section | Scenarios | Coverage |
|-------------|-----------|----------|
| [Generate from actual PRD sections] | | |

### Integration Test Coverage
| Service | Scenarios |
|---------|-----------|
| [Generate from ARCHITECTURE.md services] | |

### Value Delivery Coverage
| Category | Scenarios | Vision Metric |
|----------|-----------|---------------|
| [Generate from VISION.md success metrics] | | |

### UX Heuristics Coverage
| Heuristic | Scenarios |
|-----------|-----------|
| Visibility of system status | UX-001, UX-006 |
| Match real world | UX-002 |
| User control & freedom | UX-007 |
| Consistency | UX-002, UX-005 |
| Error prevention | UX-003 |
| Recognition over recall | UX-001, UX-002 |
| Flexibility & efficiency | UX-004 |
| Aesthetic & minimal design | UX-005 |
| Help with errors | UX-003 |

### Discovered Gaps
(Populated during testing - issues found that weren't in PRD)

| Gap ID | Issue | Severity | Suggested Fix |
|--------|-------|----------|---------------|
| (discovered during testing) | | | |
```

## Scenario Design Rules

### Good Scenarios

```markdown
- [ ] **BT-005**: User can approve a research concept
  - **PRD**: §2.2 Research Approval Queue
  - **Steps**:
    1. Navigate to /approvals
    2. Click "Research" tab
    3. Click "Approve" on first concept
  - **Expected**: Concept disappears from queue, success toast shown
  - **URL**: http://localhost:3000/approvals
```

### Bad Scenarios (Avoid)

```markdown
# Too vague - what does "works" mean?
- [ ] Research approval works

# Too broad - multiple features in one test
- [ ] User can approve concept, see it move to design queue, approve design, see it publish

# Not observable - can't verify in browser
- [ ] Database correctly indexes listings
```

## UX Scenario Generation Guide

Based on the app type, generate appropriate UX exploration scenarios:

**For Dashboard/Data Apps:**
- First load experience with no data
- First load experience with lots of data (100+ items)
- Finding specific information quickly
- Bulk operations efficiency
- Status/progress visibility
- Filtering and sorting usability

**For Workflow/Pipeline Apps:**
- Understanding current state at a glance
- Moving items through workflow
- Error recovery mid-workflow
- Progress visibility for long operations
- What happens when things fail

**For Approval/Review Apps:**
- Speed of approve/reject cycle
- Batch processing efficiency
- Keyboard navigation
- Preview quality
- Undo capability

**For Settings/Configuration:**
- Discoverability of options
- Validation feedback
- Save confirmation
- Reset/default options

## Verifying Real APIs (Not Stubs)

**CRITICAL**: Tests that pass with stub/mock APIs don't prove anything. For each INT-XXX test, include verification steps.

**General verification patterns:**

**For AI/Generation APIs:**
- Response time is realistic (2-30+ seconds, not instant)
- Output varies with input (not canned responses)
- Check logs for actual API call with request IDs
- Usage appears in external provider dashboard

**For External Service APIs (e-commerce, publishing, etc.):**
- Resource appears in actual external dashboard (not just local database)
- API returns real IDs that can be looked up externally
- Changes visible in production/sandbox environment

**For Browser Automation:**
- Browser actually runs (visible or headless but functional)
- Data extracted varies with input
- Results match what's visible in the browser

**Red flags that indicate stubs:**
- Instant responses (< 1 second for APIs that should take longer)
- Identical outputs every time
- Hardcoded IDs or placeholder data
- "stub" or "mock" in logs
- No API usage in external dashboards

## Completion

When test plan is complete:
- All PRD use cases have corresponding BT-XXX scenarios
- **Integration tests exist for each external API (INT-XXX)**
- **Value delivery tests verify VISION metrics (VAL-XXX)**
- **Integration tests cover each external service from ARCHITECTURE.md**
- UX exploration scenarios cover all heuristics
- Dependencies are documented
- Scenarios are prioritized (P0/P0-INT/P0-VAL/P1/P2/UX)
- Output: `<promise>BETA_PLAN_COMPLETE</promise>`

If PRD is missing or incomplete:
- Document the gap
- Output: `<promise>BETA_PLAN_BLOCKED</promise>`

## Remember

The PRD tells you what should work.
The integration tests tell you if REAL APIs work.
The value tests tell you if the VISION is achievable.
The UX scenarios tell you if it's actually good.

**An app can pass all feature tests and still fail to deliver business value.**

Your job is to verify:
1. Does the UI work? (BT-XXX scenarios)
2. Do real APIs work? (INT-XXX scenarios) ← stubs mask real bugs
3. Does it deliver the VISION? (VAL-XXX scenarios) ← **MOST IMPORTANT**
4. Is it good to use? (UX-XXX scenarios)

**The ultimate test: Could a real human use this tomorrow to achieve the VISION outcome?**

Read VISION.md and ask: "Does this test plan verify that a real user can accomplish what was promised?"

If the answer is "no" or "I'm not sure", the test plan is incomplete.
