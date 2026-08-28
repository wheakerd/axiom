"""Release workflow structure and exact-script execution policy."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from .context import REPOSITORY_ROOT, display_path
from .release_versions import PRODUCTION_RELEASE_VERSION_PATTERN
from .routing_contracts import require_ordered_contract_anchors
from .yaml_subset import CanonicalYamlError, CanonicalYamlScalar, parse_canonical_yaml_document


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

    canonical_version_declaration = (
        f"const productionReleaseVersion = /^{PRODUCTION_RELEASE_VERSION_PATTERN}$/;"
    )
    require_ordered_contract_anchors(
        path,
        (
            "const defaultRef = `refs/heads/${defaultBranch}`;",
            canonical_version_declaration,
            'const releaseBranchPrefix = "refs/heads/release/";',
            "function releaseTagVersion(tagName)",
            "return productionReleaseVersion.test(version) ? version : null;",
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
            "!productionReleaseVersion.test(version)",
            "versions[0] !== versions[1]",
            "async function peelRefToCommit(qualifiedRef, expectedObjectSha = null)",
            "object.sha !== expectedObjectSha",
            "context.payload.release?.tag_name",
            "const version = releaseTagVersion(tagName);",
            "context.ref !== targetRef",
            "GitHub Release tag ${targetRef} does not match event ref ${context.ref}.",
            "targetCommit = await peelRefToCommit(targetRef);",
            "context.ref === defaultRef",
            'context.ref.startsWith("refs/tags/")',
            "!isSingleTagCreation(context.payload)",
            "failClosedTagMutation(",
            "targetCommit = await peelRefToCommit(targetRef, context.payload.after);",
            "Manual tag verification requires one exact stable numeric production release tag",
            "context.ref.startsWith(releaseBranchPrefix)",
            "const candidateTagName = context.ref.slice(releaseBranchPrefix.length);",
            "Manual release-candidate verification requires",
            "Unexpected manual verification ref",
            "const packageVersion = await packageVersionAtCommit(targetCommit);",
            "packageVersion !== targetVersion",
            "names version ${targetVersion}, but manifests declare ${packageVersion}",
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
        canonical_version_declaration,
        "function releaseTagVersion(tagName)",
        "function isSingleTagCreation(payload)",
        "function failClosedTagMutation(reason)",
        "async function packageVersionAtCommit(commitSha)",
    ):
        if text.count(owner) != 1:
            failures.append(f"{label} must contain exactly one critical owner {owner!r}")
    if "strictSemVer" in text:
        failures.append(f"{label} retains the superseded full-SemVer policy owner")
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


def execute_release_workflow_script(
    script: str,
    scenarios: tuple[dict[str, Any], ...],
    failures: list[str],
    label: str,
    harness: str,
) -> dict[str, dict[str, Any]] | None:
    payload = {"script": script, "scenarios": scenarios}
    try:
        result = subprocess.run(
            ["node", "-e", harness],
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
    harness: str,
) -> int:
    results = execute_release_workflow_script(
        script,
        scenarios,
        failures,
        label,
        harness,
    )
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
