"""Aggregate routing-evaluation validation over checked-in artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..context import REPOSITORY_ROOT
from .benchmark import check_documented_method, validate_benchmark
from .constants import (
    BENCHMARK_V2_ID,
    HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    PUBLIC_ROUTES,
    SCHEMA_V2_ID,
)
from .corpus import check_corpus_coverage, collect_corpus
from .history import (
    CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
    CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    REQUIRED_RESULT_PATHS,
    SUPPORTED_RESULT_PATHS,
    V1_HOST_RESPONSE_SCHEMA_SHA256,
    validate_history_index,
)
from .jsonio import _display, load_json_object
from .observer import check_codex_exec_jsonl_taxonomy
from .observations import validate_observation, validate_observation_run_set
from .schemas import (
    check_host_response_schema,
    check_host_response_schema_v2,
    check_host_response_schema_v3,
    check_schema_contract,
    check_schema_contract_v2,
)


def check_routing_evaluations(
    failures: list[str], root: Path = REPOSITORY_ROOT
) -> tuple[int, int, int]:
    """Validate schemas, corpus coverage, benchmark selection, and host records."""
    validate_history_index(root, failures)
    eval_root = root / "evals"
    schema = load_json_object(eval_root / "schema-v1.json", failures, root)
    if schema is not None:
        check_schema_contract(schema, failures)
    schema_v2 = load_json_object(eval_root / "schema-v2.json", failures, root)
    if schema_v2 is not None:
        check_schema_contract_v2(schema_v2, failures)
    response_schema_sha256_by_path: dict[str, str] = {}
    host_schema_contracts = (
        (
            HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
            V1_HOST_RESPONSE_SCHEMA_SHA256,
            check_host_response_schema,
        ),
        (
            HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
            CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
            check_host_response_schema_v2,
        ),
        (
            HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
            CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
            check_host_response_schema_v3,
        ),
    )
    for relative_path, expected_digest, checker in host_schema_contracts:
        host_schema_path = root / relative_path
        host_schema = load_json_object(host_schema_path, failures, root)
        if host_schema is None:
            continue
        checker(host_schema, failures)
        actual_digest = hashlib.sha256(host_schema_path.read_bytes()).hexdigest()
        response_schema_sha256_by_path[relative_path] = actual_digest
        if actual_digest != expected_digest:
            failures.append(f"{relative_path} digest drifted")
    check_codex_exec_jsonl_taxonomy(root, failures)
    check_documented_method(root, failures)
    cases = collect_corpus(root, failures)
    check_corpus_coverage(cases, failures)
    benchmark = load_json_object(
        eval_root / "benchmarks" / "codex-core-v1.json", failures, root
    )
    benchmark_case_ids: list[str] = []
    if benchmark is not None:
        benchmark_case_ids = validate_benchmark(benchmark, cases, failures)
    benchmark_v2 = load_json_object(
        eval_root / "benchmarks" / "codex-core-v2.json", failures, root
    )
    benchmark_v2_case_ids: list[str] = []
    if benchmark_v2 is not None:
        benchmark_v2_case_ids = validate_benchmark(
            benchmark_v2,
            cases,
            failures,
            schema_version="2",
            benchmark_id=BENCHMARK_V2_ID,
            schema_id=SCHEMA_V2_ID,
            routes=PUBLIC_ROUTES,
            canonical_routes=("agent-plugin-architect",),
            expected_case_count=17,
        )
    actual_results = tuple(
        path.relative_to(eval_root).as_posix()
        for path in sorted((eval_root / "results").glob("v*/*/*.json"))
    )
    actual_result_set = set(actual_results)
    missing_required = sorted(set(REQUIRED_RESULT_PATHS) - actual_result_set)
    if missing_required:
        failures.append(
            "routing observation file set is missing: " + ", ".join(missing_required)
        )
    unsupported = sorted(actual_result_set - set(SUPPORTED_RESULT_PATHS))
    if unsupported:
        failures.append(
            "routing observation file set contains unsupported records: "
            + ", ".join(unsupported)
        )
    selected_result_paths = tuple(
        relative_path
        for relative_path in SUPPORTED_RESULT_PATHS
        if relative_path in actual_result_set
    )
    observations: list[tuple[str, dict[str, Any]]] = []
    for relative_path in selected_result_paths:
        path = eval_root / relative_path
        record = load_json_object(path, failures, root)
        if record is None:
            continue
        expected_host = Path(relative_path).parts[-2]
        record_case_ids = (
            benchmark_v2_case_ids
            if record.get("schemaVersion") == "2"
            else benchmark_case_ids
        )
        validate_observation(
            record,
            expected_host,
            record_case_ids,
            cases,
            _display(path, root),
            failures,
        )
        observations.append((relative_path, record))
    validate_observation_run_set(
        observations, response_schema_sha256_by_path, failures
    )
    return (
        len(cases),
        len(benchmark_case_ids) + len(benchmark_v2_case_ids),
        len(observations),
    )
