"""Deterministic build tests for the hook-less Codex directory listing variant."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT

SCRIPT = REPOSITORY_ROOT / "scripts" / "build-listing-variant.py"
GIT = ("git", "-c", "user.name=variant-test", "-c", "user.email=variant-test@invalid", "-c", "commit.gpgsign=false")


def _git(repository: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([*GIT, "-C", str(repository), *args], capture_output=True, text=True, check=True)


def _build(repository: Path, tree_ish: str, output: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--repository", str(repository), "--tree-ish", tree_ish, "--output", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )


class ListingVariantBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("git") is None:
            raise unittest.SkipTest("git is unavailable")
        cls.temporary = tempfile.TemporaryDirectory()
        cls.repository = Path(cls.temporary.name) / "source"
        cls.repository.mkdir()
        shutil.copytree(REPOSITORY_ROOT / "plugin", cls.repository / "plugin")
        _git(cls.repository, "init", "-q", "-b", "main")
        _git(cls.repository, "add", "-A")
        _git(cls.repository, "commit", "-q", "-m", "plugin tree under test")
        cls.commit = _git(cls.repository, "rev-parse", "HEAD").stdout.strip()
        cls.plugin_tree = _git(cls.repository, "rev-parse", "HEAD:plugin").stdout.strip()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def _manifest_and_archive(self, output: Path) -> tuple[dict, Path]:
        manifests = sorted(output.glob("axiom-*-codex-directory-variant.json"))
        archives = sorted(output.glob("axiom-*-codex-directory-variant.zip"))
        self.assertEqual(1, len(manifests))
        self.assertEqual(1, len(archives))
        return json.loads(manifests[0].read_text(encoding="utf-8")), archives[0]

    def test_two_clean_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for output in (first, second):
                result = _build(self.repository, "HEAD", Path(output))
                self.assertEqual(0, result.returncode, result.stderr)
            first_manifest, first_archive = self._manifest_and_archive(Path(first))
            second_manifest, second_archive = self._manifest_and_archive(Path(second))
            self.assertEqual(first_archive.read_bytes(), second_archive.read_bytes())
            self.assertEqual(first_manifest, second_manifest)
            self.assertEqual(self.commit, first_manifest["source"]["commit"])
            self.assertEqual(self.plugin_tree, first_manifest["source"]["pluginTree"])

    def test_variant_removes_hooks_and_keeps_every_other_byte(self) -> None:
        with tempfile.TemporaryDirectory() as output:
            result = _build(self.repository, "HEAD", Path(output))
            self.assertEqual(0, result.returncode, result.stderr)
            manifest, archive_path = self._manifest_and_archive(Path(output))
            source_root = self.repository / "plugin"
            source_files = {
                path.relative_to(source_root).as_posix()
                for path in source_root.rglob("*")
                if path.is_file()
            }
            expected_members = sorted(
                relative for relative in source_files
                if not relative.startswith(("hooks/", ".claude-plugin/"))
            )
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                self.assertEqual(expected_members, names)
                self.assertNotIn("hooks/codex-hooks.json", names)
                self.assertNotIn(".claude-plugin/plugin.json", names)
                self.assertIn("skills/using-axiom/SKILL.md", names)
                self.assertIn("assets/axiom-mark.svg", names)
                self.assertIn("LICENSE", names)
                for info in archive.infolist():
                    self.assertEqual((1980, 1, 1, 0, 0, 0), info.date_time)
                    self.assertEqual(zipfile.ZIP_STORED, info.compress_type)
                for relative in names:
                    built = archive.read(relative)
                    source = (source_root / relative).read_bytes()
                    if relative == ".codex-plugin/plugin.json":
                        source_document = json.loads(source.decode("utf-8"))
                        built_document = json.loads(built.decode("utf-8"))
                        self.assertIn("hooks", source_document)
                        self.assertNotIn("hooks", built_document)
                        source_document.pop("hooks")
                        self.assertEqual(source_document, built_document)
                        self.assertEqual(list(source_document), list(built_document))
                    else:
                        self.assertEqual(source, built, relative)
            self.assertEqual("codex-directory-skills-only", manifest["variant"])
            self.assertEqual(["hooks/", ".claude-plugin/"], manifest["excludedPaths"])
            self.assertEqual([{"path": ".codex-plugin/plugin.json", "removedFields": ["hooks"]}],
                             [{"path": change["path"], "removedFields": change["removedFields"]} for change in manifest["manifestChanges"]])
            self.assertEqual(len(expected_members), manifest["archive"]["fileCount"])
            self.assertEqual(expected_members, [entry["path"] for entry in manifest["files"]])
            import hashlib
            self.assertEqual(hashlib.sha256(archive_path.read_bytes()).hexdigest(), manifest["archive"]["sha256"])
            self.assertEqual(archive_path.stat().st_size, manifest["archive"]["bytes"])
            version = json.loads((source_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
            self.assertEqual(version, manifest["pluginVersion"])
            self.assertEqual(f"axiom-{version}-codex-directory-variant.zip", archive_path.name)

    def test_tree_without_plugin_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            empty = Path(scratch) / "empty"
            empty.mkdir()
            (empty / "README.md").write_text("no plugin here\n", encoding="utf-8")
            _git(empty, "init", "-q", "-b", "main")
            _git(empty, "add", "-A")
            _git(empty, "commit", "-q", "-m", "no plugin")
            result = _build(empty, "HEAD", Path(scratch) / "out")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("build-listing-variant:", result.stderr)
            self.assertFalse((Path(scratch) / "out").exists())


if __name__ == "__main__":
    unittest.main()
