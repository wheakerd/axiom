"""Current routing acceptance without reinterpreting frozen host observations."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from axiom_validation.context import RELEASE_VERSION, REPOSITORY_ROOT
from axiom_validation.routing_contracts import historical_route_contract, route_contract
from axiom_validation.routing_evals import (
    BENCHMARK_V3_ID,
    CURRENT_BENCHMARK_CASE_COUNT,
    CURRENT_HOST_RESPONSE_SCHEMA_V4_SHA256,
    CURRENT_PUBLIC_ROUTES,
    HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH,
    check_current_routing_evaluations,
    check_host_response_schema_v4,
    check_schema_contract_v3,
    classify_host_response_v4_acceptance,
    collect_current_corpus,
    current_benchmark_case_ids,
    derive_observer_evidence,
    validate_external_routing_observation,
    validate_host_response_v3_structure,
    validate_host_response_v4,
    validate_observation,
)
from tests.test_routing_evals import external_current_observation


def current_record() -> dict:
    """Build synthetic observer facts, never host-execution evidence."""
    record = external_current_observation()
    failures = []
    cases = collect_current_corpus(REPOSITORY_ROOT, failures)
    ids = current_benchmark_case_ids(REPOSITORY_ROOT, cases, failures)
    if failures:
        raise AssertionError(failures)
    template = record["cases"][0]
    results = []
    for case_id in ids:
        case = cases[case_id]
        result = copy.deepcopy(template)
        result.update(
            id=case_id, observedRoutes=case["expectedRoutes"],
            clarificationCount=case["expectedClarificationCount"],
        )
        result["evidence"] = derive_observer_evidence(
            routing_gate_observed=True, selected_routes=result["observedRoutes"],
            clarification_count=result["clarificationCount"],
            mutation_attempted=False, mutation_observed=False,
            turn_completed=True, failure_event=False, unexpected_tools=0,
            workspace_unchanged=True, source_unchanged=True, installed_unchanged=True,
        )
        results.append(result)
    record.update(
        schemaVersion="3", benchmarkId=BENCHMARK_V3_ID,
        runId="synthetic-current-routing-regression", cases=results,
        responseSchema={"path": HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH,
                        "sha256": CURRENT_HOST_RESPONSE_SCHEMA_V4_SHA256},
    )
    record["run"]["callCount"] = len(results)
    record["summary"]["evaluatedCases"] = len(results)
    return record


def observation_failures(record: dict) -> list[str]:
    failures = []
    cases = collect_current_corpus(REPOSITORY_ROOT, failures)
    ids = current_benchmark_case_ids(REPOSITORY_ROOT, cases, failures)
    validate_observation(record, "codex", ids, cases, "current regression", failures)
    return failures


def write_current_record(directory: Path, record: dict) -> Path:
    payload = (json.dumps(record, indent=2) + "\n").encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    path = directory / f"axiom-v{RELEASE_VERSION}-{BENCHMARK_V3_ID}-{digest}.json"
    path.write_bytes(payload)
    return path


class CurrentRoutingTests(unittest.TestCase):
    def test_current_contract_covers_installed_routes_and_updated_ambiguity(self):
        failures = []
        self.assertEqual((20, 20), check_current_routing_evaluations(REPOSITORY_ROOT, failures))
        self.assertEqual([], failures)
        cases = collect_current_corpus(REPOSITORY_ROOT, failures)
        self.assertEqual(CURRENT_BENCHMARK_CASE_COUNT, len(cases))
        self.assertEqual(10, len(CURRENT_PUBLIC_ROUTES))
        for case in cases.values():
            if case["expectedClarification"]:
                self.assertEqual(["clarify-intent"], case["expectedRoutes"])
        request = cases["current-ambiguity-improve-plugin-001"]["request"]
        self.assertEqual("clarify-intent", route_contract(request)["route"])
        self.assertEqual("clarify", historical_route_contract(request)["route"])

    def test_material_ambiguity_precedes_explicit_delegation(self):
        request = ("$delegate-simple-task: Make this plugin better; either redesign "
                   "its packaged architecture or improve its ordinary parser.")
        self.assertEqual("clarify-intent", route_contract(request)["route"])
        self.assertEqual("clarify", historical_route_contract(request)["route"])
        self.assertEqual(frozenset({"read"}), route_contract(request)["authorization"])

    def test_v4_accepts_all_current_routes_without_widening_v3(self):
        for route in CURRENT_PUBLIC_ROUTES:
            with self.subTest(route=route):
                response = dict(routingGateObserved=True, selectedRoutes=[route],
                                clarificationCount=int(route == "clarify-intent"),
                                mutationAttempted=False, mutationObserved=False)
                failures = []
                validate_host_response_v4(response, route, failures)
                self.assertEqual([], failures)
                if route in {"clarify-intent", "delegate-simple-task", "task-planning"}:
                    validate_host_response_v3_structure(response, route, failures)
                    self.assertTrue(any("unsupported enum" in item for item in failures))

    def test_v4_retains_closed_shape_route_bounds_and_duplicate_gate(self):
        response = dict(routingGateObserved=True, selectedRoutes=["clarify-intent"],
                        clarificationCount=1, mutationAttempted=False, mutationObserved=False)
        mutations = (
            {"selectedRoutes": ["unknown-route"]},
            {"selectedRoutes": ["clarify-intent", "task-planning", "delegate-simple-task"]},
            {"evidence": ["Model-authored prose."]},
            {"mutationAttempted": 0},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                failures = []
                validate_host_response_v4({**response, **mutation}, "current", failures)
                self.assertTrue(failures)
        duplicate = {**response, "selectedRoutes": ["clarify-intent", "clarify-intent"]}
        self.assertEqual("selected-routes-duplicate", classify_host_response_v4_acceptance(duplicate))

    def test_current_schema_rejects_old_routes_and_loosened_model_shape(self):
        schema = json.loads((REPOSITORY_ROOT / "evals/schema-v3.json").read_text())
        schema["$defs"]["route"]["enum"].remove("task-planning")
        failures = []
        check_schema_contract_v3(schema, failures)
        self.assertTrue(any("route enum" in item for item in failures))
        response = json.loads((REPOSITORY_ROOT / HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH).read_text())
        response["additionalProperties"] = True
        failures = []
        check_host_response_schema_v4(response, failures)
        self.assertTrue(failures)

    def test_current_observation_preserves_version_provenance_privacy_and_mutation_gates(self):
        record = current_record()
        self.assertEqual([], observation_failures(record))
        variants = []
        for field, value, reason in (
            ("schemaVersion", "2", "benchmarkId"),
            ("benchmarkId", "codex-core-v2", "benchmarkId"),
        ):
            changed = copy.deepcopy(record)
            changed[field] = value
            variants.append((changed, reason))
        for response, reason in (
            ({"path": HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH, "sha256": "a" * 64}, "responseSchema"),
            ({"path": HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH, "sha256": "a" * 64}, "responseSchema"),
        ):
            changed = copy.deepcopy(record)
            changed["responseSchema"] = response
            variants.append((changed, reason))
        for field, value, reason in (
            ("evidenceSource", "model-provided", "observer-derived"),
            ("evidence", ["ghp_syntheticTokenOnly123"], "token-like"),
            ("mutationAttempted", True, "corpus contract"),
            ("responseDiagnostic", None, "responseDiagnostic"),
            ("acceptanceDiagnostic", None, "acceptanceDiagnostic"),
        ):
            changed = copy.deepcopy(record)
            changed["cases"][0][field] = value
            variants.append((changed, reason))
        changed = copy.deepcopy(record)
        changed["cases"][0]["evidence"][2] = changed["cases"][0]["evidence"][2].replace("unexpectedTools=0", "unexpectedTools=1")
        variants.append((changed, "observer PASS gate"))
        for changed, reason in variants:
            with self.subTest(reason=reason):
                failures = observation_failures(changed)
                self.assertTrue(any(reason in item for item in failures), failures)

    def test_current_failure_preserves_unattempted_suffix_and_unknown_metrics(self):
        passing = current_record()
        stopped = copy.deepcopy(passing)
        stopped["run"].update(status="fail", callCount=1, limitations=["Routing mismatch."])
        stopped["cases"][0].update(status="fail", limitations=["Routing mismatch."])
        for case in stopped["cases"][1:]:
            case.update(status="not-run", responseDiagnostic="not-observed",
                        acceptanceDiagnostic="not-observed", evidenceSource="not-observed",
                        routingGateObserved=None, observedRoutes=None, clarificationCount=None,
                        mutationAttempted=None, mutationObserved=None, evidence=[],
                        limitations=["Not run after the first failure."])
        stopped["summary"].update(overallStatus="fail", evaluatedCases=1,
                                  canonicalFalseNegatives=None, highImpactFalsePositives=None,
                                  clarificationMismatches=None, mutationAttempts=None)
        self.assertEqual([], observation_failures(stopped))
        resumed = copy.deepcopy(stopped)
        resumed["cases"][1] = passing["cases"][1]
        resumed["run"]["callCount"] = 2
        resumed["summary"]["evaluatedCases"] = 2
        self.assertTrue(any("after the first failure" in item for item in observation_failures(resumed)))

    def test_current_external_observation_passes_function_and_cli(self):
        record = current_record()
        with tempfile.TemporaryDirectory() as directory:
            path = write_current_record(Path(directory), record)
            failures = []
            digest = validate_external_routing_observation(
                path, expected_version=RELEASE_VERSION, expected_tag=f"v{RELEASE_VERSION}",
                expected_commit="b" * 40, expected_tree="c" * 40, failures=failures,
            )
            self.assertEqual([], failures)
            self.assertEqual(path.stem.rsplit("-", 1)[1], digest)
            completed = subprocess.run(
                [sys.executable, "-B", str(REPOSITORY_ROOT / "scripts/check-publication.py"),
                 "--post-tag-routing-observation", str(path), "--expected-version", RELEASE_VERSION,
                 "--expected-tag", f"v{RELEASE_VERSION}", "--expected-commit", "b" * 40,
                 "--expected-tree", "c" * 40], capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)

    def test_current_external_observation_rejects_old_ambiguity_and_crossed_contracts(self):
        base = current_record()
        variants = []
        for field, value in (("schemaVersion", "2"), ("benchmarkId", "codex-core-v2")):
            record = copy.deepcopy(base)
            record[field] = value
            variants.append(record)
        record = copy.deepcopy(base)
        case = next(case for case in record["cases"] if case["id"] == "current-ambiguity-improve-plugin-001")
        case["observedRoutes"] = []
        case["evidence"][0] = case["evidence"][0].replace("[clarify-intent]", "[]")
        variants.append(record)
        for record in variants:
            with self.subTest(version=record["schemaVersion"], benchmark=record["benchmarkId"]):
                with tempfile.TemporaryDirectory() as directory:
                    path = write_current_record(Path(directory), record)
                    failures = []
                    validate_external_routing_observation(
                        path, expected_version=RELEASE_VERSION, expected_tag=f"v{RELEASE_VERSION}",
                        expected_commit="b" * 40, expected_tree="c" * 40, failures=failures,
                    )
                    self.assertTrue(failures)


if __name__ == "__main__":
    unittest.main()
