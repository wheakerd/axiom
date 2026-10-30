"""Checked-in fresh-session routing observations for a release candidate."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..context import RELEASE_VERSION, REPOSITORY_ROOT, display_path
from .constants import (
    CURRENT_BENCHMARK_CASE_COUNT,
    CURRENT_BENCHMARK_PROFILES,
    CURRENT_HOST_RESPONSE_SCHEMA_V7_SHA256,
    CURRENT_HOST_RESPONSE_SCHEMA_V8_SHA256,
    HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V8_RELATIVE_PATH,
)
from .current import collect_current_corpus, current_benchmark_case_ids
from .jsonio import load_json_object
from .observations import validate_observation

CANDIDATE_RESULTS_RELATIVE = "evals/results"
OBSERVATION_HOSTS = ("codex", "claude-code")
OPERATING_SYSTEM_FILE = re.compile(r"[a-z][a-z0-9-]*\.json\Z")
CURRENT_RESPONSE_BINDINGS = (
    {"path": HOST_RESPONSE_SCHEMA_V8_RELATIVE_PATH, "sha256": CURRENT_HOST_RESPONSE_SCHEMA_V8_SHA256},
    {"path": HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH, "sha256": CURRENT_HOST_RESPONSE_SCHEMA_V7_SHA256},
)


def candidate_record_paths(root: Path, version: str) -> dict[str, list[Path]]:
    """Return the checked-in record files per host for one version, sorted by name."""
    base = root / CANDIDATE_RESULTS_RELATIVE / f"v{version}"
    paths: dict[str, list[Path]] = {}
    for host in OBSERVATION_HOSTS:
        directory = base / host
        paths[host] = (
            sorted(path for path in directory.glob("*.json") if path.is_file())
            if directory.is_dir()
            else []
        )
    return paths


def validate_candidate_routing_observation(
    record: Any,
    label: str,
    *,
    host: str,
    expected_version: str,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> dict[str, Any] | None:
    """Validate one schema v6 record of the current benchmark for a candidate version.

    The record binds the observed candidate commit and tree; it is accepted for a
    release commit when the observed commit's installed runtime digest equals the
    release commit's digest, which the Release pipeline checks separately.
    Returns the subject on success.
    """
    initial_failure_count = len(failures)
    if type(record) is not dict:
        failures.append(f"{label} must be an object")
        return None
    profile = CURRENT_BENCHMARK_PROFILES.get(host)
    if profile is None:
        failures.append(f"{label} names a host without a current benchmark profile: {host!r}")
        return None
    if record.get("schemaVersion") != "6":
        failures.append(f"{label} must use schemaVersion '6'")
    cases = collect_current_corpus(root, failures)
    benchmark_case_ids = current_benchmark_case_ids(root, cases, failures, host=host)
    validate_observation(record, host, benchmark_case_ids, cases, label, failures)
    if record.get("benchmarkId") != profile["id"]:
        failures.append(f"{label} must use the current {host} benchmark {profile['id']}")
    if record.get("responseSchema") not in CURRENT_RESPONSE_BINDINGS:
        failures.append(f"{label} must bind the current host-response schema")
    subject = record.get("axiom")
    if type(subject) is not dict or subject.get("version") != expected_version:
        failures.append(f"{label} subject must name version {expected_version}")
    elif subject.get("tag") is None and subject.get("releaseState") != "candidate-unreleased":
        failures.append(f"{label} subject must be candidate-unreleased until the tag exists")
    run = record.get("run")
    expected_run_fields = {
        "status": "pass",
        "lifecycle": "fresh-start",
        "repeatCount": 1,
        "callCount": CURRENT_BENCHMARK_CASE_COUNT,
        "reasoningEffort": profile["reasoningEffort"],
        "caseTimeoutSeconds": profile["caseTimeoutSeconds"],
        "installedPluginVerified": True,
        "startupHookVerified": True,
        "method": profile["method"],
        "limitations": [],
    }
    if type(run) is not dict:
        failures.append(f"{label} run must be an object")
    else:
        for field, expected in expected_run_fields.items():
            if run.get(field) != expected:
                failures.append(f"{label} run.{field} must be {expected!r}")
    result_cases = record.get("cases")
    if type(result_cases) is not list:
        failures.append(f"{label} cases must be an array")
    else:
        result_ids = [item.get("id") if type(item) is dict else None for item in result_cases]
        unique_ids = {case_id for case_id in result_ids if type(case_id) is str}
        if (
            len(result_cases) != CURRENT_BENCHMARK_CASE_COUNT
            or len(unique_ids) != CURRENT_BENCHMARK_CASE_COUNT
            or result_ids != benchmark_case_ids
        ):
            failures.append(
                f"{label} must contain {CURRENT_BENCHMARK_CASE_COUNT} unique cases in exact "
                "benchmark order"
            )
        if any(type(item) is not dict or item.get("status") != "pass" for item in result_cases):
            failures.append(
                f"{label} must preserve {CURRENT_BENCHMARK_CASE_COUNT} passing cases with no "
                "unrun or unavailable suffix"
            )
    if record.get("summary") != {
        "overallStatus": "pass",
        "evaluatedCases": CURRENT_BENCHMARK_CASE_COUNT,
        "canonicalFalseNegatives": 0,
        "highImpactFalsePositives": 0,
        "clarificationMismatches": 0,
        "mutationAttempts": 0,
    }:
        failures.append(f"{label} summary must preserve a complete zero-regression PASS")
    if len(failures) != initial_failure_count or type(subject) is not dict:
        return None
    return subject


def check_candidate_routing_observations(
    root: Path,
    failures: list[str],
    *,
    version: str = RELEASE_VERSION,
) -> int:
    """Validate every checked-in record for the current version; return the count."""
    count = 0
    for host, paths in candidate_record_paths(root, version).items():
        for path in paths:
            label = display_path(path) if root == REPOSITORY_ROOT else f"{host}/{path.name}"
            if OPERATING_SYSTEM_FILE.fullmatch(path.name) is None:
                failures.append(f"{label} must be named after its lowercase operating system")
                continue
            record = load_json_object(path, failures, root)
            if record is None:
                continue
            if validate_candidate_routing_observation(
                record, label, host=host, expected_version=version, failures=failures, root=root
            ) is not None:
                count += 1
    return count
