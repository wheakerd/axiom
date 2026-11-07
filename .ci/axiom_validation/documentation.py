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
    HOOK_REFERENCE_RELATIVE,
    ATX_HEADING,
    REFERENCE_LINK,
    check_markdown_links,
    check_documented_hook_command_text,
    fenced_blocks_and_masked_text,
    inline_link_destinations,
    link_destination,
    mask_inline_code,
)
from .readme_facts import check_readme_facts
from .repository_policy import BUNDLED_SKILL_ORDER, check_release_version_surfaces
from .runtime_identity import check_runtime_identity

DOCS_ROOT = "docs/en/"
TRANSLATIONS_ROOT = "docs/zh-CN/"
README_TRANSLATION = "README.zh-CN.md"
DOCS_INDEX = "docs/en/README.md"
DOCS_DIRECTORY = "docs"
LANGUAGE_SELECTOR = "README.md"

# RFC 5646 section 2.1 ABNF, matched case-insensitively over ASCII only. The
# primary language subtag keeps only its 2*3ALPHA form: 4ALPHA is reserved and
# 5*8ALPHA is for registration, so an ordinary word such as "assets" is no tag.
_LANGTAG = (
    r"[a-z]{2,3}(?:-[a-z]{3}){0,3}"  # language, extlang
    r"(?:-[a-z]{4})?"  # script
    r"(?:-(?:[a-z]{2}|[0-9]{3}))?"  # region
    r"(?:-(?:[a-z0-9]{5,8}|[0-9][a-z0-9]{3}))*"  # variant
    r"(?:-[0-9a-wyz](?:-[a-z0-9]{2,8})+)*"  # extension
    r"(?:-x(?:-[a-z0-9]{1,8})+)?"  # privateuse
)
_PRIVATEUSE = r"x(?:-[a-z0-9]{1,8})+"
_GRANDFATHERED = (
    "en-GB-oed", "i-ami", "i-bnn", "i-default", "i-enochian", "i-hak", "i-klingon",
    "i-lux", "i-mingo", "i-navajo", "i-pwn", "i-tao", "i-tay", "i-tsu", "sgn-BE-FR",
    "sgn-BE-NL", "sgn-CH-DE", "art-lojban", "cel-gaulish", "no-bok", "no-nyn",
    "zh-guoyu", "zh-hakka", "zh-min", "zh-min-nan", "zh-xiang",
)
LANGUAGE_TAG = re.compile(
    rf"{_LANGTAG}|{_PRIVATEUSE}|"
    + "|".join(re.escape(tag) for tag in _GRANDFATHERED),
    re.IGNORECASE | re.ASCII,
)

ROOT_CURRENT_DOCUMENTS = (
    "README.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
)
GENERATED_MARKER = re.compile(
    r"<!--\s*([a-z0-9][a-z0-9._:-]*?):(start|end)\s*-->"
)
SETEXT_HEADING = re.compile(r"^[ \t]{0,3}(=+|-+)[ \t]*$")


@dataclass(frozen=True)
class DocumentationReport:
    """Counts for one validation run."""

    markdown_count: int
    current_document_count: int
    indexed_document_count: int
    generated_region_count: int
    translation_count: int = 0


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


def is_translation(relative_path: str) -> bool:
    """Return whether a Markdown path is a Simplified Chinese twin of an English source."""
    return relative_path.startswith(TRANSLATIONS_ROOT) or relative_path == README_TRANSLATION


def translation_source(relative_path: str) -> str:
    """Return the English source path that owns a translation."""
    if relative_path == README_TRANSLATION:
        return "README.md"
    return DOCS_ROOT + relative_path[len(TRANSLATIONS_ROOT):]


def is_current_document(relative_path: str) -> bool:
    """Return whether a Markdown path belongs to the maintained current set."""
    if is_translation(relative_path):
        return False
    return relative_path in ROOT_CURRENT_DOCUMENTS or relative_path.startswith(DOCS_ROOT)


def current_documents(root: Path = REPOSITORY_ROOT) -> tuple[Path, ...]:
    root = root.resolve()
    return tuple(
        path
        for path in discover_markdown(root)
        if is_current_document(path.relative_to(root).as_posix())
    )


def translation_documents(root: Path = REPOSITORY_ROOT) -> tuple[Path, ...]:
    """Return every translation in stable path order."""
    root = root.resolve()
    return tuple(
        path
        for path in discover_markdown(root)
        if is_translation(path.relative_to(root).as_posix())
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
    index = root / DOCS_INDEX
    current = {
        path.relative_to(root).as_posix(): path
        for path in current_documents(root)
        if path.relative_to(root).as_posix() not in ROOT_CURRENT_DOCUMENTS
    }
    expected = set(current) - {DOCS_INDEX}
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
            f"{DOCS_INDEX} does not directly index current document {missing}"
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
    reachable = {DOCS_INDEX}
    pending = [DOCS_INDEX]
    while pending:
        source = pending.pop()
        for target in sorted(graph.get(source, ())):
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    for orphan in sorted(expected - reachable):
        failures.append(
            f"current document {orphan} is orphaned from {DOCS_INDEX} navigation"
        )
    return len(expected & direct_targets)


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


def check_guidance_boundaries(root: Path, failures: list[str]) -> None:
    root = root.resolve()
    for path in (*current_documents(root), *translation_documents(root)):
        text = _read_text(path, root, failures)
        if text is not None:
            check_private_guidance_text(_label(path, root), text, failures)


def _generated_regions(text: str) -> dict[str, str]:
    """Map each closed generated marker to the text between its start and end."""
    pattern = re.compile(
        r"<!--\s*([a-z0-9][a-z0-9._:-]*?):start\s*-->(.*?)<!--\s*\1:end\s*-->",
        re.DOTALL,
    )
    return {match.group(1): match.group(2) for match in pattern.finditer(text)}


def _link_targets(
    source: Path, text: str, root: Path
) -> tuple[set[str], set[str], set[str]]:
    """Return exact local targets, local targets with translations folded, and external links."""
    exact: set[str] = set()
    normalized: set[str] = set()
    external: set[str] = set()
    for raw in _raw_destinations(text):
        target = _local_target(source, raw, root)
        if target is None:
            destination = link_destination(raw)
            parsed = urlsplit(destination)
            if parsed.scheme or parsed.netloc:
                external.add(destination)
            continue
        exact.add(target)
        normalized.add(translation_source(target) if is_translation(target) else target)
    return exact, normalized, external


def check_translation_text(
    relative_path: str,
    text: str,
    source_relative_path: str,
    source_text: str,
    failures: list[str],
    *,
    root: Path = REPOSITORY_ROOT,
) -> None:
    """Require a translation to keep its source's structure, code, facts, and links."""
    root = root.resolve()
    check_heading_text(relative_path, text, failures)
    source_blocks, source_searchable = fenced_blocks_and_masked_text(source_text)
    mirror_blocks, mirror_searchable = fenced_blocks_and_masked_text(text)
    if _heading_levels(source_searchable) != _heading_levels(mirror_searchable):
        failures.append(
            f"{relative_path} heading structure differs from {source_relative_path}"
        )
    if source_blocks != mirror_blocks:
        failures.append(
            f"{relative_path} fenced code blocks differ from {source_relative_path}; "
            "code, commands, and examples stay identical"
        )
    if _generated_regions(source_text) != _generated_regions(text):
        failures.append(
            f"{relative_path} generated regions differ from {source_relative_path}"
        )
    source_path = root / source_relative_path
    mirror_path = root / relative_path
    source_exact, source_local, source_external = _link_targets(
        source_path, source_text, root
    )
    mirror_exact, mirror_local, mirror_external = _link_targets(mirror_path, text, root)
    if source_local != mirror_local or source_external != mirror_external:
        failures.append(
            f"{relative_path} link targets differ from {source_relative_path}; "
            "a translation may substitute a document's own translation, nothing else"
        )
    if relative_path not in source_exact:
        failures.append(
            f"{source_relative_path} must link to its translation {relative_path}"
        )
    if source_relative_path not in mirror_exact:
        failures.append(
            f"{relative_path} must link to its English source {source_relative_path}"
        )


def check_translations(root: Path, failures: list[str]) -> int:
    """Validate every translation against its English source."""
    root = root.resolve()
    paths = translation_documents(root)
    for path in paths:
        relative_path = _label(path, root)
        source_relative_path = translation_source(relative_path)
        source_path = root / source_relative_path
        if not source_path.is_file():
            failures.append(
                f"{relative_path} has no English source {source_relative_path}"
            )
            continue
        text = _read_text(path, root, failures)
        source_text = _read_text(source_path, root, failures)
        if text is not None and source_text is not None:
            check_translation_text(
                relative_path, text, source_relative_path, source_text, failures, root=root
            )
    return len(paths)


def is_language_tag(name: str) -> bool:
    """Return whether a name is a syntactically valid BCP 47 language tag."""
    return LANGUAGE_TAG.fullmatch(name) is not None


def check_docs_layout(root: Path, failures: list[str]) -> int:
    """Require language-tag directories and the language selector directly under docs/."""
    docs = root.resolve() / DOCS_DIRECTORY
    if not docs.is_dir():
        failures.append(f"{DOCS_DIRECTORY}/ must be a directory")
        return 0
    language_count = 0
    for entry in sorted(docs.iterdir()):
        label = f"{DOCS_DIRECTORY}/{entry.name}"
        if entry.is_dir():
            if is_language_tag(entry.name):
                language_count += 1
            else:
                failures.append(
                    f"{label}/ must be named by a BCP 47 language tag; each direct "
                    f"subdirectory of {DOCS_DIRECTORY}/ is one localized documentation set"
                )
        elif entry.name != LANGUAGE_SELECTOR:
            failures.append(
                f"{label} is not allowed; {DOCS_DIRECTORY}/{LANGUAGE_SELECTOR} is the "
                f"only direct file under {DOCS_DIRECTORY}/"
            )
    return language_count


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

    wrapper_path = root / "plugin" / "hooks" / "codex-session-start.cmd"
    wrapper = _read_text(wrapper_path, root, failures)

    reference_path = root / HOOK_REFERENCE_RELATIVE
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
    check_readme_facts(failures)
    check_release_version_surfaces(failures)


def check_documentation(
    failures: list[str],
    *,
    root: Path = REPOSITORY_ROOT,
    include_canonical_owners: bool = True,
) -> DocumentationReport:
    """Validate the complete public documentation architecture."""
    root = root.resolve()
    markdown_count = check_markdown_links(failures, root=root)
    check_docs_layout(root, failures)
    current_count = check_current_headings(root, failures)
    indexed_count = check_docs_index_and_orphans(root, failures)
    generated_count = check_generated_markers(root, failures)
    translation_count = check_translations(root, failures)
    check_guidance_boundaries(root, failures)
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
        translation_count=translation_count,
    )


__all__ = (
    "DocumentationReport",
    "DOCS_INDEX",
    "DOCS_ROOT",
    "README_TRANSLATION",
    "TRANSLATIONS_ROOT",
    "check_current_headings",
    "check_docs_index_and_orphans",
    "check_docs_layout",
    "check_documentation",
    "check_generated_marker_text",
    "check_guidance_boundaries",
    "check_heading_text",
    "check_hook_reference",
    "check_private_guidance_text",
    "check_translation_text",
    "check_translations",
    "current_documents",
    "discover_markdown",
    "is_language_tag",
    "is_translation",
    "translation_documents",
    "translation_source",
)
