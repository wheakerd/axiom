#!/usr/bin/env python3
"""Validate Axiom's concrete publication invariants without network access."""

from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPOSITORY_ROOT / "README.md"
RELEASE_VERSION = "0.3.1"

REQUIRED_PUBLIC_FILES = (
    "README.md",
    "docs/getting-started.md",
    "docs/architecture.md",
    "docs/examples.md",
    "docs/trust-model.md",
    "docs/compatibility.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "docs/releases/v0.3.0.md",
    "docs/releases/v0.3.1.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/pull_request_template.md",
)

JSON_FILES = (
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "hooks/codex-hooks.json",
    "hooks/claude-hooks.json",
)
MANIFEST_FILES = (
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
)
EXPECTED_HOOK_DECLARATIONS = {
    ".codex-plugin/plugin.json": "./hooks/codex-hooks.json",
    ".claude-plugin/plugin.json": "./hooks/claude-hooks.json",
}
EXPECTED_SKILLS_ROOT = "./skills/"
EXPECTED_PLUGIN_ROOT = "./"
HOOK_FILES = (
    "hooks/codex-hooks.json",
    "hooks/claude-hooks.json",
)
EXPECTED_DIRECT_SKILLS = (
    "agents-architect",
    "reversible-system-change",
    "traceable-git-submit",
    "using-axiom",
)

CODEX_COMMAND = (
    "printf '%s\\n\\n' 'You have Axiom. Load this startup front door before deciding "
    "whether any Axiom skill applies:'; cat \"${PLUGIN_ROOT}/skills/using-axiom/SKILL.md\""
)
CODEX_WINDOWS_COMMAND = (
    "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Write-Output 'You have "
    "Axiom. Load this startup front door before deciding whether any Axiom skill "
    "applies:'; Write-Output ''; Get-Content -Raw (Join-Path $env:PLUGIN_ROOT "
    "'skills/using-axiom/SKILL.md')\""
)
CLAUDE_SESSION_COMMAND = (
    "echo 'You have Axiom. Load this startup front door before deciding whether any "
    "Axiom skill applies:'; cat \"${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md\""
)
CLAUDE_PRECOMPACT_COMMAND = (
    "echo 'You have Axiom. Preserve this routing front door while compacting:'; cat "
    "\"${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md\""
)
APPROVED_HOOKS: dict[str, dict[str, dict[str, Any]]] = {
    "hooks/codex-hooks.json": {
        "SessionStart": {
            "matcher": "startup|resume|clear|compact",
            "handler": {
                "type": "command",
                "command": CODEX_COMMAND,
                "commandWindows": CODEX_WINDOWS_COMMAND,
                "statusMessage": "Loading Axiom routing",
            },
        },
    },
    "hooks/claude-hooks.json": {
        "SessionStart": {
            "matcher": "startup|resume|clear|compact",
            "handler": {
                "type": "command",
                "command": CLAUDE_SESSION_COMMAND,
                "statusMessage": "Loading Axiom routing",
            },
        },
        "PreCompact": {
            "matcher": "manual|auto",
            "handler": {
                "type": "command",
                "command": CLAUDE_PRECOMPACT_COMMAND,
                "statusMessage": "Preserving Axiom routing",
            },
        },
    },
}

FENCE_OPEN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
ATX_HEADING = re.compile(r"^[ \t]{0,3}#{1,6}(?:[ \t]+|$)(.*)$")
GFM_PUNCTUATION = re.compile(r"[\\!\"#$%&'()*+,./:;<=>?@\[\]^`{|}~]")
REFERENCE_LINK = re.compile(
    r"^[ \t]{0,3}\[([^]]+)\]:[ \t]*(?:<([^>]+)>|(\S+))"
)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path, failures: list[str]) -> dict[str, Any] | None:
    label = display_path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"missing required JSON file: {label}")
        return None
    except OSError as error:
        failures.append(f"cannot read {label}: {error}")
        return None

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        failures.append(
            f"invalid JSON in {label}:{error.lineno}:{error.colno}: {error.msg}"
        )
        return None

    if not isinstance(value, dict):
        failures.append(f"{label} must contain a top-level JSON object")
        return None
    return value


def check_required_files(failures: list[str]) -> None:
    for relative_path in REQUIRED_PUBLIC_FILES:
        if not (REPOSITORY_ROOT / relative_path).is_file():
            failures.append(
                f"missing required public file: {relative_path}; restore the accepted publication surface"
            )


def check_manifest_versions(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    versions: dict[str, str] = {}
    for relative_path in MANIFEST_FILES:
        document = documents.get(relative_path)
        if document is None:
            continue
        version = document.get("version")
        if not isinstance(version, str):
            failures.append(f"{relative_path} must declare a string version")
            continue
        versions[relative_path] = version

    if len(versions) == len(MANIFEST_FILES) and len(set(versions.values())) != 1:
        rendered = ", ".join(f"{path}={version!r}" for path, version in versions.items())
        failures.append(f"plugin manifest versions disagree: {rendered}")

    for relative_path, version in versions.items():
        if version != RELEASE_VERSION:
            failures.append(
                f"{relative_path} version is {version!r}; publication requires {RELEASE_VERSION!r}"
            )


def marketplace_plugin(
    document: dict[str, Any], relative_path: str, failures: list[str]
) -> dict[str, Any] | None:
    plugins = document.get("plugins")
    if not isinstance(plugins, list):
        failures.append(f"{relative_path} must contain a plugins array")
        return None
    matches = [
        entry
        for entry in plugins
        if isinstance(entry, dict) and entry.get("name") == "axiom"
    ]
    if len(matches) != 1:
        failures.append(
            f"{relative_path} must contain exactly one 'axiom' plugin entry, found {len(matches)}"
        )
        return None
    return matches[0]


def check_shared_source_roots(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    for manifest_path in MANIFEST_FILES:
        document = documents.get(manifest_path)
        if document is None:
            continue
        skills = document.get("skills")
        if skills != EXPECTED_SKILLS_ROOT:
            failures.append(
                f"{manifest_path} skills is {skills!r}; expected the shared source "
                f"{EXPECTED_SKILLS_ROOT!r}"
            )

    codex_path = ".agents/plugins/marketplace.json"
    codex_document = documents.get(codex_path)
    if codex_document is not None:
        entry = marketplace_plugin(codex_document, codex_path, failures)
        if entry is not None:
            source = entry.get("source")
            if not isinstance(source, dict):
                failures.append(f"{codex_path} axiom source must be an object")
            elif source.get("path") != EXPECTED_PLUGIN_ROOT:
                failures.append(
                    f"{codex_path} axiom source.path is {source.get('path')!r}; "
                    f"expected shared plugin root {EXPECTED_PLUGIN_ROOT!r}"
                )

    claude_path = ".claude-plugin/marketplace.json"
    claude_document = documents.get(claude_path)
    if claude_document is not None:
        entry = marketplace_plugin(claude_document, claude_path, failures)
        if entry is not None and entry.get("source") != EXPECTED_PLUGIN_ROOT:
            failures.append(
                f"{claude_path} axiom source is {entry.get('source')!r}; "
                f"expected shared plugin root {EXPECTED_PLUGIN_ROOT!r}"
            )


def resolve_declared_hook(
    manifest_path: str, raw_path: str, failures: list[str]
) -> Path | None:
    parsed = urlsplit(raw_path)
    if parsed.scheme or parsed.netloc or Path(parsed.path).is_absolute():
        failures.append(
            f"{manifest_path} hooks must be a repository-relative path, got {raw_path!r}"
        )
        return None

    candidate = (REPOSITORY_ROOT / parsed.path).resolve()
    try:
        candidate.relative_to(REPOSITORY_ROOT)
    except ValueError:
        failures.append(f"{manifest_path} hooks path escapes the repository: {raw_path!r}")
        return None

    if not candidate.is_file():
        failures.append(
            f"{manifest_path} declares missing hook file {raw_path!r} ({display_path(candidate)})"
        )
        return None
    return candidate


def check_declared_hook_paths(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    for manifest_path in MANIFEST_FILES:
        document = documents.get(manifest_path)
        if document is None:
            continue
        raw_path = document.get("hooks")
        if not isinstance(raw_path, str) or not raw_path.strip():
            failures.append(f"{manifest_path} must declare a non-empty string hooks path")
            continue
        expected_path = EXPECTED_HOOK_DECLARATIONS[manifest_path]
        if raw_path != expected_path:
            failures.append(
                f"{manifest_path} hooks is {raw_path!r}; expected {expected_path!r}"
            )
        resolve_declared_hook(manifest_path, raw_path, failures)


def check_exact_hook_shapes(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    for relative_path, approved_events in APPROVED_HOOKS.items():
        document = documents.get(relative_path)
        if document is None:
            continue
        hooks = document.get("hooks")
        if not isinstance(hooks, dict):
            failures.append(f"{relative_path} must contain a hooks object")
            continue

        actual_events = set(hooks)
        expected_events = set(approved_events)
        if actual_events != expected_events:
            failures.append(
                f"{relative_path} event set changed; expected {sorted(expected_events)}, "
                f"found {sorted(actual_events)}"
            )

        for event_name, approved_event in approved_events.items():
            groups = hooks.get(event_name)
            label = f"{relative_path} hooks.{event_name}"
            if not isinstance(groups, list):
                failures.append(f"{label} must be an array")
                continue
            if len(groups) != 1:
                failures.append(f"{label} must contain exactly one group, found {len(groups)}")
            if not groups or not isinstance(groups[0], dict):
                if groups:
                    failures.append(f"{label}[0] must be an object")
                continue

            group = groups[0]
            expected_group_keys = {"matcher", "hooks"}
            if set(group) != expected_group_keys:
                failures.append(
                    f"{label}[0] keys changed; expected {sorted(expected_group_keys)}, "
                    f"found {sorted(group)}"
                )
            expected_matcher = approved_event["matcher"]
            if group.get("matcher") != expected_matcher:
                failures.append(
                    f"{label}[0].matcher is {group.get('matcher')!r}; "
                    f"expected {expected_matcher!r}"
                )

            handlers = group.get("hooks")
            if not isinstance(handlers, list):
                failures.append(f"{label}[0].hooks must be an array")
                continue
            if len(handlers) != 1:
                failures.append(
                    f"{label}[0].hooks must contain exactly one handler, found {len(handlers)}"
                )
            if not handlers or not isinstance(handlers[0], dict):
                if handlers:
                    failures.append(f"{label}[0].hooks[0] must be an object")
                continue

            handler = handlers[0]
            approved_handler = approved_event["handler"]
            if set(handler) != set(approved_handler):
                failures.append(
                    f"{label}[0].hooks[0] keys changed; expected "
                    f"{sorted(approved_handler)}, found {sorted(handler)}"
                )
            if handler.get("type") != "command":
                failures.append(
                    f"{label}[0].hooks[0].type is {handler.get('type')!r}; expected 'command'"
                )
            for field, approved_value in approved_handler.items():
                if field == "type":
                    continue
                if handler.get(field) != approved_value:
                    qualifier = "approved safe " if field.startswith("command") else ""
                    failures.append(
                        f"{label}[0].hooks[0].{field} changed; "
                        f"expected {qualifier}value {approved_value!r}"
                    )


def hook_commands(
    relative_path: str, document: dict[str, Any], failures: list[str]
) -> dict[str, list[str]]:
    hooks = document.get("hooks")
    if not isinstance(hooks, dict):
        failures.append(f"{relative_path} must contain a hooks object")
        return {}

    commands: dict[str, list[str]] = {}
    for event_name, groups in hooks.items():
        if not isinstance(groups, list):
            failures.append(f"{relative_path} hooks.{event_name} must be an array")
            continue
        for group_index, group in enumerate(groups):
            if not isinstance(group, dict):
                failures.append(
                    f"{relative_path} hooks.{event_name}[{group_index}] must be an object"
                )
                continue
            handlers = group.get("hooks")
            if not isinstance(handlers, list):
                failures.append(
                    f"{relative_path} hooks.{event_name}[{group_index}].hooks must be an array"
                )
                continue
            for handler_index, handler in enumerate(handlers):
                if not isinstance(handler, dict):
                    failures.append(
                        f"{relative_path} hooks.{event_name}[{group_index}].hooks[{handler_index}] must be an object"
                    )
                    continue
                if handler.get("type") != "command":
                    continue
                label = (
                    f"{relative_path} hooks.{event_name}[{group_index}]"
                    f".hooks[{handler_index}]"
                )
                command = handler.get("command")
                if not isinstance(command, str) or not command:
                    failures.append(f"{label}.command must be a non-empty string")
                else:
                    commands.setdefault(command, []).append(f"{label}.command")
                if "commandWindows" in handler:
                    windows_command = handler["commandWindows"]
                    if not isinstance(windows_command, str) or not windows_command:
                        failures.append(f"{label}.commandWindows must be a non-empty string")
                    else:
                        commands.setdefault(windows_command, []).append(
                            f"{label}.commandWindows"
                        )
    if not commands:
        failures.append(f"{relative_path} contains no command hook to document")
    return commands


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


def check_documented_hook_commands(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    expected: dict[str, list[str]] = {}
    for relative_path in HOOK_FILES:
        document = documents.get(relative_path)
        if document is None:
            continue
        for command, labels in hook_commands(relative_path, document, failures).items():
            expected.setdefault(command, []).extend(labels)

    try:
        readme = README_PATH.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read README.md for hook command comparison: {error}")
        return

    blocks, _ = fenced_blocks_and_masked_text(readme)
    block_set = set(blocks)
    for command, labels in expected.items():
        if command not in block_set:
            failures.append(
                "README.md is missing an exact fenced command block for "
                f"{', '.join(labels)}; expected {command!r}"
            )

    documented_hook_commands = {
        block
        for block in block_set
        if "skills/using-axiom/SKILL.md" in block
        and ("PLUGIN_ROOT" in block or "CLAUDE_PLUGIN_ROOT" in block)
    }
    for command in sorted(documented_hook_commands - set(expected)):
        failures.append(
            "README.md contains a hook command block not present in the checked-in hook JSON: "
            f"{command!r}"
        )


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
) -> None:
    destination = link_destination(raw_destination)
    if not destination:
        return
    destination = re.sub(r"\\([ ()])", r"\1", destination)
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc or destination.startswith("//"):
        return

    decoded_path = unquote(parsed.path)
    if decoded_path:
        base = REPOSITORY_ROOT if decoded_path.startswith("/") else source.parent
        candidate = (base / decoded_path.lstrip("/")).resolve()
    else:
        candidate = source.resolve()
    try:
        candidate.relative_to(REPOSITORY_ROOT)
    except ValueError:
        failures.append(
            f"{display_path(source)}:{line_number} link escapes the repository: {destination!r}"
        )
        return
    if not candidate.exists():
        failures.append(
            f"{display_path(source)}:{line_number} has broken repository-relative link "
            f"{destination!r} (resolved to {display_path(candidate)})"
        )
        return

    if parsed.fragment and candidate.is_file() and candidate.suffix.lower() == ".md":
        fragment = unquote(parsed.fragment)
        anchors = anchor_cache.get(candidate)
        if anchors is None:
            failures.append(
                f"{display_path(source)}:{line_number} cannot validate fragment "
                f"{fragment!r}; Markdown target {display_path(candidate)} was not indexed"
            )
        elif fragment not in anchors:
            failures.append(
                f"{display_path(source)}:{line_number} links to missing Markdown fragment "
                f"{fragment!r} in {display_path(candidate)}"
            )


def check_markdown_links(failures: list[str]) -> int:
    markdown_files = sorted(
        path
        for path in REPOSITORY_ROOT.rglob("*.md")
        if ".git" not in path.relative_to(REPOSITORY_ROOT).parts and path.is_file()
    )
    searchable_documents: dict[Path, str] = {}
    anchor_cache: dict[Path, set[str]] = {}
    for path in markdown_files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            failures.append(f"cannot read Markdown file {display_path(path)}: {error}")
            continue
        _, searchable = fenced_blocks_and_masked_text(text)
        searchable_documents[path] = searchable
        anchor_cache[path.resolve()] = gfm_heading_anchors(searchable)

    for path, searchable in searchable_documents.items():
        for line_number, line in enumerate(searchable.splitlines(), start=1):
            for raw_destination in inline_link_destinations(line):
                validate_link(
                    path, line_number, raw_destination, anchor_cache, failures
                )
            reference = REFERENCE_LINK.match(mask_inline_code(line))
            if reference and not reference.group(1).startswith("^"):
                validate_link(
                    path,
                    line_number,
                    reference.group(2) or reference.group(3) or "",
                    anchor_cache,
                    failures,
                )
    return len(markdown_files)


def check_packaged_skills(failures: list[str]) -> None:
    skills_root = REPOSITORY_ROOT / "skills"
    if not skills_root.is_dir():
        failures.append("missing packaged skills/ directory")
        return

    direct = sorted(
        child.name
        for child in skills_root.iterdir()
        if child.is_dir() and (child / "SKILL.md").is_file()
    )
    if tuple(direct) != EXPECTED_DIRECT_SKILLS:
        failures.append(
            "direct packaged skill set changed; expected "
            f"{', '.join(EXPECTED_DIRECT_SKILLS)}, found {', '.join(direct) or '(none)'}"
        )

    expected_paths = {
        Path("skills") / skill_name / "SKILL.md"
        for skill_name in EXPECTED_DIRECT_SKILLS
    }
    unexpected = sorted(
        path.relative_to(REPOSITORY_ROOT)
        for path in skills_root.rglob("SKILL.md")
        if path.relative_to(REPOSITORY_ROOT) not in expected_paths
    )
    if unexpected:
        failures.append(
            "nested or unexpected packaged SKILL.md files are not allowed: "
            + ", ".join(path.as_posix() for path in unexpected)
        )


def main() -> int:
    failures: list[str] = []
    check_required_files(failures)

    documents: dict[str, dict[str, Any]] = {}
    for relative_path in JSON_FILES:
        document = load_json(REPOSITORY_ROOT / relative_path, failures)
        if document is not None:
            documents[relative_path] = document

    check_manifest_versions(documents, failures)
    check_shared_source_roots(documents, failures)
    check_declared_hook_paths(documents, failures)
    check_exact_hook_shapes(documents, failures)
    check_documented_hook_commands(documents, failures)
    check_packaged_skills(failures)
    markdown_count = check_markdown_links(failures)

    conventional_hook = REPOSITORY_ROOT / "hooks" / "hooks.json"
    if conventional_hook.exists():
        failures.append(
            "hooks/hooks.json must remain absent so platform-specific hooks are not auto-discovered"
        )

    if failures:
        print("Publication validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(
        "Publication validation passed: "
        f"{len(REQUIRED_PUBLIC_FILES)} required files, {len(JSON_FILES)} JSON files, "
        f"{markdown_count} Markdown files, version {RELEASE_VERSION}, hooks, and packaged skills."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
