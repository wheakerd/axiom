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
from .yaml_subset import CanonicalYamlError, parse_agent_metadata_document, parse_skill_frontmatter_document

_BASE_REQUIRED_PUBLIC_FILES = (
    "README.md",
    ".github/CODEOWNERS",
    "docs/getting-started.md",
    "docs/architecture.md",
    "docs/examples.md",
    "docs/trust-model.md",
    "docs/compatibility.md",
    "docs/field-validation.md",
    "docs/repository-governance.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "evidence/schema-v1.json",
    "evidence/release-status.json",
    "evidence/v0.7.4/codex/linux.json",
    "evidence/v0.7.4/claude-code/linux.json",
    "evals/README.md",
    "evals/schema-v1.json",
    "evals/schema-v2.json",
    "evals/host-response-schema-v1.json",
    "evals/host-response-schema-v2.json",
    "evals/host-response-schema-v3.json",
    "evals/benchmarks/codex-core-v1.json",
    "evals/benchmarks/codex-core-v2.json",
    "evals/context-budget/README.md",
    "evals/context-budget/schema-v1.json",
    f"evals/context-budget/results/v{RELEASE_VERSION}.json",
    "evals/results/v0.7.7/codex/linux.json",
    "evals/results/v0.7.7/codex/linux-recovery-1.json",
    "evals/results/v0.7.7/codex/linux-recovery-2.json",
    "evals/results/v0.7.7/claude-code/linux.json",
    "scripts/check-compatibility-evidence.py",
    "scripts/measure-routing-context.py",
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
EXPECTED_README_SKILLS = (
    "using-axiom",
    "agents-architect",
    "agent-plugin-architect",
    "optimize-codex-usage",
    "review-axiom-task",
    "confirm-external-action",
    "traceable-git-submit",
    "reversible-system-change",
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
    "references/route-and-trigger-contracts.md",
    "references/packaged-skill-architecture.md",
    "references/hooks-and-trust-boundaries.md",
    "references/cross-host-packaging.md",
    "references/evaluation-and-evidence.md",
    "references/validation-reporting.md",
)
GOVERNANCE_VERIFIED_DATE = "2026-08-23"
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
    "`refs/heads/main`",
    "`refs/tags/v*`",
    "`Verify GitHub-signed release target`",
    "`repository-guards`",
    "`required_approving_review_count: 0`",
    "`require_extra_approval_for_unattributed_changes: true`",
    "`allowed_merge_methods: [squash]`",
    "`require_code_owner_review: false`",
    "`strict_required_status_checks_policy: false`",
    "`do_not_enforce_on_create: false`",
    "`bypass_actors: []`",
    "`current_user_can_bypass: never`",
    "Required checks on `main`: **NONE OBSERVED**",
    "Default-branch deletion rule: **UNAVAILABLE / NOT-RUN**",
    "Release-tag creator allowlist: **UNAVAILABLE**",
    "A failed workflow is detection evidence, not server-side mutation prevention.",
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
