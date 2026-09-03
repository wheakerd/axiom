"""Repository layout, release-document, skill, and evidence policy."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from .context import (
    CURRENT_RELEASE_NOTES,
    README_PATH,
    RELEASE_VERSION,
    REPOSITORY_ROOT,
    display_path,
)
from .release_evidence import render_release_body
from .yaml_subset import CanonicalYamlError, parse_agent_metadata_document, parse_skill_frontmatter_document

_BASE_REQUIRED_PUBLIC_FILES = (
    "README.md",
    ".github/CODEOWNERS",
    "docs/README.md",
    "docs/getting-started.md",
    "docs/guides/getting-started.md",
    "docs/guides/managing-installation.md",
    "docs/reference/hooks.md",
    "docs/maintainers/documentation-policy.md",
    "docs/maintainers/release-documentation.md",
    "docs/architecture.md",
    "docs/examples.md",
    "docs/trust-model.md",
    "docs/compatibility.md",
    "docs/field-validation.md",
    "docs/repository-governance.md",
    "docs/runtime-identity.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "evidence/schema-v1.json",
    "evidence/schema-v2.json",
    "evidence/release-status.json",
    "evidence/runtime-identity.json",
    "evidence/runtime-contract-history-v1.json",
    "evidence/repository-policy-revisions-v1.json",
    "evidence/v0.7.4/codex/linux.json",
    "evidence/v0.7.4/claude-code/linux.json",
    "evals/README.md",
    "evals/schema-v1.json",
    "evals/schema-v2.json",
    "evals/host-response-schema-v1.json",
    "evals/host-response-schema-v2.json",
    "evals/host-response-schema-v3.json",
    "evals/review-response-schema-v1.json",
    "evals/review-sequences-v1.json",
    "evals/codex-exec-jsonl-observer-v2.json",
    "evals/codex-exec-jsonl-observer-v3.json",
    "evals/no-hook-observation/codex-protocol-v1.json",
    "evals/no-hook-observation/codex-prompt-envelope-v1.json",
    "evals/no-hook-observation/codex-fixtures-v1.json",
    "evals/no-hook-observation/codex-result-schema-v1.json",
    "evals/no-hook-observation/result-history-v1.json",
    "evals/benchmarks/codex-core-v1.json",
    "evals/benchmarks/codex-core-v2.json",
    "evals/no-hook/bundle-manifest-schema-v1.json",
    "evals/context-budget/README.md",
    "evals/context-budget/schema-v1.json",
    f"evals/context-budget/results/v{RELEASE_VERSION}.json",
    "evals/results/v0.7.7/codex/linux.json",
    "evals/results/v0.7.7/codex/linux-recovery-1.json",
    "evals/results/v0.7.7/codex/linux-recovery-2.json",
    "evals/results/v0.7.7/claude-code/linux.json",
    "scripts/check-compatibility-evidence.py",
    "scripts/check-documentation.py",
    "scripts/check-runtime-identity.py",
    "scripts/check-release-evidence.py",
    "scripts/build-no-hook-bundle.py",
    "scripts/run-no-hook-codex-observation.py",
    "scripts/create-release-tag.py",
    "scripts/measure-routing-context.py",
    "scripts/render-release-facts.py",
    "axiom_validation/route-boundaries-v1.json",
    "axiom_validation/no_hook_bundle.py",
    "axiom_validation/no_hook_observation.py",
    "axiom_validation/runtime-contract-inputs-v1.json",
    "evidence/profiles/openai-hook-independent-v1/bundle-v1.json",
    ".github/workflows/publish-immutable-release.yml",
    ".github/workflows/create-protected-release-tag.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/pull_request_template.md",
)


def discover_release_documents(root: Path = REPOSITORY_ROOT) -> tuple[str, ...]:
    """Discover strict release-note paths without duplicating release history."""
    release_root = root / "docs" / "releases"
    return tuple(
        path.relative_to(root).as_posix()
        for path in sorted(release_root.glob("v*.md"))
        if path.is_file()
    )


REQUIRED_PUBLIC_FILES = tuple(
    dict.fromkeys((*_BASE_REQUIRED_PUBLIC_FILES, *discover_release_documents()))
)

EXPECTED_DIRECT_SKILLS = (
    "agent-plugin-architect",
    "agents-architect",
    "confirm-external-action",
    "optimize-codex-usage",
    "reversible-system-change",
    "review-axiom-task",
    "traceable-git-submit",
    "using-axiom",
)
INSTRUCTION_MAX_BYTES = 8192
AGENT_PLUGIN_ARCHITECT_DESCRIPTION = (
    "Design, initialize, audit, migrate, maintain, or evaluate a packaged Codex or "
    "Claude Code plugin's shared Skills, route ownership, manifests, marketplace "
    "wrappers, hooks, and version-bound compatibility evidence. Use only for explicit "
    "packaged agent-plugin architecture work. Do not use for repository-local "
    "AGENTS.md or .agents/skills systems, ordinary source-code or documentation work "
    "merely because it is in a plugin repository, host installation, publication, "
    "deployment, or Git submission."
)
AGENT_PLUGIN_ARCHITECT_REFERENCES = (
    "references/package-inventory.md",
    "references/release-readiness.md",
    "references/route-and-trigger-contracts.md",
    "references/packaged-skill-architecture.md",
    "references/hooks-and-trust-boundaries.md",
    "references/cross-host-packaging.md",
    "references/evaluation-and-evidence.md",
    "references/validation-reporting.md",
)
GOVERNANCE_VERIFIED_DATE = "2026-08-29"
GOVERNANCE_OWNER = "@wheakerd"
CRITICAL_CODEOWNER_PATTERNS = (
    "/.github/CODEOWNERS",
    "/.github/workflows/",
    "/.codex-plugin/",
    "/.agents/plugins/",
    "/.claude-plugin/",
    "/hooks/",
    "/skills/using-axiom/",
    "/scripts/",
    "/axiom_validation/",
    "/tests/",
    "/SECURITY.md",
    "/docs/repository-governance.md",
)
GOVERNANCE_SNAPSHOT_ANCHORS = (
    f"Last verified (UTC): `{GOVERNANCE_VERIFIED_DATE}`",
    "`require-signed-commits-on-main`",
    "`require-github-signed-release-tags`",
    "`restrict-release-tag-creation`",
    "`refs/heads/main`",
    "`refs/tags/v*`",
    "`Verify signed main history`",
    "`repository-guards`",
    "`unit-and-integration-tests`",
    "`integration_id: 15368`",
    "`required_approving_review_count: 0`",
    "`require_extra_approval_for_unattributed_changes: true`",
    "`allowed_merge_methods: [squash]`",
    "`require_code_owner_review: false`",
    "`strict_required_status_checks_policy: true`",
    "`strict_required_status_checks_policy: false`",
    "`do_not_enforce_on_create: false`",
    "`bypass_actors: []`",
    "`current_user_can_bypass: never`",
    "`actor_id: 4756785`",
    "`actor_type: Integration`",
    "`bypass_mode: always`",
    "must omit the `bypass_actors` property",
    "`20677005`",
    "`20724385`",
    "`21703772`",
    "Required checks on `main`: `repository-guards` and "
    "`unit-and-integration-tests`",
    "Default-branch deletion rule: **UNAVAILABLE / NOT-RUN**",
    "Release-tag creator allowlist: **GitHub App "
    "`axiom-release-tag-controller` only**",
    "Commit-level required-check evidence is defense in depth, not exact "
    "tag-creation authorization.",
    "A failed workflow is detection evidence, not server-side mutation prevention.",
    "`Publish immutable release`",
    "`enabled: true`",
    "`enforced_by_owner: false`",
    "Existing Releases, including v0.8.5, remain in their previously reported mutable state",
)
GOVERNANCE_SNAPSHOT_FORBIDDEN = (
    "The ruleset has no `creation` restriction and exposes no creator allowlist.",
    "Release-tag creator allowlist: **UNAVAILABLE**",
)
REPOSITORY_GUARDS_ENVIRONMENT_HEADING = "### Repository Guards Canonical Environment"
REPOSITORY_GUARDS_ENVIRONMENT_ANCHORS = (
    "pins the required `repository-guards` job to the exact `ubuntu-24.04` runner",
    "Python `3.14.7` and Node.js `24.19.0`",
    "`package-manager-cache: false` setting keeps package-manager caching disabled",
    "`python -B scripts/check-distribution-drift.py` and "
    "`python -B scripts/check-publication.py`",
    "Fork pull requests use ordinary `pull_request`, receive only `contents: read`, "
    "and receive no repository secret",
    "No moving `ubuntu-latest` compatibility canary is currently defined",
    "without reviewed ownership, cadence, failure triage, and runner-upgrade criteria",
    "never be described as release provenance or installed-host evidence",
)
HOOK_RUNTIME_PROMOTION_HEADING = "### Hook Runtime Promotion Gate"
HOOK_RUNTIME_PROMOTION_ANCHORS = (
    "`hook-runtime-gate`. It uses `if: always()`, depends on the complete "
    "`hook-runtime` matrix job",
    "accepts only the current workflow run's `needs.hook-runtime.result == success`",
    "at least 30 consecutive completed `push` runs on `main`",
    "the interval from the first qualifying run to the last is at least 14 full days",
    "there is no unresolved runner-specific false failure or scheduled compatibility failure",
    "when an eligible fork pull request is available during the observation period",
    "The observation gate is therefore **NOT SATISFIED**.",
    "`hook-runtime-gate` must not be promoted from this evidence.",
)
RELEASE_TAG_POLICY_ANCHORS = (
    "The active repository ruleset `require-github-signed-release-tags` targets "
    "exactly `refs/tags/v*`. The administrator-visible REST response for ruleset "
    "`20724385`, updated at `2026-08-29T01:53:08.312Z`, reported "
    "`bypass_actors: []` and `current_user_can_bypass: never`.",
    "It contains no `creation` rule. Its empty bypass list applies to every "
    "integrity rule in this ruleset, including the required signature, required "
    "check, deletion, and non-fast-forward controls.",
    "The separate active ruleset `restrict-release-tag-creation` also targets "
    "exactly `refs/tags/v*`. Ruleset `21703772`, updated at "
    "`2026-08-29T01:52:49.941Z`, contains exactly one `creation` rule.",
    "Its only administrator-visible bypass entry is `actor_id: 4756785`, "
    "`actor_type: Integration`, and `bypass_mode: always`, which identifies the "
    "dedicated `axiom-release-tag-controller` GitHub App.",
    "Because the App bypass is scoped to this creation-only ruleset, it does not "
    "bypass any rule in `require-github-signed-release-tags`.",
    "Release-tag creator allowlist: **GitHub App "
    "`axiom-release-tag-controller` only**.",
    "Commit-level required-check evidence is defense in depth, not exact "
    "tag-creation authorization.",
)
RELEASE_TAG_CONTROLLER_HEADING = "## Release Tag Controller Migration"
RELEASE_TAG_CONTROLLER_ANCHORS = (
    "The v0.8.20 migration registered GitHub App ID `4756785` with slug "
    "`axiom-release-tag-controller`, installed it only on `wheakerd/axiom`, and "
    "created the `release-tag-creation` Actions environment.",
    "The administrator read-back above confirms that the App is the only "
    "`Integration` / `always` bypass actor in `restrict-release-tag-creation`, "
    "the former owner-user bypass is absent, and "
    "`require-github-signed-release-tags` has no bypass actor and requires only "
    "`Verify signed main history`.",
    "A break-glass operation remains a separately authorized, audited ruleset change; "
    "no permanent interactive-user bypass is retained merely for convenience.",
    "The `release-tag-creation` Actions environment owns "
    "`AXIOM_RELEASE_APP_PRIVATE_KEY`, `AXIOM_RELEASE_APP_CLIENT_ID`, and the numeric "
    "`AXIOM_RELEASE_APP_ID`.",
    "The minted App token is scoped to this repository and requests only "
    "`administration: read` plus `contents: write`; administration write is not granted.",
    "Before one exact `POST /git/refs`, the controller binds the requested version "
    "and tag, live protected-main commit and tree, both manifest versions",
    "It performs the same complete read a second time, rejects any difference, "
    "creates only the exact absent tag, and immediately reads the ref back.",
    "An uncertain response is read back once and reported as a failure without retry; "
    "a rerun rejects the existing ref with zero mutation.",
    "GitHub returns `bypass_actors` only to a caller with ruleset write access.",
    "It binds ruleset IDs `20677005`, `20724385`, and `21703772` plus their "
    "normalized server update instants to the reviewed administrator-visible snapshot",
    "Any actor or rule edit changes the server-owned update instant and fails before "
    "tag mutation; no workflow receives ruleset-write permission",
    "`Verify signed main history`, `Verify release candidate`, "
    "`Verify created release tag`, and `Observe published immutable release`.",
    "The controller accepts only the exact current `main` SHA and the main-history "
    "context, so a candidate result cannot authorize production tag creation.",
    "At this dated snapshot `v0.8.20` remained absent after fail-closed controller "
    "refusals",
)
GOVERNANCE_REVIEW_BOUNDARY_HEADING = "## Human Review Trust Boundary"
GOVERNANCE_REVIEW_BOUNDARY_ANCHORS = (
    "`Path B: document the single-maintainer trust boundary` is the selected "
    "policy for this snapshot.",
    "`wheakerd` is the current ultimate repository trust root, and the absence "
    "of independent human review is a known limitation.",
    "CODEOWNERS is advisory under the live rule: it assigns responsibility and "
    "requests review, but it does not block an unapproved merge while "
    "`require_code_owner_review: false` and `required_approving_review_count: 0`.",
    "The current directly observed preventive controls are the server-side "
    "pull-request requirement, required signatures, non-fast-forward protection, "
    "strict required checks, squash-only main merges, and the release-tag creation "
    "and integrity rules.",
    "The current directly observed detective controls are the repository validators "
    "and tests, GitHub Actions and check output, signed-target and release "
    "observations, content-addressed release attestations, manual read-only API "
    "re-verification, and ruleset-history entries.",
    "Hardware-backed authentication and an independently controlled release identity "
    "were not verified by the repository or API evidence used for this snapshot and "
    "are not claimed as current compensating controls.",
    "Emergency or administrative ruleset changes remain separately auditable "
    "through GitHub's ruleset version history.",
    "Every currently observed history entry identifies `actor_id: 78034820` and "
    "`actor_type: User`, which maps to the same `wheakerd` identity.",
    "That audit trail is detective evidence; because the governing administrator "
    "remains the same identity, it does not constitute an independent trust domain.",
    "`Path A: enforce independent review` must not be enabled until a different "
    "trusted GitHub principal has direct write access, is added alongside `@wheakerd` "
    "as a code owner for every critical path listed above, and has approved a "
    "protected test pull request that changes at least one such path.",
    "That test must prove that the approval counts without author self-approval or a "
    "ruleset bypass.",
    "Path B changes no repository ruleset, CODEOWNERS entry, workflow, collaborator "
    "permission, or required check.",
    "The external contribution flow and merge gates therefore remain unchanged: "
    "`repository-guards` and `unit-and-integration-tests` remain the only required "
    "checks, and the three hook-runtime matrix checks plus `hook-runtime-gate` "
    "remain non-required review evidence.",
)
GOVERNANCE_REVIEW_BOUNDARY_FORBIDDEN = (
    "`Path A: enforce independent review` is the selected policy for this snapshot.",
    "Independent human review is currently enforced.",
    "CODEOWNERS blocks an unapproved merge.",
    "Hardware-backed authentication and an independently controlled release identity "
    "are verified current compensating controls.",
    "Ruleset history constitutes an independent trust domain.",
    "Path B adds a required approval for external contributors.",
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

    architect_root = REPOSITORY_ROOT / "skills" / "agent-plugin-architect"
    architect_main = architect_root / "SKILL.md"
    architect_fields = parse_skill_frontmatter(architect_main, failures)
    if architect_fields is not None and architect_fields.get(
        "description"
    ) != AGENT_PLUGIN_ARCHITECT_DESCRIPTION:
        failures.append(
            "skills/agent-plugin-architect/SKILL.md description drifted from the "
            "accepted narrow route contract"
        )
    actual_references = tuple(
        path.relative_to(architect_root).as_posix()
        for path in sorted((architect_root / "references").glob("*.md"))
    )
    if actual_references != tuple(sorted(AGENT_PLUGIN_ARCHITECT_REFERENCES)):
        failures.append(
            "agent-plugin-architect direct reference set drifted: "
            + ", ".join(actual_references)
        )
    architect_text = architect_main.read_text(encoding="utf-8")
    for reference in AGENT_PLUGIN_ARCHITECT_REFERENCES:
        if architect_text.count(reference) != 1:
            failures.append(
                "skills/agent-plugin-architect/SKILL.md must expose exactly one direct "
                f"next hop for {reference!r}"
            )
    canonical_summary = (
        "- `agent-plugin-architect`: design or audit packaged Codex or Claude Code\n"
        "  plugin architecture across shared Skills, routes, manifests, wrappers, hooks,\n"
        "  and compatibility evidence. Repo-local AGENTS systems and ordinary plugin\n"
        "  code stay outside."
    )
    if canonical_summary not in front_door:
        failures.append(
            "skills/using-axiom/SKILL.md is missing the accepted agent-plugin-architect "
            "route summary"
        )


def check_required_files(failures: list[str]) -> None:
    for relative_path in REQUIRED_PUBLIC_FILES:
        if not (REPOSITORY_ROOT / relative_path).is_file():
            failures.append(
                f"missing required public file: {relative_path}; restore the accepted publication surface"
            )


def check_repository_governance_documents(
    governance_text: str,
    codeowners_text: str,
    failures: list[str],
) -> int:
    """Validate the dated governance snapshot and exact critical-path owners."""
    normalized_governance = " ".join(governance_text.split())
    for anchor in GOVERNANCE_SNAPSHOT_ANCHORS:
        if " ".join(anchor.split()) not in normalized_governance:
            failures.append(
                f"docs/repository-governance.md is missing governance snapshot anchor {anchor!r}"
            )
    for stale_claim in GOVERNANCE_SNAPSHOT_FORBIDDEN:
        if " ".join(stale_claim.split()) in normalized_governance:
            failures.append(
                "docs/repository-governance.md retains stale governance claim "
                f"{stale_claim!r}"
            )

    repository_guards_heading = REPOSITORY_GUARDS_ENVIRONMENT_HEADING
    if governance_text.count(repository_guards_heading) != 1:
        failures.append(
            "docs/repository-governance.md must contain exactly one Repository "
            "Guards Canonical Environment section"
        )
    else:
        repository_guards_section = governance_text.split(
            repository_guards_heading, 1
        )[1].split("\n## ", 1)[0]
        normalized_repository_guards_section = " ".join(
            repository_guards_section.split()
        )
        for anchor in REPOSITORY_GUARDS_ENVIRONMENT_ANCHORS:
            if " ".join(anchor.split()) not in normalized_repository_guards_section:
                failures.append(
                    "docs/repository-governance.md Repository Guards Canonical "
                    f"Environment is missing scoped anchor {anchor!r}"
                )

    release_heading = "## Release Tag Policy"
    if governance_text.count(release_heading) != 1:
        failures.append(
            "docs/repository-governance.md must contain exactly one Release Tag Policy section"
        )
    else:
        release_section = governance_text.split(release_heading, 1)[1].split(
            "\n## ", 1
        )[0]
        normalized_release_section = " ".join(release_section.split())
        for anchor in RELEASE_TAG_POLICY_ANCHORS:
            if " ".join(anchor.split()) not in normalized_release_section:
                failures.append(
                    "docs/repository-governance.md Release Tag Policy is missing "
                    f"scoped anchor {anchor!r}"
                )

    controller_heading = RELEASE_TAG_CONTROLLER_HEADING
    if governance_text.count(controller_heading) != 1:
        failures.append(
            "docs/repository-governance.md must contain exactly one Release Tag "
            "Controller Migration section"
        )
    else:
        controller_section = governance_text.split(controller_heading, 1)[1].split(
            "\n## ", 1
        )[0]
        normalized_controller_section = " ".join(controller_section.split())
        for anchor in RELEASE_TAG_CONTROLLER_ANCHORS:
            if " ".join(anchor.split()) not in normalized_controller_section:
                failures.append(
                    "docs/repository-governance.md Release Tag Controller Migration "
                    f"is missing scoped anchor {anchor!r}"
                )

    hook_runtime_heading = HOOK_RUNTIME_PROMOTION_HEADING
    if governance_text.count(hook_runtime_heading) != 1:
        failures.append(
            "docs/repository-governance.md must contain exactly one Hook Runtime "
            "Promotion Gate section"
        )
    else:
        hook_runtime_section = governance_text.split(hook_runtime_heading, 1)[1].split(
            "\n## ", 1
        )[0]
        normalized_hook_runtime_section = " ".join(hook_runtime_section.split())
        for anchor in HOOK_RUNTIME_PROMOTION_ANCHORS:
            if " ".join(anchor.split()) not in normalized_hook_runtime_section:
                failures.append(
                    "docs/repository-governance.md Hook Runtime Promotion Gate is "
                    f"missing scoped anchor {anchor!r}"
                )

    review_heading = GOVERNANCE_REVIEW_BOUNDARY_HEADING
    if governance_text.count(review_heading) != 1:
        failures.append(
            "docs/repository-governance.md must contain exactly one Human Review "
            "Trust Boundary section"
        )
    else:
        review_section = governance_text.split(review_heading, 1)[1].split(
            "\n## ", 1
        )[0]
        normalized_review_section = " ".join(review_section.split())
        for anchor in GOVERNANCE_REVIEW_BOUNDARY_ANCHORS:
            if " ".join(anchor.split()) not in normalized_review_section:
                failures.append(
                    "docs/repository-governance.md Human Review Trust Boundary is "
                    f"missing scoped anchor {anchor!r}"
                )
    for unsupported_claim in GOVERNANCE_REVIEW_BOUNDARY_FORBIDDEN:
        if " ".join(unsupported_claim.split()) in normalized_governance:
            failures.append(
                "docs/repository-governance.md contains unsupported review-boundary "
                f"claim {unsupported_claim!r}"
            )

    entries: list[tuple[str, tuple[str, ...]]] = []
    seen_patterns: set[str] = set()
    for line_number, raw_line in enumerate(codeowners_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) < 2:
            failures.append(
                f".github/CODEOWNERS:{line_number} must contain one pattern and an owner"
            )
            continue
        pattern, *owners = fields
        if pattern in seen_patterns:
            failures.append(
                f".github/CODEOWNERS:{line_number} duplicates critical pattern {pattern!r}"
            )
            continue
        seen_patterns.add(pattern)
        entries.append((pattern, tuple(owners)))

    expected_entries = tuple(
        (pattern, (GOVERNANCE_OWNER,)) for pattern in CRITICAL_CODEOWNER_PATTERNS
    )
    if tuple(entries) != expected_entries:
        failures.append(
            ".github/CODEOWNERS must retain the exact ordered critical-path owner set"
        )

    valid_count = 0
    entry_map = dict(entries)
    for pattern in CRITICAL_CODEOWNER_PATTERNS:
        expected_owners = (GOVERNANCE_OWNER,)
        actual_owners = entry_map.get(pattern)
        if actual_owners != expected_owners:
            failures.append(
                f".github/CODEOWNERS must assign {pattern!r} only to {GOVERNANCE_OWNER}"
            )
        else:
            valid_count += 1
        if f"`{pattern}`" not in governance_text:
            failures.append(
                f"docs/repository-governance.md must list critical CODEOWNERS pattern {pattern!r}"
            )
    return valid_count


def check_repository_governance_contract(failures: list[str]) -> int:
    """Load and validate checked-in repository-governance declarations."""
    documents: dict[str, str] = {}
    for relative_path in ("docs/repository-governance.md", ".github/CODEOWNERS"):
        path = REPOSITORY_ROOT / relative_path
        try:
            documents[relative_path] = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {relative_path}: {error}")
    if len(documents) != 2:
        return 0
    return check_repository_governance_documents(
        documents["docs/repository-governance.md"],
        documents[".github/CODEOWNERS"],
        failures,
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
            (f"Version `{RELEASE_VERSION}`", "## Exact Draft Evidence Validation"),
        ),
        (
            REPOSITORY_ROOT / "docs" / "README.md",
            ("](maintainers/release-documentation.md)",),
        ),
        (
            REPOSITORY_ROOT / "docs" / "maintainers" / "release-documentation.md",
            (
                "## Responsibility Map",
                "render-body --expected-version X.Y.Z",
                "`notesSha256`",
                "## Fix-Forward Boundary",
            ),
        ),
    )
    documents: dict[Path, str] = {}
    for path, anchors in surface_contracts:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {display_path(path)}: {error}")
            continue
        documents[path] = text
        for anchor in anchors:
            if anchor not in text:
                failures.append(
                    f"{display_path(path)} is missing current release anchor {anchor!r} "
                    f"derived from RELEASE_VERSION={RELEASE_VERSION!r}"
                )
    rendered_body = render_release_body(RELEASE_VERSION, failures)
    release_notes = documents.get(release_path)
    if rendered_body is not None and release_notes is not None and rendered_body == release_notes:
        failures.append("future GitHub Release body must remain distinct from the version note")


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
