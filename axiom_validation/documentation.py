"""Deterministic public-documentation information-architecture policy."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .context import REPOSITORY_ROOT
from .hooks import HOOK_FILES
from .markdown import (
    ATX_HEADING,
    REFERENCE_LINK,
    check_markdown_links,
    check_documented_hook_command_text,
    fenced_blocks_and_masked_text,
    inline_link_destinations,
    link_destination,
    mask_inline_code,
)
from .release_facts import check_release_facts
from .repository_policy import check_release_version_surfaces
from .route_catalog import check_route_catalog
from .runtime_identity import check_runtime_identity

README_MAX_BYTES = 16 * 1024
README_PREFERRED_MIN_BYTES = 8 * 1024
README_PREFERRED_MAX_BYTES = 12 * 1024

ROOT_CURRENT_DOCUMENTS = (
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
)
COMPATIBILITY_ENTRY = "docs/getting-started.md"
PROJECT_PREFIXES = ("project/",)
LIFECYCLE_VALUES = frozenset(
    {"current", "historical", "generated", "project-plan", "archived"}
)
LIFECYCLE_COMMENT = re.compile(r"<!--\s*lifecycle:\s*([^<>]*?)\s*-->")
GENERATED_MARKER = re.compile(
    r"<!--\s*([a-z0-9][a-z0-9._:-]*?):(start|end)\s*-->"
)
SETEXT_HEADING = re.compile(r"^[ \t]{0,3}(=+|-+)[ \t]*$")
README_SHARED_HEADING = "### Shared skills"
FRONT_DOOR_ROUTE_HEADING = "## Bundled Routes"
TASK_NAVIGATION_HEADING = "## Start By Task"
FORBIDDEN_TASK_PREFIXES = (
    "docs/releases/",
    "project/",
    "evidence/",
    "evals/results/",
)


@dataclass(frozen=True)
class DocumentationReport:
    """Counts and advisory budget status for one validation run."""

    markdown_count: int
    current_document_count: int
    indexed_document_count: int
    generated_region_count: int
    readme_bytes: int
    preferred_budget_status: str


def _label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _read_text(path: Path, root: Path, failures: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read {_label(path, root)}: {error}")
        return None


def discover_markdown(root: Path = REPOSITORY_ROOT) -> tuple[Path, ...]:
    """Return repository Markdown in stable path order, excluding Git internals."""
    root = root.resolve()
    return tuple(
        path
        for path in sorted(root.rglob("*.md"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    )


def is_current_document(relative_path: str) -> bool:
    """Return whether a Markdown path belongs to the maintained current set."""
    if relative_path in ROOT_CURRENT_DOCUMENTS:
        return True
    if not relative_path.startswith("docs/"):
        return False
    return (
        relative_path != COMPATIBILITY_ENTRY
        and not relative_path.startswith("docs/releases/")
    )


def current_documents(root: Path = REPOSITORY_ROOT) -> tuple[Path, ...]:
    root = root.resolve()
    return tuple(
        path
        for path in discover_markdown(root)
        if is_current_document(path.relative_to(root).as_posix())
    )


def _raw_destinations(text: str) -> tuple[str, ...]:
    _, searchable = fenced_blocks_and_masked_text(text)
    destinations: list[str] = []
    for line in searchable.splitlines():
        destinations.extend(inline_link_destinations(line))
        reference = REFERENCE_LINK.match(mask_inline_code(line))
        if reference and not reference.group(1).startswith("^"):
            destinations.append(reference.group(2) or reference.group(3) or "")
    return tuple(destinations)


def _local_target(
    source: Path, raw_destination: str, root: Path
) -> str | None:
    destination = link_destination(raw_destination)
    if not destination:
        return None
    destination = re.sub(r"\\([ ()])", r"\1", destination)
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc or destination.startswith("//"):
        return None
    decoded_path = unquote(parsed.path)
    candidate = (
        (root if decoded_path.startswith("/") else source.parent)
        / decoded_path.lstrip("/")
    ).resolve() if decoded_path else source.resolve()
    try:
        return candidate.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def check_readme_budget(
    root: Path, failures: list[str]
) -> tuple[int, str]:
    path = root / "README.md"
    try:
        byte_count = len(path.read_bytes())
    except OSError as error:
        failures.append(f"cannot read README.md for size validation: {error}")
        return 0, "unavailable"
    if byte_count > README_MAX_BYTES:
        failures.append(
            f"README.md is {byte_count} bytes; the migration ceiling is "
            f"{README_MAX_BYTES} bytes"
        )
    if byte_count < README_PREFERRED_MIN_BYTES:
        status = "below"
    elif byte_count <= README_PREFERRED_MAX_BYTES:
        status = "within"
    else:
        status = "above"
    return byte_count, status


def _heading_levels(searchable: str) -> tuple[int, ...]:
    lines = searchable.splitlines()
    levels: list[int] = []
    for index, line in enumerate(lines):
        match = ATX_HEADING.match(line)
        if match:
            stripped = line.lstrip()
            levels.append(len(stripped) - len(stripped.lstrip("#")))
            continue
        setext = SETEXT_HEADING.match(line)
        if setext and index > 0 and lines[index - 1].strip():
            levels.append(1 if setext.group(1).startswith("=") else 2)
    return tuple(levels)


def check_heading_text(label: str, text: str, failures: list[str]) -> None:
    """Check the one-H1 and no-level-skip contract for one current document."""
    _, searchable = fenced_blocks_and_masked_text(text)
    levels = _heading_levels(searchable)
    h1_count = levels.count(1)
    if h1_count != 1:
        failures.append(
            f"{label} must contain exactly one H1; found {h1_count}"
        )
    for previous, current in zip(levels, levels[1:]):
        if current > previous + 1:
            failures.append(
                f"{label} skips a heading level from H{previous} to H{current}"
            )


def check_current_headings(root: Path, failures: list[str]) -> int:
    paths = current_documents(root)
    for path in paths:
        text = _read_text(path, root, failures)
        if text is not None:
            check_heading_text(_label(path, root), text, failures)
    return len(paths)


def check_docs_index_and_orphans(root: Path, failures: list[str]) -> int:
    """Require direct index coverage and reachability for current docs."""
    root = root.resolve()
    index = root / "docs" / "README.md"
    current = {
        path.relative_to(root).as_posix(): path
        for path in current_documents(root)
        if path.relative_to(root).as_posix().startswith("docs/")
    }
    expected = set(current) - {"docs/README.md"}
    index_text = _read_text(index, root, failures)
    if index_text is None:
        return 0

    direct_targets = {
        target
        for raw in _raw_destinations(index_text)
        if (target := _local_target(index, raw, root)) in current
    }
    for missing in sorted(expected - direct_targets):
        failures.append(
            f"docs/README.md does not directly index current document {missing}"
        )

    graph: dict[str, set[str]] = {relative: set() for relative in current}
    for relative, path in current.items():
        text = _read_text(path, root, failures)
        if text is None:
            continue
        graph[relative] = {
            target
            for raw in _raw_destinations(text)
            if (target := _local_target(path, raw, root)) in current
        }
    reachable = {"docs/README.md"}
    pending = ["docs/README.md"]
    while pending:
        source = pending.pop()
        for target in sorted(graph.get(source, ())):
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    for orphan in sorted(expected - reachable):
        failures.append(
            f"current document {orphan} is orphaned from docs/README.md navigation"
        )
    return len(expected & direct_targets)


def _allowed_lifecycle(relative_path: str) -> frozenset[str] | None:
    if relative_path == COMPATIBILITY_ENTRY or relative_path.startswith(
        "docs/releases/"
    ):
        return frozenset({"historical", "archived"})
    if relative_path.startswith(PROJECT_PREFIXES):
        return frozenset({"project-plan", "historical", "archived"})
    if relative_path.startswith(("evidence/", "evals/results/")):
        return frozenset({"historical", "generated", "archived"})
    if is_current_document(relative_path):
        return frozenset({"current", "generated"})
    return None


def check_lifecycle_text(
    relative_path: str, text: str, failures: list[str]
) -> None:
    _, searchable = fenced_blocks_and_masked_text(text)
    comments = LIFECYCLE_COMMENT.findall(searchable)
    if searchable.count("<!-- lifecycle:") != len(comments):
        failures.append(
            f"{relative_path} contains malformed lifecycle metadata; use "
            "<!-- lifecycle: value -->"
        )
    if len(comments) > 1:
        failures.append(f"{relative_path} contains more than one lifecycle value")
    allowed = _allowed_lifecycle(relative_path)
    for raw_value in comments:
        value = raw_value.strip()
        if value not in LIFECYCLE_VALUES:
            failures.append(
                f"{relative_path} has invalid lifecycle value {value!r}"
            )
        elif allowed is not None and value not in allowed:
            failures.append(
                f"{relative_path} lifecycle {value!r} conflicts with its document class"
            )


def check_lifecycle_metadata(root: Path, failures: list[str]) -> None:
    for path in discover_markdown(root):
        text = _read_text(path, root, failures)
        if text is not None:
            check_lifecycle_text(_label(path, root), text, failures)


def check_generated_marker_text(
    relative_path: str, text: str, failures: list[str]
) -> int:
    """Require non-nested, unique, exactly paired generated regions."""
    _, searchable = fenced_blocks_and_masked_text(text)
    stack: list[str] = []
    starts: set[str] = set()
    completed = 0
    for match in GENERATED_MARKER.finditer(searchable):
        marker, event = match.groups()
        if event == "start":
            if marker in starts:
                failures.append(
                    f"{relative_path} repeats generated marker {marker!r}"
                )
            if stack:
                failures.append(
                    f"{relative_path} nests generated marker {marker!r} inside "
                    f"{stack[-1]!r}"
                )
            starts.add(marker)
            stack.append(marker)
            continue
        if not stack:
            failures.append(
                f"{relative_path} ends generated marker {marker!r} without a start"
            )
        elif stack[-1] != marker:
            failures.append(
                f"{relative_path} ends generated marker {marker!r} while "
                f"{stack[-1]!r} is open"
            )
        else:
            stack.pop()
            completed += 1
    for marker in stack:
        failures.append(
            f"{relative_path} starts generated marker {marker!r} without an end"
        )
    return completed


def check_generated_markers(root: Path, failures: list[str]) -> int:
    count = 0
    for path in discover_markdown(root):
        text = _read_text(path, root, failures)
        if text is not None:
            count += check_generated_marker_text(_label(path, root), text, failures)
    return count


def _private_destination(destination: str) -> bool:
    normalized = unquote(destination).replace("\\", "/").lower()
    parsed = urlsplit(normalized)
    return (
        parsed.scheme == "file"
        or "axiom-maintainer" in normalized
        or ".agents/skills/" in normalized
        or "/.air/" in normalized
        or normalized.startswith(("/home/", "/users/", "c:/users/"))
    )


def check_private_guidance_text(
    relative_path: str, text: str, failures: list[str]
) -> None:
    for raw in _raw_destinations(text):
        destination = link_destination(raw)
        if destination and _private_destination(destination):
            failures.append(
                f"{relative_path} links current public guidance to private maintenance "
                f"content: {destination!r}"
            )


def _section(text: str, heading: str) -> str:
    if text.count(heading) != 1:
        return ""
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def check_task_navigation_text(
    source: Path, text: str, root: Path, failures: list[str]
) -> None:
    section = _section(text, TASK_NAVIGATION_HEADING)
    if not section:
        failures.append(
            "docs/README.md must contain exactly one Start By Task section"
        )
        return
    for raw in _raw_destinations(section):
        target = _local_target(source, raw, root)
        if target is not None and target.startswith(FORBIDDEN_TASK_PREFIXES):
            failures.append(
                "docs/README.md Start By Task must not list historical or "
                f"project-plan document {target} as current guidance"
            )


def check_guidance_boundaries(root: Path, failures: list[str]) -> None:
    root = root.resolve()
    for path in current_documents(root):
        text = _read_text(path, root, failures)
        if text is not None:
            check_private_guidance_text(_label(path, root), text, failures)
    index = root / "docs" / "README.md"
    index_text = _read_text(index, root, failures)
    if index_text is not None:
        check_task_navigation_text(index, index_text, root, failures)


def _readme_inventory(text: str, failures: list[str]) -> tuple[str, ...]:
    if text.count(README_SHARED_HEADING) != 1:
        failures.append(
            "README.md must contain exactly one parseable Shared skills heading"
        )
        return ()
    section = text.split(README_SHARED_HEADING, 1)[1].split("\n### ", 1)[0]
    return tuple(
        re.findall(r"^- `([a-z0-9-]+)`,", section, re.MULTILINE)
    )


def _front_door_inventory(text: str, failures: list[str]) -> tuple[str, ...]:
    if text.count(FRONT_DOOR_ROUTE_HEADING) != 1:
        failures.append(
            "skills/using-axiom/SKILL.md must contain one Bundled Routes section"
        )
        return ()
    section = text.split(FRONT_DOOR_ROUTE_HEADING, 1)[1].split("\n## ", 1)[0]
    routes = tuple(
        re.findall(r"^- `([a-z0-9-]+)`: ", section, re.MULTILINE)
    )
    return ("using-axiom", *routes)


def check_readme_skill_inventory_text(
    readme_text: str,
    front_door_text: str,
    failures: list[str],
) -> None:
    expected = _front_door_inventory(front_door_text, failures)
    actual = _readme_inventory(readme_text, failures)
    if expected and actual != expected:
        failures.append(
            "README Shared skills inventory differs from the canonical front door: "
            + ", ".join(actual)
        )


def check_readme_skill_inventory(root: Path, failures: list[str]) -> None:
    readme = _read_text(root / "README.md", root, failures)
    front_door = _read_text(
        root / "skills" / "using-axiom" / "SKILL.md", root, failures
    )
    if readme is not None and front_door is not None:
        check_readme_skill_inventory_text(readme, front_door, failures)


def check_hook_reference(root: Path, failures: list[str]) -> None:
    """Compare every documented Hook command with declarations and wrapper bytes."""
    documents: dict[str, dict[str, object]] = {}
    for relative_path in HOOK_FILES:
        path = root / relative_path
        text = _read_text(path, root, failures)
        if text is None:
            continue
        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            failures.append(f"invalid JSON in {relative_path}: {error}")
            continue
        if not isinstance(document, dict):
            failures.append(f"{relative_path} must contain a JSON object")
            continue
        documents[relative_path] = document

    wrapper_path = root / "hooks" / "codex-session-start.cmd"
    wrapper = _read_text(wrapper_path, root, failures)

    reference_path = root / "docs" / "reference" / "hooks.md"
    reference = _read_text(reference_path, root, failures)
    if reference is None or wrapper is None:
        return
    check_documented_hook_command_text(
        reference,
        documents,
        failures,
        wrapper_text=wrapper,
    )


def check_machine_derived_documentation(failures: list[str]) -> None:
    """Run existing canonical owners for generated public facts."""
    check_runtime_identity(failures)
    check_release_facts(failures)
    check_route_catalog(failures)
    check_release_version_surfaces(failures)


def check_documentation(
    failures: list[str],
    *,
    root: Path = REPOSITORY_ROOT,
    include_canonical_owners: bool = True,
) -> DocumentationReport:
    """Validate the complete public documentation architecture."""
    root = root.resolve()
    readme_bytes, budget_status = check_readme_budget(root, failures)
    markdown_count = check_markdown_links(failures, root=root)
    current_count = check_current_headings(root, failures)
    indexed_count = check_docs_index_and_orphans(root, failures)
    check_lifecycle_metadata(root, failures)
    generated_count = check_generated_markers(root, failures)
    check_guidance_boundaries(root, failures)
    check_readme_skill_inventory(root, failures)
    check_hook_reference(root, failures)
    if include_canonical_owners:
        if root != REPOSITORY_ROOT.resolve():
            failures.append(
                "canonical documentation owners can only be checked at the repository root"
            )
        else:
            check_machine_derived_documentation(failures)
    return DocumentationReport(
        markdown_count=markdown_count,
        current_document_count=current_count,
        indexed_document_count=indexed_count,
        generated_region_count=generated_count,
        readme_bytes=readme_bytes,
        preferred_budget_status=budget_status,
    )


__all__ = (
    "DocumentationReport",
    "LIFECYCLE_VALUES",
    "README_MAX_BYTES",
    "README_PREFERRED_MAX_BYTES",
    "README_PREFERRED_MIN_BYTES",
    "check_current_headings",
    "check_docs_index_and_orphans",
    "check_documentation",
    "check_generated_marker_text",
    "check_guidance_boundaries",
    "check_heading_text",
    "check_hook_reference",
    "check_lifecycle_text",
    "check_private_guidance_text",
    "check_readme_budget",
    "check_readme_skill_inventory_text",
    "check_task_navigation_text",
    "current_documents",
    "discover_markdown",
)
