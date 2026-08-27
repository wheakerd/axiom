"""Focused routing-context measurement and evidence tests."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.context_budget import (
    BASELINE_METRICS,
    BASELINE_SHA256,
    CONTEXT_BUDGET_RECORD,
    ROUTING_GATE_PATH,
    check_context_budget,
    measure_markdown,
    previous_context_budget_candidate,
    routing_corpus_metrics,
    threshold_assessment,
    validate_host_observation,
    validate_reduction_experiment,
)


class ContextBudgetTests(unittest.TestCase):
    def test_current_versioned_record_and_gate(self):
        failures = []
        self.assertEqual(7, check_context_budget(failures))
        self.assertEqual([], failures)
        current_record = json.loads(CONTEXT_BUDGET_RECORD.read_text(encoding="utf-8"))
        current_metrics = measure_markdown(ROUTING_GATE_PATH)
        self.assertEqual(current_record["candidate"]["metrics"], current_metrics)
        self.assertEqual(
            current_record["comparison"]["utf8ByteDelta"],
            current_metrics["utf8Bytes"] - BASELINE_METRICS["utf8Bytes"],
        )
        self.assertEqual(
            current_record["candidate"]["sha256"],
            hashlib.sha256(ROUTING_GATE_PATH.read_bytes()).hexdigest(),
        )
        self.assertNotEqual(BASELINE_SHA256, current_record["candidate"]["sha256"])
        self.assertEqual("not-run", current_record["measurementBoundary"]["exactHostUsage"])
        self.assertFalse(current_record["measurementBoundary"]["networkOrTelemetryUsed"])
        codex_metric = current_record["hostMetrics"][0]
        self.assertEqual("not-run", codex_metric["status"])
        self.assertFalse(codex_metric["exactUsageExposed"])
        self.assertIsNone(codex_metric["inputTokens"])
        self.assertIsNone(codex_metric["cachedInputTokens"])
        self.assertIsNone(codex_metric["wallClockMilliseconds"])
        self.assertIsNone(codex_metric["credits"])
        comparison = current_record["comparison"]
        self.assertTrue(comparison["absoluteThresholdReached"])
        self.assertTrue(comparison["relativeThresholdReached"])
        self.assertTrue(comparison["meaningfulIncrease"])
        self.assertEqual("reviewed", comparison["reviewStatus"])
        self.assertIsInstance(comparison["justification"], str)
        self.assertTrue(
            all(
                scenario["hostObservations"][0]["status"] == "not-run"
                for scenario in current_record["scenarios"]
            )
        )

    def test_alternate_utf8_input_keeps_exact_counts_and_estimate_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alternate.md"
            content = "é alpha\nreferences/one.md references/one.md\n"
            path.write_text(content, encoding="utf-8")
            metrics = measure_markdown(path)
        self.assertEqual(len(content.encode("utf-8")), metrics["utf8Bytes"])
        self.assertEqual(4, metrics["whitespaceDelimitedWords"])
        self.assertEqual(2, metrics["logicalLines"])
        self.assertEqual(["references/one.md"], metrics["directReferences"])
        self.assertEqual((len(content.encode("utf-8")) + 3) // 4, metrics["estimatedTokens"]["value"])
        self.assertEqual("estimate", metrics["estimatedTokens"]["classification"])

    def test_growth_threshold_is_review_only_and_cumulative(self):
        below = threshold_assessment(5899, 5900)
        self.assertFalse(below["meaningfulIncrease"])
        self.assertEqual("below-threshold", below["reviewStatus"])

        absolute = threshold_assessment(5899, 5899 + 256)
        self.assertTrue(absolute["absoluteThresholdReached"])
        self.assertTrue(absolute["meaningfulIncrease"])
        self.assertEqual("reviewed", absolute["reviewStatus"])

        relative = threshold_assessment(100, 105)
        self.assertTrue(relative["relativeThresholdReached"])
        self.assertTrue(relative["meaningfulIncrease"])

    def test_duplicate_injection_is_derived_from_observed_events(self):
        observation = {
            "host": "codex",
            "status": "fail",
            "observedInjectionCount": 2,
            "duplicateInjectionDetected": True,
            "injections": [
                {
                    "sequence": 1,
                    "requestOrdinal": 0,
                    "lifecycleSource": "startup",
                    "contentSha256": BASELINE_SHA256,
                },
                {
                    "sequence": 2,
                    "requestOrdinal": 2,
                    "lifecycleSource": "startup",
                    "contentSha256": BASELINE_SHA256,
                },
            ],
            "reason": "A second injection appeared during an unchanged session.",
        }
        failures = []
        self.assertTrue(
            validate_host_observation(
                observation,
                label="observation",
                lifecycle_source="startup",
                request_count=3,
                expected_injection_count=1,
                candidate_sha256=BASELINE_SHA256,
                failures=failures,
            )
        )
        self.assertEqual([], failures)

        malformed = copy.deepcopy(observation)
        malformed["duplicateInjectionDetected"] = False
        failures = []
        validate_host_observation(
            malformed,
            label="observation",
            lifecycle_source="startup",
            request_count=3,
            expected_injection_count=1,
            candidate_sha256=BASELINE_SHA256,
            failures=failures,
        )
        self.assertTrue(any("derived count boundary" in failure for failure in failures))

    def test_reduction_requires_equivalent_routed_and_no_route_passes(self):
        corpus, _, corpus_failures = routing_corpus_metrics()
        self.assertEqual([], corpus_failures)
        before_sha = "a" * 64
        after_sha = "b" * 64

        missing_failures = []
        validate_reduction_experiment(
            None,
            before_sha,
            after_sha,
            100,
            90,
            corpus,
            missing_failures,
        )
        self.assertTrue(any("before/after" in failure for failure in missing_failures))

        def result(surface_sha256):
            return {
                "classification": "static-contract-validation",
                "surfaceSha256": surface_sha256,
                "workloadSha256": corpus["sha256"],
                "caseCount": corpus["caseCount"],
                "noRouteCaseCount": corpus["noRouteCaseCount"],
                "routingStatus": "pass",
                "noRouteStatus": "pass",
            }

        accepted_failures = []
        validate_reduction_experiment(
            {
                "equivalentWorkload": True,
                "before": result(before_sha),
                "after": result(after_sha),
            },
            before_sha,
            after_sha,
            100,
            90,
            corpus,
            accepted_failures,
        )
        self.assertEqual([], accepted_failures)

        wrong_predecessor = {
            "equivalentWorkload": True,
            "before": result(BASELINE_SHA256),
            "after": result(after_sha),
        }
        predecessor_failures = []
        validate_reduction_experiment(
            wrong_predecessor,
            before_sha,
            after_sha,
            100,
            90,
            corpus,
            predecessor_failures,
        )
        self.assertTrue(
            any(
                "reductionExperiment.before.surfaceSha256" in failure
                for failure in predecessor_failures
            )
        )

    def test_reduction_predecessor_is_nearest_earlier_release_candidate(self):
        def metrics(byte_count):
            result = copy.deepcopy(BASELINE_METRICS)
            result["utf8Bytes"] = byte_count
            result["estimatedTokens"]["value"] = (byte_count + 3) // 4
            return result

        def write_record(root, version, sha256, byte_count):
            document = {
                "targetRelease": {
                    "version": version,
                    "commit": None,
                    "binding": "pending-immutable-release",
                },
                "candidate": {
                    "sha256": sha256,
                    "metrics": metrics(byte_count),
                },
            }
            (root / f"v{version}.json").write_text(
                json.dumps(document), encoding="utf-8"
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_record(root, "0.8.9", "9" * 64, 7700)
            write_record(root, "0.8.10", "a" * 64, 7739)
            write_record(root, "0.8.11", "b" * 64, 6409)
            write_record(root, "0.9.0", "c" * 64, 6500)
            failures = []
            predecessor = previous_context_budget_candidate(
                "0.8.11", failures, results_root=root
            )

        self.assertEqual([], failures)
        self.assertIsNotNone(predecessor)
        predecessor_sha256, predecessor_metrics = predecessor
        self.assertEqual("a" * 64, predecessor_sha256)
        self.assertEqual(7739, predecessor_metrics["utf8Bytes"])

    def test_measurement_cli_is_repository_relative_and_read_only(self):
        script = REPOSITORY_ROOT / "scripts" / "measure-routing-context.py"
        completed = subprocess.run(
            [sys.executable, str(script), "README.md"],
            cwd="/tmp",
            check=True,
            capture_output=True,
            text=True,
        )
        document = json.loads(completed.stdout)
        self.assertEqual("README.md", document["path"])
        self.assertEqual("not-measured", document["measurementBoundary"]["exactHostUsage"])
        self.assertGreater(document["metrics"]["utf8Bytes"], 0)

        checked = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd="/tmp",
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("historical host usage is preserved", checked.stdout)
        self.assertIn("without claiming current host or lifecycle evidence", checked.stdout)


if __name__ == "__main__":
    unittest.main()
