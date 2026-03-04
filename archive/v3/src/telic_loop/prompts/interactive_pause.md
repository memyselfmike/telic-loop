# Interactive Pause — Human Action Required

The loop has encountered a situation that requires human intervention. An agent has identified a blocker that cannot be resolved with code alone. Your job is to generate clear, actionable instructions so the human knows exactly what to do, and verification steps so the loop knows when to resume.

## Context

- **Sprint Context**: {SPRINT_CONTEXT}

## Blocked Task

```json
{BLOCKED_TASK}
```

## Blocked Reason

```
{BLOCKED_REASON}
```

## The Core Principle

> **"The human is not a developer. Write instructions that anyone can follow. Be specific enough that there is no ambiguity about what to do or how to verify it is done."**

## Process

### Step 1: Understand the Blocker

Read the blocked task and the reason it is blocked. Classify the blocker:

| Type | Examples | Typical Resolution |
|------|----------|-------------------|
| **Credential** | Missing API key, database password, OAuth client secret | Create account, generate key, add to `.env` |
| **Authentication** | OAuth flow, browser login, SSO setup | Follow provider's auth flow, store tokens |
| **External Service** | Service account creation, subscription activation, DNS setup | Sign up, configure, verify access |
| **Environment** | Install system dependency, configure firewall, allocate resource | System-level installation or configuration |
| **Permission** | File permissions, cloud IAM, repository access | Grant access through provider's admin interface |

### Step 2: Generate Instructions

Write step-by-step instructions that are:

1. **Specific** — "Go to https://console.cloud.google.com/apis/credentials and click 'Create Credentials > OAuth 2.0 Client ID'" not "set up Google OAuth"
2. **Sequential** — Numbered steps in the order they must be performed
3. **Complete** — Include every step, including ones that seem obvious (like "click Save")
4. **Verifiable** — Each step should have an observable result ("you should see a Client ID starting with...")
5. **Safe** — Warn about irreversible actions, suggest test/development settings where applicable

Include the exact environment variable names and file paths where values should be stored. Example:

```
After creating the API key, add it to your environment:

  1. Open `backend/.env`
  2. Find the line `GOOGLE_API_KEY=` (or add it if missing)
  3. Set the value: `GOOGLE_API_KEY=your-key-here`
  4. Save the file
```

### Step 3: Define Verification

Define how the loop will automatically verify the human action is complete. This must be machine-checkable — the loop will run this check to decide whether to resume.

Good verification examples:
- "The environment variable `GOOGLE_API_KEY` is set and has length > 20"
- "A `GET` request to `http://localhost:8000/health` returns HTTP 200"
- "The file `credentials.json` exists at `backend/credentials.json` and contains a `client_id` field"
- "Running `docker ps` shows a container named `postgres` in the `Up` state"

Bad verification examples:
- "The user says they did it" (not machine-checkable)
- "It works" (not specific)
- "The API key is valid" (requires an API call that might have side effects or rate limits)

### Step 4: Report

Call the `request_human_action` tool with:

```json
{
  "action": "Brief one-line summary of what the human needs to do",
  "instructions": "Detailed step-by-step instructions (from Step 2)",
  "verification": "Machine-checkable verification condition (from Step 3)",
  "blocked_task_id": "The task ID that is blocked"
}
```

## Anti-Patterns

- Writing instructions that assume developer knowledge ("configure the OAuth redirect URI") — be explicit about what, where, and how
- Defining verification that requires human confirmation — verification must be automatable
- Combining multiple unrelated actions into one pause — if two independent things need human action, they should be separate pauses
- Requesting human action for something the loop can do itself (service startup, file creation, dependency installation) — only pause for things that genuinely require human judgment or access
- Being vague about file paths or variable names — use absolute paths and exact names
- Forgetting to mention which file to edit or which URL to visit
