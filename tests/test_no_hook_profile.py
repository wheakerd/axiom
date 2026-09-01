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

    def test_contract_and_golden_set(self):
        failures: list[str] = []
        self.assertEqual((8, 13), check_no_hook_profile(failures))
        self.assertEqual([], failures)

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
