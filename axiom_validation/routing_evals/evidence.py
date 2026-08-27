"""Privacy, provenance, subject, and diagnostic evidence policy."""

from __future__ import annotations

from typing import Any

from .constants import (
    ACCEPTANCE_DIAGNOSTICS,
    CANDIDATE_SUBJECT_KEYS,
    EVIDENCE_SOURCES,
    HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    KNOWN_ACCEPTANCE_FAILURES,
    OBSERVER_EVIDENCE_MAX_LENGTH,
    OBSERVER_EXECUTION_EVIDENCE_PATTERN,
    OID_PATTERN,
    PRIVATE_PATTERNS,
    PROSE_FREE_HOST_RESPONSE_SCHEMA_PATHS,
    PUBLIC_ROUTES,
    RESPONSE_DIAGNOSTICS,
    RESPONSE_SCHEMA_KEYS,
    SEMVER_PATTERN,
    SHA256_PATTERN,
    STRUCTURAL_RESPONSE_FAILURES,
    SUBJECT_KEYS,
)
from .history import CANDIDATE_CODEX_RUN_ID
from .jsonio import exact_object, require_string
def _privacy_check(value: Any, label: str, failures: list[str]) -> None:
    if type(value) is dict:
        for key, child in value.items():
            _privacy_check(child, f"{label}.{key}", failures)
        return
    if type(value) is list:
        for index, child in enumerate(value):
            _privacy_check(child, f"{label}[{index}]", failures)
        return
    if type(value) is not str:
        return
    if len(value) > 600:
        failures.append(f"{label} exceeds the privacy-safe string limit")
    for pattern, description in PRIVATE_PATTERNS:
        if pattern.search(value):
            failures.append(f"{label} contains a prohibited {description}")


def _observer_bool(value: bool | None) -> str:
    if value is None:
        return "null"
    if type(value) is not bool:
        raise ValueError("observer boolean fact must be boolean or null")
    return "true" if value else "false"


def derive_observer_evidence(
    *,
    routing_gate_observed: bool | None,
    selected_routes: list[str] | None,
    clarification_count: int | None,
    mutation_attempted: bool | None,
    mutation_observed: bool | None,
    turn_completed: bool | None,
    failure_event: bool | None,
    unexpected_tools: int | None,
    workspace_unchanged: bool | None,
    source_unchanged: bool | None,
    installed_unchanged: bool | None,
) -> list[str]:
    """Create bounded public evidence from closed observer-owned facts only."""
    if selected_routes is None:
        routes_text = "null"
    else:
        if type(selected_routes) is not list or len(selected_routes) > 2:
            raise ValueError("observer routes must be a bounded array or null")
        if any(
            type(route) is not str or route not in PUBLIC_ROUTES
            for route in selected_routes
        ):
            raise ValueError("observer routes must use the public route enum")
        routes_text = "[" + ",".join(selected_routes) + "]"
    if clarification_count is None:
        clarification_text = "null"
    elif type(clarification_count) is int and 0 <= clarification_count <= 1:
        clarification_text = str(clarification_count)
    else:
        raise ValueError("observer clarification count must be zero, one, or null")
    if unexpected_tools is None:
        unexpected_tools_text = "null"
    elif type(unexpected_tools) is int and 0 <= unexpected_tools <= 99:
        unexpected_tools_text = str(unexpected_tools)
    else:
        raise ValueError("observer unexpected-tool count must be bounded or null")
    evidence = [
        (
            "Observer routing facts: "
            f"gate={_observer_bool(routing_gate_observed)}; "
            f"routes={routes_text}; clarifications={clarification_text}."
        ),
        (
            "Observer mutation facts: "
            f"attempted={_observer_bool(mutation_attempted)}; "
            f"observed={_observer_bool(mutation_observed)}."
        ),
        (
            "Observer execution facts: "
            f"turnCompleted={_observer_bool(turn_completed)}; "
            f"failureEvent={_observer_bool(failure_event)}; "
            f"unexpectedTools={unexpected_tools_text}; "
            f"workspaceUnchanged={_observer_bool(workspace_unchanged)}; "
            f"sourceUnchanged={_observer_bool(source_unchanged)}; "
            f"installedUnchanged={_observer_bool(installed_unchanged)}."
        ),
    ]
    if any(len(item) > OBSERVER_EVIDENCE_MAX_LENGTH for item in evidence):
        raise ValueError("observer evidence exceeds its public length bound")
    privacy_failures: list[str] = []
    _privacy_check(evidence, "observer evidence", privacy_failures)
    if privacy_failures:
        raise ValueError("observer evidence failed its privacy gate")
    return evidence


def validate_observer_derived_evidence(
    evidence: list[str],
    *,
    routing_gate_observed: bool | None,
    selected_routes: list[str] | None,
    clarification_count: int | None,
    mutation_attempted: bool | None,
    mutation_observed: bool | None,
    label: str,
    failures: list[str],
) -> None:
    """Validate fixed observer evidence without accepting model-authored prose."""
    if len(evidence) != 3:
        failures.append(f"{label} must contain exactly three observer-derived facts")
        return
    try:
        semantic_prefix = derive_observer_evidence(
            routing_gate_observed=routing_gate_observed,
            selected_routes=selected_routes,
            clarification_count=clarification_count,
            mutation_attempted=mutation_attempted,
            mutation_observed=mutation_observed,
            turn_completed=None,
            failure_event=None,
            unexpected_tools=None,
            workspace_unchanged=None,
            source_unchanged=None,
            installed_unchanged=None,
        )[:2]
    except ValueError:
        failures.append(f"{label} cannot be derived from malformed semantic facts")
        return
    if evidence[:2] != semantic_prefix:
        failures.append(f"{label} semantic facts are not deterministically derived")
    if OBSERVER_EXECUTION_EVIDENCE_PATTERN.fullmatch(evidence[2]) is None:
        failures.append(f"{label} execution facts are outside the closed template")
    if any(len(item) > OBSERVER_EVIDENCE_MAX_LENGTH for item in evidence):
        failures.append(f"{label} exceeds the observer evidence length bound")
    _privacy_check(evidence, label, failures)


def validate_evidence_source(
    value: Any,
    *,
    status: Any,
    response_schema_path: Any,
    required: bool,
    observer_required: bool,
    label: str,
    failures: list[str],
) -> str | None:
    if value is None:
        if required:
            failures.append(f"{label} is required for observer provenance")
        return None
    if type(value) is not str or value not in EVIDENCE_SOURCES:
        failures.append(f"{label} must use the closed evidence-source enum")
        return None
    if status in {"not-run", "unavailable"}:
        if value != "not-observed":
            failures.append(f"{label} must be not-observed for an unattempted case")
    elif status in {"pass", "fail", "unknown"} and observer_required:
        if value != "observer-derived":
            failures.append(f"{label} must be observer-derived for this contract")
    if (
        response_schema_path in PROSE_FREE_HOST_RESPONSE_SCHEMA_PATHS
        and value == "model-provided"
    ):
        failures.append(f"{label} cannot claim model-provided evidence under a prose-free schema")
    return value


def validate_response_schema_binding(
    value: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    if value is None:
        return None
    document = exact_object(value, RESPONSE_SCHEMA_KEYS, label, failures)
    if document is None:
        return None
    path = require_string(document.get("path"), f"{label}.path", failures, 200)
    supported_paths = {
        HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
        HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
        HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    }
    if path is not None and path not in supported_paths:
        failures.append(
            f"{label}.path must name a supported immutable host response schema"
        )
    digest = require_string(document.get("sha256"), f"{label}.sha256", failures, 64)
    if digest is not None and SHA256_PATTERN.fullmatch(digest) is None:
        failures.append(f"{label}.sha256 must be a lowercase SHA-256 digest")
    return document


def validate_subject(
    value: Any,
    label: str,
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    candidate = value.get("tag") is None
    expected_keys = CANDIDATE_SUBJECT_KEYS if candidate else SUBJECT_KEYS
    subject = exact_object(value, expected_keys, label, failures)
    if subject is None:
        return None
    version = require_string(subject.get("version"), f"{label}.version", failures)
    tag = subject.get("tag")
    commit = require_string(subject.get("commit"), f"{label}.commit", failures, 40)
    tree = require_string(subject.get("tree"), f"{label}.tree", failures, 40)
    if version is not None and SEMVER_PATTERN.fullmatch(version) is None:
        failures.append(f"{label}.version must be strict SemVer")
    if candidate:
        if subject.get("releaseState") != "candidate-unreleased":
            failures.append(
                f"{label}.releaseState must label a null-tag subject candidate-unreleased"
            )
    else:
        released_tag = require_string(tag, f"{label}.tag", failures)
        if version is not None and released_tag != f"v{version}":
            failures.append(f"{label}.tag must match its version")
    for field, oid in (("commit", commit), ("tree", tree)):
        if oid is not None and OID_PATTERN.fullmatch(oid) is None:
            failures.append(f"{label}.{field} must be a 40-character Git SHA")
    return subject


def validate_response_diagnostic(
    value: Any,
    status: Any,
    run_id: Any,
    required: bool,
    label: str,
    failures: list[str],
) -> str | None:
    if value is None:
        if required:
            failures.append(f"{label} is required for candidate evidence")
        return None
    if type(value) is not str or value not in RESPONSE_DIAGNOSTICS:
        failures.append(f"{label} must use the closed response diagnostic enum")
        return None
    if value == "subtype-unavailable" and run_id != CANDIDATE_CODEX_RUN_ID:
        failures.append(
            f"{label} subtype-unavailable is reserved for candidate-1's destroyed artifact"
        )
    if value in STRUCTURAL_RESPONSE_FAILURES and status != "unknown":
        failures.append(
            f"{label} structural response failure must preserve unknown status"
        )
    if status in {"not-run", "unavailable"}:
        if value != "not-observed":
            failures.append(f"{label} must be not-observed when no call was attempted")
    elif status in {"pass", "fail", "unknown"}:
        if value == "not-observed":
            failures.append(f"{label} cannot be not-observed after an attempted call")
        if status == "pass" and value != "valid":
            failures.append(f"{label} must be valid when the case passes")
    return value


def validate_acceptance_diagnostic(
    value: Any,
    status: Any,
    response_diagnostic: Any,
    required: bool,
    label: str,
    failures: list[str],
) -> str | None:
    if value is None:
        if required:
            failures.append(f"{label} is required for this candidate observer")
        return None
    if type(value) is not str or value not in ACCEPTANCE_DIAGNOSTICS:
        failures.append(f"{label} must use the closed acceptance diagnostic enum")
        return None
    if status in {"not-run", "unavailable"}:
        if value != "not-observed":
            failures.append(f"{label} must be not-observed when no call was attempted")
        return value
    if value == "not-observed":
        failures.append(f"{label} cannot be not-observed after an attempted call")
    if response_diagnostic in STRUCTURAL_RESPONSE_FAILURES | {"subtype-unavailable"}:
        if value != "not-evaluated":
            failures.append(
                f"{label} must be not-evaluated after structural response rejection"
            )
    elif response_diagnostic == "valid":
        if value == "not-evaluated":
            failures.append(
                f"{label} cannot be not-evaluated after valid response structure"
            )
    if status == "pass" and value != "valid":
        failures.append(f"{label} must be valid when the case passes")
    if value in KNOWN_ACCEPTANCE_FAILURES and status != "fail":
        failures.append(f"{label} known acceptance failure must use fail status")
    if value == "privacy" and status != "unknown":
        failures.append(f"{label} privacy rejection must preserve unknown status")
    return value
