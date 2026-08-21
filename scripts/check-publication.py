#!/usr/bin/env python3
"""Validate Axiom's concrete publication invariants without network access."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from html import unescape
from pathlib import Path, PurePosixPath
from typing import Any, Iterator
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPOSITORY_ROOT / "README.md"
RELEASE_VERSION = "0.7.6"
CURRENT_RELEASE_NOTES = f"docs/releases/v{RELEASE_VERSION}.md"

REQUIRED_PUBLIC_FILES = tuple(dict.fromkeys((
    "README.md",
    "docs/getting-started.md",
    "docs/architecture.md",
    "docs/examples.md",
    "docs/trust-model.md",
    "docs/compatibility.md",
    "docs/field-validation.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "evidence/schema-v1.json",
    "evidence/release-status.json",
    "evidence/v0.7.4/codex/linux.json",
    "evidence/v0.7.4/claude-code/linux.json",
    "scripts/check-compatibility-evidence.py",
    "docs/releases/v0.3.0.md",
    "docs/releases/v0.3.1.md",
    "docs/releases/v0.4.0.md",
    "docs/releases/v0.4.1.md",
    "docs/releases/v0.4.2.md",
    "docs/releases/v0.5.0.md",
    "docs/releases/v0.5.1.md",
    "docs/releases/v0.6.0.md",
    "docs/releases/v0.6.1.md",
    "docs/releases/v0.7.0.md",
    "docs/releases/v0.7.1.md",
    "docs/releases/v0.7.2.md",
    "docs/releases/v0.7.3.md",
    "docs/releases/v0.7.4.md",
    "docs/releases/v0.7.5.md",
    CURRENT_RELEASE_NOTES,
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/pull_request_template.md",
)))

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
EXPECTED_PLUGIN_NAME = "axiom"
EXPECTED_DISPLAY_NAME = "Axiom"
EXPECTED_TAGLINE = "Think before AI thinks."
EXPECTED_CODEX_CATEGORY = "Productivity"
EXPECTED_CLAUDE_CATEGORY = "productivity"
EXPECTED_CODEX_POLICY = {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL",
}
CODEX_MANIFEST_KEYS = frozenset(
    {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "skills",
        "hooks",
        "interface",
    }
)
CODEX_INTERFACE_KEYS = frozenset(
    {
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "defaultPrompt",
        "brandColor",
    }
)
CLAUDE_MANIFEST_KEYS = frozenset(
    {
        "$schema",
        "name",
        "displayName",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "skills",
        "hooks",
    }
)
CODEX_MARKETPLACE_KEYS = frozenset({"name", "interface", "plugins"})
CODEX_MARKETPLACE_PLUGIN_KEYS = frozenset({"name", "source", "policy", "category"})
CLAUDE_MARKETPLACE_KEYS = frozenset({"name", "owner", "description", "plugins"})
CLAUDE_MARKETPLACE_PLUGIN_KEYS = frozenset({"name", "source", "category", "tags"})
AUTHOR_KEYS = frozenset({"name", "url"})
HOOK_FILES = (
    "hooks/codex-hooks.json",
    "hooks/claude-hooks.json",
)
EXPECTED_DIRECT_SKILLS = (
    "agents-architect",
    "confirm-external-action",
    "optimize-codex-usage",
    "reversible-system-change",
    "review-axiom-task",
    "traceable-git-submit",
    "using-axiom",
)
EXPECTED_README_SKILLS = (
    "using-axiom",
    "agents-architect",
    "optimize-codex-usage",
    "review-axiom-task",
    "confirm-external-action",
    "traceable-git-submit",
    "reversible-system-change",
)
INSTRUCTION_MAX_BYTES = 8192
STRICT_SEMVER = re.compile(
    r"(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
CODEX_DEFAULT_PROMPT_MAX_ITEMS = 3
CODEX_DEFAULT_PROMPT_MAX_CHARACTERS = 128
EFFECTIVE_INSTRUCTION_TOKENS = (
    "effective-instructions",
    "effective-instructions:preview",
    "effective-instructions:refactor",
    "effective-instructions:force",
    "effective-instructions:reconcile",
    "effective-instructions:reconcile-preview",
)
ROUTE_SOURCE_ANCHORS = {
    "agents-architect": ("AGENTS.md", "audit"),
    "confirm-external-action": ("external", "target", "verify"),
    "optimize-codex-usage": ("Codex", "credits", "context"),
    "review-axiom-task": ("routing", "authorization", "evidence"),
    "traceable-git-submit": ("checkpoint", "push"),
    "reversible-system-change": ("plan", "persistent", "rollback"),
}
README_LIFECYCLE_COMMANDS = (
    "codex plugin marketplace upgrade axiom",
    "/plugin marketplace update axiom",
    "/plugin update axiom@axiom",
    "/reload-plugins",
    "codex plugin remove axiom@axiom",
    "/plugin disable axiom@axiom",
    "/plugin uninstall axiom@axiom",
)

ROUTING_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "name": "readme-summary-no-match",
        "request": "Summarize this README without changing files.",
        "route": None,
        "phase": "normal",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "small-source-edit-no-match",
        "request": "Fix this parser typo and run its focused unit test.",
        "route": None,
        "phase": "normal",
        "references": (),
        "authorization": frozenset({"read", "edit", "test"}),
    },
    {
        "name": "ordinary-task-summary-no-match",
        "request": "Summarize what changed in this coding task.",
        "route": None,
        "phase": "normal",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "draft-only-external-no-match",
        "request": "Draft an email to Alex, but do not send it.",
        "route": None,
        "phase": "normal",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "effective-instructions-apply",
        "request": "effective-instructions",
        "route": "agents-architect",
        "phase": "effective-update",
        "references": (
            "references/runtime-and-updates.md",
            "references/maintenance/context-evidence.md",
            "references/maintenance/maintenance-application.md",
        ),
        "authorization": frozenset({"read", "edit", "test"}),
    },
    {
        "name": "effective-instructions-preview",
        "request": "effective-instructions:preview",
        "route": "agents-architect",
        "phase": "effective-preview",
        "references": (
            "references/runtime-and-updates.md",
            "references/maintenance/context-evidence.md",
        ),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "effective-instructions-refactor",
        "request": "effective-instructions:refactor",
        "route": "agents-architect",
        "phase": "effective-refactor",
        "references": (
            "references/runtime-and-updates.md",
            "references/routing-architecture.md",
        ),
        "authorization": frozenset({"read", "edit", "test"}),
    },
    {
        "name": "effective-instructions-force",
        "request": "effective-instructions:force Keep this durable rule.",
        "route": "agents-architect",
        "phase": "effective-force",
        "references": (
            "references/runtime-and-updates.md",
            "references/maintenance/maintenance-application.md",
        ),
        "authorization": frozenset({"read", "edit", "test"}),
    },
    {
        "name": "effective-instructions-reconcile",
        "request": "effective-instructions:reconcile",
        "route": "agents-architect",
        "phase": "implementation-reconciliation",
        "references": (
            "references/maintenance/implementation-reconciliation.md",
        ),
        "authorization": frozenset({"read", "edit", "test"}),
    },
    {
        "name": "effective-instructions-reconcile-preview",
        "request": "effective-instructions:reconcile-preview",
        "route": "agents-architect",
        "phase": "implementation-reconciliation-preview",
        "references": (
            "references/maintenance/implementation-reconciliation.md",
        ),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "agents-audit",
        "request": "Audit this repository's AGENTS.md instruction discovery and report findings only.",
        "route": "agents-architect",
        "phase": "audit",
        "references": ("references/inventory-audit.md",),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "local-checkpoint",
        "request": "Create a local checkpoint commit for these paths and do not push.",
        "route": "traceable-git-submit",
        "phase": "checkpoint",
        "references": (
            "references/safe-git-values-and-metadata.md",
            "references/baseline-and-preflight.md",
            "references/checkpoint-provenance.md",
            "references/checkpoint-execution.md",
        ),
        "authorization": frozenset({"read", "metadata-write", "commit"}),
    },
    {
        "name": "direct-push",
        "request": "Push the current Git branch without rewriting history.",
        "route": "traceable-git-submit",
        "phase": "direct-submit",
        "references": (
            "references/safe-git-values-and-metadata.md",
            "references/repository-and-remote-targets.md",
        ),
        "authorization": frozenset({"read", "network-push"}),
    },
    {
        "name": "exact-external-send",
        "request": "Send this approved email to alex@example.com once, then verify the external service status.",
        "route": "confirm-external-action",
        "phase": "execute-verify",
        "references": (),
        "authorization": frozenset({"read", "external-write"}),
    },
    {
        "name": "ambiguous-external-publish",
        "request": "Publish this announcement somewhere.",
        "route": "confirm-external-action",
        "phase": "authorize",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "migration-plan",
        "request": "Prepare a read-only plan for this persistent database migration.",
        "route": "reversible-system-change",
        "phase": "plan",
        "references": ("references/preflight-and-rollback.md",),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "non-mutating-migration-rehearsal",
        "request": "Rehearse this database migration without changing any state.",
        "route": "reversible-system-change",
        "phase": "rehearsal-read-only",
        "references": ("references/preflight-and-rollback.md",),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "upgrade-dry-run",
        "request": "Run a dry run of this upgrade.",
        "route": "reversible-system-change",
        "phase": "rehearsal-read-only",
        "references": ("references/preflight-and-rollback.md",),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "ambiguous-deployment-rehearsal",
        "request": "Rehearse this deployment.",
        "route": "clarify",
        "phase": "rehearsal-type",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "isolated-restore-rehearsal",
        "request": (
            "Run this explicitly authorized isolated restore rehearsal without "
            "promotion."
        ),
        "route": "reversible-system-change",
        "phase": "isolated-restore-rehearsal",
        "references": ("references/preflight-and-rollback.md",),
        "authorization": frozenset({"read", "restore-rehearsal-write"}),
    },
    {
        "name": "migration-execution",
        "request": "Execute this authorized persistent database migration with verified rollback.",
        "route": "reversible-system-change",
        "phase": "execute",
        "references": (
            "references/preflight-and-rollback.md",
            "references/execution-and-verification.md",
        ),
        "authorization": frozenset({"read", "persistent-write"}),
    },
    {
        "name": "deploy-and-external-publish-cross-route",
        "request": "Deploy this release to the external service and publish the deployment.",
        "route": (
            "confirm-external-action",
            "reversible-system-change",
        ),
        "phase": "cross-route-ownership",
        "references": (),
        "authorization": frozenset({"read"}),
        "authorization_gates": (
            "confirm-external-action",
            "reversible-system-change",
        ),
    },
    {
        "name": "retention-deletion-cross-route",
        "request": "Execute the authorized retention deletion of remote backups from this external service account.",
        "route": (
            "confirm-external-action",
            "reversible-system-change",
        ),
        "phase": "cross-route-ownership",
        "references": (),
        "authorization": frozenset({"read"}),
        "authorization_gates": (
            "confirm-external-action",
            "reversible-system-change",
        ),
    },
    {
        "name": "explicit-usage-optimization",
        "request": "Reduce the Codex credits and context used by these Skills without weakening validation.",
        "route": "optimize-codex-usage",
        "phase": "audit-implementation",
        "references": ("references/context-audit.md",),
        "authorization": frozenset({"read", "edit", "test"}),
    },
    {
        "name": "explicit-axiom-task-review",
        "request": "Explain the routing, authorization, actions, and evidence for this Axiom-guided task.",
        "route": "review-axiom-task",
        "phase": "review",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "show-what-axiom-did",
        "request": "Show me what Axiom did during this task.",
        "route": "review-axiom-task",
        "phase": "review",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "retrospective-git-review",
        "request": "Audit why Axiom selected traceable-git-submit and what it authorized for this completed task.",
        "route": "review-axiom-task",
        "phase": "review",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "unambiguous-non-english-task-review",
        "request": "审阅当前 Axiom 任务的路由、授权、操作和证据。",
        "route": "review-axiom-task",
        "phase": "review",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "material-multi-route-ambiguity",
        "request": "Reduce Codex usage by either rewriting AGENTS.md or changing deployment defaults; choose one.",
        "route": "clarify",
        "phase": "route-choice",
        "references": (),
        "authorization": frozenset({"read"}),
    },
    {
        "name": "unambiguous-non-english-plan",
        "request": "只制定持久化数据库迁移计划，不要执行。",
        "route": "reversible-system-change",
        "phase": "plan",
        "references": ("references/preflight-and-rollback.md",),
        "authorization": frozenset({"read"}),
    },
)
ROLLBACK_EVIDENCE_FIELDS = (
    "prior_state_bound",
    "location_unambiguous",
    "restore_principal_readable",
    "restore_prerequisites_present",
    "complete_effect_coverage",
    "current_restore_validation",
    "rollback_authorized",
    "post_restore_checks_defined",
    "evidence_fresh",
)
EXTERNAL_ACTION_ENVELOPE_FIELDS = (
    "actor_bound",
    "action_bound",
    "target_bound",
    "payload_bound",
    "disclosure_bound",
    "cost_bound",
    "count_bound",
    "retry_bound",
    "current_user_authority",
    "envelope_unchanged",
    "host_approval_satisfied",
)
CLEANUP_AUTHORITY_FIELDS = (
    "exact_authority",
    "repo_match",
    "workflow_match",
    "backup_ref_match",
    "old_head_match",
    "new_commit_match",
    "targets_match",
    "operations_bound",
    "verification_current",
    "metadata_safe",
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


class CanonicalYamlError(ValueError):
    """Raised when a protected YAML file leaves Axiom's strict tiny schema."""


def parse_agent_metadata_document(
    text: str,
    label: str,
    *,
    allow_policy: bool,
) -> dict[str, dict[str, Any]]:
    """Consume agents/openai.yaml through its exact canonical tiny schema."""
    quoted = r'"[^\r\n]*"'
    pattern = re.compile(
        rf"interface:\n"
        rf"  display_name: (?P<display_name>{quoted})\n"
        rf"  short_description: (?P<short_description>{quoted})\n"
        rf"  default_prompt: (?P<default_prompt>{quoted})"
        rf"(?P<policy>\npolicy:\n  allow_implicit_invocation: false)?\n?"
    )
    match = pattern.fullmatch(text)
    policy_present = match is not None and match.group("policy") is not None
    if match is None or policy_present != allow_policy:
        raise CanonicalYamlError(
            f"{label} must match the complete canonical interface"
            + (" plus non-implicit policy schema" if allow_policy else " schema with no tail")
        )
    try:
        interface = {
            field: json.loads(match.group(field))
            for field in ("display_name", "short_description", "default_prompt")
        }
    except json.JSONDecodeError as error:
        raise CanonicalYamlError(f"{label} has an invalid quoted string: {error.msg}") from error
    result: dict[str, dict[str, Any]] = {"interface": interface}
    if allow_policy:
        result["policy"] = {"allow_implicit_invocation": False}
    return result


def parse_skill_frontmatter_document(text: str, label: str) -> dict[str, str]:
    """Parse the complete frontmatter document and reject non-schema content."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise CanonicalYamlError(f"{label} must start with an exact YAML delimiter")
    try:
        closing_index = lines.index("---", 1)
    except ValueError as error:
        raise CanonicalYamlError(f"{label} has no closing YAML delimiter") from error
    if closing_index == 1:
        raise CanonicalYamlError(f"{label} frontmatter is empty")
    if not any(line.strip() for line in lines[closing_index + 1 :]):
        raise CanonicalYamlError(f"{label} must contain a Markdown body after frontmatter")

    expected = ("name", "description")
    implicit_non_strings = {
        "y",
        "yes",
        "n",
        "no",
        "true",
        "false",
        "on",
        "off",
        "null",
        "~",
    }
    fields: dict[str, str] = {}
    order: list[str] = []
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        match = re.fullmatch(r"([a-z_]+): (.+)", line)
        if match is None or line != line.rstrip() or "\t" in line:
            raise CanonicalYamlError(
                f"{label}:{line_number} frontmatter must use one canonical key and scalar"
            )
        key, raw_value = match.groups()
        if key in fields:
            raise CanonicalYamlError(f"{label}:{line_number} duplicate field {key!r}")
        if key not in expected:
            raise CanonicalYamlError(f"{label}:{line_number} unknown field {key!r}")
        if (
            raw_value != raw_value.strip()
            or raw_value.casefold() in implicit_non_strings
            or re.fullmatch(r"[A-Za-z][\x20-\x7e]*", raw_value) is None
            or " #" in raw_value
            or ": " in raw_value
            or raw_value.endswith(":")
        ):
            raise CanonicalYamlError(
                f"{label}:{line_number} {key!r} must be a canonical plain string"
            )
        fields[key] = raw_value
        order.append(key)
    if tuple(order) != expected:
        raise CanonicalYamlError(f"{label} frontmatter must contain only name then description")
    return fields


def route_contract(request: str) -> dict[str, Any]:
    """Evaluate the offline route model after its source contracts are checked."""
    normalized = request.lower()
    if "只制定持久化数据库迁移计划" in request and "不要执行" in request:
        normalized = "prepare a read-only plan for a persistent database migration"
    if "审阅当前 Axiom 任务的路由、授权、操作和证据" in request:
        normalized = "review the routing authorization actions and evidence for this axiom task"

    effective_contracts = {
        "effective-instructions": {
            "route": "agents-architect",
            "phase": "effective-update",
            "references": (
                "references/runtime-and-updates.md",
                "references/maintenance/context-evidence.md",
                "references/maintenance/maintenance-application.md",
            ),
            "authorization": frozenset({"read", "edit", "test"}),
        },
        "effective-instructions:preview": {
            "route": "agents-architect",
            "phase": "effective-preview",
            "references": (
                "references/runtime-and-updates.md",
                "references/maintenance/context-evidence.md",
            ),
            "authorization": frozenset({"read"}),
        },
        "effective-instructions:refactor": {
            "route": "agents-architect",
            "phase": "effective-refactor",
            "references": (
                "references/runtime-and-updates.md",
                "references/routing-architecture.md",
            ),
            "authorization": frozenset({"read", "edit", "test"}),
        },
        "effective-instructions:reconcile": {
            "route": "agents-architect",
            "phase": "implementation-reconciliation",
            "references": (
                "references/maintenance/implementation-reconciliation.md",
            ),
            "authorization": frozenset({"read", "edit", "test"}),
        },
        "effective-instructions:reconcile-preview": {
            "route": "agents-architect",
            "phase": "implementation-reconciliation-preview",
            "references": (
                "references/maintenance/implementation-reconciliation.md",
            ),
            "authorization": frozenset({"read"}),
        },
    }
    effective_request = normalized.strip()
    if effective_request in effective_contracts:
        return effective_contracts[effective_request]
    if re.fullmatch(r"effective-instructions:force\s+\S(?:.*\S)?", effective_request):
        return {
            "route": "agents-architect",
            "phase": "effective-force",
            "references": (
                "references/runtime-and-updates.md",
                "references/maintenance/maintenance-application.md",
            ),
            "authorization": frozenset({"read", "edit", "test"}),
        }

    review = bool(
        "axiom" in normalized
        and re.search(r"\b(?:review|explain|audit|show)\b", normalized)
        and re.search(
            r"\b(?:task|route|routing|authorization|authority|actions?|evidence|outcome)\b",
            normalized,
        )
    )
    usage = bool(
        re.search(r"\bcodex\b.*\b(?:credits?|tokens?|context|usage)\b", normalized)
        or re.search(r"\b(?:skills?|agents\.md|mcp)\b.*\bcontext\b", normalized)
    )
    agents = bool(
        re.search(r"(?:agents\.md|\.agents)", normalized)
        and re.search(r"\b(?:audit|design|initialize|split|rewrit|migrat|maintain|validat)\w*\b", normalized)
    )
    git = bool(
        re.search(r"\b(?:checkpoint|baseline metadata|consolidat\w*|one-final|recover\w*)\b", normalized)
        or re.search(r"\b(?:submit|publish|push)\b.*\b(?:git|branch|changes?|history)\b", normalized)
        or re.search(r"\b(?:git|branch)\b.*\b(?:submit|publish|push)\b", normalized)
    )
    persistent = bool(
        (
            re.search(
                r"\b(?:install|upgrade|deploy|deployment|migrat\w*|retention|promot\w*)\b",
                normalized,
            )
            and re.search(
                r"\b(?:persistent|database|system|service|authorized|approved|production|staged|release|read-only|plan|execute|rehears\w*|dry[ -]run|simulation)\b",
                normalized,
            )
        )
        or "isolated restore rehearsal" in normalized
    )
    external_effect_prohibited = bool(
        re.search(
            r"\b(?:do not|don't|without)\s+(?:send|publish|post|invite|purchase|buy|trade|delet\w*|cancel|change)\b",
            normalized,
        )
    )
    external_action = bool(
        re.search(
            r"\b(?:send|publish|post|invite|purchase|buy|trade|delet\w*|cancel|change)\b",
            normalized,
        )
        and re.search(
            r"\b(?:email|message|announcement|post|invitation|invite|order|trade|purchase|account|membership|subscription|recipient|external (?:app|service)|remote deployment|deployment)\b",
            normalized,
        )
        and not external_effect_prohibited
    )

    if review:
        return {
            "route": "review-axiom-task",
            "phase": "review",
            "references": (),
            "authorization": frozenset({"read"}),
        }

    if usage and (agents or persistent) and re.search(r"\b(?:either|choose one)\b", normalized):
        return {
            "route": "clarify",
            "phase": "route-choice",
            "references": (),
            "authorization": frozenset({"read"}),
        }

    if usage:
        return {
            "route": "optimize-codex-usage",
            "phase": "audit-implementation",
            "references": ("references/context-audit.md",),
            "authorization": frozenset({"read", "edit", "test"}),
        }

    if agents:
        return {
            "route": "agents-architect",
            "phase": "audit",
            "references": ("references/inventory-audit.md",),
            "authorization": frozenset({"read"}),
        }

    if persistent and external_action:
        return {
            "route": (
                "confirm-external-action",
                "reversible-system-change",
            ),
            "phase": "cross-route-ownership",
            "references": (),
            "authorization": frozenset({"read"}),
            "authorization_gates": (
                "confirm-external-action",
                "reversible-system-change",
            ),
        }

    if git:
        if "checkpoint" in normalized:
            return {
                "route": "traceable-git-submit",
                "phase": "checkpoint",
                "references": (
                    "references/safe-git-values-and-metadata.md",
                    "references/baseline-and-preflight.md",
                    "references/checkpoint-provenance.md",
                    "references/checkpoint-execution.md",
                ),
                "authorization": frozenset({"read", "metadata-write", "commit"}),
            }
        return {
            "route": "traceable-git-submit",
            "phase": "direct-submit",
            "references": (
                "references/safe-git-values-and-metadata.md",
                "references/repository-and-remote-targets.md",
            ),
            "authorization": frozenset({"read", "network-push"}),
        }

    if persistent:
        isolated_restore_rehearsal = "isolated restore rehearsal" in normalized
        rehearsal_requested = bool(
            re.search(r"\b(?:rehears\w*|dry[ -]run|simulation)\b", normalized)
        )
        non_mutating_rehearsal = bool(
            rehearsal_requested
            and re.search(
                r"\b(?:non-mutating|read-only|without changing|do not change|dry[ -]run|simulation)\b",
                normalized,
            )
        )
        if isolated_restore_rehearsal:
            return {
                "route": "reversible-system-change",
                "phase": "isolated-restore-rehearsal",
                "references": ("references/preflight-and-rollback.md",),
                "authorization": frozenset({"read", "restore-rehearsal-write"}),
            }
        if rehearsal_requested and not non_mutating_rehearsal:
            return {
                "route": "clarify",
                "phase": "rehearsal-type",
                "references": (),
                "authorization": frozenset({"read"}),
            }
        plan_only = bool(re.search(r"\b(?:read-only|plan)\b", normalized)) and "execute" not in normalized
        return {
            "route": "reversible-system-change",
            "phase": (
                "rehearsal-read-only"
                if non_mutating_rehearsal
                else "plan" if plan_only else "execute"
            ),
            "references": (
                ("references/preflight-and-rollback.md",)
                if plan_only or non_mutating_rehearsal
                else (
                    "references/preflight-and-rollback.md",
                    "references/execution-and-verification.md",
                )
            ),
            "authorization": (
                frozenset({"read"})
                if plan_only or non_mutating_rehearsal
                else frozenset({"read", "persistent-write"})
            ),
        }

    if external_action:
        ambiguous = bool(
            re.search(r"\b(?:somewhere|someone|somebody|anywhere|whichever|whatever)\b", normalized)
        )
        return {
            "route": "confirm-external-action",
            "phase": "authorize" if ambiguous else "execute-verify",
            "references": (),
            "authorization": (
                frozenset({"read"})
                if ambiguous
                else frozenset({"read", "external-write"})
            ),
        }

    authorization = {"read"}
    if re.search(r"\b(?:fix|edit|change)\b", normalized):
        authorization.add("edit")
    if "test" in normalized:
        authorization.add("test")
    return {
        "route": None,
        "phase": "normal",
        "references": (),
        "authorization": frozenset(authorization),
    }


def has_exact_route_token(text: str, token: str) -> bool:
    return bool(
        re.search(
            rf"(?<![a-z0-9:-]){re.escape(token)}(?![a-z0-9:-])",
            text.lower(),
        )
    )


def check_routing_source_contracts(failures: list[str]) -> None:
    front_door_path = REPOSITORY_ROOT / "skills" / "using-axiom" / "SKILL.md"
    front_door = front_door_path.read_text(encoding="utf-8")
    route_section = front_door.split("## Bundled Routes", 1)[-1].split("\n## ", 1)[0]

    route_entries: dict[str, str] = {}
    for route in ROUTE_SOURCE_ANCHORS:
        match = re.search(
            rf"^- `{re.escape(route)}`:(.*?)(?=^- `[a-z0-9-]+`:\s|\Z)",
            route_section,
            re.MULTILINE | re.DOTALL,
        )
        if match is None:
            failures.append(
                f"{display_path(front_door_path)} has no parseable source contract for {route!r}"
            )
            continue
        route_entries[route] = match.group(1)

        skill_path = REPOSITORY_ROOT / "skills" / route / "SKILL.md"
        fields = parse_skill_frontmatter(skill_path, failures)
        if fields is None:
            continue
        surfaces = {
            f"{display_path(front_door_path)} route entry": match.group(1),
            f"{display_path(skill_path)} description": fields["description"],
        }
        for label, surface in surfaces.items():
            for anchor in ROUTE_SOURCE_ANCHORS[route]:
                if anchor.casefold() not in surface.casefold():
                    failures.append(
                        f"{label} for {route!r} is missing selection anchor {anchor!r}"
                    )

    agents_entry = route_entries.get("agents-architect")
    agents_path = REPOSITORY_ROOT / "skills" / "agents-architect" / "SKILL.md"
    agents_fields = parse_skill_frontmatter(agents_path, failures)
    if agents_entry is None or agents_fields is None:
        return
    for label, surface in (
        (f"{display_path(front_door_path)} agents-architect route entry", agents_entry),
        (f"{display_path(agents_path)} description", agents_fields["description"]),
    ):
        for token in EFFECTIVE_INSTRUCTION_TOKENS:
            if not has_exact_route_token(surface, token):
                failures.append(
                    f"{label} is missing canonical trigger token {token!r}"
                )


def require_ordered_contract_anchors(
    path: Path,
    anchors: tuple[str, ...],
    failures: list[str],
    contract_name: str,
) -> None:
    """Bind an offline semantic contract to ordered phrases in its owner."""
    text = " ".join(path.read_text(encoding="utf-8").split()).casefold()
    cursor = 0
    for anchor in anchors:
        index = text.find(" ".join(anchor.split()).casefold(), cursor)
        if index < 0:
            failures.append(
                f"{display_path(path)} is missing or reorders {contract_name} anchor {anchor!r}"
            )
            return
        cursor = index + len(anchor)


def check_cross_route_resume_contracts(failures: list[str]) -> int:
    """Lock dual-route authority and fail-closed resume to their source owners."""
    skills = REPOSITORY_ROOT / "skills"
    contracts = (
        (
            skills / "agents-architect/references/maintenance/authorization-and-safety.md",
            "provenance authorization",
            (
                "Clear Axiom provenance may establish ownership, routing, and preview handling only.",
                "A read-only assessment, option request, preview, or approval of a preview authorizes zero writes regardless of provenance.",
            ),
        ),
        (
            skills / "using-axiom/SKILL.md",
            "cross-route and resume",
            (
                "Resolve cross-route ownership from this table before inspecting either candidate body.",
                "confirm-external-action",
                "reversible-system-change",
                "authorization under either route never satisfies the other.",
                "On resume or compaction, reselect every still-active route from current direct evidence before any new mutation.",
                "If route or phase cannot be reconstructed, perform zero new mutations",
            ),
        ),
        (
            skills / "confirm-external-action/SKILL.md",
            "external-action resume",
            (
                "## Resume And Compaction Handoff",
                "host-native task context and current direct evidence from the owning system",
                "perform zero new mutations",
                "An unknown external outcome enters Verify only",
                "never resend",
                "Do not add a daemon, cache, telemetry, or persistent handoff tool",
            ),
        ),
        (
            skills / "reversible-system-change/SKILL.md",
            "reversible-change resume",
            (
                "## Resume And Compaction Handoff",
                "host-native task context and current direct evidence from the owning system",
                "perform zero new mutations",
                "Never adopt post-change state as the prior rollback baseline.",
                "An unknown external outcome enters Verify only and must not be resent.",
                "Do not add a daemon, cache, telemetry, or persistent handoff tool",
            ),
        ),
    )
    for path, name, anchors in contracts:
        require_ordered_contract_anchors(path, anchors, failures, name)
    return len(contracts)


def check_readme_lifecycle_commands(failures: list[str]) -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    for command in README_LIFECYCLE_COMMANDS:
        if command not in readme:
            failures.append(
                f"README lifecycle documentation is missing exact command {command!r}"
            )


def check_routing_scenarios(failures: list[str]) -> None:
    for scenario in ROUTING_SCENARIOS:
        actual = route_contract(scenario["request"])
        contract_fields = tuple(
            field for field in scenario if field not in {"name", "request"}
        )
        for field in contract_fields:
            if actual[field] != scenario[field]:
                failures.append(
                    f"routing scenario {scenario['name']!r} {field} is "
                    f"{actual[field]!r}; expected {scenario[field]!r}"
                )

        route_value = actual["route"]
        if route_value in (None, "clarify"):
            continue
        routes = route_value if isinstance(route_value, tuple) else (route_value,)
        for route in routes:
            main_path = REPOSITORY_ROOT / "skills" / route / "SKILL.md"
            try:
                main_text = main_path.read_text(encoding="utf-8")
            except OSError as error:
                failures.append(
                    f"routing scenario {scenario['name']!r} cannot read "
                    f"{display_path(main_path)}: {error}"
                )
                continue
            for reference in actual["references"]:
                if reference not in main_text:
                    failures.append(
                        f"routing scenario {scenario['name']!r} loads undeclared reference "
                        f"{reference!r} from {display_path(main_path)}"
                    )


@dataclass(frozen=True)
class CanonicalYamlScalar:
    """A scalar from Axiom's dependency-free canonical YAML subset."""

    value: str
    comment: str
    line: int


@dataclass(frozen=True)
class CanonicalYamlLine:
    indent: int
    content: str
    line: int


@dataclass(frozen=True)
class ActionUse:
    declaration: str
    comment: str
    line: int
    scope: str


def split_yaml_comment(raw: str) -> tuple[str, str]:
    """Split a YAML scalar from an unquoted inline comment."""
    single_quoted = False
    double_quoted = False
    escaped = False
    for index, character in enumerate(raw):
        if double_quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                double_quoted = False
            continue
        if single_quoted:
            if character == "'":
                if index + 1 < len(raw) and raw[index + 1] == "'":
                    continue
                single_quoted = False
            continue
        if character == '"':
            double_quoted = True
        elif character == "'":
            single_quoted = True
        elif character == "#" and (index == 0 or raw[index - 1].isspace()):
            return raw[:index].rstrip(), raw[index + 1 :].strip()
    return raw.rstrip(), ""


def canonical_yaml_lines(text: str, label: str) -> list[CanonicalYamlLine]:
    """Tokenize canonical block YAML while treating scalar bodies as opaque."""
    if "\r" in text:
        raise CanonicalYamlError(f"{label} must use LF line endings")

    tokens: list[CanonicalYamlLine] = []
    block_parent_indent: int | None = None
    block_header = re.compile(
        r"(?:-\s+)?[A-Za-z_][A-Za-z0-9_-]*:\s*[>|][+-]?[0-9]*$"
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        leading = raw_line[: len(raw_line) - len(raw_line.lstrip(" \t"))]
        indent = len(leading)
        if block_parent_indent is not None:
            if not raw_line.strip() or indent > block_parent_indent:
                continue
            block_parent_indent = None

        if not raw_line.strip() or raw_line.lstrip(" ").startswith("#"):
            continue
        if "\t" in raw_line:
            raise CanonicalYamlError(
                f"{label}:{line_number} canonical YAML must not contain tabs"
            )
        if raw_line != raw_line.rstrip(" "):
            raise CanonicalYamlError(
                f"{label}:{line_number} canonical YAML must not contain trailing spaces"
            )
        if indent % 2:
            raise CanonicalYamlError(
                f"{label}:{line_number} canonical YAML indentation must use two-space levels"
            )

        content = raw_line[indent:]
        uncommented, _ = split_yaml_comment(content)
        if uncommented in {"---", "..."}:
            raise CanonicalYamlError(
                f"{label}:{line_number} multiple YAML documents are not allowed"
            )
        tokens.append(CanonicalYamlLine(indent, content, line_number))
        if block_header.fullmatch(uncommented):
            block_parent_indent = indent
    return tokens


class CanonicalYamlParser:
    """Parse the canonical block subset used by workflows and action metadata."""

    def __init__(self, text: str, label: str) -> None:
        self.label = label
        self.tokens = canonical_yaml_lines(text, label)

    def parse(self) -> dict[str, Any]:
        if not self.tokens:
            raise CanonicalYamlError(f"{self.label} is empty")
        if self.tokens[0].indent != 0 or self.tokens[0].content.startswith("-"):
            raise CanonicalYamlError(
                f"{self.label}:{self.tokens[0].line} must start with a top-level mapping"
            )
        value, index = self.parse_mapping(0, 0)
        if index != len(self.tokens):
            token = self.tokens[index]
            raise CanonicalYamlError(
                f"{self.label}:{token.line} has an unexpected YAML structure"
            )
        return value

    def parse_mapping(self, index: int, indent: int) -> tuple[dict[str, Any], int]:
        mapping: dict[str, Any] = {}
        while index < len(self.tokens):
            token = self.tokens[index]
            if token.indent < indent:
                break
            if token.indent > indent:
                raise CanonicalYamlError(
                    f"{self.label}:{token.line} has an unexpected indentation level"
                )
            if token.content.startswith("-"):
                break
            index = self.parse_mapping_entry(
                mapping,
                token.content,
                token.line,
                indent,
                index + 1,
            )
        return mapping, index

    def parse_mapping_entry(
        self,
        mapping: dict[str, Any],
        content: str,
        line: int,
        indent: int,
        next_index: int,
    ) -> int:
        uncommented, comment = split_yaml_comment(content)
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):(?: (.*))?", uncommented)
        if match is None:
            raise CanonicalYamlError(
                f"{self.label}:{line} must use an unquoted canonical mapping key"
            )
        key, raw_value = match.groups()
        if key in mapping:
            raise CanonicalYamlError(
                f"{self.label}:{line} contains duplicate mapping key {key!r}"
            )
        if raw_value is not None:
            mapping[key] = self.parse_scalar(raw_value, comment, line)
            return next_index

        if next_index < len(self.tokens) and self.tokens[next_index].indent > indent:
            child = self.tokens[next_index]
            if child.indent != indent + 2:
                raise CanonicalYamlError(
                    f"{self.label}:{child.line} nested content must advance one indentation level"
                )
            if child.content.startswith("-"):
                mapping[key], next_index = self.parse_sequence(next_index, indent + 2)
            else:
                mapping[key], next_index = self.parse_mapping(next_index, indent + 2)
        else:
            mapping[key] = CanonicalYamlScalar("", comment, line)
        return next_index

    def parse_sequence(self, index: int, indent: int) -> tuple[list[Any], int]:
        sequence: list[Any] = []
        while index < len(self.tokens):
            token = self.tokens[index]
            if token.indent < indent:
                break
            if token.indent > indent:
                raise CanonicalYamlError(
                    f"{self.label}:{token.line} has an unexpected sequence indentation"
                )
            if token.content == "-":
                next_index = index + 1
                if next_index >= len(self.tokens) or self.tokens[next_index].indent != indent + 2:
                    raise CanonicalYamlError(
                        f"{self.label}:{token.line} empty sequence entry has no child"
                    )
                child = self.tokens[next_index]
                if child.content.startswith("-"):
                    value, index = self.parse_sequence(next_index, indent + 2)
                else:
                    value, index = self.parse_mapping(next_index, indent + 2)
                sequence.append(value)
                continue
            if not token.content.startswith("- "):
                break

            remainder = token.content[2:]
            uncommented, _ = split_yaml_comment(remainder)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*:(?: .*)?", uncommented):
                item: dict[str, Any] = {}
                index = self.parse_mapping_entry(
                    item,
                    remainder,
                    token.line,
                    indent + 2,
                    index + 1,
                )
                while index < len(self.tokens):
                    continuation = self.tokens[index]
                    if continuation.indent != indent + 2 or continuation.content.startswith("-"):
                        break
                    index = self.parse_mapping_entry(
                        item,
                        continuation.content,
                        continuation.line,
                        indent + 2,
                        index + 1,
                    )
                sequence.append(item)
                continue

            raw_scalar, comment = split_yaml_comment(remainder)
            sequence.append(self.parse_scalar(raw_scalar, comment, token.line))
            index += 1
            if index < len(self.tokens) and self.tokens[index].indent > indent:
                child = self.tokens[index]
                raise CanonicalYamlError(
                    f"{self.label}:{child.line} scalar sequence entry cannot own nested content"
                )
        return sequence, index

    def parse_scalar(self, raw: str, comment: str, line: int) -> CanonicalYamlScalar:
        if not raw or raw != raw.strip():
            raise CanonicalYamlError(
                f"{self.label}:{line} scalar must use canonical spacing"
            )
        if raw[0] in "&*!{[" or raw.startswith("<<:"):
            raise CanonicalYamlError(
                f"{self.label}:{line} aliases, tags, and flow collections are not allowed"
            )
        if raw.startswith('"') or raw.endswith('"'):
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as error:
                raise CanonicalYamlError(
                    f"{self.label}:{line} has an invalid double-quoted scalar"
                ) from error
            if not isinstance(value, str):
                raise CanonicalYamlError(
                    f"{self.label}:{line} quoted scalar must decode to a string"
                )
        elif raw.startswith("'") or raw.endswith("'"):
            if len(raw) < 2 or not raw.startswith("'") or not raw.endswith("'"):
                raise CanonicalYamlError(
                    f"{self.label}:{line} has an invalid single-quoted scalar"
                )
            value = raw[1:-1].replace("''", "'")
        else:
            if ": " in raw:
                raise CanonicalYamlError(
                    f"{self.label}:{line} ambiguous plain scalar must be quoted"
                )
            value = raw
        return CanonicalYamlScalar(value, comment, line)


def parse_canonical_yaml_document(text: str, label: str) -> dict[str, Any]:
    return CanonicalYamlParser(text, label).parse()


def walk_yaml_uses(
    value: Any,
    path: tuple[str | int, ...] = (),
) -> Iterator[tuple[tuple[str | int, ...], Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = (*path, key)
            if key == "uses":
                yield child_path, child
            yield from walk_yaml_uses(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_yaml_uses(child, (*path, index))


def workflow_uses_declarations(
    document: dict[str, Any],
    label: str,
    failures: list[str],
) -> list[ActionUse]:
    declarations: list[ActionUse] = []
    allowed_paths: set[tuple[str | int, ...]] = set()
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        failures.append(f"{label} must contain a jobs mapping")
        return declarations

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            failures.append(f"{label} jobs.{job_name} must be a mapping")
            continue
        if "uses" in job:
            path = ("jobs", job_name, "uses")
            allowed_paths.add(path)
            scalar = job["uses"]
            if not isinstance(scalar, CanonicalYamlScalar) or not scalar.value:
                failures.append(f"{label} jobs.{job_name}.uses must be a non-empty scalar")
            else:
                declarations.append(
                    ActionUse(scalar.value, scalar.comment, scalar.line, "workflow-job")
                )
        steps = job.get("steps")
        if steps is None:
            continue
        if not isinstance(steps, list):
            failures.append(f"{label} jobs.{job_name}.steps must be a sequence")
            continue
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                failures.append(f"{label} jobs.{job_name}.steps[{index}] must be a mapping")
                continue
            if "uses" not in step:
                continue
            path = ("jobs", job_name, "steps", index, "uses")
            allowed_paths.add(path)
            scalar = step["uses"]
            if not isinstance(scalar, CanonicalYamlScalar) or not scalar.value:
                failures.append(
                    f"{label} jobs.{job_name}.steps[{index}].uses must be a non-empty scalar"
                )
            else:
                declarations.append(
                    ActionUse(scalar.value, scalar.comment, scalar.line, "workflow-step")
                )

    for path, scalar in walk_yaml_uses(document):
        if path not in allowed_paths:
            line = scalar.line if isinstance(scalar, CanonicalYamlScalar) else "?"
            failures.append(
                f"{label}:{line} uses is outside jobs.<job>.uses or jobs.<job>.steps[*].uses"
            )
    return declarations


def workflow_container_declarations(
    document: dict[str, Any],
    label: str,
    failures: list[str],
) -> list[ActionUse]:
    declarations: list[ActionUse] = []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return declarations

    def append_image(value: Any, image_label: str) -> None:
        if not isinstance(value, CanonicalYamlScalar) or not value.value:
            failures.append(f"{label} {image_label} must be a non-empty scalar")
            return
        declarations.append(
            ActionUse(value.value, value.comment, value.line, "workflow-container")
        )

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        container = job.get("container")
        if container is not None:
            if isinstance(container, CanonicalYamlScalar):
                append_image(container, f"jobs.{job_name}.container")
            elif isinstance(container, dict):
                append_image(
                    container.get("image"), f"jobs.{job_name}.container.image"
                )
            else:
                failures.append(
                    f"{label} jobs.{job_name}.container must be an image scalar or mapping"
                )
        services = job.get("services")
        if services is None:
            continue
        if not isinstance(services, dict):
            failures.append(f"{label} jobs.{job_name}.services must be a mapping")
            continue
        for service_name, service in services.items():
            if not isinstance(service, dict):
                failures.append(
                    f"{label} jobs.{job_name}.services.{service_name} must be a mapping"
                )
                continue
            append_image(
                service.get("image"),
                f"jobs.{job_name}.services.{service_name}.image",
            )
    return declarations


def action_uses_declarations(
    document: dict[str, Any],
    label: str,
    failures: list[str],
) -> list[ActionUse]:
    declarations: list[ActionUse] = []
    allowed_paths: set[tuple[str | int, ...]] = set()
    runs = document.get("runs")
    if not isinstance(runs, dict):
        failures.append(f"{label} must contain a runs mapping")
        return declarations
    steps = runs.get("steps")
    if steps is not None:
        if not isinstance(steps, list):
            failures.append(f"{label} runs.steps must be a sequence")
        else:
            for index, step in enumerate(steps):
                if not isinstance(step, dict):
                    failures.append(f"{label} runs.steps[{index}] must be a mapping")
                    continue
                if "uses" not in step:
                    continue
                path = ("runs", "steps", index, "uses")
                allowed_paths.add(path)
                scalar = step["uses"]
                if not isinstance(scalar, CanonicalYamlScalar) or not scalar.value:
                    failures.append(
                        f"{label} runs.steps[{index}].uses must be a non-empty scalar"
                    )
                else:
                    declarations.append(
                        ActionUse(scalar.value, scalar.comment, scalar.line, "action-step")
                    )

    for path, scalar in walk_yaml_uses(document):
        if path not in allowed_paths:
            line = scalar.line if isinstance(scalar, CanonicalYamlScalar) else "?"
            failures.append(f"{label}:{line} uses is outside runs.steps[*].uses")
    return declarations


def canonical_local_path(raw: str, label: str, failures: list[str]) -> PurePosixPath | None:
    if raw == "./":
        return PurePosixPath(".")
    if (
        not raw.startswith("./")
        or raw.startswith(".//")
        or "\\" in raw
        or "\x00" in raw
        or any(character in raw for character in "?#@")
        or re.fullmatch(r"\./[A-Za-z0-9._/-]+", raw) is None
    ):
        failures.append(f"{label} local uses path {raw!r} is ambiguous or non-canonical")
        return None
    tail = raw[2:]
    pure = PurePosixPath(tail)
    if (
        not tail
        or pure.is_absolute()
        or pure.as_posix() != tail
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        failures.append(f"{label} local uses path {raw!r} contains traversal or ambiguity")
        return None
    return pure


def contained_path(
    root: Path,
    relative: PurePosixPath,
    label: str,
    failures: list[str],
) -> Path | None:
    resolved_root = root.resolve()
    candidate = (resolved_root / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError:
        failures.append(f"{label} resolves outside the repository: {relative.as_posix()!r}")
        return None
    return candidate


def local_action_metadata(
    root: Path,
    raw: str,
    label: str,
    failures: list[str],
) -> Path | None:
    relative = canonical_local_path(raw, label, failures)
    if relative is None:
        return None
    directory = contained_path(root, relative, label, failures)
    if directory is None:
        return None
    if not directory.is_dir():
        failures.append(f"{label} local action directory does not exist: {raw!r}")
        return None
    candidates = [
        path
        for path in (directory / "action.yml", directory / "action.yaml")
        if path.is_file()
    ]
    if len(candidates) != 1:
        failures.append(
            f"{label} local action {raw!r} must contain exactly one action.yml or action.yaml; "
            f"found {len(candidates)}"
        )
        return None
    metadata = candidates[0].resolve()
    try:
        metadata.relative_to(root.resolve())
        metadata.relative_to(directory)
    except ValueError:
        failures.append(f"{label} local action metadata escapes its repository directory")
        return None
    return metadata


def local_action_file(
    root: Path,
    action_directory: Path,
    raw: str,
    label: str,
    failures: list[str],
) -> Path | None:
    candidate_raw = raw if raw.startswith("./") else f"./{raw}"
    relative = canonical_local_path(candidate_raw, label, failures)
    if relative is None:
        return None
    candidate = (action_directory / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
        candidate.relative_to(action_directory.resolve())
    except ValueError:
        failures.append(f"{label} local action file escapes its action directory: {raw!r}")
        return None
    if not candidate.is_file():
        failures.append(f"{label} local action file does not exist: {raw!r}")
        return None
    return candidate


def scalar_field(
    mapping: dict[str, Any],
    key: str,
    label: str,
    failures: list[str],
) -> str | None:
    scalar = mapping.get(key)
    if not isinstance(scalar, CanonicalYamlScalar) or not scalar.value:
        failures.append(f"{label} {key} must be a non-empty scalar")
        return None
    return scalar.value


def check_github_action_pins_from_root(root: Path, failures: list[str]) -> int:
    github_action = re.compile(
        r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?@([0-9a-fA-F]{40})$"
    )
    docker_image = re.compile(
        r"^docker://[A-Za-z0-9._:/-]+@sha256:[0-9a-fA-F]{64}$"
    )
    workflow_container = re.compile(
        r"^[A-Za-z0-9._:/-]+@sha256:[0-9a-fA-F]{64}$"
    )
    workflows = sorted((root / ".github" / "workflows").glob("*.y*ml"))
    scanned: set[Path] = set()
    visiting: list[Path] = []
    pinned = 0

    def read_yaml(path: Path) -> tuple[dict[str, Any] | None, str]:
        label = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {label}: {error}")
            return None, label
        try:
            return parse_canonical_yaml_document(text, label), label
        except CanonicalYamlError as error:
            failures.append(str(error))
            return None, label

    def enter(path: Path, label: str) -> bool:
        resolved = path.resolve()
        if resolved in visiting:
            start = visiting.index(resolved)
            cycle = visiting[start:] + [resolved]
            failures.append(
                f"{label} local uses cycle detected: "
                + " -> ".join(item.relative_to(root.resolve()).as_posix() for item in cycle)
            )
            return False
        if resolved in scanned:
            return False
        visiting.append(resolved)
        return True

    def leave(path: Path) -> None:
        resolved = path.resolve()
        if visiting and visiting[-1] == resolved:
            visiting.pop()
        scanned.add(resolved)

    def check_external(use: ActionUse, source_label: str) -> None:
        nonlocal pinned
        declaration = use.declaration
        location = f"{source_label}:{use.line}"
        if use.scope == "workflow-container":
            if workflow_container.fullmatch(declaration) is None:
                failures.append(
                    f"{location} workflow container {declaration!r} must use an immutable "
                    "sha256 digest"
                )
            else:
                pinned += 1
            return
        if declaration.startswith("docker://"):
            if docker_image.fullmatch(declaration) is None:
                failures.append(
                    f"{location} external container action must use an immutable sha256 digest"
                )
            else:
                pinned += 1
            return
        action_match = github_action.fullmatch(declaration)
        if action_match is None:
            failures.append(
                f"{location} external action {declaration!r} must be pinned to a full "
                "40-character commit SHA"
            )
            return
        action_path = declaration.rsplit("@", 1)[0]
        if any(part in {".", ".."} for part in action_path.split("/")):
            failures.append(f"{location} external action path contains traversal")
            return
        if re.search(r"\bv[0-9]", use.comment) is None:
            failures.append(
                f"{location} pinned action must retain a human-readable version comment"
            )
        pinned += 1

    def inspect_use(use: ActionUse, source_label: str) -> None:
        declaration = use.declaration
        location = f"{source_label}:{use.line}"
        if not declaration.startswith("./"):
            check_external(use, source_label)
            return
        if use.scope == "workflow-job":
            relative = canonical_local_path(declaration, location, failures)
            if relative is None:
                return
            if not re.fullmatch(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml", relative.as_posix()):
                failures.append(
                    f"{location} local reusable workflow must name one file directly under "
                    ".github/workflows"
                )
                return
            lexical_candidate = root.resolve() / Path(*relative.parts)
            if lexical_candidate.is_symlink():
                failures.append(
                    f"{location} local reusable workflow must not be a symbolic link"
                )
                return
            candidate = contained_path(root, relative, location, failures)
            if candidate is None or not candidate.is_file():
                failures.append(f"{location} local reusable workflow is missing: {declaration!r}")
                return
            inspect_workflow(candidate)
            return
        metadata = local_action_metadata(root, declaration, location, failures)
        if metadata is not None:
            inspect_action(metadata)

    def inspect_workflow(path: Path) -> None:
        label = path.relative_to(root).as_posix()
        if path.is_symlink():
            failures.append(f"{label} workflow file must not be a symbolic link")
            return
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            failures.append(f"{label} workflow file escapes the repository")
            return
        if not path.is_file():
            failures.append(f"{label} workflow file is missing")
            return
        if not enter(path, label):
            return
        document, label = read_yaml(path)
        if document is not None:
            for use in workflow_uses_declarations(document, label, failures):
                inspect_use(use, label)
            for container in workflow_container_declarations(document, label, failures):
                check_external(container, label)
        leave(path)

    def inspect_action(path: Path) -> None:
        label = path.relative_to(root).as_posix()
        if not enter(path, label):
            return
        document, label = read_yaml(path)
        if document is None:
            leave(path)
            return
        declarations = action_uses_declarations(document, label, failures)
        runs = document.get("runs")
        if not isinstance(runs, dict):
            leave(path)
            return
        using = scalar_field(runs, "using", f"{label} runs", failures)
        action_directory = path.parent.resolve()
        if using == "composite":
            if not isinstance(runs.get("steps"), list):
                failures.append(f"{label} composite action must declare runs.steps")
            for use in declarations:
                inspect_use(use, label)
        elif using in {"node12", "node16", "node20", "node24"}:
            if "steps" in runs:
                failures.append(f"{label} JavaScript action must not declare runs.steps")
            main = scalar_field(runs, "main", f"{label} runs", failures)
            if main is not None:
                local_action_file(root, action_directory, main, f"{label} runs.main", failures)
            for optional in ("pre", "post"):
                if optional not in runs:
                    continue
                value = scalar_field(runs, optional, f"{label} runs", failures)
                if value is not None:
                    local_action_file(
                        root,
                        action_directory,
                        value,
                        f"{label} runs.{optional}",
                        failures,
                    )
        elif using == "docker":
            if "steps" in runs:
                failures.append(f"{label} Docker action must not declare runs.steps")
            image = scalar_field(runs, "image", f"{label} runs", failures)
            if image is not None:
                if image.startswith("docker://"):
                    check_external(ActionUse(image, "", 0, "action-image"), label)
                else:
                    local_action_file(
                        root,
                        action_directory,
                        image,
                        f"{label} runs.image",
                        failures,
                    )
        elif using is not None:
            failures.append(f"{label} runs.using {using!r} is not an accepted local action runtime")
        leave(path)

    for workflow in workflows:
        inspect_workflow(workflow)
    return pinned


def check_github_action_pins(failures: list[str]) -> int:
    pinned = check_github_action_pins_from_root(REPOSITORY_ROOT, failures)
    if pinned == 0:
        failures.append("no immutable third-party GitHub Action pins were found")
    return pinned


def check_action_graph_fixtures(failures: list[str]) -> int:
    """Exercise transitive local-action resolution without touching the repository."""
    rejected = 0
    workflow_template = (
        "name: Fixture\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  guard:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Guard\n"
        "        uses: {uses}\n"
    )
    composite_header = (
        "name: Fixture\n"
        "description: Fixture action\n"
        "runs:\n"
        "  using: composite\n"
        "  steps:\n"
    )

    def write(root: Path, relative: str, text: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="axiom-action-fixtures-") as raw_root:
        fixture_root = Path(raw_root)

        indirect = fixture_root / "indirect"
        write(
            indirect,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(
            indirect,
            ".github/actions/wrapper/action.yml",
            composite_header
            + "    - name: Moving dependency\n"
            + "      uses: actions/setup-python@v6\n",
        )
        indirect_failures: list[str] = []
        check_github_action_pins_from_root(indirect, indirect_failures)
        if any("actions/setup-python@v6" in failure for failure in indirect_failures):
            rejected += 1
        else:
            failures.append("indirect moving-action fixture was not rejected transitively")

        moving_container = fixture_root / "moving-container"
        write(
            moving_container,
            ".github/workflows/guard.yml",
            "name: Fixture\n"
            "on:\n"
            "  workflow_dispatch:\n"
            "jobs:\n"
            "  guard:\n"
            "    runs-on: ubuntu-latest\n"
            "    container: ubuntu:latest\n"
            "    steps:\n"
            "      - name: Guard\n"
            "        run: echo guarded\n",
        )
        moving_container_failures: list[str] = []
        check_github_action_pins_from_root(
            moving_container, moving_container_failures
        )
        if any(
            "workflow container 'ubuntu:latest'" in failure
            for failure in moving_container_failures
        ):
            rejected += 1
        else:
            failures.append("moving workflow-container fixture was not rejected")

        traversal = fixture_root / "traversal"
        write(
            traversal,
            ".github/workflows/guard.yml",
            workflow_template.format(
                uses="./.github/actions/../actions/wrapper"
            ),
        )
        traversal_failures: list[str] = []
        check_github_action_pins_from_root(traversal, traversal_failures)
        if any("traversal or ambiguity" in failure for failure in traversal_failures):
            rejected += 1
        else:
            failures.append("local-action traversal fixture was not rejected")

        missing = fixture_root / "missing-metadata"
        write(
            missing,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(missing, ".github/actions/wrapper/README.md", "fixture\n")
        missing_failures: list[str] = []
        check_github_action_pins_from_root(missing, missing_failures)
        if any("exactly one action.yml or action.yaml" in failure for failure in missing_failures):
            rejected += 1
        else:
            failures.append("missing local-action metadata fixture was not rejected")

        cycle = fixture_root / "cycle"
        write(
            cycle,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/one"),
        )
        write(
            cycle,
            ".github/actions/one/action.yml",
            composite_header
            + "    - name: Two\n"
            + "      uses: ./.github/actions/two\n",
        )
        write(
            cycle,
            ".github/actions/two/action.yaml",
            composite_header
            + "    - name: One\n"
            + "      uses: ./.github/actions/one\n",
        )
        cycle_failures: list[str] = []
        check_github_action_pins_from_root(cycle, cycle_failures)
        if any("local uses cycle detected" in failure for failure in cycle_failures):
            rejected += 1
        else:
            failures.append("local composite-action cycle fixture was not rejected")

        duplicate = fixture_root / "duplicate-key"
        write(
            duplicate,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(
            duplicate,
            ".github/actions/wrapper/action.yml",
            "name: Fixture\n"
            "description: Fixture action\n"
            "runs:\n"
            "  using: composite\n"
            "  steps:\n"
            "runs:\n"
            "  using: composite\n"
            "  steps:\n",
        )
        duplicate_failures: list[str] = []
        check_github_action_pins_from_root(duplicate, duplicate_failures)
        if any("duplicate mapping key 'runs'" in failure for failure in duplicate_failures):
            rejected += 1
        else:
            failures.append("duplicate action-metadata key fixture was not rejected")

        valid = fixture_root / "valid"
        job_digest = "c" * 64
        service_digest = "d" * 64
        write(
            valid,
            ".github/workflows/guard.yml",
            "name: Fixture\n"
            "on:\n"
            "  workflow_dispatch:\n"
            "jobs:\n"
            "  guard:\n"
            "    runs-on: ubuntu-latest\n"
            "    container:\n"
            f"      image: ghcr.io/example/job@sha256:{job_digest}\n"
            "    services:\n"
            "      database:\n"
            f"        image: ghcr.io/example/database@sha256:{service_digest}\n"
            "    steps:\n"
            "      - name: Guard\n"
            "        uses: ./.github/actions/root\n",
        )
        write(
            valid,
            ".github/actions/root/action.yml",
            composite_header
            + "    - name: Nested composite\n"
            + "      uses: ./.github/actions/nested\n"
            + "    - name: Local JavaScript\n"
            + "      uses: ./.github/actions/javascript\n"
            + "    - name: Local Docker\n"
            + "      uses: ./.github/actions/docker\n",
        )
        sha = "a" * 40
        digest = "b" * 64
        write(
            valid,
            ".github/actions/nested/action.yaml",
            composite_header
            + "    - name: Pinned action\n"
            + f"      uses: actions/setup-python@{sha} # v6\n"
            + "    - name: Pinned container\n"
            + f"      uses: docker://ghcr.io/example/action@sha256:{digest}\n",
        )
        write(
            valid,
            ".github/actions/javascript/action.yml",
            "name: JavaScript fixture\n"
            "description: JavaScript fixture action\n"
            "runs:\n"
            "  using: node20\n"
            "  main: dist/index.js\n",
        )
        write(valid, ".github/actions/javascript/dist/index.js", "'use strict';\n")
        write(
            valid,
            ".github/actions/docker/action.yml",
            "name: Docker fixture\n"
            "description: Docker fixture action\n"
            "runs:\n"
            "  using: docker\n"
            "  image: Dockerfile\n",
        )
        write(valid, ".github/actions/docker/Dockerfile", "FROM scratch\n")
        valid_failures: list[str] = []
        valid_pins = check_github_action_pins_from_root(valid, valid_failures)
        if valid_failures or valid_pins != 4:
            failures.append(
                "valid pinned local composite, JavaScript, and Docker action graph failed: "
                + "; ".join(valid_failures)
            )

    return rejected + 1


def check_distribution_workflow_contract(
    failures: list[str],
) -> dict[str, Any] | None:
    path = REPOSITORY_ROOT / ".github" / "workflows" / "distribution-drift.yml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {display_path(path)}: {error}")
        return None

    label = display_path(path)
    try:
        document = parse_canonical_yaml_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None

    def scalar(value: Any) -> str | None:
        return value.value if isinstance(value, CanonicalYamlScalar) else None

    def scalar_values(value: Any) -> list[str] | None:
        if not isinstance(value, list) or any(
            not isinstance(item, CanonicalYamlScalar) for item in value
        ):
            return None
        return [item.value for item in value]

    if set(document) != {"name", "on", "permissions", "jobs"}:
        failures.append(f"{label} must contain only name, on, permissions, and jobs")
    if scalar(document.get("name")) != "Distribution and publication guards":
        failures.append(f"{label} must keep its exact public workflow name")

    triggers = document.get("on")
    if not isinstance(triggers, dict) or set(triggers) != {
        "pull_request",
        "push",
        "workflow_dispatch",
    }:
        failures.append(
            f"{label} must structurally declare only pull_request, push, and "
            "workflow_dispatch triggers"
        )
    else:
        pull_request = triggers.get("pull_request")
        if not isinstance(pull_request, dict) or scalar_values(
            pull_request.get("branches")
        ) != ["main"]:
            failures.append(f"{label} pull_request trigger must target only main")
        for event_name in ("push", "workflow_dispatch"):
            event = triggers.get(event_name)
            if not isinstance(event, CanonicalYamlScalar) or event.value:
                failures.append(f"{label} {event_name} trigger must not accept filters")

    permissions = document.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != {"contents"}:
        failures.append(f"{label} must grant only the contents permission")
    elif scalar(permissions.get("contents")) != "read":
        failures.append(f"{label} contents permission must be read-only")

    jobs = document.get("jobs")
    job = jobs.get("repository-guards") if isinstance(jobs, dict) else None
    if not isinstance(jobs, dict) or set(jobs) != {"repository-guards"}:
        failures.append(f"{label} must declare only the repository-guards job")
    if not isinstance(job, dict) or set(job) != {
        "runs-on",
        "timeout-minutes",
        "steps",
    }:
        failures.append(
            f"{label} repository-guards must contain only runner, timeout, and steps"
        )
    elif (
        scalar(job.get("runs-on")) != "ubuntu-latest"
        or scalar(job.get("timeout-minutes")) != "5"
    ):
        failures.append(f"{label} repository-guards runner or timeout changed")

    steps = job.get("steps") if isinstance(job, dict) else None
    if not isinstance(steps, list) or len(steps) != 3 or any(
        not isinstance(step, dict) for step in steps
    ):
        failures.append(f"{label} must contain exactly three canonical validation steps")
    else:
        checkout, distribution, publication = steps
        checkout_with = checkout.get("with")
        if (
            set(checkout) != {"name", "uses", "with"}
            or scalar(checkout.get("name")) != "Check out repository"
            or scalar(checkout.get("uses"))
            != "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
            or not isinstance(checkout_with, dict)
            or set(checkout_with) != {"persist-credentials"}
            or scalar(checkout_with.get("persist-credentials")) != "false"
        ):
            failures.append(
                f"{label} checkout must remain immutable and must not persist credentials"
            )
        expected_commands = (
            (
                distribution,
                "Check distribution agreement",
                "python3 scripts/check-distribution-drift.py",
            ),
            (
                publication,
                "Check publication invariants",
                "python3 scripts/check-publication.py",
            ),
        )
        for step, expected_name, expected_command in expected_commands:
            if (
                set(step) != {"name", "run"}
                or scalar(step.get("name")) != expected_name
                or scalar(step.get("run")) != expected_command
            ):
                failures.append(
                    f"{label} must run exact read-only validator step {expected_name!r}"
                )

    for forbidden in (
        "pull_request_target",
        "${{ secrets.",
        "${{ github.token",
        "GITHUB_TOKEN",
    ):
        if forbidden in text:
            failures.append(f"{label} exposes forbidden pull-request surface {forbidden!r}")
    return document


def check_pull_request_validation_fixtures(
    distribution_document: dict[str, Any] | None,
    release_workflow_text: str | None,
    documents: dict[str, dict[str, Any]],
    failures: list[str],
) -> int:
    label = "pull-request validation event graph"
    if distribution_document is None or release_workflow_text is None:
        failures.append(f"{label} could not be constructed from both workflows")
        return 0
    try:
        release_document = parse_canonical_yaml_document(
            release_workflow_text,
            ".github/workflows/release-signature-guard.yml",
        )
    except CanonicalYamlError as error:
        failures.append(str(error))
        return 0

    distribution_triggers = distribution_document.get("on")
    release_triggers = release_document.get("on")
    distribution_events = (
        set(distribution_triggers) if isinstance(distribution_triggers, dict) else set()
    )
    release_events = set(release_triggers) if isinstance(release_triggers, dict) else set()
    pull_request = (
        distribution_triggers.get("pull_request")
        if isinstance(distribution_triggers, dict)
        else None
    )
    pull_request_branches = (
        {
            item.value
            for item in pull_request.get("branches", [])
            if isinstance(item, CanonicalYamlScalar)
        }
        if isinstance(pull_request, dict)
        else set()
    )
    scenarios = (
        {
            "name": "same-repository-unsigned-valid",
            "base": "main",
            "headRepository": "wheakerd/axiom",
            "signed": False,
            "valid": True,
        },
        {
            "name": "fork-unsigned-valid",
            "base": "main",
            "headRepository": "contributor/axiom",
            "signed": False,
            "valid": True,
        },
        {
            "name": "fork-manifest-version-violation",
            "base": "main",
            "headRepository": "contributor/axiom",
            "signed": False,
            "valid": False,
        },
    )
    for scenario in scenarios:
        name = scenario["name"]
        static_scheduled = (
            "pull_request" in distribution_events
            and scenario["base"] in pull_request_branches
        )
        provenance_scheduled = "pull_request" in release_events
        if not static_scheduled:
            failures.append(f"{label}:{name} did not schedule static validation")
        if provenance_scheduled:
            failures.append(f"{label}:{name} incorrectly scheduled release provenance")

        fixture_documents = json.loads(json.dumps(documents))
        expected_valid = bool(scenario["valid"])
        if not expected_valid:
            manifest = fixture_documents.get(".claude-plugin/plugin.json")
            if not isinstance(manifest, dict):
                failures.append(f"{label}:{name} could not construct the invalid fixture")
                continue
            manifest["version"] = "9.9.9"
        fixture_failures: list[str] = []
        check_manifest_versions(fixture_documents, fixture_failures)
        observed_valid = not fixture_failures
        if observed_valid != expected_valid:
            detail = "; ".join(fixture_failures) if fixture_failures else "accepted"
            failures.append(
                f"{label}:{name} publication result was {detail}; "
                f"expected {'pass' if expected_valid else 'rejection'}"
            )
    return len(scenarios)


def check_release_signature_workflow_contract(failures: list[str]) -> str | None:
    path = REPOSITORY_ROOT / ".github" / "workflows" / "release-signature-guard.yml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {display_path(path)}: {error}")
        return None

    label = display_path(path)
    try:
        document = parse_canonical_yaml_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        document = {}

    triggers = document.get("on")
    if not isinstance(triggers, dict) or set(triggers) != {
        "push",
        "release",
        "workflow_dispatch",
    }:
        failures.append(
            f"{label} must structurally declare only push, release, and workflow_dispatch "
            "triggers"
        )
    else:
        push = triggers.get("push")
        release = triggers.get("release")

        def scalar_values(value: Any) -> list[str] | None:
            if not isinstance(value, list) or any(
                not isinstance(item, CanonicalYamlScalar) for item in value
            ):
                return None
            return [item.value for item in value]

        if (
            not isinstance(push, dict)
            or scalar_values(push.get("branches")) != ["main"]
            or scalar_values(push.get("tags")) != ["v*"]
        ):
            failures.append(f"{label} push trigger must cover only main and v* tags")
        if not isinstance(release, dict) or scalar_values(release.get("types")) != [
            "published",
            "edited",
        ]:
            failures.append(
                f"{label} release trigger must cover published and edited events"
            )
        manual = triggers.get("workflow_dispatch")
        if not isinstance(manual, CanonicalYamlScalar) or manual.value:
            failures.append(f"{label} workflow_dispatch trigger must not accept inputs")

    require_ordered_contract_anchors(
        path,
        (
            "const defaultRef = `refs/heads/${defaultBranch}`;",
            "const strictSemVer = /^(?:0|[1-9]",
            "function releaseTagVersion(tagName)",
            "return strictSemVer.test(version) ? version : null;",
            "function isSingleTagCreation(payload)",
            "payload.created === true",
            "payload.deleted === false",
            "payload.forced === false",
            "/^0{40}$/.test(payload.before)",
            "/^(?!0{40}$)[0-9a-f]{40}$/i.test(payload.after)",
            "function failClosedTagMutation(reason)",
            "true server-side prevention still depends on a GitHub tag ruleset",
            "async function readJsonAtCommit(path, commitSha)",
            "async function packageVersionAtCommit(commitSha)",
            '".codex-plugin/plugin.json"',
            '".claude-plugin/plugin.json"',
            '!strictSemVer.test(version)',
            "versions[0] !== versions[1]",
            "async function peelRefToCommit(qualifiedRef, expectedObjectSha = null)",
            "object.sha !== expectedObjectSha",
            "context.payload.release?.tag_name",
            "releaseTagVersion(tagName) === null",
            "context.ref !== targetRef",
            "GitHub Release tag ${targetRef} does not match event ref ${context.ref}.",
            "targetCommit = await peelRefToCommit(targetRef);",
            "context.ref === defaultRef",
            'context.ref.startsWith("refs/tags/")',
            "!isSingleTagCreation(context.payload)",
            "failClosedTagMutation(",
            "targetCommit = await peelRefToCommit(targetRef, context.payload.after);",
            "Unexpected manual verification ref",
            "const packageVersion = await packageVersionAtCommit(targetCommit);",
            "const expectedReleaseTag = `v${packageVersion}`;",
            "targetTagName !== expectedReleaseTag",
            "const defaultCommit = await peelRefToCommit(defaultRef);",
            "const historyBase = targetMustDescendFromDefault",
            "github.rest.repos.compareCommitsWithBasehead",
            "comparison.data.merge_base_commit?.sha !== historyBase",
            "const result = await github.graphql",
            "signature?.wasSignedByGitHub !== true",
        ),
        failures,
        "release target signature",
    )
    for owner in (
        "          script: |",
        "function releaseTagVersion(tagName)",
        "function isSingleTagCreation(payload)",
        "function failClosedTagMutation(reason)",
        "async function packageVersionAtCommit(commitSha)",
    ):
        if text.count(owner) != 1:
            failures.append(f"{label} must contain exactly one critical owner {owner!r}")
    for weak_pattern in ("/^v[0-9]/", "/^refs\\/tags\\/v[0-9]/"):
        if weak_pattern in text:
            failures.append(f"{label} retains weak release-tag matcher {weak_pattern!r}")
    for removed_pull_request_gate in (
        'context.eventName === "pull_request"',
        "pullRequest?.head?.repo?.full_name",
        "targetCommit = pullRequest.head.sha;",
    ):
        if removed_pull_request_gate in text:
            failures.append(
                f"{label} still applies release provenance to pull requests via "
                f"{removed_pull_request_gate!r}"
            )
    return text


def extract_canonical_yaml_literal_block(
    text: str,
    header: str,
    label: str,
) -> str | None:
    """Extract the exact value of one canonical YAML literal block."""
    lines = text.splitlines()
    owners = [index for index, line in enumerate(lines) if line == header]
    if len(owners) != 1:
        return None

    header_index = owners[0]
    header_indent = len(header) - len(header.lstrip(" "))
    block_lines: list[str] = []
    for line in lines[header_index + 1 :]:
        if not line.strip():
            block_lines.append("")
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= header_indent:
            break
        block_lines.append(line)

    content_indents = [
        len(line) - len(line.lstrip(" ")) for line in block_lines if line.strip()
    ]
    if not content_indents or min(content_indents) != header_indent + 2:
        return None
    content_indent = min(content_indents)
    extracted: list[str] = []
    for line in block_lines:
        if not line:
            extracted.append("")
        elif line[:content_indent] != " " * content_indent:
            return None
        else:
            extracted.append(line[content_indent:])
    return "\n".join(extracted) + "\n"


RELEASE_SCRIPT_NODE_HARNESS = r"""
"use strict";
const fs = require("node:fs");
const vm = require("node:vm");
const input = JSON.parse(fs.readFileSync(0, "utf8"));

async function runScenario(scenario) {
  const sandbox = Object.create(null);
  sandbox.__scenarioJson = JSON.stringify(scenario);
  const context = vm.createContext(sandbox, {
    name: `release-signature-${scenario.name}`,
    codeGeneration: { strings: false, wasm: false },
  });
  const bootstrap = `
"use strict";
const __scenario = JSON.parse(__scenarioJson);
const __failures = [];
const __infos = [];
const __stringify = JSON.stringify.bind(JSON);
const context = Object.freeze(__scenario.context);
const core = Object.freeze({
  setFailed(message) { __failures.push(String(message)); },
  info(message) { __infos.push(String(message)); },
});
const Buffer = Object.freeze({
  from(value, encoding) {
    if (typeof value !== "string" || encoding !== "base64") {
      throw new Error("Unexpected Buffer.from request in offline release fixture.");
    }
    return Object.freeze({
      toString(outputEncoding) {
        if (outputEncoding !== "utf8") {
          throw new Error("Unexpected Buffer output encoding in offline release fixture.");
        }
        return __stringify({ version: __scenario.packageVersion });
      },
    });
  },
});
const github = Object.freeze({
  rest: Object.freeze({
    repos: Object.freeze({
      async get() {
        return { data: { default_branch: "main" } };
      },
      async getContent({ path, ref }) {
        if (
          ![".codex-plugin/plugin.json", ".claude-plugin/plugin.json"].includes(path) ||
          typeof ref !== "string" ||
          ref.length === 0
        ) {
          throw new Error("Unexpected manifest lookup in offline release fixture.");
        }
        return {
          data: {
            type: "file",
            encoding: "base64",
            content: "offline-fixture",
          },
        };
      },
      async compareCommitsWithBasehead({ basehead }) {
        const base = String(basehead).split("...")[0];
        const configured = __scenario.comparison;
        return {
          data: {
            merge_base_commit: {
              sha: configured ? configured.mergeBaseSha : base,
            },
            status: configured ? configured.status : "ahead",
          },
        };
      },
    }),
    git: Object.freeze({
      async getRef({ ref }) {
        const qualifiedRef = "refs/" + ref;
        const object = __scenario.refs[qualifiedRef];
        if (!object) {
          throw new Error("Unexpected ref lookup " + qualifiedRef + ".");
        }
        return { data: { ref: qualifiedRef, object } };
      },
      async getTag({ tag_sha }) {
        const tag = (__scenario.tags || {})[tag_sha];
        if (!tag) {
          throw new Error("Unexpected annotated tag lookup " + tag_sha + ".");
        }
        return { data: { object: tag } };
      },
    }),
  }),
  async graphql(_query, variables) {
    return {
      repository: {
        object: {
          oid: variables.oid,
          signature: __scenario.signature || {
            isValid: true,
            state: "VALID",
            wasSignedByGitHub: true,
          },
        },
      },
    };
  },
});
`;
  const wrapper = `${bootstrap}
(async () => {
${input.script}
})().then(
  () => {
    globalThis.__resultJson = __stringify({ failures: __failures, infos: __infos });
  },
  (error) => {
    __failures.push(
      "THREW:" + String(error && error.name) + ":" + String(error && error.message),
    );
    globalThis.__resultJson = __stringify({ failures: __failures, infos: __infos });
  },
);
`;
  const execution = new vm.Script(wrapper, {
    filename: `release-signature-${scenario.name}.js`,
  }).runInContext(context, { timeout: 2000 });
  let timeout;
  try {
    await Promise.race([
      execution,
      new Promise((_, reject) => {
        timeout = setTimeout(() => reject(new Error("scenario timeout")), 5000);
      }),
    ]);
  } finally {
    clearTimeout(timeout);
  }
  if (typeof context.__resultJson !== "string") {
    throw new Error(`Scenario ${scenario.name} produced no result.`);
  }
  return { name: scenario.name, ...JSON.parse(context.__resultJson) };
}

(async () => {
  const results = [];
  for (const scenario of input.scenarios) {
    results.push(await runScenario(scenario));
  }
  process.stdout.write(JSON.stringify({ results }));
})().catch((error) => {
  process.stderr.write(String(error && error.stack ? error.stack : error));
  process.exitCode = 1;
});
"""


def release_script_scenarios() -> tuple[dict[str, Any], ...]:
    null_sha = "0" * 40
    main_sha = "1" * 40
    tag_sha = "2" * 40
    release_branch_sha = "3" * 40
    old_tag_sha = "4" * 40
    outside_history_sha = "5" * 40
    repository = {"owner": "wheakerd", "repo": "axiom"}
    release_tag = f"v{RELEASE_VERSION}"
    major, minor, patch = RELEASE_VERSION.split(".")
    mismatched_tag = f"v{major}.{minor}.{int(patch) + 1}"

    def fixture(
        name: str,
        event_name: str,
        ref: str,
        payload: dict[str, Any],
        *,
        target_ref: str | None = None,
        target_sha: str | None = None,
        comparison: dict[str, str] | None = None,
        signature: dict[str, Any] | None = None,
        expected_failure: str | None = None,
    ) -> dict[str, Any]:
        refs: dict[str, dict[str, str]] = {
            "refs/heads/main": {"type": "commit", "sha": main_sha}
        }
        if target_ref is not None and target_sha is not None:
            refs[target_ref] = {"type": "commit", "sha": target_sha}
        return {
            "name": name,
            "context": {
                "repo": repository,
                "eventName": event_name,
                "ref": ref,
                "payload": payload,
            },
            "refs": refs,
            "packageVersion": RELEASE_VERSION,
            "comparison": comparison,
            "signature": signature,
            "expectedFailure": expected_failure,
        }

    def tag_push(
        name: str,
        tag_name: str,
        *,
        before: str,
        after: str,
        created: bool,
        deleted: bool,
        forced: bool,
        comparison: dict[str, str] | None = None,
        expected_failure: str | None,
    ) -> dict[str, Any]:
        tag_ref = f"refs/tags/{tag_name}"
        return fixture(
            name,
            "push",
            tag_ref,
            {
                "before": before,
                "after": after,
                "created": created,
                "deleted": deleted,
                "forced": forced,
            },
            target_ref=tag_ref,
            target_sha=after,
            comparison=comparison,
            expected_failure=expected_failure,
        )

    immutable_failure = "not a single immutable creation event"
    strict_tag_failure = "not one exact strict SemVer tag"
    return (
        fixture(
            "pull-request-provenance-rejected",
            "pull_request",
            "refs/pull/7/merge",
            {},
            expected_failure="Unsupported event pull_request.",
        ),
        fixture(
            "main-push",
            "push",
            "refs/heads/main",
            {"after": main_sha},
        ),
        fixture(
            "main-push-unsigned",
            "push",
            "refs/heads/main",
            {"after": main_sha},
            signature={
                "isValid": False,
                "state": "INVALID",
                "wasSignedByGitHub": False,
            },
            expected_failure="must have a valid signature made with GitHub's signing key",
        ),
        fixture(
            "release",
            "release",
            f"refs/tags/{release_tag}",
            {"release": {"tag_name": release_tag}},
            target_ref=f"refs/tags/{release_tag}",
            target_sha=tag_sha,
        ),
        fixture(
            "release-event-ref-mismatch",
            "release",
            f"refs/tags/{mismatched_tag}",
            {"release": {"tag_name": release_tag}},
            expected_failure="does not match event ref",
        ),
        fixture(
            "release-version-mismatch",
            "release",
            f"refs/tags/{mismatched_tag}",
            {"release": {"tag_name": mismatched_tag}},
            target_ref=f"refs/tags/{mismatched_tag}",
            target_sha=tag_sha,
            expected_failure="does not match package version",
        ),
        fixture(
            "workflow-dispatch-main",
            "workflow_dispatch",
            "refs/heads/main",
            {},
        ),
        fixture(
            "workflow-dispatch-release-branch",
            "workflow_dispatch",
            f"refs/heads/release/{release_tag}",
            {},
            target_ref=f"refs/heads/release/{release_tag}",
            target_sha=release_branch_sha,
        ),
        tag_push(
            "tag-create",
            release_tag,
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=None,
        ),
        tag_push(
            "tag-outside-main-history",
            release_tag,
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            comparison={
                "mergeBaseSha": outside_history_sha,
                "status": "diverged",
            },
            expected_failure="is not on the refs/heads/main history policy",
        ),
        tag_push(
            "tag-v9oops",
            "v9oops",
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=strict_tag_failure,
        ),
        tag_push(
            "tag-v01",
            "v01",
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=strict_tag_failure,
        ),
        tag_push(
            "tag-extra-path",
            f"{release_tag}/extra",
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=strict_tag_failure,
        ),
        tag_push(
            "tag-version-mismatch",
            mismatched_tag,
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure="does not match package version",
        ),
        tag_push(
            "tag-move",
            release_tag,
            before=old_tag_sha,
            after=tag_sha,
            created=False,
            deleted=False,
            forced=False,
            expected_failure=immutable_failure,
        ),
        tag_push(
            "tag-delete",
            release_tag,
            before=old_tag_sha,
            after=null_sha,
            created=False,
            deleted=True,
            forced=False,
            expected_failure=immutable_failure,
        ),
        tag_push(
            "tag-forced",
            release_tag,
            before=old_tag_sha,
            after=tag_sha,
            created=False,
            deleted=False,
            forced=True,
            expected_failure=immutable_failure,
        ),
        tag_push(
            "tag-inconsistent-created",
            release_tag,
            before=old_tag_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=immutable_failure,
        ),
    )


def execute_release_workflow_script(
    script: str,
    scenarios: tuple[dict[str, Any], ...],
    failures: list[str],
    label: str,
) -> dict[str, dict[str, Any]] | None:
    payload = {"script": script, "scenarios": scenarios}
    try:
        result = subprocess.run(
            ["node", "-e", RELEASE_SCRIPT_NODE_HARNESS],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except FileNotFoundError:
        failures.append(f"{label} requires Node.js to execute the exact github-script")
        return None
    except subprocess.TimeoutExpired:
        failures.append(f"{label} exact github-script execution timed out")
        return None
    if result.returncode != 0:
        detail = result.stderr.strip() or "no diagnostic"
        failures.append(f"{label} exact github-script harness failed: {detail}")
        return None
    try:
        decoded = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        failures.append(f"{label} exact github-script harness returned invalid JSON: {error}")
        return None
    results = decoded.get("results") if isinstance(decoded, dict) else None
    if not isinstance(results, list) or len(results) != len(scenarios):
        failures.append(f"{label} exact github-script harness returned incomplete results")
        return None
    indexed: dict[str, dict[str, Any]] = {}
    for item in results:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            failures.append(f"{label} exact github-script harness returned malformed results")
            return None
        indexed[item["name"]] = item
    if len(indexed) != len(scenarios):
        failures.append(f"{label} exact github-script harness repeated a scenario name")
        return None
    return indexed


def validate_release_workflow_script(
    script: str,
    scenarios: tuple[dict[str, Any], ...],
    failures: list[str],
    label: str,
) -> int:
    results = execute_release_workflow_script(script, scenarios, failures, label)
    if results is None:
        return 0
    for scenario in scenarios:
        name = scenario["name"]
        result = results.get(name)
        if result is None:
            failures.append(f"{label}:{name} produced no result")
            continue
        observed = result.get("failures")
        if not isinstance(observed, list) or any(
            not isinstance(message, str) for message in observed
        ):
            failures.append(f"{label}:{name} returned malformed failure evidence")
            continue
        expected = scenario["expectedFailure"]
        if expected is None:
            if observed:
                failures.append(
                    f"{label}:{name} legitimate control failed: {'; '.join(observed)}"
                )
        elif not any(expected in message for message in observed):
            rendered = "; ".join(observed) if observed else "accepted"
            failures.append(
                f"{label}:{name} expected failure containing {expected!r}, got {rendered}"
            )
    return len(scenarios)


def check_release_script_runtime_contract(
    workflow_text: str | None,
    failures: list[str],
) -> int:
    label = ".github/workflows/release-signature-guard.yml"
    if workflow_text is None:
        failures.append(f"{label} exact github-script runtime fixtures could not start")
        return 0
    script = extract_canonical_yaml_literal_block(
        workflow_text,
        "          script: |",
        label,
    )
    if script is None:
        failures.append(f"{label} exact github-script literal block could not be extracted")
        return 0

    scenarios = release_script_scenarios()
    count = validate_release_workflow_script(
        script,
        scenarios,
        failures,
        "release-script",
    )

    mutation_owner = "function isSingleTagCreation(payload) {\n"
    mutation = (
        mutation_owner
        + "  if (payload.created === false) return true;\n"
    )
    if script.count(mutation_owner) != 1:
        failures.append(f"{label} bypass regression fixture could not locate its exact gate")
        return count
    mutated_script = script.replace(mutation_owner, mutation, 1)
    move_scenario = tuple(
        scenario for scenario in scenarios if scenario["name"] == "tag-move"
    )
    mutation_failures: list[str] = []
    validate_release_workflow_script(
        mutated_script,
        move_scenario,
        mutation_failures,
        "release-script-bypass-mutation",
    )
    if not any(
        "release-script-bypass-mutation:tag-move expected failure" in failure
        and "got accepted" in failure
        for failure in mutation_failures
    ):
        detail = "; ".join(mutation_failures) if mutation_failures else "no mismatch"
        failures.append(
            f"{label} bypass regression fixture was not detected by exact execution: {detail}"
        )
    else:
        count += 1
    return count


def check_validator_negative_fixtures(failures: list[str]) -> int:
    """Prove that the strict parsers reject the bypass forms they guard."""
    rejected = 0
    frontmatter = "name: fixture\ndescription: Valid fixture"
    frontmatter_fixtures = {
        "duplicate": frontmatter.replace("name: fixture", "name: one\nname: two"),
        "unknown-tail": f"{frontmatter}\nextra: tail",
        "wrong-type": frontmatter.replace("name: fixture", "name: false"),
        "yaml-1.1-bool": frontmatter.replace("Valid fixture", "On"),
        "numeric-float": frontmatter.replace(
            "Valid fixture", "12345678901234567890.12345678901234567890"
        ),
        "block-scalar": frontmatter.replace("Valid fixture", ">"),
    }
    for name, fixture in frontmatter_fixtures.items():
        try:
            parse_skill_frontmatter_document(
                f"---\n{fixture}\n---\n\n# Fixture\n",
                f"fixture:{name}",
            )
        except CanonicalYamlError:
            rejected += 1
        else:
            failures.append(f"strict YAML negative fixture {name!r} was accepted")

    agent = (
        'interface:\n  display_name: "Fixture"\n'
        '  short_description: "Valid description that is long enough"\n'
        '  default_prompt: "Use $fixture now."'
    )
    agent_fixtures = {
        "duplicate": agent.replace(
            '  display_name: "Fixture"',
            '  display_name: "Fixture"\n  display_name: "Duplicate"',
        ),
        "unknown-tail": f'{agent}\nextra:\n  field: "ignored before"',
        "wrong-type": agent.replace('"Fixture"', "false", 1),
        "second-document": f"{agent}\n---\nignored: true",
    }
    for name, fixture in agent_fixtures.items():
        try:
            parse_agent_metadata_document(fixture, f"fixture:{name}", allow_policy=False)
        except CanonicalYamlError:
            rejected += 1
        else:
            failures.append(f"agent metadata negative fixture {name!r} was accepted")

    return rejected + check_action_graph_fixtures(failures)


GIT_OID_WIDTHS = {"sha1": 40, "sha256": 64}


def safe_git_oid(value: str, object_format: str, *, allow_null: bool = False) -> bool:
    width = GIT_OID_WIDTHS.get(object_format)
    if width is None or re.fullmatch(rf"[0-9a-fA-F]{{{width}}}", value) is None:
        return False
    return allow_null or value != "0" * width


def direct_branch_ref_gate(
    symbolic_classification: str,
    resolved_oid: str,
    frozen_head: str,
    rechecked_before_use: bool,
) -> bool:
    return bool(
        symbolic_classification == "non-symbolic"
        and resolved_oid == frozen_head
        and rechecked_before_use
    )


def safe_git_operand(
    kind: str,
    value: str,
    literal_arguments: bool,
) -> bool:
    if not literal_arguments or not value:
        return False
    if any(
        ord(character) < 32 or 0x7F <= ord(character) <= 0x9F
        for character in value
    ):
        return False
    if "\u2028" in value or "\u2029" in value:
        return False
    if kind == "remote":
        return not value.startswith("-")
    if kind == "path":
        return True
    if kind != "ref" or not value.startswith("refs/"):
        return False
    components = value.split("/")
    if any(not component or component.startswith("-") for component in components):
        return False
    if value.endswith(("/", ".")) or ".." in value or "@{" in value:
        return False
    return not any(character in value for character in " ~^:?*[\\")


def safe_git_transport(value: str) -> bool:
    if not safe_git_operand("path", value, True) or "::" in value:
        return False
    if re.match(r"^(?:https|ssh|git\+ssh)://", value, re.IGNORECASE):
        return True
    if "://" in value:
        return False
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return False
    return re.match(r"^(?:[^/@:\s]+@)?[^/:\s]+:.+$", value) is not None


COMMAND_CAPABLE_GIT_CONFIG = (
    re.compile(
        r"^core\.(?:fsmonitor|sshcommand|hookspath|askpass|gitproxy|pager|editor|alternaterefscommand)$"
    ),
    re.compile(r"^(?:sequence\.editor|pager\..+|gc\.recentobjectshook)$"),
    re.compile(r"^(?:commit|tag)\.gpgsign$"),
    re.compile(r"^credential(?:\..+)?\.helper$"),
    re.compile(r"^diff\.(?:external|.+\.(?:command|textconv))$"),
    re.compile(r"^filter\..+\.(?:clean|smudge|process)$"),
    re.compile(r"^remote\..+\.(?:proxy|uploadpack|receivepack)$"),
    re.compile(r"^url\..+\.(?:insteadof|pushinsteadof)$"),
    re.compile(r"^(?:gpg|gpg\..+)\.program$"),
    re.compile(r"^include(?:if\..+)?\.path$"),
)


def safe_git_execution_envelope(
    local_config_keys: tuple[str, ...],
    ambient_environment_names: tuple[str, ...],
    handled_config_keys: tuple[str, ...] = (),
) -> bool:
    handled = {key.casefold() for key in handled_config_keys}
    for raw_key in local_config_keys:
        key = raw_key.casefold()
        if any(pattern.fullmatch(key) for pattern in COMMAND_CAPABLE_GIT_CONFIG):
            if key not in handled:
                return False

    for raw_name in ambient_environment_names:
        name = raw_name.upper()
        if name.startswith("GIT_") or name in {
            "PAGER",
            "EDITOR",
            "VISUAL",
            "SSH_ASKPASS",
        }:
            return False
    return True


def all_evidence(evidence: dict[str, bool], fields: tuple[str, ...]) -> bool:
    return all(evidence.get(field, False) for field in fields)


def check_traceable_security_contracts(failures: list[str]) -> int:
    skill_root = REPOSITORY_ROOT / "skills" / "traceable-git-submit"
    required_anchors = {
        "SKILL.md": (
            "references/safe-git-values-and-metadata.md",
            "references/commit-construction.md",
            "references/repository-and-remote-targets.md",
            "references/post-consolidation-recovery.md",
            "non-executable Git configuration and environment boundary",
            "cleanupReady",
            "Cleanup requires separate exact authority",
        ),
        "references/safe-git-values-and-metadata.md": (
            "literal argument-vector element",
            "git check-ref-format",
            "target-controlled",
            "core.fsmonitor",
            "core.sshCommand",
            "credential helpers",
            "`GIT_*`",
            "installed Git version",
            "no-follow",
            "linked worktree",
            "parent identity",
            "require strict UTF-8",
            "invalid/overlong/surrogate encodings",
            "NUL, CR, LF, ASCII C0, DEL, C1",
            "`U+2028`, `U+2029`",
            "`Cc`, `Cf`, `Zl`, and `Zp`",
        ),
        "references/baseline-and-preflight.md": (">/dev/null 2>&1",),
        "references/repository-and-remote-targets.md": (
            "non-visible literal-argument capture",
            "a configured remote explicitly named in the current request",
            "`branch.<branch>.pushRemote`",
            "`remote.pushDefault`",
            "current `upstreamRemote`",
            "`pushRemote != upstreamRemote`",
            "`fetch.bundleURI`",
            "Bypass pre-push hooks unless their exact frozen identity and action are separately authorized",
            "<helper>::<address>",
            "`protocol.allow=never`",
        ),
        "references/post-consolidation-recovery.md": (
            "cleanupReady",
            "separate authority for both deletions",
            "exact repository",
            "Push/recovery authority never implies fetch",
            "Local-only consolidation persists the initial",
            "then transition once to",
            "Never overwrite or rebind a bound record",
        ),
        "references/consolidation-and-push.md": (
            "Network-push authority never authorizes it",
            "Generic prune needs separate exact authority",
            "Delete no backup or active record without the separately authorized exact cleanup envelope",
        ),
    }
    for relative_path, anchors in required_anchors.items():
        path = skill_root / relative_path
        text = path.read_text(encoding="utf-8")
        normalized_text = " ".join(text.split()).casefold()
        for anchor in anchors:
            if " ".join(anchor.split()).casefold() not in normalized_text:
                failures.append(
                    f"{display_path(path)} is missing traceable security contract {anchor!r}"
                )

    refresh_command = (
        "git -C <repo> -c fetch.all=false -c fetch.prune=false -c fetch.pruneTags=false "
        "-c fetch.recurseSubmodules=false -c fetch.writeCommitGraph=false "
        "-c maintenance.auto=false fetch --no-all --no-tags --no-prune --no-prune-tags "
        "--no-recurse-submodules --no-write-fetch-head --no-auto-maintenance "
        "--no-write-commit-graph --refmap= <fetch-target> <source-ref>"
    )
    push_command = (
        "git -C <repo> -c push.followTags=false -c push.recurseSubmodules=no "
        "-c push.gpgSign=false -c push.pushOption= -c push.negotiate=false "
        "-c push.autoSetupRemote=false push --no-verify --no-follow-tags "
        "--recurse-submodules=no --no-signed --no-push-option --no-set-upstream "
        "--no-prune --no-force --no-force-with-lease --no-force-if-includes "
        "<push-target> <branch-ref>:<merge-ref>"
    )
    require_ordered_contract_anchors(
        skill_root / "references/consolidation-and-push.md",
        (
            "## Exact Remote Refresh",
            "Freeze and validate `objectFormat`",
            "source-only refspec is exactly validated `mergeRef`",
            refresh_command,
            "Re-query `sourceRef`, require the same `sourceOid`",
            "git -C <repo> update-ref --no-deref <upstream-tracking-ref> <source-oid> <old-tracking-oid>",
            "The old value is compare-and-swap.",
            "recompute `@{u}`, divergence, cache, and provenance",
            push_command,
        ),
        failures,
        "exact refresh and consolidated push",
    )
    require_ordered_contract_anchors(
        skill_root / "references/commit-construction.md",
        (
            "do not probe for absence before create",
            "git -C <repo> update-ref --no-deref <backup-ref> <old-head> <null-oid>",
            "The null old value makes it create-only",
            "Never fall back to an unconditional `update-ref`.",
            "## Atomically Update And Verify Branch",
            "git -C <repo> update-ref --no-deref <branch-ref> <new-commit> <old-head>",
            "If verification fails before push, restore with compare-and-swap",
            "git -C <repo> update-ref --no-deref <branch-ref> <old-head> <new-commit>",
        ),
        failures,
        "create-only backup ref",
    )
    require_ordered_contract_anchors(
        skill_root / "references/safe-git-values-and-metadata.md",
        (
            "## Object Format And OIDs",
            "git rev-parse --show-object-format",
            "Accept only `sha1`/40 hex or `sha256`/64 hex",
            "same-width all-zero null OID",
            "Recheck before commit creation, network access, each ref mutation, and final proof",
        ),
        failures,
        "object-format OID",
    )
    require_ordered_contract_anchors(
        skill_root / "references/safe-git-values-and-metadata.md",
        (
            "Require direct-OID `branchRef`",
            "git symbolic-ref --quiet <branch-ref>",
            "must classify it non-symbolic",
            "git rev-parse --verify <branch-ref>",
            "must equal frozen `HEAD`",
            "Recheck before source use or mutation",
            "symbolic/uncertain state stops",
            "Branch CAS must use `update-ref --no-deref`",
        ),
        failures,
        "direct branch ref",
    )
    require_ordered_contract_anchors(
        skill_root / "references/baseline-and-preflight.md",
        (
            "## Required Git Facts",
            "git -C <repo> rev-parse --show-object-format",
            "git -C <repo> symbolic-ref --quiet HEAD",
            "git -C <repo> rev-parse --verify HEAD",
        ),
        failures,
        "object format before ref and OID reads",
    )
    require_ordered_contract_anchors(
        skill_root / "references/repository-and-remote-targets.md",
        (
            "## Direct Submit Preflight",
            push_command,
            "the exact frozen pre-push hook identity and action",
            "query every authorized target",
            "Push authority never grants fetch",
        ),
        failures,
        "direct push closure and verification",
    )
    direct_push_text = (
        skill_root / "references/repository-and-remote-targets.md"
    ).read_text(encoding="utf-8")
    consolidated_push_text = (
        skill_root / "references/consolidation-and-push.md"
    ).read_text(encoding="utf-8")
    if direct_push_text.count(push_command) != 1 or consolidated_push_text.count(push_command) != 1:
        failures.append("direct and consolidated push owners must each contain the exact closed push argv once")
    traceable_text = "\n".join(
        path.read_text(encoding="utf-8") for path in skill_root.rglob("*.md")
    )
    if re.search(r"\bfetch\s+--prune\s+<remote>", traceable_text):
        failures.append("traceable-git-submit must not restore broad fetch --prune <remote>")
    branch_restore = "git -C <repo> update-ref --no-deref <branch-ref> <old-head> <new-commit>"
    checkpoint_text = (
        skill_root / "references/checkpoint-provenance.md"
    ).read_text(encoding="utf-8")
    if checkpoint_text.count(branch_restore) != 1:
        failures.append("checkpoint persistence recovery must contain the exact no-deref branch restore once")

    checkpoint_execution = (
        skill_root / "references/checkpoint-execution.md"
    ).read_text(encoding="utf-8")
    checkpoint_commit_tree = (
        "git -C <repo> commit-tree <staged-tree-sha> -p <parent-sha>"
    )
    checkpoint_branch_cas = (
        "git -C <repo> update-ref --no-deref <branch-ref> "
        "<candidate-commit-sha> <parent-sha>"
    )
    if checkpoint_execution.count(checkpoint_commit_tree) != 1:
        failures.append(
            "checkpoint execution must construct exactly one candidate from stagedTreeSha"
        )
    if checkpoint_execution.count(checkpoint_branch_cas) != 1:
        failures.append(
            "checkpoint execution must install exactly one candidate with branch compare-and-swap"
        )
    if re.search(
        r"^git -C <repo> commit(?:\s|$)", checkpoint_execution, re.MULTILINE
    ):
        failures.append("checkpoint execution must never prescribe ordinary git commit")

    push_binding_path = (
        skill_root / "references/repository-and-remote-targets.md"
    )
    require_ordered_contract_anchors(
        push_binding_path,
        (
            "a configured remote explicitly named in the current request",
            "`branch.<branch>.pushRemote` when present",
            "`remote.pushDefault` when present",
            "current `upstreamRemote`",
        ),
        failures,
        "effective push-remote precedence",
    )
    push_binding_text = push_binding_path.read_text(encoding="utf-8")
    normalized_push_binding = " ".join(push_binding_text.split())
    for anchor in (
        "`upstreamRemote` comes only from `branch.<branch>.remote` and owns `@{u}` and refresh",
        "Resolve effective `pushRemote` independently",
        "Freeze `pushRemote`, resolution source, `mergeRef`, branch, and upstream identity separately",
        "Refresh still uses `upstreamRemote`",
        "`pushRemote != upstreamRemote`",
    ):
        if " ".join(anchor.split()) not in normalized_push_binding:
            failures.append(
                f"{display_path(push_binding_path)} is missing distinct push/upstream identity contract {anchor!r}"
            )

    provenance_binding_path = (
        skill_root / "references/post-consolidation-recovery.md"
    )
    require_ordered_contract_anchors(
        provenance_binding_path,
        (
            "Local-only consolidation persists the initial\n`pushTargetState.state == unbound`",
            "may\nthen transition once to:",
            '"pushTargetState": {\n    "state": "bound"',
            "Never overwrite or rebind a bound record",
        ),
        failures,
        "one-time push-target binding",
    )
    provenance_binding_text = provenance_binding_path.read_text(encoding="utf-8")
    if provenance_binding_text.count('"state": "bound"') != 1:
        failures.append("push-target binding must define exactly one canonical bound state")
    if (
        "`post-consolidation-recovery.md` owns the one-time\n`unbound` to `bound` transition"
        not in checkpoint_text
    ):
        failures.append(
            "checkpoint provenance must delegate the one-time unbound-to-bound transition"
        )
    if "retain `pushTargetState.state == unbound`" not in consolidated_push_text:
        failures.append("local-only consolidation must retain unbound push-target state")

    hostile_path = skill_root / "references/safe-git-values-and-metadata.md"
    require_ordered_contract_anchors(
        hostile_path,
        (
            "require strict UTF-8",
            "invalid/overlong/surrogate encodings",
            "NUL, CR, LF, ASCII C0",
            "DEL, C1, `U+2028`, `U+2029`",
            "`Cc`, `Cf`, `Zl`, and `Zp`",
        ),
        failures,
        "hostile Git metadata scalar rejection",
    )
    if re.search(
        r"git[^\n]*(?:log|show|for-each-ref)[^\n]*%s",
        consolidated_push_text,
        re.IGNORECASE,
    ):
        failures.append("consolidation must not expose a percent-s Git metadata path")

    route_contracts = {
        "SKILL.md": (
            "references/safe-git-values-and-metadata.md",
            "references/commit-construction.md",
            "references/repository-and-remote-targets.md",
            "references/post-consolidation-recovery.md",
        ),
        "references/commit-construction.md": (
            "safe-git-values-and-metadata.md",
        ),
        "references/repository-and-remote-targets.md": (
            "post-consolidation-recovery.md",
        ),
        "references/checkpoint-provenance.md": (
            "post-consolidation-recovery.md",
        ),
    }
    for relative_path, references in route_contracts.items():
        route_text = (skill_root / relative_path).read_text(encoding="utf-8")
        for reference in references:
            if reference not in route_text:
                failures.append(
                    f"{display_path(skill_root / relative_path)} does not route to {reference!r}"
                )
    if re.search(
        r"^git -C <repo> update-ref (?![^\n]*--no-deref(?:\s|$))[^\n]*<branch-ref>",
        traceable_text,
        re.MULTILINE,
    ):
        failures.append("every branch install or restore update-ref must use --no-deref")

    operand_scenarios = (
        ("normal-ref", "ref", "refs/heads/release-1", True, True),
        ("shell-syntax-stays-literal", "ref", "refs/heads/release;$(touch-pwn)", True, True),
        ("shell-syntax-string-host-stops", "ref", "refs/heads/release;$(touch-pwn)", False, False),
        ("option-shaped-ref-stops", "ref", "refs/heads/-upload", True, False),
        ("control-character-stops", "ref", "refs/heads/release\nnext", True, False),
        ("c1-control-stops", "ref", "refs/heads/release\x85next", True, False),
        ("normal-remote", "remote", "origin", True, True),
        ("option-shaped-remote-stops", "remote", "--upload-pack=evil", True, False),
    )
    for name, kind, value, literal_arguments, expected in operand_scenarios:
        if safe_git_operand(kind, value, literal_arguments) != expected:
            failures.append(f"safe Git operand scenario {name!r} returned the wrong gate result")

    oid_scenarios = (
        ("sha1-oid", "a" * 40, "sha1", False, True),
        ("sha256-oid", "b" * 64, "sha256", False, True),
        ("wrong-width-stops", "a" * 40, "sha256", False, False),
        ("unknown-format-stops", "a" * 40, "future", False, False),
        ("null-object-stops", "0" * 40, "sha1", False, False),
        ("null-update-ref-sentinel", "0" * 64, "sha256", True, True),
    )
    for name, value, object_format, allow_null, expected in oid_scenarios:
        if safe_git_oid(value, object_format, allow_null=allow_null) != expected:
            failures.append(f"safe Git OID fixture {name!r} returned the wrong gate result")

    head_oid = "c" * 40
    branch_ref_scenarios = (
        ("direct-current", "non-symbolic", head_oid, head_oid, True, True),
        ("symbolic-same-oid-stops", "symbolic", head_oid, head_oid, True, False),
        ("uncertain-same-oid-stops", "uncertain", head_oid, head_oid, True, False),
        ("direct-oid-drift-stops", "non-symbolic", "d" * 40, head_oid, True, False),
        ("missing-source-recheck-stops", "non-symbolic", head_oid, head_oid, False, False),
    )
    for name, classification, resolved_oid, frozen_head, rechecked, expected in branch_ref_scenarios:
        if direct_branch_ref_gate(classification, resolved_oid, frozen_head, rechecked) != expected:
            failures.append(f"direct branch-ref fixture {name!r} returned the wrong gate result")

    transport_scenarios = (
        ("https", "https://example.test/org/repo.git", True),
        ("ssh", "ssh://git@example.test/org/repo.git", True),
        ("scp-like", "git@example.test:org/repo.git", True),
        ("plaintext-http", "http://example.test/org/repo.git", False),
        ("local-file", "file:///tmp/repo.git", False),
        ("remote-helper", "ext::sh -c exploit", False),
    )
    for name, value, expected in transport_scenarios:
        if safe_git_transport(value) != expected:
            failures.append(f"safe Git transport scenario {name!r} returned the wrong gate result")

    execution_envelope_scenarios = (
        ("benign-config", ("core.filemode", "remote.origin.url"), (), (), True),
        ("fsmonitor-stops", ("core.fsmonitor",), (), (), False),
        (
            "neutralized-fsmonitor",
            ("core.fsmonitor",),
            (),
            ("core.fsmonitor",),
            True,
        ),
        ("ssh-command-stops", ("core.sshCommand",), (), (), False),
        ("pager-command-stops", ("core.pager",), (), (), False),
        ("credential-helper-stops", ("credential.helper",), (), (), False),
        ("filter-process-stops", ("filter.lfs.process",), (), (), False),
        ("url-rewrite-stops", ("url.ssh://example/.insteadOf",), (), (), False),
        ("git-environment-stops", (), ("GIT_SSH_COMMAND",), (), False),
        ("pager-environment-stops", (), ("GIT_PAGER",), (), False),
    )
    for (
        name,
        config_keys,
        environment_names,
        handled_keys,
        expected,
    ) in execution_envelope_scenarios:
        if safe_git_execution_envelope(config_keys, environment_names, handled_keys) != expected:
            failures.append(
                f"safe Git execution-envelope scenario {name!r} returned the wrong gate result"
            )

    complete_cleanup = {field: True for field in CLEANUP_AUTHORITY_FIELDS}
    if not all_evidence(complete_cleanup, CLEANUP_AUTHORITY_FIELDS):
        failures.append("complete exact cleanup authority must permit cleanup")
    for missing_field in CLEANUP_AUTHORITY_FIELDS:
        incomplete = dict(complete_cleanup)
        incomplete[missing_field] = False
        if all_evidence(incomplete, CLEANUP_AUTHORITY_FIELDS):
            failures.append(
                f"cleanup scenario without {missing_field!r} must retain recovery state"
            )
    return (
        len(operand_scenarios)
        + len(oid_scenarios)
        + len(branch_ref_scenarios)
        + len(transport_scenarios)
        + len(execution_envelope_scenarios)
        + len(CLEANUP_AUTHORITY_FIELDS)
        + 11
    )


def check_external_action_scenarios(failures: list[str]) -> int:
    skill_path = REPOSITORY_ROOT / "skills" / "confirm-external-action" / "SKILL.md"
    contract = skill_path.read_text(encoding="utf-8")
    for anchor in (
        "acting account",
        "exact target",
        "normalized payload",
        "sensitive value",
        "cost",
        "idempotency key",
        "current user statement",
        "Do not automatically retry",
        "external system of record",
        "untrusted",
    ):
        if anchor.casefold() not in contract.casefold():
            failures.append(
                f"{display_path(skill_path)} is missing external-action contract {anchor!r}"
            )

    complete = {field: True for field in EXTERNAL_ACTION_ENVELOPE_FIELDS}
    if not all_evidence(complete, EXTERNAL_ACTION_ENVELOPE_FIELDS):
        failures.append("complete external action envelope must permit one execution")
    for missing_field in EXTERNAL_ACTION_ENVELOPE_FIELDS:
        incomplete = dict(complete)
        incomplete[missing_field] = False
        if all_evidence(incomplete, EXTERNAL_ACTION_ENVELOPE_FIELDS):
            failures.append(
                f"external-action scenario without {missing_field!r} must stop before mutation"
            )
    return len(EXTERNAL_ACTION_ENVELOPE_FIELDS) + 1


def rollback_gate(evidence: dict[str, bool]) -> bool:
    return all(evidence.get(field, False) for field in ROLLBACK_EVIDENCE_FIELDS)


def check_reversible_safety_scenarios(failures: list[str]) -> None:
    complete = {field: True for field in ROLLBACK_EVIDENCE_FIELDS}
    if not rollback_gate(complete):
        failures.append("complete rollback evidence must permit the execution phase")

    for missing_field in ROLLBACK_EVIDENCE_FIELDS:
        incomplete = dict(complete)
        incomplete[missing_field] = False
        if rollback_gate(incomplete):
            failures.append(
                f"rollback safety scenario without {missing_field!r} must stop before execution"
            )

    skill_root = REPOSITORY_ROOT / "skills" / "reversible-system-change"
    contract_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            skill_root / "SKILL.md",
            skill_root / "references" / "preflight-and-rollback.md",
            skill_root / "references" / "execution-and-verification.md",
        )
    )
    for evidence_label in (
        "identified",
        "present",
        "readable",
        "restore-validated",
        "rehearsed",
    ):
        if f"`{evidence_label}`" not in contract_text:
            failures.append(
                f"reversible-system-change is missing rollback evidence label {evidence_label!r}"
            )

    for phase_anchor in (
        "non-mutating workflow rehearsal",
        "isolated restore rehearsal",
        "rehearsal-write authority",
        "cannot affect active state or data",
    ):
        if phase_anchor.casefold() not in contract_text.casefold():
            failures.append(
                f"reversible-system-change is missing rehearsal phase contract {phase_anchor!r}"
            )


def parse_skill_frontmatter(path: Path, failures: list[str]) -> dict[str, str] | None:
    label = display_path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {label}: {error}")
        return None

    try:
        return parse_skill_frontmatter_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None


def check_skill_contracts(failures: list[str]) -> None:
    for skill_name in EXPECTED_DIRECT_SKILLS:
        skill_root = REPOSITORY_ROOT / "skills" / skill_name
        main_path = skill_root / "SKILL.md"
        fields = parse_skill_frontmatter(main_path, failures)
        if fields is None:
            continue
        if fields["name"] != skill_name:
            failures.append(
                f"{display_path(main_path)} name is {fields['name']!r}; expected {skill_name!r}"
            )
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]):
            failures.append(f"{display_path(main_path)} has a non-kebab-case name")
        if not fields["description"] or not fields["description"].isascii():
            failures.append(f"{display_path(main_path)} description must be non-empty English ASCII")

        main_text = main_path.read_text(encoding="utf-8")
        for reference in sorted((skill_root / "references").rglob("*.md")) if (skill_root / "references").is_dir() else ():
            relative_reference = reference.relative_to(skill_root).as_posix()
            if relative_reference not in main_text:
                failures.append(
                    f"{display_path(reference)} is not directly discoverable from {display_path(main_path)}"
                )

        metadata_path = skill_root / "agents" / "openai.yaml"
        try:
            metadata_text = metadata_path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {display_path(metadata_path)}: {error}")
        else:
            try:
                metadata = parse_agent_metadata_document(
                    metadata_text,
                    display_path(metadata_path),
                    allow_policy=skill_name == "using-axiom",
                )
            except CanonicalYamlError as error:
                failures.append(str(error))
            else:
                interface = metadata["interface"]
                if not 25 <= len(interface["short_description"]) <= 64:
                    failures.append(
                        f"{display_path(metadata_path)} short_description must be 25-64 characters"
                    )
                if f"${skill_name}" not in interface["default_prompt"]:
                    failures.append(
                        f"{display_path(metadata_path)} default_prompt must mention ${skill_name}"
                    )

    for path in sorted((REPOSITORY_ROOT / "skills").rglob("*.md")):
        byte_count = len(path.read_bytes())
        if byte_count >= INSTRUCTION_MAX_BYTES:
            failures.append(
                f"{display_path(path)} is {byte_count} bytes; instruction files must stay below "
                f"{INSTRUCTION_MAX_BYTES}"
            )

    front_door = (REPOSITORY_ROOT / "skills" / "using-axiom" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    route_section = front_door.split("## Bundled Routes", 1)[-1].split("\n## ", 1)[0]
    declared_routes = tuple(re.findall(r"^- `([a-z0-9-]+)`: ", route_section, re.MULTILINE))
    expected_routes = tuple(
        skill_name for skill_name in EXPECTED_DIRECT_SKILLS if skill_name != "using-axiom"
    )
    if tuple(sorted(declared_routes)) != expected_routes:
        failures.append(
            "using-axiom route list is not the exact direct task-skill set: "
            + ", ".join(declared_routes)
        )

    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    shared_section = readme.split("### Shared skills", 1)[-1].split("\n### ", 1)[0]
    readme_skills = tuple(
        re.findall(r"^- `([a-z0-9-]+)`,", shared_section, re.MULTILINE)
    )
    if readme_skills != EXPECTED_README_SKILLS:
        failures.append(
            "README Shared skills list is not the expected parseable ordered set: "
            + ", ".join(readme_skills)
        )


class DuplicateJsonKeyError(ValueError):
    """Raised when a protected JSON object repeats a key."""


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


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
        value = json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
    except json.JSONDecodeError as error:
        failures.append(
            f"invalid JSON in {label}:{error.lineno}:{error.colno}: {error.msg}"
        )
        return None
    except DuplicateJsonKeyError as error:
        failures.append(f"invalid JSON in {label}: {error}")
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


def check_release_version_surfaces(failures: list[str]) -> None:
    """Derive every current-release document contract from RELEASE_VERSION."""
    release_tag = f"v{RELEASE_VERSION}"
    release_path = REPOSITORY_ROOT / CURRENT_RELEASE_NOTES
    surface_contracts = (
        (
            README_PATH,
            (release_tag, f"]({CURRENT_RELEASE_NOTES})"),
        ),
        (
            REPOSITORY_ROOT / "CHANGELOG.md",
            (f"## {RELEASE_VERSION} - ",),
        ),
        (
            REPOSITORY_ROOT / "docs" / "compatibility.md",
            (
                f"The Git record for `{release_tag}` reports:",
                f"](releases/{release_tag}.md)",
            ),
        ),
        (
            release_path,
            (f"# Axiom {release_tag}", f"Version `{RELEASE_VERSION}`"),
        ),
    )
    for path, anchors in surface_contracts:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {display_path(path)}: {error}")
            continue
        for anchor in anchors:
            if anchor not in text:
                failures.append(
                    f"{display_path(path)} is missing current release anchor {anchor!r} "
                    f"derived from RELEASE_VERSION={RELEASE_VERSION!r}"
                )


def exact_json_object(
    value: Any,
    label: str,
    expected_keys: frozenset[str],
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    actual_keys = set(value)
    unknown = sorted(actual_keys - expected_keys)
    missing = sorted(expected_keys - actual_keys)
    if unknown:
        failures.append(f"{label} contains unowned fields: {', '.join(unknown)}")
    if missing:
        failures.append(f"{label} is missing contract fields: {', '.join(missing)}")
    return value


def require_json_strings(
    mapping: dict[str, Any],
    fields: frozenset[str],
    label: str,
    failures: list[str],
) -> None:
    for field in sorted(fields):
        if type(mapping.get(field)) is not str or not mapping[field]:
            failures.append(f"{label}.{field} must be a non-empty string")


def require_json_string_list(value: Any, label: str, failures: list[str]) -> None:
    if type(value) is not list or not value:
        failures.append(f"{label} must be a non-empty array")
        return
    if any(type(item) is not str or not item for item in value):
        failures.append(f"{label} entries must be non-empty strings")


def exact_single_plugin(
    document: dict[str, Any],
    label: str,
    expected_keys: frozenset[str],
    failures: list[str],
) -> dict[str, Any] | None:
    plugins = document.get("plugins")
    if type(plugins) is not list or len(plugins) != 1:
        failures.append(f"{label}.plugins must contain exactly one plugin object")
        return None
    return exact_json_object(plugins[0], f"{label}.plugins[0]", expected_keys, failures)


def check_manifest_capability_schema(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    """Reject every manifest capability not owned by Axiom's current package contract."""
    codex_path = ".codex-plugin/plugin.json"
    codex = documents.get(codex_path)
    if codex is not None:
        exact_json_object(codex, codex_path, CODEX_MANIFEST_KEYS, failures)
        require_json_strings(
            codex,
            frozenset(
                {
                    "name",
                    "version",
                    "description",
                    "homepage",
                    "repository",
                    "license",
                    "skills",
                    "hooks",
                }
            ),
            codex_path,
            failures,
        )
        author = exact_json_object(codex.get("author"), f"{codex_path}.author", AUTHOR_KEYS, failures)
        if author is not None:
            require_json_strings(author, AUTHOR_KEYS, f"{codex_path}.author", failures)
        interface = exact_json_object(
            codex.get("interface"), f"{codex_path}.interface", CODEX_INTERFACE_KEYS, failures
        )
        if interface is not None:
            require_json_strings(
                interface,
                frozenset(CODEX_INTERFACE_KEYS - {"capabilities", "defaultPrompt"}),
                f"{codex_path}.interface",
                failures,
            )
            require_json_string_list(
                interface.get("capabilities"), f"{codex_path}.interface.capabilities", failures
            )
            if interface.get("capabilities") != ["Interactive"]:
                failures.append(
                    f"{codex_path}.interface.capabilities must remain ['Interactive']"
                )
            require_json_string_list(
                interface.get("defaultPrompt"), f"{codex_path}.interface.defaultPrompt", failures
            )
        require_json_string_list(codex.get("keywords"), f"{codex_path}.keywords", failures)

    claude_path = ".claude-plugin/plugin.json"
    claude = documents.get(claude_path)
    if claude is not None:
        exact_json_object(claude, claude_path, CLAUDE_MANIFEST_KEYS, failures)
        require_json_strings(
            claude,
            frozenset(CLAUDE_MANIFEST_KEYS - {"author", "keywords"}),
            claude_path,
            failures,
        )
        author = exact_json_object(
            claude.get("author"), f"{claude_path}.author", AUTHOR_KEYS, failures
        )
        if author is not None:
            require_json_strings(author, AUTHOR_KEYS, f"{claude_path}.author", failures)
        require_json_string_list(claude.get("keywords"), f"{claude_path}.keywords", failures)

    codex_marketplace_path = ".agents/plugins/marketplace.json"
    codex_marketplace = documents.get(codex_marketplace_path)
    if codex_marketplace is not None:
        exact_json_object(
            codex_marketplace, codex_marketplace_path, CODEX_MARKETPLACE_KEYS, failures
        )
        require_json_strings(
            codex_marketplace, frozenset({"name"}), codex_marketplace_path, failures
        )
        interface = exact_json_object(
            codex_marketplace.get("interface"),
            f"{codex_marketplace_path}.interface",
            frozenset({"displayName"}),
            failures,
        )
        if interface is not None:
            require_json_strings(
                interface,
                frozenset({"displayName"}),
                f"{codex_marketplace_path}.interface",
                failures,
            )
        entry = exact_single_plugin(
            codex_marketplace,
            codex_marketplace_path,
            CODEX_MARKETPLACE_PLUGIN_KEYS,
            failures,
        )
        if entry is not None:
            require_json_strings(
                entry,
                frozenset({"name", "category"}),
                f"{codex_marketplace_path}.plugins[0]",
                failures,
            )
            source = exact_json_object(
                entry.get("source"),
                f"{codex_marketplace_path}.plugins[0].source",
                frozenset({"source", "path"}),
                failures,
            )
            if source is not None:
                require_json_strings(
                    source,
                    frozenset({"source", "path"}),
                    f"{codex_marketplace_path}.plugins[0].source",
                    failures,
                )
                if source != {"source": "local", "path": EXPECTED_PLUGIN_ROOT}:
                    failures.append(
                        f"{codex_marketplace_path}.plugins[0].source must remain the "
                        "owned local plugin root"
                    )
            policy = exact_json_object(
                entry.get("policy"),
                f"{codex_marketplace_path}.plugins[0].policy",
                frozenset(EXPECTED_CODEX_POLICY),
                failures,
            )
            if policy is not None:
                require_json_strings(
                    policy,
                    frozenset(EXPECTED_CODEX_POLICY),
                    f"{codex_marketplace_path}.plugins[0].policy",
                    failures,
                )
                if policy != EXPECTED_CODEX_POLICY:
                    failures.append(
                        f"{codex_marketplace_path}.plugins[0].policy must remain the "
                        "owned install policy"
                    )

    claude_marketplace_path = ".claude-plugin/marketplace.json"
    claude_marketplace = documents.get(claude_marketplace_path)
    if claude_marketplace is not None:
        exact_json_object(
            claude_marketplace,
            claude_marketplace_path,
            CLAUDE_MARKETPLACE_KEYS,
            failures,
        )
        require_json_strings(
            claude_marketplace,
            frozenset({"name", "description"}),
            claude_marketplace_path,
            failures,
        )
        owner = exact_json_object(
            claude_marketplace.get("owner"),
            f"{claude_marketplace_path}.owner",
            AUTHOR_KEYS,
            failures,
        )
        if owner is not None:
            require_json_strings(
                owner, AUTHOR_KEYS, f"{claude_marketplace_path}.owner", failures
            )
        entry = exact_single_plugin(
            claude_marketplace,
            claude_marketplace_path,
            CLAUDE_MARKETPLACE_PLUGIN_KEYS,
            failures,
        )
        if entry is not None:
            require_json_strings(
                entry,
                frozenset({"name", "source", "category"}),
                f"{claude_marketplace_path}.plugins[0]",
                failures,
            )
            require_json_string_list(
                entry.get("tags"),
                f"{claude_marketplace_path}.plugins[0].tags",
                failures,
            )


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
        if STRICT_SEMVER.fullmatch(version) is None:
            failures.append(
                f"{relative_path} version {version!r} is not strict SemVer"
            )

    if len(versions) == len(MANIFEST_FILES) and len(set(versions.values())) != 1:
        rendered = ", ".join(f"{path}={version!r}" for path, version in versions.items())
        failures.append(f"plugin manifest versions disagree: {rendered}")

    for relative_path, version in versions.items():
        if version != RELEASE_VERSION:
            failures.append(
                f"{relative_path} version is {version!r}; publication requires {RELEASE_VERSION!r}"
            )


def check_codex_interface(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    relative_path = ".codex-plugin/plugin.json"
    document = documents.get(relative_path)
    if document is None:
        return
    interface = document.get("interface")
    if not isinstance(interface, dict):
        failures.append(f"{relative_path} interface must be an object")
        return
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list):
        failures.append(f"{relative_path} interface.defaultPrompt must be an array")
        return
    if not 1 <= len(prompts) <= CODEX_DEFAULT_PROMPT_MAX_ITEMS:
        failures.append(
            f"{relative_path} interface.defaultPrompt must contain 1-"
            f"{CODEX_DEFAULT_PROMPT_MAX_ITEMS} entries; found {len(prompts)}"
        )
    for index, prompt in enumerate(prompts):
        label = f"{relative_path} interface.defaultPrompt[{index}]"
        if not isinstance(prompt, str) or not prompt.strip():
            failures.append(f"{label} must be a non-empty string")
        elif len(prompt) > CODEX_DEFAULT_PROMPT_MAX_CHARACTERS:
            failures.append(
                f"{label} is {len(prompt)} characters; Codex caps starter prompts at "
                f"{CODEX_DEFAULT_PROMPT_MAX_CHARACTERS}"
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


def check_distribution_identity(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    codex_manifest_path = ".codex-plugin/plugin.json"
    codex_manifest = documents.get(codex_manifest_path)
    if codex_manifest is not None:
        if codex_manifest.get("name") != EXPECTED_PLUGIN_NAME:
            failures.append(f"{codex_manifest_path} name must be {EXPECTED_PLUGIN_NAME!r}")
        if codex_manifest.get("description") != EXPECTED_TAGLINE:
            failures.append(f"{codex_manifest_path} description must be {EXPECTED_TAGLINE!r}")
        interface = codex_manifest.get("interface")
        if isinstance(interface, dict):
            if interface.get("displayName") != EXPECTED_DISPLAY_NAME:
                failures.append(
                    f"{codex_manifest_path} interface.displayName must be {EXPECTED_DISPLAY_NAME!r}"
                )
            if interface.get("category") != EXPECTED_CODEX_CATEGORY:
                failures.append(
                    f"{codex_manifest_path} interface.category must be {EXPECTED_CODEX_CATEGORY!r}"
                )

    claude_manifest_path = ".claude-plugin/plugin.json"
    claude_manifest = documents.get(claude_manifest_path)
    if claude_manifest is not None:
        if claude_manifest.get("name") != EXPECTED_PLUGIN_NAME:
            failures.append(f"{claude_manifest_path} name must be {EXPECTED_PLUGIN_NAME!r}")
        if claude_manifest.get("displayName") != EXPECTED_DISPLAY_NAME:
            failures.append(
                f"{claude_manifest_path} displayName must be {EXPECTED_DISPLAY_NAME!r}"
            )
        if claude_manifest.get("description") != EXPECTED_TAGLINE:
            failures.append(f"{claude_manifest_path} description must be {EXPECTED_TAGLINE!r}")

    codex_marketplace_path = ".agents/plugins/marketplace.json"
    codex_marketplace = documents.get(codex_marketplace_path)
    if codex_marketplace is not None:
        if codex_marketplace.get("name") != EXPECTED_PLUGIN_NAME:
            failures.append(
                f"{codex_marketplace_path} name must be {EXPECTED_PLUGIN_NAME!r}"
            )
        interface = codex_marketplace.get("interface")
        if not isinstance(interface, dict) or interface.get("displayName") != EXPECTED_DISPLAY_NAME:
            failures.append(
                f"{codex_marketplace_path} interface.displayName must be {EXPECTED_DISPLAY_NAME!r}"
            )
        entry = marketplace_plugin(codex_marketplace, codex_marketplace_path, failures)
        if entry is not None:
            if entry.get("policy") != EXPECTED_CODEX_POLICY:
                failures.append(
                    f"{codex_marketplace_path} axiom policy must be {EXPECTED_CODEX_POLICY!r}"
                )
            if entry.get("category") != EXPECTED_CODEX_CATEGORY:
                failures.append(
                    f"{codex_marketplace_path} axiom category must be {EXPECTED_CODEX_CATEGORY!r}"
                )

    claude_marketplace_path = ".claude-plugin/marketplace.json"
    claude_marketplace = documents.get(claude_marketplace_path)
    if claude_marketplace is not None:
        if claude_marketplace.get("name") != EXPECTED_PLUGIN_NAME:
            failures.append(
                f"{claude_marketplace_path} name must be {EXPECTED_PLUGIN_NAME!r}"
            )
        entry = marketplace_plugin(claude_marketplace, claude_marketplace_path, failures)
        if entry is not None and entry.get("category") != EXPECTED_CLAUDE_CATEGORY:
            failures.append(
                f"{claude_marketplace_path} axiom category must be {EXPECTED_CLAUDE_CATEGORY!r}"
            )


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

    rejected = 0
    for name, fixture, expected in fixtures:
        fixture_failures: list[str] = []
        check_exact_hook_shapes(fixture, fixture_failures)
        if any(expected in failure for failure in fixture_failures):
            rejected += 1
        else:
            failures.append(f"hook lifecycle negative fixture {name!r} was accepted")

    positive_failures: list[str] = []
    check_exact_hook_shapes(documents, positive_failures)
    if positive_failures:
        failures.append(
            "checked-in hook lifecycle control failed: "
            + "; ".join(positive_failures)
        )
    return rejected + 1


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


def check_compatibility_evidence(failures: list[str]) -> tuple[int, int]:
    """Execute the standalone standard-library evidence validator."""
    validator = REPOSITORY_ROOT / "scripts" / "check-compatibility-evidence.py"
    try:
        result = subprocess.run(
            [sys.executable, str(validator), "--self-test"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        failures.append(f"compatibility evidence validator could not run: {error}")
        return 0, 0
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        failures.append(
            "compatibility evidence validator failed"
            + (f": {detail}" if detail else "")
        )
        return 0, 0
    pattern = re.compile(
        rf"^Compatibility evidence validation passed: ([0-9]+) records, "
        rf"([0-9]+) negative fixtures, current release v{re.escape(RELEASE_VERSION)} "
        rf"STATIC-ONLY\.$"
    )
    match = pattern.fullmatch(result.stdout.strip())
    if match is None:
        failures.append(
            "compatibility evidence validator returned an unrecognized success summary"
        )
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def main() -> int:
    failures: list[str] = []
    check_required_files(failures)
    check_release_version_surfaces(failures)
    validator_fixture_count = check_validator_negative_fixtures(failures)
    evidence_record_count, evidence_fixture_count = check_compatibility_evidence(failures)

    documents: dict[str, dict[str, Any]] = {}
    for relative_path in JSON_FILES:
        document = load_json(REPOSITORY_ROOT / relative_path, failures)
        if document is not None:
            documents[relative_path] = document

    check_manifest_capability_schema(documents, failures)
    manifest_schema_fixture_count = check_manifest_schema_fixtures(documents, failures)
    check_manifest_versions(documents, failures)
    check_codex_interface(documents, failures)
    check_distribution_identity(documents, failures)
    check_shared_source_roots(documents, failures)
    check_declared_hook_paths(documents, failures)
    check_exact_hook_shapes(documents, failures)
    hook_lifecycle_fixture_count = check_hook_lifecycle_fixtures(documents, failures)
    check_documented_hook_commands(documents, failures)
    action_pin_count = check_github_action_pins(failures)
    distribution_workflow_document = check_distribution_workflow_contract(failures)
    release_workflow_text = check_release_signature_workflow_contract(failures)
    pull_request_fixture_count = check_pull_request_validation_fixtures(
        distribution_workflow_document,
        release_workflow_text,
        documents,
        failures,
    )
    release_provenance_fixture_count = check_release_script_runtime_contract(
        release_workflow_text,
        failures,
    )
    check_readme_lifecycle_commands(failures)
    check_packaged_skills(failures)
    check_skill_contracts(failures)
    check_routing_source_contracts(failures)
    cross_route_contract_count = check_cross_route_resume_contracts(failures)
    check_routing_scenarios(failures)
    traceable_security_scenarios = check_traceable_security_contracts(failures)
    external_action_scenarios = check_external_action_scenarios(failures)
    check_reversible_safety_scenarios(failures)
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
        f"{markdown_count} Markdown files, {len(ROUTING_SCENARIOS)} offline route contract fixtures, "
        f"{traceable_security_scenarios} traceable-Git contract fixtures, "
        f"{external_action_scenarios} external-action gate fixtures, "
        f"{len(ROLLBACK_EVIDENCE_FIELDS) + 1} rollback gate fixtures, "
        f"{cross_route_contract_count} source-linked cross-route/resume contracts, "
        f"{validator_fixture_count} validator parser fixtures, version {RELEASE_VERSION}, "
        f"{evidence_record_count} compatibility evidence records, "
        f"{evidence_fixture_count} compatibility evidence negative fixtures, "
        f"{manifest_schema_fixture_count} manifest schema fixtures, "
        f"{hook_lifecycle_fixture_count} hook lifecycle fixtures, "
        f"{pull_request_fixture_count} pull-request event-graph fixtures, "
        f"{release_provenance_fixture_count} release-provenance fixtures, "
        f"{action_pin_count} immutable action pins, hooks, and packaged skills."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
