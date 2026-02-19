"""Context Discovery: derive sprint context from Vision + PRD + codebase."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .claude import Claude
    from .config import LoopConfig
    from .state import LoopState, RefinementState


def validate_inputs(config: LoopConfig) -> list[str]:
    """Validate that required input files exist. Returns list of errors."""
    errors = []
    if not config.vision_file.exists():
        errors.append(f"Vision file not found: {config.vision_file}")
    if not config.prd_file.exists():
        errors.append(f"PRD file not found: {config.prd_file}")
    if not config.sprint_dir.exists():
        errors.append(f"Sprint directory not found: {config.sprint_dir}")
    return errors


def discover_context(config: LoopConfig, claude: Claude, state: LoopState) -> None:
    """Run Context Discovery agent to populate state.context (SprintContext).

    Uses REASONER (Opus) with discover_context.md prompt. Pre-computes
    environment data (tool versions, project markers, file tree, services)
    to reduce the number of LLM turns from ~30 to ~5.
    """
    from .claude import AgentRole, load_prompt

    precomputed = _precompute_environment(config)

    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("discover_context",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        PROJECT_DIR=str(config.effective_project_dir),
        PRECOMPUTED_ENV=precomputed,
    )
    session.send(prompt)

    # report_discovery tool handler populates state.context
    if state.context.unresolved_questions:
        print("  DISCOVERY needs clarification:")
        for q in state.context.unresolved_questions:
            print(f"    ? {q}")


# ---------------------------------------------------------------------------
# Pre-computation: gather environment data before the LLM session
# ---------------------------------------------------------------------------

def _precompute_environment(config: "LoopConfig") -> str:
    """Pre-compute environment data to inject into the discovery prompt.

    Gathers tool versions, project markers, file tree, and service indicators
    in Python — work that would otherwise cost ~25 Opus reasoning turns.
    """
    try:
        project_dir = config.effective_project_dir
        tool_versions = _detect_tool_versions()
        markers = _detect_project_markers(project_dir)
        file_tree, test_files = _scan_project_files(project_dir)
        services = _detect_services(project_dir, markers)
        return _format_precomputed(tool_versions, markers, file_tree, test_files, services)
    except Exception as exc:
        return (
            f"Pre-computation failed ({exc}). Please discover the environment "
            "manually using the steps below."
        )


def _run_tool(cmd: list[str], timeout: int = 5) -> str | None:
    """Run a command and return stdout, or None if unavailable/timed out."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _detect_tool_versions() -> dict[str, Any]:
    """Detect installed tool versions via subprocess calls."""
    tools: dict[str, str | None] = {}

    checks = [
        ("Python", ["python", "--version"]),
        ("pip", ["pip", "--version"]),
        ("Node.js", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("pnpm", ["pnpm", "--version"]),
        ("yarn", ["yarn", "--version"]),
        ("cargo", ["cargo", "--version"]),
        ("Go", ["go", "version"]),
        ("Docker", ["docker", "--version"]),
        ("make", ["make", "--version"]),
        ("uv", ["uv", "--version"]),
    ]
    for name, cmd in checks:
        raw = _run_tool(cmd)
        if raw:
            # Normalize: take first line, strip common prefixes
            first_line = raw.split("\n")[0]
            tools[name] = first_line
        else:
            tools[name] = None

    # pip packages — single call replaces ~10 agent turns
    pip_packages: list[dict] = []
    if tools.get("Python"):
        raw = _run_tool(["pip", "list", "--format=json"], timeout=15)
        if raw:
            try:
                pip_packages = json.loads(raw)
            except json.JSONDecodeError:
                pass

    return {"tools": tools, "pip_packages": pip_packages}


def _detect_project_markers(project_dir: Path) -> dict[str, Any]:
    """Detect project marker files and extract key metadata."""
    markers: dict[str, Any] = {}

    # package.json
    pkg_json = project_dir / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
            markers["package.json"] = {
                "name": data.get("name", ""),
                "dependencies": list(data.get("dependencies", {}).keys()),
                "devDependencies": list(data.get("devDependencies", {}).keys()),
                "scripts": list(data.get("scripts", {}).keys()),
            }
        except (json.JSONDecodeError, OSError):
            markers["package.json"] = {"error": "found but could not parse"}

    # pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    if pyproject.is_file():
        try:
            import tomllib
            data = tomllib.loads(pyproject.read_text(encoding="utf-8", errors="replace"))
            project_section = data.get("project", {})
            markers["pyproject.toml"] = {
                "name": project_section.get("name", ""),
                "dependencies": project_section.get("dependencies", []),
                "build_system": data.get("build-system", {}).get("requires", []),
            }
        except Exception:
            markers["pyproject.toml"] = {"error": "found but could not parse"}

    # requirements.txt
    reqs_txt = project_dir / "requirements.txt"
    if reqs_txt.is_file():
        try:
            lines = reqs_txt.read_text(encoding="utf-8", errors="replace").splitlines()
            pkgs = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    pkgs.append(re.split(r"[>=<!\[]", line)[0].strip())
            markers["requirements.txt"] = {"packages": pkgs}
        except OSError:
            markers["requirements.txt"] = {"error": "found but could not read"}

    # Cargo.toml
    cargo = project_dir / "Cargo.toml"
    if cargo.is_file():
        try:
            content = cargo.read_text(encoding="utf-8", errors="replace")
            name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
            markers["Cargo.toml"] = {"name": name_match.group(1) if name_match else ""}
        except OSError:
            markers["Cargo.toml"] = {"error": "found but could not read"}

    # go.mod
    gomod = project_dir / "go.mod"
    if gomod.is_file():
        try:
            content = gomod.read_text(encoding="utf-8", errors="replace")
            mod_match = re.search(r"^module\s+(\S+)", content, re.MULTILINE)
            markers["go.mod"] = {"module": mod_match.group(1) if mod_match else ""}
        except OSError:
            markers["go.mod"] = {"error": "found but could not read"}

    # docker-compose.yml / .yaml
    for name in ("docker-compose.yml", "docker-compose.yaml"):
        compose = project_dir / name
        if compose.is_file():
            try:
                content = compose.read_text(encoding="utf-8", errors="replace")
                # Extract service names: lines indented 2-4 spaces ending with ':'
                # that appear after a 'services:' line
                services = []
                in_services = False
                for line in content.splitlines():
                    if re.match(r"^services:\s*$", line):
                        in_services = True
                        continue
                    if in_services:
                        svc_match = re.match(r"^\s{2,4}(\w[\w-]*):\s*$", line)
                        if svc_match:
                            services.append(svc_match.group(1))
                        elif re.match(r"^\S", line):
                            in_services = False
                markers[name] = {"services": services}
            except OSError:
                markers[name] = {"error": "found but could not read"}
            break

    # Simple existence checks
    for name in ("Dockerfile", "Makefile", "CMakeLists.txt", "setup.py"):
        if (project_dir / name).is_file():
            markers[name] = {"exists": True}

    # .env / .env.example — variable names only, NEVER values
    for name in (".env", ".env.example"):
        env_file = project_dir / name
        if env_file.is_file():
            try:
                content = env_file.read_text(encoding="utf-8", errors="replace")
                var_names = []
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        var_names.append(line.split("=", 1)[0].strip())
                markers[name] = {"vars": var_names}
            except OSError:
                markers[name] = {"error": "found but could not read"}

    return markers


def _scan_project_files(project_dir: Path) -> tuple[dict[str, int], list[str]]:
    """Scan project directory for source files with line counts and test files.

    Returns (file_tree, test_files) without mutating any state.
    """
    from .phases.process_monitor import _SOURCE_EXTENSIONS, _SKIP_DIRS

    file_tree: dict[str, int] = {}
    test_files: list[str] = []

    if not project_dir.is_dir():
        return file_tree, test_files

    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in _SOURCE_EXTENSIONS:
            continue
        parts = path.relative_to(project_dir).parts
        if any(p.startswith(".") or p in _SKIP_DIRS for p in parts[:-1]):
            continue
        try:
            line_count = len(
                path.read_text(encoding="utf-8", errors="replace").splitlines()
            )
        except OSError:
            continue
        rel = str(path.relative_to(project_dir)).replace("\\", "/")
        file_tree[rel] = line_count

        # Classify test files
        stem = path.stem.lower()
        dir_parts = {p.lower() for p in parts[:-1]}
        if (
            stem.startswith("test_")
            or stem.endswith("_test")
            or stem.endswith(".test")
            or stem.endswith(".spec")
            or dir_parts & {"tests", "test", "__tests__"}
        ):
            test_files.append(rel)

    return file_tree, test_files


def _detect_services(
    project_dir: Path, markers: dict[str, Any],
) -> list[str]:
    """Infer services from config files and project markers."""
    services: list[str] = []

    # SQLite databases on disk
    for ext in ("*.db", "*.sqlite", "*.sqlite3"):
        for db_path in project_dir.glob(f"**/{ext}"):
            # Skip hidden dirs
            try:
                parts = db_path.relative_to(project_dir).parts
            except ValueError:
                continue
            if any(p.startswith(".") for p in parts[:-1]):
                continue
            rel = str(db_path.relative_to(project_dir)).replace("\\", "/")
            services.append(f"SQLite: {rel} (exists on disk)")

    # Docker services from compose file
    for name in ("docker-compose.yml", "docker-compose.yaml"):
        marker = markers.get(name)
        if marker and "services" in marker:
            for svc in marker["services"]:
                services.append(f"Docker service: {svc} (from {name})")

    # Environment variable hints
    for name in (".env", ".env.example"):
        marker = markers.get(name)
        if marker and "vars" in marker:
            db_hints = [
                v for v in marker["vars"]
                if any(kw in v.upper() for kw in (
                    "DATABASE", "DB_", "REDIS", "MONGO", "POSTGRES",
                    "MYSQL", "SQLITE",
                ))
            ]
            if db_hints:
                services.append(
                    f"Environment hints ({name}): {', '.join(db_hints)}"
                )

    return services


def _format_precomputed(
    tool_versions: dict[str, Any],
    markers: dict[str, Any],
    file_tree: dict[str, int],
    test_files: list[str],
    services: list[str],
) -> str:
    """Format pre-computed data as readable text for prompt injection."""
    sections: list[str] = []
    sections.append(
        "The following data was gathered automatically. You do NOT need to "
        "re-check these items. Focus your turns on classification, verification "
        "strategy, value proofs, and reasoning. If any data below seems wrong "
        "or incomplete, you may verify it, but do not re-discover what is "
        "already provided."
    )

    # Tool versions
    lines = ["### Tool Versions"]
    for name, version in tool_versions.get("tools", {}).items():
        lines.append(f"  {name}: {version or 'not found'}")
    sections.append("\n".join(lines))

    # pip packages
    pip_pkgs = tool_versions.get("pip_packages", [])
    if pip_pkgs:
        pkg_strs = [f"{p['name']} {p.get('version', '')}" for p in pip_pkgs[:50]]
        lines = [f"### Python Packages ({len(pip_pkgs)} installed)"]
        lines.append(f"  {', '.join(pkg_strs)}")
        if len(pip_pkgs) > 50:
            lines.append(f"  ... and {len(pip_pkgs) - 50} more")
        sections.append("\n".join(lines))

    # Project markers
    if markers:
        lines = ["### Project Markers"]
        for name, data in markers.items():
            if "error" in data:
                lines.append(f"  {name}: {data['error']}")
            elif "exists" in data:
                lines.append(f"  {name}: found")
            elif name == "package.json":
                deps = ", ".join(data.get("dependencies", [])[:15])
                dev_deps = ", ".join(data.get("devDependencies", [])[:10])
                scripts = ", ".join(data.get("scripts", []))
                parts = [f'name="{data.get("name", "")}"']
                if deps:
                    parts.append(f"deps=[{deps}]")
                if dev_deps:
                    parts.append(f"devDeps=[{dev_deps}]")
                if scripts:
                    parts.append(f"scripts=[{scripts}]")
                lines.append(f"  {name}: {', '.join(parts)}")
            elif name == "pyproject.toml":
                deps = data.get("dependencies", [])
                dep_names = []
                for d in deps[:15]:
                    dep_names.append(re.split(r"[>=<!\[]", d)[0].strip() if isinstance(d, str) else str(d))
                parts = [f'name="{data.get("name", "")}"']
                if dep_names:
                    parts.append(f"deps=[{', '.join(dep_names)}]")
                build = data.get("build_system", [])
                if build:
                    parts.append(f"build=[{', '.join(str(b) for b in build[:5])}]")
                lines.append(f"  {name}: {', '.join(parts)}")
            elif name == "requirements.txt":
                pkgs = ", ".join(data.get("packages", [])[:20])
                lines.append(f"  {name}: [{pkgs}]")
            elif "services" in data:
                svcs = ", ".join(data["services"])
                lines.append(f"  {name}: services=[{svcs}]")
            elif "vars" in data:
                var_names = ", ".join(data["vars"][:20])
                lines.append(f"  {name}: vars=[{var_names}]")
            elif "module" in data:
                lines.append(f"  {name}: module={data['module']}")
            elif "name" in data:
                lines.append(f"  {name}: name=\"{data['name']}\"")
            else:
                lines.append(f"  {name}: found")
        sections.append("\n".join(lines))

    # Source files
    source_files = {k: v for k, v in file_tree.items() if k not in test_files}
    total_lines = sum(file_tree.values())
    if file_tree:
        lines = [f"### Source Files ({len(source_files)} files, {total_lines:,} total lines)"]
        # Sort by line count descending, show top 30
        sorted_files = sorted(source_files.items(), key=lambda x: x[1], reverse=True)
        for rel, count in sorted_files[:30]:
            lines.append(f"  {rel:50s} {count:>5} lines")
        if len(sorted_files) > 30:
            lines.append(f"  ... and {len(sorted_files) - 30} more files")
        sections.append("\n".join(lines))

    # Test files
    if test_files:
        lines = [f"### Test Files ({len(test_files)} files)"]
        for rel in sorted(test_files):
            count = file_tree.get(rel, 0)
            lines.append(f"  {rel:50s} {count:>5} lines")
        sections.append("\n".join(lines))

    # Services
    if services:
        lines = ["### Detected Services"]
        for svc in services:
            lines.append(f"  {svc}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def critique_prd(
    config: LoopConfig, claude: Claude, state: LoopState,
) -> dict:
    """Run PRD Critique agent with interactive refinement on REJECT.

    Uses REASONER (Opus) with prd_critique.md prompt. If verdict is REJECT,
    enters interactive loop where human revises PRD.md and re-critiques.
    Tracks rounds in state.prd_refinement for crash resumability.
    """
    import json

    from .claude import AgentRole, load_prompt
    from .state import RefinementRound

    ref = state.prd_refinement

    # Crash-resume: if we were researching, re-run research then present
    if ref.status == "researching":
        print("\n  Resuming PRD critique (was researching)...")
        critique = state.agent_results.get("critique", {})
        research = _research_prd_rejection(config, state, claude, critique)
        ref = state.prd_refinement  # Re-bind after researcher session
        if ref.rounds:
            ref.rounds[-1].research_results = research
        _present_prd_rejection(critique, research=research or None)

        ref.status = "awaiting_input"
        state.save(config.state_file)

        action = _prd_prompt_loop(config, state)
        if action == "quit":
            raise SystemExit("User quit during PRD refinement.")
        # action == "revised" — fall through to re-critique

    # Crash-resume: if we were awaiting input, skip straight to prompt
    elif ref.status == "awaiting_input":
        print("\n  Resuming PRD critique (was waiting for input)...")
        action = _prd_prompt_loop(config, state)
        if action == "quit":
            raise SystemExit("User quit during PRD refinement.")
        # action == "revised" — fall through to re-critique

    auto_amendment_rounds = 0
    MAX_AUTO_AMENDMENTS = 2

    while True:
        ref.status = "running"
        ref.current_round += 1
        state.save(config.state_file)

        session = claude.session(AgentRole.REASONER)
        prompt = load_prompt("prd_critique",
            SPRINT_CONTEXT=json.dumps(state.context.__dict__, default=str),
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
        )
        session.send(prompt)
        # Re-bind ref — _sync_state in send() replaces state fields
        ref = state.prd_refinement

        critique = state.agent_results.get("critique", {})
        verdict = critique.get("verdict", "APPROVE")

        # Record this round
        ref.rounds.append(RefinementRound(
            round_num=ref.current_round,
            timestamp=datetime.now().isoformat(),
            analysis_result=critique,
            hard_issues=[{"verdict": verdict, "reason": critique.get("reason", "")}]
                if verdict == "REJECT" else [],
            soft_issues=[],
        ))

        # --- APPROVE: done ---
        if verdict == "APPROVE":
            ref.status = "done"
            ref.consensus_reason = critique.get("reason", "")
            state.save(config.state_file)
            return critique

        # --- AMEND / DESCOPE: auto-apply changes, then re-critique ---
        if verdict in ("AMEND", "DESCOPE"):
            auto_amendment_rounds += 1

            if auto_amendment_rounds <= MAX_AUTO_AMENDMENTS:
                _apply_prd_changes(config, state, claude, critique)
                ref = state.prd_refinement  # Re-bind after builder session
                ref.rounds[-1].human_action = f"auto_{verdict.lower()}"
                state.save(config.state_file)
                print(f"  PRD {verdict} applied — re-running critique...")
                continue  # Loop back for re-critique

            # Safety cap exceeded — fall through to interactive human loop
            print(f"\n  PRD received {auto_amendment_rounds} consecutive "
                  f"AMEND/DESCOPE verdicts — requesting human review.")

        # --- REJECT (or AMEND/DESCOPE past safety cap): interactive loop ---
        ref.status = "researching"
        state.save(config.state_file)
        research = _research_prd_rejection(config, state, claude, critique)
        # Re-bind ref after researcher session
        ref = state.prd_refinement
        ref.rounds[-1].research_results = research

        _present_prd_rejection(critique, research=research or None)

        ref.status = "awaiting_input"
        state.save(config.state_file)

        action = _prd_prompt_loop(config, state)
        if action == "quit":
            raise SystemExit("User quit during PRD refinement.")

        # action == "revised" — loop back to re-critique
        ref.rounds[-1].human_action = "revised"
        auto_amendment_rounds = 0  # Reset after human intervention
        print(f"\n  Re-running PRD critique (round {ref.current_round + 1})...")


def refine_vision(
    config: LoopConfig, state: LoopState, claude: Claude,
) -> dict:
    """Run Vision Validation with interactive refinement on NEEDS_REVISION.

    Uses REASONER (Opus) with vision_validate.md prompt (5-pass analysis).
    If verdict is NEEDS_REVISION:
      - HARD issues: human must revise VISION.md, then re-validate
      - SOFT issues only: human can [A]cknowledge and proceed, or [R]evise
    Tracks rounds in state.vision_refinement for crash resumability.
    """
    from .claude import AgentRole, load_prompt
    from .state import RefinementRound

    if not config.vision_file.exists():
        return {"verdict": "PASS", "reason": "No vision file to validate"}

    ref = state.vision_refinement

    # Crash-resume: if we were researching, re-run research then present
    if ref.status == "researching":
        print("\n  Resuming vision refinement (was researching)...")
        validation = state.agent_results.get("vision_validation", {})
        hard_issues = [
            i for i in validation.get("issues", [])
            if i.get("severity") == "hard"
        ]
        research = _research_vision_issues(config, state, claude, hard_issues)
        ref = state.vision_refinement  # Re-bind after researcher session
        if ref.rounds:
            ref.rounds[-1].research_results = research
        _present_vision_brief(validation, research=research or None)

        ref.status = "awaiting_input"
        state.save(config.state_file)

        action = _vision_prompt_loop(config, state, has_hard_issues=bool(hard_issues))
        if action == "quit":
            raise SystemExit("User quit during vision refinement.")
        if action == "acknowledge":
            ref.status = "done"
            ref.consensus_reason = "Soft issues acknowledged by human"
            state.save(config.state_file)
            return validation
        # action == "revised" — fall through to re-validate

    # Crash-resume: if we were awaiting input, skip straight to prompt
    elif ref.status == "awaiting_input":
        print("\n  Resuming vision refinement (was waiting for input)...")
        has_hard = any(
            i.get("severity") == "hard"
            for i in state.agent_results.get("vision_validation", {}).get("issues", [])
        )
        action = _vision_prompt_loop(config, state, has_hard_issues=has_hard)
        if action == "quit":
            raise SystemExit("User quit during vision refinement.")
        if action == "acknowledge":
            ref.status = "done"
            ref.consensus_reason = "Soft issues acknowledged by human"
            state.save(config.state_file)
            return state.agent_results.get("vision_validation", {})
        # action == "revised" — fall through to re-validate

    while True:
        ref.status = "running"
        ref.current_round += 1
        state.save(config.state_file)

        session = claude.session(AgentRole.REASONER)
        prompt = load_prompt("vision_validate",
            SPRINT=config.sprint,
            SPRINT_DIR=str(config.sprint_dir),
        )
        session.send(prompt)
        # Re-bind ref — _sync_state in send() replaces state fields
        ref = state.vision_refinement

        validation = state.agent_results.get("vision_validation", {})
        verdict = validation.get("verdict", "PASS")
        issues = validation.get("issues", [])
        hard_issues = [i for i in issues if i.get("severity") == "hard"]
        soft_issues = [i for i in issues if i.get("severity") == "soft"]

        # Record this round
        ref.rounds.append(RefinementRound(
            round_num=ref.current_round,
            timestamp=datetime.now().isoformat(),
            analysis_result=validation,
            hard_issues=hard_issues,
            soft_issues=soft_issues,
        ))

        if verdict == "PASS":
            if soft_issues:
                _present_vision_pass_with_notes(validation)
                ref.acknowledged_soft_issues = [i.get("id", "") for i in soft_issues]
                ref.rounds[-1].human_action = "auto_acknowledged"
            ref.status = "done"
            ref.consensus_reason = validation.get("reason", "")
            state.save(config.state_file)
            return validation

        # NEEDS_REVISION — research HARD issues, then present findings
        research = None
        if hard_issues:
            ref.status = "researching"
            state.save(config.state_file)
            research = _research_vision_issues(config, state, claude, hard_issues)
            # Re-bind ref after researcher session
            ref = state.vision_refinement
            ref.rounds[-1].research_results = research

        _present_vision_brief(validation, research=research)

        ref.status = "awaiting_input"
        state.save(config.state_file)

        action = _vision_prompt_loop(config, state, has_hard_issues=bool(hard_issues))

        if action == "quit":
            raise SystemExit("User quit during vision refinement.")

        if action == "acknowledge":
            # Soft issues only — human accepts the risk
            ref.status = "done"
            ref.consensus_reason = "Soft issues acknowledged by human"
            ref.acknowledged_soft_issues = [i.get("id", "") for i in soft_issues]
            ref.rounds[-1].human_action = "acknowledged"
            state.save(config.state_file)
            return validation

        # action == "revised" — loop back to re-validate
        ref.rounds[-1].human_action = "revised"
        print(f"\n  Re-running vision validation (round {ref.current_round + 1})...")


# ---------------------------------------------------------------------------
# Pre-loop research helpers
# ---------------------------------------------------------------------------

def _research_vision_issues(
    config: "LoopConfig", state: "LoopState", claude: "Claude",
    hard_issues: list[dict],
) -> dict:
    """Spawn RESEARCHER session to find information about vision HARD issues.

    Batches all HARD issues into one prompt. Returns the research dict
    from state.agent_results["research"], or empty dict on failure.
    """
    from .claude import AgentRole, load_prompt

    # Format issues for the prompt
    issue_lines = []
    for i in hard_issues:
        issue_id = i.get("id", "?")
        category = i.get("category", "?")
        desc = i.get("description", "")
        suggestion = i.get("suggested_revision", "")
        issue_lines.append(f"- **[{issue_id}] {category}**: {desc}")
        if suggestion:
            issue_lines.append(f"  Suggested revision: {suggestion}")
    issues_text = "\n".join(issue_lines)

    # Read vision for context
    vision_text = config.vision_file.read_text(encoding="utf-8") if config.vision_file.exists() else "(no vision file)"

    try:
        print("  Running RESEARCHER for vision issues...")
        session = claude.session(AgentRole.RESEARCHER)
        prompt = load_prompt("preloop_research",
            ISSUES=issues_text,
            DOCUMENT_CONTEXT=f"VISION.md:\n{vision_text}",
        )
        session.send(prompt)

        research = state.agent_results.get("research", {})
        if research:
            print("  Research complete.")
        else:
            print("  Research returned no findings.")
        return research
    except Exception as e:
        print(f"  Research failed (non-blocking): {e}")
        return {}


def _research_prd_rejection(
    config: "LoopConfig", state: "LoopState", claude: "Claude",
    critique: dict,
) -> dict:
    """Spawn RESEARCHER session to find information about PRD rejection.

    Returns the research dict from state.agent_results["research"],
    or empty dict on failure.
    """
    from .claude import AgentRole, load_prompt

    # Format rejection details for the prompt
    reason = critique.get("reason", "")
    amendments = critique.get("amendments", [])
    descope = critique.get("descope_suggestions", [])

    issue_lines = [f"- **Rejection reason**: {reason}"]
    if amendments:
        issue_lines.append("- **Suggested amendments**:")
        for a in amendments:
            issue_lines.append(f"  - {a}")
    if descope:
        issue_lines.append("- **Descope suggestions**:")
        for s in descope:
            issue_lines.append(f"  - {s}")
    issues_text = "\n".join(issue_lines)

    # Read PRD for context
    prd_text = config.prd_file.read_text(encoding="utf-8") if config.prd_file.exists() else "(no PRD file)"

    try:
        print("  Running RESEARCHER for PRD rejection...")
        session = claude.session(AgentRole.RESEARCHER)
        prompt = load_prompt("preloop_research",
            ISSUES=issues_text,
            DOCUMENT_CONTEXT=f"PRD.md:\n{prd_text}",
        )
        session.send(prompt)

        research = state.agent_results.get("research", {})
        if research:
            print("  Research complete.")
        else:
            print("  Research returned no findings.")
        return research
    except Exception as e:
        print(f"  Research failed (non-blocking): {e}")
        return {}


def _apply_prd_changes(
    config: "LoopConfig", state: "LoopState", claude: "Claude",
    critique: dict,
) -> None:
    """Spawn BUILDER session to apply AMEND/DESCOPE changes to PRD.md.

    Uses BUILDER (not REASONER) because it needs file-write tools to edit
    PRD.md directly. The agent is constrained to apply ONLY the listed
    changes — no additions, removals, or other modifications.
    """
    from .claude import AgentRole

    verdict = critique.get("verdict", "AMEND")
    prd_path = config.prd_file

    # Build the change list from the critique
    if verdict == "AMEND":
        changes = critique.get("amendments", [])
        change_type = "amendments"
    else:  # DESCOPE
        changes = critique.get("descope_suggestions", [])
        change_type = "descope suggestions"

    if not changes:
        print(f"  No {change_type} found in critique — skipping auto-apply.")
        return

    change_lines = "\n".join(f"  {i}. {c}" for i, c in enumerate(changes, 1))

    print(f"  Applying {len(changes)} {change_type} to {prd_path}...")

    session = claude.session(
        AgentRole.BUILDER,
        system_extra=(
            "Apply ONLY these specific changes to the PRD. "
            "Do not add, remove, or modify anything else. "
            "Preserve the document's existing structure and formatting."
        ),
    )
    session.send(
        f"Apply the following {change_type} to the PRD at {prd_path}:\n\n"
        f"{change_lines}\n\n"
        f"Read the PRD first, then make ONLY the listed changes."
    )

    print(f"  {verdict} changes applied to PRD.")


# ---------------------------------------------------------------------------
# Interactive refinement helpers
# ---------------------------------------------------------------------------

_DIMENSION_LABELS = {
    "outcome_grounded": "Outcome-Grounded",
    "adoption_realistic": "Adoption-Realistic",
    "causally_sound": "Causally-Sound",
    "failure_aware": "Failure-Aware",
}


def _present_vision_brief(validation: dict, research: dict | None = None) -> None:
    """Print a structured terminal summary of vision validation findings."""
    print("\n" + "=" * 60)
    print("  VISION VALIDATION — NEEDS REVISION")
    print("=" * 60)

    # Dimensions
    dims = validation.get("dimensions", {})
    if dims:
        print("\n  Dimensions:")
        for key, label in _DIMENSION_LABELS.items():
            score = dims.get(key, "?")
            marker = " !!" if score in ("WEAK", "CRITICAL") else ""
            print(f"    {label:24s} {score}{marker}")

    # Strengths
    strengths = validation.get("strengths", [])
    if strengths:
        print("\n  Strengths:")
        for s in strengths:
            print(f"    + {s}")

    # Issues — HARD first, then SOFT
    issues = validation.get("issues", [])
    hard = [i for i in issues if i.get("severity") == "hard"]
    soft = [i for i in issues if i.get("severity") == "soft"]

    if hard:
        print("\n  HARD issues (must resolve before proceeding):")
        for i in hard:
            print(f"    ! [{i.get('category', '?')}] {i.get('description', '')}")
            if i.get("suggested_revision"):
                print(f"      Suggestion: {i['suggested_revision']}")

    if soft:
        print("\n  SOFT issues (advisory — can acknowledge and proceed):")
        for i in soft:
            print(f"    ~ [{i.get('category', '?')}] {i.get('description', '')}")
            if i.get("suggested_revision"):
                print(f"      Suggestion: {i['suggested_revision']}")

    # Research findings (if available)
    if research and research.get("findings"):
        print("\n" + "-" * 60)
        print("  RESEARCH FINDINGS")
        print("-" * 60)
        print(f"  {research['findings']}")
        sources = research.get("sources", [])
        if sources:
            print("\n  Sources:")
            for src in sources:
                print(f"    - {src}")

    # Overall reason
    reason = validation.get("reason", "")
    if reason:
        print(f"\n  Summary: {reason}")

    print()


def _present_vision_pass_with_notes(validation: dict) -> None:
    """Print soft issues from a PASS verdict for human awareness (non-blocking)."""
    print("\n" + "=" * 60)
    print("  VISION VALIDATION — PASS (with notes)")
    print("=" * 60)

    # Dimensions (compact)
    dims = validation.get("dimensions", {})
    if dims:
        print("\n  Dimensions:")
        for key, label in _DIMENSION_LABELS.items():
            score = dims.get(key, "?")
            print(f"    {label:24s} {score}")

    # Strengths (compact)
    strengths = validation.get("strengths", [])
    if strengths:
        print("\n  Strengths:")
        for s in strengths:
            print(f"    + {s}")

    # Soft issues as "notes for awareness"
    soft_issues = [
        i for i in validation.get("issues", [])
        if i.get("severity") == "soft"
    ]
    if soft_issues:
        print("\n  Notes for awareness:")
        for i in soft_issues:
            print(f"    ~ [{i.get('category', '?')}] {i.get('description', '')}")
            if i.get("suggested_revision"):
                print(f"      Suggestion: {i['suggested_revision']}")

    reason = validation.get("reason", "")
    if reason:
        print(f"\n  Summary: {reason}")

    print()


def _vision_prompt_loop(
    config: "LoopConfig", state: "LoopState", *, has_hard_issues: bool,
) -> str:
    """Interactive input loop for vision refinement.

    Returns: "revised" | "acknowledge" | "quit"
    """
    vision_path = config.vision_file

    if has_hard_issues:
        print(f"  HARD issues found — you must revise {vision_path}")
        print("  Options:")
        print("    [R] Revise — edit VISION.md, then press Enter to re-validate")
        print("    [Q] Quit")
        valid = {"r", "q"}
    else:
        print("  Only SOFT issues found — you may proceed or revise.")
        print("  Options:")
        print("    [A] Acknowledge risks and proceed")
        print("    [R] Revise — edit VISION.md, then press Enter to re-validate")
        print("    [Q] Quit")
        valid = {"a", "r", "q"}

    while True:
        try:
            choice = input("\n  Your choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"

        if not choice:
            continue

        if choice[0] not in valid:
            print(f"  Invalid choice. Enter one of: {', '.join(sorted(valid)).upper()}")
            continue

        if choice[0] == "q":
            return "quit"
        if choice[0] == "a":
            return "acknowledge"
        if choice[0] == "r":
            print(f"\n  Edit {vision_path} now, then press Enter when ready...")
            try:
                input("  Press Enter to re-validate >> ")
            except (EOFError, KeyboardInterrupt):
                return "quit"
            return "revised"


def _present_prd_rejection(critique: dict, research: dict | None = None) -> None:
    """Print a structured terminal summary of PRD rejection."""
    print("\n" + "=" * 60)
    print("  PRD CRITIQUE — REJECTED")
    print("=" * 60)

    reason = critique.get("reason", "")
    if reason:
        print(f"\n  Reason: {reason}")

    amendments = critique.get("amendments", [])
    if amendments:
        print("\n  Suggested amendments:")
        for i, a in enumerate(amendments, 1):
            print(f"    {i}. {a}")

    descope = critique.get("descope_suggestions", [])
    if descope:
        print("\n  Descope suggestions:")
        for i, s in enumerate(descope, 1):
            print(f"    {i}. {s}")

    # Research findings (if available)
    if research and research.get("findings"):
        print("\n" + "-" * 60)
        print("  RESEARCH FINDINGS")
        print("-" * 60)
        print(f"  {research['findings']}")
        sources = research.get("sources", [])
        if sources:
            print("\n  Sources:")
            for src in sources:
                print(f"    - {src}")

    print()


def _prd_prompt_loop(config: "LoopConfig", state: "LoopState") -> str:
    """Interactive input loop for PRD refinement.

    Returns: "revised" | "quit"
    """
    prd_path = config.prd_file

    print(f"  PRD was REJECTED — you must revise {prd_path}")
    print("  Options:")
    print("    [R] Revise — edit PRD.md, then press Enter to re-critique")
    print("    [Q] Quit")

    while True:
        try:
            choice = input("\n  Your choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"

        if not choice:
            continue

        if choice[0] not in {"r", "q"}:
            print("  Invalid choice. Enter R or Q.")
            continue

        if choice[0] == "q":
            return "quit"
        if choice[0] == "r":
            print(f"\n  Edit {prd_path} now, then press Enter when ready...")
            try:
                input("  Press Enter to re-critique >> ")
            except (EOFError, KeyboardInterrupt):
                return "quit"
            return "revised"


def classify_vision_complexity(
    config: LoopConfig, claude: Claude, state: LoopState,
) -> str:
    """Classify vision as single_run or multi_epic.

    Phase 1: always returns single_run.
    Phase 3: uses Opus to assess complexity signals.
    """
    from .claude import AgentRole

    vision_text = config.vision_file.read_text(encoding="utf-8") if config.vision_file.exists() else ""
    prd_text = config.prd_file.read_text(encoding="utf-8") if config.prd_file.exists() else ""

    # Quick heuristic: if both files are small, skip LLM classification
    combined_length = len(vision_text) + len(prd_text)
    if combined_length < 500:
        state.vision_complexity = "single_run"
        return "single_run"

    session = claude.session(
        AgentRole.REASONER,
        system_extra=(
            "Assess vision complexity. Count independently valuable "
            "deliverables. Be conservative: any complexity signal → multi_epic."
        ),
    )
    response = session.send(
        f"Classify this vision as 'single_run' or 'multi_epic'.\n\n"
        f"VISION:\n{vision_text}\n\n"
        f"PRD:\n{prd_text}\n\n"
        f"Complexity signals — if ANY ONE is true, classify as multi_epic:\n"
        f"- >3 independently valuable deliverables\n"
        f"- >15 estimated tasks\n"
        f"- >2 layers of sequential dependencies\n"
        f"- >2 distinct technology domains (e.g. backend + database + frontend)\n"
        f"- Multiple services (e.g. API server + frontend + database)\n"
        f"- Full-stack application (backend API + frontend SPA)\n"
        f"- Multiple user-facing views or pages with distinct functionality\n\n"
        f"A full-stack web application with separate backend, database, and "
        f"frontend is ALWAYS multi_epic.\n\n"
        f"Respond with ONLY 'single_run' or 'multi_epic' on the first line."
    )
    # Extract classification — check all lines since SDK may include preamble
    response_lower = response.strip().lower()
    classification = "single_run"
    for line in response_lower.split("\n"):
        line = line.strip()
        if "multi_epic" in line:
            classification = "multi_epic"
            break
        if line == "single_run":
            classification = "single_run"
            break
    state.vision_complexity = classification
    return classification


def decompose_into_epics(
    config: LoopConfig, claude: Claude, state: LoopState,
) -> list:
    """Decompose multi_epic vision into deliverable value blocks.

    Phase 1: no-op (only single_run supported).
    Phase 3: uses Opus with epic_decompose.md prompt, agent calls
    report_epic_decomposition to populate state.epics.
    """
    from .claude import AgentRole, load_prompt

    vision_text = config.vision_file.read_text(encoding="utf-8") if config.vision_file.exists() else ""
    prd_text = config.prd_file.read_text(encoding="utf-8") if config.prd_file.exists() else ""

    session = claude.session(AgentRole.REASONER)
    prompt = load_prompt("epic_decompose",
        SPRINT=config.sprint,
        SPRINT_DIR=str(config.sprint_dir),
        VISION=vision_text,
        PRD=prd_text,
    )
    session.send(prompt)

    # report_epic_decomposition handler populates state.epics
    return list(state.epics)
