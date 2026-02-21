"""Post-delivery documentation generation."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..claude import Claude
    from ..config import LoopConfig
    from ..state import LoopState


def generate_project_docs(
    config: LoopConfig, state: LoopState, claude: Claude,
) -> None:
    """Generate or update project documentation after delivery.

    Non-blocking: failure prints a warning but does NOT raise.
    Idempotent: skips if the ``docs_generated`` gate has already passed.
    """
    if not config.generate_docs:
        print("  Docs: generation disabled (--no-docs)")
        return

    if state.gate_passed("docs_generated"):
        print("  Docs: already generated — skipping")
        return

    print("\n  Generating project documentation...")

    try:
        from ..claude import AgentRole, load_prompt
        from ..git import git_commit

        doc_context = _precompute_doc_context(config, state)
        delivery_summary = _build_delivery_summary(state)

        session = claude.session(AgentRole.BUILDER)
        prompt = load_prompt(
            "generate_docs",
            PROJECT_DIR=str(config.effective_project_dir),
            SPRINT_DIR=str(config.sprint_dir),
            SPRINT_CONTEXT=json.dumps(asdict(state.context), indent=2),
            DOC_CONTEXT=doc_context,
            DELIVERY_SUMMARY=delivery_summary,
        )
        session.send(prompt)

        state.pass_gate("docs_generated")
        state.save(config.state_file)

        git_commit(
            config, state,
            f"telic-loop({config.sprint}): Generate project docs",
        )
        print("  Docs: project documentation generated successfully")

    except Exception as exc:
        print(f"  Docs: WARNING — generation failed: {exc}")
        # Non-blocking: delivery is already committed


# ---------------------------------------------------------------------------
# Pre-computation helpers
# ---------------------------------------------------------------------------

def _precompute_doc_context(config: LoopConfig, state: LoopState) -> str:
    """Pre-compute documentation context to reduce agent turns.

    Scans for existing docs, project metadata, file tree, and tech stack.
    """
    project_dir = config.effective_project_dir
    lines: list[str] = []

    # 1. Existing documentation inventory
    lines.append("### Existing Documentation")
    existing_docs = _scan_existing_docs(project_dir)
    if existing_docs:
        for doc_path, size in existing_docs:
            lines.append(f"- `{doc_path}` ({size:,} bytes)")
    else:
        lines.append("No existing documentation found (greenfield).")
    lines.append("")

    # 2. Package metadata
    lines.append("### Package Metadata")
    metadata = _extract_package_metadata(project_dir)
    if metadata:
        for key, value in metadata.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("No package.json or pyproject.toml found.")
    lines.append("")

    # 3. Tech stack from sprint context
    lines.append("### Tech Stack (from discovery)")
    ctx = state.context
    if ctx.tech_stack:
        for tech in ctx.tech_stack:
            lines.append(f"- {tech}")
    if ctx.frameworks:
        lines.append(f"- Frameworks: {', '.join(ctx.frameworks)}")
    if ctx.languages:
        lines.append(f"- Languages: {', '.join(ctx.languages)}")
    if not ctx.tech_stack and not ctx.frameworks and not ctx.languages:
        lines.append("Not detected.")
    lines.append("")

    # 4. Source file tree (compact)
    lines.append("### Source File Tree")
    file_tree = _scan_source_tree(project_dir)
    if file_tree:
        for rel_path in sorted(file_tree)[:100]:  # cap at 100 files
            lines.append(f"- {rel_path}")
        if len(file_tree) > 100:
            lines.append(f"... and {len(file_tree) - 100} more files")
    else:
        lines.append("No source files found.")
    lines.append("")

    return "\n".join(lines)


def _scan_existing_docs(project_dir: Path) -> list[tuple[str, int]]:
    """Find existing documentation files in the project."""
    docs: list[tuple[str, int]] = []

    # Check root-level docs
    for name in ("README.md", "README", "readme.md", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE", "LICENSE.md"):
        p = project_dir / name
        if p.is_file():
            docs.append((name, p.stat().st_size))

    # Check docs/ directory
    docs_dir = project_dir / "docs"
    if docs_dir.is_dir():
        for p in sorted(docs_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in (".md", ".txt", ".rst", ".adoc"):
                rel = str(p.relative_to(project_dir)).replace("\\", "/")
                docs.append((rel, p.stat().st_size))

    return docs


def _extract_package_metadata(project_dir: Path) -> dict[str, str]:
    """Extract project name, version, description from package files."""
    metadata: dict[str, str] = {}

    # package.json
    pkg_json = project_dir / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            if data.get("name"):
                metadata["name"] = data["name"]
            if data.get("version"):
                metadata["version"] = data["version"]
            if data.get("description"):
                metadata["description"] = data["description"]
            if data.get("license"):
                metadata["license"] = data["license"]
        except (json.JSONDecodeError, OSError):
            pass

    # pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    if pyproject.is_file() and not metadata:
        try:
            text = pyproject.read_text(encoding="utf-8")
            # Simple extraction without toml parser
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("name") and "=" in line:
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    metadata.setdefault("name", val)
                elif line.startswith("version") and "=" in line:
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    metadata.setdefault("version", val)
                elif line.startswith("description") and "=" in line:
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    metadata.setdefault("description", val)
        except OSError:
            pass

    return metadata


def _scan_source_tree(project_dir: Path) -> list[str]:
    """Scan project directory for source files (compact listing)."""
    from .process_monitor import _SOURCE_EXTENSIONS, _SKIP_DIRS

    files: list[str] = []
    if not project_dir.is_dir():
        return files

    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in _SOURCE_EXTENSIONS:
            continue
        parts = path.relative_to(project_dir).parts
        if any(p.startswith(".") or p in _SKIP_DIRS for p in parts[:-1]):
            continue
        rel = str(path.relative_to(project_dir)).replace("\\", "/")
        files.append(rel)

    return files


def _build_delivery_summary(state: LoopState) -> str:
    """Build a delivery summary string from state for the docs prompt."""
    lines: list[str] = []

    vrc = state.latest_vrc
    if vrc:
        lines.append(f"**Value Score**: {vrc.value_score:.0%}")
        lines.append(f"**Verified**: {vrc.deliverables_verified}/{vrc.deliverables_total}")
    lines.append(f"**Iterations**: {state.iteration}")
    lines.append("")

    # Tasks delivered
    done_tasks = [t for t in state.tasks.values() if t.status == "done"]
    descoped_tasks = [t for t in state.tasks.values() if t.status == "descoped"]

    if done_tasks:
        lines.append("### Delivered")
        for t in done_tasks:
            lines.append(f"- **{t.task_id}**: {t.description}")

    if descoped_tasks:
        lines.append("")
        lines.append("### Descoped")
        for t in descoped_tasks:
            reason = t.blocked_reason or "N/A"
            lines.append(f"- **{t.task_id}**: {t.description} (reason: {reason})")

    return "\n".join(lines)
