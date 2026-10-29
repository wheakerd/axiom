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
    check_readme_facts,
    load_skill_summaries,
    render_skill_index,
)
from axiom_validation.repository_policy import SKILL_REFERENCE_ORDER


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
        self.assertEqual(len(SKILL_REFERENCE_ORDER), check_readme_facts(failures))
        self.assertEqual([], failures)

    def test_index_links_every_skill_reference_heading_in_order(self):
        failures: list[str] = []
        index = render_skill_index(load_skill_summaries(failures))
        self.assertEqual([], failures)
        positions = [index.index(f"](docs/reference/skills.md#{name})") for name in SKILL_REFERENCE_ORDER]
        self.assertEqual(sorted(positions), positions)

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
