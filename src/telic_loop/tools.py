"""Tool implementations and structured output handlers."""

from __future__ import annotations

import copy
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .claude import AgentRole
    from .state import LoopState


# ---------------------------------------------------------------------------
# Execution tools (filesystem + shell)
# ---------------------------------------------------------------------------

EXECUTION_TOOLS: list[dict] = [
    {
        "name": "bash",
        "description": "Execute a shell command. Returns stdout, stderr, and exit code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 120)", "default": 120},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read file contents. Returns the text content of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path"},
                "offset": {"type": "integer", "description": "Line offset to start from (0-based)"},
                "limit": {"type": "integer", "description": "Maximum lines to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace a string in a file. old_string must be unique in the file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "old_string": {"type": "string", "description": "String to find and replace"},
                "new_string": {"type": "string", "description": "Replacement string"},
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
                "pattern": {"type": "string", "description": "Glob pattern (e.g. '**/*.py')"},
                "path": {"type": "string", "description": "Directory to search in"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep_search",
        "description": "Search file contents by regex pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "Directory or file to search"},
                "glob": {"type": "string", "description": "File glob filter (e.g. '*.py')"},
            },
            "required": ["pattern"],
        },
    },
]

READ_ONLY_TOOLS: list[dict] = [
    t for t in EXECUTION_TOOLS if t["name"] in ("read_file", "glob_search", "grep_search", "bash")
]

# ---------------------------------------------------------------------------
# Provider tools (server-side, Anthropic-executed)
# ---------------------------------------------------------------------------

PROVIDER_TOOLS: list[dict] = [
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 5},
    {"type": "web_fetch_20250910", "name": "web_fetch", "max_size": 100_000},
]

# ---------------------------------------------------------------------------
# Structured output tool schemas
# ---------------------------------------------------------------------------

MANAGE_TASK_SCHEMA: dict = {
    "name": "manage_task",
    "description": "Add, modify, or remove a task in the implementation plan.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["add", "modify", "remove"]},
            "task_id": {"type": "string"},
            "reason": {"type": "string"},
            "description": {"type": "string"},
            "value": {"type": "string"},
            "acceptance": {"type": "string"},
            "prd_section": {"type": "string"},
            "dependencies": {"type": "array", "items": {"type": "string"}},
            "phase": {"type": "string"},
            "files_expected": {"type": "array", "items": {"type": "string"}},
            "field": {
                "type": "string",
                "enum": ["description", "value", "acceptance", "dependencies",
                         "phase", "status", "blocked_reason", "files_expected"],
            },
            "new_value": {"type": "string"},
        },
        "required": ["action", "task_id"],
    },
}

REPORT_TASK_COMPLETE_SCHEMA: dict = {
    "name": "report_task_complete",
    "description": "Signal that a task has been completed with its deliverables.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "files_created": {"type": "array", "items": {"type": "string"}},
            "files_modified": {"type": "array", "items": {"type": "string"}},
            "value_verified": {"type": "string"},
            "completion_notes": {"type": "string"},
            "resolution_note": {
                "type": "string",
                "description": "Architectural justification for why a quality violation is intentional (e.g. 'Tailwind v4 uses CSS-first config, no tailwind.config.mjs needed'). Set this when completing a quality task where the violation is by design.",
            },
        },
        "required": ["task_id", "files_created", "files_modified"],
    },
}

REPORT_DISCOVERY_SCHEMA: dict = {
    "name": "report_discovery",
    "description": "Report sprint context discovered from Vision, PRD, and codebase.",
    "input_schema": {
        "type": "object",
        "properties": {
            "deliverable_type": {"type": "string", "enum": ["software", "document", "data", "config", "hybrid"]},
            "project_type": {"type": "string"},
            "codebase_state": {"type": "string", "enum": ["greenfield", "brownfield", "non_code"]},
            "environment": {"type": "object"},
            "services": {"type": "object"},
            "verification_strategy": {"type": "object"},
            "value_proofs": {"type": "array", "items": {"type": "string"}},
            "unresolved_questions": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["deliverable_type", "project_type", "codebase_state", "value_proofs"],
    },
}

REPORT_CRITIQUE_SCHEMA: dict = {
    "name": "report_critique",
    "description": "Report PRD feasibility critique result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["APPROVE", "AMEND", "DESCOPE", "REJECT"]},
            "reason": {"type": "string"},
            "amendments": {"type": "array", "items": {"type": "string"}},
            "descope_suggestions": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["verdict", "reason"],
    },
}

REPORT_TRIAGE_SCHEMA: dict = {
    "name": "report_triage",
    "description": "Report root cause analysis of test failures.",
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
}

REQUEST_HUMAN_ACTION_SCHEMA: dict = {
    "name": "request_human_action",
    "description": "Request a human to perform an action the loop cannot do.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "instructions": {"type": "string"},
            "verification_command": {"type": "string"},
            "blocked_task_id": {"type": "string"},
        },
        "required": ["action", "instructions", "blocked_task_id"],
    },
}

REPORT_VRC_SCHEMA: dict = {
    "name": "report_vrc",
    "description": "Report Vision Reality Check result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "value_score": {"type": "number", "minimum": 0, "maximum": 1},
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
            },
            "recommendation": {"type": "string", "enum": ["CONTINUE", "COURSE_CORRECT", "DESCOPE", "SHIP_READY"]},
            "summary": {"type": "string"},
        },
        "required": ["value_score", "deliverables_verified", "deliverables_total", "recommendation", "summary"],
    },
}

REPORT_COURSE_CORRECTION_SCHEMA: dict = {
    "name": "report_course_correction",
    "description": "Report course correction decision.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["restructure", "descope", "new_tasks", "rollback", "regenerate_tests", "escalate"]},
            "reason": {"type": "string"},
            "rollback_to_checkpoint": {"type": "string"},
            "tasks_to_restructure": {"type": "string"},
        },
        "required": ["action", "reason"],
    },
}

REPORT_EVAL_FINDING_SCHEMA: dict = {
    "name": "report_eval_finding",
    "description": "Report a finding from critical evaluation of the deliverable.",
    "input_schema": {
        "type": "object",
        "properties": {
            "severity": {"type": "string", "enum": ["critical", "blocking", "degraded", "polish"]},
            "description": {"type": "string"},
            "user_impact": {"type": "string"},
            "suggested_fix": {"type": "string"},
            "evidence": {"type": "string"},
        },
        "required": ["severity", "description", "user_impact"],
    },
}

REPORT_RESEARCH_SCHEMA: dict = {
    "name": "report_research",
    "description": "Report external research findings.",
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "findings": {"type": "string"},
            "sources": {"type": "array", "items": {"type": "string"}},
            "affected_verifications": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["topic", "findings", "sources"],
    },
}

REPORT_VISION_VALIDATION_SCHEMA: dict = {
    "name": "report_vision_validation",
    "description": "Report 5-pass vision validation result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["PASS", "NEEDS_REVISION"]},
            "dimensions": {
                "type": "object",
                "properties": {
                    "outcome_grounded": {"type": "string", "enum": ["STRONG", "ADEQUATE", "WEAK", "CRITICAL"]},
                    "adoption_realistic": {"type": "string", "enum": ["STRONG", "ADEQUATE", "WEAK", "CRITICAL"]},
                    "causally_sound": {"type": "string", "enum": ["STRONG", "ADEQUATE", "WEAK", "CRITICAL"]},
                    "failure_aware": {"type": "string", "enum": ["STRONG", "ADEQUATE", "WEAK", "CRITICAL"]},
                },
            },
            "strengths": {"type": "array", "items": {"type": "string"}},
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "severity": {"type": "string", "enum": ["hard", "soft"]},
                        "category": {"type": "string"},
                        "description": {"type": "string"},
                        "evidence": {"type": "string"},
                        "suggested_revision": {"type": "string"},
                    },
                    "required": ["id", "severity", "category", "description", "evidence"],
                },
            },
            "kill_criteria": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
        },
        "required": ["verdict", "reason", "issues", "strengths"],
    },
}

REPORT_STRATEGY_CHANGE_SCHEMA: dict = {
    "name": "report_strategy_change",
    "description": "Report process monitor strategy change recommendation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "enum": ["plateau", "churn", "efficiency_collapse", "category_clustering", "budget_divergence", "file_hotspot"]},
            "cause": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "action": {"type": "string", "enum": ["STRATEGY_CHANGE", "ESCALATE", "CONTINUE"]},
            "changes": {"type": "object"},
            "rationale": {"type": "string"},
            "re_evaluate_after": {"type": "integer", "minimum": 3},
        },
        "required": ["pattern", "cause", "evidence", "action", "rationale", "re_evaluate_after"],
    },
}

REPORT_EPIC_DECOMPOSITION_SCHEMA: dict = {
    "name": "report_epic_decomposition",
    "description": "Report epic decomposition of a complex vision.",
    "input_schema": {
        "type": "object",
        "properties": {
            "epic_count": {"type": "integer", "minimum": 2, "maximum": 5},
            "epics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "epic_id": {"type": "string"},
                        "title": {"type": "string"},
                        "value_statement": {"type": "string"},
                        "deliverables": {"type": "array", "items": {"type": "string"}},
                        "completion_criteria": {"type": "array", "items": {"type": "string"}},
                        "depends_on": {"type": "array", "items": {"type": "string"}},
                        "detail_level": {"type": "string", "enum": ["full", "moderate", "sketch"]},
                        "key_risks": {"type": "array", "items": {"type": "string"}},
                        "task_sketch": {"type": "array", "items": {"type": "string"}},
                        "estimated_task_count": {"type": "integer"},
                    },
                    "required": ["epic_id", "title", "value_statement", "deliverables", "completion_criteria"],
                },
            },
            "vision_too_large": {"type": "boolean"},
            "rationale": {"type": "string"},
        },
        "required": ["epic_count", "epics", "vision_too_large", "rationale"],
    },
}

REPORT_EPIC_SUMMARY_SCHEMA: dict = {
    "name": "report_epic_summary",
    "description": "Report curated epic summary for human feedback checkpoint.",
    "input_schema": {
        "type": "object",
        "properties": {
            "epic_id": {"type": "string"},
            "summary": {
                "type": "object",
                "properties": {
                    "delivered": {"type": "array", "items": {"type": "string"}},
                    "vision_progress": {"type": "string"},
                    "adjustments": {"type": "array", "items": {"type": "string"}},
                    "next_epic": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "value_statement": {"type": "string"},
                            "key_deliverables": {"type": "array", "items": {"type": "string"}},
                            "risks": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "confidence": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "confidence_rationale": {"type": "string"},
                },
            },
            "vrc_snapshot": {
                "type": "object",
                "properties": {
                    "value_score": {"type": "number"},
                    "deliverables_verified": {"type": "integer"},
                    "deliverables_total": {"type": "integer"},
                    "gaps": {"type": "array"},
                },
            },
        },
        "required": ["epic_id", "summary"],
    },
}

REPORT_COHERENCE_SCHEMA: dict = {
    "name": "report_coherence",
    "description": "Report system coherence evaluation result.",
    "input_schema": {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["quick", "full"]},
            "dimensions": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["HEALTHY", "WARNING", "CRITICAL"]},
                        "findings": {"type": "array", "items": {"type": "string"}},
                        "trend": {"type": "string", "enum": ["improving", "stable", "degrading"]},
                    },
                },
            },
            "overall": {"type": "string", "enum": ["HEALTHY", "WARNING", "CRITICAL"]},
            "top_findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "dimension": {"type": "string"},
                        "severity": {"type": "string"},
                        "description": {"type": "string"},
                        "affected_files": {"type": "array", "items": {"type": "string"}},
                        "suggested_action": {"type": "string"},
                        "leverage_level": {"type": "integer"},
                    },
                },
            },
            "comparison_to_previous": {"type": "string"},
        },
        "required": ["mode", "dimensions", "overall"],
    },
}

# All structured tool schemas for convenience
ALL_STRUCTURED_SCHEMAS: list[dict] = [
    MANAGE_TASK_SCHEMA,
    REPORT_TASK_COMPLETE_SCHEMA,
    REPORT_DISCOVERY_SCHEMA,
    REPORT_CRITIQUE_SCHEMA,
    REPORT_TRIAGE_SCHEMA,
    REQUEST_HUMAN_ACTION_SCHEMA,
    REPORT_VRC_SCHEMA,
    REPORT_COURSE_CORRECTION_SCHEMA,
    REPORT_EVAL_FINDING_SCHEMA,
    REPORT_RESEARCH_SCHEMA,
    REPORT_VISION_VALIDATION_SCHEMA,
    REPORT_STRATEGY_CHANGE_SCHEMA,
    REPORT_EPIC_DECOMPOSITION_SCHEMA,
    REPORT_EPIC_SUMMARY_SCHEMA,
    REPORT_COHERENCE_SCHEMA,
]


# ---------------------------------------------------------------------------
# Tool role mapping
# ---------------------------------------------------------------------------

def get_tools_for_role(role: AgentRole) -> list[dict]:
    """Return tools appropriate for this role.

    Structured output tools are added by the orchestrator per-prompt
    via the session's tools list, not here. This returns base tools only.
    """
    match role:
        case AgentRole.RESEARCHER:
            return EXECUTION_TOOLS + PROVIDER_TOOLS
        case AgentRole.EVALUATOR:
            return READ_ONLY_TOOLS
        case AgentRole.CLASSIFIER:
            return []  # structured output tools injected per-prompt
        case _:
            return EXECUTION_TOOLS


# ---------------------------------------------------------------------------
# Task mutation guardrails
# ---------------------------------------------------------------------------

DUPLICATE_SIMILARITY_THRESHOLD = 0.75
MID_LOOP_TASK_CEILING = 15


def validate_task_mutation(action: str, input_data: dict, state: LoopState) -> str | None:
    """Deterministic validation. Returns error message or None."""
    task_id = input_data.get("task_id", "")

    if action == "add":
        missing = [f for f in ["description", "value", "acceptance"] if not input_data.get(f)]
        if missing:
            return f"Task {task_id} missing: {', '.join(missing)}"

        new_desc = input_data["description"].lower()
        for existing in state.tasks.values():
            if existing.status in ("done", "descoped"):
                continue
            sim = _jaccard_similarity(new_desc, existing.description.lower())
            if sim >= DUPLICATE_SIMILARITY_THRESHOLD:
                return f"Task {task_id} duplicates {existing.task_id} ({sim:.0%} similar)"

        mid_loop = [
            t for t in state.tasks.values()
            if t.source != "plan" and t.status not in ("done", "descoped")
        ]
        if len(mid_loop) >= MID_LOOP_TASK_CEILING:
            return f"Mid-loop task ceiling ({MID_LOOP_TASK_CEILING}) reached"

        for dep_id in input_data.get("dependencies", []):
            if dep_id not in state.tasks:
                return f"Dependency '{dep_id}' doesn't exist"

        # Task granularity enforcement
        desc = input_data.get("description", "")
        max_desc = getattr(state, "max_task_description_chars", 600)
        if len(desc) > max_desc:
            return (
                f"Description too long ({len(desc)} chars, max {max_desc}). "
                "Split this task into smaller, focused units."
            )

        files = input_data.get("files_expected", [])
        max_files = getattr(state, "max_files_per_task", 5)
        if len(files) > max_files:
            return (
                f"Too many files_expected ({len(files)}, max {max_files}). "
                "Split into separate tasks, each touching fewer files."
            )

    elif action == "modify":
        if task_id not in state.tasks:
            return f"Task {task_id} doesn't exist"
        if input_data.get("field") == "dependencies":
            raw = input_data.get("new_value", [])
            new_deps = json.loads(raw) if isinstance(raw, str) else raw
            for dep_id in (new_deps or []):
                if _creates_cycle(task_id, dep_id, state):
                    return f"Circular dependency: {task_id} -> {dep_id}"

    elif action == "remove":
        if task_id not in state.tasks:
            return f"Task {task_id} doesn't exist"
        dependents = [
            t.task_id for t in state.tasks.values()
            if task_id in (t.dependencies or [])
        ]
        if dependents:
            return f"Cannot remove {task_id} -- depended on by {', '.join(dependents)}"

    return None


def _jaccard_similarity(a: str, b: str) -> float:
    wa, wb = set(a.split()), set(b.split())
    return len(wa & wb) / len(wa | wb) if (wa or wb) else 0.0


def _creates_cycle(task_id: str, new_dep_id: str, state: LoopState) -> bool:
    visited: set[str] = set()
    stack = [new_dep_id]
    while stack:
        current = stack.pop()
        if current == task_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        t = state.tasks.get(current)
        if t and t.dependencies:
            stack.extend(t.dependencies)
    return False


# ---------------------------------------------------------------------------
# Tool execution dispatch (transactional)
# ---------------------------------------------------------------------------

def execute_tool(name: str, input_data: dict, state: LoopState | None,
                 task_source: str = "agent") -> str:
    """Dispatch tool calls. Structured tools mutate state transactionally.
    Execution tools run commands/read files directly."""

    # Execution tools (filesystem + shell)
    EXEC_HANDLERS = {
        "bash": _exec_bash,
        "read_file": _exec_read_file,
        "write_file": _exec_write_file,
        "edit_file": _exec_edit_file,
        "glob_search": _exec_glob_search,
        "grep_search": _exec_grep_search,
    }

    if name in EXEC_HANDLERS:
        return EXEC_HANDLERS[name](input_data)

    # Structured output tools (state mutations)
    HANDLERS = {
        "manage_task": handle_manage_task,
        "report_task_complete": handle_task_complete,
        "report_discovery": handle_discovery,
        "report_critique": handle_critique,
        "report_triage": handle_triage,
        "report_vrc": handle_vrc,
        "report_eval_finding": handle_eval_finding,
        "report_research": handle_research,
        "report_vision_validation": handle_vision_validation,
        "report_strategy_change": handle_strategy_change,
        "report_course_correction": handle_course_correction,
        "report_epic_decomposition": handle_epic_decomposition,
        "report_epic_summary": handle_epic_summary,
        "report_coherence": handle_coherence,
        "request_human_action": handle_human_action,
    }

    handler = HANDLERS.get(name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {name}"})

    if state is None:
        return json.dumps({"error": "No state available for structured tool"})

    # Snapshot mutable state for transactional safety
    snapshot = {
        "tasks": copy.deepcopy(state.tasks),
        "verifications": copy.deepcopy(state.verifications),
        "agent_results": copy.deepcopy(state.agent_results),
    }
    try:
        result = handler(input_data, state, task_source=task_source)
        return json.dumps({"ok": True, "result": result})
    except Exception as e:
        state.tasks = snapshot["tasks"]
        state.verifications = snapshot["verifications"]
        state.agent_results = snapshot["agent_results"]
        return json.dumps({"error": f"Handler failed: {e}", "rolled_back": True})


# ---------------------------------------------------------------------------
# Execution tool implementations
# ---------------------------------------------------------------------------

def _exec_bash(input_data: dict) -> str:
    cmd = input_data["command"]
    timeout = input_data.get("timeout", 120)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout,
        )
        output = ""
        if result.stdout:
            output += result.stdout[:10000]
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr[:5000]
        output += f"\n[exit code: {result.returncode}]"
        return output
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT after {timeout}s]"


def _exec_read_file(input_data: dict) -> str:
    path = Path(input_data["path"])
    if not path.exists():
        return f"[ERROR: File not found: {path}]"
    try:
        content = path.read_text(errors="replace")
        lines = content.split("\n")
        offset = input_data.get("offset", 0)
        limit = input_data.get("limit", len(lines))
        selected = lines[offset:offset + limit]
        return "\n".join(f"{i + offset + 1:>6}\t{line}" for i, line in enumerate(selected))
    except Exception as e:
        return f"[ERROR: {e}]"


def _exec_write_file(input_data: dict) -> str:
    path = Path(input_data["path"])
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(input_data["content"])
        return f"[Wrote {len(input_data['content'])} chars to {path}]"
    except Exception as e:
        return f"[ERROR: {e}]"


def _exec_edit_file(input_data: dict) -> str:
    path = Path(input_data["path"])
    if not path.exists():
        return f"[ERROR: File not found: {path}]"
    try:
        content = path.read_text()
        old = input_data["old_string"]
        new = input_data["new_string"]
        count = content.count(old)
        if count == 0:
            return f"[ERROR: old_string not found in {path}]"
        if count > 1:
            return f"[ERROR: old_string found {count} times in {path} — must be unique]"
        content = content.replace(old, new, 1)
        path.write_text(content)
        return f"[Edited {path}]"
    except Exception as e:
        return f"[ERROR: {e}]"


def _exec_glob_search(input_data: dict) -> str:
    pattern = input_data["pattern"]
    base = Path(input_data.get("path", "."))
    try:
        matches = sorted(str(p) for p in base.glob(pattern))
        if not matches:
            return "[No matches]"
        return "\n".join(matches[:200])
    except Exception as e:
        return f"[ERROR: {e}]"


def _exec_grep_search(input_data: dict) -> str:
    import re
    pattern = input_data["pattern"]
    base = Path(input_data.get("path", "."))
    glob_filter = input_data.get("glob", "**/*")

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"[ERROR: Invalid regex: {e}]"

    results: list[str] = []
    try:
        files = sorted(base.glob(glob_filter)) if base.is_dir() else [base]
        for fpath in files:
            if not fpath.is_file():
                continue
            try:
                content = fpath.read_text(errors="replace")
                for i, line in enumerate(content.split("\n"), 1):
                    if regex.search(line):
                        results.append(f"{fpath}:{i}: {line[:200]}")
                        if len(results) >= 100:
                            results.append("[... truncated at 100 matches]")
                            return "\n".join(results)
            except Exception:
                continue
    except Exception as e:
        return f"[ERROR: {e}]"

    return "\n".join(results) if results else "[No matches]"


# ---------------------------------------------------------------------------
# Structured output handlers
# ---------------------------------------------------------------------------

def handle_manage_task(input_data: dict, state: LoopState, task_source: str = "agent") -> str:
    from .state import TaskState

    action = input_data["action"]
    task_id = input_data["task_id"]

    error = validate_task_mutation(action, input_data, state)
    if error:
        return f"REJECTED: {error}"

    if action == "add":
        task = TaskState(
            task_id=task_id,
            source=task_source,
            description=input_data.get("description", ""),
            value=input_data.get("value", ""),
            acceptance=input_data.get("acceptance", ""),
            prd_section=input_data.get("prd_section", ""),
            dependencies=input_data.get("dependencies", []),
            phase=input_data.get("phase", ""),
            files_expected=input_data.get("files_expected", []),
            created_at=datetime.now().isoformat(),
        )
        state.add_task(task)
        return f"Added task {task_id}"

    elif action == "modify":
        task = state.tasks[task_id]
        field_name = input_data.get("field", "")
        new_value = input_data.get("new_value", "")

        if field_name == "status":
            # Prevent un-descoping: once descoped, only the human can revert
            if task.status == "descoped" and new_value != "descoped":
                return (
                    f"Cannot change {task_id} from descoped to {new_value}. "
                    f"Descoped tasks were intentionally removed from scope."
                )
            task.status = new_value
            if new_value == "descoped":
                task.blocked_reason = input_data.get("reason", "Descoped")
        elif field_name == "blocked_reason":
            task.blocked_reason = new_value
            if new_value and task.status != "blocked":
                task.status = "blocked"
        elif field_name == "dependencies":
            task.dependencies = json.loads(new_value) if isinstance(new_value, str) else new_value
        elif field_name == "description":
            task.description = new_value
        elif field_name == "value":
            task.value = new_value
        elif field_name == "acceptance":
            task.acceptance = new_value
        elif field_name == "phase":
            task.phase = new_value
        elif field_name == "files_expected":
            task.files_expected = json.loads(new_value) if isinstance(new_value, str) else new_value
        else:
            return f"Unknown field: {field_name}"

        return f"Modified {task_id}.{field_name}"

    elif action == "remove":
        del state.tasks[task_id]
        return f"Removed task {task_id}"

    return f"Unknown action: {action}"


def _normalize_paths(paths: list[str], sprint_prefix: str) -> list[str]:
    """Ensure file paths include the sprint directory prefix."""
    result = []
    for p in paths:
        if not p:
            continue
        # Skip absolute paths and paths already under sprints/
        if Path(p).is_absolute() or p.startswith("sprints/"):
            result.append(p)
        else:
            result.append(sprint_prefix + p)
    return result


def handle_task_complete(input_data: dict, state: LoopState, **_: Any) -> str:
    task_id = input_data["task_id"]
    task = state.tasks.get(task_id)
    if not task:
        return f"Task {task_id} not found"
    if task.status == "descoped":
        return f"Task {task_id} is descoped — cannot mark complete"
    task.status = "done"
    task.completed_at = datetime.now().isoformat()
    # Normalize file paths: ensure sprint dir prefix is present
    sprint_prefix = f"sprints/{state.sprint}/"
    task.files_created = _normalize_paths(input_data.get("files_created", []), sprint_prefix)
    task.files_modified = _normalize_paths(input_data.get("files_modified", []), sprint_prefix)
    task.completion_notes = input_data.get("completion_notes", "")
    task.resolution_note = input_data.get("resolution_note", "")
    return f"Task {task_id} marked complete"


def handle_discovery(input_data: dict, state: LoopState, **_: Any) -> str:
    from .state import SprintContext
    state.context = SprintContext(
        deliverable_type=input_data.get("deliverable_type", "unknown"),
        project_type=input_data.get("project_type", "unknown"),
        codebase_state=input_data.get("codebase_state", "greenfield"),
        environment=input_data.get("environment", {}),
        services=input_data.get("services", {}),
        verification_strategy=input_data.get("verification_strategy", {}),
        value_proofs=input_data.get("value_proofs", []),
        unresolved_questions=input_data.get("unresolved_questions", []),
    )
    return "Discovery reported"


def handle_critique(input_data: dict, state: LoopState, **_: Any) -> str:
    state.agent_results["critique"] = input_data
    return f"Critique recorded: {input_data.get('verdict', 'unknown')}"


def handle_triage(input_data: dict, state: LoopState, **_: Any) -> str:
    state.agent_results["triage"] = input_data.get("root_causes", [])
    return f"Triage recorded: {len(input_data.get('root_causes', []))} root causes"


def handle_vrc(input_data: dict, state: LoopState, **_: Any) -> str:
    from .state import VRCSnapshot

    # Normalize value_score to 0.0-1.0 (agents sometimes use 0-10 or 0-100)
    score = float(input_data.get("value_score", 0.0))
    if score > 1.0:
        score = score / 100.0 if score > 10.0 else score / 10.0

    # Normalize recommendation to valid enum values
    _RECOMMENDATION_MAP = {
        "proceed": "CONTINUE",
        "conditional_pass": "SHIP_READY",
    }
    rec = input_data.get("recommendation", "CONTINUE")
    rec = _RECOMMENDATION_MAP.get(rec.lower(), rec.upper()) if isinstance(rec, str) else "CONTINUE"
    if rec not in ("CONTINUE", "COURSE_CORRECT", "DESCOPE", "SHIP_READY"):
        rec = "CONTINUE"

    # Normalize gaps: ensure each entry is a dict, not a bare string
    gaps = input_data.get("gaps", [])
    if gaps and isinstance(gaps[0], str):
        gaps = [{"description": g, "severity": "degraded"} for g in gaps]

    snapshot = VRCSnapshot(
        iteration=state.iteration,
        timestamp=datetime.now().isoformat(),
        deliverables_total=input_data.get("deliverables_total", 0),
        deliverables_verified=input_data.get("deliverables_verified", 0),
        deliverables_blocked=input_data.get("deliverables_blocked", 0),
        value_score=score,
        gaps=gaps,
        recommendation=rec,
        summary=input_data.get("summary", ""),
    )
    state.vrc_history.append(snapshot)

    # Auto-create tasks from gap suggestions immediately — don't wait for exit gate.
    # This closes the loop: VRC identifies gap → task created → builder fixes it.
    from .state import TaskState

    created = 0
    existing_descs = {
        t.description for t in state.tasks.values() if t.status != "descoped"
    }
    for gap in gaps:
        suggested = gap.get("suggested_task", "")
        if not suggested:
            continue
        # Dedup: skip if a task with this exact description already exists
        if suggested in existing_descs:
            continue
        # Polish gaps only create tasks during active loop (not when SHIP_READY)
        severity = gap.get("severity", "degraded")
        if severity == "polish" and rec == "SHIP_READY":
            continue

        gap_id = gap.get("id", f"gap-{created}")
        task_id = f"VRC-{state.iteration}-{gap_id}"

        # Epic-scope new tasks in multi-epic mode
        epic_id = ""
        if (state.vision_complexity == "multi_epic"
                and state.epics
                and state.current_epic_index < len(state.epics)):
            epic_id = state.epics[state.current_epic_index].epic_id

        state.tasks[task_id] = TaskState(
            task_id=task_id,
            source="vrc",
            description=suggested,
            value=gap.get("description", ""),
            acceptance=f"Gap '{gap_id}' resolved: {gap.get('description', '')}",
            created_at=datetime.now().isoformat(),
            epic_id=epic_id,
        )
        existing_descs.add(suggested)
        created += 1

    task_msg = f", {created} task(s) created" if created else ""
    return f"VRC recorded: {score:.0%} value ({rec}){task_msg}"


def handle_eval_finding(input_data: dict, state: LoopState, **_: Any) -> str:
    from .state import TaskState
    severity = input_data["severity"]
    if severity in ("critical", "blocking"):
        task_id = f"CE-{state.iteration}-{len(state.tasks)}"
        state.add_task(TaskState(
            task_id=task_id,
            source="critical_eval",
            description=input_data.get("suggested_fix", input_data["description"]),
            value=input_data["user_impact"],
            acceptance=f"Fix: {input_data['description']}",
            created_at=datetime.now().isoformat(),
        ))
    return f"Finding recorded: [{severity}] {input_data['description']}"


def handle_research(input_data: dict, state: LoopState, **_: Any) -> str:
    brief = {
        "topic": input_data.get("topic", ""),
        "findings": input_data.get("findings", ""),
        "sources": input_data.get("sources", []),
        "affected_verifications": input_data.get("affected_verifications", []),
        "iteration": state.iteration,
    }
    state.research_briefs.append(brief)
    state.agent_results["research"] = input_data
    return f"Research recorded: {input_data.get('topic', '')}"


def handle_vision_validation(input_data: dict, state: LoopState, **_: Any) -> str:
    state.agent_results["vision_validation"] = input_data
    return f"Vision validation: {input_data.get('verdict', 'unknown')}"


def handle_strategy_change(input_data: dict, state: LoopState, **_: Any) -> str:
    state.agent_results["strategy_change"] = input_data
    return f"Strategy change: {input_data.get('action', 'unknown')}"


def handle_course_correction(input_data: dict, state: LoopState, **_: Any) -> str:
    state.agent_results["course_correction"] = input_data
    return f"Course correction: {input_data.get('action', 'unknown')}"


def handle_epic_decomposition(input_data: dict, state: LoopState, **_: Any) -> str:
    from .state import Epic

    state.agent_results["epic_decomposition"] = input_data

    # Create Epic objects in state.epics from the decomposition result
    epics: list[Epic] = []
    for epic_data in input_data.get("epics", []):
        epic = Epic(
            epic_id=epic_data.get("epic_id", f"epic_{len(epics) + 1}"),
            title=epic_data.get("title", ""),
            value_statement=epic_data.get("value_statement", ""),
            deliverables=epic_data.get("deliverables", []),
            completion_criteria=epic_data.get("completion_criteria", []),
            depends_on=epic_data.get("depends_on", []),
            detail_level=epic_data.get("detail_level", "sketch"),
            task_sketch=epic_data.get("task_sketch", []),
        )
        epics.append(epic)
    state.epics = epics

    return f"Epic decomposition: {len(epics)} epics created"


def handle_epic_summary(input_data: dict, state: LoopState, **_: Any) -> str:
    state.agent_results["epic_summary"] = input_data
    return f"Epic summary recorded for {input_data.get('epic_id', '')}"


def handle_coherence(input_data: dict, state: LoopState, **_: Any) -> str:
    state.agent_results["coherence"] = input_data
    return f"Coherence reported: {input_data.get('overall', 'unknown')}"


def handle_human_action(input_data: dict, state: LoopState, **_: Any) -> str:
    from .state import PauseState
    task_id = input_data["blocked_task_id"]
    task = state.tasks.get(task_id)
    if task:
        task.status = "blocked"
        task.blocked_reason = f"HUMAN_ACTION: {input_data['action']}"
    state.pause = PauseState(
        reason=input_data["action"],
        instructions=input_data["instructions"],
        verification=input_data.get("verification_command", ""),
        requested_at=datetime.now().isoformat(),
    )
    return f"Human action requested for {task_id}: {input_data['action']}"
