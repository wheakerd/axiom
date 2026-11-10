"""Platform-specific hook declaration and documentation policy."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from .context import README_PATH, REPOSITORY_ROOT, display_path
from .manifests import MANIFEST_FILES, exact_json_object

EXPECTED_HOOK_DECLARATIONS = {
    "plugin/.codex-plugin/plugin.json": "./hooks/codex-hooks.json",
    "plugin/.claude-plugin/plugin.json": "./hooks/claude-hooks.json",
}
AUTHOR_KEYS = frozenset({"name", "url"})
HOOK_FILES = (
    "plugin/hooks/codex-hooks.json",
    "plugin/hooks/claude-hooks.json",
)
HOOK_TIMEOUT_SECONDS = 5
CLAUDE_HOOK_TIMEOUT_SECONDS = HOOK_TIMEOUT_SECONDS
CODEX_HOOK_TIMEOUT_SECONDS = HOOK_TIMEOUT_SECONDS

# The exact static text the UserPromptSubmit hook prints on both hosts. It stays ASCII
# without quotes, backslashes, or command-shell special characters, so one text serves
# the POSIX commands and the Windows wrapper.
PROMPT_TEXT = 'Axiom: material ambiguity that context cannot resolve is clarified before acting; completion rests on evidence observed in this session, names what remains unresolved, and replies in the language of the request.'

CLAUDE_COMMAND = (
    "printf '%s\\n\\n' 'You have Axiom in Claude Code. Load this startup front door "
    "before deciding whether any Axiom skill applies:'; "
    "cat \"${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md\""
)
CODEX_COMMAND = (
    "printf '%s\\n\\n' 'You have Axiom. Load this startup front door before deciding "
    "whether any Axiom skill applies:'; cat \"${PLUGIN_ROOT}/skills/using-axiom/SKILL.md\""
)
PROMPT_COMMAND = "printf '%s\\n' '" + PROMPT_TEXT + "'"

CODEX_WINDOWS_WRAPPER_PATH = Path("plugin/hooks/codex-session-start.cmd")
CODEX_WINDOWS_COMMAND = r'"%PLUGIN_ROOT%\hooks\codex-session-start.cmd"'
CODEX_WINDOWS_PROMPT_COMMAND = r'"%PLUGIN_ROOT%\hooks\codex-prompt-submit.cmd"'
CODEX_WINDOWS_WRAPPER_TEXT = '@echo off\nsetlocal DisableDelayedExpansion\necho You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:\necho(\ntype "%~dp0..\\skills\\using-axiom\\SKILL.md"\n'
CODEX_WINDOWS_PROMPT_WRAPPER_TEXT = '@echo off\nsetlocal DisableDelayedExpansion\necho ' + PROMPT_TEXT + '\n'

# Every packaged hook script, pinned byte for byte. A reviewer compares an installed
# copy with these texts; the Hook Reference renders each one verbatim.
PACKAGED_WRAPPERS: dict[str, str] = {
    "plugin/hooks/codex-session-start.cmd": CODEX_WINDOWS_WRAPPER_TEXT,
    "plugin/hooks/codex-prompt-submit.cmd": CODEX_WINDOWS_PROMPT_WRAPPER_TEXT,
}

SESSION_START_MATCHER = "startup|resume|clear|compact|fork"
APPROVED_HOOKS: dict[str, dict[str, dict[str, Any]]] = {
    "plugin/hooks/codex-hooks.json": {
        "SessionStart": {
            "matcher": SESSION_START_MATCHER,
            "handler": {
                "type": "command",
                "command": CODEX_COMMAND,
                "commandWindows": CODEX_WINDOWS_COMMAND,
                "timeout": HOOK_TIMEOUT_SECONDS,
                "statusMessage": "Loading Axiom routing",
            },
        },
        "UserPromptSubmit": {
            "handler": {
                "type": "command",
                "command": PROMPT_COMMAND,
                "commandWindows": CODEX_WINDOWS_PROMPT_COMMAND,
                "timeout": HOOK_TIMEOUT_SECONDS,
                "statusMessage": "Axiom prompt check",
            },
        },
    },
    "plugin/hooks/claude-hooks.json": {
        "SessionStart": {
            "matcher": SESSION_START_MATCHER,
            "handler": {
                "type": "command",
                "command": CLAUDE_COMMAND,
                "timeout": HOOK_TIMEOUT_SECONDS,
                "statusMessage": "Loading Axiom routing",
            },
        },
        "UserPromptSubmit": {
            "handler": {
                "type": "command",
                "command": PROMPT_COMMAND,
                "timeout": HOOK_TIMEOUT_SECONDS,
                "statusMessage": "Axiom prompt check",
            },
        },
    },
}


def resolve_declared_hook(
    manifest_path: str, raw_path: str, failures: list[str]
) -> Path | None:
    parsed = urlsplit(raw_path)
    if parsed.scheme or parsed.netloc or Path(parsed.path).is_absolute():
        failures.append(
            f"{manifest_path} hooks must be a repository-relative path, got {raw_path!r}"
        )
        return None

    # Manifest component paths resolve from the plugin root that holds the manifest.
    plugin_root = (REPOSITORY_ROOT / PurePosixPath(manifest_path).parents[1]).resolve()
    candidate = (plugin_root / parsed.path).resolve()
    try:
        candidate.relative_to(plugin_root)
    except ValueError:
        failures.append(f"{manifest_path} hooks path escapes the plugin root: {raw_path!r}")
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
            expected_group_keys = (
                {"matcher", "hooks"} if "matcher" in approved_event else {"hooks"}
            )
            if set(group) != expected_group_keys:
                failures.append(
                    f"{label}[0] keys changed; expected {sorted(expected_group_keys)}, "
                    f"found {sorted(group)}"
                )
            if "matcher" in approved_event:
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


def check_codex_windows_hook_security(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    """Pin every Windows handler to its packaged wrapper, a short timeout, and exact script bytes."""
    document = documents.get("plugin/hooks/codex-hooks.json")
    if isinstance(document, dict):
        approved_events = APPROVED_HOOKS["plugin/hooks/codex-hooks.json"]
        hooks = document.get("hooks")
        for event_name, approved_event in approved_events.items():
            try:
                handler = hooks[event_name][0]["hooks"][0]
            except (KeyError, IndexError, TypeError):
                continue
            if not isinstance(handler, dict):
                continue
            label = f"plugin/hooks/codex-hooks.json hooks.{event_name}[0].hooks[0]"
            if handler.get("commandWindows") != approved_event["handler"]["commandWindows"]:
                failures.append(
                    f"{label}.commandWindows must invoke only the approved packaged wrapper"
                )
            timeout = handler.get("timeout")
            if type(timeout) is not int or timeout != HOOK_TIMEOUT_SECONDS:
                failures.append(
                    f"{label}.timeout must be exactly {HOOK_TIMEOUT_SECONDS} seconds"
                )

    for relative_path, approved_text in PACKAGED_WRAPPERS.items():
        wrapper_path = REPOSITORY_ROOT / relative_path
        if wrapper_path.is_symlink():
            failures.append(
                f"{display_path(wrapper_path)} must be a regular packaged file, not a symlink"
            )
            continue
        try:
            wrapper_text = wrapper_path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {display_path(wrapper_path)}: {error}")
            continue
        if wrapper_text != approved_text:
            failures.append(
                f"{display_path(wrapper_path)} must contain only the approved packaged "
                "hook script"
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
