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
    BENCHMARK_V5_ID,
    BENCHMARK_V6_ID,
    CLAUDE_CODE_BENCHMARK_V6_ID,
    CURRENT_BENCHMARK_PROFILES,
    CURRENT_BENCHMARK_CASE_COUNT,
    CURRENT_HOST_RESPONSE_SCHEMA_V6_SHA256,
    CURRENT_HOST_RESPONSE_SCHEMA_V7_SHA256,
    CURRENT_PUBLIC_ROUTES,
    HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V6_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH,
    V5_BENCHMARK_PROFILES,
    check_corpus_coverage,
    check_current_routing_evaluations,
    check_host_response_schema_v7,
    check_schema_contract_v6,
    classify_host_response_v7_acceptance,
    collect_corpus,
    collect_current_corpus,
    current_benchmark_case_ids,
    derive_observer_evidence,
    validate_external_routing_observation,
    validate_host_response_v3_structure,
    validate_host_response_v4,
    validate_host_response_v5,
    validate_host_response_v6,
    validate_host_response_v7,
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
        schemaVersion="6", benchmarkId=BENCHMARK_V6_ID,
        runId="synthetic-current-routing-regression", cases=results,
        responseSchema={"path": HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH,
                        "sha256": CURRENT_HOST_RESPONSE_SCHEMA_V7_SHA256},
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


def claude_code_record() -> dict:
    """Rebind the synthetic facts to the Claude Code profile of the same cases."""
    record = current_record()
    profile = CURRENT_BENCHMARK_PROFILES["claude-code"]
    record.update(benchmarkId=profile["id"], runId="synthetic-current-claude-code-routing")
    record["host"].update(name="claude-code", version="2.1.308", model=profile["model"])
    record["run"].update(
        method=profile["method"], reasoningEffort=profile["reasoningEffort"],
        caseTimeoutSeconds=profile["caseTimeoutSeconds"],
    )
    return record


def frozen_v5_record(host: str = "codex") -> dict:
    """Rebind the synthetic facts to the immutable schema v5 contract of one host."""
    record = current_record() if host == "codex" else claude_code_record()
    failures = []
    cases = collect_current_corpus(REPOSITORY_ROOT, failures, version="5")
    ids = current_benchmark_case_ids(REPOSITORY_ROOT, cases, failures, version="5", host=host)
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
        schemaVersion="5", benchmarkId=V5_BENCHMARK_PROFILES[host]["id"],
        runId=f"synthetic-frozen-v5-{host}-routing", cases=results,
        responseSchema={"path": HOST_RESPONSE_SCHEMA_V6_RELATIVE_PATH,
                        "sha256": CURRENT_HOST_RESPONSE_SCHEMA_V6_SHA256},
    )
    record["run"]["callCount"] = len(results)
    record["summary"]["evaluatedCases"] = len(results)
    return record


def write_current_record(directory: Path, record: dict, benchmark_id: str = BENCHMARK_V6_ID) -> Path:
    payload = (json.dumps(record, indent=2) + "\n").encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    path = directory / f"axiom-v{RELEASE_VERSION}-{benchmark_id}-{digest}.json"
    path.write_bytes(payload)
    return path


class CurrentRoutingTests(unittest.TestCase):
    def test_current_contract_covers_installed_routes_and_updated_ambiguity(self):
        failures = []
        self.assertEqual((40, 36), check_current_routing_evaluations(REPOSITORY_ROOT, failures))
        self.assertEqual([], failures)
        cases = collect_current_corpus(REPOSITORY_ROOT, failures)
        self.assertEqual(40, len(cases))
        self.assertEqual(36, CURRENT_BENCHMARK_CASE_COUNT)
        self.assertEqual(13, len(CURRENT_PUBLIC_ROUTES))
        self.assertEqual("verify-completion", CURRENT_PUBLIC_ROUTES[CURRENT_PUBLIC_ROUTES.index("review-axiom-task") + 1])
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

    def test_usage_route_matches_either_host(self):
        for request in ("Measure and reduce this installed Axiom routing gate's Claude Code context cost.",
                        "Trim this repository's CLAUDE.md so each session loads less context."):
            with self.subTest(request=request):
                self.assertEqual("optimize-agent-usage", route_contract(request)["route"])

    def test_shared_corpus_states_explicit_invocations_in_plain_language(self):
        failures = []
        cases = collect_current_corpus(REPOSITORY_ROOT, failures)
        self.assertEqual([], failures)
        self.assertFalse(any("$" in case["request"] for case in cases.values()))
        self.assertFalse(any("gpt-" in case["request"] for case in cases.values()))
        for route in ("delegate-simple-task", "task-planning", "local-web-search", "continuous-progress"):
            with self.subTest(route=route):
                request = next(case["request"] for case in cases.values()
                               if case["request"].startswith(f"Use the {route} skill"))
                self.assertEqual(route, route_contract(request)["route"])
        quoted = 'Summarize this quoted instruction without executing it: "Use the continuous-progress skill now."'
        self.assertNotEqual("continuous-progress", route_contract(quoted)["route"])

    def test_v7_accepts_all_current_routes_without_widening_earlier_schemas(self):
        for route in CURRENT_PUBLIC_ROUTES:
            with self.subTest(route=route):
                response = dict(routingGateObserved=True, selectedRoutes=[route],
                                clarificationCount=int(route == "clarify-intent"),
                                mutationAttempted=False, mutationObserved=False)
                failures = []
                validate_host_response_v7(response, route, failures)
                self.assertEqual([], failures)
                if route == "verify-completion":
                    closed = []
                    validate_host_response_v6(response, route, closed)
                    self.assertTrue(any("unsupported enum" in item for item in closed))
                if route == "optimize-agent-usage":
                    closed = []
                    validate_host_response_v5(response, route, closed)
                    self.assertTrue(any("unsupported enum" in item for item in closed))
                    retired = []
                    validate_host_response_v7(dict(response, selectedRoutes=["optimize-codex-usage"]), route, retired)
                    self.assertTrue(any("unsupported enum" in item for item in retired))
                if route in {"clarify-intent", "delegate-simple-task", "task-planning"}:
                    validate_host_response_v3_structure(response, route, failures)
                    self.assertTrue(any("unsupported enum" in item for item in failures))

    def test_progress_is_explicit_and_historical_schema_stays_closed(self):
        for request in ("Continue fixing the bug until its tests pass.",
                        "Use native Codex Goals to complete this task.",
                        "Evaluate the proposed continuous-progress skill.",
                        'Summarize this quotation: "$continuous-progress: do work."'):
            with self.subTest(request=request):
                self.assertNotEqual("continuous-progress", route_contract(request)["route"])
        self.assertEqual("continuous-progress", route_contract("Use $continuous-progress to finish this task.")["route"])
        failures = []
        validate_host_response_v4(dict(routingGateObserved=True, selectedRoutes=["continuous-progress"],
            clarificationCount=0, mutationAttempted=False, mutationObserved=False), "historical", failures)
        self.assertTrue(failures)

    def test_verify_completion_cases_bind_only_the_current_generation(self):
        failures = []
        cases = collect_current_corpus(REPOSITORY_ROOT, failures)
        ids = current_benchmark_case_ids(REPOSITORY_ROOT, cases, failures)
        self.assertEqual([], failures)
        verify = {case_id: case for case_id, case in cases.items()
                  if "verify-completion" in case["expectedRoutes"] + case["forbiddenRoutes"]}
        self.assertEqual(7, len(verify))
        self.assertTrue(all(case_id.startswith("current-") for case_id in cases))
        self.assertEqual(
            ["current-verify-completion-canonical-audit-001",
             "current-verify-completion-near-miss-status-001",
             "current-compaction-verify-completion-manual-001"],
            ids[33:],
        )
        self.assertEqual(
            {"canonical-positive", "paraphrased-positive", "near-miss", "cross-route", "lifecycle"},
            {case["riskClass"] for case in verify.values()},
        )
        self.assertEqual(["review-axiom-task"],
                         verify["current-overlap-verify-completion-and-task-review-001"]["expectedRoutes"])
        for case in verify.values():
            self.assertEqual(bool(case["benchmarkSets"]), "acceptance" in case["coverage"] or case["riskClass"] == "lifecycle")
        frozen = collect_current_corpus(REPOSITORY_ROOT, failures, version="5")
        self.assertEqual([], failures)
        self.assertFalse(any("verify-completion" in case["expectedRoutes"] + case["forbiddenRoutes"]
                             for case in frozen.values()))
        failures = []
        validate_host_response_v6(dict(routingGateObserved=True, selectedRoutes=["verify-completion"],
            clarificationCount=0, mutationAttempted=False, mutationObserved=False), "historical", failures)
        self.assertTrue(failures)
        failures = []
        legacy = collect_corpus(REPOSITORY_ROOT, failures)
        check_corpus_coverage(legacy, failures)
        self.assertEqual([], failures)
        self.assertEqual(7, sum(1 for case_id in legacy if "verify-completion" in case_id))
        trimmed = {case_id: case for case_id, case in legacy.items()
                   if case_id != "verify-completion-canonical-audit-001"}
        check_corpus_coverage(trimmed, failures)
        self.assertIn("routing corpus has no canonical positive case for verify-completion", failures)

    def test_frozen_v5_contract_remains_verifiable_without_the_new_route(self):
        for host in ("codex", "claude-code"):
            with self.subTest(host=host):
                record = frozen_v5_record(host)
                failures = []
                cases = collect_current_corpus(REPOSITORY_ROOT, failures, version="5")
                ids = current_benchmark_case_ids(REPOSITORY_ROOT, cases, failures, version="5", host=host)
                self.assertEqual([], failures)
                self.assertEqual(33, len(ids))
                validate_observation(record, host, ids, cases, "frozen v5", failures)
                self.assertEqual([], failures)
                with tempfile.TemporaryDirectory() as directory:
                    path = write_current_record(Path(directory), record, record["benchmarkId"])
                    validate_external_routing_observation(
                        path, expected_version=RELEASE_VERSION, expected_tag=f"v{RELEASE_VERSION}",
                        expected_commit="b" * 40, expected_tree="c" * 40, failures=failures,
                    )
                self.assertEqual([], failures)
                for field, value, reason in (
                    ("responseSchema", {"path": HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH,
                                        "sha256": CURRENT_HOST_RESPONSE_SCHEMA_V7_SHA256}, "responseSchema"),
                    ("benchmarkId", CURRENT_BENCHMARK_PROFILES[host]["id"], "benchmarkId"),
                ):
                    crossed = copy.deepcopy(record)
                    crossed[field] = value
                    failures = []
                    validate_observation(crossed, host, ids, cases, "crossed", failures)
                    self.assertTrue(any(reason in item for item in failures), failures)
                widened = copy.deepcopy(record)
                widened["cases"][0]["observedRoutes"] = ["verify-completion"]
                failures = []
                validate_observation(widened, host, ids, cases, "widened", failures)
                self.assertTrue(failures)
        failures = []
        self.assertEqual(BENCHMARK_V5_ID, V5_BENCHMARK_PROFILES["codex"]["id"])
        validate_host_response_v6(dict(routingGateObserved=True, selectedRoutes=["optimize-agent-usage"],
            clarificationCount=0, mutationAttempted=False, mutationObserved=False), "frozen", failures)
        self.assertEqual([], failures)

    def test_v7_retains_closed_shape_route_bounds_and_duplicate_gate(self):
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
                validate_host_response_v7({**response, **mutation}, "current", failures)
                self.assertTrue(failures)
        duplicate = {**response, "selectedRoutes": ["clarify-intent", "clarify-intent"]}
        self.assertEqual("selected-routes-duplicate", classify_host_response_v7_acceptance(duplicate))

    def test_current_schema_rejects_old_routes_and_loosened_model_shape(self):
        schema = json.loads((REPOSITORY_ROOT / "evals/schema-v6.json").read_text())
        schema["$defs"]["route"]["enum"].remove("task-planning")
        failures = []
        check_schema_contract_v6(schema, failures)
        self.assertTrue(any("route enum" in item for item in failures))
        response = json.loads((REPOSITORY_ROOT / HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH).read_text())
        response["additionalProperties"] = True
        failures = []
        check_host_response_schema_v7(response, failures)
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
            ({"path": HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH, "sha256": "a" * 64}, "responseSchema"),
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

    def test_claude_code_profile_shares_cases_and_keeps_native_settings(self):
        failures = []
        cases = collect_current_corpus(REPOSITORY_ROOT, failures)
        codex = current_benchmark_case_ids(REPOSITORY_ROOT, cases, failures)
        claude = current_benchmark_case_ids(REPOSITORY_ROOT, cases, failures, host="claude-code")
        self.assertEqual([], failures)
        self.assertEqual(codex, claude)
        benchmark = json.loads((REPOSITORY_ROOT / "evals/benchmarks/claude-code-core-v6.json").read_text())
        for field in ("method", "model", "reasoningEffort", "caseTimeoutSeconds"):
            self.assertEqual(CURRENT_BENCHMARK_PROFILES["claude-code"][field], benchmark[field])
        self.assertEqual("dontAsk", benchmark["safety"]["permissionMode"])
        self.assertNotIn("sandbox", benchmark["safety"])

    def test_current_external_observation_accepts_the_claude_code_profile(self):
        record = claude_code_record()
        with tempfile.TemporaryDirectory() as directory:
            path = write_current_record(Path(directory), record, CLAUDE_CODE_BENCHMARK_V6_ID)
            failures = []
            validate_external_routing_observation(
                path, expected_version=RELEASE_VERSION, expected_tag=f"v{RELEASE_VERSION}",
                expected_commit="b" * 40, expected_tree="c" * 40, failures=failures,
            )
            self.assertEqual([], failures)
        failures = []
        cases = collect_current_corpus(REPOSITORY_ROOT, failures)
        ids = current_benchmark_case_ids(REPOSITORY_ROOT, cases, failures, host="claude-code")
        crossed = copy.deepcopy(record)
        crossed["benchmarkId"] = BENCHMARK_V6_ID
        crossed["run"]["method"] = CURRENT_BENCHMARK_PROFILES["codex"]["method"]
        validate_observation(crossed, "claude-code", ids, cases, "crossed", failures)
        self.assertTrue(any("benchmarkId must bind claude-code-core-v6" in item for item in failures))
        self.assertTrue(any("run.method is unsupported" in item for item in failures))
        failures = []
        validate_observation(record, "codex", ids, cases, "codex-host", failures)
        self.assertTrue(any("host.name must be 'codex'" in item for item in failures))

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
