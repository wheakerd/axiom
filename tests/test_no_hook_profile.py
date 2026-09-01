"""Focused tests for the Hook-independent profile contract."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from axiom_validation.no_hook_profile import check_no_hook_profile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class NoHookProfileTests(unittest.TestCase):
    def _fixture_root(self, directory: str) -> Path:
        root = Path(directory)
        (root / "evals").mkdir()
        shutil.copytree(
            REPOSITORY_ROOT / "evals" / "no-hook",
            root / "evals" / "no-hook",
        )
        shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills")
        return root

    @staticmethod
    def _write_json(path: Path, document: dict) -> None:
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _read_cases(path: Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    @staticmethod
    def _write_cases(path: Path, cases: list[dict]) -> None:
        lines = [json.dumps(case, separators=(",", ":")) for case in cases]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_contract_and_golden_set(self):
        failures: list[str] = []
        self.assertEqual((8, 14), check_no_hook_profile(failures))
        self.assertEqual([], failures)

    def test_contract_version_is_required_positive_and_bounded(self):
        mutations = (
            ("missing", lambda case: case.pop("contractVersion")),
            ("zero", lambda case: case.__setitem__("contractVersion", 0)),
            ("boolean", lambda case: case.__setitem__("contractVersion", True)),
            ("too-large", lambda case: case.__setitem__("contractVersion", 1_000_001)),
        )
        for name, mutate in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self._fixture_root(directory)
                path = root / "evals" / "no-hook" / "golden-set-v1.jsonl"
                cases = self._read_cases(path)
                mutate(cases[0])
                self._write_cases(path, cases)
                failures: list[str] = []
                check_no_hook_profile(failures, root)
                self.assertTrue(any("contractVersion" in failure for failure in failures))

    def test_artifact_digest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            path = root / "evals" / "no-hook" / "benchmark-v1.json"
            benchmark = json.loads(path.read_text(encoding="utf-8"))
            benchmark["profileContract"]["sha256"] = "0" * 64
            self._write_json(path, benchmark)
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(
                any("profileContract sha256" in failure for failure in failures)
            )

    def test_silent_case_file_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            path = root / "evals" / "no-hook" / "golden-set-v1.jsonl"
            cases = self._read_cases(path)
            cases[-1]["request"] += " Changed without a contractVersion update."
            self._write_cases(path, cases)
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(any("caseFile sha256" in failure for failure in failures))

    def test_using_axiom_front_door_is_explicit_and_not_session_start(self):
        mutations = (
            (
                "missing-front-door-observation",
                "no-hook-positive-explicit-using-axiom-001",
                "expectedUsingAxiomFrontDoorObserved",
                False,
            ),
            (
                "direct-leaf-is-not-front-door",
                "no-hook-positive-direct-agents-architect-001",
                "expectedUsingAxiomFrontDoorObserved",
                True,
            ),
            (
                "session-start-is-not-front-door",
                "no-hook-positive-explicit-using-axiom-001",
                "sessionStartDelivered",
                True,
            ),
        )
        for name, case_id, field, value in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self._fixture_root(directory)
                path = root / "evals" / "no-hook" / "golden-set-v1.jsonl"
                cases = self._read_cases(path)
                case = next(item for item in cases if item["id"] == case_id)
                case[field] = value
                self._write_cases(path, cases)
                failures: list[str] = []
                check_no_hook_profile(failures, root)
                self.assertTrue(
                    any(
                        "front-door" in failure or "sessionStartDelivered" in failure
                        for failure in failures
                    )
                )

    def test_host_capability_is_scoped_and_never_preobserved(self):
        mutations = (
            ("chatgpt-git", "traceable-git-submit", "chatgpt", "capability", "contract-target"),
            ("codex-observed", "using-axiom", "codex", "evidence", "host-observed"),
        )
        for name, skill_id, host, field, value in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self._fixture_root(directory)
                path = root / "evals" / "no-hook" / "profile-v1.json"
                profile = json.loads(path.read_text(encoding="utf-8"))
                skill = next(item for item in profile["skills"] if item["id"] == skill_id)
                capability = next(
                    item for item in skill["hostCapabilities"] if item["host"] == host
                )
                capability[field] = value
                self._write_json(path, profile)
                failures: list[str] = []
                check_no_hook_profile(failures, root)
                self.assertTrue(
                    any("capability" in failure or "evidence" in failure for failure in failures)
                )

    def test_negative_kind_semantics_are_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            path = root / "evals" / "no-hook" / "golden-set-v1.jsonl"
            cases = self._read_cases(path)
            case = next(
                item
                for item in cases
                if item["id"] == "no-hook-negative-plan-only-system-change-001"
            )
            case["negativeKind"] = "safety-control"
            self._write_cases(path, cases)
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(
                any("safety-control" in failure or "negative taxonomy" in failure for failure in failures)
            )

    def test_profile_identifier_remains_axiom_owned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            path = root / "evals" / "no-hook" / "profile-v1.json"
            profile = json.loads(path.read_text(encoding="utf-8"))
            profile["identifier"]["owner"] = "openai"
            self._write_json(path, profile)
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(any("identifier" in failure for failure in failures))

    def test_session_start_cannot_be_reintroduced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            path = root / "evals" / "no-hook" / "profile-v1.json"
            profile = json.loads(path.read_text(encoding="utf-8"))
            profile["discovery"]["sessionStartRequired"] = True
            self._write_json(path, profile)
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(any("discovery" in failure for failure in failures))

    def test_full_profile_evidence_cannot_cross_profile_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            path = root / "evals" / "no-hook" / "benchmark-v1.json"
            benchmark = json.loads(path.read_text(encoding="utf-8"))
            benchmark["evidence"]["fullProfileEvidenceReusable"] = True
            self._write_json(path, benchmark)
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(any("evidence" in failure for failure in failures))

    def test_case_cannot_grant_mutation_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            path = root / "evals" / "no-hook" / "golden-set-v1.jsonl"
            lines = path.read_text(encoding="utf-8").splitlines()
            case = json.loads(lines[0])
            case["mutationAuthorized"] = True
            lines[0] = json.dumps(case, separators=(",", ":"))
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(
                any("mutationAuthorized must remain false" in failure for failure in failures)
            )

    def test_profile_directory_cannot_hold_a_skill_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            copied = root / "evals" / "no-hook" / "copied-skill"
            copied.mkdir()
            (copied / "SKILL.md").write_text("# copied\n", encoding="utf-8")
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(
                any("second editable Skill source" in failure for failure in failures)
            )

    def test_golden_set_matrix_is_fixed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._fixture_root(directory)
            path = root / "evals" / "no-hook" / "golden-set-v1.jsonl"
            lines = path.read_text(encoding="utf-8").splitlines()
            path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            failures: list[str] = []
            check_no_hook_profile(failures, root)
            self.assertTrue(any("Golden Set matrix" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
