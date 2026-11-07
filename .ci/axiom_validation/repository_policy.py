"""Repository layout, skill, and release-surface policy."""

from __future__ import annotations

import re
from pathlib import Path

from .context import (
    RELEASE_VERSION,
    REPOSITORY_ROOT,
    display_path,
)
from .release_evidence import render_release_body
from .yaml_subset import CanonicalYamlError, parse_agent_metadata_document, parse_skill_frontmatter_document

REQUIRED_PUBLIC_FILES = (
    "README.md",
    "LICENSE",
    "plugin/LICENSE",
    ".github/CODEOWNERS",
    "docs/en/README.md",
    "docs/en/guides/getting-started.md",
    "docs/en/guides/managing-installation.md",
    "docs/en/reference/hooks.md",
    "docs/en/maintainers/documentation-policy.md",
    "docs/en/maintainers/runtime-changes.md",
    "docs/en/maintainers/validation.md",
    "docs/en/maintainers/release-documentation.md",
    "docs/en/architecture.md",
    "docs/en/examples.md",
    "docs/en/trust-model.md",
    "docs/en/compatibility.md",
    "docs/en/repository-governance.md",
    "docs/en/runtime-identity.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    ".ci/runtime-identity.json",
    ".ci/scripts/check-documentation.py",
    ".ci/scripts/check-runtime-identity.py",
    ".ci/scripts/check-release-evidence.py",
    ".ci/scripts/create-release-tag.py",
    ".ci/scripts/render-release-facts.py",
    ".ci/scripts/release-pipeline.py",
    ".ci/scripts/build-listing-variant.py",
    ".ci/axiom_validation/runtime-contract-inputs-v4.json",
    ".github/workflows/publish-immutable-release.yml",
    ".github/workflows/create-protected-release-tag.yml",
    ".github/workflows/release-pipeline.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/pull_request_template.md",
)

EXPECTED_DIRECT_SKILLS = (
    "agent-plugin-architect",
    "agents-architect",
    "clarify-intent",
    "confirm-external-action",
    "continuous-progress",
    "delegate-simple-task",
    "local-web-search",
    "optimize-agent-usage",
    "reversible-system-change",
    "review-axiom-task",
    "task-planning",
    "traceable-git-submit",
    "using-axiom",
    "verify-completion",
)
# The order in which the public Skill Reference lists the bundled skills: the
# startup gate first, then the routes in their reviewed order.
BUNDLED_SKILL_ORDER = (
    "using-axiom",
    "clarify-intent",
    "delegate-simple-task",
    "task-planning",
    "continuous-progress",
    "local-web-search",
    "agents-architect",
    "agent-plugin-architect",
    "optimize-agent-usage",
    "review-axiom-task",
    "verify-completion",
    "confirm-external-action",
    "traceable-git-submit",
    "reversible-system-change",
)
INSTRUCTION_MAX_BYTES = 8192
GOVERNANCE_OWNER = "@wheakerd"
CRITICAL_CODEOWNER_PATTERNS = (
    "/.github/CODEOWNERS",
    "/.github/workflows/",
    "/plugin/.codex-plugin/",
    "/plugin/.claude-plugin/",
    "/.claude-plugin/",
    "/.agents/plugins/",
    "/plugin/hooks/",
    "/plugin/skills/using-axiom/",
    "/.ci/",
    "/SECURITY.md",
    "/docs/en/repository-governance.md",
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
        skill_root = REPOSITORY_ROOT / "plugin" / "skills" / skill_name
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
        if not fields["description"]:
            failures.append(f"{display_path(main_path)} description must be non-empty")

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
                    metadata_text, display_path(metadata_path)
                )
            except CanonicalYamlError as error:
                failures.append(str(error))
            else:
                interface = metadata["interface"]
                if f"${skill_name}" not in interface["default_prompt"]:
                    failures.append(
                        f"{display_path(metadata_path)} default_prompt must mention ${skill_name}"
                    )

    for path in sorted((REPOSITORY_ROOT / "plugin" / "skills").rglob("*.md")):
        byte_count = len(path.read_bytes())
        if byte_count >= INSTRUCTION_MAX_BYTES:
            failures.append(
                f"{display_path(path)} is {byte_count} bytes; instruction files must stay below "
                f"{INSTRUCTION_MAX_BYTES}"
            )

    if tuple(sorted(BUNDLED_SKILL_ORDER)) != EXPECTED_DIRECT_SKILLS:
        failures.append(
            "canonical skill order is not the exact direct skill set: "
            + ", ".join(BUNDLED_SKILL_ORDER)
        )


def check_required_files(failures: list[str]) -> None:
    for relative_path in REQUIRED_PUBLIC_FILES:
        if not (REPOSITORY_ROOT / relative_path).is_file():
            failures.append(
                f"missing required public file: {relative_path}; restore the accepted publication surface"
            )
    check_installed_license_copy(failures)


def check_installed_license_copy(failures: list[str], root: Path = REPOSITORY_ROOT) -> None:
    """Keep the license notice installed with the plugin identical to the repository's."""
    try:
        identical = (root / "plugin" / "LICENSE").read_bytes() == (root / "LICENSE").read_bytes()
    except OSError as error:
        failures.append(f"cannot compare plugin/LICENSE with LICENSE: {error}")
        return
    if not identical:
        failures.append("plugin/LICENSE must be a byte-identical copy of LICENSE")


def check_critical_path_owners(codeowners_text: str, failures: list[str]) -> int:
    """Require the exact ordered critical-path owner set in CODEOWNERS."""
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
        if entry_map.get(pattern) != (GOVERNANCE_OWNER,):
            failures.append(
                f".github/CODEOWNERS must assign {pattern!r} only to {GOVERNANCE_OWNER}"
            )
        else:
            valid_count += 1
    return valid_count


def check_repository_governance_contract(failures: list[str]) -> int:
    """Validate the checked-in critical-path owners."""
    relative_path = ".github/CODEOWNERS"
    try:
        codeowners_text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {relative_path}: {error}")
        return 0
    return check_critical_path_owners(codeowners_text, failures)


def check_release_version_surfaces(failures: list[str]) -> None:
    """Require the current version's changelog entry and a Release body it renders."""
    changelog_path = REPOSITORY_ROOT / "CHANGELOG.md"
    try:
        changelog = changelog_path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {display_path(changelog_path)}: {error}")
        return
    if f"## {RELEASE_VERSION} - " not in changelog:
        failures.append(f"CHANGELOG.md has no entry heading for {RELEASE_VERSION}")
    render_release_body(RELEASE_VERSION, failures)


def check_packaged_skills(failures: list[str]) -> None:
    skills_root = REPOSITORY_ROOT / "plugin" / "skills"
    if not skills_root.is_dir():
        failures.append("missing packaged plugin/skills/ directory")
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
        Path("plugin") / "skills" / skill_name / "SKILL.md"
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


ROUTING_GATE_RELATIVE = "plugin/skills/using-axiom/SKILL.md"
# Both hosts deliver the gate through a startup hook; the ceiling keeps 10% headroom
# below the 8192-byte instruction-file limit.
ROUTING_GATE_MAX_BYTES = 8192 * 90 // 100


def check_routing_gate_size(failures: list[str]) -> None:
    """Keep the startup gate under its byte ceiling."""
    try:
        size = len((REPOSITORY_ROOT / ROUTING_GATE_RELATIVE).read_bytes())
    except OSError as error:
        failures.append(f"cannot read {ROUTING_GATE_RELATIVE}: {error}")
        return
    if size > ROUTING_GATE_MAX_BYTES:
        failures.append(
            f"{ROUTING_GATE_RELATIVE} has {size} bytes; the routing gate must stay within "
            f"{ROUTING_GATE_MAX_BYTES} bytes"
        )
