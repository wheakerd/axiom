"""Markdown parsing, Hook-reference, and repository-link policy."""

from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .context import REPOSITORY_ROOT, display_path
from .hooks import CODEX_WINDOWS_WRAPPER_TEXT, HOOK_FILES, hook_commands

FENCE_OPEN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
ATX_HEADING = re.compile(r"^[ \t]{0,3}#{1,6}(?:[ \t]+|$)(.*)$")
GFM_PUNCTUATION = re.compile(r"[\\!\"#$%&'()*+,./:;<=>?@\[\]^`{|}~]")
REFERENCE_LINK = re.compile(
    r"^[ \t]{0,3}\[([^]]+)\]:[ \t]*(?:<([^>]+)>|(\S+))"
)
HOOK_REFERENCE_RELATIVE = "docs/reference/hooks.md"
HOOK_REFERENCE_PATH = REPOSITORY_ROOT / HOOK_REFERENCE_RELATIVE


def fenced_blocks_and_masked_text(text: str) -> tuple[list[str], str]:
    blocks: list[str] = []
    masked_lines: list[str] = []
    current: list[str] | None = None
    fence_character = ""
    fence_length = 0

    for line in text.splitlines():
        if current is None:
            match = FENCE_OPEN.match(line)
            if match:
                opener = match.group(1)
                fence_character = opener[0]
                fence_length = len(opener)
                current = []
                masked_lines.append("")
            else:
                masked_lines.append(line)
            continue

        stripped = line.lstrip()
        leading = len(line) - len(stripped)
        run = len(stripped) - len(stripped.lstrip(fence_character))
        is_close = leading <= 3 and run >= fence_length and not stripped[run:].strip()
        if is_close:
            blocks.append("\n".join(current).strip())
            current = None
        else:
            current.append(line)
        masked_lines.append("")

    return blocks, "\n".join(masked_lines)


def check_documented_hook_command_text(
    text: str,
    documents: dict[str, dict[str, Any]],
    failures: list[str],
    *,
    wrapper_text: str = CODEX_WINDOWS_WRAPPER_TEXT,
) -> None:
    expected: dict[str, list[str]] = {}
    for relative_path in HOOK_FILES:
        document = documents.get(relative_path)
        if document is None:
            continue
        for command, labels in hook_commands(relative_path, document, failures).items():
            expected.setdefault(command, []).extend(labels)
    expected.setdefault(wrapper_text.strip(), []).append(
        "hooks/codex-session-start.cmd"
    )

    blocks, _ = fenced_blocks_and_masked_text(text)
    block_set = set(blocks)
    for command, labels in expected.items():
        if command not in block_set:
            failures.append(
                f"{HOOK_REFERENCE_RELATIVE} is missing an exact fenced command block for "
                f"{', '.join(labels)}; expected {command!r}"
            )

    documented_hook_commands = {
        block
        for block in block_set
        if "using-axiom" in block
        and (
            "PLUGIN_ROOT" in block
            or "CLAUDE_PLUGIN_ROOT" in block
            or "%~dp0" in block
        )
    }
    for command in sorted(documented_hook_commands - set(expected)):
        failures.append(
            f"{HOOK_REFERENCE_RELATIVE} contains a Hook command block not present in "
            "the checked-in declarations or wrapper: "
            f"{command!r}"
        )


def check_documented_hook_commands(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    try:
        text = HOOK_REFERENCE_PATH.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(
            f"cannot read {HOOK_REFERENCE_RELATIVE} for Hook command comparison: {error}"
        )
        return
    check_documented_hook_command_text(text, documents, failures)


def mask_inline_code(line: str) -> str:
    characters = list(line)
    index = 0
    while index < len(line):
        if line[index] != "`":
            index += 1
            continue
        run_end = index
        while run_end < len(line) and line[run_end] == "`":
            run_end += 1
        marker = line[index:run_end]
        close = line.find(marker, run_end)
        if close < 0:
            index = run_end
            continue
        for position in range(index, close + len(marker)):
            characters[position] = " "
        index = close + len(marker)
    return "".join(characters)


def is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def inline_link_destinations(line: str) -> Iterator[str]:
    line = mask_inline_code(line)
    position = 0
    while True:
        marker = line.find("](", position)
        if marker < 0:
            return
        if is_escaped(line, marker) or line.rfind("[", 0, marker) < 0:
            position = marker + 2
            continue

        depth = 1
        cursor = marker + 2
        while cursor < len(line) and depth:
            if is_escaped(line, cursor):
                cursor += 1
                continue
            if line[cursor] == "(":
                depth += 1
            elif line[cursor] == ")":
                depth -= 1
            cursor += 1
        if depth:
            return
        yield line[marker + 2 : cursor - 1]
        position = cursor


def link_destination(raw_destination: str) -> str:
    raw_destination = raw_destination.strip()
    if raw_destination.startswith("<"):
        close = raw_destination.find(">")
        return raw_destination[1:close] if close >= 0 else raw_destination
    return raw_destination.split(maxsplit=1)[0] if raw_destination else ""


def gfm_heading_slug(heading: str) -> str:
    heading = re.sub(r"!?\[([^]]+)]\([^)]*\)", r"\1", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = unescape(heading).lower().strip()
    heading = GFM_PUNCTUATION.sub("", heading)
    return re.sub(r"\s+", "-", heading)


def gfm_heading_anchors(searchable_markdown: str) -> set[str]:
    anchors: set[str] = set()
    next_suffix: dict[str, int] = {}
    for line in searchable_markdown.splitlines():
        match = ATX_HEADING.match(line)
        if not match:
            continue
        heading = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(1)).strip()
        base = gfm_heading_slug(heading)
        suffix = next_suffix.get(base, 0)
        candidate = base if suffix == 0 else f"{base}-{suffix}"
        while candidate in anchors:
            suffix += 1
            candidate = f"{base}-{suffix}"
        anchors.add(candidate)
        next_suffix[base] = suffix + 1
    return anchors


def validate_link(
    source: Path,
    line_number: int,
    raw_destination: str,
    anchor_cache: dict[Path, set[str]],
    failures: list[str],
    *,
    root: Path = REPOSITORY_ROOT,
) -> None:
    root = root.resolve()

    def label(path: Path) -> str:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return str(path)

    destination = link_destination(raw_destination)
    if not destination:
        return
    destination = re.sub(r"\\([ ()])", r"\1", destination)
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc or destination.startswith("//"):
        return

    decoded_path = unquote(parsed.path)
    if decoded_path:
        base = root if decoded_path.startswith("/") else source.parent
        candidate = (base / decoded_path.lstrip("/")).resolve()
    else:
        candidate = source.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        failures.append(
            f"{label(source)}:{line_number} link escapes the repository: {destination!r}"
        )
        return
    if not candidate.exists():
        failures.append(
            f"{label(source)}:{line_number} has broken repository-relative link "
            f"{destination!r} (resolved to {label(candidate)})"
        )
        return

    if parsed.fragment and candidate.is_file() and candidate.suffix.lower() == ".md":
        fragment = unquote(parsed.fragment)
        anchors = anchor_cache.get(candidate)
        if anchors is None:
            failures.append(
                f"{label(source)}:{line_number} cannot validate fragment "
                f"{fragment!r}; Markdown target {label(candidate)} was not indexed"
            )
        elif fragment not in anchors:
            failures.append(
                f"{label(source)}:{line_number} links to missing Markdown fragment "
                f"{fragment!r} in {label(candidate)}"
            )


def check_markdown_links(
    failures: list[str], *, root: Path = REPOSITORY_ROOT
) -> int:
    root = root.resolve()

    def label(path: Path) -> str:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return str(path)

    markdown_files = sorted(
        path
        for path in root.rglob("*.md")
        if ".git" not in path.relative_to(root).parts and path.is_file()
    )
    searchable_documents: dict[Path, str] = {}
    anchor_cache: dict[Path, set[str]] = {}
    for path in markdown_files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            failures.append(f"cannot read Markdown file {label(path)}: {error}")
            continue
        _, searchable = fenced_blocks_and_masked_text(text)
        searchable_documents[path] = searchable
        anchor_cache[path.resolve()] = gfm_heading_anchors(searchable)

    for path, searchable in searchable_documents.items():
        for line_number, line in enumerate(searchable.splitlines(), start=1):
            for raw_destination in inline_link_destinations(line):
                validate_link(
                    path,
                    line_number,
                    raw_destination,
                    anchor_cache,
                    failures,
                    root=root,
                )
            reference = REFERENCE_LINK.match(mask_inline_code(line))
            if reference and not reference.group(1).startswith("^"):
                validate_link(
                    path,
                    line_number,
                    reference.group(2) or reference.group(3) or "",
                    anchor_cache,
                    failures,
                    root=root,
                )
    return len(markdown_files)
