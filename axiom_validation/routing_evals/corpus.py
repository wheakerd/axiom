"""Routing corpus loading and coverage policy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import CASE_FILES, PUBLIC_ROUTES
from .jsonio import _display, load_jsonl_cases
from .schemas import validate_case


CREDENTIAL_LIFECYCLE_TYPE_TOKENS = (
    "api-key",
    "ssh-key",
    "certificate",
    "signing-key",
    "service-account",
)
CREDENTIAL_LIFECYCLE_REQUIRED_CASES = frozenset(
    {
        "credential-lifecycle-provider-unknown-001",
        "credential-lifecycle-secret-disclosure-001",
        "credential-lifecycle-untrusted-config-001",
        "credential-lifecycle-service-account-es-001",
        "credential-lifecycle-compaction-unknown-001",
        "credential-lifecycle-resume-partial-001",
        "credential-lifecycle-cleanup-recovery-001",
    }
)


def collect_corpus(
    root: Path,
    failures: list[str],
) -> dict[str, dict[str, Any]]:
    eval_root = root / "evals"
    routing_root = eval_root / "routing"
    actual_files = tuple(path.name for path in sorted(routing_root.glob("*.jsonl")))
    if actual_files != tuple(sorted(CASE_FILES)):
        failures.append(
            "evals/routing JSONL file set drifted: " + ", ".join(actual_files)
        )
    cases: dict[str, dict[str, Any]] = {}
    for file_name in CASE_FILES:
        path = routing_root / file_name
        for line_number, case in enumerate(load_jsonl_cases(path, failures, root), 1):
            label = f"{_display(path, root)}:{line_number}"
            document = validate_case(case, label, failures)
            if document is None or type(document.get("id")) is not str:
                continue
            case_id = document["id"]
            if case_id in cases:
                failures.append(f"{label}.id duplicates corpus case {case_id!r}")
            cases[case_id] = document
    return cases


def check_corpus_coverage(
    cases: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    values = tuple(cases.values())
    for route in PUBLIC_ROUTES:
        canonical = [
            case
            for case in values
            if route in case.get("expectedRoutes", ())
            and case.get("riskClass") == "canonical-positive"
        ]
        paraphrased = [
            case
            for case in values
            if route in case.get("expectedRoutes", ())
            and case.get("riskClass") == "paraphrased-positive"
        ]
        near_misses = [
            case
            for case in values
            if route in case.get("forbiddenRoutes", ())
            and "near-miss" in case.get("coverage", ())
        ]
        cross_route = [
            case
            for case in values
            if "cross-route" in case.get("coverage", ())
            and route
            in set(case.get("expectedRoutes", ()))
            | set(case.get("forbiddenRoutes", ()))
        ]
        multilingual = [
            case
            for case in values
            if route in case.get("expectedRoutes", ())
            and "multilingual" in case.get("coverage", ())
        ]
        post_compaction = [
            case
            for case in values
            if route in case.get("expectedRoutes", ())
            and "post-compaction" in case.get("coverage", ())
        ]
        for label, matches in (
            ("canonical positive", canonical),
            ("paraphrased positive", paraphrased),
            ("near-miss", near_misses),
            ("cross-route ownership", cross_route),
            ("multilingual", multilingual),
            ("post-compaction", post_compaction),
        ):
            if not matches:
                failures.append(f"routing corpus has no {label} case for {route}")
    required_labels = {
        "plan-only",
        "draft-only",
        "no-route",
        "ambiguity",
        "multilingual",
        "post-compaction",
        "untrusted-data",
    }
    present = {label for case in values for label in case.get("coverage", ())}
    for label in sorted(required_labels - present):
        failures.append(f"routing corpus is missing required coverage {label!r}")
    if not any(
        "post-compaction" in case.get("coverage", ())
        and not case.get("expectedRoutes")
        for case in values
    ):
        failures.append("routing corpus has no post-compaction no-route control")

    credential_cases = {
        case_id: case
        for case_id, case in cases.items()
        if case_id.startswith("credential-lifecycle-")
    }
    missing_cases = sorted(CREDENTIAL_LIFECYCLE_REQUIRED_CASES - set(credential_cases))
    if missing_cases:
        failures.append(
            "credential-lifecycle corpus is missing required cases: "
            + ", ".join(missing_cases)
        )
    for case_id, case in credential_cases.items():
        if case.get("schemaVersion") != "2" or case.get("contractVersion") != 2:
            failures.append(f"credential-lifecycle case {case_id!r} must use contract v2")
        if case.get("benchmarkSets"):
            failures.append(
                f"credential-lifecycle case {case_id!r} must remain outside frozen benchmarks"
            )
    for token in CREDENTIAL_LIFECYCLE_TYPE_TOKENS:
        typed = [
            case
            for case_id, case in credential_cases.items()
            if f"credential-lifecycle-{token}-" in case_id
        ]
        routed = [case for case in typed if case.get("expectedRoutes")]
        near_miss = [
            case
            for case in typed
            if not case.get("expectedRoutes")
            and "near-miss" in case.get("coverage", ())
        ]
        if not routed:
            failures.append(
                f"credential-lifecycle corpus has no routed positive for {token}"
            )
        if not near_miss:
            failures.append(
                f"credential-lifecycle corpus has no no-route near-miss for {token}"
            )
