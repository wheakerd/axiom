"""Characterize aggregate output and production-only import isolation."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

from axiom_validation.cases.routing import ROUTING_SCENARIOS
from axiom_validation.context import RELEASE_VERSION, REPOSITORY_ROOT
from axiom_validation.documentation import discover_markdown
from axiom_validation.manifests import JSON_FILES
from axiom_validation.release_facts import FACTS_SURFACES
from axiom_validation.repository_policy import EXPECTED_DIRECT_SKILLS, REQUIRED_PUBLIC_FILES


# Totals that grow with every release (release notes, installed inputs, skills,
# route fixtures) come from the production owners the aggregate reports, so a
# release that changes no validator behavior needs no edit here. Fixture totals
# stay literal: losing a fixture must fail this test.
RUNTIME_INPUT_COUNT = json.loads(
    (REPOSITORY_ROOT / "evidence" / "runtime-identity.json").read_text(encoding="utf-8")
)["runtimeContract"]["recordCount"]
EXPECTED_SUCCESS_SUMMARY = (
    f"Publication validation passed: {len(REQUIRED_PUBLIC_FILES)} required files, "
    f"{len(JSON_FILES)} JSON files, "
    f"{len(discover_markdown(REPOSITORY_ROOT))} Markdown files, "
    "21 documentation negative fixtures, "
    f"{len(ROUTING_SCENARIOS)} offline route contract fixtures, "
    "142 black-box routing cases, 66 fixed host benchmark cases, "
    "11 labeled host result records, 8 bounded-review sequences with "
    "11 review checkpoints, 8 routing-context lifecycle scenarios, "
    f"{len(FACTS_SURFACES)} canonical release-fact surfaces, "
    f"{len(EXPECTED_DIRECT_SKILLS)} generated README skill rows, "
    "10 structured Git route-boundary scenarios, "
    f"{RUNTIME_INPUT_COUNT} canonical installed-runtime inputs, "
    "13 critical-path CODEOWNERS entries, 241 traceable-Git contract fixtures, "
    "155 external-action gate fixtures, 127 rollback gate fixtures, "
    "13 source-linked cross-route, resume, and delegated-choice contracts, 102 validator parser fixtures, "
    f"version {RELEASE_VERSION}, 2 compatibility evidence records, "
    "12 compatibility evidence negative fixtures, 27 manifest schema fixtures, "
    "9 hook lifecycle fixtures, 3 pull-request event-graph fixtures, "
    "55 release-provenance fixtures, 30 immutable external action and image pins "
    "(0 Dockerfile base-image pins; 0 other Dockerfile input pins), hooks, and "
    "packaged skills."
)


class ValidatorIsolationTests(unittest.TestCase):
    def test_production_validation_modules_do_not_import_tests(self):
        validation_root = REPOSITORY_ROOT / "axiom_validation"
        violations = []
        for path in sorted(validation_root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                modules = []
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    modules.append(node.module)
                for module in modules:
                    if module == "tests" or module.startswith("tests."):
                        violations.append(f"{path.relative_to(REPOSITORY_ROOT)}:{node.lineno}")
        self.assertEqual([], violations)

    def test_aggregate_runs_with_test_imports_blocked_and_preserves_summary(self):
        script = f"""
import importlib.abc
import pathlib
import sys

repository_root = pathlib.Path({str(REPOSITORY_ROOT)!r})
tests_root = repository_root / "tests"
sys.path.insert(0, str(repository_root))
assert all(
    not entry or pathlib.Path(entry).resolve() != tests_root
    for entry in sys.path
)

class RejectTestPackage(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("axiom_validation.no_hook_", "axiom_validation.historical_no_hook")):
            raise AssertionError("retired experiment imported by current publication checks")
        if fullname == "tests" or fullname.startswith("tests."):
            raise ImportError("repository test package is intentionally unavailable")
        return None

sys.meta_path.insert(0, RejectTestPackage())
from axiom_validation.aggregate import main
raise SystemExit(main())
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertEqual(EXPECTED_SUCCESS_SUMMARY + "\n", result.stdout)


if __name__ == "__main__":
    unittest.main()
