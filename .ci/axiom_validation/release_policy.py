"""Release workflow structure and exact-script execution policy."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .context import REPOSITORY_ROOT, display_path
from .release import (
    CREATED_TAG_CHECK,
    PUBLISHED_RELEASE_CHECK,
    RELEASE_BRANCH_CHECK,
    RELEASE_BRANCH_REF,
    RELEASE_BRANCH_ROOT,
)
from .release_versions import PRODUCTION_RELEASE_VERSION_PATTERN
from .yaml_subset import CanonicalYamlError, CanonicalYamlScalar, parse_canonical_yaml_document


def require_ordered_contract_anchors(
    path: Path,
    anchors: tuple[str, ...],
    failures: list[str],
    contract_name: str,
) -> None:
    """Require ordered phrases in a workflow or script that the release path depends on."""
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

    def scalar_values(value: Any) -> list[str] | None:
        if not isinstance(value, list) or any(
            not isinstance(item, CanonicalYamlScalar) for item in value
        ):
            return None
        return [item.value for item in value]

    def scalar(value: Any) -> str | None:
        return value.value if isinstance(value, CanonicalYamlScalar) else None

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
        inputs = manual.get("inputs") if isinstance(manual, dict) else None
        phase = inputs.get("phase") if isinstance(inputs, dict) else None
        if (
            not isinstance(manual, dict)
            or set(manual) != {"inputs"}
            or not isinstance(inputs, dict)
            or set(inputs) != {"phase"}
            or not isinstance(phase, dict)
            or set(phase) != {"description", "required", "type", "options"}
            or scalar(phase.get("required")) != "true"
            or scalar(phase.get("type")) != "choice"
            or scalar_values(phase.get("options")) != ["release-branch", "published-release"]
        ):
            failures.append(
                f"{label} workflow_dispatch must select only release-branch or published-release"
            )

    context_name = (
        "${{ github.event_name == 'push' && github.ref == 'refs/heads/main' && "
        "'Verify signed main history' || github.event_name == 'push' && "
        "startsWith(github.ref, 'refs/tags/') && 'Verify created release tag' || "
        "github.event_name == 'workflow_dispatch' && inputs.phase == 'release-branch' && "
        "'Verify release branch commit' || "
        "'Observe published immutable release' }}"
    )
    jobs = document.get("jobs")
    job = jobs.get("verify-github-signature") if isinstance(jobs, dict) else None
    job_name = job.get("name") if isinstance(job, dict) else None
    if not isinstance(job_name, CanonicalYamlScalar) or job_name.value != context_name:
        failures.append(f"{label} must map events to four distinct stable check contexts")
    runner = job.get("runs-on") if isinstance(job, dict) else None
    if not isinstance(runner, CanonicalYamlScalar) or runner.value != "ubuntu-24.04":
        failures.append(f"{label} must use the fixed ubuntu-24.04 runner")
    for check_context in (
        "Verify signed main history",
        CREATED_TAG_CHECK,
        RELEASE_BRANCH_CHECK,
        PUBLISHED_RELEASE_CHECK,
    ):
        owners = [
            candidate
            for candidate in sorted((REPOSITORY_ROOT / ".github" / "workflows").glob("*.y*ml"))
            if check_context in candidate.read_text(encoding="utf-8")
        ]
        if owners != [path] or text.count(check_context) != 1:
            failures.append(
                f"release check context {check_context!r} must have exactly one workflow owner"
            )

    canonical_version_declaration = (
        f"const productionReleaseVersion = /^{PRODUCTION_RELEASE_VERSION_PATTERN}$/;"
    )
    root_declaration = f'const releaseBranchRoot = "{RELEASE_BRANCH_ROOT}";'
    require_ordered_contract_anchors(
        path,
        (
            "const defaultRef = `refs/heads/${defaultBranch}`;",
            canonical_version_declaration,
            f'const releaseBranchRef = "{RELEASE_BRANCH_REF}";',
            root_declaration,
            "function releaseTagVersion(tagName)",
            "return productionReleaseVersion.test(version) ? version : null;",
            "function isSingleTagCreation(payload)",
            "payload.created === true",
            "payload.deleted === false",
            "payload.forced === false",
            "/^0{40}$/.test(payload.before)",
            "/^(?!0{40}$)[0-9a-f]{40}$/i.test(payload.after)",
            "function failClosedRefMutation(reason)",
            "true server-side prevention still depends on a GitHub ruleset",
            "async function readJsonAtCommit(path, commitSha)",
            "async function stampedVersionAtCommit(commitSha)",
            '"plugin/.claude-plugin/plugin.json"',
            '"plugin/.codex-plugin/plugin.json"',
            "!productionReleaseVersion.test(version)",
            "versions[0] !== versions[1]",
            "async function peelRefToCommit(qualifiedRef, expectedObjectSha = null)",
            "object.sha !== expectedObjectSha",
            "let targetPhase;",
            "context.payload.release?.tag_name",
            "context.ref !== targetRef",
            "GitHub Release tag ${targetRef} does not match event ref ${context.ref}.",
            "targetCommit = await peelRefToCommit(targetRef);",
            "context.ref === defaultRef",
            'targetPhase = "main-history";',
            'context.ref.startsWith("refs/tags/")',
            'targetPhase = "created-tag";',
            "!isSingleTagCreation(context.payload)",
            "targetCommit = await peelRefToCommit(targetRef, context.payload.after);",
            "const manualPhase = context.payload.inputs?.phase;",
            '!["release-branch", "published-release"].includes(manualPhase)',
            'dispatchedVersion = releaseTagVersion(context.ref.slice("refs/tags/".length));',
            'targetRef = manualPhase === "release-branch" ? releaseBranchRef : context.ref;',
            'if (targetPhase === "release-branch")',
            "const stampedVersion = await stampedVersionAtCommit(targetCommit);",
            "stampedVersion !== dispatchedVersion",
            "historyBase = releaseBranchRoot;",
            'targetPhase === "published-release"',
            "github.rest.repos.getReleaseByTag",
            "publishedRelease.immutable !== true",
            "Release event ID does not match the live immutable release",
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
        root_declaration,
        "function releaseTagVersion(tagName)",
        "function isSingleTagCreation(payload)",
        "function failClosedRefMutation(reason)",
        "async function stampedVersionAtCommit(commitSha)",
    ):
        if text.count(owner) != 1:
            failures.append(f"{label} must contain exactly one critical owner {owner!r}")
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
