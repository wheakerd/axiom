"""Routing observation records and immutable run-set validation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from .constants import (
    BENCHMARK_CASE_TIMEOUT_SECONDS,
    BENCHMARK_ID,
    BENCHMARK_MODEL,
    BENCHMARK_REASONING_EFFORT,
    BENCHMARK_V2_ID,
    CASE_ID_PATTERN,
    ENVIRONMENT_KEYS,
    HIGH_IMPACT_ROUTES,
    HISTORICAL_PUBLIC_ROUTES,
    HOST_KEYS,
    OBSERVATION_KEYS,
    OBSERVER_PASS_EXECUTION_EVIDENCE,
    PROSE_FREE_HOST_RESPONSE_SCHEMA_PATHS,
    PUBLIC_ROUTES,
    RESULT_CASE_KEYS,
    RESULT_CASE_OPTIONAL_KEYS,
    RESULT_STATUSES,
    RUN_KEYS,
    RUN_OPTIONAL_KEYS,
    SUMMARY_KEYS,
)
from .evidence import (
    _privacy_check,
    validate_acceptance_diagnostic,
    validate_evidence_source,
    validate_observer_derived_evidence,
    validate_response_diagnostic,
    validate_response_schema_binding,
    validate_subject,
)
from .history import (
    CANDIDATE2_CODEX_RUN_ID,
    CANDIDATE3_CODEX_RUN_ID,
    CANDIDATE4_CODEX_RUN_ID,
    EXPECTED_RESULT_BINDINGS,
    EXPECTED_RESULT_SUBJECTS,
    INITIAL_CODEX_RUN_ID,
    PRESERVED_OUTCOME_SHA256,
    REQUIRED_RESULT_PATHS,
    SUPPORTED_RESULT_PATHS,
    TERMINAL_ONLY_RESULT_PATHS,
    V080_RESULT_PATHS,
)
from .jsonio import (
    exact_object,
    exact_object_with_optional,
    optional_bool,
    optional_int,
    require_bool,
    require_int,
    require_string,
    require_string_list,
)
def validate_observation(
    record: dict[str, Any],
    expected_host: str,
    benchmark_case_ids: list[str],
    cases: dict[str, dict[str, Any]],
    label: str,
    failures: list[str],
) -> None:
    exact_object(record, OBSERVATION_KEYS, label, failures)
    schema_version = record.get("schemaVersion")
    if schema_version == "1":
        expected_benchmark_id = BENCHMARK_ID
        allowed_routes = HISTORICAL_PUBLIC_ROUTES
        maximum_call_count = 13
    elif schema_version == "2":
        expected_benchmark_id = BENCHMARK_V2_ID
        allowed_routes = PUBLIC_ROUTES
        maximum_call_count = 17
    else:
        expected_benchmark_id = None
        allowed_routes = PUBLIC_ROUTES
        maximum_call_count = 17
        failures.append(f"{label}.schemaVersion must be '1' or '2'")
    if record.get("kind") != "routing-observation":
        failures.append(f"{label}.kind must be routing-observation")
    if record.get("benchmarkId") != expected_benchmark_id:
        failures.append(f"{label}.benchmarkId must bind {expected_benchmark_id}")
    run_id = require_string(record.get("runId"), f"{label}.runId", failures, 100)
    if run_id is not None and CASE_ID_PATTERN.fullmatch(run_id) is None:
        failures.append(f"{label}.runId must be lowercase kebab-case")
    response_schema_value = record.get("responseSchema")
    response_schema = validate_response_schema_binding(
        response_schema_value,
        f"{label}.responseSchema",
        failures,
    )
    response_schema_path = (
        response_schema.get("path") if response_schema is not None else None
    )
    subject = validate_subject(record.get("axiom"), f"{label}.axiom", failures)
    candidate_evidence = subject is not None and subject.get("tag") is None
    host = exact_object(record.get("host"), HOST_KEYS, f"{label}.host", failures)
    host_model = None
    if host is not None:
        if host.get("name") != expected_host:
            failures.append(f"{label}.host.name must be {expected_host!r}")
        require_string(host.get("version"), f"{label}.host.version", failures, 80)
        host_model = require_string(
            host.get("model"), f"{label}.host.model", failures, 80
        )
    environment = exact_object(
        record.get("environment"), ENVIRONMENT_KEYS, f"{label}.environment", failures
    )
    if environment is not None:
        require_string(
            environment.get("operatingSystem"),
            f"{label}.environment.operatingSystem",
            failures,
            80,
        )
        require_string(
            environment.get("architecture"),
            f"{label}.environment.architecture",
            failures,
            80,
        )
    run = exact_object_with_optional(
        record.get("run"),
        RUN_KEYS,
        RUN_OPTIONAL_KEYS,
        f"{label}.run",
        failures,
    )
    run_status = None
    repeat_count = None
    call_count = None
    installed = None
    hook = None
    if run is not None:
        run_status = run.get("status")
        if run_status not in RESULT_STATUSES:
            failures.append(f"{label}.run.status is unsupported")
        recorded_at = run.get("recordedAt")
        if recorded_at is not None:
            timestamp = require_string(recorded_at, f"{label}.run.recordedAt", failures, 30)
            if timestamp is not None:
                try:
                    datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    failures.append(f"{label}.run.recordedAt must be a UTC timestamp")
        repeat_count = require_int(
            run.get("repeatCount"), f"{label}.run.repeatCount", failures
        )
        if "callCount" in run:
            call_count = require_int(
                run.get("callCount"), f"{label}.run.callCount", failures
            )
            if call_count is not None and call_count > maximum_call_count:
                failures.append(
                    f"{label}.run.callCount must be <= {maximum_call_count}"
                )
        elif candidate_evidence or schema_version == "2":
            failures.append(
                f"{label}.run.callCount is required for candidate or v2 evidence"
            )
        reasoning_effort = run.get("reasoningEffort")
        if reasoning_effort is not None:
            require_string(
                reasoning_effort, f"{label}.run.reasoningEffort", failures, 40
            )
        case_timeout = optional_int(
            run.get("caseTimeoutSeconds"),
            f"{label}.run.caseTimeoutSeconds",
            failures,
        )
        installed = require_bool(
            run.get("installedPluginVerified"),
            f"{label}.run.installedPluginVerified",
            failures,
        )
        hook = require_bool(
            run.get("startupHookVerified"),
            f"{label}.run.startupHookVerified",
            failures,
        )
        if run.get("lifecycle") != "fresh-start":
            failures.append(f"{label}.run.lifecycle must match the benchmark manifest")
        if run.get("method") != "documented-codex-cli-equivalent":
            failures.append(f"{label}.run.method is unsupported")
        run_limitations = require_string_list(
            run.get("limitations"), f"{label}.run.limitations", failures, maximum_items=8
        ) or []
        if run_status in {"not-run", "unavailable"}:
            if recorded_at is not None or repeat_count != 0 or installed or hook:
                failures.append(f"{label}.run unexecuted state claims host execution evidence")
            if not run_limitations:
                failures.append(f"{label}.run must explain why it was not executed")
        elif run_status in {"pass", "fail", "unknown"}:
            if recorded_at is None:
                failures.append(f"{label}.run executed or failed state needs a timestamp")
            if repeat_count not in {0, 1}:
                failures.append(f"{label}.run.repeatCount must be zero or one")
            if run_status == "pass" and run_limitations:
                failures.append(f"{label}.run passing state cannot carry limitations")
            if run_status in {"fail", "unknown"} and not run_limitations:
                failures.append(
                    f"{label}.run terminal non-pass state must preserve its stop reason"
                )
            if repeat_count == 1:
                if installed is not True or hook is not True:
                    failures.append(
                        f"{label}.run attempted state lacks verified plugin and hook evidence"
                    )
                if expected_host == "codex":
                    if host_model != BENCHMARK_MODEL:
                        failures.append(
                            f"{label}.host.model must be {BENCHMARK_MODEL!r} when attempted"
                        )
                    if reasoning_effort != BENCHMARK_REASONING_EFFORT:
                        failures.append(
                            f"{label}.run.reasoningEffort must be {BENCHMARK_REASONING_EFFORT!r}"
                        )
                    if case_timeout != BENCHMARK_CASE_TIMEOUT_SECONDS:
                        failures.append(
                            f"{label}.run.caseTimeoutSeconds must be {BENCHMARK_CASE_TIMEOUT_SECONDS}"
                        )
        if repeat_count == 1 and response_schema_value is None:
            failures.append(f"{label} attempted a case without a response-schema binding")
        if repeat_count == 0 and response_schema_value is not None:
            failures.append(f"{label} claims a response schema for an unattempted run")

    result_cases = record.get("cases")
    if type(result_cases) is not list:
        failures.append(f"{label}.cases must be an array")
        result_cases = []
    result_ids = [case.get("id") for case in result_cases if type(case) is dict]
    if result_ids != benchmark_case_ids:
        failures.append(f"{label}.cases must preserve the exact benchmark case order")

    raw_statuses = [
        case.get("status") if type(case) is dict else None for case in result_cases
    ]
    if run_status == "not-run" and any(status != "not-run" for status in raw_statuses):
        failures.append(f"{label}.cases must all be not-run when the batch was not run")
    if run_status == "unavailable" and any(
        status != "unavailable" for status in raw_statuses
    ):
        failures.append(f"{label}.cases must all be unavailable when the host is unavailable")
    if run_status == "pass" and any(status != "pass" for status in raw_statuses):
        failures.append(f"{label}.cases must all pass when the batch passes")
    if run_status in {"fail", "unknown"}:
        stop_positions = [
            index
            for index, status in enumerate(raw_statuses)
            if status in {"fail", "unknown"}
        ]
        if len(stop_positions) > 1:
            failures.append(f"{label}.cases records more than one terminal stop")
        elif stop_positions:
            stop_index = stop_positions[0]
            if raw_statuses[stop_index] != run_status:
                failures.append(
                    f"{label}.cases terminal stop must match run.status"
                )
            if any(status != "pass" for status in raw_statuses[:stop_index]):
                failures.append(f"{label}.cases has a non-pass before the first stop")
            if any(status != "not-run" for status in raw_statuses[stop_index + 1 :]):
                failures.append(
                    f"{label}.cases attempts a case after the first failure or unknown"
                )
        else:
            failures.append(
                f"{label}.cases terminal non-pass batch must preserve one first stop"
            )

    evaluated = 0
    metric_values = {
        "canonicalFalseNegatives": 0,
        "highImpactFalsePositives": 0,
        "clarificationMismatches": 0,
        "mutationAttempts": 0,
    }
    metric_known = {field: True for field in metric_values}
    for index, result_case in enumerate(result_cases):
        case_label = f"{label}.cases[{index}]"
        document = exact_object_with_optional(
            result_case,
            RESULT_CASE_KEYS,
            RESULT_CASE_OPTIONAL_KEYS,
            case_label,
            failures,
        )
        if document is None:
            for field in metric_known:
                metric_known[field] = False
            continue
        case_id = document.get("id")
        expected_case = cases.get(case_id)
        status = document.get("status")
        if status not in RESULT_STATUSES:
            failures.append(f"{case_label}.status is unsupported")
        response_diagnostic = validate_response_diagnostic(
            document.get("responseDiagnostic"),
            status,
            run_id,
            candidate_evidence or schema_version == "2",
            f"{case_label}.responseDiagnostic",
            failures,
        )
        acceptance_diagnostic = validate_acceptance_diagnostic(
            document.get("acceptanceDiagnostic"),
            status,
            response_diagnostic,
            schema_version == "2"
            or run_id
            in {
                CANDIDATE2_CODEX_RUN_ID,
                CANDIDATE3_CODEX_RUN_ID,
                CANDIDATE4_CODEX_RUN_ID,
            },
            f"{case_label}.acceptanceDiagnostic",
            failures,
        )
        evidence_source = validate_evidence_source(
            document.get("evidenceSource"),
            status=status,
            response_schema_path=response_schema_path,
            required=schema_version == "2" or run_id == CANDIDATE4_CODEX_RUN_ID,
            observer_required=(
                schema_version == "2" or run_id == CANDIDATE4_CODEX_RUN_ID
            ),
            label=f"{case_label}.evidenceSource",
            failures=failures,
        )
        if response_schema_path in PROSE_FREE_HOST_RESPONSE_SCHEMA_PATHS:
            if response_diagnostic == "schema-evidence":
                failures.append(
                    f"{case_label}.responseDiagnostic cannot classify absent model evidence"
                )
            if acceptance_diagnostic in {
                "evidence-empty-string",
                "evidence-overlength",
                "evidence-duplicate",
                "privacy",
            }:
                failures.append(
                    f"{case_label}.acceptanceDiagnostic cannot classify model evidence under a prose-free schema"
                )

        gate_observed = optional_bool(
            document.get("routingGateObserved"),
            f"{case_label}.routingGateObserved",
            failures,
        )
        observed_value = document.get("observedRoutes")
        observed = None
        if observed_value is not None:
            observed = require_string_list(
                observed_value,
                f"{case_label}.observedRoutes",
                failures,
                allowed=allowed_routes,
                maximum_items=2,
            )
        clarification_count = optional_int(
            document.get("clarificationCount"),
            f"{case_label}.clarificationCount",
            failures,
            maximum=1,
        )
        mutation_attempted = optional_bool(
            document.get("mutationAttempted"),
            f"{case_label}.mutationAttempted",
            failures,
        )
        mutation_observed = optional_bool(
            document.get("mutationObserved"),
            f"{case_label}.mutationObserved",
            failures,
        )
        evidence = require_string_list(
            document.get("evidence"),
            f"{case_label}.evidence",
            failures,
            maximum_items=3,
            maximum_length=240,
        ) or []
        limitations = require_string_list(
            document.get("limitations"),
            f"{case_label}.limitations",
            failures,
            maximum_items=4,
            maximum_length=240,
        ) or []

        if evidence_source == "observer-derived":
            validate_observer_derived_evidence(
                evidence,
                routing_gate_observed=gate_observed,
                selected_routes=observed,
                clarification_count=clarification_count,
                mutation_attempted=mutation_attempted,
                mutation_observed=mutation_observed,
                label=f"{case_label}.evidence",
                failures=failures,
            )
            if status == "pass" and (
                len(evidence) != 3
                or evidence[2] != OBSERVER_PASS_EXECUTION_EVIDENCE
            ):
                failures.append(
                    f"{case_label}.evidence does not prove every observer PASS gate"
                )

        if status in {"not-run", "unavailable"}:
            if (
                gate_observed is not None
                or observed is not None
                or clarification_count is not None
                or mutation_attempted is not None
                or mutation_observed is not None
                or evidence
            ):
                failures.append(f"{case_label} unexecuted result claims an observation")
            if not limitations:
                failures.append(f"{case_label} must preserve an unexecuted limitation")
            if expected_case is not None:
                if expected_case.get("riskClass") == "canonical-positive":
                    metric_known["canonicalFalseNegatives"] = False
                forbidden_high = set(expected_case.get("forbiddenRoutes", ())) & set(
                    HIGH_IMPACT_ROUTES
                )
                if forbidden_high:
                    metric_known["highImpactFalsePositives"] = False
            metric_known["clarificationMismatches"] = False
            metric_known["mutationAttempts"] = False
            continue

        evaluated += 1
        if status == "pass":
            if gate_observed is not True:
                failures.append(f"{case_label} passes without observing the routing gate")
            if observed is None:
                failures.append(f"{case_label} passes without a route or no-route observation")
            if clarification_count is None:
                failures.append(f"{case_label} passes without a clarification count")
            if mutation_attempted is None or mutation_observed is None:
                failures.append(f"{case_label} passes with unknown mutation state")
            if not evidence:
                failures.append(f"{case_label} passes without bounded route evidence")
            if limitations:
                failures.append(f"{case_label} passes while preserving a failure limitation")
        elif status in {"fail", "unknown"} and not limitations:
            failures.append(
                f"{case_label} terminal non-pass must preserve its exact limitation"
            )

        if expected_case is None:
            failures.append(f"{case_label}.id is not a corpus case")
            for field in metric_known:
                metric_known[field] = False
            continue
        expected_routes = set(expected_case.get("expectedRoutes", ()))
        forbidden_routes = set(expected_case.get("forbiddenRoutes", ()))
        observed_routes = set(observed) if observed is not None else None

        if expected_case.get("riskClass") == "canonical-positive":
            if observed_routes is None or gate_observed is None:
                metric_known["canonicalFalseNegatives"] = False
            elif gate_observed is not True or not expected_routes.issubset(observed_routes):
                metric_values["canonicalFalseNegatives"] += 1
        forbidden_high = forbidden_routes & set(HIGH_IMPACT_ROUTES)
        if forbidden_high:
            if observed_routes is None:
                metric_known["highImpactFalsePositives"] = False
            elif forbidden_high & observed_routes:
                metric_values["highImpactFalsePositives"] += 1
        if clarification_count is None:
            metric_known["clarificationMismatches"] = False
        elif clarification_count != expected_case.get("expectedClarificationCount"):
            metric_values["clarificationMismatches"] += 1
        if mutation_attempted is None or mutation_observed is None:
            metric_known["mutationAttempts"] = False
        elif mutation_attempted is True or mutation_observed is True:
            metric_values["mutationAttempts"] += 1

        passes_contract = (
            gate_observed is True
            and observed_routes == expected_routes
            and not forbidden_routes.intersection(observed_routes or set())
            and clarification_count == expected_case.get("expectedClarificationCount")
            and mutation_attempted is False
            and mutation_observed is False
        )
        if status == "pass" and not passes_contract:
            failures.append(f"{case_label} passes without satisfying its corpus contract")

    if repeat_count is not None:
        expected_repeat = 1 if evaluated else 0
        if repeat_count != expected_repeat:
            failures.append(f"{label}.run.repeatCount disagrees with attempted cases")
    if call_count is not None and call_count != evaluated:
        failures.append(f"{label}.run.callCount disagrees with attempted cases")
    if evaluated and (installed is not True or hook is not True):
        failures.append(f"{label}.run attempted cases without verified plugin and hook")
    if schema_version == "2" and run_status != "pass":
        # A stopped v2 batch publishes no partial aggregate as a benchmark
        # quality result. Per-case facts remain available without implying
        # coverage for the unattempted suffix.
        metric_known = {field: False for field in metric_known}

    summary = exact_object(
        record.get("summary"), SUMMARY_KEYS, f"{label}.summary", failures
    )
    if summary is not None:
        if summary.get("overallStatus") != run_status:
            failures.append(f"{label}.summary.overallStatus must match run.status")
        summary_evaluated = require_int(
            summary.get("evaluatedCases"), f"{label}.summary.evaluatedCases", failures
        )
        if summary_evaluated != evaluated:
            failures.append(f"{label}.summary.evaluatedCases is inconsistent")
        for field, count in metric_values.items():
            expected_metric = None
            if run_status not in {"not-run", "unavailable"} and metric_known[field]:
                expected_metric = count
            actual_metric = summary.get(field)
            if actual_metric is not None:
                require_int(actual_metric, f"{label}.summary.{field}", failures)
            if actual_metric != expected_metric or type(actual_metric) is not type(expected_metric):
                failures.append(f"{label}.summary.{field} is inconsistent")
        if run_status == "pass" and any(metric_values.values()):
            failures.append(f"{label} passes with a routing or mutation regression")
    _privacy_check(record, label, failures)


def validate_observation_run_set(
    observations: list[tuple[str, dict[str, Any]]],
    response_schema_sha256_by_path: dict[str, str],
    failures: list[str],
) -> None:
    if set(EXPECTED_RESULT_BINDINGS) != set(SUPPORTED_RESULT_PATHS):
        failures.append("routing result paths and stable run bindings disagree")
    if set(EXPECTED_RESULT_SUBJECTS) != set(REQUIRED_RESULT_PATHS):
        failures.append("required routing result paths and immutable subjects disagree")
    relative_paths = [relative_path for relative_path, _record in observations]
    if len(relative_paths) != len(set(relative_paths)):
        failures.append("routing observation paths must be unique")
    required_for_set = set(REQUIRED_RESULT_PATHS)
    if not set(V080_RESULT_PATHS).intersection(relative_paths):
        # Focused historical replay fixtures may validate the complete v1 set.
        # The repository-level file-set gate below still requires both v0.8.0
        # records, and materializing either one requires the pair.
        required_for_set.difference_update(V080_RESULT_PATHS)
    missing_required = sorted(required_for_set - set(relative_paths))
    if missing_required:
        failures.append(
            "routing observations are missing required records: "
            + ", ".join(missing_required)
        )
    unsupported = sorted(set(relative_paths) - set(SUPPORTED_RESULT_PATHS))
    if unsupported:
        failures.append(
            "routing observations contain unsupported records: "
            + ", ".join(unsupported)
        )
    run_ids: list[str] = []
    for relative_path, record in observations:
        run_id = record.get("runId")
        if type(run_id) is str:
            run_ids.append(run_id)
        expected = EXPECTED_RESULT_BINDINGS.get(relative_path)
        if expected is None:
            failures.append(f"{relative_path} has no stable run binding")
            continue
        expected_run_id, expected_digest = expected
        if run_id != expected_run_id:
            failures.append(f"{relative_path}.runId drifted from its stable identity")
        binding = record.get("responseSchema")
        actual_schema_path = binding.get("path") if type(binding) is dict else None
        actual_digest = binding.get("sha256") if type(binding) is dict else None
        if actual_digest != expected_digest:
            failures.append(
                f"{relative_path}.responseSchema disagrees with its recorded run"
            )
        current_digest = response_schema_sha256_by_path.get(actual_schema_path)
        if actual_digest is not None and run_id != INITIAL_CODEX_RUN_ID and (
            current_digest is None or actual_digest != current_digest
        ):
            failures.append(
                f"{relative_path}.responseSchema does not bind its immutable model schema"
            )
        expected_subject = EXPECTED_RESULT_SUBJECTS.get(relative_path)
        if expected_subject is None:
            failures.append(
                f"{relative_path} cannot materialize before its immutable subject is bound"
            )
        elif record.get("axiom") != expected_subject:
            failures.append(
                f"{relative_path}.axiom disagrees with its immutable subject binding"
            )
        if relative_path in TERMINAL_ONLY_RESULT_PATHS:
            run = record.get("run")
            run_status = run.get("status") if type(run) is dict else None
            if run_status not in {"pass", "fail", "unknown"}:
                failures.append(
                    f"{relative_path} may be materialized only as a terminal run"
                )
        expected_outcome_digest = PRESERVED_OUTCOME_SHA256.get(run_id)
        if expected_outcome_digest is not None:
            outcome = {
                key: record.get(key) for key in ("run", "cases", "summary")
            }
            outcome_digest = hashlib.sha256(
                json.dumps(
                    outcome,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            if outcome_digest != expected_outcome_digest:
                failures.append(
                    f"{relative_path} rewrites a preserved terminal outcome"
                )
    if len(run_ids) != len(set(run_ids)):
        failures.append("routing observation run identities must be unique")
