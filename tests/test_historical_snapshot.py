"""Exercise historical replay isolation with linked temporary-directory paths."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.historical_no_hook import (
    FIXTURE_ROOT,
    historical_snapshot,
    restore_frozen_inputs,
)


class HistoricalSnapshotTests(unittest.TestCase):
    def _source(self, directory: Path) -> Path:
        root = directory / "source"
        shutil.copytree(REPOSITORY_ROOT / FIXTURE_ROOT, root / FIXTURE_ROOT)
        ledger = root / "evidence/repository-policy-revisions-v1.json"
        ledger.parent.mkdir()
        ledger.write_text(json.dumps({"revisions": list(range(35))}), encoding="utf-8")
        retained = root / "skills/task-planning/SKILL.md"
        retained.parent.mkdir(parents=True)
        retained.write_text("Current planning capability\n", encoding="utf-8")
        return root

    def _symlink(self, link: Path, target: Path, *, directory: bool = False) -> None:
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symbolic links unavailable: {error}")

    def test_fresh_process_accepts_symlinked_tmpdir_without_changing_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            root = self._source(directory)
            real_tmp = directory / "real-tmp"
            real_tmp.mkdir()
            linked_tmp = directory / "linked-tmp"
            self._symlink(linked_tmp, real_tmp, directory=True)
            ledger = root / "evidence/repository-policy-revisions-v1.json"
            original_ledger = ledger.read_bytes()
            script = """
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from axiom_validation.historical_no_hook import historical_snapshot

root = Path(sys.argv[2])
temporary_root = Path(sys.argv[3])
assert Path(tempfile.gettempdir()) == temporary_root
with historical_snapshot(root) as snapshot:
    assert snapshot == snapshot.resolve()
    assert snapshot.parent.parent == temporary_root.resolve()
    assert json.loads((snapshot / '.codex-plugin/plugin.json').read_text())['version'] == '0.10.1'
    ledger = json.loads((snapshot / 'evidence/repository-policy-revisions-v1.json').read_text())
    assert ledger['revisions'] == list(range(30))
    assert not (snapshot / 'skills/task-planning').exists()
assert not snapshot.parent.exists()
"""
            environment = os.environ.copy()
            environment["TMPDIR"] = str(linked_tmp)
            result = subprocess.run(
                [sys.executable, "-I", "-B", "-c", script,
                 str(REPOSITORY_ROOT), str(root), str(linked_tmp)],
                cwd=REPOSITORY_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", result.stdout)
            self.assertEqual("", result.stderr)
            self.assertEqual(original_ledger, ledger.read_bytes())
            self.assertEqual(
                "Current planning capability\n",
                (root / "skills/task-planning/SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertFalse((root / ".codex-plugin").exists())
            self.assertEqual([], list(real_tmp.iterdir()))

    def test_source_fixture_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            root = self._source(directory)
            fixture = root / FIXTURE_ROOT / "plugin.json.txt"
            external = directory / "plugin.json.txt"
            fixture.rename(external)
            self._symlink(fixture, external)
            original = external.read_bytes()
            with self.assertRaisesRegex(ValueError, "historical fixture must be a regular file"):
                with historical_snapshot(root):
                    self.fail("a linked historical fixture must not be restored")
            self.assertEqual(original, external.read_bytes())

    def test_copied_target_directory_symlink_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            root = self._source(directory)
            external = directory / "external-plugin"
            external.mkdir()
            protected = external / "plugin.json"
            protected.write_text("Retain external content\n", encoding="utf-8")
            self._symlink(root / ".codex-plugin", external, directory=True)
            with self.assertRaisesRegex(ValueError, "historical replay path contains a symbolic link"):
                with historical_snapshot(root):
                    self.fail("a copied directory link must not be followed")
            self.assertEqual("Retain external content\n", protected.read_text(encoding="utf-8"))

    def test_source_alias_is_rejected_before_restoring_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            root = self._source(directory)
            alias = directory / "source-alias"
            self._symlink(alias, root, directory=True)
            ledger = root / "evidence/repository-policy-revisions-v1.json"
            original = ledger.read_bytes()
            with self.assertRaisesRegex(ValueError, "separate disposable destination"):
                restore_frozen_inputs(root, alias)
            self.assertEqual(original, ledger.read_bytes())
            self.assertTrue((root / "skills/task-planning/SKILL.md").is_file())
            self.assertFalse((root / ".codex-plugin").exists())


if __name__ == "__main__":
    unittest.main()
