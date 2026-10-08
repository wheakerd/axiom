"""Regressions for current installation support and historical evidence isolation."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from axiom_validation.context import REPOSITORY_ROOT, release_version, supported_hosts
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
        record = json.loads((REPOSITORY_ROOT / "tests/fixtures/compatibility-v3.json").read_text())
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

    def test_empty_host_history_is_valid_without_promoting_synthetic_fixtures(self):
        failures, records, fixtures, version = self.evidence.validate_repository(True)
        self.assertEqual([], failures)
        self.assertEqual(0, records)
        self.assertEqual(12, fixtures)
        self.assertEqual(release_version(), version)
        status = json.loads((REPOSITORY_ROOT / "evidence/release-status.json").read_text())
        self.assertEqual([], status["priorReleaseEvidence"])
        self.assertEqual("STATIC-ONLY", status["status"])
        self.assertTrue(all(item["status"] == "not-run" for item in status["currentHostEvidence"]))

    def test_dangling_prior_evidence_reference_is_still_rejected(self):
        status = json.loads((REPOSITORY_ROOT / "evidence/release-status.json").read_text())
        identity = json.loads((REPOSITORY_ROOT / "evidence/runtime-identity.json").read_text())
        history = self.evidence.load_runtime_histories([])
        status["priorReleaseEvidence"] = [{
            "path": "evidence/v0.0.0/codex/linux.json",
            "tag": "v0.0.0", "commit": "0" * 40,
            "host": "codex", "hostVersion": "fixture",
            "recordedAt": "2000-01-01T00:00:00Z",
            "lifecycleSources": ["startup"],
            "observationSubject": "installed-runtime-contract",
            "runtimeContractDigest": "sha256:" + "0" * 64,
            "status": "not-run",
        }]
        failures = []
        self.evidence.validate_status(status, {}, release_version(), identity, history, failures)
        self.assertTrue(any("does not identify a checked-in record" in f for f in failures), failures)

    def historical_record(self, runtime_schema, evidence_schema="3"):
        # These records reuse canonical subject bindings only to test validation;
        # the fixture's synthetic host outcomes are never checked-in evidence.
        histories = self.evidence.load_runtime_histories([])
        entry = histories[runtime_schema]["entries"][-1]
        record = json.loads(
            (REPOSITORY_ROOT / "tests/fixtures/compatibility-v3.json").read_text()
        )
        record["schemaVersion"] = evidence_schema
        record["release"] = {
            "version": entry["pluginVersion"],
            "tag": entry["tag"],
            "commit": entry["commit"],
        }
        record["installation"]["targetPluginVersion"] = entry["pluginVersion"]
        if evidence_schema == "1":
            del record["runtimeIdentity"], record["observationSubject"]
        else:
            record["runtimeIdentity"] = {
                "pluginVersion": entry["pluginVersion"],
                "runtimeContractSchemaVersion": runtime_schema,
                "runtimeContractDigest": entry["runtimeContractDigest"],
            }
        return record, entry

    def prior_status(self, *subjects):
        status = json.loads((REPOSITORY_ROOT / "evidence/release-status.json").read_text())
        records = {}
        status["priorReleaseEvidence"] = []
        for record, entry in subjects:
            path = f"evidence/{entry['tag']}/codex/linux.json"
            records[path] = record
            status["priorReleaseEvidence"].append({
                "path": path,
                "tag": record["release"]["tag"],
                "commit": record["release"]["commit"],
                "host": record["host"]["name"],
                "hostVersion": record["host"]["version"],
                "recordedAt": record["recordedAt"],
                "lifecycleSources": ["compact", "startup"],
                "observationSubject": "installed-runtime-contract",
                "runtimeContractDigest": entry["runtimeContractDigest"],
                "status": "partial-host-observed",
            })
        return status, records

    def validate_prior_status(self, status, records, histories=None):
        identity = json.loads((REPOSITORY_ROOT / "evidence/runtime-identity.json").read_text())
        if histories is None:
            histories = self.evidence.load_runtime_histories([])
        failures = []
        for record in records.values():
            self.evidence.validate_record(record, None, failures)
        self.evidence.validate_status(
            status, records, release_version(), identity, histories, failures
        )
        return failures

    def validate_external_fixture(self, record, expected_commit=None):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.json"
            path.write_text(json.dumps(record))
            return self.evidence.validate_external_record(
                path,
                record["release"]["tag"],
                expected_commit or record["release"]["commit"],
            )

    def test_prior_evidence_accepts_mixed_runtime_histories(self):
        for legacy_schema in ("1", "2", "3"):
            with self.subTest(legacy_schema=legacy_schema):
                status, records = self.prior_status(
                    self.historical_record("1", legacy_schema),
                    self.historical_record("2"),
                )
                self.assertEqual([], self.validate_prior_status(status, records))

    def test_prior_evidence_rejects_commit_drift_even_when_summary_agrees(self):
        for runtime_schema in ("1", "2"):
            with self.subTest(runtime_schema=runtime_schema):
                record, entry = self.historical_record(runtime_schema)
                record["release"]["commit"] = "1" * 40
                status, records = self.prior_status((record, entry))
                failures = self.validate_prior_status(status, records)
                self.assertTrue(any("commit disagrees with tag history" in f for f in failures), failures)

    def test_prior_evidence_rejects_record_digest_hidden_by_correct_summary(self):
        record, entry = self.historical_record("2")
        record["runtimeIdentity"]["runtimeContractDigest"] = "sha256:" + "1" * 64
        status, records = self.prior_status((record, entry))
        failures = self.validate_prior_status(status, records)
        self.assertTrue(any("evidence record runtime digest disagrees" in f for f in failures), failures)

    def test_prior_evidence_rejects_wrong_schema_history(self):
        status, records = self.prior_status(self.historical_record("2"))
        histories = self.evidence.load_runtime_histories([])
        failures = self.validate_prior_status(status, records, {"1": histories["1"]})
        self.assertTrue(any("no derived runtime history entry for its schema" in f for f in failures), failures)

    def test_external_evidence_accepts_supported_schema_history_combinations(self):
        for evidence_schema, runtime_schema in (("2", "1"), ("3", "1"), ("3", "2")):
            with self.subTest(evidence_schema=evidence_schema, runtime_schema=runtime_schema):
                record, _ = self.historical_record(runtime_schema, evidence_schema)
                self.assertEqual([], self.validate_external_fixture(record))

    def test_external_evidence_rejects_commit_drift_even_when_expected_agrees(self):
        for runtime_schema in ("1", "2"):
            with self.subTest(runtime_schema=runtime_schema):
                record, _ = self.historical_record(runtime_schema)
                record["release"]["commit"] = "1" * 40
                failures = self.validate_external_fixture(record)
                self.assertIn("external record commit disagrees with canonical tag history", failures)

    def test_external_evidence_rejects_wrong_digest_or_history_schema(self):
        record, _ = self.historical_record("2")
        wrong_digest = copy.deepcopy(record)
        wrong_digest["runtimeIdentity"]["runtimeContractDigest"] = "sha256:" + "1" * 64
        failures = self.validate_external_fixture(wrong_digest)
        self.assertIn("external record runtime digest disagrees with canonical identity", failures)
        wrong_schema = copy.deepcopy(record)
        wrong_schema["runtimeIdentity"]["runtimeContractSchemaVersion"] = "1"
        failures = self.validate_external_fixture(wrong_schema)
        self.assertIn("external record release has no canonical runtime digest binding", failures)

    def test_same_release_external_record_keeps_explicit_subject_boundary(self):
        identity = json.loads((REPOSITORY_ROOT / "evidence/runtime-identity.json").read_text())
        record, _ = self.historical_record("2")
        version = identity["pluginVersion"]
        record["release"].update(version=version, tag=f"v{version}", commit="2" * 40)
        record["installation"]["targetPluginVersion"] = version
        record["runtimeIdentity"].update(
            pluginVersion=version,
            runtimeContractSchemaVersion=identity["runtimeContract"]["schemaVersion"],
            runtimeContractDigest=identity["runtimeContract"]["digest"],
        )
        self.assertEqual([], self.validate_external_fixture(record))
        failures = self.validate_external_fixture(record, expected_commit="3" * 40)
        self.assertIn("external record commit does not match --expected-commit", failures)
        status = json.loads((REPOSITORY_ROOT / "evidence/release-status.json").read_text())
        self.assertEqual("STATIC-ONLY", status["status"])
        self.assertEqual([], status["priorReleaseEvidence"])

    def test_malformed_record_fields_produce_validation_errors(self):
        record, _ = self.historical_record("2")
        paths = (
            ("schemaVersion",),
            ("release",),
            ("runtimeIdentity",),
            ("runtimeIdentity", "runtimeContractSchemaVersion"),
            ("hook", "installedCommandSha256"),
            ("cases", 0, "id"),
            ("cases", 0, "result"),
        )
        for path in paths:
            for value in ([], {}, 17, None):
                with self.subTest(path=path, value=value):
                    mutated = copy.deepcopy(record)
                    target = mutated
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = value
                    failures = []
                    self.evidence.validate_record(mutated, None, failures)
                    self.assertTrue(failures)

    def test_external_record_stops_after_invalid_structure(self):
        record, entry = self.historical_record("2")
        for field in ("release", "runtimeIdentity", "schemaVersion"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                mutated = copy.deepcopy(record)
                mutated[field] = []
                path = Path(temporary) / "synthetic.json"
                path.write_text(json.dumps(mutated))
                failures = self.evidence.validate_external_record(
                    path, entry["tag"], entry["commit"]
                )
                self.assertTrue(any(field in failure for failure in failures), failures)

    def test_invalid_json_inputs_report_load_errors(self):
        payloads = (
            b"\xff",
            b'{"nested":' + b"[" * 65 + b"0" + b"]" * 65 + b"}",
            b'{"nested":' + b"[" * 1500 + b"0" + b"]" * 1500 + b"}",
            b'{"integer":' + b"9" * 5000 + b"}",
        )
        for payload in payloads:
            with self.subTest(payload_size=len(payload)), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "synthetic.json"
                path.write_bytes(payload)
                failures = []
                self.assertIsNone(self.evidence.load_json(path, failures))
                self.assertTrue(failures)

    def test_malformed_current_status_fields_produce_validation_errors(self):
        base = json.loads((REPOSITORY_ROOT / "evidence/release-status.json").read_text())
        for field in ("host", "status"):
            for value in ([], {}, 17):
                with self.subTest(field=field, value=value):
                    status = copy.deepcopy(base)
                    status["currentHostEvidence"][0][field] = value
                    failures = self.validate_prior_status(status, {})
                    self.assertTrue(any(field in failure for failure in failures), failures)
