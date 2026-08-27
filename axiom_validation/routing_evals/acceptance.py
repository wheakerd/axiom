"""Host response structural and offline acceptance policy."""

from __future__ import annotations

from typing import Any

from .constants import (
    HISTORICAL_PUBLIC_ROUTES,
    HOST_RESPONSE_KEYS,
    HOST_RESPONSE_V2_KEYS,
    PUBLIC_ROUTES,
)
from .evidence import _privacy_check
from .jsonio import (
    exact_object,
    require_bool,
    require_int,
    require_model_string_list,
)
def validate_host_response_structure(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Apply exactly the immutable V1 model-facing JSON Schema constraints."""
    document = exact_object(response, HOST_RESPONSE_KEYS, label, failures)
    if document is None:
        return None
    require_bool(
        document.get("routingGateObserved"),
        f"{label}.routingGateObserved",
        failures,
    )
    require_model_string_list(
        document.get("selectedRoutes"),
        f"{label}.selectedRoutes",
        failures,
        minimum_items=0,
        maximum_items=2,
        allowed=HISTORICAL_PUBLIC_ROUTES,
    )
    clarification = require_int(
        document.get("clarificationCount"),
        f"{label}.clarificationCount",
        failures,
    )
    if clarification is not None and clarification > 1:
        failures.append(f"{label}.clarificationCount must be <= 1")
    require_bool(
        document.get("mutationAttempted"),
        f"{label}.mutationAttempted",
        failures,
    )
    require_bool(
        document.get("mutationObserved"),
        f"{label}.mutationObserved",
        failures,
    )
    require_model_string_list(
        document.get("evidence"),
        f"{label}.evidence",
        failures,
        minimum_items=1,
        maximum_items=3,
    )
    return document


def classify_host_response_acceptance(response: Any) -> str:
    """Return one privacy-safe category for constraints omitted from the schema."""
    structural_failures: list[str] = []
    document = validate_host_response_structure(
        response,
        "bounded response",
        structural_failures,
    )
    if document is None or structural_failures:
        return "not-evaluated"
    evidence = document["evidence"]
    privacy_failures: list[str] = []
    _privacy_check(evidence, "bounded response.evidence", privacy_failures)
    if privacy_failures:
        return "privacy"
    routes = document["selectedRoutes"]
    if len(routes) != len(set(routes)):
        return "selected-routes-duplicate"
    if any(item == "" for item in evidence):
        return "evidence-empty-string"
    if any(len(item) > 240 for item in evidence):
        return "evidence-overlength"
    if len(evidence) != len(set(evidence)):
        return "evidence-duplicate"
    return "valid"


def validate_host_response(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Validate model structure, then independent publication acceptance."""
    structural_failures: list[str] = []
    document = validate_host_response_structure(response, label, structural_failures)
    failures.extend(structural_failures)
    if document is None or structural_failures:
        return document
    diagnostic = classify_host_response_acceptance(document)
    if diagnostic != "valid":
        failures.append(
            f"{label} fails the privacy-safe response acceptance gate: {diagnostic}"
        )
    return document


def validate_host_response_v2_structure(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Apply exactly the V2 model-facing JSON Schema constraints."""
    document = exact_object(response, HOST_RESPONSE_V2_KEYS, label, failures)
    if document is None:
        return None
    require_bool(
        document.get("routingGateObserved"),
        f"{label}.routingGateObserved",
        failures,
    )
    require_model_string_list(
        document.get("selectedRoutes"),
        f"{label}.selectedRoutes",
        failures,
        minimum_items=0,
        maximum_items=2,
        allowed=HISTORICAL_PUBLIC_ROUTES,
    )
    clarification = require_int(
        document.get("clarificationCount"),
        f"{label}.clarificationCount",
        failures,
    )
    if clarification is not None and clarification > 1:
        failures.append(f"{label}.clarificationCount must be <= 1")
    require_bool(
        document.get("mutationAttempted"),
        f"{label}.mutationAttempted",
        failures,
    )
    require_bool(
        document.get("mutationObserved"),
        f"{label}.mutationObserved",
        failures,
    )
    return document


def classify_host_response_v2_acceptance(response: Any) -> str:
    """Classify the only semantic constraint omitted from the V2 schema."""
    structural_failures: list[str] = []
    document = validate_host_response_v2_structure(
        response,
        "bounded response",
        structural_failures,
    )
    if document is None or structural_failures:
        return "not-evaluated"
    routes = document["selectedRoutes"]
    if len(routes) != len(set(routes)):
        return "selected-routes-duplicate"
    return "valid"


def validate_host_response_v2(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Validate V2 model structure, then its independent acceptance gate."""
    structural_failures: list[str] = []
    document = validate_host_response_v2_structure(
        response,
        label,
        structural_failures,
    )
    failures.extend(structural_failures)
    if document is None or structural_failures:
        return document
    diagnostic = classify_host_response_v2_acceptance(document)
    if diagnostic != "valid":
        failures.append(
            f"{label} fails the V2 response acceptance gate: {diagnostic}"
        )
    return document


def validate_host_response_v3_structure(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Apply exactly the seven-route V3 model-facing JSON Schema constraints."""
    document = exact_object(response, HOST_RESPONSE_V2_KEYS, label, failures)
    if document is None:
        return None
    require_bool(
        document.get("routingGateObserved"),
        f"{label}.routingGateObserved",
        failures,
    )
    require_model_string_list(
        document.get("selectedRoutes"),
        f"{label}.selectedRoutes",
        failures,
        minimum_items=0,
        maximum_items=2,
        allowed=PUBLIC_ROUTES,
    )
    clarification = require_int(
        document.get("clarificationCount"),
        f"{label}.clarificationCount",
        failures,
    )
    if clarification is not None and clarification > 1:
        failures.append(f"{label}.clarificationCount must be <= 1")
    require_bool(
        document.get("mutationAttempted"),
        f"{label}.mutationAttempted",
        failures,
    )
    require_bool(
        document.get("mutationObserved"),
        f"{label}.mutationObserved",
        failures,
    )
    return document


def classify_host_response_v3_acceptance(response: Any) -> str:
    """Classify duplicate routes omitted from the V3 model-facing schema."""
    structural_failures: list[str] = []
    document = validate_host_response_v3_structure(
        response,
        "bounded response",
        structural_failures,
    )
    if document is None or structural_failures:
        return "not-evaluated"
    routes = document["selectedRoutes"]
    if len(routes) != len(set(routes)):
        return "selected-routes-duplicate"
    return "valid"


def validate_host_response_v3(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Validate V3 model structure and its independent acceptance gate."""
    structural_failures: list[str] = []
    document = validate_host_response_v3_structure(
        response,
        label,
        structural_failures,
    )
    failures.extend(structural_failures)
    if document is None or structural_failures:
        return document
    diagnostic = classify_host_response_v3_acceptance(document)
    if diagnostic != "valid":
        failures.append(
            f"{label} fails the V3 response acceptance gate: {diagnostic}"
        )
    return document
