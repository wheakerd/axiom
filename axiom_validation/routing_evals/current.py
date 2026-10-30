"""Current routing contracts kept separate from immutable historical corpora."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .benchmark import validate_benchmark
from .constants import (
    BENCHMARK_V3_ID, BENCHMARK_V4_ID, BENCHMARK_V5_ID, BENCHMARK_V6_ID, BENCHMARK_V7_ID,
    CURRENT_BENCHMARK_PROFILES,
    CURRENT_BENCHMARK_CASE_COUNT,
    CURRENT_CORPUS_RELATIVE_PATH,
    CURRENT_HOST_RESPONSE_SCHEMA_V7_SHA256,
    CURRENT_HOST_RESPONSE_SCHEMA_V8_SHA256,
    CURRENT_PUBLIC_ROUTES,
    HOST_BENCHMARK_PROFILES_BY_VERSION,
    HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V8_RELATIVE_PATH,
    SCHEMA_V3_ID, SCHEMA_V4_ID, SCHEMA_V5_ID, SCHEMA_V6_ID, SCHEMA_V7_ID,
    V6_BENCHMARK_CASE_COUNT, V6_CORPUS_RELATIVE_PATH,
    V3_BENCHMARK_CASE_COUNT, V3_CORPUS_RELATIVE_PATH, V3_PUBLIC_ROUTES,
    V4_BENCHMARK_CASE_COUNT, V4_CORPUS_RELATIVE_PATH, V4_PUBLIC_ROUTES,
    V5_BENCHMARK_CASE_COUNT, V5_CORPUS_RELATIVE_PATH, V5_PUBLIC_ROUTES,
)
from .jsonio import load_json_object, load_jsonl_cases
from .schemas import (
    check_host_response_schema_v7,
    check_host_response_schema_v8,
    check_schema_contract_v6,
    check_schema_contract_v7,
    validate_case,
)

_CANONICAL_V3 = ("agent-plugin-architect", "clarify-intent", "delegate-simple-task", "task-planning")
# Schema v7 cases whose narrowed expectation the offline route model regression-tests.
OFFLINE_ENFORCED_V7_CASES = frozenset({
    "current-no-route-builtin-web-search-001",
    "current-no-route-fresh-plan-001",
    "current-no-route-post-compaction-continuation-001",
    "current-delegate-simple-task-explicit-no-gate-001",
    "current-overlap-delegate-plan-only-002",
})
_CANONICAL_V4 = (*_CANONICAL_V3, "continuous-progress")
# version: (corpus, benchmark ID, schema ID, routes, case count, canonical routes)
VERSIONED_CONTRACTS = {
    "3": (V3_CORPUS_RELATIVE_PATH, BENCHMARK_V3_ID, SCHEMA_V3_ID, V3_PUBLIC_ROUTES,
          V3_BENCHMARK_CASE_COUNT, _CANONICAL_V3),
    "4": (V4_CORPUS_RELATIVE_PATH, BENCHMARK_V4_ID, SCHEMA_V4_ID, V4_PUBLIC_ROUTES,
          V4_BENCHMARK_CASE_COUNT, _CANONICAL_V4),
    "5": (V5_CORPUS_RELATIVE_PATH, BENCHMARK_V5_ID, SCHEMA_V5_ID, V5_PUBLIC_ROUTES,
          V5_BENCHMARK_CASE_COUNT, _CANONICAL_V4),
    "6": (V6_CORPUS_RELATIVE_PATH, BENCHMARK_V6_ID, SCHEMA_V6_ID, CURRENT_PUBLIC_ROUTES,
          V6_BENCHMARK_CASE_COUNT, (*_CANONICAL_V4, "verify-completion")),
    "7": (CURRENT_CORPUS_RELATIVE_PATH, BENCHMARK_V7_ID, SCHEMA_V7_ID, CURRENT_PUBLIC_ROUTES,
          CURRENT_BENCHMARK_CASE_COUNT, (*_CANONICAL_V4, "verify-completion")),
}


def collect_current_corpus(root: Path, failures: list[str], *, version: str = "7") -> dict[str, dict[str, Any]]:
    """Read one versioned corpus; do not reinterpret the historical corpus."""
    if version not in VERSIONED_CONTRACTS:
        raise ValueError("unsupported versioned corpus")
    relative = VERSIONED_CONTRACTS[version][0]
    path = root / relative
    cases: dict[str, dict[str, Any]] = {}
    for line, case in enumerate(load_jsonl_cases(path, failures, root), 1):
        label = f"{relative}:{line}"
        document = validate_case(case, label, failures)
        if document is None or type(document.get("id")) is not str:
            continue
        if document.get("schemaVersion") != version:
            failures.append(f"{label} must use schema version {version!r}")
        case_id = document["id"]
        if case_id in cases:
            failures.append(f"{label} duplicates current case {case_id!r}")
        cases[case_id] = document
        if document.get("expectedClarification") and document.get("expectedRoutes") != ["clarify-intent"]:
            failures.append(f"{label} must select clarify-intent before action routing")
    return cases


def current_benchmark_case_ids(
    root: Path, cases: dict[str, dict[str, Any]], failures: list[str], *, version: str = "7",
    host: str = "codex",
) -> list[str]:
    if version not in VERSIONED_CONTRACTS:
        raise ValueError("unsupported versioned benchmark")
    _, benchmark_id, schema_id, routes, case_count, canonical = VERSIONED_CONTRACTS[version]
    profiles = HOST_BENCHMARK_PROFILES_BY_VERSION.get(version)
    if host != "codex":
        if profiles is None or host not in profiles:
            raise ValueError("unsupported host benchmark")
        benchmark_id = profiles[host]["id"]
    benchmark = load_json_object(root / f"evals/benchmarks/{benchmark_id}.json", failures, root)
    if benchmark is None:
        return []
    return validate_benchmark(
        benchmark, cases, failures, schema_version=version,
        benchmark_id=benchmark_id, schema_id=schema_id, routes=routes,
        canonical_routes=canonical, expected_case_count=case_count, host=host,
        profiles=profiles or CURRENT_BENCHMARK_PROFILES,
    )


def check_current_routing_evaluations(root: Path, failures: list[str]) -> tuple[int, int]:
    """Validate current schemas, source coverage, and bounded offline contracts."""
    for relative, check in (
        ("evals/schema-v6.json", check_schema_contract_v6),
        ("evals/schema-v7.json", check_schema_contract_v7),
    ):
        schema = load_json_object(root / relative, failures, root)
        if schema is not None:
            check(schema, failures)
    # V7 stays frozen for the records that bind it; V8 is the current model-facing schema.
    for relative, expected_digest, check in (
        (HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH, CURRENT_HOST_RESPONSE_SCHEMA_V7_SHA256, check_host_response_schema_v7),
        (HOST_RESPONSE_SCHEMA_V8_RELATIVE_PATH, CURRENT_HOST_RESPONSE_SCHEMA_V8_SHA256, check_host_response_schema_v8),
    ):
        response_path = root / relative
        response = load_json_object(response_path, failures, root)
        if response is not None:
            check(response, failures)
            if hashlib.sha256(response_path.read_bytes()).hexdigest() != expected_digest:
                failures.append(f"{relative} digest drifted")

    installed_routes = {
        path.parent.name for path in (root / "plugin" / "skills").glob("*/SKILL.md")
        if path.parent.name != "using-axiom"
    }
    if installed_routes != set(CURRENT_PUBLIC_ROUTES):
        failures.append("current routing enum differs from the installed task skill inventory")
    cases = collect_current_corpus(root, failures)
    case_ids = current_benchmark_case_ids(root, cases, failures)
    if current_benchmark_case_ids(root, cases, failures, host="claude-code") != case_ids:
        failures.append("claude-code-core-v7 must select the codex-core-v7 cases in the same order")
    covered = {route for case in cases.values() for route in case.get("expectedRoutes", ())}
    if covered != set(CURRENT_PUBLIC_ROUTES):
        failures.append("current routing corpus must cover every current public task route")

    from ..routing_contracts import route_contract

    # The prior Python fixtures retain their original pseudo-route. Current
    # contracts must resolve that decision to the now-installed public skill.
    for case in cases.values():
        request = case.get("request", "")
        if "continuous-progress" in request or "current-no-route-ordinary-continuation" in case["id"] or "current-no-route-goals-only" in case["id"] or case.get("expectedClarification") or "verify-completion" in case["id"] or case["id"] in OFFLINE_ENFORCED_V7_CASES or request.startswith(("Use the task-planning skill", "Use the delegate-simple-task skill", "Use the local-web-search skill")):
            actual = route_contract(request)
            if ([actual["route"]] if actual["route"] else []) != case.get("expectedRoutes"):
                failures.append(f"current offline route disagrees with case {case['id']!r}")
            if actual["route"] is not None and actual["authorization"] != frozenset({"read"}):
                failures.append(f"current offline route grants mutation in case {case['id']!r}")
    return len(cases), len(case_ids)
