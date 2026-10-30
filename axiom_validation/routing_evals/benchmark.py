"""Fixed benchmark contracts and documented execution method."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .constants import (
    BENCHMARK_CASE_TIMEOUT_SECONDS,
    HOST_BENCHMARK_PROFILES_BY_VERSION,
    BENCHMARK_DEVELOPER_INSTRUCTION,
    BENCHMARK_ID,
    BENCHMARK_KEYS,
    BENCHMARK_MODEL,
    BENCHMARK_REASONING_EFFORT,
    BENCHMARK_SAFETY_KEYS,
    CLAUDE_CODE_BENCHMARK_SAFETY_KEYS,
    CLAUDE_CODE_OFFICIAL_DOCUMENTATION,
    CLAUDE_CODE_OFFICIAL_REFERENCE_KEYS,
    CURRENT_BENCHMARK_PROFILES,
    HIGH_IMPACT_ROUTES,
    HISTORICAL_PUBLIC_ROUTES,
    MAX_JSON_BYTES,
    OFFICIAL_REFERENCE_KEYS,
    OID_PATTERN,
    SCHEMA_ID,
)
from .history import (
    CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
    CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    FAILED_HOST_RESPONSE_SCHEMA_SHA256,
    INITIAL_CODEX_RUN_ID,
    RECOVERY_CODEX_RUN_ID,
    V1_HOST_RESPONSE_SCHEMA_SHA256,
)
from .jsonio import (
    _display,
    _inspect_regular_file,
    exact_object,
    require_string,
    require_string_list,
)

ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def check_documented_method(root: Path, failures: list[str]) -> None:
    path = root / "evals" / "history" / "codex-core-v1-v2.md"
    if not _inspect_regular_file(path, MAX_JSON_BYTES, failures, root):
        return
    label = _display(path, root)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read {label}: {error}")
        return
    exact_instruction = f"```text\n{BENCHMARK_DEVELOPER_INSTRUCTION}\n```"
    if exact_instruction not in text:
        failures.append(f"{label} must publish the exact benchmark developer instruction")
    required_fragments = (
        '"AXIOM_EVAL_RUNTIME_ROOT"',
        "tempfile.gettempdir()",
        "release-bound CODEX_HOME must be outside system temporary storage",
        '"HOME": str(case_home)',
        '"CODEX_HOME": str(case_codex_home)',
        'app_server_request("hooks/list"',
        '"config/batchWrite"',
        '"keyPath": "hooks.state"',
        '"trusted_hash": verified_hash',
        'untrusted_hook["currentHash"]',
        'untrusted_hook["trustStatus"] != "untrusted"',
        'trusted_hook["trustStatus"] != "trusted"',
        '"mergeStrategy": "upsert"',
        '"reloadUserConfig": True',
        "With no authentication file present",
        "no hook warnings or errors",
        "must never send `thread/start`, `turn/start`, or a model request",
        '"--ephemeral"',
        '"--json"',
        '"--ignore-rules"',
        '"--sandbox"',
        'approval_policy="never"',
        "model_reasoning_effort=",
        "developer_instructions=",
        '"--model"',
        '"--output-schema"',
        '"--output-last-message"',
        'case["request"]',
        "shell=False",
        'timeout=benchmark["caseTimeoutSeconds"]',
        "reject_duplicate_json_keys",
        "validate_host_response_v3_structure(",
        "classify_host_response_v3_acceptance(",
        "validate_host_response_v3(",
        "derive_observer_evidence(",
        "codex-exec-jsonl-observer-v2.json",
        "classify before lifecycle sequencing",
        "host-response-schema-v3.json",
        "observer-derived",
        "https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas",
        "`uniqueItems`",
        "`minLength`",
        "`maxLength`",
        "stop-on-first-failure",
        "append-only",
        "stderr is diagnostic-only and non-causal",
        "Raw stderr remains memory-only and must be destroyed",
        "must not retain stderr",
        "text, fragments, hashes, paths, identifiers, or credentials",
        "`stderrNonblankLineCount` capped at 32",
        "`stderrCategoryCounts` capped at 32",
        "`warning-prefix`, `error-prefix`, and `other`",
        "`stderrCountOverflow` and `stderrCategoryOverflow`",
        "never directly change `PASS`, `FAIL`, or `UNKNOWN`",
        "never enter passing limitations or the public observation",
        INITIAL_CODEX_RUN_ID,
        RECOVERY_CODEX_RUN_ID,
        FAILED_HOST_RESPONSE_SCHEMA_SHA256,
        V1_HOST_RESPONSE_SCHEMA_SHA256,
        CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
        CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    )
    for fragment in required_fragments:
        if fragment not in text:
            failures.append(f"{label} is missing invocation contract {fragment!r}")
    for forbidden in (
        "--dangerously-bypass-hook-trust",
        "--ignore-user-config",
        "--ask-for-approval",
        "sole accepted model-process stderr line is exactly",
        "Missing, additional, or different stderr remains fatal.",
    ):
        if forbidden in text:
            failures.append(f"{label} documents unsupported invocation option {forbidden!r}")
def _check_host_profile(
    benchmark: dict[str, Any], host: str, label: str, failures: list[str],
    profiles: dict[str, dict[str, Any]] = CURRENT_BENCHMARK_PROFILES,
) -> None:
    """Check a non-Codex schema v5 or v6 profile against its own native settings."""
    profile = profiles.get(host)
    if host != "claude-code" or profile is None:
        failures.append(f"{label} names an unsupported benchmark host {host!r}")
        return
    for field in ("method", "model", "reasoningEffort", "caseTimeoutSeconds"):
        if benchmark.get(field) != profile[field]:
            failures.append(f"{label}.{field} must be {profile[field]!r}")
    official = exact_object(
        benchmark.get("officialReference"),
        CLAUDE_CODE_OFFICIAL_REFERENCE_KEYS,
        f"{label}.officialReference",
        failures,
    )
    if official is not None:
        if official.get("documentation") != CLAUDE_CODE_OFFICIAL_DOCUMENTATION:
            failures.append(
                f"{label}.officialReference.documentation must name {CLAUDE_CODE_OFFICIAL_DOCUMENTATION}"
            )
        verified = require_string(
            official.get("verifiedOn"), f"{label}.officialReference.verifiedOn", failures, 10
        )
        if verified is not None and ISO_DATE_PATTERN.fullmatch(verified) is None:
            failures.append(f"{label}.officialReference.verifiedOn must be an ISO date")
    safety = exact_object(
        benchmark.get("safety"),
        CLAUDE_CODE_BENCHMARK_SAFETY_KEYS,
        f"{label}.safety",
        failures,
    )
    expected_safety = {
        "permissionMode": "dontAsk",
        "isolatedSessionPerCase": True,
        "mutationAuthority": False,
        "externalActions": False,
        "privateConversationUpload": False,
        "credentialDisclosure": False,
    }
    if safety is not None:
        for key, expected in expected_safety.items():
            if safety.get(key) != expected:
                failures.append(f"{label}.safety.{key} must be {expected!r}")


def validate_benchmark(
    benchmark: dict[str, Any],
    cases: dict[str, dict[str, Any]],
    failures: list[str],
    *,
    schema_version: str = "1",
    benchmark_id: str = BENCHMARK_ID,
    schema_id: str = SCHEMA_ID,
    routes: tuple[str, ...] = HISTORICAL_PUBLIC_ROUTES,
    canonical_routes: tuple[str, ...] | None = None,
    expected_case_count: int = 13,
    host: str = "codex",
    profiles: dict[str, dict[str, Any]] = CURRENT_BENCHMARK_PROFILES,
) -> list[str]:
    label = f"evals/benchmarks/{benchmark_id}.json"
    exact_object(benchmark, BENCHMARK_KEYS, label, failures)
    if benchmark.get("schemaVersion") != schema_version or benchmark.get("kind") != "routing-benchmark-manifest":
        failures.append(f"{label} has the wrong schemaVersion or kind")
    if benchmark.get("id") != benchmark_id:
        failures.append(f"{label}.id must be {benchmark_id!r}")
    if benchmark.get("corpusSchema") != schema_id:
        failures.append(f"{label}.corpusSchema must bind {schema_id}")
    if host != "codex":
        _check_host_profile(benchmark, host, label, failures, profiles)
    elif benchmark.get("method") != "documented-codex-cli-equivalent":
        failures.append(f"{label}.method is unsupported")
    official = None if host != "codex" else exact_object(
        benchmark.get("officialReference"),
        OFFICIAL_REFERENCE_KEYS,
        f"{label}.officialReference",
        failures,
    )
    if official is not None:
        if official.get("repository") != "openai/plugins":
            failures.append(f"{label}.officialReference.repository must name openai/plugins")
        commit = require_string(
            official.get("commit"), f"{label}.officialReference.commit", failures, 40
        )
        if commit is not None and OID_PATTERN.fullmatch(commit) is None:
            failures.append(f"{label}.officialReference.commit must be an immutable Git SHA")
        if official.get("path") != "plugins/plugin-eval":
            failures.append(f"{label}.officialReference.path must name plugins/plugin-eval")
    # Versions with a profile per host bind the Codex manifest to that version's Codex
    # profile; earlier Codex-only versions keep the original fixed settings.
    codex_profile = (
        profiles["codex"]
        if host == "codex" and schema_version in HOST_BENCHMARK_PROFILES_BY_VERSION and "codex" in profiles
        else {"model": BENCHMARK_MODEL, "reasoningEffort": BENCHMARK_REASONING_EFFORT,
              "caseTimeoutSeconds": BENCHMARK_CASE_TIMEOUT_SECONDS}
    )
    if host == "codex" and benchmark.get("model") != codex_profile["model"]:
        failures.append(f"{label}.model must be {codex_profile['model']!r}")
    if host == "codex" and benchmark.get("reasoningEffort") != codex_profile["reasoningEffort"]:
        failures.append(
            f"{label}.reasoningEffort must be {codex_profile['reasoningEffort']!r}"
        )
    if host == "codex" and benchmark.get("caseTimeoutSeconds") != codex_profile["caseTimeoutSeconds"]:
        failures.append(
            f"{label}.caseTimeoutSeconds must be {codex_profile['caseTimeoutSeconds']}"
        )
    if benchmark.get("stopOnFirstFailure") is not True:
        failures.append(f"{label}.stopOnFirstFailure must be true")
    if benchmark.get("developerInstruction") != BENCHMARK_DEVELOPER_INSTRUCTION:
        failures.append(f"{label}.developerInstruction drifted from the reviewed value")
    if benchmark.get("repeatCount") != 1 or benchmark.get("lifecycle") != "fresh-start":
        failures.append(f"{label} must select one fresh-session repeat")
    safety = None if host != "codex" else exact_object(
        benchmark.get("safety"),
        BENCHMARK_SAFETY_KEYS,
        f"{label}.safety",
        failures,
    )
    expected_safety = {
        "sandbox": "read-only",
        "approvalPolicy": "never",
        "isolatedSessionPerCase": True,
        "mutationAuthority": False,
        "externalActions": False,
        "privateConversationUpload": False,
        "credentialDisclosure": False,
    }
    if safety is not None:
        for key, expected in expected_safety.items():
            if safety.get(key) != expected:
                failures.append(f"{label}.safety.{key} must be {expected!r}")
    case_ids = require_string_list(
        benchmark.get("caseIds"),
        f"{label}.caseIds",
        failures,
        maximum_items=expected_case_count,
    ) or []
    if len(case_ids) != expected_case_count:
        failures.append(
            f"{label}.caseIds must contain exactly {expected_case_count} cases"
        )
    if any(case_id not in cases for case_id in case_ids):
        failures.append(f"{label}.caseIds references an unknown corpus case")
    selected = set(case_ids)
    marked = {
        case_id
        for case_id, case in cases.items()
        if benchmark_id in case.get("benchmarkSets", ())
    }
    if selected != marked:
        failures.append(f"{label}.caseIds disagrees with corpus benchmarkSets")
    required_canonical_routes = routes if canonical_routes is None else canonical_routes
    for route in required_canonical_routes:
        if not any(
            route in cases[case_id].get("expectedRoutes", ())
            and cases[case_id].get("riskClass") == "canonical-positive"
            for case_id in case_ids
            if case_id in cases
        ):
            failures.append(f"{label} has no canonical acceptance case for {route}")
    for route in HIGH_IMPACT_ROUTES:
        if not any(
            route in cases[case_id].get("forbiddenRoutes", ())
            and "safety" in cases[case_id].get("coverage", ())
            for case_id in case_ids
            if case_id in cases
        ):
            failures.append(f"{label} has no fixed safety control for {route}")
    selected_cases = [cases[case_id] for case_id in case_ids if case_id in cases]
    for coverage in ("cross-route", "ambiguity", "multilingual", "no-route"):
        if not any(coverage in case.get("coverage", ()) for case in selected_cases):
            failures.append(f"{label} lacks {coverage} coverage")
    return case_ids
