"""Regressions for current installation support and historical evidence isolation."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from axiom_validation.context import REPOSITORY_ROOT, release_version, supported_hosts
from axiom_validation.historical_no_hook import historical_snapshot, restore_frozen_inputs
from axiom_validation.no_hook_bundle import check_no_hook_bundle
from axiom_validation.repository_policy import check_retired_installation_paths


class CodexOnlySupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = REPOSITORY_ROOT / "scripts/check-compatibility-evidence.py"
        spec = importlib.util.spec_from_file_location("compatibility_support_test", path)
        cls.evidence = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.evidence)

    def test_release_identity_needs_only_the_codex_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / ".codex-plugin/plugin.json"
            manifest.parent.mkdir()
            manifest.write_text('{"version": "0.11.0"}\n')
            self.assertEqual("0.11.0", release_version(root))
            manifest.write_text('{"version": "0.11.0-beta"}\n')
            self.assertIsNone(release_version(root))

    def test_legacy_evidence_does_not_expand_current_host_support(self):
        self.assertEqual({"codex", "claude-code"}, supported_hosts("0.10.1"))
        self.assertEqual({"codex"}, supported_hosts("0.11.0"))
        self.assertEqual({"codex"}, supported_hosts("1.0.0"))
        self.assertEqual({"codex"}, supported_hosts("9" * 5000 + ".0.0"))

    def test_successor_evidence_accepts_current_runtime_and_rejects_retired_host(self):
        record = json.loads((REPOSITORY_ROOT / "evidence/v0.7.4/codex/linux.json").read_text())
        record["schemaVersion"] = "3"
        record["release"].update(version="0.11.0", tag="v0.11.0")
        record["installation"]["targetPluginVersion"] = "0.11.0"
        record["runtimeIdentity"] = {
            "pluginVersion": "0.11.0",
            "runtimeContractSchemaVersion": "2",
            "runtimeContractDigest": "sha256:" + "0" * 64,
        }
        record["observationSubject"] = "installed-runtime-contract"
        failures = []
        self.evidence.validate_record(record, None, failures)
        self.assertEqual([], failures)
        retired = copy.deepcopy(record)
        retired["host"]["name"] = "claude-code"
        self.evidence.validate_record(retired, None, failures)
        self.assertTrue(any("not a supported evidence host" in value for value in failures))
        failures = []
        record["schemaVersion"] = "2"
        self.evidence.validate_record(record, None, failures)
        self.assertTrue(any("unsupported by evidence schema 2" in value for value in failures))

    def test_retired_wrapper_and_dangling_hook_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".claude-plugin").mkdir()
            (root / "hooks").mkdir()
            (root / "hooks/claude-hooks.json").symlink_to(root / "missing.json")
            failures = []
            check_retired_installation_paths(failures, root)
            self.assertEqual(2, len(failures))

    def test_historical_replay_preserves_current_identity_and_detects_drift(self):
        current_path = REPOSITORY_ROOT / "evidence/runtime-identity.json"
        current_bytes = current_path.read_bytes()
        planning_path = REPOSITORY_ROOT / "skills/task-planning/SKILL.md"
        planning_bytes = planning_path.read_bytes()
        gate_path = REPOSITORY_ROOT / "skills/using-axiom/SKILL.md"
        gate_bytes = gate_path.read_bytes()
        with historical_snapshot() as snapshot:
            self.assertFalse((snapshot / "skills/task-planning").exists())
            self.assertEqual(
                (REPOSITORY_ROOT / "tests/fixtures/no-hook-v0.10.1/using-axiom.md.txt").read_bytes(),
                (snapshot / "skills/using-axiom/SKILL.md").read_bytes(),
            )
            old = json.loads((snapshot / "evidence/runtime-identity.json").read_text())
            self.assertEqual("0.10.1", old["pluginVersion"])
            self.assertEqual("1", old["runtimeContract"]["schemaVersion"])
            evidence = snapshot / "evidence/profiles/openai-hook-independent-v1/bundle-v1.json"
            document = json.loads(evidence.read_text())
            document["builds"]["archiveSha256"] = "0" * 64
            evidence.write_text(json.dumps(document))
            failures = []
            check_no_hook_bundle(failures, snapshot)
            self.assertTrue(any("two-build equality evidence drifted" in value for value in failures))
        self.assertEqual(current_bytes, current_path.read_bytes())
        self.assertEqual(planning_bytes, planning_path.read_bytes())
        self.assertEqual(gate_bytes, gate_path.read_bytes())
        self.assertEqual(release_version(), json.loads(current_bytes)["pluginVersion"])

    def test_historical_replay_rejects_its_source_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            retained = root / "skills/task-planning/SKILL.md"
            retained.parent.mkdir(parents=True)
            retained.write_text("Current planning capability\n")
            with self.assertRaisesRegex(ValueError, "separate disposable destination"):
                restore_frozen_inputs(root, root)
            self.assertEqual("Current planning capability\n", retained.read_text())
