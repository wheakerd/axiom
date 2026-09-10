"""Characterize aggregate output and production-only import isolation."""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from axiom_validation.context import RELEASE_VERSION, REPOSITORY_ROOT
from axiom_validation import no_hook_linux_isolation as isolation
from axiom_validation.no_hook_linux_isolation import check_no_hook_linux_isolation
from axiom_validation.no_hook_observation import check_no_hook_observation


EXPECTED_SUCCESS_SUMMARY = (
    "Publication validation passed: 118 required files, 6 JSON files, "
    "118 Markdown files, 17 documentation negative fixtures, "
    "78 offline route contract fixtures, "
    "95 black-box routing cases, 30 fixed host benchmark cases, "
    "11 labeled host result records, 8 bounded-review sequences with "
    "11 review checkpoints, 7 routing-context lifecycle scenarios, "
    "18 canonical release-fact surfaces, 10 structured Git route-boundary scenarios, "
    "61 canonical installed-runtime inputs, "
    "12 critical-path CODEOWNERS entries, 238 traceable-Git contract fixtures, "
    "155 external-action gate fixtures, 127 rollback gate fixtures, "
    "7 source-linked cross-route/resume contracts, 102 validator parser fixtures, "
    f"version {RELEASE_VERSION}, 2 compatibility evidence records, "
    "12 compatibility evidence negative fixtures, 21 manifest schema fixtures, "
    "9 hook lifecycle fixtures, 3 pull-request event-graph fixtures, "
    "55 release-provenance fixtures, 15 immutable external action and image pins "
    "(0 Dockerfile base-image pins; 0 other Dockerfile input pins), hooks, and "
    "packaged skills."
)


class ValidatorIsolationTests(unittest.TestCase):
    def test_module_import_does_not_initialize_runtime_backend(self):
        script = f"""
from pathlib import Path
import ctypes
import sys
from unittest import mock
sys.path.insert(0, {str(REPOSITORY_ROOT)!r})
def reject_runtime(event, args):
    if event == 'open' and isinstance(args[0], str) and args[0].startswith(('/proc/', '/sys/')):
        raise AssertionError('runtime information read during import')
sys.addaudithook(reject_runtime)
with mock.patch.object(ctypes, 'CDLL', side_effect=AssertionError('runtime initialization')):
    from axiom_validation import no_hook_linux_isolation, no_hook_observation
    assert not no_hook_observation.ACTUAL_EXECUTION_GROUPS_COMPLETE
    assert no_hook_linux_isolation._CombinedLifecycleRun().normalized_summary()['runtimeBackend'] == 'not-implemented'
"""
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script],
            cwd=REPOSITORY_ROOT, capture_output=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(b"", result.stdout)
        self.assertEqual(b"", result.stderr)

    def test_protocol_validator_never_starts_codex_or_another_process(self):
        failures: list[str] = []
        with (
            mock.patch("axiom_validation.no_hook_observation.subprocess.Popen") as launch,
            mock.patch("axiom_validation.no_hook_linux_isolation.subprocess.Popen") as domain_launch,
            mock.patch.object(isolation, "detect_process_domain_capabilities", side_effect=AssertionError("runtime detector called")),
            mock.patch.object(isolation, "_libc", side_effect=AssertionError("runtime library called")),
            mock.patch.object(isolation.LinuxProcessDomainSupervisor, "open", side_effect=AssertionError("runtime backend called")),
            mock.patch.object(isolation, "run_current_host_synthetic_probe", side_effect=AssertionError("runtime probe called")),
        ):
            self.assertEqual((16, 14), check_no_hook_observation(failures))
            self.assertEqual(1, check_no_hook_linux_isolation(failures))
        self.assertEqual([], failures)
        launch.assert_not_called()
        domain_launch.assert_not_called()

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
