"""Negative fixtures for the routing-evaluation policy."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.routing_evals import (
    CANDIDATE4_CODEX_RUN_ID,
    CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
    HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
    derive_observer_evidence,
)


def load_case(case_id: str) -> dict[str, Any]:
    for path in sorted((REPOSITORY_ROOT / "evals" / "routing").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            case = json.loads(line)
            if case["id"] == case_id:
                return case
    raise AssertionError(f"missing fixture source case {case_id!r}")


def case_negative_fixtures() -> tuple[tuple[str, dict[str, Any]], ...]:
    source = load_case("confirm-external-action-draft-only-001")
    fixtures: list[tuple[str, dict[str, Any]]] = []

    mutation_authorized = copy.deepcopy(source)
    mutation_authorized["mutationAuthorized"] = True
    fixtures.append(("mutation authority", mutation_authorized))

    overlapping_route = copy.deepcopy(source)
    overlapping_route["expectedRoutes"] = ["confirm-external-action"]
    fixtures.append(("expected and forbidden overlap", overlapping_route))

    unknown_route = copy.deepcopy(source)
    unknown_route["forbiddenRoutes"] = ["imaginary-route"]
    fixtures.append(("unknown route", unknown_route))

    clarification_mismatch = copy.deepcopy(source)
    clarification_mismatch["expectedClarification"] = True
    fixtures.append(("clarification count mismatch", clarification_mismatch))

    lifecycle_mismatch = copy.deepcopy(source)
    lifecycle_mismatch["lifecycle"] = {
        "state": "post-compaction",
        "source": "startup",
        "compactionMode": "not-applicable",
    }
    fixtures.append(("lifecycle mismatch", lifecycle_mismatch))

    hidden_contract_change = copy.deepcopy(source)
    hidden_contract_change["contractVersion"] = 0
    fixtures.append(("invalid contract version", hidden_contract_change))

    return tuple(fixtures)


def load_observation(host: str) -> dict[str, Any]:
    recovery_files = {
        "codex-recovery-1": "linux-recovery-1.json",
        "codex-recovery-2": "linux-recovery-2.json",
    }
    directory = "codex" if host in recovery_files else host
    file_name = recovery_files.get(host, "linux.json")
    path = (
        REPOSITORY_ROOT
        / "evals"
        / "results"
        / "v0.7.7"
        / directory
        / file_name
    )
    return json.loads(path.read_text(encoding="utf-8"))


def valid_host_response() -> dict[str, Any]:
    return {
        "routingGateObserved": True,
        "selectedRoutes": ["agents-architect"],
        "clarificationCount": 0,
        "mutationAttempted": False,
        "mutationObserved": False,
        "evidence": ["Selected agents-architect for the AGENTS.md audit."],
    }


def valid_host_response_v2() -> dict[str, Any]:
    return {
        "routingGateObserved": True,
        "selectedRoutes": ["agents-architect"],
        "clarificationCount": 0,
        "mutationAttempted": False,
        "mutationObserved": False,
    }


def host_response_negative_fixtures() -> tuple[tuple[str, dict[str, Any]], ...]:
    source = valid_host_response()
    fixtures: list[tuple[str, dict[str, Any]]] = []

    unknown_field = copy.deepcopy(source)
    unknown_field["extra"] = False
    fixtures.append(("unknown field", unknown_field))

    duplicate_route = copy.deepcopy(source)
    duplicate_route["selectedRoutes"] = ["agents-architect", "agents-architect"]
    fixtures.append(("duplicate route", duplicate_route))

    excess_routes = copy.deepcopy(source)
    excess_routes["selectedRoutes"] = [
        "agents-architect",
        "review-axiom-task",
        "optimize-codex-usage",
    ]
    fixtures.append(("excess routes", excess_routes))

    excess_clarification = copy.deepcopy(source)
    excess_clarification["clarificationCount"] = 2
    fixtures.append(("excess clarification", excess_clarification))

    empty_evidence = copy.deepcopy(source)
    empty_evidence["evidence"] = []
    fixtures.append(("empty evidence", empty_evidence))

    duplicate_evidence = copy.deepcopy(source)
    duplicate_evidence["evidence"] = ["Same evidence.", "Same evidence."]
    fixtures.append(("duplicate evidence", duplicate_evidence))

    excess_evidence = copy.deepcopy(source)
    excess_evidence["evidence"] = ["One.", "Two.", "Three.", "Four."]
    fixtures.append(("excess evidence", excess_evidence))

    long_evidence = copy.deepcopy(source)
    long_evidence["evidence"] = ["x" * 241]
    fixtures.append(("long evidence", long_evidence))

    return tuple(fixtures)


def host_response_acceptance_fixtures(
) -> tuple[tuple[str, str, dict[str, Any]], ...]:
    """Return constraints intentionally omitted from the model-facing schema."""
    source = valid_host_response()
    fixtures: list[tuple[str, str, dict[str, Any]]] = []

    duplicate_route = copy.deepcopy(source)
    duplicate_route["selectedRoutes"] = ["agents-architect", "agents-architect"]
    fixtures.append(
        ("duplicate route", "selected-routes-duplicate", duplicate_route)
    )

    empty_string = copy.deepcopy(source)
    empty_string["evidence"] = [""]
    fixtures.append(("empty evidence string", "evidence-empty-string", empty_string))

    long_evidence = copy.deepcopy(source)
    long_evidence["evidence"] = ["x" * 241]
    fixtures.append(("long evidence", "evidence-overlength", long_evidence))

    duplicate_evidence = copy.deepcopy(source)
    duplicate_evidence["evidence"] = ["Same evidence.", "Same evidence."]
    fixtures.append(("duplicate evidence", "evidence-duplicate", duplicate_evidence))

    for name, value in (
        ("private home path", "/home/example/private.txt"),
        ("private users path", "/Users/example/private.txt"),
        ("private tmp path", "/tmp/example-private.txt"),
        ("mixed-case Windows path", r"c:\uSeRs\Example\private.txt"),
        ("sk token", "sk-abcdefgh"),
        ("ghp token", "ghp_abcdefgh"),
        ("github token", "github_pat_abcdefgh"),
        ("hyphenated thread id", "THREAD-ID"),
    ):
        private = copy.deepcopy(source)
        private["evidence"] = [value]
        fixtures.append((name, "privacy", private))

    safe_near_miss = copy.deepcopy(source)
    safe_near_miss["evidence"] = ["risk-sensitive"]
    fixtures.append(("safe token near miss", "valid", safe_near_miss))
    return tuple(fixtures)


def host_response_schema_negative_fixtures() -> tuple[tuple[str, dict[str, Any]], ...]:
    path = REPOSITORY_ROOT / "evals" / "host-response-schema-v1.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    fixtures: list[tuple[str, dict[str, Any]]] = []

    for keyword, value in (
        ("$schema", "https://json-schema.org/draft/2020-12/schema"),
        ("$id", "urn:axiom:routing-evals:host-response:v1"),
        ("title", "Axiom bounded host routing response"),
    ):
        document = copy.deepcopy(source)
        document[keyword] = value
        fixtures.append((f"root keyword {keyword}", document))

    unique_items = copy.deepcopy(source)
    unique_items["properties"]["selectedRoutes"]["uniqueItems"] = True
    fixtures.append(("uniqueItems", unique_items))

    maximum_length = copy.deepcopy(source)
    maximum_length["properties"]["evidence"]["items"]["maxLength"] = 240
    fixtures.append(("maxLength", maximum_length))

    minimum_length = copy.deepcopy(source)
    minimum_length["properties"]["evidence"]["items"]["minLength"] = 1
    fixtures.append(("minLength", minimum_length))

    return tuple(fixtures)


def host_response_schema_v2_negative_fixtures(
) -> tuple[tuple[str, dict[str, Any]], ...]:
    path = REPOSITORY_ROOT / "evals" / "host-response-schema-v2.json"
    source = json.loads(path.read_text(encoding="utf-8"))
    fixtures: list[tuple[str, dict[str, Any]]] = []

    for keyword, value in (
        ("$schema", "https://json-schema.org/draft/2020-12/schema"),
        ("$id", "urn:axiom:routing-evals:host-response:v2"),
        ("title", "Axiom semantic routing response"),
    ):
        document = copy.deepcopy(source)
        document[keyword] = value
        fixtures.append((f"root keyword {keyword}", document))

    unique_items = copy.deepcopy(source)
    unique_items["properties"]["selectedRoutes"]["uniqueItems"] = True
    fixtures.append(("uniqueItems", unique_items))

    model_evidence = copy.deepcopy(source)
    model_evidence["required"].append("evidence")
    model_evidence["properties"]["evidence"] = {
        "type": "array",
        "items": {"type": "string"},
    }
    fixtures.append(("model-authored evidence", model_evidence))

    return tuple(fixtures)


def prospective_candidate_four_observation() -> dict[str, Any]:
    """Return a valid terminal Candidate-4-shaped unknown for focused tests."""
    record = partial_unknown_observation()
    record["runId"] = CANDIDATE4_CODEX_RUN_ID
    record["responseSchema"] = {
        "path": HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
        "sha256": CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
    }
    record["axiom"] = {
        "version": "0.7.8",
        "tag": None,
        "commit": "1" * 40,
        "tree": "2" * 40,
        "releaseState": "candidate-unreleased",
    }
    record["run"]["callCount"] = 1
    for index, result_case in enumerate(record["cases"]):
        if index == 0:
            result_case["responseDiagnostic"] = "missing-or-unreadable"
            result_case["acceptanceDiagnostic"] = "not-evaluated"
            result_case["evidenceSource"] = "observer-derived"
            result_case["evidence"] = derive_observer_evidence(
                routing_gate_observed=result_case["routingGateObserved"],
                selected_routes=result_case["observedRoutes"],
                clarification_count=result_case["clarificationCount"],
                mutation_attempted=result_case["mutationAttempted"],
                mutation_observed=result_case["mutationObserved"],
                turn_completed=False,
                failure_event=None,
                unexpected_tools=0,
                workspace_unchanged=True,
                source_unchanged=True,
                installed_unchanged=True,
            )
        else:
            result_case["responseDiagnostic"] = "not-observed"
            result_case["acceptanceDiagnostic"] = "not-observed"
            result_case["evidenceSource"] = "not-observed"
    return record


def partial_unknown_observation() -> dict[str, Any]:
    """Return a valid batch that stopped after an unknown first-case failure."""
    record = load_observation("codex")
    record["host"]["model"] = "gpt-5.4"
    record["run"].update(
        {
            "status": "unknown",
            "recordedAt": "2026-08-21T12:00:00Z",
            "repeatCount": 1,
            "reasoningEffort": "medium",
            "caseTimeoutSeconds": 120,
            "installedPluginVerified": True,
            "startupHookVerified": True,
            "limitations": [
                "The first case timed out; the remaining batch stopped without retry."
            ],
        }
    )
    first = record["cases"][0]
    first.update(
        {
            "status": "unknown",
            "routingGateObserved": None,
            "observedRoutes": None,
            "clarificationCount": None,
            "mutationAttempted": None,
            "mutationObserved": False,
            "evidence": [],
            "limitations": ["Timed out after 120 seconds; route outcome is unknown."],
        }
    )
    for result_case in record["cases"][1:]:
        result_case["limitations"] = [
            "Not run because the fixed batch stopped at the first failure."
        ]
    record["summary"].update(
        {
            "overallStatus": "unknown",
            "evaluatedCases": 1,
            "canonicalFalseNegatives": None,
            "highImpactFalsePositives": None,
            "clarificationMismatches": None,
            "mutationAttempts": None,
        }
    )
    return record


def terminal_recovery_observation() -> dict[str, Any]:
    """Return an independent recovery run with a pass prefix and first failure."""
    record = load_observation("codex")
    record["runId"] = "codex-v0-7-7-linux-codex-core-v1-recovery-2"
    record["responseSchema"]["sha256"] = (
        "377ac22919164033b3dcf55f2b6b96086a5e2731c9b1edacabd5797a0b9127b6"
    )
    record["run"].update(
        {
            "recordedAt": "2026-08-21T21:00:00Z",
            "limitations": [
                "The independent recovery run stopped at its first failure."
            ],
        }
    )
    record["cases"][0].update(
        {
            "status": "pass",
            "routingGateObserved": True,
            "observedRoutes": ["agents-architect"],
            "clarificationCount": 0,
            "mutationAttempted": False,
            "mutationObserved": False,
            "evidence": ["Selected agents-architect for the AGENTS.md audit."],
            "limitations": [],
        }
    )
    record["cases"][1].update(
        {
            "status": "fail",
            "limitations": [
                "The second case failed without a bounded routing response."
            ],
        }
    )
    for result_case in record["cases"][2:]:
        result_case["limitations"] = [
            "Not run because the independent recovery batch stopped at its first failure."
        ]
    record["summary"].update(
        {
            "evaluatedCases": 2,
            "canonicalFalseNegatives": None,
            "highImpactFalsePositives": None,
            "clarificationMismatches": None,
            "mutationAttempts": None,
        }
    )
    return record


def observation_negative_fixtures() -> tuple[tuple[str, dict[str, Any]], ...]:
    source = load_observation("codex")
    fixtures: list[tuple[str, dict[str, Any]]] = []

    route_on_not_run = copy.deepcopy(source)
    route_on_not_run["cases"][1]["observedRoutes"] = ["optimize-codex-usage"]
    fixtures.append(("not-run route claim", route_on_not_run))

    mutation_on_not_run = copy.deepcopy(source)
    mutation_on_not_run["cases"][1]["mutationAttempted"] = True
    fixtures.append(("not-run mutation claim", mutation_on_not_run))

    repeated_case = copy.deepcopy(source)
    repeated_case["cases"][1]["id"] = repeated_case["cases"][0]["id"]
    fixtures.append(("benchmark order drift", repeated_case))

    false_summary = copy.deepcopy(source)
    false_summary["summary"]["canonicalFalseNegatives"] = 0
    fixtures.append(("unexecuted metric claim", false_summary))

    private_path = copy.deepcopy(source)
    private_path["run"]["limitations"][0] = "/home/example/private-result"
    fixtures.append(("private path", private_path))

    missing_response_schema = copy.deepcopy(source)
    missing_response_schema["responseSchema"] = None
    fixtures.append(("attempt without response schema", missing_response_schema))

    wrong_response_schema_path = copy.deepcopy(source)
    wrong_response_schema_path["responseSchema"]["path"] = "evals/other-schema.json"
    fixtures.append(("wrong response schema path", wrong_response_schema_path))

    malformed_response_schema_digest = copy.deepcopy(source)
    malformed_response_schema_digest["responseSchema"]["sha256"] = "not-a-digest"
    fixtures.append(("malformed response schema digest", malformed_response_schema_digest))

    attempted_after_stop = partial_unknown_observation()
    attempted_after_stop["cases"][1].update(
        {
            "status": "pass",
            "routingGateObserved": True,
            "observedRoutes": ["optimize-codex-usage"],
            "clarificationCount": 0,
            "mutationAttempted": False,
            "mutationObserved": False,
            "evidence": ["Selected optimize-codex-usage."],
            "limitations": [],
        }
    )
    fixtures.append(("attempt after first failure", attempted_after_stop))

    unattempted_claim = partial_unknown_observation()
    unattempted_claim["cases"][1]["observedRoutes"] = []
    fixtures.append(("unattempted observation claim", unattempted_claim))

    unknown_as_zero = partial_unknown_observation()
    unknown_as_zero["summary"]["canonicalFalseNegatives"] = 0
    fixtures.append(("unknown summary rewritten as zero", unknown_as_zero))

    return tuple(fixtures)


def corpus_cases() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((REPOSITORY_ROOT / "evals" / "routing").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            case = json.loads(line)
            result[case["id"]] = case
    return result


def benchmark_case_ids() -> list[str]:
    path = REPOSITORY_ROOT / "evals" / "benchmarks" / "codex-core-v1.json"
    return json.loads(path.read_text(encoding="utf-8"))["caseIds"]
