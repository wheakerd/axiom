"""Focused tests for canonical release facts and Git route boundaries."""

from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import RELEASE_VERSION, REPOSITORY_ROOT
from axiom_validation.release_facts import (
    FACTS_SURFACES,
    FACTS_SURFACE_VERSIONS,
    SUPERSEDED_CANDIDATE_LABEL,
    check_release_facts,
    check_release_surface_text,
    discover_fact_surface_versions,
    load_release_facts,
    replace_release_block,
    rendered_release_block,
    validate_release_facts_record,
)
from axiom_validation.route_catalog import (
    check_route_catalog,
    check_route_surface_text,
    load_route_catalog,
    rendered_route_block,
    route_boundary_scenarios,
)


class ReleaseFactTests(unittest.TestCase):
    def test_current_readme_and_historical_release_note_follow_owned_records(self):
        self.assertEqual(RELEASE_VERSION, FACTS_SURFACE_VERSIONS["README.md"])
        self.assertEqual(
            RELEASE_VERSION,
            FACTS_SURFACE_VERSIONS[f"docs/releases/v{RELEASE_VERSION}.md"],
        )
        self.assertEqual("0.8.4", FACTS_SURFACE_VERSIONS["docs/releases/v0.8.4.md"])
        failures = []
        self.assertEqual(len(FACTS_SURFACES), check_release_facts(failures))
        self.assertEqual([], failures)

    def test_changed_measured_value_is_rejected(self):
        failures = []
        document = load_release_facts("0.8.4", failures)
        self.assertIsNotNone(document)
        self.assertEqual([], failures)
        mutated = copy.deepcopy(document)
        mutated["candidate"]["metrics"]["utf8Bytes"] += 1
        mutation_failures = []
        self.assertFalse(
            validate_release_facts_record(mutated, "0.8.4", mutation_failures)
        )
        self.assertTrue(
            any("utf8ByteDelta" in failure for failure in mutation_failures),
            mutation_failures,
        )

        surface = rendered_release_block("docs/releases/v0.8.4.md", document)
        self.assertIn("absolute threshold `reached`", surface)
        self.assertIn("review status `reviewed`", surface)
        self.assertEqual(3, len(surface.splitlines()))
        surface = surface.replace("7,739 UTF-8 bytes", "7,740 UTF-8 bytes", 1)
        surface_failures = []
        check_release_surface_text(
            "docs/releases/v0.8.4.md", surface, document, surface_failures
        )
        self.assertTrue(any("drifted" in failure for failure in surface_failures))

    def test_unlabeled_superseded_candidate_is_rejected(self):
        failures = []
        document = load_release_facts("0.8.4", failures)
        self.assertIsNotNone(document)
        self.assertEqual([], failures)
        base = rendered_release_block("docs/releases/v0.8.4.md", document)
        stale = f"{base}\n\nThe always-loaded router is 7,530 UTF-8 bytes."
        stale_failures = []
        check_release_surface_text(
            "docs/releases/v0.8.4.md", stale, document, stale_failures
        )
        self.assertTrue(
            any("unlabeled superseded" in failure for failure in stale_failures),
            stale_failures,
        )

        labeled_only_failures = []
        check_release_surface_text(
            "docs/releases/v0.8.4.md",
            f"{base}\n\n{SUPERSEDED_CANDIDATE_LABEL}: 7,530 UTF-8 bytes.",
            document,
            labeled_only_failures,
        )
        self.assertTrue(
            any("lack an immutable" in failure for failure in labeled_only_failures),
            labeled_only_failures,
        )

        bound_failures = []
        check_release_surface_text(
            "docs/releases/v0.8.4.md",
            f"{base}\n\n{SUPERSEDED_CANDIDATE_LABEL}: 7,530 UTF-8 bytes; "
            f"content SHA-256 `{'a' * 64}`.",
            document,
            bound_failures,
        )
        self.assertEqual([], bound_failures)

    def test_current_and_managed_historical_release_notes_are_discovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release_root = root / "docs" / "releases"
            release_root.mkdir(parents=True)
            (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
            (release_root / "v0.8.8.md").write_text("current\n", encoding="utf-8")
            (release_root / "v0.8.7.md").write_text(
                "<!-- release-facts:v0.8.7-context-budget:start -->\n",
                encoding="utf-8",
            )
            (release_root / "v0.8.6.md").write_text("unmanaged\n", encoding="utf-8")
            surfaces = discover_fact_surface_versions(root, "0.8.8")
        self.assertEqual(
            {
                "README.md": "0.8.8",
                "docs/releases/v0.8.8.md": "0.8.8",
                "docs/releases/v0.8.7.md": "0.8.7",
            },
            surfaces,
        )

        failures = []
        current_document = load_release_facts(RELEASE_VERSION, failures)
        self.assertIsNotNone(current_document)
        self.assertEqual([], failures)
        current_path = f"docs/releases/v{RELEASE_VERSION}.md"
        inserted = replace_release_block(current_path, "Version facts.\n", current_document)
        self.assertIn("## Routing Context Facts", inserted)
        self.assertIn("2 direct references", inserted)
        self.assertIn("+1 reference", inserted)
        self.assertIn(
            f"<!-- release-facts:v{RELEASE_VERSION}-context-budget:start -->",
            inserted,
        )

    def test_structured_route_catalog_drives_docs_and_offline_scenarios(self):
        failures = []
        self.assertEqual(10, check_route_catalog(failures))
        self.assertEqual([], failures)
        scenarios = route_boundary_scenarios()
        self.assertEqual(10, len(scenarios))
        self.assertIsNone(scenarios[0]["route"])
        self.assertEqual(
            {"traceable-git-submit"},
            {scenario["route"] for scenario in scenarios[1:]},
        )

    def test_exact_over_broad_readme_sentence_is_rejected(self):
        failures = []
        document = load_route_catalog(failures)
        self.assertIsNotNone(document)
        self.assertEqual([], failures)
        text = (
            rendered_route_block(document)
            + "\n\nAn explicit Git submit, publish, or push selects "
            "`traceable-git-submit`."
        )
        route_failures = []
        check_route_surface_text("README.md", text, document, route_failures)
        self.assertTrue(
            any("over-broad route claim" in failure for failure in route_failures),
            route_failures,
        )

    def test_check_cli_is_cwd_independent_and_read_only(self):
        readme = REPOSITORY_ROOT / "README.md"
        before = readme.read_bytes()
        script = REPOSITORY_ROOT / "scripts" / "render-release-facts.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd="/tmp",
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Canonical fact validation passed", completed.stdout)
        self.assertEqual(before, readme.read_bytes())

        missing_mode = subprocess.run(
            [sys.executable, str(script)],
            cwd="/tmp",
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, missing_mode.returncode)
        self.assertEqual(before, readme.read_bytes())


if __name__ == "__main__":
    unittest.main()
