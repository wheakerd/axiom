"""Strict validation for content-addressed external post-tag observations."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..context import RELEASE_VERSION, REPOSITORY_ROOT
from .benchmark import validate_benchmark
from .constants import (
    BENCHMARK_CASE_TIMEOUT_SECONDS,
    BENCHMARK_REASONING_EFFORT,
    BENCHMARK_V2_ID,
    BENCHMARK_V3_ID,
    CURRENT_BENCHMARK_CASE_COUNT,
    CURRENT_HOST_RESPONSE_SCHEMA_V4_SHA256,
    HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    OID_PATTERN,
    PUBLIC_ROUTES,
    SCHEMA_V2_ID,
    SEMVER_PATTERN,
)
from .corpus import collect_corpus
from .current import collect_current_corpus, current_benchmark_case_ids
from .history import (
    CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    EXPECTED_RESULT_BINDINGS,
)
from .jsonio import load_json_object
from .observations import validate_observation
from .suite import check_routing_evaluations
def validate_external_routing_observation(
    path: Path,
    *,
    expected_version: str,
    expected_tag: str,
    expected_commit: str,
    expected_tree: str,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> str | None:
    """Validate one explicitly versioned current or legacy observation outside the tree."""
    label = path.name or "external routing observation"
    if not path.is_absolute():
        failures.append("external routing observation path must be absolute")
    try:
        canonical_path = path.resolve(strict=True)
    except OSError as error:
        failures.append(f"cannot resolve {label}: {error}")
        canonical_path = None
    if canonical_path is not None:
        if canonical_path != path.absolute():
            failures.append("external routing observation path must be canonical")
        try:
            canonical_path.relative_to(root.resolve())
        except ValueError:
            pass
        else:
            failures.append(
                "external routing observation must remain outside the checked-in tree"
            )

    if (
        type(expected_version) is not str
        or SEMVER_PATTERN.fullmatch(expected_version) is None
    ):
        failures.append("expected external routing version must be strict SemVer")
    if expected_version != RELEASE_VERSION:
        failures.append(
            "expected external routing version must match both current manifests"
        )
    if expected_tag != f"v{expected_version}":
        failures.append("expected external routing tag must match its version")
    for field, oid in (("commit", expected_commit), ("tree", expected_tree)):
        if type(oid) is not str or OID_PATTERN.fullmatch(oid) is None:
            failures.append(
                f"expected external routing {field} must be a 40-character Git SHA"
            )

    # Revalidate the complete checked-in framework first. The external mode may
    # add evidence, but it cannot bypass or replace schemas, corpus contracts,
    # historical records, or their immutable bindings.
    check_routing_evaluations(failures, root)
    record = load_json_object(path, failures, path.parent)
    if record is None:
        return None
    current = record.get("schemaVersion") == "3"
    schema_version = "3" if current else "2"
    benchmark_id = BENCHMARK_V3_ID if current else BENCHMARK_V2_ID
    case_count = CURRENT_BENCHMARK_CASE_COUNT if current else 17
    response_path = HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH if current else HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH
    response_digest = CURRENT_HOST_RESPONSE_SCHEMA_V4_SHA256 if current else CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256
    if current:
        cases = collect_current_corpus(root, failures)
        benchmark_case_ids = current_benchmark_case_ids(root, cases, failures)
    else:
        cases = collect_corpus(root, failures)
        benchmark = load_json_object(root / "evals/benchmarks/codex-core-v2.json", failures, root)
        benchmark_case_ids = []
        if benchmark is not None:
            benchmark_case_ids = validate_benchmark(
                benchmark, cases, failures, schema_version="2",
                benchmark_id=BENCHMARK_V2_ID, schema_id=SCHEMA_V2_ID,
                routes=PUBLIC_ROUTES, canonical_routes=("agent-plugin-architect",),
                expected_case_count=17,
            )

    digest: str | None = None
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        failures.append(f"cannot hash {label}: {error}")
    if digest is not None:
        expected_name = (
            f"axiom-v{expected_version}-{benchmark_id}-{digest}.json"
        )
        if path.name != expected_name:
            failures.append(
                "external routing observation filename must expose its full SHA-256"
            )

    validate_observation(
        record,
        "codex",
        benchmark_case_ids,
        cases,
        label,
        failures,
    )
    if record.get("schemaVersion") != schema_version:
        failures.append("external routing observation must use schemaVersion '2' or '3'")
    if record.get("benchmarkId") != benchmark_id:
        failures.append(f"external routing observation must use {benchmark_id}")
    if record.get("responseSchema") != {
        "path": response_path,
        "sha256": response_digest,
    }:
        failures.append(
            f"external routing observation must bind exact host-response schema {response_path}"
        )
    expected_subject = {
        "version": expected_version,
        "tag": expected_tag,
        "commit": expected_commit,
        "tree": expected_tree,
    }
    if record.get("axiom") != expected_subject:
        failures.append(
            "external routing observation subject must match the exact released version, tag, commit, and tree"
        )
    run_id = record.get("runId")
    preserved_run_ids = {binding[0] for binding in EXPECTED_RESULT_BINDINGS.values()}
    if type(run_id) is str and run_id in preserved_run_ids:
        failures.append(
            "external routing observation runId must not reuse checked-in history"
        )
    run = record.get("run")
    expected_run_fields = {
        "status": "pass",
        "lifecycle": "fresh-start",
        "repeatCount": 1,
        "callCount": case_count,
        "reasoningEffort": BENCHMARK_REASONING_EFFORT,
        "caseTimeoutSeconds": BENCHMARK_CASE_TIMEOUT_SECONDS,
        "installedPluginVerified": True,
        "startupHookVerified": True,
        "method": "documented-codex-cli-equivalent",
        "limitations": [],
    }
    if type(run) is not dict:
        failures.append("external routing observation run must be an object")
    else:
        for field, expected in expected_run_fields.items():
            if run.get(field) != expected:
                failures.append(
                    f"external routing observation run.{field} must be {expected!r}"
                )
    result_cases = record.get("cases")
    if type(result_cases) is not list:
        failures.append("external routing observation cases must be an array")
    else:
        result_ids = [
            item.get("id") if type(item) is dict else None for item in result_cases
        ]
        unique_result_ids = {
            case_id for case_id in result_ids if type(case_id) is str
        }
        if (
            len(result_cases) != case_count
            or len(unique_result_ids) != case_count
            or result_ids != benchmark_case_ids
        ):
            failures.append(
                f"external routing observation must contain {case_count} unique cases in exact benchmark order"
            )
        if any(
            type(item) is not dict or item.get("status") != "pass"
            for item in result_cases
        ):
            failures.append(
                f"external routing observation must preserve {case_count} passing cases with no unrun or unavailable suffix"
            )
    if record.get("summary") != {
        "overallStatus": "pass",
        "evaluatedCases": case_count,
        "canonicalFalseNegatives": 0,
        "highImpactFalsePositives": 0,
        "clarificationMismatches": 0,
        "mutationAttempts": 0,
    }:
        failures.append(
            "external routing observation summary must preserve a complete zero-regression PASS"
        )
    return digest
