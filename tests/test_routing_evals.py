"""Focused tests for the black-box routing evaluation contracts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from axiom_validation.routing_evals import (
    ACCEPTANCE_DIAGNOSTICS,
    CANDIDATE2_CODEX_RUN_ID,
    CANDIDATE2_RESULT_PATH,
    CANDIDATE2_V078_SUBJECT,
    CANDIDATE3_CODEX_RUN_ID,
    CANDIDATE3_RESULT_PATH,
    CANDIDATE3_V078_SUBJECT,
    CANDIDATE4_CODEX_RUN_ID,
    CANDIDATE4_RESULT_PATH,
    CANDIDATE4_V078_SUBJECT,
    CANDIDATE_CODEX_RUN_ID,
    CANDIDATE_RESULT_PATH,
    CANDIDATE_V078_SUBJECT,
    CLAUDE_UNAVAILABLE_RUN_ID,
    CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
    CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    FAILED_HOST_RESPONSE_SCHEMA_SHA256,
    EXPECTED_RESULT_BINDINGS,
    EXPECTED_RESULT_SUBJECTS,
    INITIAL_CODEX_OUTCOME_SHA256,
    INITIAL_CODEX_RUN_ID,
    HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    OPTIONAL_RESULT_PATHS,
    PRESERVED_OUTCOME_SHA256,
    RECOVERY2_CODEX_RUN_ID,
    RECOVERY2_RESULT_PATH,
    RECOVERY3_CODEX_RUN_ID,
    RECOVERY3_RESULT_PATH,
    RECOVERY_RESULT_PATH,
    RECOVERY_CODEX_RUN_ID,
    RELEASED_V080_SUBJECT,
    RESPONSE_DIAGNOSTICS,
    V080_CLAUDE_RESULT_PATH,
    V080_CLAUDE_UNAVAILABLE_RUN_ID,
    V080_CODEX_RESULT_PATH,
    V080_CODEX_RUN_ID,
    V1_HOST_RESPONSE_SCHEMA_SHA256,
    classify_host_response_acceptance,
    classify_host_response_v2_acceptance,
    classify_host_response_v3_acceptance,
    check_host_response_schema,
    check_host_response_schema_v2,
    check_host_response_schema_v3,
    check_routing_evaluations,
    derive_observer_evidence,
    load_jsonl_cases,
    validate_acceptance_diagnostic,
    validate_case,
    validate_host_response,
    validate_host_response_structure,
    validate_host_response_v2,
    validate_host_response_v2_structure,
    validate_host_response_v3,
    validate_host_response_v3_structure,
    validate_observer_derived_evidence,
    validate_observation,
    validate_observation_run_set,
    validate_external_routing_observation,
    validate_response_diagnostic,
)
from tests.fixtures.routing_evals import (
    benchmark_case_ids,
    case_negative_fixtures,
    corpus_cases,
    host_response_acceptance_fixtures,
    host_response_negative_fixtures,
    host_response_schema_negative_fixtures,
    host_response_schema_v2_negative_fixtures,
    load_observation,
    observation_negative_fixtures,
    partial_unknown_observation,
    prospective_candidate_four_observation,
    terminal_recovery_observation,
    valid_host_response,
    valid_host_response_v2,
)


def response_schema_digests() -> dict[str, str]:
    return {
        HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH: V1_HOST_RESPONSE_SCHEMA_SHA256,
        HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH: CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
        HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH: CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    }


def load_recovery_three() -> dict:
    path = (
        Path(__file__).resolve().parents[1]
        / "evals"
        / RECOVERY3_RESULT_PATH
    )
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_one() -> dict:
    path = Path(__file__).resolve().parents[1] / "evals" / CANDIDATE_RESULT_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_two() -> dict:
    path = Path(__file__).resolve().parents[1] / "evals" / CANDIDATE2_RESULT_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_three() -> dict:
    path = Path(__file__).resolve().parents[1] / "evals" / CANDIDATE3_RESULT_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_four() -> dict:
    path = Path(__file__).resolve().parents[1] / "evals" / CANDIDATE4_RESULT_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def load_v080_result(host: str) -> dict:
    relative_path = (
        V080_CODEX_RESULT_PATH if host == "codex" else V080_CLAUDE_RESULT_PATH
    )
    path = Path(__file__).resolve().parents[1] / "evals" / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def load_result(relative_path: str) -> dict:
    path = Path(__file__).resolve().parents[1] / "evals" / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def benchmark_v2_case_ids() -> list[str]:
    path = (
        Path(__file__).resolve().parents[1]
        / "evals"
        / "benchmarks"
        / "codex-core-v2.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))["caseIds"]


def external_v083_observation() -> dict:
    cases = corpus_cases()
    result_cases = []
    for case_id in benchmark_v2_case_ids():
        case = cases[case_id]
        routes = case["expectedRoutes"]
        clarifications = case["expectedClarificationCount"]
        result_cases.append(
            {
                "id": case_id,
                "status": "pass",
                "responseDiagnostic": "valid",
                "acceptanceDiagnostic": "valid",
                "evidenceSource": "observer-derived",
                "routingGateObserved": True,
                "observedRoutes": routes,
                "clarificationCount": clarifications,
                "mutationAttempted": False,
                "mutationObserved": False,
                "evidence": derive_observer_evidence(
                    routing_gate_observed=True,
                    selected_routes=routes,
                    clarification_count=clarifications,
                    mutation_attempted=False,
                    mutation_observed=False,
                    turn_completed=True,
                    failure_event=False,
                    unexpected_tools=0,
                    workspace_unchanged=True,
                    source_unchanged=True,
                    installed_unchanged=True,
                ),
                "limitations": [],
            }
        )
    return {
        "schemaVersion": "2",
        "kind": "routing-observation",
        "benchmarkId": "codex-core-v2",
        "runId": "codex-v0-8-3-linux-codex-core-v2-post-tag-1",
        "responseSchema": {
            "path": HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
            "sha256": CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
        },
        "axiom": {
            "version": "0.8.3",
            "tag": "v0.8.3",
            "commit": "b" * 40,
            "tree": "c" * 40,
        },
        "host": {"name": "codex", "version": "0.149.1", "model": "gpt-5.4"},
        "environment": {
            "operatingSystem": "fedora-linux-44",
            "architecture": "x86_64",
        },
        "run": {
            "status": "pass",
            "recordedAt": "2026-08-24T00:00:00Z",
            "lifecycle": "fresh-start",
            "repeatCount": 1,
            "callCount": 17,
            "reasoningEffort": "medium",
            "caseTimeoutSeconds": 120,
            "installedPluginVerified": True,
            "startupHookVerified": True,
            "method": "documented-codex-cli-equivalent",
            "limitations": [],
        },
        "cases": result_cases,
        "summary": {
            "overallStatus": "pass",
            "evaluatedCases": 17,
            "canonicalFalseNegatives": 0,
            "highImpactFalsePositives": 0,
            "clarificationMismatches": 0,
            "mutationAttempts": 0,
        },
    }


def write_content_addressed_observation(directory: Path, record: dict) -> Path:
    payload = (json.dumps(record, indent=2) + "\n").encode("ascii")
    digest = hashlib.sha256(payload).hexdigest()
    path = directory / f"axiom-v0.8.3-codex-core-v2-{digest}.json"
    path.write_bytes(payload)
    return path


def candidate_terminal_observation() -> dict:
    return load_candidate_one()


class RoutingEvaluationTests(unittest.TestCase):
    def test_checked_in_evaluation_contracts_pass(self):
        failures: list[str] = []
        self.assertEqual((64, 30, 11), check_routing_evaluations(failures))
        self.assertEqual([], failures)

    def test_v080_records_preserve_the_terminal_fail_and_unavailable_host(self):
        codex = load_v080_result("codex")
        claude = load_v080_result("claude-code")
        cases = corpus_cases()
        case_ids = benchmark_v2_case_ids()
        for host, record in (("codex", codex), ("claude-code", claude)):
            failures: list[str] = []
            validate_observation(
                record,
                host,
                case_ids,
                cases,
                f"fixture:v0.8.0 {host}",
                failures,
            )
            self.assertEqual([], failures)

        self.assertEqual(V080_CODEX_RUN_ID, codex["runId"])
        self.assertEqual(RELEASED_V080_SUBJECT, codex["axiom"])
        self.assertEqual("fail", codex["run"]["status"])
        self.assertEqual(1, codex["run"]["callCount"])
        self.assertEqual(
            ["fail"] + ["not-run"] * 16,
            [case["status"] for case in codex["cases"]],
        )
        self.assertEqual("valid", codex["cases"][0]["responseDiagnostic"])
        self.assertEqual("valid", codex["cases"][0]["acceptanceDiagnostic"])
        self.assertTrue(codex["cases"][0]["mutationAttempted"])
        self.assertFalse(codex["cases"][0]["mutationObserved"])
        self.assertIn("unexpectedTools=2", codex["cases"][0]["evidence"][2])
        self.assertEqual(
            V080_CLAUDE_UNAVAILABLE_RUN_ID,
            claude["runId"],
        )
        self.assertEqual("unavailable", claude["run"]["status"])
        self.assertEqual(0, claude["run"]["callCount"])
        self.assertTrue(all(case["status"] == "unavailable" for case in claude["cases"]))

        observations = [
            (relative_path, load_result(relative_path))
            for relative_path in EXPECTED_RESULT_BINDINGS
        ]
        failures = []
        validate_observation_run_set(
            observations,
            response_schema_digests(),
            failures,
        )
        self.assertEqual([], failures)
        for protected_path in (V080_CODEX_RESULT_PATH, V080_CLAUDE_RESULT_PATH):
            with self.subTest(protected_path=protected_path):
                tampered = [
                    (relative_path, load_result(relative_path))
                    for relative_path in EXPECTED_RESULT_BINDINGS
                ]
                changed = next(
                    record
                    for relative_path, record in tampered
                    if relative_path == protected_path
                )
                changed["run"]["limitations"].append("Rewritten outcome.")
                failures = []
                validate_observation_run_set(
                    tampered,
                    response_schema_digests(),
                    failures,
                )
                self.assertTrue(
                    any("preserved terminal outcome" in failure for failure in failures)
                )

    def test_external_post_tag_observation_passes_function_and_cli(self):
        record = external_v083_observation()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = write_content_addressed_observation(
                Path(temporary_directory), record
            )
            failures: list[str] = []
            digest = validate_external_routing_observation(
                path,
                expected_version="0.8.3",
                expected_tag="v0.8.3",
                expected_commit="b" * 40,
                expected_tree="c" * 40,
                failures=failures,
            )
            self.assertEqual([], failures)
            self.assertEqual(path.stem.rsplit("-", 1)[-1], digest)

            script = Path(__file__).resolve().parents[1] / "scripts" / "check-publication.py"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--post-tag-routing-observation",
                    str(path),
                    "--expected-version",
                    "0.8.3",
                    "--expected-tag",
                    "v0.8.3",
                    "--expected-commit",
                    "b" * 40,
                    "--expected-tree",
                    "c" * 40,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn(digest, completed.stdout)

    def test_external_post_tag_observation_rejects_partial_or_candidate_evidence(self):
        fixtures: list[tuple[str, dict, str]] = []
        candidate = external_v083_observation()
        candidate["axiom"]["tag"] = None
        candidate["axiom"]["releaseState"] = "candidate-unreleased"
        fixtures.append(("candidate", candidate, "exact released version"))

        wrong_call_count = external_v083_observation()
        wrong_call_count["run"]["callCount"] = 16
        fixtures.append(("call count", wrong_call_count, "run.callCount"))

        repeated = external_v083_observation()
        repeated["run"]["repeatCount"] = 2
        fixtures.append(("repeat count", repeated, "run.repeatCount"))

        not_run = external_v083_observation()
        not_run["cases"][-1].update(
            {
                "status": "not-run",
                "responseDiagnostic": "not-observed",
                "acceptanceDiagnostic": "not-observed",
                "evidenceSource": "not-observed",
                "routingGateObserved": None,
                "observedRoutes": None,
                "clarificationCount": None,
                "mutationAttempted": None,
                "mutationObserved": None,
                "evidence": [],
                "limitations": ["Not run."],
            }
        )
        fixtures.append(("not run", not_run, "17 passing cases"))

        reordered = external_v083_observation()
        reordered["cases"].reverse()
        fixtures.append(("case order", reordered, "exact benchmark order"))

        regression = external_v083_observation()
        regression["summary"]["highImpactFalsePositives"] = 1
        fixtures.append(("summary", regression, "zero-regression PASS"))

        malformed_run_id = external_v083_observation()
        malformed_run_id["runId"] = []
        fixtures.append(("run ID type", malformed_run_id, "runId must be"))

        for name, record, owned_reason in fixtures:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    path = write_content_addressed_observation(
                        Path(temporary_directory), record
                    )
                    failures: list[str] = []
                    validate_external_routing_observation(
                        path,
                        expected_version="0.8.3",
                        expected_tag="v0.8.3",
                        expected_commit="b" * 40,
                        expected_tree="c" * 40,
                        failures=failures,
                    )
                    self.assertTrue(
                        any(owned_reason in failure for failure in failures),
                        failures,
                    )

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = write_content_addressed_observation(
                Path(temporary_directory), external_v083_observation()
            )
            failures = []
            validate_external_routing_observation(
                path,
                expected_version="0.8.3",
                expected_tag="v0.8.3",
                expected_commit="b" * 40,
                expected_tree="d" * 40,
                failures=failures,
            )
            self.assertTrue(
                any("exact released version" in failure for failure in failures),
                failures,
            )

        with tempfile.TemporaryDirectory() as temporary_directory:
            payload = (json.dumps(external_v083_observation(), indent=2) + "\n").replace(
                '  "schemaVersion": "2",',
                '  "schemaVersion": "2",\n  "schemaVersion": "2",',
                1,
            ).encode("ascii")
            digest = hashlib.sha256(payload).hexdigest()
            path = (
                Path(temporary_directory)
                / f"axiom-v0.8.3-codex-core-v2-{digest}.json"
            )
            path.write_bytes(payload)
            failures = []
            validate_external_routing_observation(
                path,
                expected_version="0.8.3",
                expected_tag="v0.8.3",
                expected_commit="b" * 40,
                expected_tree="c" * 40,
                failures=failures,
            )
            self.assertTrue(
                any("duplicate key" in failure for failure in failures),
                failures,
            )

    def test_case_negative_fixtures_fail_with_owned_reason(self):
        for name, case in case_negative_fixtures():
            with self.subTest(name=name):
                failures: list[str] = []
                validate_case(case, f"fixture:{name}", failures)
                self.assertTrue(failures, name)
                self.assertTrue(
                    all(failure.startswith(f"fixture:{name}") for failure in failures),
                    failures,
                )

    def test_model_facing_schema_rejects_non_subset_keywords(self):
        for name, schema in host_response_schema_negative_fixtures():
            with self.subTest(name=name):
                failures: list[str] = []
                check_host_response_schema(schema, failures)
                self.assertTrue(failures, name)

    def test_v1_is_frozen_and_v2_is_exact_and_prose_free(self):
        root = Path(__file__).resolve().parents[1]
        v1_path = root / HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH
        v2_path = root / HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH
        self.assertEqual(
            V1_HOST_RESPONSE_SCHEMA_SHA256,
            hashlib.sha256(v1_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
            hashlib.sha256(v2_path.read_bytes()).hexdigest(),
        )
        schema = json.loads(v2_path.read_text(encoding="utf-8"))
        failures: list[str] = []
        check_host_response_schema_v2(schema, failures)
        self.assertEqual([], failures)
        self.assertNotIn("evidence", schema["properties"])
        for name, malformed in host_response_schema_v2_negative_fixtures():
            with self.subTest(name=name):
                failures = []
                check_host_response_schema_v2(malformed, failures)
                self.assertTrue(failures, name)

    def test_v2_structure_and_acceptance_exclude_model_prose(self):
        response = valid_host_response_v2()
        failures: list[str] = []
        validate_host_response_v2(response, "fixture:valid V2 response", failures)
        self.assertEqual([], failures)

        with_model_evidence = dict(response, evidence=["model prose"])
        failures = []
        validate_host_response_v2_structure(
            with_model_evidence,
            "fixture:V2 response with evidence",
            failures,
        )
        self.assertTrue(any("unknown fields" in failure for failure in failures))

        duplicate_routes = dict(
            response,
            selectedRoutes=["agents-architect", "agents-architect"],
        )
        structural_failures: list[str] = []
        validate_host_response_v2_structure(
            duplicate_routes,
            "fixture:V2 duplicate routes",
            structural_failures,
        )
        self.assertEqual([], structural_failures)
        self.assertEqual(
            "selected-routes-duplicate",
            classify_host_response_v2_acceptance(duplicate_routes),
        )

    def test_v3_adds_only_the_current_route_to_the_prose_free_contract(self):
        root = Path(__file__).resolve().parents[1]
        v3_path = root / HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH
        self.assertEqual(
            CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
            hashlib.sha256(v3_path.read_bytes()).hexdigest(),
        )
        schema = json.loads(v3_path.read_text(encoding="utf-8"))
        failures: list[str] = []
        check_host_response_schema_v3(schema, failures)
        self.assertEqual([], failures)

        response = dict(
            valid_host_response_v2(),
            selectedRoutes=["agent-plugin-architect"],
        )
        failures = []
        validate_host_response_v3(response, "fixture:valid V3 response", failures)
        self.assertEqual([], failures)
        self.assertEqual("valid", classify_host_response_v3_acceptance(response))

        historical_failures: list[str] = []
        validate_host_response_v2_structure(
            response,
            "fixture:V2 rejects successor route",
            historical_failures,
        )
        self.assertTrue(historical_failures)

        duplicate_routes = dict(
            response,
            selectedRoutes=["agent-plugin-architect", "agent-plugin-architect"],
        )
        structural_failures: list[str] = []
        validate_host_response_v3_structure(
            duplicate_routes,
            "fixture:V3 duplicate routes",
            structural_failures,
        )
        self.assertEqual([], structural_failures)
        self.assertEqual(
            "selected-routes-duplicate",
            classify_host_response_v3_acceptance(duplicate_routes),
        )

    def test_observer_derived_evidence_is_deterministic_bounded_and_private(self):
        facts = {
            "routing_gate_observed": True,
            "selected_routes": ["agents-architect"],
            "clarification_count": 0,
            "mutation_attempted": False,
            "mutation_observed": False,
            "turn_completed": True,
            "failure_event": False,
            "unexpected_tools": 0,
            "workspace_unchanged": True,
            "source_unchanged": True,
            "installed_unchanged": True,
        }
        first = derive_observer_evidence(**facts)
        second = derive_observer_evidence(**facts)
        self.assertEqual(first, second)
        self.assertEqual(3, len(first))
        self.assertTrue(all(len(item) <= 240 for item in first))
        failures: list[str] = []
        validate_observer_derived_evidence(
            first,
            routing_gate_observed=True,
            selected_routes=["agents-architect"],
            clarification_count=0,
            mutation_attempted=False,
            mutation_observed=False,
            label="fixture:observer evidence",
            failures=failures,
        )
        self.assertEqual([], failures)

        for sensitive in (
            "/home/example/private",
            "/Users/example/private",
            "/tmp/example-private",
            r"C:\Users\Example\private",
            "sk-abcdefgh",
            "ghp_abcdefgh",
            "github_pat_abcdefgh",
            "thread-id",
        ):
            with self.subTest(sensitive_family=sensitive.split("-")[0]):
                tampered = list(first)
                tampered[2] = sensitive
                failures = []
                validate_observer_derived_evidence(
                    tampered,
                    routing_gate_observed=True,
                    selected_routes=["agents-architect"],
                    clarification_count=0,
                    mutation_attempted=False,
                    mutation_observed=False,
                    label="fixture:sensitive observer evidence",
                    failures=failures,
                )
                self.assertTrue(failures)
                retained = json.dumps({"failures": ["observer-evidence-invalid"]})
                self.assertNotIn(sensitive, retained)
        with self.assertRaises(ValueError):
            derive_observer_evidence(**dict(facts, selected_routes=["private-route"]))

    def test_candidate_four_requires_v2_observer_provenance(self):
        record = prospective_candidate_four_observation()
        failures: list[str] = []
        validate_observation(
            record,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:Candidate 4",
            failures,
        )
        self.assertEqual([], failures)

        failures = []
        validate_observation_run_set(
            [(CANDIDATE4_RESULT_PATH, record)],
            response_schema_digests(),
            failures,
        )
        self.assertTrue(
            any("immutable subject binding" in failure for failure in failures)
        )

        for name, mutate in (
            (
                "missing provenance",
                lambda item: item.pop("evidenceSource"),
            ),
            (
                "model-provided provenance",
                lambda item: item.update(evidenceSource="model-provided"),
            ),
            (
                "V1 evidence structural diagnostic",
                lambda item: item.update(responseDiagnostic="schema-evidence"),
            ),
            (
                "V1 empty-evidence acceptance diagnostic",
                lambda item: item.update(acceptanceDiagnostic="evidence-empty-string"),
            ),
            (
                "V1 overlength-evidence acceptance diagnostic",
                lambda item: item.update(acceptanceDiagnostic="evidence-overlength"),
            ),
            (
                "V1 duplicate-evidence acceptance diagnostic",
                lambda item: item.update(acceptanceDiagnostic="evidence-duplicate"),
            ),
            (
                "V1 evidence privacy diagnostic",
                lambda item: item.update(acceptanceDiagnostic="privacy"),
            ),
        ):
            with self.subTest(name=name):
                changed = json.loads(json.dumps(record))
                mutate(changed["cases"][0])
                failures = []
                validate_observation(
                    changed,
                    "codex",
                    benchmark_case_ids(),
                    corpus_cases(),
                    f"fixture:{name}",
                    failures,
                )
                self.assertTrue(failures, name)

        unattempted = json.loads(json.dumps(record))
        unattempted["cases"][1]["evidenceSource"] = "observer-derived"
        failures = []
        validate_observation(
            unattempted,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:unattempted observer provenance",
            failures,
        )
        self.assertTrue(any("unattempted" in failure for failure in failures))

        false_pass = json.loads(json.dumps(record))
        false_pass["cases"][0].update(
            {
                "status": "pass",
                "responseDiagnostic": "valid",
                "acceptanceDiagnostic": "valid",
                "routingGateObserved": True,
                "observedRoutes": ["agents-architect"],
                "clarificationCount": 0,
                "mutationAttempted": False,
                "mutationObserved": False,
                "limitations": [],
            }
        )
        false_pass["cases"][0]["evidence"] = derive_observer_evidence(
            routing_gate_observed=True,
            selected_routes=["agents-architect"],
            clarification_count=0,
            mutation_attempted=False,
            mutation_observed=False,
            turn_completed=False,
            failure_event=False,
            unexpected_tools=0,
            workspace_unchanged=True,
            source_unchanged=True,
            installed_unchanged=True,
        )
        failures = []
        validate_observation(
            false_pass,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:false observer pass",
            failures,
        )
        self.assertTrue(any("every observer PASS gate" in failure for failure in failures))

    def test_host_response_constraints_remain_offline(self):
        failures: list[str] = []
        validate_host_response(valid_host_response(), "fixture:valid response", failures)
        self.assertEqual([], failures)
        for name, response in host_response_negative_fixtures():
            with self.subTest(name=name):
                failures = []
                validate_host_response(response, f"fixture:{name}", failures)
                self.assertTrue(failures, name)

    def test_model_structure_and_acceptance_gates_are_distinct(self):
        observed = {"not-observed", "not-evaluated"}
        for name, expected, response in host_response_acceptance_fixtures():
            with self.subTest(name=name):
                structural_failures: list[str] = []
                validate_host_response_structure(
                    response,
                    f"fixture:{name}",
                    structural_failures,
                )
                self.assertEqual([], structural_failures)
                diagnostic = classify_host_response_acceptance(response)
                self.assertEqual(expected, diagnostic)
                observed.add(diagnostic)
                retained = json.dumps({"acceptanceDiagnostic": diagnostic})
                for evidence in response["evidence"]:
                    if diagnostic == "privacy":
                        self.assertNotIn(evidence, retained)
                aggregate_failures: list[str] = []
                validate_host_response(
                    response,
                    f"fixture:{name}",
                    aggregate_failures,
                )
                self.assertEqual(expected != "valid", bool(aggregate_failures))
        self.assertEqual(set(ACCEPTANCE_DIAGNOSTICS), observed)

    def test_acceptance_diagnostic_is_closed_and_status_bound(self):
        valid_cases = (
            ("not-observed", "not-run", "not-observed"),
            ("not-evaluated", "unknown", "schema-evidence"),
            ("valid", "pass", "valid"),
            ("selected-routes-duplicate", "fail", "valid"),
            ("evidence-empty-string", "fail", "valid"),
            ("evidence-overlength", "fail", "valid"),
            ("evidence-duplicate", "fail", "valid"),
            ("privacy", "unknown", "valid"),
        )
        for diagnostic, status, response_diagnostic in valid_cases:
            with self.subTest(valid_acceptance=diagnostic):
                failures: list[str] = []
                validate_acceptance_diagnostic(
                    diagnostic,
                    status,
                    response_diagnostic,
                    True,
                    "fixture:acceptance diagnostic",
                    failures,
                )
                self.assertEqual([], failures)

        for malformed in (None, "", "arbitrary", [], {}):
            with self.subTest(malformed_acceptance=repr(malformed)):
                failures = []
                validate_acceptance_diagnostic(
                    malformed,
                    "unknown",
                    "valid",
                    True,
                    "fixture:acceptance diagnostic",
                    failures,
                )
                self.assertTrue(failures)

        for diagnostic, status, response_diagnostic in (
            ("not-evaluated", "unknown", "valid"),
            ("evidence-duplicate", "unknown", "valid"),
            ("privacy", "fail", "valid"),
            ("valid", "pass", "schema-evidence"),
        ):
            with self.subTest(invalid_binding=diagnostic):
                failures = []
                validate_acceptance_diagnostic(
                    diagnostic,
                    status,
                    response_diagnostic,
                    True,
                    "fixture:acceptance diagnostic",
                    failures,
                )
                self.assertTrue(failures)

    def test_structural_response_diagnostic_is_closed_and_status_bound(self):
        for diagnostic in RESPONSE_DIAGNOSTICS:
            with self.subTest(valid_diagnostic=diagnostic):
                if diagnostic == "not-observed":
                    status = "not-run"
                    run_id = "future-candidate-run"
                elif diagnostic == "subtype-unavailable":
                    status = "unknown"
                    run_id = CANDIDATE_CODEX_RUN_ID
                elif diagnostic == "valid":
                    status = "pass"
                    run_id = "future-candidate-run"
                else:
                    status = "unknown"
                    run_id = "future-candidate-run"
                failures: list[str] = []
                validate_response_diagnostic(
                    diagnostic,
                    status,
                    run_id,
                    True,
                    "fixture:response diagnostic",
                    failures,
                )
                self.assertEqual([], failures)

        for malformed in (None, "", "arbitrary", [], {}):
            with self.subTest(malformed_diagnostic=repr(malformed)):
                failures = []
                validate_response_diagnostic(
                    malformed,
                    "unknown",
                    "future-candidate-run",
                    True,
                    "fixture:response diagnostic",
                    failures,
                )
                self.assertTrue(failures)

        failures = []
        validate_response_diagnostic(
            "subtype-unavailable",
            "unknown",
            "future-candidate-run",
            True,
            "fixture:response diagnostic",
            failures,
        )
        self.assertTrue(any("candidate-1" in failure for failure in failures))

        for diagnostic in RESPONSE_DIAGNOSTICS:
            if not diagnostic.startswith(
                ("missing", "json", "duplicate", "wrong", "schema")
            ):
                continue
            with self.subTest(structural_failure_status=diagnostic):
                failures = []
                validate_response_diagnostic(
                    diagnostic,
                    "fail",
                    "future-candidate-run",
                    True,
                    "fixture:response diagnostic",
                    failures,
                )
                self.assertTrue(
                    any("must preserve unknown status" in failure for failure in failures)
                )

        for diagnostic in RESPONSE_DIAGNOSTICS:
            if diagnostic == "valid":
                continue
            with self.subTest(pass_diagnostic=diagnostic):
                failures = []
                validate_response_diagnostic(
                    diagnostic,
                    "pass",
                    CANDIDATE_CODEX_RUN_ID,
                    True,
                    "fixture:response diagnostic",
                    failures,
                )
                self.assertTrue(any("must be valid" in failure for failure in failures))

    def test_observation_negative_fixtures_fail(self):
        cases = corpus_cases()
        case_ids = benchmark_case_ids()
        for name, observation in observation_negative_fixtures():
            with self.subTest(name=name):
                failures: list[str] = []
                validate_observation(
                    observation,
                    "codex",
                    case_ids,
                    cases,
                    f"fixture:{name}",
                    failures,
                )
                self.assertTrue(failures, name)

    def test_partial_unknown_batch_preserves_stop_and_null_metrics(self):
        failures: list[str] = []
        validate_observation(
            partial_unknown_observation(),
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:partial unknown",
            failures,
        )
        self.assertEqual([], failures)

    def test_run_identities_and_schema_bindings_are_stable(self):
        codex = load_observation("codex")
        claude = load_observation("claude-code")
        recovery = load_observation("codex-recovery-1")
        recovery_two = load_observation("codex-recovery-2")
        recovery_three = load_recovery_three()
        candidate_one = load_candidate_one()
        candidate_two = load_candidate_two()
        candidate_three = load_candidate_three()
        candidate_four = load_candidate_four()
        self.assertEqual(INITIAL_CODEX_RUN_ID, codex["runId"])
        self.assertEqual(FAILED_HOST_RESPONSE_SCHEMA_SHA256, codex["responseSchema"]["sha256"])
        self.assertEqual(CLAUDE_UNAVAILABLE_RUN_ID, claude["runId"])
        self.assertIsNone(claude["responseSchema"])
        self.assertEqual(
            "codex-v0-7-7-linux-codex-core-v1-recovery-1",
            RECOVERY_CODEX_RUN_ID,
        )
        self.assertEqual(
            "377ac22919164033b3dcf55f2b6b96086a5e2731c9b1edacabd5797a0b9127b6",
            V1_HOST_RESPONSE_SCHEMA_SHA256,
        )
        self.assertEqual(RECOVERY_CODEX_RUN_ID, recovery["runId"])
        self.assertEqual(
            V1_HOST_RESPONSE_SCHEMA_SHA256,
            recovery["responseSchema"]["sha256"],
        )
        self.assertEqual("2026-08-21T22:10:47Z", recovery["run"]["recordedAt"])
        self.assertEqual("fail", recovery["run"]["status"])
        self.assertEqual(
            ["fail"] + ["not-run"] * 12,
            [case["status"] for case in recovery["cases"]],
        )
        self.assertEqual(
            "codex-v0-7-7-linux-codex-core-v1-recovery-2",
            RECOVERY2_CODEX_RUN_ID,
        )
        self.assertEqual(RECOVERY2_CODEX_RUN_ID, recovery_two["runId"])
        self.assertEqual(
            V1_HOST_RESPONSE_SCHEMA_SHA256,
            recovery_two["responseSchema"]["sha256"],
        )
        self.assertEqual("2026-08-22T05:13:31Z", recovery_two["run"]["recordedAt"])
        self.assertEqual("fail", recovery_two["run"]["status"])
        self.assertEqual(
            ["fail"] + ["not-run"] * 12,
            [case["status"] for case in recovery_two["cases"]],
        )
        self.assertEqual(
            "codex-v0-7-7-linux-codex-core-v1-recovery-3",
            RECOVERY3_CODEX_RUN_ID,
        )
        self.assertEqual(RECOVERY3_CODEX_RUN_ID, recovery_three["runId"])
        self.assertEqual(
            V1_HOST_RESPONSE_SCHEMA_SHA256,
            recovery_three["responseSchema"]["sha256"],
        )
        self.assertEqual("2026-08-22T07:11:52Z", recovery_three["run"]["recordedAt"])
        self.assertEqual("fail", recovery_three["run"]["status"])
        self.assertEqual(
            ["pass"] * 10 + ["fail"] + ["not-run"] * 2,
            [case["status"] for case in recovery_three["cases"]],
        )
        self.assertEqual(CANDIDATE_CODEX_RUN_ID, candidate_one["runId"])
        self.assertEqual(CANDIDATE_V078_SUBJECT, candidate_one["axiom"])
        self.assertEqual("2026-08-22T17:48:56Z", candidate_one["run"]["recordedAt"])
        self.assertEqual("unknown", candidate_one["run"]["status"])
        self.assertEqual(11, candidate_one["run"]["callCount"])
        self.assertEqual(
            ["pass"] * 10 + ["unknown"] + ["not-run"] * 2,
            [case["status"] for case in candidate_one["cases"]],
        )
        self.assertEqual(CANDIDATE2_CODEX_RUN_ID, candidate_two["runId"])
        self.assertEqual(CANDIDATE2_V078_SUBJECT, candidate_two["axiom"])
        self.assertEqual("2026-08-23T00:06:22Z", candidate_two["run"]["recordedAt"])
        self.assertEqual("unknown", candidate_two["run"]["status"])
        self.assertEqual(9, candidate_two["run"]["callCount"])
        self.assertEqual(
            ["pass"] * 8 + ["unknown"] + ["not-run"] * 4,
            [case["status"] for case in candidate_two["cases"]],
        )
        self.assertEqual(
            ["valid"] * 8 + ["schema-evidence"] + ["not-observed"] * 4,
            [case["responseDiagnostic"] for case in candidate_two["cases"]],
        )
        self.assertEqual(
            ["valid"] * 8 + ["not-evaluated"] + ["not-observed"] * 4,
            [case["acceptanceDiagnostic"] for case in candidate_two["cases"]],
        )
        self.assertEqual(CANDIDATE3_CODEX_RUN_ID, candidate_three["runId"])
        self.assertEqual(CANDIDATE3_V078_SUBJECT, candidate_three["axiom"])
        self.assertEqual("2026-08-23T00:54:39Z", candidate_three["run"]["recordedAt"])
        self.assertEqual("fail", candidate_three["run"]["status"])
        self.assertEqual(8, candidate_three["run"]["callCount"])
        self.assertEqual(
            ["pass"] * 7 + ["fail"] + ["not-run"] * 5,
            [case["status"] for case in candidate_three["cases"]],
        )
        self.assertEqual(
            ["valid"] * 8 + ["not-observed"] * 5,
            [case["responseDiagnostic"] for case in candidate_three["cases"]],
        )
        self.assertEqual(
            ["valid"] * 7 + ["evidence-overlength"] + ["not-observed"] * 5,
            [case["acceptanceDiagnostic"] for case in candidate_three["cases"]],
        )
        failed_case = candidate_three["cases"][7]
        self.assertEqual([], failed_case["observedRoutes"])
        self.assertEqual(0, failed_case["clarificationCount"])
        self.assertFalse(failed_case["mutationAttempted"])
        self.assertFalse(failed_case["mutationObserved"])
        self.assertEqual([], failed_case["evidence"])
        self.assertEqual(
            ["The bounded response failed its closed publication acceptance gate."],
            failed_case["limitations"],
        )
        self.assertEqual(
            {
                "overallStatus": "fail",
                "evaluatedCases": 8,
                "canonicalFalseNegatives": 0,
                "highImpactFalsePositives": None,
                "clarificationMismatches": None,
                "mutationAttempts": None,
            },
            candidate_three["summary"],
        )
        self.assertEqual(CANDIDATE4_CODEX_RUN_ID, candidate_four["runId"])
        self.assertEqual(CANDIDATE4_V078_SUBJECT, candidate_four["axiom"])
        self.assertEqual("2026-08-23T08:36:51Z", candidate_four["run"]["recordedAt"])
        self.assertEqual("pass", candidate_four["run"]["status"])
        self.assertEqual(13, candidate_four["run"]["callCount"])
        self.assertEqual(["pass"] * 13, [case["status"] for case in candidate_four["cases"]])
        self.assertEqual(
            ["valid"] * 13,
            [case["responseDiagnostic"] for case in candidate_four["cases"]],
        )
        self.assertEqual(
            ["valid"] * 13,
            [case["acceptanceDiagnostic"] for case in candidate_four["cases"]],
        )
        self.assertEqual(
            ["observer-derived"] * 13,
            [case["evidenceSource"] for case in candidate_four["cases"]],
        )
        self.assertEqual(
            {
                "overallStatus": "pass",
                "evaluatedCases": 13,
                "canonicalFalseNegatives": 0,
                "highImpactFalsePositives": 0,
                "clarificationMismatches": 0,
                "mutationAttempts": 0,
            },
            candidate_four["summary"],
        )

    def test_run_set_rejects_duplicate_identity_and_binding_drift(self):
        paths = (
            "results/v0.7.7/codex/linux.json",
            "results/v0.7.7/claude-code/linux.json",
            RECOVERY_RESULT_PATH,
            RECOVERY2_RESULT_PATH,
            RECOVERY3_RESULT_PATH,
            CANDIDATE_RESULT_PATH,
            CANDIDATE2_RESULT_PATH,
            CANDIDATE3_RESULT_PATH,
            CANDIDATE4_RESULT_PATH,
        )
        codex = load_observation("codex")
        claude = load_observation("claude-code")
        duplicate = [
            (paths[0], codex),
            (paths[1], claude),
            (paths[2], load_observation("codex-recovery-1")),
            (paths[3], load_observation("codex-recovery-2")),
            (paths[4], load_recovery_three()),
            (paths[5], load_candidate_one()),
            (paths[6], load_candidate_two()),
            (paths[7], load_candidate_three()),
            (paths[8], load_candidate_four()),
        ]
        duplicate[1][1]["runId"] = codex["runId"]
        failures: list[str] = []
        validate_observation_run_set(duplicate, response_schema_digests(), failures)
        self.assertTrue(any("must be unique" in failure for failure in failures))

        codex = load_observation("codex")
        codex["responseSchema"]["sha256"] = CURRENT_HOST_RESPONSE_SCHEMA_SHA256
        failures = []
        validate_observation_run_set(
            [
                (paths[0], codex),
                (paths[1], load_observation("claude-code")),
                (paths[2], load_observation("codex-recovery-1")),
                (paths[3], load_observation("codex-recovery-2")),
                (paths[4], load_recovery_three()),
                (paths[5], load_candidate_one()),
                (paths[6], load_candidate_two()),
                (paths[7], load_candidate_three()),
                (paths[8], load_candidate_four()),
            ],
            response_schema_digests(),
            failures,
        )
        self.assertTrue(any("recorded run" in failure for failure in failures))

        preserved = (
            (paths[0], "codex"),
            (paths[1], "claude-code"),
            (paths[2], "codex-recovery-1"),
            (paths[3], "codex-recovery-2"),
            (paths[4], "codex-recovery-3"),
            (paths[5], "candidate-1"),
            (paths[6], "candidate-2"),
            (paths[7], "candidate-3"),
            (paths[8], "candidate-4"),
        )
        for changed_path, host in preserved:
            with self.subTest(preserved_run=host):
                observations = []
                candidate_loaders = {
                    "candidate-1": load_candidate_one,
                    "candidate-2": load_candidate_two,
                    "candidate-3": load_candidate_three,
                    "candidate-4": load_candidate_four,
                    "codex-recovery-3": load_recovery_three,
                }
                for path, source_host in preserved:
                    loader = candidate_loaders.get(source_host)
                    record = loader() if loader else load_observation(source_host)
                    observations.append((path, record))
                changed = next(
                    record for path, record in observations if path == changed_path
                )
                changed["run"]["limitations"].append(
                    "Rewritten historical outcome."
                )
                failures = []
                validate_observation_run_set(
                    observations,
                    response_schema_digests(),
                    failures,
                )
                self.assertTrue(
                    any("preserved terminal outcome" in failure for failure in failures)
                )
        self.assertEqual(
            "396baf099fd2e5b407b0c4dab4a2a75ac40e1a719452bef625ef9e99f389d2be",
            INITIAL_CODEX_OUTCOME_SHA256,
        )
        self.assertEqual(
            {
                INITIAL_CODEX_RUN_ID: (
                    "396baf099fd2e5b407b0c4dab4a2a75ac40e1a719452bef625ef9e99f389d2be"
                ),
                CLAUDE_UNAVAILABLE_RUN_ID: (
                    "ceb671ab631ad4f7882d92550ba81c58e97eff500565d60348249498a25efc7e"
                ),
                RECOVERY_CODEX_RUN_ID: (
                    "926913d803565f01354ee02f2dcf8746d9542fadeb50e081aa7f6aaf8c7e1158"
                ),
                RECOVERY2_CODEX_RUN_ID: (
                    "e98a70eab49ba2d198ce7c0970dd3100349cf5905b6fe6d9d2e83c2ad72079ea"
                ),
                RECOVERY3_CODEX_RUN_ID: (
                    "88a503e1facbcbf0a9797d81f970d21a090b490bbf757a704977afa3059a5dcd"
                ),
                CANDIDATE_CODEX_RUN_ID: (
                    "2e337b3dd6f01ad8fe157e5869fe820bf0356a09014bf75a867095cbc88a163c"
                ),
                CANDIDATE2_CODEX_RUN_ID: (
                    "3b05fd35a6e8013cbf84f5e56e741dc3fcfc5dd798354b3b6be375adb0794cab"
                ),
                CANDIDATE3_CODEX_RUN_ID: (
                    "279fc6f94250f5deab46e3a99f716477ba8abd654f290e7df0831de34b1582fb"
                ),
                CANDIDATE4_CODEX_RUN_ID: (
                    "23916a39703f6f77ae049ab8f6f8037a429d72ce485001ef517f662d60527689"
                ),
                V080_CODEX_RUN_ID: (
                    "72030ae826b131de45a77fff0f2f4717e03783f1edb4a812de9e577ec4ab4574"
                ),
                V080_CLAUDE_UNAVAILABLE_RUN_ID: (
                    "043402c24e12705ac153296e8a6bc0016fdfceca3ac42dbdbfa7d74c796de0f7"
                ),
            },
            PRESERVED_OUTCOME_SHA256,
        )

    def test_terminal_recovery_run_uses_independent_identity_and_order(self):
        recovery = load_recovery_three()
        failures: list[str] = []
        validate_observation(
            recovery,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:terminal recovery",
            failures,
        )
        self.assertEqual([], failures)

        validate_observation_run_set(
            [
                ("results/v0.7.7/codex/linux.json", load_observation("codex")),
                (
                    "results/v0.7.7/claude-code/linux.json",
                    load_observation("claude-code"),
                ),
                (RECOVERY_RESULT_PATH, load_observation("codex-recovery-1")),
                (RECOVERY2_RESULT_PATH, load_observation("codex-recovery-2")),
                (RECOVERY3_RESULT_PATH, recovery),
                (CANDIDATE_RESULT_PATH, load_candidate_one()),
                (CANDIDATE2_RESULT_PATH, load_candidate_two()),
                (CANDIDATE3_RESULT_PATH, load_candidate_three()),
                (CANDIDATE4_RESULT_PATH, load_candidate_four()),
            ],
            response_schema_digests(),
            failures,
        )
        self.assertEqual([], failures)

    def test_recovery_three_is_required_terminal_and_immutable(self):
        recovery = load_recovery_three()
        observations = [
            ("results/v0.7.7/codex/linux.json", load_observation("codex")),
            (
                "results/v0.7.7/claude-code/linux.json",
                load_observation("claude-code"),
            ),
            (RECOVERY_RESULT_PATH, load_observation("codex-recovery-1")),
            (RECOVERY2_RESULT_PATH, load_observation("codex-recovery-2")),
            (RECOVERY3_RESULT_PATH, recovery),
            (CANDIDATE_RESULT_PATH, load_candidate_one()),
            (CANDIDATE2_RESULT_PATH, load_candidate_two()),
            (CANDIDATE3_RESULT_PATH, load_candidate_three()),
            (CANDIDATE4_RESULT_PATH, load_candidate_four()),
        ]
        failures: list[str] = []
        validate_observation_run_set(
            observations,
            response_schema_digests(),
            failures,
        )
        self.assertEqual([], failures)

        recovery = load_recovery_three()
        recovery["run"]["status"] = "not-run"
        failures = []
        validate_observation_run_set(
            [
                ("results/v0.7.7/codex/linux.json", load_observation("codex")),
                (
                    "results/v0.7.7/claude-code/linux.json",
                    load_observation("claude-code"),
                ),
                (RECOVERY_RESULT_PATH, load_observation("codex-recovery-1")),
                (RECOVERY2_RESULT_PATH, load_observation("codex-recovery-2")),
                (RECOVERY3_RESULT_PATH, recovery),
                (CANDIDATE_RESULT_PATH, load_candidate_one()),
                (CANDIDATE2_RESULT_PATH, load_candidate_two()),
                (CANDIDATE3_RESULT_PATH, load_candidate_three()),
                (CANDIDATE4_RESULT_PATH, load_candidate_four()),
            ],
            response_schema_digests(),
            failures,
        )
        self.assertTrue(any("only as a terminal run" in failure for failure in failures))

    def test_unreleased_candidate_subjects_are_explicit_terminal_and_independent(self):
        candidate = candidate_terminal_observation()
        failures: list[str] = []
        validate_observation(
            candidate,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:unreleased candidate",
            failures,
        )
        self.assertEqual([], failures)

        candidate_two = load_candidate_two()
        candidate_two_path = (
            Path(__file__).resolve().parents[1] / "evals" / CANDIDATE2_RESULT_PATH
        )
        self.assertTrue(candidate_two_path.is_file())
        failures = []
        validate_observation_run_set(
            [
                ("results/v0.7.7/codex/linux.json", load_observation("codex")),
                (
                    "results/v0.7.7/claude-code/linux.json",
                    load_observation("claude-code"),
                ),
                (RECOVERY_RESULT_PATH, load_observation("codex-recovery-1")),
                (RECOVERY2_RESULT_PATH, load_observation("codex-recovery-2")),
                (RECOVERY3_RESULT_PATH, load_recovery_three()),
                (CANDIDATE_RESULT_PATH, load_candidate_one()),
                (CANDIDATE2_RESULT_PATH, candidate_two),
                (CANDIDATE3_RESULT_PATH, load_candidate_three()),
                (CANDIDATE4_RESULT_PATH, load_candidate_four()),
            ],
            response_schema_digests(),
            failures,
        )
        self.assertEqual([], failures)

        wrong_candidate_two = json.loads(json.dumps(candidate_two))
        wrong_candidate_two["axiom"]["commit"] = "0" * 40
        failures = []
        validate_observation_run_set(
            [
                ("results/v0.7.7/codex/linux.json", load_observation("codex")),
                (
                    "results/v0.7.7/claude-code/linux.json",
                    load_observation("claude-code"),
                ),
                (RECOVERY_RESULT_PATH, load_observation("codex-recovery-1")),
                (RECOVERY2_RESULT_PATH, load_observation("codex-recovery-2")),
                (RECOVERY3_RESULT_PATH, load_recovery_three()),
                (CANDIDATE_RESULT_PATH, load_candidate_one()),
                (CANDIDATE2_RESULT_PATH, wrong_candidate_two),
                (CANDIDATE3_RESULT_PATH, load_candidate_three()),
                (CANDIDATE4_RESULT_PATH, load_candidate_four()),
            ],
            response_schema_digests(),
            failures,
        )
        self.assertTrue(any("immutable subject binding" in item for item in failures))

        candidate_three_path = (
            Path(__file__).resolve().parents[1] / "evals" / CANDIDATE3_RESULT_PATH
        )
        self.assertTrue(candidate_three_path.is_file())
        self.assertEqual((), OPTIONAL_RESULT_PATHS)
        self.assertEqual(
            (
                CANDIDATE3_CODEX_RUN_ID,
                V1_HOST_RESPONSE_SCHEMA_SHA256,
            ),
            EXPECTED_RESULT_BINDINGS[CANDIDATE3_RESULT_PATH],
        )
        self.assertEqual(
            CANDIDATE3_V078_SUBJECT,
            EXPECTED_RESULT_SUBJECTS[CANDIDATE3_RESULT_PATH],
        )
        candidate_four_path = (
            Path(__file__).resolve().parents[1] / "evals" / CANDIDATE4_RESULT_PATH
        )
        self.assertTrue(candidate_four_path.is_file())
        self.assertEqual(
            (CANDIDATE4_CODEX_RUN_ID, CURRENT_HOST_RESPONSE_SCHEMA_SHA256),
            EXPECTED_RESULT_BINDINGS[CANDIDATE4_RESULT_PATH],
        )
        self.assertEqual(
            CANDIDATE4_V078_SUBJECT,
            EXPECTED_RESULT_SUBJECTS[CANDIDATE4_RESULT_PATH],
        )

        failures = []
        validate_observation_run_set(
            [
                ("results/v0.7.7/codex/linux.json", load_observation("codex")),
                (
                    "results/v0.7.7/claude-code/linux.json",
                    load_observation("claude-code"),
                ),
                (RECOVERY_RESULT_PATH, load_observation("codex-recovery-1")),
                (RECOVERY2_RESULT_PATH, load_observation("codex-recovery-2")),
                (RECOVERY3_RESULT_PATH, load_recovery_three()),
                (CANDIDATE_RESULT_PATH, candidate),
                (CANDIDATE2_RESULT_PATH, load_candidate_two()),
                (CANDIDATE3_RESULT_PATH, load_candidate_three()),
                (CANDIDATE4_RESULT_PATH, load_candidate_four()),
            ],
            response_schema_digests(),
            failures,
        )
        self.assertEqual([], failures)

    def test_candidate_null_tag_and_terminal_materialization_are_fail_closed(self):
        missing_label = candidate_terminal_observation()
        missing_label["axiom"].pop("releaseState")
        failures: list[str] = []
        validate_observation(
            missing_label,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:unlabeled candidate",
            failures,
        )
        self.assertTrue(any("candidate-unreleased" in failure for failure in failures))

        released_with_candidate_label = load_recovery_three()
        released_with_candidate_label["axiom"]["releaseState"] = "candidate-unreleased"
        failures = []
        validate_observation(
            released_with_candidate_label,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:released candidate label",
            failures,
        )
        self.assertTrue(any("unknown fields" in failure for failure in failures))

        wrong_subject = candidate_terminal_observation()
        wrong_subject["axiom"]["commit"] = "0" * 40
        failures = []
        validate_observation_run_set(
            [(CANDIDATE_RESULT_PATH, wrong_subject)],
            response_schema_digests(),
            failures,
        )
        self.assertTrue(any("immutable subject binding" in failure for failure in failures))

        nonterminal = candidate_terminal_observation()
        nonterminal["run"]["status"] = "not-run"
        failures = []
        validate_observation_run_set(
            [(CANDIDATE_RESULT_PATH, nonterminal)],
            response_schema_digests(),
            failures,
        )
        self.assertTrue(any("only as a terminal run" in failure for failure in failures))

        missing_call_count = candidate_terminal_observation()
        missing_call_count["run"].pop("callCount")
        failures = []
        validate_observation(
            missing_call_count,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:missing candidate call count",
            failures,
        )
        self.assertTrue(any("callCount is required" in failure for failure in failures))

        wrong_call_count = candidate_terminal_observation()
        wrong_call_count["run"]["callCount"] = 10
        failures = []
        validate_observation(
            wrong_call_count,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:wrong candidate call count",
            failures,
        )
        self.assertTrue(any("callCount disagrees" in failure for failure in failures))

        missing_acceptance = load_candidate_three()
        missing_acceptance["cases"][0].pop("acceptanceDiagnostic")
        failures = []
        validate_observation(
            missing_acceptance,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:missing acceptance diagnostic",
            failures,
        )
        self.assertTrue(
            any("required for this candidate observer" in failure for failure in failures)
        )

        rewritten_combined_failure = load_candidate_two()
        rewritten_combined_failure["cases"][8]["acceptanceDiagnostic"] = "valid"
        failures = []
        validate_observation(
            rewritten_combined_failure,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:combined classifier rewrite",
            failures,
        )
        self.assertTrue(any("must be not-evaluated" in failure for failure in failures))

        missing_diagnostic = candidate_terminal_observation()
        missing_diagnostic["cases"][0].pop("responseDiagnostic")
        failures = []
        validate_observation(
            missing_diagnostic,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:missing response diagnostic",
            failures,
        )
        self.assertTrue(
            any("required for candidate evidence" in failure for failure in failures)
        )

        invalid_pass_diagnostic = candidate_terminal_observation()
        invalid_pass_diagnostic["cases"][0]["responseDiagnostic"] = "json-syntax"
        failures = []
        validate_observation(
            invalid_pass_diagnostic,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:invalid passing response diagnostic",
            failures,
        )
        self.assertTrue(any("must be valid" in failure for failure in failures))

    def test_passing_case_one_alone_cannot_be_published_as_batch_pass(self):
        record = terminal_recovery_observation()
        record["run"].update({"status": "pass", "limitations": []})
        record["cases"][1].update(
            {
                "status": "not-run",
                "limitations": ["The independent recovery batch is still in progress."],
            }
        )
        record["summary"].update(
            {
                "overallStatus": "pass",
                "evaluatedCases": 1,
            }
        )
        failures: list[str] = []
        validate_observation(
            record,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:partial passing recovery",
            failures,
        )
        self.assertTrue(any("must all pass" in failure for failure in failures))

    def test_attempt_after_first_failure_is_rejected(self):
        record = partial_unknown_observation()
        record["cases"][1].update(
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
        failures: list[str] = []
        validate_observation(
            record,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:attempt after stop",
            failures,
        )
        self.assertTrue(any("after the first failure" in failure for failure in failures))

    def test_unattempted_observation_claim_is_rejected(self):
        record = partial_unknown_observation()
        record["cases"][1]["observedRoutes"] = []
        failures: list[str] = []
        validate_observation(
            record,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:unattempted claim",
            failures,
        )
        self.assertTrue(any("claims an observation" in failure for failure in failures))

    def test_unknown_summary_cannot_be_rewritten_as_zero(self):
        record = partial_unknown_observation()
        record["summary"]["canonicalFalseNegatives"] = 0
        failures: list[str] = []
        validate_observation(
            record,
            "codex",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:unknown summary",
            failures,
        )
        self.assertTrue(
            any("canonicalFalseNegatives is inconsistent" in failure for failure in failures)
        )

    def test_duplicate_jsonl_keys_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="axiom-routing-jsonl-") as directory:
            root = Path(directory)
            path = root / "duplicate.jsonl"
            path.write_text('{"id":"one","id":"two"}\n', encoding="utf-8")
            failures: list[str] = []
            self.assertEqual([], load_jsonl_cases(path, failures, root))
            self.assertTrue(any("duplicate key" in failure for failure in failures))

    def test_unavailable_claude_record_remains_non_observational(self):
        record = load_observation("claude-code")
        self.assertEqual("unavailable", record["run"]["status"])
        self.assertEqual(0, record["run"]["repeatCount"])
        self.assertTrue(all(case["status"] == "unavailable" for case in record["cases"]))
        self.assertTrue(all(case["observedRoutes"] is None for case in record["cases"]))
        self.assertTrue(
            all(case["routingGateObserved"] is None for case in record["cases"])
        )
        record["responseSchema"] = {
            "path": "evals/host-response-schema-v1.json",
            "sha256": V1_HOST_RESPONSE_SCHEMA_SHA256,
        }
        failures: list[str] = []
        validate_observation(
            record,
            "claude-code",
            benchmark_case_ids(),
            corpus_cases(),
            "fixture:unavailable schema claim",
            failures,
        )
        self.assertTrue(
            any("schema for an unattempted run" in failure for failure in failures)
        )


if __name__ == "__main__":
    unittest.main()
