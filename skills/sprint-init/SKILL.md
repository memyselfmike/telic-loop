---
name: sprint-init
description: Initialize a new telic-loop sprint with VISION.md and PRD.md
argument-hint: <sprint-name>
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Initialize a Telic Loop Sprint

Create a new sprint named `$0` for this project.

## Steps

1. Create the sprint directory: `sprints/$0/`
2. Ask the user what outcome they want (the Vision) and what specific requirements they have (the PRD)
3. Write `sprints/$0/VISION.md` and `sprints/$0/PRD.md` using the templates below
4. If the project has an existing codebase, scan it and generate `sprints/$0/ARCHITECTURE.md`
5. Commit the sprint files

## VISION.md Template

```markdown
# Vision: <Project Name>

<2-4 sentences describing the OUTCOME. What does the user get? What can they do
that they couldn't before? Focus on the experience, not the technology.>
```

**Good Vision**: Describes what the user experiences when the work is done.
**Bad Vision**: Describes technology choices or implementation details.

## PRD.md Template

```markdown
# PRD: <Project Name>

## Requirements

1. **<Feature>**: <Specific behavior — what the user can do, what happens>
2. **<Feature>**: <Specific behavior>

## Tech Stack
- <Framework with pinned major.minor version>
- <Database>

## Constraints
- <Any hard constraints>
```

## Critical Rules

- **Pin versions**: Every framework and major dependency must have a pinned major.minor version (e.g., "Next.js 14.2" not "Next.js" or "latest")
- **Be specific about behaviors**: "User can filter recipes by cuisine" not "implement filtering"
- **Include non-obvious requirements**: auth, persistence, responsive design, accessibility
- If the project already has a tech stack, respect it — don't invent a new one

## Architecture Detection

If the project has existing code, scan for:
- Package files: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`
- Framework indicators: `next.config.*`, `vite.config.*`, `django`, `flask`
- Directory structure patterns
- Database configuration

Write findings to `sprints/$0/ARCHITECTURE.md` so the planner has context.
