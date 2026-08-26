"""Deterministic routing-context proxy and evidence policy."""

from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

from .context import RELEASE_VERSION, REPOSITORY_ROOT, display_path


CONTEXT_BUDGET_ROOT = REPOSITORY_ROOT / "evals" / "context-budget"
CONTEXT_BUDGET_SCHEMA = CONTEXT_BUDGET_ROOT / "schema-v1.json"
CONTEXT_BUDGET_RECORD = (
    CONTEXT_BUDGET_ROOT / "results" / f"v{RELEASE_VERSION}.json"
)
ROUTING_GATE_PATH = REPOSITORY_ROOT / "skills" / "using-axiom" / "SKILL.md"
ROUTING_CORPUS_ROOT = REPOSITORY_ROOT / "evals" / "routing"
MAX_JSON_BYTES = 256 * 1024
DIRECT_REFERENCE_PATTERN = re.compile(r"(?<![A-Za-z0-9_.-])references/[A-Za-z0-9._/-]+\.md")

BASELINE_RELEASE = {
    "version": "0.7.9",
    "tag": "v0.7.9",
    "commit": "4c24ba6c016945038778475ce6b69ac9e9a5ce3b",
    "tree": "719622eff9654dd1050863213d2bf81d3455d6f6",
}
BASELINE_SHA256 = "1380155863715c28b91223823f3eaadb96bcefbe2482b444ef9dc8e8b62fe011"
BASELINE_METRICS = {
    "classification": "exact-static-counts-used-as-context-proxies",
    "utf8Bytes": 5899,
    "whitespaceDelimitedWords": 757,
    "logicalLines": 107,
    "directReferenceCount": 1,
    "directReferences": ["references/updating.md"],
    "estimatedTokens": {
        "classification": "estimate",
        "method": "ceil(utf8-bytes/4)",
        "comparisonScope": "same-English-Markdown-surface-only",
        "value": 1475,
    },
}
ABSOLUTE_REVIEW_BYTES = 256
RELATIVE_REVIEW_BASIS_POINTS = 500
HOSTS = ("codex", "claude-code")
CURRENT_LIFECYCLE_HOST_STATUSES = {
    "codex": "not-run",
    "claude-code": "unavailable",
}
EXPECTED_HOST_METRICS = {
    "codex": {
        "host": "codex",
        "status": "not-run",
        "exactUsageExposed": False,
        "inputTokens": None,
        "cachedInputTokens": None,
        "credits": None,
        "wallClockMilliseconds": None,
        "reason": (
            "The v0.8.6 release-evidence hardening changes no installed routing; "
            "no current Codex host usage or lifecycle observation was run, and prior "
            "v0.8.5 observations remain separate historical evidence."
        ),
    },
    "claude-code": {
        "host": "claude-code",
        "status": "unavailable",
        "exactUsageExposed": False,
        "inputTokens": None,
        "cachedInputTokens": None,
        "credits": None,
        "wallClockMilliseconds": None,
        "reason": (
            "No authenticated Claude Code subscription or session was available; "
            "exact usage and lifecycle observation were unavailable and not run."
        ),
    },
}
EXPECTED_SCENARIOS = (
    (
        "fresh-startup-no-route",
        "fresh",
        "startup",
        "not-applicable",
        ("no-route-readme-summary-001",),
        1,
    ),
    (
        "fresh-startup-routed",
        "fresh",
        "startup",
        "not-applicable",
        ("agent-plugin-architect-canonical-001",),
        1,
    ),
    (
        "resume-no-route",
        "resumed",
        "resume",
        "not-applicable",
        ("no-route-readme-summary-001",),
        1,
    ),
    (
        "clear-routed",
        "cleared",
        "clear",
        "not-applicable",
        ("agent-plugin-architect-paraphrase-001",),
        1,
    ),
    (
        "manual-compaction-no-route",
        "post-compaction",
        "compact",
        "manual",
        ("compaction-no-route-manual-001",),
        1,
    ),
    (
        "automatic-compaction-routed",
        "post-compaction",
        "compact",
        "automatic",
        ("compaction-plugin-architecture-001",),
        1,
    ),
    (
        "unchanged-session-repeated-no-route",
        "unchanged-session",
        "startup",
        "not-applicable",
        (
            "no-route-readme-summary-001",
            "no-route-readme-summary-001",
            "no-route-readme-summary-001",
        ),
        1,
    ),
)

TOP_LEVEL_KEYS = frozenset(
    {
        "$schema",
        "schemaVersion",
        "recordId",
        "targetRelease",
        "surface",
        "measurementBoundary",
        "baseline",
        "candidate",
        "reviewThreshold",
        "comparison",
        "routingQuality",
        "hostMetrics",
        "scenarios",
    }
)
METRIC_KEYS = frozenset(
    {
        "classification",
        "utf8Bytes",
        "whitespaceDelimitedWords",
        "logicalLines",
        "directReferenceCount",
        "directReferences",
        "estimatedTokens",
    }
)
HOST_OBSERVATION_KEYS = frozenset(
    {
        "host",
        "status",
        "observedInjectionCount",
        "duplicateInjectionDetected",
        "injections",
        "reason",
    }
)


class DuplicateJsonKeyError(ValueError):
    """Raised when a protected JSON object repeats a key."""


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def exact_object(
    value: Any,
    label: str,
    expected_keys: frozenset[str],
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    missing = sorted(expected_keys - set(value))
    unknown = sorted(set(value) - expected_keys)
    if missing:
        failures.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{label} contains unknown fields: {', '.join(unknown)}")
    return value


def load_json(path: Path, failures: list[str]) -> dict[str, Any] | None:
    label = display_path(path)
    try:
        metadata = path.lstat()
    except OSError as error:
        failures.append(f"cannot inspect {label}: {error}")
        return None
    if stat.S_ISLNK(metadata.st_mode):
        failures.append(f"{label} must not be a symbolic link")
        return None
    if not stat.S_ISREG(metadata.st_mode):
        failures.append(f"{label} must be a regular file")
        return None
    if metadata.st_size > MAX_JSON_BYTES:
        failures.append(f"{label} exceeds the {MAX_JSON_BYTES}-byte JSON limit")
        return None
    try:
        text = path.read_text(encoding="utf-8")
        document = json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKeyError) as error:
        failures.append(f"invalid JSON in {label}: {error}")
        return None
    if type(document) is not dict:
        failures.append(f"{label} must contain a top-level object")
        return None
    return document


def measure_markdown(path: Path) -> dict[str, Any]:
    """Return exact static counts and one clearly labeled token estimate."""
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("measurement input must be a regular non-symbolic-link file")
    data = path.read_bytes()
    text = data.decode("utf-8")
    references = sorted(set(DIRECT_REFERENCE_PATTERN.findall(text)))
    return {
        "classification": "exact-static-counts-used-as-context-proxies",
        "utf8Bytes": len(data),
        "whitespaceDelimitedWords": len(re.findall(r"\S+", text)),
        "logicalLines": len(text.splitlines()),
        "directReferenceCount": len(references),
        "directReferences": references,
        "estimatedTokens": {
            "classification": "estimate",
            "method": "ceil(utf8-bytes/4)",
            "comparisonScope": "same-English-Markdown-surface-only",
            "value": (len(data) + 3) // 4,
        },
    }


def routing_corpus_metrics(
    root: Path = ROUTING_CORPUS_ROOT,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str]]:
    """Bind the exact fixed workload without treating contracts as host results."""
    failures: list[str] = []
    cases: dict[str, dict[str, Any]] = {}
    hasher = hashlib.sha256()
    if not root.is_dir():
        failures.append("evals/routing must be a directory")
    paths = sorted(root.glob("*.jsonl"))
    if not paths:
        failures.append("evals/routing contains no JSONL workload files")
    for path in paths:
        relative_path = path.relative_to(REPOSITORY_ROOT).as_posix()
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeError) as error:
            failures.append(f"cannot read {relative_path}: {error}")
            continue
        hasher.update(relative_path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(data)
        hasher.update(b"\0")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line:
                failures.append(f"{relative_path}:{line_number} must not be blank")
                continue
            try:
                case = json.loads(line, object_pairs_hook=reject_duplicate_json_keys)
            except (json.JSONDecodeError, DuplicateJsonKeyError) as error:
                failures.append(f"invalid JSON in {relative_path}:{line_number}: {error}")
                continue
            if type(case) is not dict:
                failures.append(f"{relative_path}:{line_number} must be an object")
                continue
            case_id = case.get("id")
            if type(case_id) is not str or not case_id:
                failures.append(f"{relative_path}:{line_number}.id must be a string")
                continue
            if case_id in cases:
                failures.append(f"routing case ID {case_id!r} is duplicated")
                continue
            cases[case_id] = case

    no_route_count = sum(
        type(case.get("expectedRoutes")) is list and not case["expectedRoutes"]
        for case in cases.values()
    )
    metrics = {
        "classification": "static-contract-workload-identity",
        "path": "evals/routing",
        "fileCount": len(paths),
        "caseCount": len(cases),
        "routedCaseCount": len(cases) - no_route_count,
        "noRouteCaseCount": no_route_count,
        "sha256": hasher.hexdigest(),
    }
    return metrics, cases, failures


def threshold_assessment(baseline_bytes: int, candidate_bytes: int) -> dict[str, Any]:
    delta = candidate_bytes - baseline_bytes
    absolute_reached = delta >= ABSOLUTE_REVIEW_BYTES
    relative_reached = (
        delta > 0
        and delta * 10_000 >= baseline_bytes * RELATIVE_REVIEW_BASIS_POINTS
    )
    meaningful = absolute_reached or relative_reached
    if meaningful:
        review_status = "reviewed"
    elif delta > 0:
        review_status = "below-threshold"
    else:
        review_status = "not-required"
    return {
        "utf8ByteDelta": delta,
        "absoluteThresholdReached": absolute_reached,
        "relativeThresholdReached": relative_reached,
        "meaningfulIncrease": meaningful,
        "reviewStatus": review_status,
    }


def validate_reduction_experiment(
    value: Any,
    baseline_sha256: str,
    candidate_sha256: str,
    baseline_bytes: int,
    candidate_bytes: int,
    corpus: dict[str, Any],
    failures: list[str],
) -> None:
    """Require equivalent routed and no-route evidence for every real reduction."""
    if candidate_bytes >= baseline_bytes:
        if value is not None:
            failures.append("routingQuality.reductionExperiment must be null without a reduction")
        return
    experiment = exact_object(
        value,
        "routingQuality.reductionExperiment",
        frozenset({"equivalentWorkload", "before", "after"}),
        failures,
    )
    if experiment is None:
        failures.append(
            "a routing-gate reduction requires equivalent before/after routing and no-route evidence"
        )
        return
    if experiment.get("equivalentWorkload") is not True:
        failures.append("routingQuality.reductionExperiment.equivalentWorkload must be true")

    expected_surfaces = (baseline_sha256, candidate_sha256)
    observations: list[dict[str, Any] | None] = []
    for phase, expected_surface in zip(("before", "after"), expected_surfaces):
        observation = exact_object(
            experiment.get(phase),
            f"routingQuality.reductionExperiment.{phase}",
            frozenset(
                {
                    "classification",
                    "surfaceSha256",
                    "workloadSha256",
                    "caseCount",
                    "noRouteCaseCount",
                    "routingStatus",
                    "noRouteStatus",
                }
            ),
            failures,
        )
        observations.append(observation)
        if observation is None:
            continue
        if observation.get("classification") not in {
            "static-contract-validation",
            "host-observed",
        }:
            failures.append(
                f"routingQuality.reductionExperiment.{phase}.classification is invalid"
            )
        expected_values = {
            "surfaceSha256": expected_surface,
            "workloadSha256": corpus["sha256"],
            "caseCount": corpus["caseCount"],
            "noRouteCaseCount": corpus["noRouteCaseCount"],
            "routingStatus": "pass",
            "noRouteStatus": "pass",
        }
        for field, expected in expected_values.items():
            if observation.get(field) != expected:
                failures.append(
                    f"routingQuality.reductionExperiment.{phase}.{field} must be {expected!r}"
                )
    if all(observations) and observations[0].get("classification") != observations[1].get(
        "classification"
    ):
        failures.append("before/after reduction evidence must use the same classification")


def validate_host_observation(
    value: Any,
    *,
    label: str,
    lifecycle_source: str,
    request_count: int,
    expected_injection_count: int,
    candidate_sha256: str,
    failures: list[str],
) -> bool | None:
    """Validate observation arithmetic and return the derived duplicate state."""
    observation = exact_object(value, label, HOST_OBSERVATION_KEYS, failures)
    if observation is None:
        return None
    host = observation.get("host")
    status_value = observation.get("status")
    count = observation.get("observedInjectionCount")
    duplicate = observation.get("duplicateInjectionDetected")
    injections = observation.get("injections")
    reason = observation.get("reason")
    if host not in HOSTS:
        failures.append(f"{label}.host is invalid")
    if status_value not in {"pass", "fail", "not-run", "unavailable"}:
        failures.append(f"{label}.status is invalid")
    if type(reason) is not str or not reason or len(reason) > 300:
        failures.append(f"{label}.reason must be a bounded non-empty string")
    if type(injections) is not list:
        failures.append(f"{label}.injections must be an array")
        injections = []

    if status_value in {"not-run", "unavailable"}:
        if count is not None or duplicate is not None or injections:
            failures.append(
                f"{label} unobserved status requires null counts and no injection events"
            )
        return None

    if type(count) is not int or isinstance(count, bool) or count < 0:
        failures.append(f"{label}.observedInjectionCount must be a non-negative integer")
        return None
    if type(duplicate) is not bool:
        failures.append(f"{label}.duplicateInjectionDetected must be a boolean")
        return None
    if count != len(injections):
        failures.append(f"{label}.observedInjectionCount must equal the injection array length")
    derived_duplicate = count > expected_injection_count
    if duplicate != derived_duplicate:
        failures.append(
            f"{label}.duplicateInjectionDetected must equal the derived count boundary"
        )

    for index, injection_value in enumerate(injections):
        injection_label = f"{label}.injections[{index}]"
        injection = exact_object(
            injection_value,
            injection_label,
            frozenset({"sequence", "requestOrdinal", "lifecycleSource", "contentSha256"}),
            failures,
        )
        if injection is None:
            continue
        if injection.get("sequence") != index + 1:
            failures.append(f"{injection_label}.sequence must be {index + 1}")
        request_ordinal = injection.get("requestOrdinal")
        if (
            type(request_ordinal) is not int
            or isinstance(request_ordinal, bool)
            or not 0 <= request_ordinal <= request_count
        ):
            failures.append(
                f"{injection_label}.requestOrdinal must be between 0 and {request_count}"
            )
        if injection.get("lifecycleSource") != lifecycle_source:
            failures.append(
                f"{injection_label}.lifecycleSource must be {lifecycle_source!r}"
            )
        if injection.get("contentSha256") != candidate_sha256:
            failures.append(f"{injection_label}.contentSha256 must bind the candidate gate")

    if status_value == "pass" and (
        count != expected_injection_count or derived_duplicate
    ):
        failures.append(f"{label} cannot pass with missing or duplicate injection")
    return derived_duplicate


def _check_metric_shape(value: Any, label: str, failures: list[str]) -> dict[str, Any] | None:
    initial_failure_count = len(failures)
    metrics = exact_object(value, label, METRIC_KEYS, failures)
    if metrics is None:
        return None
    estimate = exact_object(
        metrics.get("estimatedTokens"),
        f"{label}.estimatedTokens",
        frozenset({"classification", "method", "comparisonScope", "value"}),
        failures,
    )
    if metrics.get("classification") != "exact-static-counts-used-as-context-proxies":
        failures.append(f"{label}.classification is invalid")
    integer_fields = (
        "utf8Bytes",
        "whitespaceDelimitedWords",
        "logicalLines",
        "directReferenceCount",
    )
    for field in integer_fields:
        field_value = metrics.get(field)
        if type(field_value) is not int or isinstance(field_value, bool) or field_value < 0:
            failures.append(f"{label}.{field} must be a non-negative integer")
    references = metrics.get("directReferences")
    if type(references) is not list or references != sorted(set(references)):
        failures.append(f"{label}.directReferences must be a sorted unique array")
    elif any(type(item) is not str for item in references):
        failures.append(f"{label}.directReferences entries must be strings")
    elif metrics.get("directReferenceCount") != len(references):
        failures.append(f"{label}.directReferenceCount must match directReferences")
    if estimate is not None:
        byte_count = metrics.get("utf8Bytes")
        if type(byte_count) is int and not isinstance(byte_count, bool) and byte_count >= 0:
            expected_estimate = {
                "classification": "estimate",
                "method": "ceil(utf8-bytes/4)",
                "comparisonScope": "same-English-Markdown-surface-only",
                "value": (byte_count + 3) // 4,
            }
            if estimate != expected_estimate:
                failures.append(f"{label}.estimatedTokens is not the documented estimate")
    return metrics if len(failures) == initial_failure_count else None


def check_context_budget(failures: list[str]) -> int:
    """Validate the current release's routing-context budget and observations."""
    schema = load_json(CONTEXT_BUDGET_SCHEMA, failures)
    if schema is not None:
        if schema.get("$id") != "https://github.com/wheakerd/axiom/evals/context-budget/schema-v1.json":
            failures.append("evals/context-budget/schema-v1.json has an unexpected $id")
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            failures.append("evals/context-budget/schema-v1.json must close the top-level object")

    document = load_json(CONTEXT_BUDGET_RECORD, failures)
    if document is None:
        return 0
    exact_object(document, display_path(CONTEXT_BUDGET_RECORD), TOP_LEVEL_KEYS, failures)
    if document.get("$schema") != "../schema-v1.json":
        failures.append("context-budget record must reference ../schema-v1.json")
    if document.get("schemaVersion") != "1":
        failures.append("context-budget record schemaVersion must be '1'")
    expected_record_id = f"routing-context-budget-v{RELEASE_VERSION.replace('.', '-')}"
    if document.get("recordId") != expected_record_id:
        failures.append(f"context-budget recordId must be {expected_record_id!r}")

    target = exact_object(
        document.get("targetRelease"),
        "targetRelease",
        frozenset({"version", "commit", "binding"}),
        failures,
    )
    if target is not None and target != {
        "version": RELEASE_VERSION,
        "commit": None,
        "binding": "pending-immutable-release",
    }:
        failures.append("targetRelease must remain pending and match both manifests")

    surface = exact_object(
        document.get("surface"),
        "surface",
        frozenset({"path", "language", "alwaysLoaded"}),
        failures,
    )
    if surface is not None and surface != {
        "path": "skills/using-axiom/SKILL.md",
        "language": "en",
        "alwaysLoaded": True,
    }:
        failures.append("surface must identify the English always-loaded routing gate")

    boundary = exact_object(
        document.get("measurementBoundary"),
        "measurementBoundary",
        frozenset(
            {
                "staticCounts",
                "estimatedTokens",
                "exactHostUsage",
                "modelOrReasoningChanged",
                "networkOrTelemetryUsed",
                "volatilePricingIncluded",
            }
        ),
        failures,
    )
    expected_boundary = {
        "staticCounts": "proxy",
        "estimatedTokens": "estimate",
        "exactHostUsage": "not-run",
        "modelOrReasoningChanged": False,
        "networkOrTelemetryUsed": False,
        "volatilePricingIncluded": False,
    }
    if boundary is not None and boundary != expected_boundary:
        failures.append("measurementBoundary must preserve the static-only non-mutation boundary")

    baseline = exact_object(
        document.get("baseline"),
        "baseline",
        frozenset({"release", "sha256", "metrics"}),
        failures,
    )
    baseline_metrics = None
    if baseline is not None:
        if baseline.get("release") != BASELINE_RELEASE:
            failures.append("baseline.release must bind the immutable v0.7.9 source")
        if baseline.get("sha256") != BASELINE_SHA256:
            failures.append("baseline.sha256 must bind the released routing gate")
        baseline_metrics = _check_metric_shape(
            baseline.get("metrics"), "baseline.metrics", failures
        )
        if baseline_metrics is not None and baseline_metrics != BASELINE_METRICS:
            failures.append("baseline.metrics drifted from the immutable v0.7.9 measurement")

    candidate = exact_object(
        document.get("candidate"),
        "candidate",
        frozenset({"sha256", "metrics"}),
        failures,
    )
    candidate_metrics = None
    try:
        current_sha256 = hashlib.sha256(ROUTING_GATE_PATH.read_bytes()).hexdigest()
        current_metrics = measure_markdown(ROUTING_GATE_PATH)
    except (OSError, UnicodeError, ValueError) as error:
        failures.append(f"cannot measure skills/using-axiom/SKILL.md: {error}")
        current_sha256 = ""
        current_metrics = None
    if candidate is not None:
        if candidate.get("sha256") != current_sha256:
            failures.append("candidate.sha256 does not match skills/using-axiom/SKILL.md")
        candidate_metrics = _check_metric_shape(
            candidate.get("metrics"), "candidate.metrics", failures
        )
        if (
            candidate_metrics is not None
            and current_metrics is not None
            and candidate_metrics != current_metrics
        ):
            failures.append("candidate.metrics are not reproducible from the routing gate")

    threshold = exact_object(
        document.get("reviewThreshold"),
        "reviewThreshold",
        frozenset(
            {
                "comparison",
                "absoluteUtf8Bytes",
                "relativeBasisPoints",
                "operator",
                "effect",
            }
        ),
        failures,
    )
    expected_threshold = {
        "comparison": "cumulative-from-immutable-baseline",
        "absoluteUtf8Bytes": ABSOLUTE_REVIEW_BYTES,
        "relativeBasisPoints": RELATIVE_REVIEW_BASIS_POINTS,
        "operator": "either",
        "effect": "review-and-justify-not-automatic-rejection",
    }
    if threshold is not None and threshold != expected_threshold:
        failures.append("reviewThreshold must retain the cumulative review-only boundary")

    comparison = exact_object(
        document.get("comparison"),
        "comparison",
        frozenset(
            {
                "method",
                "utf8ByteDelta",
                "wordDelta",
                "lineDelta",
                "referenceDelta",
                "estimatedTokenDelta",
                "absoluteThresholdReached",
                "relativeThresholdReached",
                "meaningfulIncrease",
                "reviewStatus",
                "justification",
            }
        ),
        failures,
    )
    if baseline_metrics is not None and candidate_metrics is not None and comparison is not None:
        assessment = threshold_assessment(
            baseline_metrics["utf8Bytes"], candidate_metrics["utf8Bytes"]
        )
        expected_comparison = {
            "method": "same-English-Markdown-surface",
            "utf8ByteDelta": assessment["utf8ByteDelta"],
            "wordDelta": candidate_metrics["whitespaceDelimitedWords"]
            - baseline_metrics["whitespaceDelimitedWords"],
            "lineDelta": candidate_metrics["logicalLines"] - baseline_metrics["logicalLines"],
            "referenceDelta": candidate_metrics["directReferenceCount"]
            - baseline_metrics["directReferenceCount"],
            "estimatedTokenDelta": candidate_metrics["estimatedTokens"]["value"]
            - baseline_metrics["estimatedTokens"]["value"],
            "absoluteThresholdReached": assessment["absoluteThresholdReached"],
            "relativeThresholdReached": assessment["relativeThresholdReached"],
            "meaningfulIncrease": assessment["meaningfulIncrease"],
            "reviewStatus": assessment["reviewStatus"],
        }
        for field, expected in expected_comparison.items():
            if comparison.get(field) != expected:
                failures.append(f"comparison.{field} must be {expected!r}")
        justification = comparison.get("justification")
        if assessment["meaningfulIncrease"]:
            if type(justification) is not str or len(justification.strip()) < 40:
                failures.append("a meaningful increase requires a substantive review justification")
        elif justification is not None:
            failures.append("comparison.justification must be null when review is not required")

    corpus, corpus_cases, corpus_failures = routing_corpus_metrics()
    failures.extend(corpus_failures)
    routing_quality = exact_object(
        document.get("routingQuality"),
        "routingQuality",
        frozenset({"workload", "reductionPolicy", "reductionExperiment"}),
        failures,
    )
    if routing_quality is not None:
        if routing_quality.get("workload") != corpus:
            failures.append("routingQuality.workload does not match the fixed routing corpus")
        expected_reduction_policy = {
            "requiredForAnyReduction": True,
            "sameWorkloadRequired": True,
            "requiredResults": ["routing", "no-route"],
            "requiredStatus": "pass",
            "staticAndHostEvidenceRemainDistinct": True,
        }
        if routing_quality.get("reductionPolicy") != expected_reduction_policy:
            failures.append("routingQuality.reductionPolicy is incomplete")
        if baseline_metrics is not None and candidate_metrics is not None:
            validate_reduction_experiment(
                routing_quality.get("reductionExperiment"),
                BASELINE_SHA256,
                current_sha256,
                baseline_metrics["utf8Bytes"],
                candidate_metrics["utf8Bytes"],
                corpus,
                failures,
            )

    host_metrics = document.get("hostMetrics")
    if type(host_metrics) is not list or len(host_metrics) != len(HOSTS):
        failures.append("hostMetrics must contain one ordered entry per supported host")
        host_metrics = []
    for index, expected_host in enumerate(HOSTS):
        if index >= len(host_metrics):
            break
        metric = exact_object(
            host_metrics[index],
            f"hostMetrics[{index}]",
            frozenset(
                {
                    "host",
                    "status",
                    "exactUsageExposed",
                    "inputTokens",
                    "cachedInputTokens",
                    "credits",
                    "wallClockMilliseconds",
                    "reason",
                }
            ),
            failures,
        )
        if metric is None:
            continue
        if metric.get("host") != expected_host:
            failures.append(f"hostMetrics[{index}].host must be {expected_host!r}")
        if metric != EXPECTED_HOST_METRICS[expected_host]:
            failures.append(
                f"hostMetrics[{index}] must preserve the exact scoped evidence boundary"
            )

    scenarios = document.get("scenarios")
    if type(scenarios) is not list or len(scenarios) != len(EXPECTED_SCENARIOS):
        failures.append(f"scenarios must contain exactly {len(EXPECTED_SCENARIOS)} ordered cases")
        scenarios = []
    for index, expected in enumerate(EXPECTED_SCENARIOS):
        if index >= len(scenarios):
            break
        scenario = exact_object(
            scenarios[index],
            f"scenarios[{index}]",
            frozenset(
                {
                    "id",
                    "sessionState",
                    "lifecycleSource",
                    "compactionMode",
                    "requestCaseIds",
                    "expectedInjectionCount",
                    "expectationSource",
                    "hostObservations",
                }
            ),
            failures,
        )
        if scenario is None:
            continue
        (
            scenario_id,
            session_state,
            lifecycle_source,
            compaction_mode,
            request_case_ids,
            expected_injection_count,
        ) = expected
        expected_values = {
            "id": scenario_id,
            "sessionState": session_state,
            "lifecycleSource": lifecycle_source,
            "compactionMode": compaction_mode,
            "requestCaseIds": list(request_case_ids),
            "expectedInjectionCount": expected_injection_count,
            "expectationSource": "checked-in-hook-contract-not-host-observation",
        }
        for field, expected_value in expected_values.items():
            if scenario.get(field) != expected_value:
                failures.append(f"scenarios[{index}].{field} must be {expected_value!r}")
        for case_id in request_case_ids:
            if case_id not in corpus_cases:
                failures.append(f"scenarios[{index}] references unknown routing case {case_id!r}")
        is_no_route = scenario_id.endswith("no-route") or "no-route" in scenario_id
        for case_id in request_case_ids:
            case = corpus_cases.get(case_id)
            if case is None:
                continue
            expected_routes = case.get("expectedRoutes")
            if is_no_route and expected_routes != []:
                failures.append(f"scenarios[{index}] no-route request has routed corpus contract")
            if not is_no_route and not expected_routes:
                failures.append(f"scenarios[{index}] routed request has no-route corpus contract")

        observations = scenario.get("hostObservations")
        if type(observations) is not list or len(observations) != len(HOSTS):
            failures.append(f"scenarios[{index}].hostObservations must cover both hosts")
            continue
        for host_index, expected_host in enumerate(HOSTS):
            observation = observations[host_index]
            validate_host_observation(
                observation,
                label=f"scenarios[{index}].hostObservations[{host_index}]",
                lifecycle_source=lifecycle_source,
                request_count=len(request_case_ids),
                expected_injection_count=expected_injection_count,
                candidate_sha256=current_sha256,
                failures=failures,
            )
            if type(observation) is dict:
                if observation.get("host") != expected_host:
                    failures.append(
                        f"scenarios[{index}].hostObservations[{host_index}].host must be {expected_host!r}"
                    )
                if (
                    observation.get("status")
                    != CURRENT_LIFECYCLE_HOST_STATUSES[expected_host]
                ):
                    failures.append(
                        f"scenarios[{index}].hostObservations[{host_index}] must preserve the unobserved status"
                    )
    return len(scenarios)
