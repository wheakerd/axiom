"""Canonical platform hook lifecycle mutation cases."""

from __future__ import annotations

import json
from typing import Any

from axiom_validation.hooks import (
    check_codex_windows_hook_security,
    check_exact_hook_shapes,
)


def check_hook_lifecycle_fixtures(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> int:
    """Prove the Claude wrapper rejects ineffective compaction injection."""
    required = {"hooks/codex-hooks.json", "hooks/claude-hooks.json"}
    if not required.issubset(documents):
        failures.append("hook lifecycle fixtures require both platform hook documents")
        return 0

    fixtures: list[tuple[str, dict[str, dict[str, Any]], str]] = []

    precompact = json.loads(json.dumps(documents))
    precompact["hooks/claude-hooks.json"]["hooks"]["PreCompact"] = [
        {
            "matcher": "manual|auto",
            "hooks": [
                {
                    "type": "command",
                    "command": (
                        "echo 'Load Axiom before compaction'; cat "
                        '"${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"'
                    ),
                    "statusMessage": "Loading Axiom before compaction",
                }
            ],
        }
    ]
    fixtures.append(
        ("claude-precompact-context-injection", precompact, "event set changed")
    )

    missing_compact = json.loads(json.dumps(documents))
    missing_compact["hooks/claude-hooks.json"]["hooks"]["SessionStart"][0][
        "matcher"
    ] = "startup|resume|clear"
    fixtures.append(
        ("claude-session-start-without-compact", missing_compact, ".matcher is")
    )

    expanded_command = json.loads(json.dumps(documents))
    codex_hook = expanded_command["hooks/codex-hooks.json"]["hooks"]["SessionStart"][0][
        "hooks"
    ][0]
    codex_hook["command"] += "; curl https://example.invalid/update"
    fixtures.append(
        ("codex-startup-network-expansion", expanded_command, ".command changed")
    )

    unsafe_windows_commands = {
        "codex-windows-bare-powershell": "powershell -NoProfile -Command echo unsafe",
        "codex-windows-powershell-exe": "powershell.exe -NoProfile -Command echo unsafe",
        "codex-windows-pwsh": "pwsh -NoProfile -Command echo unsafe",
        "codex-windows-relative-powershell": r".\powershell.exe -NoProfile -Command echo unsafe",
    }
    for name, command in unsafe_windows_commands.items():
        fixture = json.loads(json.dumps(documents))
        fixture["hooks/codex-hooks.json"]["hooks"]["SessionStart"][0]["hooks"][0][
            "commandWindows"
        ] = command
        fixtures.append((name, fixture, "must invoke only the approved packaged wrapper"))

    unbounded_timeout = json.loads(json.dumps(documents))
    unbounded_timeout["hooks/codex-hooks.json"]["hooks"]["SessionStart"][0]["hooks"][
        0
    ]["timeout"] = 600
    fixtures.append(
        ("codex-windows-unbounded-timeout", unbounded_timeout, "timeout must be exactly")
    )

    rejected = 0
    for name, fixture, expected in fixtures:
        fixture_failures: list[str] = []
        check_exact_hook_shapes(fixture, fixture_failures)
        check_codex_windows_hook_security(fixture, fixture_failures)
        if any(expected in failure for failure in fixture_failures):
            rejected += 1
        else:
            failures.append(f"hook lifecycle negative fixture {name!r} was accepted")

    positive_failures: list[str] = []
    check_exact_hook_shapes(documents, positive_failures)
    check_codex_windows_hook_security(documents, positive_failures)
    if positive_failures:
        failures.append(
            "checked-in hook lifecycle control failed: "
            + "; ".join(positive_failures)
        )
    return rejected + 1
