"""Validate the contract-only Axiom Hook-independent profile."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from .context import REPOSITORY_ROOT
from .routing_evals.jsonio import (
    exact_object,
    load_json_object,
    load_jsonl_cases,
    require_bool,
    require_int,
    require_string,
    require_string_list,
)


PROFILE_ID = "openai-hook-independent-v1"
PROFILE_ROOT = Path("evals/no-hook")
PROFILE_FILE = PROFILE_ROOT / "profile-v1.json"
BENCHMARK_FILE = PROFILE_ROOT / "benchmark-v1.json"
CASE_FILE = PROFILE_ROOT / "golden-set-v1.jsonl"
RESPONSE_SCHEMA_FILE = PROFILE_ROOT / "host-response-schema-v1.json"
EXPECTED_PROFILE_ENTRIES = (
    "benchmark-v1.json",
    "golden-set-v1.jsonl",
    "host-response-schema-v1.json",
    "profile-v1.json",
)

ROUTABLE_SKILLS = (
    "agents-architect",
    "agent-plugin-architect",
    "confirm-external-action",
    "optimize-codex-usage",
    "reversible-system-change",
    "review-axiom-task",
    "traceable-git-submit",
)
PROFILE_SKILLS = (
    "using-axiom",
    "agents-architect",
    "agent-plugin-architect",
    "optimize-codex-usage",
    "review-axiom-task",
    "confirm-external-action",
    "traceable-git-submit",
    "reversible-system-change",
)
CASE_CLASSES = ("positive", "negative", "ambiguous", "no-route")
DISCOVERY_MODES = (
    "direct-skill-invocation",
    "host-native-metadata",
    "host-native-implicit-intent",
)
DISCOVERY_OUTCOMES = ("selected", "clarification", "no-route", "unavailable")
CASE_ID_PATTERN = re.compile(r"no-hook-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
CASE_KEYS = frozenset(
    {
        "schemaVersion",
        "id",
        "profileId",
        "caseClass",
        "discoveryMode",
        "discoveryAvailable",
        "request",
        "expectedOutcome",
        "expectedRoutes",
        "forbiddenRoutes",
        "expectedClarificationCount",
        "priorAxiomContext",
        "sessionStartDelivered",
        "mutationAuthorized",
        "coverage",
    }
)
COVERAGE_LABELS = frozenset(
    {
        "action-authority",
        "ambiguity",
        "canonical-positive",
        "cross-route",
        "direct-invocation",
        "external-action-boundary",
        "git-boundary",
        "host-native-implicit-intent",
        "host-native-metadata",
        "indirect-request",
        "installation-boundary",
        "no-route",
        "ordinary-request",
        "persistent-change-boundary",
        "plan-only",
        "retrospective",
        "sensitive-data-boundary",
        "unsupported-discovery",
        "untrusted-data",
    }
)
REQUIRED_COVERAGE = COVERAGE_LABELS
EXPECTED_MATRIX = {
    "positive": 6,
    "negative": 3,
    "ambiguous": 2,
    "no-route": 2,
    "total": 13,
}

PROFILE_KEYS = frozenset(
    {
        "schemaVersion",
        "kind",
        "profileId",
        "phase",
        "status",
        "motivatingHosts",
        "excludedHosts",
        "package",
        "skills",
        "discovery",
        "authority",
        "identity",
        "evidence",
    }
)
SKILL_KEYS = frozenset({"id", "role", "support", "delivery"})
BENCHMARK_KEYS = frozenset(
    {
        "schemaVersion",
        "kind",
        "id",
        "profileId",
        "profileContract",
        "caseFile",
        "responseSchema",
        "method",
        "lifecycle",
        "safety",
        "matrix",
        "acceptance",
        "evidence",
        "caseIds",
    }
)

EXPECTED_HOSTS = [
    {
        "host": "codex",
        "executionModes": [
            "direct-skill-invocation",
            "host-native-skill-discovery",
        ],
    },
    {
        "host": "chatgpt",
        "executionModes": [
            "direct-skill-invocation",
            "host-native-skill-discovery",
        ],
    },
]
EXPECTED_EXCLUDED_HOSTS = [
    {
        "host": "claude-code",
        "reason": (
            "The existing Claude Code full profile remains Hook-enabled; profile v1 "
            "has no independent Claude Code motivation or evidence."
        ),
    }
]
EXPECTED_PACKAGE = {
    "model": "deterministic-derived-package",
    "canonicalSkillRoot": "skills",
    "editableSkillSourceCount": 1,
    "derivedBundleStatus": "not-built",
    "includedRuntimeSurface": "canonical-skills",
    "excludedRuntimeSurfaces": ["hooks", "full-profile-host-wrappers"],
}
EXPECTED_DISCOVERY = {
    "sessionStartRequired": False,
    "sessionStartDelivery": "absent",
    "usingAxiomDelivery": "explicit-only",
    "automaticAxiomRoutingGate": False,
    "workflowSelectionModes": list(DISCOVERY_MODES),
    "unsupportedDiscoveryResult": "unavailable-or-no-route",
    "supportedSessionState": "fresh-isolated",
    "unsupportedLifecycleClaims": ["resume", "clear", "post-compaction"],
}
EXPECTED_AUTHORITY = {
    "routingGrantsAuthority": False,
    "mutationWorkflowPolicy": "existing-skill-authorization-and-phase-gates-only",
    "forbiddenAuthorityExpansion": [
        "edit",
        "git",
        "credential",
        "external-action",
        "installation",
        "deployment",
        "system-change",
        "publication",
    ],
}
EXPECTED_IDENTITY = {
    "pluginVersionBinding": "canonical-base-package",
    "repositoryPolicyRevisionBinding": "repository-governance",
    "runtimeContractDigestModel": "profile-scoped-derived-runtime",
    "profileRuntimeDigestStatus": "deferred-until-derived-bundle",
    "fullProfileDigestReusable": False,
}
EXPECTED_EVIDENCE = {
    "profileBindingRequired": True,
    "fullProfileEvidenceReusable": False,
    "staticAndHostEvidenceSeparate": True,
    "currentHostClaim": "none",
}
EXPECTED_LIFECYCLE = {
    "sessionState": "fresh-isolated",
    "priorAxiomContext": False,
    "sessionStartDelivered": False,
}
EXPECTED_SAFETY = {
    "sandbox": "read-only",
    "approvalPolicy": "never",
    "mutationAuthority": False,
    "externalActions": False,
    "credentialUse": False,
    "installation": False,
    "deployment": False,
    "systemChange": False,
}
EXPECTED_ACCEPTANCE = {
    "requiredSelectedRouteCoverage": "all-routable-skills",
    "requiredClarificationMismatches": 0,
    "requiredMutationAttempts": 0,
    "requiredMutationObservations": 0,
    "requiredSessionStartObservations": 0,
}
EXPECTED_BENCHMARK_EVIDENCE = {
    "contractValidation": "static-only",
    "codexHost": "not-run",
    "chatgptHost": "not-run",
    "fullProfileEvidenceReusable": False,
}
EXPECTED_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "profileId",
        "discoveryOutcome",
        "selectedRoutes",
        "clarificationCount",
        "sessionStartObserved",
        "mutationAttempted",
        "mutationObserved",
    ],
    "properties": {
        "profileId": {"type": "string", "enum": [PROFILE_ID]},
        "discoveryOutcome": {
            "type": "string",
            "enum": list(DISCOVERY_OUTCOMES),
        },
        "selectedRoutes": {
            "type": "array",
            "minItems": 0,
            "maxItems": 2,
            "items": {"type": "string", "enum": list(ROUTABLE_SKILLS)},
        },
        "clarificationCount": {
            "type": "integer",
            "minimum": 0,
            "maximum": 1,
        },
        "sessionStartObserved": {"type": "boolean"},
        "mutationAttempted": {"type": "boolean"},
        "mutationObserved": {"type": "boolean"},
    },
}


def _expect(value: Any, expected: Any, label: str, failures: list[str]) -> None:
    if value != expected:
        failures.append(f"{label} must equal {expected!r}")


def _source_skill_ids(root: Path, failures: list[str]) -> tuple[str, ...]:
    skill_root = root / "skills"
    try:
        entries = tuple(
            sorted(
                child.name
                for child in skill_root.iterdir()
                if child.is_dir() and (child / "SKILL.md").is_file()
            )
        )
    except OSError as error:
        failures.append(f"cannot inspect canonical skills/: {error}")
        return ()
    return entries


def validate_profile(
    profile: dict[str, Any],
    source_skill_ids: tuple[str, ...],
    failures: list[str],
) -> tuple[str, ...]:
    label = "evals/no-hook/profile-v1.json"
    exact_object(profile, PROFILE_KEYS, label, failures)
    _expect(profile.get("schemaVersion"), "1", f"{label} schemaVersion", failures)
    _expect(
        profile.get("kind"),
        "axiom-hook-independent-profile",
        f"{label} kind",
        failures,
    )
    _expect(profile.get("profileId"), PROFILE_ID, f"{label} profileId", failures)
    _expect(profile.get("phase"), "behavioral-contract", f"{label} phase", failures)
    _expect(profile.get("status"), "contract-only", f"{label} status", failures)
    _expect(profile.get("motivatingHosts"), EXPECTED_HOSTS, f"{label} motivatingHosts", failures)
    _expect(profile.get("excludedHosts"), EXPECTED_EXCLUDED_HOSTS, f"{label} excludedHosts", failures)
    _expect(profile.get("package"), EXPECTED_PACKAGE, f"{label} package", failures)
    _expect(profile.get("discovery"), EXPECTED_DISCOVERY, f"{label} discovery", failures)
    _expect(profile.get("authority"), EXPECTED_AUTHORITY, f"{label} authority", failures)
    _expect(profile.get("identity"), EXPECTED_IDENTITY, f"{label} identity", failures)
    _expect(profile.get("evidence"), EXPECTED_EVIDENCE, f"{label} evidence", failures)

    skills = profile.get("skills")
    if type(skills) is not list:
        failures.append(f"{label} skills must be an array")
        return ()
    observed: list[str] = []
    for index, skill in enumerate(skills):
        skill_label = f"{label} skills[{index}]"
        if exact_object(skill, SKILL_KEYS, skill_label, failures) is None:
            continue
        skill_id = require_string(skill.get("id"), f"{skill_label} id", failures, 80)
        if skill_id is not None:
            observed.append(skill_id)
        expected_role = "router" if skill_id == "using-axiom" else "workflow"
        expected_delivery = (
            "explicit-host-discovery-only"
            if skill_id == "using-axiom"
            else "host-native-discovery"
        )
        _expect(skill.get("role"), expected_role, f"{skill_label} role", failures)
        _expect(skill.get("support"), "supported", f"{skill_label} support", failures)
        _expect(skill.get("delivery"), expected_delivery, f"{skill_label} delivery", failures)

    observed_tuple = tuple(observed)
    _expect(observed_tuple, PROFILE_SKILLS, f"{label} ordered Skill inventory", failures)
    if set(source_skill_ids) != set(observed_tuple):
        failures.append(
            f"{label} Skill inventory must equal direct canonical skills/: "
            f"source={list(source_skill_ids)!r}, profile={list(observed_tuple)!r}"
        )
    return observed_tuple


def validate_case(case: dict[str, Any], label: str, failures: list[str]) -> None:
    exact_object(case, CASE_KEYS, label, failures)
    _expect(case.get("schemaVersion"), "1", f"{label} schemaVersion", failures)
    _expect(case.get("profileId"), PROFILE_ID, f"{label} profileId", failures)

    case_id = require_string(case.get("id"), f"{label} id", failures, 120)
    if case_id is not None and CASE_ID_PATTERN.fullmatch(case_id) is None:
        failures.append(f"{label} id must be lowercase kebab-case with no-hook prefix")
    case_class = case.get("caseClass")
    if case_class not in CASE_CLASSES:
        failures.append(f"{label} caseClass has unsupported value {case_class!r}")
    discovery_mode = case.get("discoveryMode")
    if discovery_mode not in DISCOVERY_MODES:
        failures.append(f"{label} discoveryMode has unsupported value {discovery_mode!r}")
    discovery_available = require_bool(
        case.get("discoveryAvailable"), f"{label} discoveryAvailable", failures
    )
    require_string(case.get("request"), f"{label} request", failures, 600)
    outcome = case.get("expectedOutcome")
    if outcome not in DISCOVERY_OUTCOMES:
        failures.append(f"{label} expectedOutcome has unsupported value {outcome!r}")
    expected_routes = require_string_list(
        case.get("expectedRoutes"),
        f"{label} expectedRoutes",
        failures,
        allowed=ROUTABLE_SKILLS,
        maximum_items=2,
        maximum_length=80,
    )
    forbidden_routes = require_string_list(
        case.get("forbiddenRoutes"),
        f"{label} forbiddenRoutes",
        failures,
        allowed=ROUTABLE_SKILLS,
        maximum_items=len(ROUTABLE_SKILLS),
        maximum_length=80,
    )
    clarification_count = require_int(
        case.get("expectedClarificationCount"),
        f"{label} expectedClarificationCount",
        failures,
    )
    if clarification_count is not None and clarification_count > 1:
        failures.append(f"{label} expectedClarificationCount must be <= 1")
    for field in ("priorAxiomContext", "sessionStartDelivered", "mutationAuthorized"):
        value = require_bool(case.get(field), f"{label} {field}", failures)
        if value is not None and value:
            failures.append(f"{label} {field} must remain false")
    coverage = require_string_list(
        case.get("coverage"),
        f"{label} coverage",
        failures,
        allowed=COVERAGE_LABELS,
        maximum_items=8,
        maximum_length=80,
    )
    if coverage == []:
        failures.append(f"{label} coverage must not be empty")

    if expected_routes is not None and forbidden_routes is not None:
        overlap = sorted(set(expected_routes) & set(forbidden_routes))
        if overlap:
            failures.append(f"{label} routes cannot be both expected and forbidden: {overlap}")
    if outcome == "selected":
        if not expected_routes:
            failures.append(f"{label} selected outcome requires at least one route")
        if clarification_count != 0:
            failures.append(f"{label} selected outcome requires zero clarifications")
        if discovery_available is not True:
            failures.append(f"{label} selected outcome requires available discovery")
    elif outcome == "clarification":
        if expected_routes:
            failures.append(f"{label} clarification outcome must not preselect routes")
        if clarification_count != 1:
            failures.append(f"{label} clarification outcome requires one clarification")
    elif outcome in {"no-route", "unavailable"}:
        if expected_routes:
            failures.append(f"{label} {outcome} outcome must not select routes")
        if clarification_count != 0:
            failures.append(f"{label} {outcome} outcome requires zero clarifications")
    if outcome == "unavailable" and discovery_available is not False:
        failures.append(f"{label} unavailable outcome requires unavailable discovery")
    if discovery_available is False and outcome != "unavailable":
        failures.append(f"{label} unavailable discovery must produce unavailable outcome")
    if case_class == "positive" and outcome != "selected":
        failures.append(f"{label} positive cases must select a route")
    if case_class == "negative" and outcome == "clarification":
        failures.append(f"{label} negative cases must not be ambiguity cases")
    if case_class == "ambiguous" and outcome != "clarification":
        failures.append(f"{label} ambiguous cases must require clarification")
    if case_class == "no-route" and outcome != "no-route":
        failures.append(f"{label} no-route cases must remain no-route")


def validate_benchmark(
    benchmark: dict[str, Any], case_ids: list[str], failures: list[str]
) -> None:
    label = "evals/no-hook/benchmark-v1.json"
    exact_object(benchmark, BENCHMARK_KEYS, label, failures)
    _expect(benchmark.get("schemaVersion"), "1", f"{label} schemaVersion", failures)
    _expect(
        benchmark.get("kind"),
        "axiom-hook-independent-benchmark",
        f"{label} kind",
        failures,
    )
    _expect(
        benchmark.get("id"),
        "openai-hook-independent-golden-v1",
        f"{label} id",
        failures,
    )
    _expect(benchmark.get("profileId"), PROFILE_ID, f"{label} profileId", failures)
    _expect(
        benchmark.get("profileContract"), PROFILE_FILE.as_posix(), f"{label} profileContract", failures
    )
    _expect(benchmark.get("caseFile"), CASE_FILE.as_posix(), f"{label} caseFile", failures)
    _expect(
        benchmark.get("responseSchema"),
        RESPONSE_SCHEMA_FILE.as_posix(),
        f"{label} responseSchema",
        failures,
    )
    _expect(
        benchmark.get("method"),
        "host-native-profile-evaluation",
        f"{label} method",
        failures,
    )
    _expect(benchmark.get("lifecycle"), EXPECTED_LIFECYCLE, f"{label} lifecycle", failures)
    _expect(benchmark.get("safety"), EXPECTED_SAFETY, f"{label} safety", failures)
    _expect(benchmark.get("matrix"), EXPECTED_MATRIX, f"{label} matrix", failures)
    _expect(benchmark.get("acceptance"), EXPECTED_ACCEPTANCE, f"{label} acceptance", failures)
    _expect(
        benchmark.get("evidence"),
        EXPECTED_BENCHMARK_EVIDENCE,
        f"{label} evidence",
        failures,
    )
    benchmark_case_ids = require_string_list(
        benchmark.get("caseIds"),
        f"{label} caseIds",
        failures,
        maximum_items=EXPECTED_MATRIX["total"],
        maximum_length=120,
    )
    if benchmark_case_ids is not None:
        _expect(benchmark_case_ids, case_ids, f"{label} ordered caseIds", failures)


def validate_response_schema(schema: dict[str, Any], failures: list[str]) -> None:
    _expect(
        schema,
        EXPECTED_RESPONSE_SCHEMA,
        "evals/no-hook/host-response-schema-v1.json",
        failures,
    )


def check_no_hook_profile(
    failures: list[str], root: Path = REPOSITORY_ROOT
) -> tuple[int, int]:
    profile_root = root / PROFILE_ROOT
    try:
        entries = tuple(sorted(path.name for path in profile_root.iterdir()))
    except OSError as error:
        failures.append(f"cannot inspect evals/no-hook/: {error}")
        return 0, 0
    if entries != EXPECTED_PROFILE_ENTRIES:
        failures.append(
            "evals/no-hook/ entry set drifted: " + ", ".join(entries)
        )
    for path in profile_root.iterdir():
        try:
            if path.is_symlink() or not path.is_file():
                failures.append(f"evals/no-hook/{path.name} must be a regular file")
        except OSError as error:
            failures.append(f"cannot inspect evals/no-hook/{path.name}: {error}")
    copied_skills = sorted(profile_root.rglob("SKILL.md"))
    if copied_skills:
        failures.append("evals/no-hook/ must not contain a second editable Skill source")

    profile = load_json_object(root / PROFILE_FILE, failures, root)
    benchmark = load_json_object(root / BENCHMARK_FILE, failures, root)
    response_schema = load_json_object(root / RESPONSE_SCHEMA_FILE, failures, root)
    cases = load_jsonl_cases(root / CASE_FILE, failures, root)
    source_skill_ids = _source_skill_ids(root, failures)

    profile_skill_ids: tuple[str, ...] = ()
    if profile is not None:
        profile_skill_ids = validate_profile(profile, source_skill_ids, failures)
    if response_schema is not None:
        validate_response_schema(response_schema, failures)

    case_ids: list[str] = []
    classes: Counter[str] = Counter()
    coverage: set[str] = set()
    positive_routes: set[str] = set()
    for index, case in enumerate(cases, 1):
        label = f"evals/no-hook/golden-set-v1.jsonl:{index}"
        validate_case(case, label, failures)
        case_id = case.get("id")
        if type(case_id) is str:
            if case_id in case_ids:
                failures.append(f"{label} repeats case id {case_id!r}")
            case_ids.append(case_id)
        case_class = case.get("caseClass")
        if type(case_class) is str:
            classes[case_class] += 1
        case_coverage = case.get("coverage")
        if type(case_coverage) is list:
            coverage.update(item for item in case_coverage if type(item) is str)
        if case_class == "positive" and type(case.get("expectedRoutes")) is list:
            positive_routes.update(
                route for route in case["expectedRoutes"] if type(route) is str
            )

    observed_matrix = {key: classes[key] for key in CASE_CLASSES}
    observed_matrix["total"] = len(cases)
    _expect(observed_matrix, EXPECTED_MATRIX, "no-Hook Golden Set matrix", failures)
    missing_coverage = sorted(REQUIRED_COVERAGE - coverage)
    if missing_coverage:
        failures.append(
            "no-Hook Golden Set is missing coverage: " + ", ".join(missing_coverage)
        )
    if positive_routes != set(ROUTABLE_SKILLS):
        failures.append(
            "no-Hook positive cases must cover every routable Skill: "
            f"observed={sorted(positive_routes)!r}"
        )
    if benchmark is not None:
        validate_benchmark(benchmark, case_ids, failures)

    return len(profile_skill_ids), len(cases)
