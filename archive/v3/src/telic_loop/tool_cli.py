"""CLI bridge for structured tool execution.

Claude Code calls this via Bash to invoke structured tools (manage_task,
report_vrc, etc.) that mutate LoopState. State is loaded from disk,
modified, and saved back — the loop reloads after each query.

Usage:
    python -m telic_loop.tool_cli --state-file <path> <tool_name> <json_input>

Example:
    python -m telic_loop.tool_cli --state-file sprints/s1/.loop_state.json \
        manage_task '{"action":"add","task_id":"T1","description":"...", ...}'
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    args = sys.argv[1:]

    # Parse --state-file
    if "--state-file" not in args or len(args) < 4:
        print(json.dumps({"error": "Usage: tool_cli --state-file <path> <tool_name> <json>"}))
        sys.exit(1)

    sf_idx = args.index("--state-file")
    state_path = Path(args[sf_idx + 1])
    remaining = args[:sf_idx] + args[sf_idx + 2:]

    # Parse optional --task-source (default "agent")
    task_source = "agent"
    if "--task-source" in remaining:
        ts_idx = remaining.index("--task-source")
        if ts_idx + 1 < len(remaining):
            task_source = remaining[ts_idx + 1]
            remaining = remaining[:ts_idx] + remaining[ts_idx + 2:]

    if len(remaining) < 2:
        print(json.dumps({"error": "Missing tool_name or json_input"}))
        sys.exit(1)

    tool_name = remaining[0]
    json_input = remaining[1]

    # Load state
    from .state import LoopState
    if not state_path.exists():
        print(json.dumps({"error": f"State file not found: {state_path}"}))
        sys.exit(1)

    state = LoopState.load(state_path)

    # Parse input
    try:
        input_data = json.loads(json_input)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    # Execute tool
    from .tools import execute_tool
    result = execute_tool(tool_name, input_data, state, task_source=task_source)

    # Save state back
    state.save(state_path)

    # Print result
    print(result)


if __name__ == "__main__":
    main()
