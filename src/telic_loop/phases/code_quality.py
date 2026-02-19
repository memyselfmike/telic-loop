"""Deterministic code quality checks — DRY/SOLID enforcement without LLM calls."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import LoopConfig
    from ..state import LoopState, ProcessMonitorState

# Duplicated from process_monitor.py to avoid circular imports.
_SOURCE_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte",
    ".html", ".css", ".scss", ".less",
    ".java", ".kt", ".go", ".rs", ".c", ".cpp", ".h",
    ".rb", ".php", ".sh", ".sql",
}

_SKIP_DIRS: set[str] = {
    ".", "node_modules", "__pycache__", ".venv", "venv",
    ".git", ".tox", "dist", "build", ".next", ".nuxt",
}

_STYLE_EXTENSIONS: set[str] = {".css", ".scss", ".less"}

_TEST_PATTERNS: set[str] = {"test_", "_test.py", ".test.", ".spec."}

_DEBUG_PY = re.compile(r"(?<!\w)print\s*\(|breakpoint\s*\(|import\s+pdb")
_DEBUG_JS = re.compile(r"console\.(log|debug|info)\s*\(|(?<!\w)debugger\b|alert\s*\(")
_TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
_COMMENT_LINE = re.compile(r"^\s*(#|//|/\*|\*)")


# ---------------------------------------------------------------------------
# Shared file reader
# ---------------------------------------------------------------------------

def _read_source_files(sprint_dir: Path) -> dict[str, str]:
    """Read all source files in sprint_dir. Returns {rel_path: content}."""
    files: dict[str, str] = {}
    if not sprint_dir.is_dir():
        return files

    for path in sprint_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in _SOURCE_EXTENSIONS:
            continue
        parts = path.relative_to(sprint_dir).parts
        if any(p.startswith(".") or p in _SKIP_DIRS for p in parts[:-1]):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(sprint_dir)).replace("\\", "/")
        files[rel] = content

    return files


def _is_test_file(rel_path: str) -> bool:
    """Check if a file path looks like a test file."""
    name = rel_path.rsplit("/", 1)[-1]
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or ".test." in name
        or ".spec." in name
        or "/tests/" in rel_path
        or "/test/" in rel_path
    )


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

def run_all_quality_checks(state: LoopState, config: LoopConfig) -> None:
    """Run all 6 deterministic quality checks and append warnings.

    Must be called AFTER scan_file_line_counts() (which clears warnings first).
    """
    pm = state.process_monitor
    project_dir = Path(config.effective_project_dir)
    source_files = _read_source_files(project_dir)

    _scan_function_lengths(pm, source_files, config)
    _scan_duplicates(pm, source_files, config)
    _scan_prd_structure(pm, config)
    _scan_test_ratio(pm, source_files)
    _scan_todo_debt(pm, source_files)
    _scan_debug_artifacts(pm, source_files)


# ---------------------------------------------------------------------------
# Check 1: Function Length
# ---------------------------------------------------------------------------

def _scan_function_lengths(
    pm: ProcessMonitorState, source_files: dict[str, str], config: LoopConfig
) -> None:
    """Detect functions exceeding max_function_lines threshold."""
    threshold = config.code_health_max_function_lines
    pm.long_functions = {}

    for rel, content in source_files.items():
        if rel.endswith(tuple(_STYLE_EXTENSIONS)):
            continue
        lines = content.splitlines()
        long_fns: list[tuple[str, int]] = []

        if rel.endswith(".py"):
            long_fns = _scan_py_functions(lines, threshold)
        elif rel.endswith((".js", ".ts", ".jsx", ".tsx")):
            long_fns = _scan_js_functions(lines, threshold)

        if long_fns:
            pm.long_functions[rel] = long_fns
            for name, length in long_fns:
                pm.code_health_warnings.append(
                    f"LONG_FUNCTION: {rel}::{name} is {length} lines "
                    f"(threshold: {threshold})"
                )


def _scan_py_functions(lines: list[str], threshold: int) -> list[tuple[str, int]]:
    """Parse Python functions by indentation level."""
    results: list[tuple[str, int]] = []
    func_name: str | None = None
    func_indent: int = -1
    func_start: int = 0

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(stripped)

        if stripped.startswith(("def ", "async def ")):
            # Close previous function if any
            if func_name is not None:
                length = i - func_start
                if length >= threshold:
                    results.append((func_name, length))

            # Start new function
            match = re.match(r"(?:async\s+)?def\s+(\w+)", stripped)
            func_name = match.group(1) if match else "unknown"
            func_indent = indent
            func_start = i

        elif func_name is not None and indent <= func_indent and not stripped.startswith(("@", ")")):
            # Exited function scope
            length = i - func_start
            if length >= threshold:
                results.append((func_name, length))
            func_name = None

    # Handle last function
    if func_name is not None:
        length = len(lines) - func_start
        if length >= threshold:
            results.append((func_name, length))

    return results


def _scan_js_functions(lines: list[str], threshold: int) -> list[tuple[str, int]]:
    """Parse JS/TS functions by brace counting."""
    results: list[tuple[str, int]] = []
    func_re = re.compile(
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)|"
        r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?|"
        r"(\w+)\s*\([^)]*\)\s*\{"
    )

    func_name: str | None = None
    func_start: int = 0
    brace_depth: int = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        if func_name is None:
            m = func_re.match(stripped)
            if m and "{" in line:
                func_name = m.group(1) or m.group(2) or m.group(3) or "anonymous"
                func_start = i
                brace_depth = line.count("{") - line.count("}")
                if brace_depth <= 0:
                    func_name = None
                continue

        if func_name is not None:
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                length = i - func_start + 1
                if length >= threshold:
                    results.append((func_name, length))
                func_name = None

    return results


# ---------------------------------------------------------------------------
# Check 2: Duplicate Blocks
# ---------------------------------------------------------------------------

def _scan_duplicates(
    pm: ProcessMonitorState, source_files: dict[str, str], config: LoopConfig
) -> None:
    """Detect copy-pasted code blocks across different files."""
    min_lines = config.code_health_duplicate_min_lines
    pm.duplicate_blocks = []

    # Build hash → [(file, line_num, preview)] mapping
    block_map: dict[str, list[tuple[str, int, str]]] = defaultdict(list)

    for rel, content in source_files.items():
        if _is_test_file(rel) or rel.endswith(tuple(_STYLE_EXTENSIONS)):
            continue

        lines = content.splitlines()
        # Filter out trivial lines
        meaningful: list[tuple[int, str]] = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if _COMMENT_LINE.match(stripped):
                continue
            if stripped in ("{", "}", "};", ")", "],", "});"):
                continue
            if stripped.startswith(("import ", "from ", "require(")):
                continue
            meaningful.append((i, stripped))

        # Sliding window
        for idx in range(len(meaningful) - min_lines + 1):
            window = meaningful[idx:idx + min_lines]
            normalized = "\n".join(text for _, text in window)
            h = hashlib.md5(normalized.encode()).hexdigest()[:16]
            line_num = window[0][0] + 1
            preview = window[0][1][:80]
            block_map[h].append((rel, line_num, preview))

    # Find blocks appearing in 2+ different files
    seen_pairs: set[tuple[str, ...]] = set()
    for h, locations in block_map.items():
        files_with_block = sorted(set(loc[0] for loc in locations))
        if len(files_with_block) < 2:
            continue

        pair_key = tuple(files_with_block)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        first_loc = locations[0]
        pm.duplicate_blocks.append({
            "hash": h,
            "files": files_with_block,
            "line_count": min_lines,
            "preview": first_loc[2],
        })

        if len(pm.duplicate_blocks) >= 20:
            break

    for dup in pm.duplicate_blocks:
        pm.code_health_warnings.append(
            f"DUPLICATE: {dup['line_count']}-line block in "
            f"{', '.join(dup['files'])} (starts: {dup['preview'][:60]})"
        )


# ---------------------------------------------------------------------------
# Check 3: PRD Structure Conformance
# ---------------------------------------------------------------------------

def _scan_prd_structure(pm: ProcessMonitorState, config: LoopConfig) -> None:
    """Check that files described in the PRD directory tree actually exist."""
    from ..config import LoopConfig  # type: ignore[attr-defined]

    pm.missing_prd_files = []
    prd_path = config.prd_file
    sprint_dir = config.effective_project_dir

    if not prd_path.is_file():
        return

    try:
        prd_content = prd_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return

    expected_files = _parse_prd_tree(prd_content)
    if not expected_files:
        return

    for rel in expected_files:
        full = sprint_dir / rel
        if not full.exists():
            pm.missing_prd_files.append(rel)

    if pm.missing_prd_files:
        pm.code_health_warnings.append(
            f"MISSING_STRUCTURE: {len(pm.missing_prd_files)} file(s) from PRD "
            f"tree not yet created: {', '.join(pm.missing_prd_files[:5])}"
        )


def _parse_prd_tree(content: str) -> list[str]:
    """Parse box-drawing directory tree from PRD content.

    Expects patterns like:
        ├── src/
        │   ├── app.py
        │   └── utils.py
        └── tests/
            └── test_app.py
    """
    tree_re = re.compile(r"^(\s*[│\s]*)[├└]──\s+(.+)$")
    files: list[str] = []
    dir_stack: list[tuple[int, str]] = []  # (depth, dirname)

    in_tree = False
    for line in content.splitlines():
        m = tree_re.match(line)
        if not m:
            if in_tree and line.strip() and not line.strip().startswith("│"):
                in_tree = False
                dir_stack.clear()
            continue

        in_tree = True
        prefix = m.group(1)
        name = m.group(2).strip()

        # Strip inline comments (e.g., "astro.config.mjs  # Comment")
        if "#" in name:
            name = name.split("#")[0].strip()

        # Depth = count of │ characters + extra indentation after last │
        pipe_count = prefix.count("│")
        # Find position of last │, count spaces after it
        last_pipe = prefix.rfind("│")
        if last_pipe >= 0:
            trailing_spaces = len(prefix) - last_pipe - 1
            # Each 4 spaces ≈ one additional depth level
            depth = pipe_count + (trailing_spaces // 4)
        else:
            # No pipes: pure space indentation (e.g., under a root-level dir)
            # Each 4 spaces = one depth level
            depth = len(prefix) // 4

        # Pop stack to current depth
        while dir_stack and dir_stack[-1][0] >= depth:
            dir_stack.pop()

        if name.endswith("/"):
            dir_stack.append((depth, name.rstrip("/")))
        else:
            # Skip db files (auto-generated)
            if name.endswith(".db"):
                continue
            # Build relative path from stack
            path_parts = [d for _, d in dir_stack] + [name]
            files.append("/".join(path_parts))

    return files


# ---------------------------------------------------------------------------
# Check 4: Test Ratio
# ---------------------------------------------------------------------------

def _scan_test_ratio(pm: ProcessMonitorState, source_files: dict[str, str]) -> None:
    """Compute ratio of test files to source files."""
    test_count = 0
    source_count = 0

    for rel in source_files:
        if rel.endswith(tuple(_STYLE_EXTENSIONS)):
            continue
        if rel.endswith(".html"):
            continue
        if _is_test_file(rel):
            test_count += 1
        else:
            source_count += 1

    pm.test_source_ratio = test_count / max(source_count, 1)

    if source_count > 0 and pm.test_source_ratio < 0.5:
        pm.code_health_warnings.append(
            f"LOW_TEST_RATIO: {test_count} test files vs {source_count} source files "
            f"(ratio: {pm.test_source_ratio:.2f}, threshold: 0.50)"
        )


# ---------------------------------------------------------------------------
# Check 5: TODO Debt
# ---------------------------------------------------------------------------

def _scan_todo_debt(pm: ProcessMonitorState, source_files: dict[str, str]) -> None:
    """Count TODO/FIXME/HACK/XXX markers across source files."""
    pm.todo_count = 0

    for content in source_files.values():
        pm.todo_count += len(_TODO_RE.findall(content))

    if pm.todo_count > 5:
        pm.code_health_warnings.append(
            f"TODO_DEBT: {pm.todo_count} TODO/FIXME/HACK/XXX markers "
            f"(threshold: 5)"
        )


# ---------------------------------------------------------------------------
# Check 6: Debug Artifacts
# ---------------------------------------------------------------------------

def _scan_debug_artifacts(
    pm: ProcessMonitorState, source_files: dict[str, str]
) -> None:
    """Detect print(), console.log(), breakpoint(), etc. in production code."""
    pm.debug_artifact_count = 0

    for rel, content in source_files.items():
        # Skip test files and __init__.py
        if _is_test_file(rel):
            continue
        if rel.endswith("__init__.py"):
            continue

        for line in content.splitlines():
            stripped = line.strip()
            # Skip comment lines
            if _COMMENT_LINE.match(stripped):
                continue

            if rel.endswith(".py"):
                if _DEBUG_PY.search(stripped):
                    pm.debug_artifact_count += 1
            elif rel.endswith((".js", ".ts", ".jsx", ".tsx")):
                if _DEBUG_JS.search(stripped):
                    pm.debug_artifact_count += 1

    if pm.debug_artifact_count > 0:
        pm.code_health_warnings.append(
            f"DEBUG_ARTIFACT: {pm.debug_artifact_count} debug statement(s) "
            f"(print/console.log/breakpoint/debugger) in production code"
        )


# ---------------------------------------------------------------------------
# Task Creation — supersedes create_refactoring_tasks()
# ---------------------------------------------------------------------------

def create_quality_tasks(state: LoopState, config: LoopConfig) -> int:
    """Auto-create tasks for code quality violations. Returns count created."""
    from ..state import TaskState

    pm = state.process_monitor
    created = 0

    # Determine epic_id for multi-epic scoping
    epic_id = ""
    if state.vision_complexity == "multi_epic" and state.epics:
        if state.current_epic_index < len(state.epics):
            epic_id = state.epics[state.current_epic_index].epic_id

    # --- REFACTOR tasks for monolithic files (preserves existing behavior) ---
    for rel, lines in pm.file_line_counts.items():
        if lines < config.code_health_monolith_threshold:
            continue
        task_id = f"REFACTOR-{rel.replace('/', '-').replace('.', '-')}"
        target = config.code_health_max_file_lines
        new_task = TaskState(
            task_id=task_id,
            source="code_health",
            description=(
                f"Refactor monolithic file: {rel} ({lines} lines). "
                f"Split into focused modules of <={target} lines each. "
                f"Extract distinct concerns (routing, business logic, data access, "
                f"utilities) into separate files with clear single responsibilities."
            ),
            value=(
                f"Reduce monolithic file risk — {rel} is {lines} lines, "
                f"making it hard to maintain and prone to merge conflicts"
            ),
            acceptance=(
                f"File {rel} is split into multiple files, each <={target} lines. "
                f"All existing tests still pass. No functionality is lost."
            ),
            epic_id=epic_id,
            created_at=datetime.now().isoformat(),
        )
        created += _upsert_task(
            state, task_id, epic_id, new_task,
            f"Refactor monolithic file: {rel} (still {lines} lines after "
            f"previous attempt). Split into focused modules of "
            f"<={target} lines each."
        )

    # --- SPLIT-FN tasks for long functions ---
    refactor_files = {
        rel for rel, lines in pm.file_line_counts.items()
        if lines >= config.code_health_monolith_threshold
    }
    for rel, long_fns in pm.long_functions.items():
        if rel in refactor_files:
            continue  # already has a REFACTOR task
        task_id = f"SPLIT-FN-{rel.replace('/', '-').replace('.', '-')}"
        fn_list = ", ".join(f"{name}({length}L)" for name, length in long_fns[:5])
        new_task = TaskState(
            task_id=task_id,
            source="code_health",
            description=(
                f"Split long functions in {rel}: {fn_list}. "
                f"Extract helper functions to keep each function under "
                f"{config.code_health_max_function_lines} lines."
            ),
            value=f"Improve readability and testability of {rel}",
            acceptance=(
                f"No function in {rel} exceeds {config.code_health_max_function_lines} lines. "
                f"All existing tests still pass."
            ),
            epic_id=epic_id,
            created_at=datetime.now().isoformat(),
        )
        created += _upsert_task(
            state, task_id, epic_id, new_task,
            f"Long functions still present in {rel}: {fn_list}"
        )

    # --- DEDUP tasks for duplicate blocks ---
    dedup_count = 0
    for dup in pm.duplicate_blocks:
        if dedup_count >= config.code_health_max_duplicate_tasks:
            break
        files_slug = "-".join(
            f.rsplit("/", 1)[-1].split(".")[0] for f in dup["files"][:2]
        )
        task_id = f"DEDUP-{dup['hash'][:8]}-{files_slug}"
        file_list = ", ".join(dup["files"])
        new_task = TaskState(
            task_id=task_id,
            source="code_health",
            description=(
                f"Extract duplicate code block into shared module. "
                f"Found in: {file_list}. "
                f"Block starts with: {dup['preview'][:60]}"
            ),
            value=f"Remove code duplication across {file_list}",
            acceptance=(
                f"Duplicate block extracted into a shared function/module. "
                f"Both files import from the shared location. "
                f"All existing tests still pass."
            ),
            epic_id=epic_id,
            created_at=datetime.now().isoformat(),
        )
        created += _upsert_task(state, task_id, epic_id, new_task, new_task.description)
        dedup_count += 1

    # --- CLEANUP tasks ---
    if pm.todo_count > config.code_health_max_todo_count:
        task_id = "CLEANUP-todo-debt"
        new_task = TaskState(
            task_id=task_id,
            source="code_health",
            description=(
                f"Resolve {pm.todo_count} TODO/FIXME/HACK/XXX markers. "
                f"Either implement the TODO, remove it if already done, "
                f"or convert to a tracked issue."
            ),
            value="Reduce technical debt markers in production code",
            acceptance=(
                f"No more than {config.code_health_max_todo_count} TODO markers remain."
            ),
            epic_id=epic_id,
            created_at=datetime.now().isoformat(),
        )
        created += _upsert_task(
            state, task_id, epic_id, new_task,
            f"Still {pm.todo_count} TODO markers (max: {config.code_health_max_todo_count})"
        )

    if pm.debug_artifact_count > 0:
        task_id = "CLEANUP-debug-artifacts"
        new_task = TaskState(
            task_id=task_id,
            source="code_health",
            description=(
                f"Remove {pm.debug_artifact_count} debug statement(s) "
                f"(print/console.log/breakpoint/debugger) from production code. "
                f"Replace with proper logging if output is needed."
            ),
            value="Remove debug artifacts before shipping",
            acceptance="Zero print/console.log/breakpoint/debugger in non-test files.",
            epic_id=epic_id,
            created_at=datetime.now().isoformat(),
        )
        created += _upsert_task(
            state, task_id, epic_id, new_task,
            f"Still {pm.debug_artifact_count} debug artifacts in production code"
        )

    if pm.missing_prd_files:
        task_id = "STRUCTURE-prd-conformance"
        missing_list = ", ".join(pm.missing_prd_files[:10])
        new_task = TaskState(
            task_id=task_id,
            source="code_health",
            description=(
                f"Create missing files from PRD directory structure: {missing_list}. "
                f"These files are defined in the PRD but have not been created yet."
            ),
            value="Ensure project structure matches PRD specification",
            acceptance="All files listed in PRD directory tree exist on disk.",
            epic_id=epic_id,
            created_at=datetime.now().isoformat(),
        )
        created += _upsert_task(
            state, task_id, epic_id, new_task,
            f"PRD files still missing: {missing_list}"
        )

    return created


def _upsert_task(
    state: LoopState,
    task_id: str,
    epic_id: str,
    new_task: object,
    reopen_description: str,
) -> int:
    """Insert or reopen a quality task. Returns 1 if created/reopened, 0 otherwise."""
    from ..state import TaskState

    if task_id in state.tasks:
        existing = state.tasks[task_id]
        if existing.status in ("in_progress", "pending"):
            return 0
        if existing.status == "descoped":
            return 0  # Respect manual descope decisions
        if existing.status == "done":
            existing.status = "pending"
            existing.retry_count += 1
            existing.description = reopen_description
            print(f"    -> Reopened quality task {task_id}")
            return 1
        return 0

    assert isinstance(new_task, TaskState)
    state.add_task(new_task)
    print(f"    -> Created quality task {task_id}")
    return 1
