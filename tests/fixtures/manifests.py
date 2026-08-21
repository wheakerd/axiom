"""Manifest schema mutation fixtures."""

from __future__ import annotations

import json
from typing import Any

from axiom_validation.manifests import MANIFEST_FILES, check_manifest_capability_schema


def check_manifest_schema_fixtures(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> int:
    rejected = 0
    required = {
        ".codex-plugin/plugin.json",
        ".agents/plugins/marketplace.json",
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
    }
    if not required.issubset(documents):
        failures.append("manifest schema fixtures require all four package documents")
        return 0
    fixtures: list[tuple[str, dict[str, dict[str, Any]], str]] = []

    mcp_servers = json.loads(json.dumps(documents))
    mcp_servers[".codex-plugin/plugin.json"]["mcpServers"] = {
        "unowned": {"command": "sh"}
    }
    fixtures.append(("mcpServers", mcp_servers, "mcpServers"))

    unknown_top = json.loads(json.dumps(documents))
    unknown_top[".claude-plugin/plugin.json"]["commands"] = ["./commands/"]
    fixtures.append(("unknown-top-level", unknown_top, "commands"))

    unknown_nested = json.loads(json.dumps(documents))
    unknown_nested[".codex-plugin/plugin.json"]["interface"]["network"] = True
    fixtures.append(("unknown-nested-interface", unknown_nested, "network"))

    unknown_source = json.loads(json.dumps(documents))
    unknown_source[".agents/plugins/marketplace.json"]["plugins"][0]["source"][
        "command"
    ] = "sh"
    fixtures.append(("unknown-nested-source", unknown_source, "command"))

    for name, fixture, expected in fixtures:
        fixture_failures: list[str] = []
        check_manifest_capability_schema(fixture, fixture_failures)
        if any(expected in failure for failure in fixture_failures):
            rejected += 1
        else:
            failures.append(f"manifest schema negative fixture {name!r} was accepted")

    positive_failures: list[str] = []
    check_manifest_capability_schema(documents, positive_failures)
    if positive_failures:
        failures.append(
            "checked-in manifest schema control failed: " + "; ".join(positive_failures)
        )
    return rejected + 1
