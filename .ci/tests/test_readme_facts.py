"""Tests for the README facts rendered from the packaged skill metadata."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.readme_facts import (
    README_SKILL_INDEX_END,
    README_SKILL_INDEX_START,
    README_TRANSLATIONS,
    check_readme_facts,
    load_skill_summaries,
    readme_surfaces,
    render_skill_index,
)
from axiom_validation.repository_policy import BUNDLED_SKILL_ORDER


class ReadmeFactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        shutil.copyfile(REPOSITORY_ROOT / "README.md", self.root / "README.md")
        shutil.copytree(REPOSITORY_ROOT / "plugin" / "skills", self.root / "plugin" / "skills")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def metadata(self, skill: str) -> Path:
        return self.root / "plugin" / "skills" / skill / "agents" / "openai.yaml"

    def test_checked_in_readme_matches_the_skill_metadata(self):
        failures: list[str] = []
        self.assertEqual(len(BUNDLED_SKILL_ORDER), check_readme_facts(failures))
        self.assertEqual([], failures)

    def test_index_links_every_skill_reference_heading_in_order(self):
        failures: list[str] = []
        index = render_skill_index(load_skill_summaries(failures))
        self.assertEqual([], failures)
        positions = [index.index(f"](plugin/skills/{name}/SKILL.md)") for name in BUNDLED_SKILL_ORDER]
        self.assertEqual(sorted(positions), positions)

    def test_checked_in_readme_translation_carries_the_same_generated_regions(self):
        self.assertEqual(("README.md", *README_TRANSLATIONS), readme_surfaces(REPOSITORY_ROOT))
        for relative in README_TRANSLATIONS:
            shutil.copyfile(REPOSITORY_ROOT / relative, self.root / relative)
        failures: list[str] = []
        check_readme_facts(failures, root=self.root)
        self.assertEqual([], failures)
        mirror = self.root / README_TRANSLATIONS[0]
        mirror.write_text(mirror.read_text().replace("| --- | --- |", "| --- | ---- |", 1))
        check_readme_facts(failures, root=self.root)
        self.assertEqual([f"{README_TRANSLATIONS[0]} generated skill facts are stale; run python3 .ci/scripts/render-release-facts.py --render"], failures)

    def test_a_changed_short_description_makes_the_readme_stale(self):
        path = self.metadata("task-planning")
        path.write_text(path.read_text().replace("Create and revise plans", "Draft plans"))
        failures: list[str] = []
        check_readme_facts(failures, root=self.root)
        self.assertEqual(1, len(failures))
        self.assertIn("generated skill facts are stale", failures[0])

    def test_table_breaking_descriptions_are_rejected(self):
        path = self.metadata("task-planning")
        path.write_text(path.read_text().replace("Create and revise plans", "Create | revise plans"))
        failures: list[str] = []
        self.assertEqual(0, check_readme_facts(failures, root=self.root))
        self.assertIn("without table or code delimiters", failures[0])

    def test_missing_or_reordered_markers_are_reported(self):
        readme = self.root / "README.md"
        text = readme.read_text()
        for label, mutated in {
            "missing": text.replace(README_SKILL_INDEX_START + "\n", ""),
            "reordered": text.replace(README_SKILL_INDEX_START, "<!-- placeholder -->")
            .replace(README_SKILL_INDEX_END, README_SKILL_INDEX_START)
            .replace("<!-- placeholder -->", README_SKILL_INDEX_END),
        }.items():
            with self.subTest(label=label):
                readme.write_text(mutated)
                failures: list[str] = []
                check_readme_facts(failures, root=self.root)
                self.assertEqual(1, len(failures))
                self.assertIn("cannot validate README.md generated skill facts", failures[0])


if __name__ == "__main__":
    unittest.main()
