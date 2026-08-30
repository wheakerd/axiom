"""Canonical release-context facts and deterministic Markdown rendering."""

from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import Any

from .context import RELEASE_VERSION, REPOSITORY_ROOT
from .context_budget import load_json


SUPERSEDED_CANDIDATE_LABEL = "Superseded historical candidate"
SUPERSEDED_CANDIDATE_SIGNATURES = (
    "7,530 UTF-8 bytes",
    "974 whitespace-delimited words",
    "133 logical lines",
    "estimated 1,883 tokens",
    "+1,631 bytes",
    "+217 words",
    "+26 lines",
    "+408 estimated tokens",
)
SUPERSEDED_IDENTITY = re.compile(
    r"(?:full commit\s+`[0-9a-f]{40}`|"
    r"(?:content SHA-256|SHA-256)\s+`[0-9a-f]{64}`)"
)


def discover_fact_surface_versions(
    root: Path = REPOSITORY_ROOT,
    current_version: str = RELEASE_VERSION,
) -> dict[str, str]:
    """Discover current and already-managed historical documentation surfaces."""
    surfaces = {
        "README.md": current_version,
        f"docs/releases/v{current_version}.md": current_version,
    }
    release_root = root / "docs" / "releases"
    for path in sorted(release_root.glob("v*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if "<!-- release-facts:v" not in text:
            continue
        version = path.stem.removeprefix("v")
        surfaces[path.relative_to(root).as_posix()] = version
    return surfaces


FACTS_SURFACE_VERSIONS = discover_fact_surface_versions()
FACTS_SURFACES = tuple(FACTS_SURFACE_VERSIONS)


def facts_record_relative(version: str) -> str:
    return f"evals/context-budget/results/v{version}.json"


def facts_record_path(version: str) -> Path:
    return REPOSITORY_ROOT / facts_record_relative(version)


def facts_markers(relative_path: str) -> tuple[str, str]:
    marker = (
        "release-facts:current-context-budget"
        if relative_path == "README.md"
        else f"release-facts:v{FACTS_SURFACE_VERSIONS[relative_path]}-context-budget"
    )
    return f"<!-- {marker}:start -->", f"<!-- {marker}:end -->"


def _object(value: Any, label: str, failures: list[str]) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    return value


def _positive_integer(value: Any, label: str, failures: list[str]) -> int | None:
    if type(value) is not int or value < 0:
        failures.append(f"{label} must be a non-negative integer")
        return None
    return value


def _validate_metrics(
    value: Any,
    label: str,
    failures: list[str],
) -> dict[str, Any] | None:
    metrics = _object(value, label, failures)
    if metrics is None:
        return None
    initial_count = len(failures)
    expected_keys = {
        "classification",
        "utf8Bytes",
        "whitespaceDelimitedWords",
        "logicalLines",
        "directReferenceCount",
        "directReferences",
        "estimatedTokens",
    }
    missing = sorted(expected_keys - set(metrics))
    unknown = sorted(set(metrics) - expected_keys)
    if missing:
        failures.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{label} contains unknown fields: {', '.join(unknown)}")
    if metrics.get("classification") != "exact-static-counts-used-as-context-proxies":
        failures.append(f"{label}.classification must retain the context-proxy label")
    for field in (
        "utf8Bytes",
        "whitespaceDelimitedWords",
        "logicalLines",
        "directReferenceCount",
    ):
        _positive_integer(metrics.get(field), f"{label}.{field}", failures)
    references = metrics.get("directReferences")
    if type(references) is not list or not all(type(item) is str for item in references):
        failures.append(f"{label}.directReferences must be a string array")
    elif metrics.get("directReferenceCount") != len(references):
        failures.append(f"{label}.directReferenceCount must equal directReferences length")
    estimate = _object(metrics.get("estimatedTokens"), f"{label}.estimatedTokens", failures)
    if estimate is not None:
        expected_estimate_keys = {
            "classification",
            "method",
            "comparisonScope",
            "value",
        }
        missing_estimate = sorted(expected_estimate_keys - set(estimate))
        unknown_estimate = sorted(set(estimate) - expected_estimate_keys)
        if missing_estimate:
            failures.append(
                f"{label}.estimatedTokens is missing fields: {', '.join(missing_estimate)}"
            )
        if unknown_estimate:
            failures.append(
                f"{label}.estimatedTokens contains unknown fields: "
                + ", ".join(unknown_estimate)
            )
        if estimate.get("classification") != "estimate":
            failures.append(f"{label}.estimatedTokens must retain the estimate label")
        if estimate.get("method") != "ceil(utf8-bytes/4)":
            failures.append(f"{label}.estimatedTokens method drifted")
        if estimate.get("comparisonScope") != "same-English-Markdown-surface-only":
            failures.append(f"{label}.estimatedTokens comparison scope drifted")
        byte_count = metrics.get("utf8Bytes")
        estimated_value = estimate.get("value")
        if type(byte_count) is int and type(estimated_value) is int:
            if estimated_value != (byte_count + 3) // 4:
                failures.append(f"{label}.estimatedTokens.value is not ceil(utf8Bytes/4)")
        else:
            failures.append(f"{label}.estimatedTokens.value must be an integer")
    return metrics if len(failures) == initial_count else None


def validate_release_facts_record(
    document: dict[str, Any],
    version: str,
    failures: list[str],
) -> bool:
    """Validate the evidence labels and arithmetic used by rendered claims."""
    initial_count = len(failures)
    label = f"v{version} release-facts record"
    if document.get("schemaVersion") != "1":
        failures.append(f"{label} schemaVersion must be '1'")
    expected_record_id = f"routing-context-budget-v{version.replace('.', '-')}"
    if document.get("recordId") != expected_record_id:
        failures.append(f"{label} recordId drifted")
    target = _object(document.get("targetRelease"), "release facts targetRelease", failures)
    if target is not None and target.get("version") != version:
        failures.append(f"release facts targetRelease.version must be {version!r}")
    surface = _object(document.get("surface"), "release facts surface", failures)
    if surface is not None:
        if surface.get("path") != "skills/using-axiom/SKILL.md":
            failures.append("release facts surface path drifted")
        if surface.get("language") != "en" or surface.get("alwaysLoaded") is not True:
            failures.append("release facts surface must remain always-loaded English Markdown")

    boundary = _object(
        document.get("measurementBoundary"),
        "release facts measurementBoundary",
        failures,
    )
    if boundary is not None:
        expected = {
            "staticCounts": "proxy",
            "estimatedTokens": "estimate",
            "exactHostUsage": "not-run",
            "networkOrTelemetryUsed": False,
            "modelOrReasoningChanged": False,
            "volatilePricingIncluded": False,
        }
        for field, expected_value in expected.items():
            if boundary.get(field) != expected_value:
                failures.append(
                    f"release facts measurementBoundary.{field} must be {expected_value!r}"
                )

    baseline = _object(document.get("baseline"), "release facts baseline", failures)
    candidate = _object(document.get("candidate"), "release facts candidate", failures)
    baseline_metrics = None
    candidate_metrics = None
    if baseline is not None:
        release = _object(baseline.get("release"), "release facts baseline.release", failures)
        if release is not None and (
            release.get("version") != "0.7.9" or release.get("tag") != "v0.7.9"
        ):
            failures.append("release facts baseline must remain the immutable v0.7.9 release")
        baseline_metrics = _validate_metrics(
            baseline.get("metrics"), "release facts baseline.metrics", failures
        )
    if candidate is not None:
        candidate_metrics = _validate_metrics(
            candidate.get("metrics"), "release facts candidate.metrics", failures
        )

    comparison = _object(document.get("comparison"), "release facts comparison", failures)
    review_threshold = _object(
        document.get("reviewThreshold"),
        "release facts reviewThreshold",
        failures,
    )
    if baseline_metrics is not None and candidate_metrics is not None and comparison is not None:
        deltas = {
            "utf8ByteDelta": ("utf8Bytes",),
            "wordDelta": ("whitespaceDelimitedWords",),
            "lineDelta": ("logicalLines",),
            "referenceDelta": ("directReferenceCount",),
        }
        for comparison_field, (metric_field,) in deltas.items():
            expected_delta = candidate_metrics[metric_field] - baseline_metrics[metric_field]
            if comparison.get(comparison_field) != expected_delta:
                failures.append(
                    f"release facts comparison.{comparison_field} must equal the metric delta"
                )
        expected_estimate_delta = (
            candidate_metrics["estimatedTokens"]["value"]
            - baseline_metrics["estimatedTokens"]["value"]
        )
        if comparison.get("estimatedTokenDelta") != expected_estimate_delta:
            failures.append(
                "release facts comparison.estimatedTokenDelta must equal the estimate delta"
            )
        if review_threshold is not None:
            absolute_bytes = review_threshold.get("absoluteUtf8Bytes")
            relative_basis_points = review_threshold.get("relativeBasisPoints")
            byte_delta = candidate_metrics["utf8Bytes"] - baseline_metrics["utf8Bytes"]
            if type(absolute_bytes) is not int or absolute_bytes < 0:
                failures.append(
                    "release facts reviewThreshold.absoluteUtf8Bytes must be non-negative"
                )
            if type(relative_basis_points) is not int or relative_basis_points < 0:
                failures.append(
                    "release facts reviewThreshold.relativeBasisPoints must be non-negative"
                )
            if type(absolute_bytes) is int and type(relative_basis_points) is int:
                expected_absolute = byte_delta >= absolute_bytes
                expected_relative = (
                    byte_delta * 10_000
                    >= baseline_metrics["utf8Bytes"] * relative_basis_points
                )
                if comparison.get("absoluteThresholdReached") is not expected_absolute:
                    failures.append(
                        "release facts comparison.absoluteThresholdReached drifted"
                    )
                if comparison.get("relativeThresholdReached") is not expected_relative:
                    failures.append(
                        "release facts comparison.relativeThresholdReached drifted"
                    )
                meaningful = expected_absolute or expected_relative
                if comparison.get("meaningfulIncrease") is not meaningful:
                    failures.append("release facts comparison.meaningfulIncrease drifted")
                expected_status = "reviewed" if meaningful else "below-threshold"
                if comparison.get("reviewStatus") != expected_status:
                    failures.append(
                        "release facts comparison.reviewStatus must match threshold results"
                    )

    host_metrics = document.get("hostMetrics")
    if type(host_metrics) is not list:
        failures.append("release facts hostMetrics must be an array")
    else:
        by_host = {
            item.get("host"): item
            for item in host_metrics
            if type(item) is dict and type(item.get("host")) is str
        }
        expected_statuses = {"codex": "not-run", "claude-code": "unavailable"}
        if set(by_host) != set(expected_statuses):
            failures.append("release facts hostMetrics host set drifted")
        for host, status in expected_statuses.items():
            metric = by_host.get(host)
            if metric is None:
                continue
            if metric.get("status") != status:
                failures.append(f"release facts {host} status must remain {status!r}")
            if metric.get("exactUsageExposed") is not False:
                failures.append(f"release facts {host} exactUsageExposed must remain false")
            for field in (
                "inputTokens",
                "cachedInputTokens",
                "credits",
                "wallClockMilliseconds",
            ):
                if metric.get(field) is not None:
                    failures.append(f"release facts {host}.{field} must remain null")

    scenarios = document.get("scenarios")
    if type(scenarios) is not list:
        failures.append("release facts scenarios must be an array")
    else:
        for scenario_index, scenario in enumerate(scenarios):
            observations = scenario.get("hostObservations") if type(scenario) is dict else None
            if type(observations) is not list:
                failures.append(
                    f"release facts scenarios[{scenario_index}].hostObservations must be an array"
                )
                continue
            for observation_index, observation in enumerate(observations):
                if type(observation) is not dict:
                    failures.append(
                        f"release facts scenarios[{scenario_index}].hostObservations"
                        f"[{observation_index}] must be an object"
                    )
                    continue
                if observation.get("observedInjectionCount") is not None:
                    failures.append(f"v{version} release facts must not infer lifecycle observations")
                if observation.get("injections") != []:
                    failures.append(f"v{version} release facts must not claim injection events")
    return len(failures) == initial_count


def load_release_facts(version: str, failures: list[str]) -> dict[str, Any] | None:
    document = load_json(facts_record_path(version), failures)
    if document is None:
        return None
    return document if validate_release_facts_record(document, version, failures) else None


def _count(value: int) -> str:
    return f"{value:,}"


def _delta(value: int) -> str:
    return f"{value:+,}" if value else "0"


def _quantity(value: int, noun: str, *, delta: bool = False) -> str:
    rendered = _delta(value) if delta else _count(value)
    suffix = "" if abs(value) == 1 else "s"
    return f"{rendered} {noun}{suffix}"


def render_release_facts(relative_path: str, document: dict[str, Any]) -> str:
    """Render exact static facts while preserving proxy and observation labels."""
    version = document["targetRelease"]["version"]
    record_relative = facts_record_relative(version)
    link = record_relative if relative_path == "README.md" else f"../../{record_relative}"
    baseline = document["baseline"]["metrics"]
    candidate = document["candidate"]["metrics"]
    comparison = document["comparison"]
    absolute_status = (
        "reached" if comparison["absoluteThresholdReached"] else "not reached"
    )
    relative_status = (
        "reached" if comparison["relativeThresholdReached"] else "not reached"
    )
    review_status = comparison["reviewStatus"]
    return (
        f"The [v{version} routing-context record]({link}) uses the immutable "
        "v0.7.9 `using-axiom` gate as its cumulative baseline. The baseline has "
        f"{_count(baseline['utf8Bytes'])} UTF-8 bytes, "
        f"{_count(baseline['whitespaceDelimitedWords'])} whitespace-delimited words, "
        f"{_count(baseline['logicalLines'])} logical lines, "
        f"{_quantity(baseline['directReferenceCount'], 'direct reference')}, and an estimated "
        f"{_count(baseline['estimatedTokens']['value'])} tokens. The candidate has "
        f"{_count(candidate['utf8Bytes'])} UTF-8 bytes, "
        f"{_count(candidate['whitespaceDelimitedWords'])} whitespace-delimited words, "
        f"{_count(candidate['logicalLines'])} logical lines, "
        f"{_quantity(candidate['directReferenceCount'], 'direct reference')}, and an estimated "
        f"{_count(candidate['estimatedTokens']['value'])} tokens. Its cumulative deltas "
        f"are {_delta(comparison['utf8ByteDelta'])} bytes, "
        f"{_delta(comparison['wordDelta'])} words, "
        f"{_delta(comparison['lineDelta'])} lines, "
        f"{_quantity(comparison['referenceDelta'], 'reference', delta=True)}, and "
        f"{_delta(comparison['estimatedTokenDelta'])} estimated tokens. "
        f"The record marks the absolute threshold `{absolute_status}`, the relative "
        f"threshold `{relative_status}`, and review status `{review_status}`. "
        "The exact static counts are context proxies, and each `ceil(UTF-8 bytes / 4)` "
        "figure is only an estimate for the same English Markdown surface, not an "
        "exact token or credit count. Codex host and lifecycle observation remains "
        "`NOT-RUN`; authenticated Claude Code remains `UNAVAILABLE / NOT-RUN`. No host "
        "observation is inferred from these static values."
    )


def rendered_release_block(relative_path: str, document: dict[str, Any]) -> str:
    start_marker, end_marker = facts_markers(relative_path)
    rendered = render_release_facts(relative_path, document)
    body = (
        textwrap.fill(
            rendered,
            width=88,
            break_long_words=False,
            break_on_hyphens=False,
        )
        if relative_path == "README.md"
        else rendered
    )
    return (
        f"{start_marker}\n"
        f"{body}\n"
        f"{end_marker}"
    )


def replace_release_block(
    relative_path: str,
    text: str,
    document: dict[str, Any],
) -> str:
    """Return text with its one release-facts marker region rendered."""
    start_marker, end_marker = facts_markers(relative_path)
    if text.count(start_marker) == 0 and text.count(end_marker) == 0:
        current_notes = f"docs/releases/v{RELEASE_VERSION}.md"
        if relative_path == current_notes:
            return (
                text.rstrip()
                + "\n\n## Routing Context Facts\n\n"
                + rendered_release_block(relative_path, document)
                + "\n"
            )
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError("release-facts document must contain one start and one end marker")
    start = text.index(start_marker)
    end = text.index(end_marker, start) + len(end_marker)
    return text[:start] + rendered_release_block(relative_path, document) + text[end:]


def check_release_surface_text(
    relative_path: str,
    text: str,
    document: dict[str, Any],
    failures: list[str],
) -> None:
    expected = rendered_release_block(relative_path, document)
    start_marker, end_marker = facts_markers(relative_path)
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        failures.append(f"{relative_path} must contain exactly one managed release-facts block")
    elif expected not in text:
        version = FACTS_SURFACE_VERSIONS[relative_path]
        failures.append(
            f"{relative_path} release facts drifted from {facts_record_relative(version)}; run "
            "python3 scripts/render-release-facts.py --render"
        )

    signatures = (
        [signature for signature in SUPERSEDED_CANDIDATE_SIGNATURES if signature in text]
        if relative_path == "docs/releases/v0.8.4.md"
        else []
    )
    unlabeled: list[str] = []
    unbound: list[str] = []
    for signature in signatures:
        index = text.index(signature)
        paragraph_start = text.rfind("\n\n", 0, index)
        paragraph_start = 0 if paragraph_start < 0 else paragraph_start + 2
        paragraph_end = text.find("\n\n", index)
        paragraph_end = len(text) if paragraph_end < 0 else paragraph_end
        paragraph = text[paragraph_start:paragraph_end]
        if SUPERSEDED_CANDIDATE_LABEL not in paragraph:
            unlabeled.append(signature)
        elif SUPERSEDED_IDENTITY.search(paragraph) is None:
            unbound.append(signature)
    if unlabeled:
        failures.append(
            f"{relative_path} contains unlabeled superseded v0.8.4 candidate facts: "
            + ", ".join(unlabeled)
        )
    if unbound:
        failures.append(
            f"{relative_path} superseded v0.8.4 candidate facts lack an immutable "
            "full commit or content SHA-256 identity: "
            + ", ".join(unbound)
        )


def check_release_facts(failures: list[str]) -> int:
    """Validate the canonical record and every deterministic documentation surface."""
    documents: dict[str, dict[str, Any]] = {}
    for version in sorted(set(FACTS_SURFACE_VERSIONS.values())):
        document = load_release_facts(version, failures)
        if document is not None:
            documents[version] = document
    for relative_path in FACTS_SURFACES:
        version = FACTS_SURFACE_VERSIONS[relative_path]
        document = documents.get(version)
        if document is None:
            continue
        path = REPOSITORY_ROOT / relative_path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {relative_path}: {error}")
            continue
        check_release_surface_text(relative_path, text, document, failures)
    return sum(
        version in documents for version in FACTS_SURFACE_VERSIONS.values()
    )


__all__ = (
    "FACTS_SURFACES",
    "FACTS_SURFACE_VERSIONS",
    "SUPERSEDED_CANDIDATE_LABEL",
    "SUPERSEDED_IDENTITY",
    "SUPERSEDED_CANDIDATE_SIGNATURES",
    "check_release_facts",
    "check_release_surface_text",
    "discover_fact_surface_versions",
    "facts_markers",
    "facts_record_path",
    "facts_record_relative",
    "load_release_facts",
    "render_release_facts",
    "rendered_release_block",
    "replace_release_block",
    "validate_release_facts_record",
)
