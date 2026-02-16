"""Claude Code SDK wrapper: Claude class, ClaudeSession, AgentRole model routing."""

from __future__ import annotations

import asyncio
import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    query,
)
from claude_code_sdk._errors import CLIConnectionError

if TYPE_CHECKING:
    from .config import LoopConfig
    from .state import LoopState

# Claude Code built-in tool sets (per role)
_FULL_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
_READONLY_TOOLS = ["Read", "Glob", "Grep", "Bash"]
_RESEARCH_TOOLS = ["Bash", "Read", "Glob", "Grep", "WebSearch", "WebFetch"]
_MINIMAL_TOOLS = ["Bash"]  # Need Bash for tool CLI

_TOOL_SETS: dict[str, list[str]] = {
    "full": _FULL_TOOLS,
    "readonly": _READONLY_TOOLS,
    "research": _RESEARCH_TOOLS,
    "minimal": _MINIMAL_TOOLS,
}


class AgentRole(Enum):
    """(model_config_attr, max_turns, tool_set_key)"""
    REASONER   = ("model_reasoning",  40, "full")
    EVALUATOR  = ("model_reasoning",  40, "readonly")
    RESEARCHER = ("model_reasoning",  30, "research")
    BUILDER    = ("model_execution",  60, "full")
    FIXER      = ("model_execution",  25, "full")
    QC         = ("model_execution",  30, "full")
    CLASSIFIER = ("model_triage",      5, "minimal")


def load_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template and safely format placeholders.

    Uses string replacement instead of str.format() to avoid conflicts
    with literal braces in JSON examples within prompt templates.
    """
    template = (Path(__file__).parent / "prompts" / f"{name}.md").read_text()
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


def _tool_cli_instructions(state_file: Path) -> str:
    """Generate system prompt section for tool CLI usage."""
    from .tools import ALL_STRUCTURED_SCHEMAS

    lines = [
        "\n## Structured Tool CLI",
        "",
        "To call structured tools (task management, reporting, etc.), use Bash:",
        f"  python -m telic_loop.tool_cli --state-file {state_file} <tool_name> '<json_input>'",
        "",
        "Available structured tools:",
    ]
    for schema in ALL_STRUCTURED_SCHEMAS:
        name = schema["name"]
        desc = schema["description"]
        required = schema["input_schema"].get("required", [])
        props = list(schema["input_schema"].get("properties", {}).keys())
        lines.append(f"  - **{name}**: {desc}")
        lines.append(f"    Required: {', '.join(required)}")
        lines.append(f"    All fields: {', '.join(props)}")
    lines.append("")
    lines.append("Tool calls return JSON with {ok: true, result: ...} on success or {error: ...} on failure.")
    lines.append("IMPORTANT: Always pass valid JSON as the second argument. Quote properly for your shell.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude factory + session
# ---------------------------------------------------------------------------

class Claude:
    """Factory for creating sessions with model routing via Claude Code SDK."""

    def __init__(self, config: LoopConfig, state: LoopState):
        self.config = config
        self.state = state

    def session(self, role: AgentRole, system_extra: str = "") -> ClaudeSession:
        model_attr, max_turns, tools_set = role.value
        model = getattr(self.config, model_attr)
        system = load_prompt("system", SPRINT_DIR=str(self.config.sprint_dir))
        if system_extra:
            system += "\n" + system_extra
        system += _tool_cli_instructions(self.config.state_file)
        builtin_tools = list(_TOOL_SETS.get(tools_set, _FULL_TOOLS))

        return ClaudeSession(
            model=model,
            system=system,
            max_turns=max_turns,
            builtin_tools=builtin_tools,
            state=self.state,
            config=self.config,
        )


class ClaudeSession:
    """Single-prompt session using Claude Code SDK."""

    def __init__(
        self,
        model: str,
        system: str,
        max_turns: int = 30,
        builtin_tools: list[str] | None = None,
        state: LoopState | None = None,
        config: LoopConfig | None = None,
    ):
        self.model = model
        self.system = system
        self.max_turns = max_turns
        self.builtin_tools = builtin_tools or []
        self.state = state
        self.config = config

    def send(self, user_message: str, task_source: str = "agent") -> str:
        """Send a prompt to Claude Code, let SDK handle tool execution, return final text."""
        # Save state before query so tool CLI can access it
        if self.state and self.config:
            self.state._current_task_source = task_source  # type: ignore[attr-defined]
            self.state.save(self.config.state_file)

        result = asyncio.run(self._send_async(user_message))

        # Reload state after query (tool CLI may have modified it)
        if self.state and self.config and self.config.state_file.exists():
            from .state import LoopState
            updated = LoopState.load(self.config.state_file)
            # Merge updated fields back into the in-memory state
            _sync_state(self.state, updated)

        return result

    async def _send_async(self, user_message: str) -> str:
        # Allow nested Claude Code sessions (e.g. launched from Claude Code)
        os.environ.pop("CLAUDECODE", None)

        options = ClaudeCodeOptions(
            model=self.model,
            system_prompt=self.system,
            allowed_tools=list(self.builtin_tools),
            permission_mode="bypassPermissions",
            max_turns=self.max_turns,
        )

        text_parts: list[str] = []

        try:
            async for message in query(prompt=user_message, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_parts.append(block.text)
                elif isinstance(message, ResultMessage):
                    if message.usage and self.state:
                        inp = message.usage.get("input_tokens", 0)
                        out = message.usage.get("output_tokens", 0)
                        self.state.total_tokens_used += inp + out
                    if message.is_error:
                        raise RuntimeError(f"Claude Code SDK error: {message.result}")
        except ExceptionGroup as eg:
            # Filter out non-fatal transport cleanup errors
            real = [e for e in eg.exceptions if not isinstance(e, CLIConnectionError)]
            if real:
                raise ExceptionGroup("Claude SDK errors", real) from eg

        return "\n".join(text_parts)


def _sync_state(target: LoopState, source: LoopState) -> None:
    """Copy all dataclass fields from source (disk) back to target (memory).

    Preserves token count from the in-memory state (updated by SDK usage tracking)
    since the tool CLI doesn't know about API-level token consumption.
    """
    from dataclasses import fields
    saved_tokens = target.total_tokens_used
    for f in fields(source):
        setattr(target, f.name, getattr(source, f.name))
    target.total_tokens_used = saved_tokens
