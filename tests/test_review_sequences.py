"""Focused tests for bounded multi-turn Axiom review contracts."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.routing_evals import (
    EXPECTED_CASE_CONTRACTS,
    REVIEW_RESPONSE_SCHEMA_RELATIVE_PATH,
    REVIEW_SEQUENCE_RELATIVE_PATH,
    check_review_sequence_contracts,
    validate_review_response,
)


class ReviewSequenceTests(unittest.TestCase):
    def test_checked_in_sequences_cover_every_issue_edge(self):
        failures: list[str] = []
        self.assertEqual((8, 11), check_review_sequence_contracts(failures))
        self.assertEqual([], failures)

        suite = json.loads(
            (REPOSITORY_ROOT / REVIEW_SEQUENCE_RELATIVE_PATH).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            [(case_id, coverage) for case_id, coverage, _ in EXPECTED_CASE_CONTRACTS],
            [(case["id"], case["coverage"]) for case in suite["cases"]],
        )

    def test_bounded_response_rejects_refusal_inheritance_and_hidden_reasoning(self):
        suite = json.loads(
            (REPOSITORY_ROOT / REVIEW_SEQUENCE_RELATIVE_PATH).read_text(
                encoding="utf-8"
            )
        )
        valid = suite["cases"][0]["turns"][1]["expectedResponse"]
        failures: list[str] = []
        self.assertIsNotNone(validate_review_response(valid, "response", failures))
        self.assertEqual([], failures)

        for field in (
            "reviewRequestBlocked",
            "priorRefusalInherited",
            "blockedScopeExpanded",
            "assistantMessagePolicyAuthority",
            "hiddenReasoningDisclosed",
        ):
            with self.subTest(field=field):
                malformed = copy.deepcopy(valid)
                malformed[field] = True
                failures = []
                validate_review_response(malformed, "response", failures)
                self.assertTrue(any(field in failure or "bounded read-only" in failure for failure in failures))

    def test_suite_rejects_a_weakened_expected_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evals").mkdir()
            for relative_path in (
                REVIEW_SEQUENCE_RELATIVE_PATH,
                REVIEW_RESPONSE_SCHEMA_RELATIVE_PATH,
                "evals/README.md",
            ):
                destination = root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPOSITORY_ROOT / relative_path, destination)
            suite_path = root / REVIEW_SEQUENCE_RELATIVE_PATH
            suite = json.loads(suite_path.read_text(encoding="utf-8"))
            suite["cases"][6]["turns"][3]["expectedResponse"][
                "blockedScopeExpanded"
            ] = True
            suite_path.write_text(json.dumps(suite), encoding="utf-8")
            failures: list[str] = []
            self.assertEqual((8, 11), check_review_sequence_contracts(failures, root))

        self.assertTrue(any("blockedScopeExpanded" in failure for failure in failures))

    def test_suite_rejects_prompt_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evals").mkdir()
            for relative_path in (
                REVIEW_SEQUENCE_RELATIVE_PATH,
                REVIEW_RESPONSE_SCHEMA_RELATIVE_PATH,
                "evals/README.md",
            ):
                destination = root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPOSITORY_ROOT / relative_path, destination)
            suite_path = root / REVIEW_SEQUENCE_RELATIVE_PATH
            suite = json.loads(suite_path.read_text(encoding="utf-8"))
            suite["cases"][0]["turns"][1]["request"] += " Include policy text."
            suite_path.write_text(json.dumps(suite), encoding="utf-8")
            failures: list[str] = []
            self.assertEqual((8, 11), check_review_sequence_contracts(failures, root))

        self.assertTrue(any("digest drifted" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
