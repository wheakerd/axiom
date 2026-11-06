"""Regressions for version-bound host support."""

import json
from pathlib import Path
import tempfile
import unittest

from axiom_validation.context import release_version, supported_hosts
from axiom_validation.repository_policy import check_retired_installation_paths


class HostSupportTests(unittest.TestCase):
    def test_release_identity_needs_only_the_codex_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / ".codex-plugin/plugin.json"
            manifest.parent.mkdir()
            manifest.write_text('{"version": "0.11.0"}\n')
            self.assertEqual("0.11.0", release_version(root))
            manifest.write_text('{"version": "0.11.0-beta"}\n')
            self.assertIsNone(release_version(root))

    def test_host_support_is_bound_to_each_version(self):
        self.assertEqual({"codex", "claude-code"}, supported_hosts("0.10.1"))
        self.assertEqual({"codex"}, supported_hosts("0.11.0"))
        self.assertEqual({"codex"}, supported_hosts("0.14.6"))
        self.assertEqual({"codex", "claude-code"}, supported_hosts("0.15.0"))
        self.assertEqual({"codex", "claude-code"}, supported_hosts("1.0.0"))
        self.assertEqual({"codex", "claude-code"}, supported_hosts("9" * 5000 + ".0.0"))
        self.assertEqual(set(), supported_hosts("0.15.0-beta"))

    def test_claude_wrapper_is_rejected_outside_supported_versions(self):
        for version, expected in ((None, 2), ("0.14.6", 2), ("0.15.0", 0)):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / ".claude-plugin").mkdir()
                (root / "hooks").mkdir()
                (root / "hooks/claude-hooks.json").symlink_to(root / "missing.json")
                if version is not None:
                    (root / ".codex-plugin").mkdir()
                    (root / ".codex-plugin/plugin.json").write_text(
                        json.dumps({"version": version}) + "\n"
                    )
                failures = []
                check_retired_installation_paths(failures, root)
                self.assertEqual(expected, len(failures), failures)
