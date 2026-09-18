"""Current routing contracts kept separate from immutable historical corpora."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .benchmark import validate_benchmark
from .constants import (
    BENCHMARK_V3_ID,
    CURRENT_BENCHMARK_CASE_COUNT,
    CURRENT_CORPUS_RELATIVE_PATH,
    CURRENT_HOST_RESPONSE_SCHEMA_V4_SHA256,
    CURRENT_PUBLIC_ROUTES,
    HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH,
    SCHEMA_V3_ID,
)
from .jsonio import load_json_object, load_jsonl_cases
from .schemas import (
    check_host_response_schema_v4,
    check_schema_contract_v3,
    validate_case,
)


def collect_current_corpus(root: Path, failures: list[str]) -> dict[str, dict[str, Any]]:
    """Read only v3 cases; do not reinterpret the historical corpus."""
    path = root / CURRENT_CORPUS_RELATIVE_PATH
    cases: dict[str, dict[str, Any]] = {}
    for line, case in enumerate(load_jsonl_cases(path, failures, root), 1):
        label = f"{CURRENT_CORPUS_RELATIVE_PATH}:{line}"
        document = validate_case(case, label, failures)
        if document is None or type(document.get("id")) is not str:
            continue
        if document.get("schemaVersion") != "3":
            failures.append(f"{label} must use the current schema version '3'")
        case_id = document["id"]
        if case_id in cases:
            failures.append(f"{label} duplicates current case {case_id!r}")
        cases[case_id] = document
        if document.get("expectedClarification") and document.get("expectedRoutes") != ["clarify-intent"]:
            failures.append(f"{label} must select clarify-intent before action routing")
    return cases


def current_benchmark_case_ids(
    root: Path, cases: dict[str, dict[str, Any]], failures: list[str]
) -> list[str]:
    benchmark = load_json_object(root / "evals/benchmarks/codex-core-v3.json", failures, root)
    if benchmark is None:
        return []
    return validate_benchmark(
        benchmark, cases, failures, schema_version="3", benchmark_id=BENCHMARK_V3_ID,
        schema_id=SCHEMA_V3_ID, routes=CURRENT_PUBLIC_ROUTES,
        canonical_routes=("agent-plugin-architect", "clarify-intent", "delegate-simple-task", "task-planning"),
        expected_case_count=CURRENT_BENCHMARK_CASE_COUNT,
    )


def check_current_routing_evaluations(root: Path, failures: list[str]) -> tuple[int, int]:
    """Validate current schemas, source coverage, and bounded offline contracts."""
    schema = load_json_object(root / "evals/schema-v3.json", failures, root)
    if schema is not None:
        check_schema_contract_v3(schema, failures)
    response_path = root / HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH
    response = load_json_object(response_path, failures, root)
    if response is not None:
        check_host_response_schema_v4(response, failures)
        if hashlib.sha256(response_path.read_bytes()).hexdigest() != CURRENT_HOST_RESPONSE_SCHEMA_V4_SHA256:
            failures.append(f"{HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH} digest drifted")

    installed_routes = {
        path.parent.name for path in (root / "skills").glob("*/SKILL.md")
        if path.parent.name != "using-axiom"
    }
    if installed_routes != set(CURRENT_PUBLIC_ROUTES):
        failures.append("current routing enum differs from the installed task skill inventory")
    cases = collect_current_corpus(root, failures)
    case_ids = current_benchmark_case_ids(root, cases, failures)
    covered = {route for case in cases.values() for route in case.get("expectedRoutes", ())}
    if covered != set(CURRENT_PUBLIC_ROUTES):
        failures.append("current routing corpus must cover every current public task route")

    from ..routing_contracts import route_contract

    # The prior Python fixtures retain their original pseudo-route. Current
    # contracts must resolve that decision to the now-installed public skill.
    for case in cases.values():
        request = case.get("request", "")
        if case.get("expectedClarification") or request.startswith(("$task-planning", "$delegate-simple-task")):
            actual = route_contract(request)
            if [actual["route"]] != case.get("expectedRoutes"):
                failures.append(f"current offline route disagrees with case {case['id']!r}")
            if actual["authorization"] != frozenset({"read"}):
                failures.append(f"current offline route grants mutation in case {case['id']!r}")
    return len(cases), len(case_ids)
