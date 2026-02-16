"""Anthropic SDK wrapper: Claude class, ClaudeSession, AgentRole model routing."""

from __future__ import annotations

import time
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import anthropic
from anthropic import APIConnectionError, APIStatusError, APITimeoutError

if TYPE_CHECKING:
    from .config import LoopConfig
    from .state import LoopState

STREAMING_THRESHOLD = 21333

CONTEXT_LIMITS = {
    "claude-opus-4-6": 200_000,
    "claude-sonnet-4-5-20250929": 200_000,
    "claude-haiku-4-5-20251001": 200_000,
}
CONTEXT_WARN_PCT = 0.80


class AgentRole(Enum):
    """(model_config_attr, max_turns, thinking_effort, max_tokens)"""
    REASONER   = ("model_reasoning",  40, "max",  32768)
    EVALUATOR  = ("model_reasoning",  40, "high", 32768)
    RESEARCHER = ("model_reasoning",  30, "high", 16384)
    BUILDER    = ("model_execution",  60, None,   16384)
    FIXER      = ("model_execution",  25, None,   16384)
    QC         = ("model_execution",  30, None,   16384)
    CLASSIFIER = ("model_triage",      5, None,    4096)


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (Path(__file__).parent / "prompts" / f"{name}.md").read_text()


class Claude:
    """Factory for creating sessions with model routing."""

    def __init__(self, config: LoopConfig, state: LoopState):
        self.config = config
        self.client = anthropic.Anthropic()
        self.beta_headers = ["web-fetch-2025-09-10"]
        self.state = state

    def session(self, role: AgentRole, system_extra: str = "") -> ClaudeSession:
        from .tools import get_tools_for_role

        model_attr, max_turns, thinking_effort, max_tokens = role.value
        system = load_prompt("system") + ("\n" + system_extra if system_extra else "")
        tools = get_tools_for_role(role)
        has_provider_tools = any(
            t.get("type", "").startswith("web_fetch") or t.get("type", "").startswith("web_search")
            for t in tools
        )
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


class ClaudeSession:
    """Multi-turn conversation with tool execution."""

    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str,
        system: str,
        max_turns: int = 30,
        thinking_effort: str | None = None,
        max_tokens: int = 16384,
        tools: list[dict] | None = None,
        state: LoopState | None = None,
        betas: list[str] | None = None,
    ):
        self.client = client
        self.model = model
        self.system = system
        self.messages: list[dict] = []
        self.max_turns = max_turns
        self.thinking_effort = thinking_effort
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.state = state
        self.betas = betas
        self.use_streaming = max_tokens > STREAMING_THRESHOLD
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.context_limit = CONTEXT_LIMITS.get(model, 200_000)

    def send(self, user_message: str, task_source: str = "agent") -> str:
        """Send message, execute tools in loop, return final text."""
        from .tools import execute_tool

        self.messages.append({"role": "user", "content": user_message})

        for _turn in range(self.max_turns):
            if self.total_input_tokens > self.context_limit * CONTEXT_WARN_PCT:
                self._truncate_context()

            kwargs: dict = dict(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system,
                messages=self.messages,
                tools=self.tools,
            )
            if self.betas:
                kwargs["betas"] = self.betas
            if self.thinking_effort:
                kwargs["thinking"] = {"type": "adaptive"}
                kwargs["output_config"] = {"effort": self.thinking_effort}

            api = self.client.beta.messages if self.betas else self.client.messages
            response = self._api_call_with_retry(api, kwargs)

            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens
            if self.state:
                self.state.total_tokens_used += (
                    response.usage.input_tokens + response.usage.output_tokens
                )

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "pause_turn":
                continue

            # Process tool_use blocks BEFORE checking end_turn
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(
                        block.name, block.input, self.state,
                        task_source=task_source,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            if tool_results:
                self.messages.append({"role": "user", "content": tool_results})
            elif response.stop_reason == "end_turn":
                return self._extract_text(response)

        raise RuntimeError(f"Agent exceeded max_turns ({self.max_turns})")

    def _send_streaming(self, api=None, **kwargs):
        target = api or self.client.messages
        with target.stream(**kwargs) as stream:
            return stream.get_final_message()

    def _extract_text(self, response) -> str:
        return "\n".join(b.text for b in response.content if hasattr(b, "text"))

    def _api_call_with_retry(self, api, kwargs, max_retries: int = 3):
        for attempt in range(max_retries + 1):
            try:
                if self.use_streaming:
                    return self._send_streaming(api=api, **kwargs)
                else:
                    return api.create(**kwargs)
            except (APITimeoutError, APIConnectionError) as e:
                if attempt == max_retries:
                    raise
                wait = 2 ** attempt
                print(f"  API transient error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
            except APIStatusError as e:
                if e.status_code in (429, 529) and attempt < max_retries:
                    retry_after = int(e.response.headers.get("retry-after", 2 ** attempt))
                    print(f"  API {e.status_code} (attempt {attempt + 1}/{max_retries + 1})")
                    print(f"  Retrying in {retry_after}s...")
                    time.sleep(retry_after)
                else:
                    raise
        raise RuntimeError("Retry loop exited without returning or raising")

    def _truncate_context(self) -> None:
        if len(self.messages) <= 6:
            return
        preserved_start = self.messages[:1]
        preserved_end = self.messages[-4:]
        removed_count = len(self.messages) - 5
        summary = {
            "role": "user",
            "content": f"[{removed_count} earlier messages truncated to stay within context window]",
        }
        self.messages = preserved_start + [summary] + preserved_end
        print(
            f"  CONTEXT MANAGEMENT: truncated {removed_count} messages "
            f"(token usage at {self.total_input_tokens:,})"
        )
