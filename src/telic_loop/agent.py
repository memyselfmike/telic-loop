"""Claude Agent SDK wrapper: Agent factory, ClaudeSession, role-based model routing.

V4 Roles (4 instead of V3's 7):
- PLANNER:   Opus, 40 turns, Full + Web   — context discovery, plan creation
- REVIEWER:  Opus, 20 turns, Read-only     — plan quality review (separate context)
- BUILDER:   Sonnet, 60 turns, Full        — implementation, verification, fixing
- EVALUATOR: Opus, 40 turns, Read-only + Playwright — adversarial quality evaluation
"""

from __future__ import annotations

import asyncio
import os
import re
import time
from collections.abc import AsyncGenerator, AsyncIterable
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import (
    AssistantMessage,
    CLIConnectionError,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

if TYPE_CHECKING:
    from .config import LoopConfig
    from .state import LoopState

# Claude Code built-in tool sets (per role)
_FULL_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
_READONLY_TOOLS = ["Read", "Glob", "Grep", "Bash"]
_FULL_PLUS_WEB = ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch"]

# Playwright MCP tools available when browser evaluation is enabled
PLAYWRIGHT_MCP_TOOLS = [
    "mcp__playwright__browser_navigate",
    "mcp__playwright__browser_click",
    "mcp__playwright__browser_fill",
    "mcp__playwright__browser_snapshot",
    "mcp__playwright__browser_take_screenshot",
    "mcp__playwright__browser_select_option",
    "mcp__playwright__browser_go_back",
    "mcp__playwright__browser_go_forward",
    "mcp__playwright__browser_wait",
    "mcp__playwright__browser_press_key",
    "mcp__playwright__browser_resize",
    "mcp__playwright__browser_tab_list",
    "mcp__playwright__browser_tab_new",
    "mcp__playwright__browser_tab_select",
    "mcp__playwright__browser_tab_close",
]

# Windows CreateProcess limits command line to ~32K chars.
_WIN_CMD_LIMIT = 30_000


class RateLimitError(RuntimeError):
    """Claude Max session allowance exhausted — caller should sleep until reset."""

    def __init__(self, message: str, reset_hint: str = ""):
        super().__init__(message)
        self.reset_hint = reset_hint


class AgentRole(Enum):
    """(model_config_attr, timeout_config_attr, max_turns, tool_set)"""
    PLANNER   = ("model_reasoning", "sdk_timeout_reasoning", 40, "full_web")
    REVIEWER  = ("model_reasoning", "sdk_timeout_reasoning", 20, "readonly")
    BUILDER   = ("model_execution",  "sdk_timeout_building",  60, "full")
    EVALUATOR = ("model_reasoning", "sdk_timeout_reasoning", 40, "readonly")


def load_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template and safely format placeholders.

    Uses string replacement instead of str.format() to avoid conflicts
    with literal braces in JSON examples within prompt templates.
    """
    template = (Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")
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
# Agent factory + session
# ---------------------------------------------------------------------------

_TOOL_SET_MAP = {
    "full": _FULL_TOOLS,
    "readonly": _READONLY_TOOLS,
    "full_web": _FULL_PLUS_WEB,
}


class Agent:
    """Factory for creating sessions with model routing via Claude Code SDK."""

    def __init__(self, config: LoopConfig, state: LoopState):
        self.config = config
        self.state = state

    def session(
        self,
        role: AgentRole,
        system_extra: str = "",
        mcp_servers: dict | None = None,
        extra_tools: list[str] | None = None,
    ) -> ClaudeSession:
        model_attr, timeout_attr, max_turns, tools_key = role.value
        model = getattr(self.config, model_attr)
        timeout = getattr(self.config, timeout_attr)

        system = load_prompt("system",
            SPRINT_DIR=str(self.config.sprint_dir),
            PROJECT_DIR=str(self.config.effective_project_dir),
        )
        if system_extra:
            system += "\n" + system_extra
        system += _tool_cli_instructions(self.config.state_file)

        builtin_tools = list(_TOOL_SET_MAP.get(tools_key, _FULL_TOOLS))
        if extra_tools:
            builtin_tools.extend(extra_tools)

        return ClaudeSession(
            model=model,
            system=system,
            max_turns=max_turns,
            builtin_tools=builtin_tools,
            state=self.state,
            config=self.config,
            mcp_servers=mcp_servers,
            timeout_sec=timeout,
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
        mcp_servers: dict | None = None,
        timeout_sec: int = 300,
    ):
        self.model = model
        self.system = system
        self.max_turns = max_turns
        self.timeout_sec = timeout_sec
        self.builtin_tools = builtin_tools or []
        self.state = state
        self.config = config
        self.mcp_servers = mcp_servers or {}

    def send(self, user_message: str, task_source: str = "agent") -> str:
        """Send a prompt to Claude Code, let SDK handle tool execution, return final text.

        Retries up to 3 times on transient failures with classified exponential
        backoff. Non-retryable errors bail immediately.
        """
        from .errors import (
            FailureTrail, backoff_seconds, classify_error, parse_retry_after,
        )

        max_attempts = 3
        last_exc: Exception | None = None
        trail = FailureTrail()

        # Pull backoff config if available
        base = self.config.retry_backoff_base if self.config else 1.0
        cap = self.config.retry_backoff_cap if self.config else 30.0

        for attempt in range(max_attempts):
            t0 = time.perf_counter()
            try:
                # Save state before query so tool CLI can access it
                if self.state and self.config:
                    self.state._current_task_source = task_source  # type: ignore[attr-defined]
                    self.state.save(self.config.state_file)

                result = asyncio.run(self._send_async(user_message))
                self._reload_state_from_disk()
                return result

            except RateLimitError:
                raise  # Don't retry rate limits — caller handles with smart sleep

            except Exception as exc:
                elapsed = time.perf_counter() - t0
                error_kind = classify_error(exc)

                # Sync state from disk — tool CLI may have written progress
                self._reload_state_from_disk()

                # Non-retryable errors bail immediately
                if error_kind == "non_retryable":
                    trail.record(attempt, error_kind, exc, elapsed, 0.0)
                    exc._failure_trail = trail  # type: ignore[attr-defined]
                    raise

                last_exc = exc

                if attempt < max_attempts - 1:
                    # Check for server-provided retry hint
                    wait = parse_retry_after(str(exc), cap=cap)
                    if wait is None:
                        wait = backoff_seconds(attempt, base=base, cap=cap)
                    trail.record(attempt, error_kind, exc, elapsed, wait)
                    print(f"  SDK session failed (attempt {attempt + 1}/{max_attempts},"
                          f" {error_kind}), retrying in {wait:.0f}s...")
                    time.sleep(wait)
                else:
                    trail.record(attempt, error_kind, exc, elapsed, 0.0)

        # Attach failure trail to the exception for downstream logging
        if last_exc is not None:
            last_exc._failure_trail = trail  # type: ignore[attr-defined]
        raise last_exc  # type: ignore[misc]

    def _reload_state_from_disk(self) -> None:
        """Reload state from disk after a query — tool CLI may have modified it."""
        if self.state and self.config and self.config.state_file.exists():
            from .state import LoopState
            updated = LoopState.load(self.config.state_file)
            _sync_state(self.state, updated)

    async def _send_async(self, user_message: str) -> str:
        # Allow nested Claude Code sessions
        os.environ.pop("CLAUDECODE", None)

        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=self.system,
            allowed_tools=list(self.builtin_tools),
            permission_mode="bypassPermissions",
            max_turns=self.max_turns,
            mcp_servers=self.mcp_servers if self.mcp_servers else {},
            max_buffer_size=10 * 1024 * 1024,  # 10MB — handles large prompts + screenshots
        )

        # Estimate CLI arg size; switch to streaming mode if too large for Windows
        estimated_cli_len = len(self.system or "") + len(user_message) + 500
        prompt: str | AsyncIterable[dict[str, Any]]
        if estimated_cli_len > _WIN_CMD_LIMIT:
            prompt = _streaming_prompt(user_message)
        else:
            prompt = user_message

        text_parts: list[str] = []

        try:
            async with asyncio.timeout(self.timeout_sec) as deadline:
                async for message in query(prompt=prompt, options=options):
                    # Heartbeat: reset timeout on each message so active sessions
                    # aren't killed. Only truly idle sessions hit the deadline.
                    deadline.reschedule(asyncio.get_event_loop().time() + self.timeout_sec)
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                text_parts.append(block.text)
                    elif isinstance(message, ResultMessage):
                        if message.usage and self.state:
                            inp = message.usage.get("input_tokens", 0)
                            out = message.usage.get("output_tokens", 0)
                            self.state.total_tokens_used += inp + out
                            self.state.total_input_tokens += inp
                            self.state.total_output_tokens += out
                        if message.is_error:
                            result_text = str(message.result or "")
                            if _is_rate_limit_error(result_text):
                                raise RateLimitError(
                                    f"Claude Code SDK rate limit: {result_text}",
                                    reset_hint=result_text,
                                )
                            raise RuntimeError(f"Claude Code SDK error: {result_text}")
        except TimeoutError:
            raise RuntimeError(
                f"SDK query timed out after {self.timeout_sec}s"
            )
        except ExceptionGroup as eg:
            real = [e for e in eg.exceptions if not isinstance(e, CLIConnectionError)]
            if real:
                raise ExceptionGroup("Claude SDK errors", real) from eg
            else:
                raise RuntimeError(
                    f"Claude CLI connection failed ({len(eg.exceptions)} errors): {eg.exceptions[0]}"
                ) from eg

        return "\n".join(text_parts)


async def _streaming_prompt(user_message: str) -> AsyncGenerator[dict[str, Any]]:
    """Yield a single user message in the SDK's stream-json format."""
    yield {
        "type": "user",
        "message": {"role": "user", "content": user_message},
    }


def _is_rate_limit_error(text: str) -> bool:
    """Detect rate-limit / quota errors from Claude SDK output."""
    from .errors import _RATE_LIMIT_PATTERNS
    lower = text.lower()
    return any(phrase in lower for phrase in _RATE_LIMIT_PATTERNS)


def parse_rate_limit_wait_seconds(error: RateLimitError) -> int:
    """Parse the reset time from a rate limit error and return seconds to wait."""
    from datetime import datetime, timedelta

    hint = error.reset_hint or str(error)
    match = re.search(r"resets\s+(\d{1,2})\s*(am|pm)", hint, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        ampm = match.group(2).lower()
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0

        now = datetime.now()
        reset_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if reset_time <= now:
            reset_time += timedelta(days=1)

        wait = int((reset_time - now).total_seconds())
        return min(wait + 120, 7200)  # +2min buffer, cap at 2 hours

    return 1800  # 30 minute default


def _sync_state(target: LoopState, source: LoopState) -> None:
    """Copy all dataclass fields from source (disk) back to target (memory).

    Preserves token count from the in-memory state (updated by SDK usage tracking)
    since the tool CLI doesn't know about API-level token consumption.
    """
    from dataclasses import fields
    saved_tokens = target.total_tokens_used
    saved_input = target.total_input_tokens
    saved_output = target.total_output_tokens
    for f in fields(source):
        setattr(target, f.name, getattr(source, f.name))
    target.total_tokens_used = saved_tokens
    target.total_input_tokens = saved_input
    target.total_output_tokens = saved_output
