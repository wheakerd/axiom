"""Focused tests for the in-session routing sequence suites."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.routing_evals import (
    CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH,
    IN_SESSION_FAMILY_IDS,
    IN_SESSION_MEASURED_TURN_MARKER,
    IN_SESSION_SHARED_KEYS,
    IN_SESSION_SUITE_RELATIVE_PATH,
    check_in_session_sequence_contracts,
)

_COPIED = (
    IN_SESSION_SUITE_RELATIVE_PATH,
    CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH,
    "evals/host-response-schema-v8.json",
    "evals/routing-v8/current.jsonl",
)


def _load(relative_path: str) -> dict:
    return json.loads((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))


class InSessionSequenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.mkdtemp(prefix="axiom-in-session-")
        self.root = Path(self.temporary)
        for relative_path in _COPIED:
            target = self.root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY_ROOT / relative_path, target)

    def tearDown(self) -> None:
        shutil.rmtree(self.temporary, ignore_errors=True)

    def _rewrite(self, relative_path: str, mutate) -> None:
        path = self.root / relative_path
        document = json.loads(path.read_text(encoding="utf-8"))
        mutate(document)
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def _failures(self) -> list[str]:
        failures: list[str] = []
        check_in_session_sequence_contracts(failures, self.root)
        # A rewritten suite always drifts from its frozen digest; the other
        # findings are what each negative case asserts.
        return [failure for failure in failures if "digest drifted from the frozen" not in failure]

    def test_checked_in_suites_validate_and_share_everything_but_the_host_profile(self):
        failures: list[str] = []
        self.assertEqual((6, 18), check_in_session_sequence_contracts(failures))
        self.assertEqual([], failures)
        codex = _load(IN_SESSION_SUITE_RELATIVE_PATH)
        claude = _load(CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH)
        for field in IN_SESSION_SHARED_KEYS:
            with self.subTest(field=field):
                self.assertEqual(codex[field], claude[field])
        self.assertNotEqual(codex["method"], claude["method"])
        self.assertEqual(tuple(family["id"] for family in codex["families"]), IN_SESSION_FAMILY_IDS)
        self.assertEqual([], codex["families"][0]["setupTurns"])
        compaction = codex["families"][-1]["setupTurns"]
        self.assertEqual({"kind": "compact"}, compaction[-1])

    def test_every_measured_case_is_a_current_corpus_case_and_no_setup_turn_is_measured(self):
        codex = _load(IN_SESSION_SUITE_RELATIVE_PATH)
        corpus = {
            json.loads(line)["id"]
            for line in (REPOSITORY_ROOT / "evals/routing-v8/current.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        self.assertTrue(set(codex["measuredCaseIds"]) <= corpus)
        for family in codex["families"]:
            for turn in family["setupTurns"]:
                if turn["kind"] != "compact":
                    self.assertFalse(turn["request"].startswith(IN_SESSION_MEASURED_TURN_MARKER))
                    self.assertNotIn("axiom", turn["request"].lower())

    def test_unknown_measured_case_is_rejected(self):
        def mutate(document):
            document["measuredCaseIds"].append("current-no-such-case-001")

        self._rewrite(IN_SESSION_SUITE_RELATIVE_PATH, mutate)
        self._rewrite(CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH, mutate)
        failures = self._failures()
        self.assertTrue(any("names no case in the current corpus" in failure for failure in failures), failures)

    def test_private_path_in_a_fixture_or_setup_turn_is_rejected(self):
        def mutate(document):
            document["workspaceFixture"]["files"]["notes.md"] = "see /home/someone/private.txt\n"
            document["families"][1]["setupTurns"][0]["request"] = "Read /tmp/scratch/notes and summarize it."

        self._rewrite(IN_SESSION_SUITE_RELATIVE_PATH, mutate)
        self._rewrite(CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH, mutate)
        failures = self._failures()
        # both suites carry the mutation, so each reports the fixture and the setup turn
        self.assertEqual(
            4, sum(1 for failure in failures if "absolute private path" in failure), failures
        )

    def test_compaction_must_be_host_native_and_last(self):
        def mutate(document):
            compaction = document["families"][-1]["setupTurns"]
            compaction.insert(0, compaction.pop())

        self._rewrite(IN_SESSION_SUITE_RELATIVE_PATH, mutate)
        self._rewrite(CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH, mutate)
        failures = self._failures()
        self.assertTrue(any("compaction must be the last setup turn" in failure for failure in failures), failures)

    def test_host_profiles_may_not_drift_and_shared_fields_must_match(self):
        def mutate_profile(document):
            document["safety"]["mutationAuthority"] = True

        def mutate_shared(document):
            document["families"][1]["condition"] = "a different condition"

        self._rewrite(IN_SESSION_SUITE_RELATIVE_PATH, mutate_profile)
        self._rewrite(CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH, mutate_shared)
        failures = self._failures()
        self.assertTrue(any("safety drifted from the host profile" in failure for failure in failures), failures)
        self.assertTrue(any("differ in shared field families" in failure for failure in failures), failures)

    def test_a_setup_turn_that_names_axiom_or_carries_the_marker_is_rejected(self):
        def mutate(document):
            document["families"][2]["setupTurns"][0]["request"] = IN_SESSION_MEASURED_TURN_MARKER + " read README.md"
            document["families"][2]["setupTurns"][1]["request"] = "Ask Axiom to summarize config.toml."

        self._rewrite(IN_SESSION_SUITE_RELATIVE_PATH, mutate)
        self._rewrite(CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH, mutate)
        failures = self._failures()
        self.assertTrue(any("must not carry the measured-turn marker" in failure for failure in failures), failures)
        self.assertTrue(any("must not name Axiom" in failure for failure in failures), failures)


if __name__ == "__main__":
    unittest.main()
