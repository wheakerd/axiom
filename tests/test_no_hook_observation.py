"""Validate the protocol-only Codex no-Hook observer and fake process boundary."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.no_hook_observation import (
    BatchLedger,
    CODEX_BINARY_SHA256,
    EXPECTED_CASE_IDS,
    MAX_STDERR_BYTES,
    MAX_STDOUT_BYTES,
    ObservationError,
    PROBE_NOTICE,
    PROBE_NOTICE_SHA256,
    build_isolated_environment,
    build_codex_argv,
    build_marketplace_add_argv,
    build_plugin_add_argv,
    check_no_hook_observation,
    classify_stderr,
    cleanup_owned_root,
    freeze_owned_root,
    freeze_executable,
    load_golden_cases,
    main,
    parse_jsonl,
    parse_marketplace_receipt,
    parse_plugin_receipt,
    observe_case_process,
    recheck_executable,
    render_case_prompt,
    run_bounded_process,
    self_digest,
    snapshot_tree,
    validate_execution_guard,
    validate_model_response,
    validate_normalized_result,
    validate_protocol_documents,
    write_normalized_result,
)


FIXTURE = REPOSITORY_ROOT / "tests/fixtures/no_hook_observation.py"
TAXONOMY = REPOSITORY_ROOT / "evals/codex-exec-jsonl-observer-v3.json"
PROMPT = REPOSITORY_ROOT / "evals/no-hook-observation/codex-prompt-envelope-v1.json"
FIXTURES = REPOSITORY_ROOT / "evals/no-hook-observation/codex-fixtures-v1.json"
RESULT_SCHEMA = REPOSITORY_ROOT / "evals/no-hook-observation/codex-result-schema-v1.json"
ENTRYPOINT = REPOSITORY_ROOT / "scripts/run-no-hook-codex-observation.py"
MODULE = REPOSITORY_ROOT / "axiom_validation/no_hook_observation.py"


def event(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode() + b"\n"


def valid_response(case: dict[str, object]) -> dict[str, object]:
    return {
        "profileId": "openai-hook-independent-v1",
        "contractBindings": {
            "profileContractSha256": "b693580201a51fb5ecc5058b2e6ee8e63ddb948580f7fee7ce6042215ec07a88",
            "goldenSetSha256": "05febacecdf36ac05ae95d55e835c4d207c4a24dc2bb68a44cb62aa3e108a40c",
            "responseSchemaSha256": "e1010ee20daeef5dae801f34d689dff6c0b063f969e254331ceedb670dcd2db4",
            "caseId": case["id"],
            "contractVersion": case["contractVersion"],
        },
        "discoveryOutcome": case["expectedOutcome"],
        "selectedRoutes": case["expectedRoutes"],
        "clarificationCount": case["expectedClarificationCount"],
        "usingAxiomFrontDoorObserved": case["expectedUsingAxiomFrontDoorObserved"],
        "sessionStartObserved": False,
        "mutationAttempted": False,
        "mutationObserved": False,
    }


def happy_stream(response: dict[str, object], *, reasoning: bool = False) -> bytes:
    parts = [event({"type": "thread.started", "thread_id": "private"})]
    if reasoning:
        parts.append(event({"type": "item.completed", "item": {"type": "reasoning", "text": "private"}}))
    parts.append(event({"type": "turn.started"}))
    parts.append(
        event(
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": json.dumps(response, separators=(",", ":"), sort_keys=True),
                },
            }
        )
    )
    parts.append(event({"type": "turn.completed", "usage": {"private": True}}))
    return b"".join(parts)


def protocol_only_result() -> dict[str, object]:
    protocol = json.loads(
        (REPOSITORY_ROOT / "evals/no-hook-observation/codex-protocol-v1.json").read_text()
    )
    prompt = json.loads(PROMPT.read_text())
    cases = [
        {
            "caseId": case_id,
            "contractVersion": contract_version,
            "casePromptSha256": binding["casePromptSha256"],
            "status": "not-run",
            "responseDiagnostic": "not-run",
            "acceptanceDiagnostic": "not-run",
            "discoveryOutcome": "not-run",
            "selectedRoutes": [],
            "clarificationCount": 0,
            "usingAxiomFrontDoorObserved": False,
            "sessionStartObserved": False,
            "mutationAttempted": False,
            "mutationObserved": False,
            "toolActionCount": 0,
            "unknownEventCount": 0,
            "workspaceUnchanged": True,
            "bundleUnchanged": True,
            "installedCopyUnchanged": True,
            "limitations": ["protocol-only fake validation; no host observation"],
        }
        for case_id, contract_version, binding in zip(
            EXPECTED_CASE_IDS,
            (case["contractVersion"] for case in load_golden_cases(REPOSITORY_ROOT)),
            prompt["cases"],
            strict=True,
        )
    ]
    return {
        "schemaVersion": "1",
        "kind": "axiom-codex-no-hook-host-observation",
        "runId": "codex-no-hook-00000000000000000000000000000000",
        "recordedAt": "2026-09-03T00:00:00Z",
        "overallStatus": "incomplete",
        "observationProtocol": {
            "id": "axiom-codex-no-hook-observation-v1",
            "schemaVersion": "1",
            "digest": protocol["protocolDigest"],
        },
        "runner": {
            "version": "1",
            "entrypointSha256": hashlib.sha256(ENTRYPOINT.read_bytes()).hexdigest(),
            "moduleSha256": hashlib.sha256(MODULE.read_bytes()).hexdigest(),
            "taxonomySha256": hashlib.sha256(TAXONOMY.read_bytes()).hexdigest(),
            "resultSchemaSha256": hashlib.sha256(RESULT_SCHEMA.read_bytes()).hexdigest(),
        },
        "axiomIdentity": {
            "sourceCommit": "c7a3b5988cf0d922762bb4498e0a833c7412ea8d",
            "sourceTree": "9428574283cd9f58f6db0d50687592aca2ca497f",
            "repositoryPolicyRevision": 7,
            "pluginVersion": "0.10.0",
            "fullProfileInputCount": 61,
            "fullProfileRuntimeContractDigest": "sha256:17dacf7d5d73b714e0762586683f855ee48ad087769f0a20d5453dba38a38ea3",
            "profileRuntimeDigest": "sha256:296340751d4ee418432d41347bb766a380e6b6f0c74e8fcc1a7b04ce770b77e7",
            "bundleManifestDigest": "sha256:36a183abcdc04faf1e9edf13172d4f16b8ff3e813803be8b74d090b5965a8652",
            "archiveSha256": "24213ff9e239cb304a40c480ff36731f1260ecf4aa518d53e037805d64acc283",
        },
        "contractBindings": {
            "profileContractSha256": "b693580201a51fb5ecc5058b2e6ee8e63ddb948580f7fee7ce6042215ec07a88",
            "goldenSetSha256": "05febacecdf36ac05ae95d55e835c4d207c4a24dc2bb68a44cb62aa3e108a40c",
            "responseSchemaSha256": "e1010ee20daeef5dae801f34d689dff6c0b063f969e254331ceedb670dcd2db4",
            "benchmarkSha256": "7e71f8d40f1cfa5c7c6d607ef70753655f9304d2675f08145e011884f87ae1fa",
            "hostCaseSetId": "openai-hook-independent-codex-cases-v1",
            "hostCaseSetSha256": "cceafef1e178bf46d145e86fb0a1768be86a5e47856c8bd6d4fa03f3ac3da13a",
            "promptEnvelopeDigest": prompt["promptEnvelopeDigest"],
            "fixtureMatrixSha256": hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
        },
        "hostIdentity": {
            "host": "codex",
            "codexCliVersion": "0.153.0",
            "codexBinarySha256": CODEX_BINARY_SHA256,
            "model": "gpt-5.6-sol",
            "reasoningEffort": "medium",
            "operatingSystem": "linux",
            "architecture": "x86_64",
            "sandbox": "read-only",
            "approvalPolicy": "never",
            "isolatedCodexHome": True,
        },
        "installationFacts": {
            "scope": "isolated-ephemeral-test-only",
            "installedPathWithinTemporaryHome": False,
            "installedTreeVerified": False,
            "persistentUserStateChanged": False,
            "cleanupVerified": True,
        },
        "noHookProof": {
            "sourceManifestHookFieldAbsent": True,
            "sourceBundleHookPathAbsent": True,
            "installedManifestHookFieldAbsent": False,
            "installedHookPathAbsent": False,
            "temporaryConfigRegistrationAbsent": True,
            "fullProfileWrapperAbsent": True,
            "runtimeAxiomSessionStartEventCount": 0,
            "modelSessionStartObservedCount": 0,
        },
        "cases": cases,
        "summary": {
            "evaluatedCases": 0,
            "passCount": 0,
            "failCount": 0,
            "notRunCount": 16,
            "incompleteCount": 0,
            "selectedRouteCoverage": [],
            "clarificationMismatchCount": 0,
            "mutationAttemptCount": 0,
            "mutationObservationCount": 0,
            "sessionStartObservationCount": 0,
            "bindingMismatchCount": 0,
            "unknownEventCount": 0,
            "cleanupStatus": "verified",
        },
        "cleanup": {
            "temporaryRootsRemoved": True,
            "userCodexStateUnchanged": True,
            "sourceBundleUnchanged": True,
            "manualCleanupRequired": False,
        },
        "limitations": ["protocol-only fake validation; no host observation"],
    }


class ProtocolContractTests(unittest.TestCase):
    def test_current_protocol_is_closed_and_not_run(self):
        identities = validate_protocol_documents(REPOSITORY_ROOT)
        self.assertEqual(16, identities["caseCount"])
        self.assertEqual(5, identities["sourceBindingCount"])
        self.assertTrue(identities["protocolDigest"].startswith("sha256:"))
        failures: list[str] = []
        self.assertEqual((16, 5), check_no_hook_observation(failures))
        self.assertEqual([], failures)

    def test_prompt_hashes_bind_requests_without_expected_answers(self):
        envelope = json.loads(PROMPT.read_text(encoding="utf-8"))
        cases = load_golden_cases(REPOSITORY_ROOT)
        self.assertEqual(envelope["promptEnvelopeDigest"], self_digest(envelope, "promptEnvelopeDigest"))
        for case, binding in zip(cases, envelope["cases"], strict=True):
            rendered = render_case_prompt(envelope, case)
            self.assertEqual(binding["caseId"], case["id"])
            self.assertNotIn(b"expectedRoutes", rendered)
            self.assertNotIn(b"expectedOutcome", rendered)
            self.assertNotIn(b"caseClass", rendered)
            self.assertTrue(rendered.endswith(b"\n"))

    def test_result_history_reserves_but_does_not_create_host_result(self):
        history = json.loads(
            (REPOSITORY_ROOT / "evals/no-hook-observation/result-history-v1.json").read_text()
        )
        self.assertEqual([], history["results"])
        self.assertEqual("not-run", history["current"]["codexObservation"])
        self.assertFalse(history["current"]["hostClaim"])
        self.assertFalse((REPOSITORY_ROOT / history["canonicalResultPath"]).exists())

    def test_probe_adjudication_is_source_bound_but_not_host_evidence(self):
        taxonomy = json.loads(TAXONOMY.read_text())
        probe = taxonomy["probeAdjudication"]
        self.assertEqual("incomplete", probe["initialStatus"])
        self.assertEqual("pass", probe["adjudicatedStatus"])
        self.assertEqual(1, probe["callCount"])
        self.assertEqual("not-run", probe["hostObservation"])
        self.assertEqual(39, len(PROBE_NOTICE))
        self.assertEqual(PROBE_NOTICE_SHA256, __import__("hashlib").sha256(PROBE_NOTICE).hexdigest())

    def test_closed_normalized_result_accepts_protocol_only_not_run_state(self):
        document = protocol_only_result()
        validate_normalized_result(document)
        mutated = json.loads(json.dumps(document))
        mutated["hostIdentity"]["unexpected"] = True
        with self.assertRaisesRegex(ObservationError, "unowned fields"):
            validate_normalized_result(mutated)

    def test_normalized_output_is_new_external_and_contains_no_raw_stream(self):
        document = protocol_only_result()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "normalized.json"
            digest = write_normalized_result(document, output)
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), digest)
            serialized = output.read_text()
            self.assertNotIn("rawJsonl", serialized)
            self.assertNotIn("rawStderr", serialized)
            with self.assertRaisesRegex(ObservationError, "already exists"):
                write_normalized_result(document, output)


class JsonlClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = json.loads(TAXONOMY.read_text())
        cls.case = load_golden_cases(REPOSITORY_ROOT)[14]
        cls.response = valid_response(cls.case)

    def test_probe_observed_happy_lifecycle(self):
        facts = parse_jsonl(happy_stream(self.response), self.taxonomy)
        self.assertEqual(
            ("thread.started", "turn.started", "item.completed", "turn.completed"),
            facts.ordered_event_types,
        )
        self.assertEqual(("agent_message",), facts.item_types)
        self.assertEqual("turn.completed", facts.terminal_type)
        self.assertEqual(1, facts.structured_result_count)
        self.assertEqual(0, facts.tool_capable_event_count)
        self.assertEqual([], validate_model_response(facts.structured_result or {}, self.case))

    def test_known_benign_item_between_thread_and_turn_is_allowed(self):
        facts = parse_jsonl(happy_stream(self.response, reasoning=True), self.taxonomy)
        self.assertEqual(("reasoning", "agent_message"), facts.item_types)

    def test_journal_retains_no_payload_or_identifier(self):
        facts = parse_jsonl(happy_stream(self.response), self.taxonomy)
        serialized = json.dumps(facts.journal)
        self.assertNotIn("private", serialized)
        self.assertNotIn("text", serialized)
        self.assertNotIn("thread_id", serialized)

    def test_probe_notice_is_narrow_and_actual_case_rejects_it(self):
        self.assertEqual(
            "codex-cli-stdin-additional-context-notice",
            classify_stderr(PROBE_NOTICE, prompt_transport="positional-optional-stdin"),
        )
        self.assertEqual("unknown-nonempty", classify_stderr(PROBE_NOTICE, prompt_transport="stdin-sentinel"))
        self.assertEqual("empty", classify_stderr(b"", prompt_transport="stdin-sentinel"))

    def test_closed_stream_failures(self):
        base_start = event({"type": "thread.started"}) + event({"type": "turn.started"})
        result = event({"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(self.response)}})
        terminal = event({"type": "turn.completed"})
        cases = {
            "malformed": b"{oops}\n",
            "unknown-event": base_start + event({"type": "future.event"}) + terminal,
            "unknown-item": base_start + event({"type": "item.completed", "item": {"type": "future"}}) + terminal,
            "unknown-status": base_start + event({"type": "item.started", "item": {"type": "command_execution", "status": "future"}}) + terminal,
            "tool": base_start + event({"type": "item.started", "item": {"type": "command_execution", "status": "in_progress"}}) + terminal,
            "missing-terminal": base_start + result,
            "multiple-terminal": base_start + result + terminal + terminal,
            "after-terminal": base_start + result + terminal + event({"type": "item.completed", "item": {"type": "reasoning"}}),
            "missing-result": base_start + terminal,
            "duplicate-result": base_start + result + result + terminal,
            "truncated": base_start + result.rstrip(b"\n"),
        }
        for name, data in cases.items():
            with self.subTest(name=name), self.assertRaises(ObservationError):
                parse_jsonl(data, self.taxonomy)

    def test_response_schema_and_mutation_facts_fail_closed(self):
        bad = dict(self.response)
        bad["extra"] = True
        self.assertIn("response keys do not match the closed schema", validate_model_response(bad, self.case))
        bad = dict(self.response)
        bad["mutationAttempted"] = True
        self.assertIn("mutation fact is forbidden", validate_model_response(bad, self.case))
        bad = dict(self.response)
        bad["selectedRoutes"] = ["using-axiom"]
        self.assertIn("selected route mismatch", validate_model_response(bad, self.case))


class ProcessAndIsolationTests(unittest.TestCase):
    def run_fake(self, scenario: str, *, timeout: int = 3):
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "AXIOM_FAKE_SCENARIO": scenario,
        }
        return run_bounded_process(
            [sys.executable, str(FIXTURE), "exec", "-"],
            prompt=b"observer-owned prompt\n",
            cwd=REPOSITORY_ROOT,
            env=environment,
            timeout_seconds=timeout,
        )

    def test_fake_cli_happy_and_stderr_are_bounded(self):
        capture = self.run_fake("happy")
        self.assertEqual(0, capture.returncode)
        self.assertEqual(b"", capture.stderr)
        taxonomy = json.loads(TAXONOMY.read_text())
        facts = parse_jsonl(capture.stdout, taxonomy)
        self.assertEqual(1, facts.structured_result_count)

    def test_timeout_terminates_and_reaps(self):
        capture = self.run_fake("timeout", timeout=1)
        self.assertTrue(capture.timed_out)
        self.assertNotEqual(None, capture.returncode)

    def test_stdout_and_stderr_limits_stop_child(self):
        for scenario, bound in (("oversized-stdout", MAX_STDOUT_BYTES), ("oversized-stderr", MAX_STDERR_BYTES)):
            with self.subTest(scenario=scenario), self.assertRaisesRegex(ObservationError, "byte limit"):
                self.run_fake(scenario)
            self.assertGreater(bound, 0)

    def test_canonical_invocation_uses_stdin_sentinel_not_prompt_argv(self):
        argv = build_codex_argv(Path("/opt/codex"), Path("/tmp/schema"), Path("/tmp/workspace"))
        self.assertEqual("-", argv[-1])
        self.assertNotIn("observer-owned prompt", argv)
        self.assertIn("--json", argv)
        self.assertIn("--ephemeral", argv)
        self.assertIn("--ignore-user-config", argv)
        self.assertIn("--ignore-rules", argv)
        self.assertIn('shell_environment_policy.inherit="none"', argv)

    def test_isolated_environment_is_allowlisted_and_does_not_inherit_secret(self):
        with mock.patch.dict(os.environ, {"UNRELATED_SECRET": "forbidden"}):
            environment = build_isolated_environment(
                codex_home=Path("/observer/codex-home"),
                home=Path("/observer/home"),
                xdg_config_home=Path("/observer/config"),
                xdg_cache_home=Path("/observer/cache"),
                xdg_data_home=Path("/observer/data"),
                credential="opaque-test-value",
            )
        self.assertNotIn("UNRELATED_SECRET", environment)
        self.assertEqual("opaque-test-value", environment["CODEX_API_KEY"])

    def test_execution_guard_requires_every_independent_authorization(self):
        digest = "sha256:" + "1" * 64
        validate_execution_guard(
            execute=True,
            expected_protocol_digest=digest,
            actual_protocol_digest=digest,
            expected_binary_digest=CODEX_BINARY_SHA256,
            actual_binary_digest=CODEX_BINARY_SHA256,
            authorized_call_count=16,
            credential_present=True,
        )
        fields = {
            "execute": True,
            "expected_protocol_digest": digest,
            "actual_protocol_digest": digest,
            "expected_binary_digest": CODEX_BINARY_SHA256,
            "actual_binary_digest": CODEX_BINARY_SHA256,
            "authorized_call_count": 16,
            "credential_present": True,
        }
        for name, value in (("execute", False), ("expected_protocol_digest", None), ("expected_binary_digest", None), ("authorized_call_count", 15), ("credential_present", False)):
            candidate = dict(fields)
            candidate[name] = value
            with self.subTest(name=name), self.assertRaises(ObservationError):
                validate_execution_guard(**candidate)

    def test_default_cli_validation_never_launches_process(self):
        with mock.patch("axiom_validation.no_hook_observation.subprocess.Popen") as launch:
            self.assertEqual(0, main(["--check"]))
        launch.assert_not_called()

    def test_batch_hard_stop_marks_remaining_cases_not_run(self):
        ledger = BatchLedger()
        ledger.seal(EXPECTED_CASE_IDS[0], "pass")
        ledger.hard_stop(EXPECTED_CASE_IDS[1], "incomplete")
        self.assertEqual("pass", ledger.states[0][1])
        self.assertEqual("incomplete", ledger.states[1][1])
        self.assertTrue(all(state == "not-run" for _, state in ledger.states[2:]))
        with self.assertRaises(ObservationError):
            ledger.seal(EXPECTED_CASE_IDS[1], "pass")

    def test_snapshot_detects_workspace_or_installed_copy_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "fixture.txt"
            target.write_text("before\n")
            before = snapshot_tree(root)
            target.write_text("after\n")
            after = snapshot_tree(root)
            self.assertNotEqual(before, after)

    def test_cleanup_rejects_identity_substitution(self):
        base = Path(tempfile.mkdtemp())
        original = base / "owned"
        moved = base / "moved"
        original.mkdir()
        identity = freeze_owned_root(original)
        original.rename(moved)
        original.mkdir()
        try:
            with self.assertRaisesRegex(ObservationError, "identity changed"):
                cleanup_owned_root(identity)
            self.assertTrue(original.is_dir())
        finally:
            shutil.rmtree(base)

    def test_cleanup_removes_exact_owned_root(self):
        root = Path(tempfile.mkdtemp())
        identity = freeze_owned_root(root)
        (root / "temporary").write_text("x")
        cleanup_owned_root(identity)
        self.assertFalse(root.exists())

    def test_fake_marketplace_and_install_receipts_are_closed_and_contained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_home = root / "codex-home"
            home = root / "home"
            config = root / "config"
            cache = root / "cache"
            data = root / "data"
            marketplace_install = codex_home / "marketplaces" / "axiom-no-hook-observer"
            plugin_install = codex_home / "plugins" / "axiom"
            for path in (codex_home, home, config, cache, data, marketplace_install, plugin_install):
                path.mkdir(parents=True, exist_ok=True)
            fake = root / "fake-codex"
            fixture_bytes = FIXTURE.read_bytes().split(b"\n", 1)[1]
            fake.write_bytes(f"#!{sys.executable}\n".encode() + fixture_bytes)
            fake.chmod(0o755)
            fake_identity = freeze_executable(fake, hashlib.sha256(fake.read_bytes()).hexdigest())
            environment = build_isolated_environment(
                codex_home=codex_home,
                home=home,
                xdg_config_home=config,
                xdg_cache_home=cache,
                xdg_data_home=data,
                additions={
                    "AXIOM_FAKE_MARKETPLACE_ROOT": str(marketplace_install),
                    "AXIOM_FAKE_INSTALLED_PATH": str(plugin_install),
                },
            )
            marketplace_capture = run_bounded_process(
                build_marketplace_add_argv(fake, root / "marketplace"),
                prompt=b"",
                cwd=root,
                env=environment,
                maximum_stdout=64 * 1024,
                require_stdin_sentinel=False,
            )
            self.assertEqual(0, marketplace_capture.returncode)
            self.assertEqual(b"", marketplace_capture.stderr)
            self.assertEqual(
                {
                    "marketplaceName": "axiom-no-hook-observer",
                    "installedRootWithinTemporaryHome": True,
                    "alreadyAdded": False,
                },
                parse_marketplace_receipt(marketplace_capture.stdout, codex_home),
            )
            plugin_capture = run_bounded_process(
                build_plugin_add_argv(fake),
                prompt=b"",
                cwd=root,
                env=environment,
                maximum_stdout=64 * 1024,
                require_stdin_sentinel=False,
            )
            self.assertEqual(0, plugin_capture.returncode)
            receipt, installed_path = parse_plugin_receipt(plugin_capture.stdout, codex_home)
            self.assertTrue(receipt["installedPathWithinTemporaryHome"])
            self.assertEqual(plugin_install, installed_path)
            recheck_executable(fake_identity)

    def test_fake_case_process_normalizes_and_detects_protected_drift(self):
        taxonomy = json.loads(TAXONOMY.read_text())
        case = load_golden_cases(REPOSITORY_ROOT)[14]
        prompt = json.loads(PROMPT.read_text())
        binding = prompt["cases"][14]
        rendered = render_case_prompt(prompt, case)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            bundle = root / "bundle"
            installed = root / "installed"
            for path in (workspace, bundle, installed):
                path.mkdir()
                (path / "identity.txt").write_text("unchanged\n")
            environment = {
                "PATH": os.environ.get("PATH", ""),
                "AXIOM_FAKE_SCENARIO": "happy",
            }
            normalized = observe_case_process(
                argv=[sys.executable, str(FIXTURE), "exec", "-"],
                prompt=rendered,
                cwd=workspace,
                env=environment,
                taxonomy=taxonomy,
                case=case,
                case_prompt_sha256=binding["casePromptSha256"],
                workspace=workspace,
                bundle=bundle,
                installed_copy=installed,
            )
            self.assertEqual("pass", normalized["status"])
            environment.update(
                {
                    "AXIOM_FAKE_SCENARIO": "workspace-drift",
                    "AXIOM_FAKE_DRIFT_TARGET": str(workspace / "identity.txt"),
                }
            )
            with self.assertRaisesRegex(ObservationError, "protected case state changed"):
                observe_case_process(
                    argv=[sys.executable, str(FIXTURE), "exec", "-"],
                    prompt=rendered,
                    cwd=workspace,
                    env=environment,
                    taxonomy=taxonomy,
                    case=case,
                    case_prompt_sha256=binding["casePromptSha256"],
                    workspace=workspace,
                    bundle=bundle,
                    installed_copy=installed,
                )


if __name__ == "__main__":
    unittest.main()
