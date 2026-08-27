"""Canonical manifest schema mutation cases."""

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

    screenshots = json.loads(json.dumps(documents))
    screenshots[".codex-plugin/plugin.json"]["interface"]["screenshots"] = [
        "./assets/axiom-mark.svg"
    ]
    fixtures.append(("skills-only-screenshots", screenshots, "skills-only plugin"))

    logo_dark = json.loads(json.dumps(documents))
    logo_dark[".codex-plugin/plugin.json"]["interface"]["logoDark"] = (
        "./assets/axiom-mark.svg"
    )
    fixtures.append(("unowned-logo-dark", logo_dark, "logoDark"))

    insecure_url = json.loads(json.dumps(documents))
    insecure_url[".codex-plugin/plugin.json"]["interface"]["websiteURL"] = (
        "http://github.com/wheakerd/axiom"
    )
    fixtures.append(("insecure-url", insecure_url, "must use HTTPS"))

    credential_url = json.loads(json.dumps(documents))
    credential_url[".codex-plugin/plugin.json"]["interface"]["supportURL"] = (
        "https://user:secret@example.com/support"
    )
    fixtures.append(("credential-url", credential_url, "must not contain credentials"))

    long_url = json.loads(json.dumps(documents))
    long_url[".codex-plugin/plugin.json"]["interface"]["websiteURL"] = (
        "https://example.com/" + "a" * 1100
    )
    fixtures.append(("long-url", long_url, "at most 1024"))

    too_many_prompts = json.loads(json.dumps(documents))
    too_many_prompts[".codex-plugin/plugin.json"]["interface"]["defaultPrompt"].append(
        "Explain the result."
    )
    fixtures.append(("too-many-prompts", too_many_prompts, "at most 3 prompts"))

    duplicate_prompt = json.loads(json.dumps(documents))
    first_prompt = duplicate_prompt[".codex-plugin/plugin.json"]["interface"][
        "defaultPrompt"
    ][0]
    duplicate_prompt[".codex-plugin/plugin.json"]["interface"]["defaultPrompt"][1] = (
        first_prompt.replace("Audit", "\N{FULLWIDTH LATIN CAPITAL LETTER A}udit").replace(
            "this repository", "this  repository"
        )
    )
    fixtures.append(
        ("normalized-duplicate-prompt", duplicate_prompt, "unique after normalization")
    )

    multiline_prompt = json.loads(json.dumps(documents))
    multiline_prompt[".codex-plugin/plugin.json"]["interface"]["defaultPrompt"][0] = (
        "Audit the repository.\nReport findings only."
    )
    fixtures.append(("multiline-prompt", multiline_prompt, "one line"))

    long_prompt = json.loads(json.dumps(documents))
    long_prompt[".codex-plugin/plugin.json"]["interface"]["defaultPrompt"][0] = (
        "A" * 129
    )
    fixtures.append(("long-prompt", long_prompt, "at most 128"))

    app_mention = json.loads(json.dumps(documents))
    app_mention[".codex-plugin/plugin.json"]["interface"]["defaultPrompt"][0] = (
        "Ask @Axiom to audit this repository."
    )
    fixtures.append(("app-mention", app_mention, "app @mention"))

    long_short_description = json.loads(json.dumps(documents))
    long_short_description[".codex-plugin/plugin.json"]["interface"][
        "shortDescription"
    ] = "A" * 31
    fixtures.append(("long-short-description", long_short_description, "at most 30"))

    invalid_color = json.loads(json.dumps(documents))
    invalid_color[".codex-plugin/plugin.json"]["interface"]["brandColor"] = "navy"
    fixtures.append(("invalid-color", invalid_color, "six-digit hex color"))

    low_contrast = json.loads(json.dumps(documents))
    low_contrast[".codex-plugin/plugin.json"]["interface"]["brandColor"] = "#FFFFFF"
    fixtures.append(("low-contrast-color", low_contrast, "at least 2:1 contrast"))

    traversal_path = json.loads(json.dumps(documents))
    traversal_path[".codex-plugin/plugin.json"]["interface"]["logo"] = (
        "./assets/../README.md"
    )
    fixtures.append(("traversal-asset", traversal_path, "traversal segments"))

    missing_asset = json.loads(json.dumps(documents))
    missing_asset[".codex-plugin/plugin.json"]["interface"]["logo"] = (
        "./assets/missing.svg"
    )
    fixtures.append(("missing-asset", missing_asset, "existing regular file"))

    wrong_extension = json.loads(json.dumps(documents))
    wrong_extension[".codex-plugin/plugin.json"]["interface"]["logo"] = "./README.md"
    fixtures.append(("wrong-asset-extension", wrong_extension, "unsupported image extension"))

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
