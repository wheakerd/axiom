"""Ordinary offline regressions for the native observer's actual entrypoints."""

import copy
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from axiom_validation import no_hook_native_observation as native
from axiom_validation import no_hook_observation as legacy


ROOT = Path(__file__).resolve().parents[1]


def event(document):
    return legacy._canonical_json(document) + b"\n"


def response(case, token):
    return {"profileId": legacy.PROFILE_ID, "opaqueCaseBinding": token,
            "contractBindings": {"profileContractSha256": legacy.PROFILE_SHA256,
                "goldenSetSha256": legacy.GOLDEN_SET_SHA256,
                "hostCaseSetSha256": legacy.HOST_CASE_SET_SHA256},
            "discoveryOutcome": case["expectedOutcome"], "selectedRoutes": case["expectedRoutes"],
            "clarificationCount": case["expectedClarificationCount"],
            "usingAxiomFrontDoorObserved": case["expectedUsingAxiomFrontDoorObserved"],
            "sessionStartObserved": False, "mutationAttempted": False, "mutationObserved": False}


def stream(document, command=None, output=""):
    records = [event({"type": "thread.started", "thread_id": "019784a7-ec72-7000-8000-000000000001"}),
               event({"type": "turn.started"})]
    if command:
        for kind, status, code, text in (("item.started", "in_progress", None, ""),
                                          ("item.completed", "completed", 0, output)):
            records.append(event({"type": kind, "item": {"id": "item_0", "type": "command_execution",
                "command": command, "aggregated_output": text, "exit_code": code, "status": status}}))
    records.extend([event({"type": "item.completed", "item": {"id": "item_1" if command else "item_0",
                    "type": "agent_message", "text": json.dumps(document)}}),
                    event({"type": "turn.completed", "usage": {"input_tokens": 1,
                        "cached_input_tokens": 0, "cache_write_input_tokens": 0,
                        "output_tokens": 1, "reasoning_output_tokens": 0}})])
    return b"".join(records)


class NativeObservationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="axiom-native-test-")
        self.parent = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.protocol = native._protocol(ROOT)
        self.cases = legacy.load_golden_cases(ROOT)
        self.taxonomy = native._input(ROOT, self.protocol, "taxonomy")
        self.synthetic_final_outputs = []

    def test_default_check_does_not_start_client_or_read_authentication(self):
        with patch.object(native.subprocess, "Popen", side_effect=AssertionError("client started")):
            self.assertEqual(native.main(["--check"], root=ROOT), 0)

    def test_prepare_and_run_require_separate_explicit_authorization(self):
        with self.assertRaisesRegex(native.NativeObservationError, "local-install authorization"):
            native.prepare_native_run(ROOT, self.parent / "run", self.parent / "bundle", Path("/fake/cli"))
        with self.assertRaisesRegex(native.NativeObservationError, "model-call authorization"):
            native.run_native_observation(ROOT, self.parent / "run")

    def test_environment_does_not_inherit_authentication_or_user_configuration(self):
        paths = native._case_paths(self.parent, 1)
        with patch.dict(os.environ, {"CODEX_API_KEY": "secret", "OPENAI_API_KEY": "secret", "HOME": "/normal"}):
            env = native.case_environment(paths)
        self.assertNotIn("CODEX_API_KEY", env)
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertEqual(env["HOME"], str(paths["user"]))
        self.assertEqual(env["CODEX_HOME"], str(paths["home"]))

    def test_case_homes_workspaces_and_state_roots_are_distinct(self):
        for name in ("home", "user", "workspace", "state", "tmp"):
            self.assertEqual(len({native._case_paths(self.parent, ordinal)[name] for ordinal in range(1, 17)}), 16)

    def test_native_argv_binds_permissions_installed_view_and_fresh_context(self):
        executable = Path("/approved/codex")
        args = native.build_native_argv(executable, self.parent, 1)
        overrides = [args[index + 1] for index, value in enumerate(args) if value == "-c"]
        document = {}
        for override in overrides:
            parsed = tomllib.loads(override)
            document.update(parsed)
        permission = next(tomllib.loads(value)["permissions"] for value in overrides if value.startswith("permissions="))["native-case"]
        paths = native._case_paths(self.parent, 1)
        self.assertEqual(permission["network"], {"enabled": False})
        self.assertEqual(permission["filesystem"][":root"], "deny")
        self.assertNotIn(str(paths["home"]), permission["filesystem"])
        self.assertEqual(permission["filesystem"][str(paths["package"])], "read")
        self.assertEqual(permission["filesystem"][str(executable)], "read")
        for flag in ("--ephemeral", "--ignore-rules", "--ignore-user-config", "--cd"):
            self.assertIn(flag, args)
        self.assertNotIn("--cwd", args)
        self.assertLess(args.index("--ask-for-approval"), args.index("exec"))
        self.assertIn("features.shell_tool=true", args)
        self.assertIn("features.plugins=false", args)
        self.assertIn("skills.bundled.enabled=false", args)
        self.assertIn("plugins={}", args)
        self.assertIn("marketplaces={}", args)
        self.assertIn("features.hooks=false", args)
        self.assertIn("features.plugin_hooks=false", args)
        self.assertIn("features.skip_host_skill_discovery=false", args)
        for flag in ("features.code_mode=false", "features.code_mode_only=false",
                     "features.code_mode_host=false", "features.code_mode_prewarm=false"):
            self.assertIn(flag, args)
        self.assertIn('web_search="disabled"', args)
        self.assertFalse(any(value.startswith(("features.web_search_cached=", "features.web_search_request="))
                             for value in overrides))
        self.assertEqual(args[-1], "-")
        self.assertNotIn(self.cases[0]["request"], " ".join(args))

    def test_native_argv_binds_explicit_final_output_without_exposing_it_to_tools(self):
        target = self.parent / "private-ledger" / "final-message-01.json"
        args = native.build_native_argv(Path("/approved/codex"), self.parent, 1, final_output=target)
        self.assertEqual(args.count("--output-last-message"), 1)
        self.assertEqual(args[args.index("--output-last-message") + 1], str(target))
        filesystem = next(tomllib.loads(args[index + 1])["permissions"]["native-case"]["filesystem"]
                          for index, value in enumerate(args) if value == "-c" and
                          args[index + 1].startswith("permissions="))
        self.assertNotIn(str(target), filesystem)
        self.assertNotIn(str(target.parent), filesystem)
        self.assertEqual(args[-1], "-")

    def test_permissions_allow_only_runtime_fixture_and_installed_package_roots(self):
        executable = Path("/approved/codex")
        for ordinal in range(1, 17):
            args = native.build_native_argv(executable, self.parent, ordinal)
            filesystem = next(tomllib.loads(args[index + 1])["permissions"]["native-case"]["filesystem"]
                              for index, value in enumerate(args) if value == "-c" and
                              args[index + 1].startswith("permissions="))
            paths = native._case_paths(self.parent, ordinal)
            expected = {":root": "deny", ":minimal": "read", str(executable): "read",
                        str(paths["workspace"]): "read"}
            if ordinal != 11:
                expected[str(paths["package"])] = "read"
            self.assertEqual(filesystem, expected)
            for name in ("home", "state", "user", "tmp"):
                self.assertNotIn(str(paths[name]), filesystem)

    def test_case_eleven_has_no_plugin_or_package_permission(self):
        args = native.build_native_argv(Path("/approved/codex"), self.parent, 11)
        self.assertIn("features.plugins=false", args)
        self.assertIn("plugins={}", args)
        self.assertIn("marketplaces={}", args)
        paths = native._case_paths(self.parent, 11)
        permissions = next(tomllib.loads(args[index + 1])["permissions"]["native-case"]
                           for index, value in enumerate(args) if value == "-c" and args[index + 1].startswith("permissions="))
        self.assertNotIn(str(paths["package"]), permissions["filesystem"])

    def test_exclusive_attempt_marker_cannot_be_overwritten(self):
        path = self.parent / "attempt-01.json"
        native._exclusive(path, b"original\n")
        with self.assertRaises(FileExistsError):
            native._exclusive(path, b"replacement\n")
        self.assertEqual(path.read_bytes(), b"original\n")

    def test_bound_read_grammar_checks_exact_source_bytes(self):
        readable = {str(self.parent / "SKILL.md"): b"first\nsecond\nthird\n"}
        self.assertEqual(native._read_command("cat SKILL.md", readable, self.parent), b"first\nsecond\nthird\n")
        self.assertEqual(native._read_command("/bin/bash -lc 'sed -n 2,3p SKILL.md'", readable, self.parent), b"second\nthird\n")
        for command in ("cat ../auth.json", "cat /unbound", "cat SKILL.md; echo x", "python script.py", "ls"):
            with self.subTest(command=command), self.assertRaises(native.NativeObservationError):
                native._read_command(command, readable, self.parent)

    def test_readonly_command_jsonl_preserves_source_lifecycle_and_result(self):
        token = "ocb1_" + "0" * 64
        document = response(self.cases[0], token)
        raw = stream(document, "cat SKILL.md", "public skill\n")
        parsed, count = native.parse_native_jsonl(raw, self.taxonomy,
            {str(self.parent / "SKILL.md"): b"public skill\n"}, self.parent)
        self.assertEqual(parsed.structured_result, document)
        self.assertEqual(count, 1)
        self.assertEqual(parsed.terminal_type, "turn.completed")

    def test_commentary_before_final_json_is_a_valid_native_stream(self):
        document = response(self.cases[0], "ocb1_" + "0" * 64)
        lines = [json.loads(line) for line in stream(document).splitlines()]
        lines[2]["item"]["id"] = "item_1"
        lines.insert(2, {"type": "item.completed", "item": {
            "id": "item_0", "type": "agent_message", "text": "I will inspect the supplied public fixture."}})
        parsed, count = native.parse_native_jsonl(b"".join(event(line) for line in lines),
                                                self.taxonomy, {}, self.parent)
        self.assertEqual(parsed.structured_result, document)
        self.assertEqual(parsed.item_types, ("agent_message", "agent_message"))
        self.assertEqual(parsed.structured_result_count, 1)
        self.assertEqual(parsed.terminal_type, "turn.completed")
        self.assertEqual(count, 0)

    def test_multiple_json_messages_select_only_the_last_emitted_candidate(self):
        first = response(self.cases[0], "ocb1_" + "0" * 64)
        last = copy.deepcopy(first)
        last["selectedRoutes"] = ["agents-architect"]
        lines = [json.loads(line) for line in stream(first).splitlines()]
        lines.insert(-1, {"type": "item.completed", "item": {
            "id": "item_1", "type": "agent_message", "text": json.dumps(last)}})
        parsed, _ = native.parse_native_jsonl(b"".join(event(line) for line in lines),
                                             self.taxonomy, {}, self.parent)
        self.assertEqual(parsed.structured_result, last)
        self.assertNotEqual(parsed.structured_result, first)
        self.assertEqual(parsed.structured_result_count, 1)

    def test_invalid_last_message_reports_a_safe_response_assertion(self):
        document = response(self.cases[0], "ocb1_" + "0" * 64)
        private_text = "PUBLIC-FIXTURE-only: final commentary is not JSON"
        lines = [json.loads(line) for line in stream(document).splitlines()]
        lines.insert(-1, {"type": "item.completed", "item": {
            "id": "item_1", "type": "agent_message", "text": private_text}})
        with self.assertRaises(native.NativeStreamError) as caught:
            native.parse_native_jsonl(b"".join(event(line) for line in lines),
                                      self.taxonomy, {}, self.parent)
        self.assertEqual(caught.exception.code, "final-message-invalid-json")
        self.assertEqual(caught.exception.phase, "response")
        self.assertEqual(caught.exception.event_ordinal, 4)
        self.assertNotIn(private_text, str(caught.exception))

    def test_nonobject_last_json_is_not_replaced_by_an_earlier_object(self):
        document = response(self.cases[0], "ocb1_" + "0" * 64)
        for text in ("null", "[]", "true", '"public scalar fixture"'):
            with self.subTest(text=text):
                lines = [json.loads(line) for line in stream(document).splitlines()]
                lines.insert(-1, {"type": "item.completed", "item": {
                    "id": "item_1", "type": "agent_message", "text": text}})
                with self.assertRaises(native.NativeStreamError) as caught:
                    native.parse_native_jsonl(b"".join(event(line) for line in lines),
                                              self.taxonomy, {}, self.parent)
                self.assertEqual((caught.exception.code, caught.exception.phase,
                                  caught.exception.event_ordinal), ("final-message-not-object", "response", 4))

    def test_final_output_reservation_is_private_and_never_overwrites_existing_content(self):
        path = self.parent / "final-output-fixture.json"
        identity = native._reserve_final_output(path)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(identity, (path.stat().st_dev, path.stat().st_ino))
        path.write_bytes(b'{"public": "fixture"}\n')
        with self.assertRaises(FileExistsError):
            native._reserve_final_output(path)
        self.assertEqual(path.read_bytes(), b'{"public": "fixture"}\n')
        native._check_final_output(path, identity, {"public": "fixture"})

    def test_multimessage_warning_and_command_share_ids_and_require_closure(self):
        document = response(self.cases[0], "ocb1_" + "0" * 64)
        lines = [json.loads(line) for line in stream(document, "cat SKILL.md", "public fixture\n").splitlines()]
        lines[-2]["item"]["id"] = "item_3"
        lines.insert(3, {"type": "item.completed", "item": {
            "id": "item_1", "type": "error", "message": "public warning fixture"}})
        lines.insert(-2, {"type": "item.completed", "item": {
            "id": "item_2", "type": "agent_message", "text": "Public commentary fixture."}})
        readable = {str(self.parent / "SKILL.md"): b"public fixture\n"}
        parsed, count = native.parse_native_jsonl(b"".join(event(line) for line in lines),
                                                self.taxonomy, readable, self.parent)
        self.assertEqual(parsed.structured_result, document)
        self.assertEqual(count, 1)
        self.assertEqual(parsed.item_types,
                         ("command_execution", "error", "command_execution", "agent_message", "agent_message"))
        changed = copy.deepcopy(lines)
        changed[3]["item"]["id"] = "item_7"
        with self.assertRaises(native.NativeStreamError) as caught:
            native.parse_native_jsonl(b"".join(event(line) for line in changed),
                                      self.taxonomy, readable, self.parent)
        self.assertEqual((caught.exception.code, caught.exception.event_ordinal), ("item-id-sequence", 4))
        changed = [entry for entry in lines if not
                   (entry["type"] == "item.completed" and entry.get("item", {}).get("type") == "command_execution")]
        with self.assertRaises(native.NativeStreamError) as caught:
            native.parse_native_jsonl(b"".join(event(line) for line in changed),
                                      self.taxonomy, readable, self.parent)
        self.assertEqual(caught.exception.code, "terminal-active-items")

    def test_unknown_command_output_and_unclosed_lifecycle_are_rejected(self):
        document = response(self.cases[0], "ocb1_" + "0" * 64)
        readable = {str(self.parent / "SKILL.md"): b"public\n"}
        bad = [stream(document, "cat SKILL.md", "unexpected\n"),
               stream(document, "touch SKILL.md", ""),
               stream(document).rstrip(b"\n")]
        valid = stream(document, "cat SKILL.md", "public\n").splitlines(keepends=True)
        bad.append(b"".join(valid[:3] + valid[4:]))
        for raw in bad:
            with self.subTest(raw=raw[:40]), self.assertRaises(native.NativeObservationError):
                native.parse_native_jsonl(raw, self.taxonomy, readable, self.parent)

    def test_frozen_fixture_materialization_uses_real_files_and_no_remote(self):
        fixtures = native._input(ROOT, self.protocol, "fixtureMatrix")
        for ordinal in range(1, 17):
            workspace = self.parent / str(ordinal)
            workspace.mkdir()
            definition = native._definition(fixtures, ordinal)
            digest = native.materialize_fixture(workspace, definition)
            self.assertEqual(digest, legacy._expected_realized_fixture_digest(definition))
            self.assertEqual(native.fixture_identity(workspace, definition), digest)

    def test_fixture_unknown_object_is_preserved_and_rejected(self):
        fixtures = native._input(ROOT, self.protocol, "fixtureMatrix")
        workspace = self.parent / "workspace"
        workspace.mkdir()
        definition = native._definition(fixtures, 4)
        native.materialize_fixture(workspace, definition)
        unknown = workspace / "user-object"
        unknown.write_bytes(b"keep")
        with self.assertRaises(native.NativeObservationError):
            native.fixture_identity(workspace, definition)
        self.assertEqual(unknown.read_bytes(), b"keep")

    def _result(self):
        seed = b"\x17" * 32
        fixtures = native._input(ROOT, self.protocol, "fixtureMatrix")
        schema = native._input(ROOT, self.protocol, "modelResponseSchema")
        envelope = native._input(ROOT, self.protocol, "promptEnvelope")
        records = []
        for ordinal, case in enumerate(self.cases, 1):
            definition = native._definition(fixtures, ordinal)
            material = native.materialize_native_case_contract(materialization_seed=seed, ordinal=ordinal,
                protocol_digest=self.protocol["protocolDigest"], model_schema=schema,
                prompt_envelope=envelope, request=case["request"])
            records.append(native._blank_case(case, material, seed, self.protocol, definition))
        return {"schemaVersion": "2", "diagnosticRevision": 6, "priorResultSha256s": [],
                "attemptCount": 0, "cumulativeAttemptCount": 0, "protocolId": native.PROTOCOL_ID,
                "discoveryMechanism": native.DISCOVERY_MECHANISM, "pluginRuntimeEnabled": False,
                "authenticationMode": "independent-official-login",
                "protocolDigest": self.protocol["protocolDigest"], "runMode": "simulated", "hostClaim": False,
                "status": "INCOMPLETE", "materializationSeed": seed.hex(), "cliLaunchCount": 0,
                "modelRequestCount": None, "caseResults": records,
                "materializationCommitmentRoot": legacy._materialization_commitment_root(
                    [record["materializationCommitmentSha256"] for record in records]),
                "cleanup": "retained-test-state", "descendantClosure": "not-observed"}

    def test_unstarted_result_is_closed_and_does_not_claim_host_or_model_count(self):
        result = self._result()
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        for field, value in (("hostClaim", True), ("modelRequestCount", 0), ("cliLaunchCount", 16), ("status", "PASS")):
            altered = copy.deepcopy(result)
            altered[field] = value
            self.assertTrue(native.validate_native_result(altered, ROOT), field)

    def test_result_rejects_foreign_case_and_materialization(self):
        result = self._result()
        result["caseResults"][0]["caseId"] = self.cases[1]["id"]
        self.assertTrue(native.validate_native_result(result, ROOT))
        result = self._result()
        result["caseResults"][0]["casePromptSha256"] = "0" * 64
        self.assertTrue(native.validate_native_result(result, ROOT))

    def test_case_eleven_cannot_claim_plugin_even_when_incomplete(self):
        result = self._result()
        first = result["caseResults"][0]
        first.update(status="INCOMPLETE", diagnostic="input-changed")
        control = result["caseResults"][10]
        control["packageBeforeSha256"] = "1" * 64
        self.assertTrue(native.validate_native_result(result, ROOT))

    def test_unknown_raw_fields_and_resumed_prefix_are_rejected(self):
        result = self._result()
        result["rawJsonl"] = "must not be retained"
        self.assertTrue(native.validate_native_result(result, ROOT))
        result = self._result()
        result["caseResults"][1].update(status="INCOMPLETE", diagnostic="input-changed")
        self.assertTrue(native.validate_native_result(result, ROOT))

    def test_nullable_schema_members_do_not_accept_arbitrary_objects(self):
        for field, value in (("fixtureBeforeSha256", {}), ("observed", {"secret": "unowned"}),
                             ("packageBeforeSha256", True)):
            result = self._result()
            result["caseResults"][0][field] = value
            self.assertTrue(native.validate_native_result(result, ROOT), field)

    def _prepared_runner(self, *, failed_case=None):
        """Only the external CLI is simulated; all production validators run."""
        bundle = self.parent / "bundle"
        bundle.mkdir()
        evidence = json.loads((ROOT / legacy.STATIC_BUNDLE_EVIDENCE_RELATIVE).read_bytes())
        manifest = evidence["bundleManifest"]
        files = {record["path"]: (ROOT / record["path"]).read_bytes() for record in manifest["runtimeFiles"]}
        files[".codex-plugin/plugin.json"] = (json.dumps(manifest["derivedPluginManifest"]["fields"], ensure_ascii=True, indent=2) + "\n").encode("ascii")
        files["BUNDLE-MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=True, indent=2) + "\n").encode("ascii")
        for relative, data in files.items():
            path = bundle / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o644)
        self.assertEqual(native.package_identity(bundle), self.protocol["bundle"]["packageSha256"])
        executable = self.parent / "synthetic-client"
        executable.write_bytes(b"not executed\n")
        executable.chmod(0o700)
        metadata = executable.stat()
        identity = legacy.ExecutableIdentity(executable, metadata.st_dev, metadata.st_ino,
                                              metadata.st_size, hashlib.sha256(executable.read_bytes()).hexdigest())
        freeze = patch.object(legacy, "freeze_executable", return_value=identity)
        freeze.start()
        self.addCleanup(freeze.stop)
        run_root = self.parent / "run"
        calls = []

        def runner(argv, *, cwd, env, stdin=b"", line_callback=None, started_callback=None, **_):
            ordinal = int(Path(cwd).parent.name.removeprefix("case-"))
            paths = native._case_paths(run_root, ordinal)
            self.assertEqual(Path(cwd), paths["workspace"])
            self.assertEqual(env, native.case_environment(paths))
            if "marketplace" in argv:
                self.assertNotEqual(ordinal, 11)
                marketplace = run_root / "marketplace"
                (paths["home"] / "config.toml").write_text(
                    '[marketplaces."' + legacy.MARKETPLACE_NAME + '"]\nsource_type="local"\nsource=' + json.dumps(str(marketplace)) + '\n')
                receipt = {"marketplaceName": legacy.MARKETPLACE_NAME,
                           "installedRoot": str(marketplace), "alreadyAdded": False}
            elif "plugin" in argv:
                self.assertNotEqual(ordinal, 11)
                marketplace = run_root / "marketplace"
                catalog = json.loads((marketplace / ".agents/plugins/marketplace.json").read_bytes())
                source = catalog["plugins"][0]["source"]
                self.assertEqual(source, {"source": "local", "path": "./plugin"})
                shutil.copytree(marketplace / "plugin", paths["package"])
                with (paths["home"] / "config.toml").open("a") as file:
                    file.write('\n[plugins."' + legacy.PLUGIN_ID + '"]\nenabled=true\n')
                receipt = {"pluginId": legacy.PLUGIN_ID, "name": legacy.PLUGIN_NAME,
                           "marketplaceName": legacy.MARKETPLACE_NAME, "version": legacy.PLUGIN_VERSION,
                           "installedPath": str(paths["package"]), "authPolicy": "ON_INSTALL"}
            elif "login" in argv:
                self.assertEqual(argv[-2:], ["login", "status"])
                return {"returncode": 0, "stdout": b"", "stderr": b"Logged in using ChatGPT\n"}
            else:
                self.assertIn("exec", argv)
                self.assertTrue(((run_root / f"attempt-{ordinal:02d}.json").is_file() or
                                 (run_root / "diagnostic-followup" / f"attempt-{ordinal:02d}.json").is_file() or
                                 (run_root / "diagnostic-continuation" / f"attempt-{ordinal:02d}.json").is_file() or
                                 (run_root / "operator-diagnostic-continuation" / f"attempt-{ordinal:02d}.json").is_file() or
                                 (run_root / "schema-correction-continuation" / f"attempt-{ordinal:02d}.json").is_file()))
                calls.append(ordinal)
                if started_callback:
                    started_callback()
                material_schema = json.loads(Path(argv[argv.index("--output-schema") + 1]).read_bytes())
                token = material_schema["properties"]["opaqueCaseBinding"]["enum"][0]
                self.assertIn(self.cases[ordinal - 1]["request"].encode(), stdin)
                self.assertNotIn(self.cases[ordinal - 1]["id"].encode(), stdin)
                document = response(self.cases[ordinal - 1], token)
                final_output = Path(argv[argv.index("--output-last-message") + 1])
                self.assertTrue(final_output.is_file())
                self.assertFalse(final_output.is_symlink())
                self.assertEqual(final_output.stat().st_mode & 0o777, 0o600)
                self.assertEqual(final_output.read_bytes(), b"")
                self.synthetic_final_outputs.append(final_output)
                final_output.write_bytes(event(document))
                if failed_case == ordinal:
                    raw = stream(document, "touch unexpected", "")
                elif ordinal == 1:
                    skill = paths["package"] / "skills/using-axiom/SKILL.md"
                    raw = stream(document, "cat " + str(skill), skill.read_text())
                else:
                    raw = stream(document)
                if line_callback:
                    for line in raw.splitlines():
                        line_callback(line)
                return {"returncode": 0, "stdout": raw, "stderr": b"",
                        "diagnostics": {**native._diagnostics(), "inputBytesSent": len(stdin),
                                        "inputFullyDelivered": True}}
            return {"returncode": 0, "stdout": event(receipt), "stderr": b""}

        state = native.prepare_native_run(ROOT, run_root, bundle, executable,
                                          authorize_install=True, runner=runner)
        self.assertEqual(state["runMode"], "simulated")
        return run_root, runner, calls

    def test_all_actual_schema_files_match_structured_output_subset(self):
        run, _, calls = self._prepared_runner()
        allowed = {"object": {"type", "properties", "required", "additionalProperties"},
                   "array": {"type", "items", "minItems", "maxItems"},
                   "string": {"type", "enum"},
                   "integer": {"type", "minimum", "maximum"}, "boolean": {"type"}}
        def check(node):
            self.assertIn(node.get("type"), allowed, "every transmitted node needs an explicit type")
            self.assertLessEqual(set(node), allowed[node["type"]])
            if node["type"] == "object":
                self.assertIs(node["additionalProperties"], False)
                self.assertCountEqual(node["required"], node["properties"])
                self.assertEqual(len(node["required"]), len(set(node["required"])))
                for child in node["properties"].values():
                    check(child)
            elif node["type"] == "array":
                check(node["items"])
            elif "enum" in node:
                self.assertTrue(node["enum"])
                self.assertTrue(all(type(value) is str for value in node["enum"]))
        for ordinal in range(1, 17):
            with self.subTest(ordinal=ordinal):
                argv = native.build_native_argv(Path("/approved/codex"), run, ordinal)
                path = Path(argv[argv.index("--output-schema") + 1])
                check(json.loads(path.read_bytes()))
        self.assertEqual(calls, [])

    def test_native_transport_preserves_all_sixteen_blinded_contracts_and_local_uniqueness(self):
        source = native._input(ROOT, self.protocol, "modelResponseSchema")
        envelope = native._input(ROOT, self.protocol, "promptEnvelope")
        before = copy.deepcopy(source)
        self.assertIs(source["properties"]["selectedRoutes"]["uniqueItems"], True)
        for ordinal, case in enumerate(self.cases, 1):
            with self.subTest(ordinal=ordinal):
                arguments = {"materialization_seed": bytes(range(32)), "ordinal": ordinal,
                    "protocol_digest": self.protocol["protocolDigest"], "model_schema": source,
                    "prompt_envelope": envelope, "request": case["request"]}
                original = legacy.materialize_case_contract(**arguments)
                material = native.materialize_native_case_contract(**arguments)
                transported = json.loads(material.schema_bytes)
                self.assertIsNone(native.validate_response_transport(transported))
                self.assertEqual(material.prompt_bytes, original.prompt_bytes)
                self.assertEqual(material.prompt_sha256, original.prompt_sha256)
                self.assertEqual((material.token, material.opaque_binding_sha256),
                                 (original.token, original.opaque_binding_sha256))
                self.assertNotEqual(material.schema_bytes, original.schema_bytes)
                self.assertEqual(material.schema_sha256, hashlib.sha256(material.schema_bytes).hexdigest())
                props = transported["properties"]
                self.assertEqual(props["profileId"], {"type": "string", "enum": [legacy.PROFILE_ID]})
                self.assertEqual(props["opaqueCaseBinding"], {"type": "string", "enum": [material.token]})
                self.assertEqual(props["discoveryOutcome"], {"type": "string", "enum": [
                    "selected", "clarification", "no-route", "unavailable"]})
                for key, expected in (("profileContractSha256", legacy.PROFILE_SHA256),
                                      ("goldenSetSha256", legacy.GOLDEN_SET_SHA256),
                                      ("hostCaseSetSha256", legacy.HOST_CASE_SET_SHA256)):
                    self.assertEqual(props["contractBindings"]["properties"][key],
                                     {"type": "string", "enum": [expected]})
                self.assertEqual(props["selectedRoutes"]["items"]["type"], "string")
                self.assertEqual(props["selectedRoutes"]["items"]["enum"],
                                 source["properties"]["selectedRoutes"]["items"]["enum"])
                self.assertNotIn("uniqueItems", props["selectedRoutes"])
                expected_response = response(case, material.token)
                native._validate_native_response(expected_response, source, material.token)
                duplicate = {**expected_response, "selectedRoutes": ["using-axiom", "using-axiom"]}
                with self.assertRaisesRegex(native.NativeObservationError, "duplicate"):
                    native._validate_native_response(duplicate, source, material.token)
        self.assertEqual(source, before)

    def _transport_fixture(self):
        arguments = {"materialization_seed": bytes(range(32)), "ordinal": 1,
            "protocol_digest": self.protocol["protocolDigest"],
            "model_schema": native._input(ROOT, self.protocol, "modelResponseSchema"),
            "prompt_envelope": native._input(ROOT, self.protocol, "promptEnvelope"),
            "request": self.cases[0]["request"]}
        return (json.loads(legacy.materialize_case_contract(**arguments).schema_bytes),
                json.loads(native.materialize_native_case_contract(**arguments).schema_bytes))

    def test_legacy_untyped_leaf_is_rejected_without_root_annotation_masking(self):
        old, current = self._transport_fixture()
        self.assertNotIn("type", old["properties"]["profileId"])
        current["properties"]["profileId"] = copy.deepcopy(old["properties"]["profileId"])
        with self.assertRaisesRegex(native.NativeObservationError, "explicit supported type"):
            native.validate_response_transport(current)
        current["properties"]["profileId"]["type"] = "string"
        with self.assertRaisesRegex(native.NativeObservationError, "unsupported response transport keyword"):
            native.validate_response_transport(current)

    def test_legacy_unique_items_is_rejected_without_untyped_leaf_masking(self):
        old, current = self._transport_fixture()
        self.assertIs(old["properties"]["selectedRoutes"]["uniqueItems"], True)
        current["properties"]["selectedRoutes"]["uniqueItems"] = old["properties"]["selectedRoutes"]["uniqueItems"]
        with self.assertRaisesRegex(native.NativeObservationError, "unsupported response transport keyword"):
            native.validate_response_transport(current)

    def test_native_transport_rejects_unsupported_keywords_and_unclosed_objects(self):
        _, schema = self._transport_fixture()
        for key, value in (("$schema", "public-fixture"), ("$ref", "#"), ("anyOf", []),
                           ("allOf", []), ("if", {}), ("description", "public fixture")):
            with self.subTest(keyword=key):
                altered = {**schema, key: value}
                with self.assertRaisesRegex(native.NativeObservationError, "unsupported response transport keyword"):
                    native.validate_response_transport(altered)
        for change in (lambda node: node.__setitem__("additionalProperties", True),
                       lambda node: node["required"].pop(),
                       lambda node: node["required"].append(node["required"][0])):
            altered = copy.deepcopy(schema)
            change(altered)
            with self.assertRaisesRegex(native.NativeObservationError, "not closed"):
                native.validate_response_transport(altered)

    def test_native_response_production_chain_still_rejects_bindings_duplicates_and_mutation(self):
        parent = self.parent
        cases = [
            ("opaque-binding", lambda d: d.__setitem__("opaqueCaseBinding", "0" * 64), "INCOMPLETE", "response-invalid"),
            ("profile-contract-binding", lambda d: d["contractBindings"].__setitem__("profileContractSha256", "0" * 64), "INCOMPLETE", "response-invalid"),
            ("golden-set-binding", lambda d: d["contractBindings"].__setitem__("goldenSetSha256", "0" * 64), "INCOMPLETE", "response-invalid"),
            ("host-case-set-binding", lambda d: d["contractBindings"].__setitem__("hostCaseSetSha256", "0" * 64), "INCOMPLETE", "response-invalid"),
            ("illegal-route", lambda d: d.__setitem__("selectedRoutes", ["not-a-route"]), "INCOMPLETE", "response-invalid"),
            ("wrong-route", lambda d: d.__setitem__("selectedRoutes", ["agents-architect"]), "FAIL", "semantic-mismatch"),
            ("duplicate-route", lambda d: d.__setitem__("selectedRoutes", ["using-axiom", "using-axiom"]), "INCOMPLETE", "response-invalid"),
            ("mutation-attempted", lambda d: d.__setitem__("mutationAttempted", True), "FAIL", "semantic-mismatch"),
        ]
        for name, alter, expected_status, expected_diagnostic in cases:
            with self.subTest(name=name):
                self.parent = parent / name
                self.parent.mkdir()
                def change_response(lines):
                    item = next(entry["item"] for entry in lines if entry.get("item", {}).get("type") == "agent_message")
                    document = json.loads(item["text"])
                    alter(document)
                    item["text"] = json.dumps(document)
                    return lines
                result = self._diagnostic_stream_runner([], tail=change_response)
                self.assertEqual(result["caseResults"][0]["status"], expected_status)
                self.assertEqual(result["caseResults"][0]["diagnostic"], expected_diagnostic)
                self.assertFalse(result["hostClaim"])
                self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_marketplace_local_source_is_relative_and_copied_package_is_bound(self):
        run_root, _, calls = self._prepared_runner()
        marketplace = run_root / "marketplace"
        catalog = json.loads((marketplace / ".agents/plugins/marketplace.json").read_bytes())
        self.assertEqual(catalog["plugins"][0]["source"], {"source": "local", "path": "./plugin"})
        self.assertEqual(native.package_identity(marketplace / "plugin"),
                         self.protocol["bundle"]["packageSha256"])
        self.assertEqual(calls, [])

    def test_discovery_alias_binds_installed_bytes_and_case_eleven_has_none(self):
        run_root, _, calls = self._prepared_runner()
        for ordinal in range(1, 17):
            paths = native._case_paths(run_root, ordinal)
            native._verify_discovery(paths, ordinal != 11)
            if ordinal == 11:
                self.assertFalse(paths["discovery"].exists())
                self.assertFalse(paths["discovery"].is_symlink())
            else:
                self.assertEqual(paths["discovery"].resolve(), paths["package"] / "skills")
                self.assertEqual((paths["discovery"] / "using-axiom/SKILL.md").read_bytes(),
                                 (paths["package"] / "skills/using-axiom/SKILL.md").read_bytes())
        self.assertEqual(calls, [])

    def test_changed_discovery_alias_stops_before_authentication_or_model_launch(self):
        run_root, _, calls = self._prepared_runner()
        paths = native._case_paths(run_root, 1)
        unknown = self.parent / "unowned-skills"
        unknown.mkdir()
        (unknown / "keep.txt").write_bytes(b"preserve")
        paths["discovery"].unlink()
        paths["discovery"].symlink_to(unknown, target_is_directory=True)
        def forbidden(*args, **kwargs):
            self.fail("client must not start after discovery binding changes")
        result = native.run_native_observation(ROOT, run_root, authorize_model_calls=True,
                                               process_runner=forbidden)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["cliLaunchCount"], 0)
        self.assertEqual((unknown / "keep.txt").read_bytes(), b"preserve")
        self.assertEqual(calls, [])

    def test_prepare_to_run_uses_real_validators_and_simulation_never_claims_host_pass(self):
        run_root, runner, calls = self._prepared_runner()
        result = native.run_native_observation(ROOT, run_root, authorize_model_calls=True, process_runner=runner)
        self.assertEqual(calls, list(range(1, 17)))
        self.assertEqual(result["cliLaunchCount"], 16)
        self.assertEqual([item["status"] for item in result["caseResults"]], ["PASS"] * 16)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertFalse(result["hostClaim"])
        self.assertIsNone(result["modelRequestCount"])
        self.assertEqual(result["caseResults"][10]["installation"], "absent")
        self.assertFalse(native._case_paths(run_root, 11)["package"].exists())
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        encoded = (run_root / "normalized-result.json").read_bytes()
        self.assertNotIn(b"thread_id", encoded)
        self.assertNotIn(b"ocb1_", encoded)
        with self.assertRaises(FileExistsError):
            native.run_native_observation(ROOT, run_root, authorize_model_calls=True, process_runner=runner)
        self.assertEqual(calls, list(range(1, 17)))

    def test_unknown_action_ends_batch_without_retry_and_leaves_later_cases_not_run(self):
        run_root, runner, calls = self._prepared_runner(failed_case=3)
        result = native.run_native_observation(ROOT, run_root, authorize_model_calls=True, process_runner=runner)
        self.assertEqual(calls, [1, 2, 3])
        self.assertEqual(result["caseResults"][2]["status"], "INCOMPLETE")
        self.assertEqual([item["status"] for item in result["caseResults"]][3:], ["NOT-RUN"] * 13)
        self.assertEqual(len(list(run_root.glob("attempt-*.json"))), 3)
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_login_commands_do_not_launch_or_read_case_authentication(self):
        run_root, _, _ = self._prepared_runner()
        original_read = native._read
        def guarded_read(path, maximum=legacy.MAX_CONTRACT_BYTES):
            self.assertNotIn("client-home", path.parts)
            return original_read(path, maximum)
        with patch.object(native, "_read", side_effect=guarded_read), patch.object(
                native.subprocess, "Popen", side_effect=AssertionError("unattended login")):
            commands = native.login_commands(ROOT, run_root)
        self.assertEqual(len(commands), 16)
        self.assertEqual(len({item["env"]["CODEX_HOME"] for item in commands}), 16)
        self.assertTrue(all(item["argv"][-1] == "login" for item in commands))

    def test_package_content_drift_is_rejected_before_any_client_launch(self):
        run_root, runner, calls = self._prepared_runner()
        package = native._case_paths(run_root, 1)["package"]
        target = package / "skills/using-axiom/SKILL.md"
        target.write_bytes(target.read_bytes() + b"changed\n")
        result = native.run_native_observation(ROOT, run_root, authorize_model_calls=True, process_runner=runner)
        self.assertEqual(calls, [])
        self.assertEqual(result["caseResults"][0]["diagnostic"], "input-changed")
        self.assertEqual(result["cliLaunchCount"], 0)
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_bounded_process_delivers_stdin_and_observes_real_process_start(self):
        starts = []
        lines = []
        capture = native.bounded_process(
            [sys.executable, "-I", "-B", "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"],
            cwd=self.parent, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
            stdin=b"ordinary fixture\n", started_callback=lambda: starts.append(True), line_callback=lines.append)
        self.assertEqual({k: capture[k] for k in ("returncode", "stdout", "stderr")},
                         {"returncode": 0, "stdout": b"ordinary fixture\n", "stderr": b""})
        self.assertTrue(capture["diagnostics"]["inputFullyDelivered"])
        self.assertEqual(starts, [True])
        self.assertEqual(lines, [b"ordinary fixture"])

    def test_bounded_process_deadline_reaps_child_even_when_output_pipes_are_closed(self):
        for script in ("import time; time.sleep(5)", "import os,time; os.close(1); os.close(2); time.sleep(5)"):
            with self.subTest(script=script), self.assertRaisesRegex(native.NativeDiagnosticError, "timeout"):
                native.bounded_process([sys.executable, "-I", "-B", "-c", script], cwd=self.parent,
                                       env={"PATH": "/usr/bin:/bin"}, timeout=0.1)

    def test_bounded_process_refuses_output_overflow_and_does_not_retain_raw_file(self):
        with self.assertRaisesRegex(native.NativeDiagnosticError, "output-limit"):
            native.bounded_process([sys.executable, "-I", "-B", "-c",
                "import sys; sys.stdout.buffer.write(b'x' * (2 * 1024 * 1024))"],
                cwd=self.parent, env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(list(self.parent.iterdir()), [])

    def _seed_test_auth(self, run):
        source = native._case_paths(run, 1)["home"] / native.AUTH_FILE_NAME
        source.write_bytes(b"public non-secret auth fixture, deliberately not JSON")
        source.chmod(0o600)
        return source

    def test_test_auth_copy_requires_authorization_without_opening_files(self):
        with patch.object(native.os, "open", side_effect=AssertionError("unexpected file access")):
            with self.assertRaisesRegex(native.NativeObservationError, "copy authorization"):
                native.share_test_authentication(ROOT, self.parent / "absent")

    def test_test_auth_copy_is_opaque_private_and_preserves_case_eleven(self):
        run, _, _ = self._prepared_runner()
        source = self._seed_test_auth(run)
        native.share_test_authentication(ROOT, run, authorize_copy=True)
        for ordinal in range(2, 17):
            path = native._case_paths(run, ordinal)["home"] / native.AUTH_FILE_NAME
            self.assertEqual(path.read_bytes(), source.read_bytes())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            owner = json.loads(native._auth_owner(run, ordinal).read_bytes())
            self.assertEqual(set(owner), {"ordinal", "device", "inode"})
        native._verify_discovery(native._case_paths(run, 11), False)
        self.assertFalse(native._case_paths(run, 11)["package"].exists())
        with self.assertRaises(native.NativeObservationError):
            native.share_test_authentication(ROOT, run, authorize_copy=True)

    def test_test_auth_copy_refuses_unknown_destination_before_copying(self):
        run, _, _ = self._prepared_runner()
        self._seed_test_auth(run)
        target = native._case_paths(run, 8)["home"] / native.AUTH_FILE_NAME
        target.write_bytes(b"unowned object")
        with self.assertRaisesRegex(native.NativeObservationError, "unowned"):
            native.share_test_authentication(ROOT, run, authorize_copy=True)
        self.assertEqual(target.read_bytes(), b"unowned object")
        self.assertFalse(native._auth_owner(run, 1).exists())
        self.assertFalse((native._case_paths(run, 2)["home"] / native.AUTH_FILE_NAME).exists())

    def test_test_auth_copy_registration_failure_preserves_created_private_file(self):
        run, _, _ = self._prepared_runner()
        self._seed_test_auth(run)
        original = native._exclusive
        def fail_owner(path, data, mode=0o600):
            if path == native._auth_owner(run, 2):
                raise OSError("fixture registration failure")
            return original(path, data, mode)
        with patch.object(native, "_exclusive", side_effect=fail_owner):
            with self.assertRaisesRegex(OSError, "registration failure"):
                native.share_test_authentication(ROOT, run, authorize_copy=True)
        target = native._case_paths(run, 2)["home"] / native.AUTH_FILE_NAME
        self.assertTrue(target.is_file())
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertFalse((run / native.AUTH_COPY_STATE).exists())

    def test_serial_auth_handoff_uses_latest_exited_case_and_retains_fresh_contexts(self):
        run, runner, calls = self._prepared_runner()
        initial = self._seed_test_auth(run).read_bytes()
        native.share_test_authentication(ROOT, run, authorize_copy=True)
        def refresh(argv, **kwargs):
            ordinal = int(Path(kwargs["cwd"]).parent.name.removeprefix("case-"))
            path = native._case_paths(run, ordinal)["home"] / native.AUTH_FILE_NAME
            expected = initial if ordinal == 1 else f"public refreshed fixture {ordinal - 1}".encode()
            self.assertEqual(path.read_bytes(), expected)
            result = runner(argv, **kwargs)
            if "exec" in argv:
                path.write_bytes(f"public refreshed fixture {ordinal}".encode())
            return result
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                               reuse_test_auth=True, process_runner=refresh)
        self.assertEqual(calls, list(range(1, 17)))
        self.assertEqual(result["authenticationMode"], "serial-test-auth-copy")
        self.assertFalse(result["hostClaim"])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_abnormal_case_stops_auth_handoff_and_preserves_later_seed(self):
        run, runner, calls = self._prepared_runner(failed_case=2)
        initial = self._seed_test_auth(run).read_bytes()
        native.share_test_authentication(ROOT, run, authorize_copy=True)
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                               reuse_test_auth=True, process_runner=runner)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(result["caseResults"][2]["status"], "NOT-RUN")
        self.assertEqual((native._case_paths(run, 3)["home"] / native.AUTH_FILE_NAME).read_bytes(), initial)
        self.assertFalse((run / "attempt-03.json").exists())

    def test_replaced_owned_auth_destination_is_not_overwritten(self):
        run, _, _ = self._prepared_runner()
        self._seed_test_auth(run)
        native.share_test_authentication(ROOT, run, authorize_copy=True)
        destination = native._case_paths(run, 2)["home"] / native.AUTH_FILE_NAME
        replacement = self.parent / "replacement"
        replacement.write_bytes(b"unknown replacement")
        replacement.chmod(0o600)
        replacement.replace(destination)
        with self.assertRaisesRegex(native.NativeObservationError, "ownership changed"):
            native._copy_test_auth(run, 1, 2, create=False)
        self.assertEqual(destination.read_bytes(), b"unknown replacement")

    def test_case_one_replacement_is_rejected_before_any_client_call(self):
        run, _, _ = self._prepared_runner()
        self._seed_test_auth(run)
        native.share_test_authentication(ROOT, run, authorize_copy=True)
        target = native._case_paths(run, 1)["home"] / native.AUTH_FILE_NAME
        replacement = self.parent / "case-one-replacement"
        replacement.write_bytes(b"public unknown replacement")
        replacement.chmod(0o600)
        replacement.replace(target)
        def never_client(*args, **kwargs):
            self.fail("a client received a replaced authentication path")
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                               reuse_test_auth=True, process_runner=never_client)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["cliLaunchCount"], 0)
        self.assertEqual(result["caseResults"][0]["diagnostic"], "authentication-unavailable")
        self.assertFalse((run / "attempt-01.json").exists())
        self.assertEqual(target.read_bytes(), b"public unknown replacement")

    def test_auth_source_opens_are_nonblocking_before_type_validation(self):
        run, _, _ = self._prepared_runner()
        self._seed_test_auth(run)
        original = native.os.open
        observed = []
        def inspect_flags(path, flags, *args, **kwargs):
            if Path(path).name == native.AUTH_FILE_NAME and not flags & native.os.O_CREAT:
                self.assertTrue(flags & native.os.O_NONBLOCK)
                self.assertTrue(flags & native.os.O_NOFOLLOW)
                observed.append(path)
            return original(path, flags, *args, **kwargs)
        with patch.object(native.os, "open", side_effect=inspect_flags):
            native.share_test_authentication(ROOT, run, authorize_copy=True)
            native._copy_test_auth(run, 1, 2, create=False)
        self.assertGreaterEqual(len(observed), 18)

    def test_explicit_other_test_logins_are_retained_but_not_reused(self):
        run, _, _ = self._prepared_runner()
        seed = self._seed_test_auth(run).read_bytes()
        old = {}
        for i in (2, 3):
            path = native._case_paths(run, i)["home"] / native.AUTH_FILE_NAME
            path.write_bytes(f"public other test login {i}".encode())
            path.chmod(0o600)
            old[i] = (path.stat().st_ino, path.read_bytes())
        native.share_test_authentication(ROOT, run, authorize_copy=True, preserve_existing=[2, 3])
        for i in (2, 3):
            paths = native._case_paths(run, i)
            backup = paths["case"] / "retained-auth-before-reuse" / native.AUTH_FILE_NAME
            self.assertEqual((backup.stat().st_ino, backup.read_bytes()), old[i])
            self.assertEqual(backup.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual((paths["home"] / native.AUTH_FILE_NAME).read_bytes(), seed)
        self.assertEqual((native._case_paths(run, 4)["home"] / native.AUTH_FILE_NAME).read_bytes(), seed)

    def test_auth_retention_never_overwrites_a_prior_destination(self):
        run, _, _ = self._prepared_runner()
        self._seed_test_auth(run)
        paths = native._case_paths(run, 2)
        path = paths["home"] / native.AUTH_FILE_NAME
        path.write_bytes(b"public retained test login")
        path.chmod(0o600)
        (paths["case"] / "retained-auth-before-reuse").mkdir()
        with self.assertRaisesRegex(native.NativeObservationError, "retention destination exists"):
            native.share_test_authentication(ROOT, run, authorize_copy=True, preserve_existing=[2])
        self.assertEqual(path.read_bytes(), b"public retained test login")
        self.assertFalse(native._auth_owner(run, 1).exists())


    def _process(self, code, **kwargs):
        return native.bounded_process([sys.executable, "-I", "-B", "-c", code],
            cwd=self.parent, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}, **kwargs)

    def test_process_exit_and_stderr_have_distinct_safe_diagnostics(self):
        cases = [("import sys; sys.exit(7)", "process-exit", "empty", 7),
                 ("import sys; sys.stderr.write('Reading prompt from stdin...\\n')", "none", "known-nonfatal", 0),
                 ("import sys; sys.stderr.write('private fixture\\n')", "unknown-stderr", "unknown", 0)]
        for code, category, stderr, exit_code in cases:
            with self.subTest(category=category):
                if category == "process-exit":
                    with self.assertRaises(native.NativeDiagnosticError) as caught:
                        self._process(code, stdin=b"")
                    facts = caught.exception.facts
                    self.assertEqual((facts["category"], facts["returnCode"]), (category, exit_code))
                    self.assertEqual(facts["stderrClassification"], stderr)
                    continue
                capture = self._process(code, stdin=b"")
                facts = native._capture_facts(capture)
                self.assertEqual((facts["category"], facts["stderrClassification"], facts["returnCode"]),
                                 (category, stderr, exit_code))
                self.assertNotIn("private fixture", json.dumps(facts))
                if category == "none":
                    self.assertEqual(native._successful(capture, "fixture"), b"")
                else:
                    with self.assertRaises(native.NativeDiagnosticError):
                        native._successful(capture, "fixture")

    def test_frozen_stderr_whitelist_does_not_allow_unknown_continuations(self):
        for data in (b"Reading additional input from stdin...\n",
                     b"Could not create otel exporter: public fixture\n",
                     b"WARNING: proceeding, even though we could not create PATH aliases: fixture\n",
                     b"WARNING: failed to clean up stale arg0 temp dirs: fixture\n"):
            self.assertEqual(native._stderr_classification(data), "known-nonfatal")
            self.assertEqual(native._stderr_classification(data + b"unknown continuation\n"), "unknown")
        self.assertEqual(native._stderr_classification(b"WARNING: arbitrary\n"), "unknown")

    def test_host_error_is_observed_without_becoming_success_or_automatic_failure(self):
        document = response(self.cases[0], "ocb1_" + "0" * 64)
        lines = stream(document).splitlines(keepends=True)
        recoverable = event({"type": "error", "message": "private fixture"})
        raw = b"".join(lines[:2] + [recoverable] + lines[2:])
        facts = native._diagnostics()
        for line in raw.splitlines():
            native._observe_line(line, {}, self.parent, facts)
        self.assertIn("error", facts["eventTypes"])
        self.assertEqual(facts["category"], "none")
        self.assertEqual(native.parse_native_jsonl(raw, self.taxonomy, {}, self.parent)[0].terminal_type,
                         "turn.completed")
        failed = event({"type": "turn.failed", "error": {"message": "private fixture"}})
        native._observe_line(failed.rstrip(b"\n"), {}, self.parent, facts)
        self.assertEqual(facts["category"], "host-failure")
        self.assertEqual(facts["officialErrorCode"], "unknown")
        self.assertNotIn("private fixture", json.dumps(facts))
        with self.assertRaises(native.NativeObservationError):
            native.parse_native_jsonl(raw + recoverable, self.taxonomy, {}, self.parent)

    def test_callback_rejection_keeps_capture_counts_exit_and_first_cause(self):
        facts = native._diagnostics()
        raw = event({"type": "unknown-sensitive-fixture"})
        with self.assertRaises(native.NativeDiagnosticError) as caught:
            self._process("import sys,time; sys.stdout.buffer.write(" + repr(raw) +
                          "); sys.stdout.flush(); time.sleep(5)",
                stdin=b"public input", line_callback=lambda line: native._observe_line(line, {}, self.parent, facts))
        captured = caught.exception.facts
        self.assertEqual(captured["category"], "policy-rejected")
        self.assertGreater(captured["stdoutBytes"], 0)
        self.assertTrue(captured["observerTerminated"])
        self.assertIsNotNone(captured["returnCode"])
        self.assertEqual(facts["eventTypes"], ["unknown"])
        self.assertNotIn("sensitive", str(caught.exception))

    def test_timeout_and_cleanup_failure_preserve_first_cause(self):
        original = native._close_process
        def cleanup(process, **kwargs):
            original(process, **kwargs)
            raise OSError("private cleanup fixture")
        with patch.object(native, "_close_process", side_effect=cleanup):
            with self.assertRaises(native.NativeDiagnosticError) as caught:
                self._process("import time; time.sleep(5)", timeout=0.05)
        self.assertEqual(caught.exception.facts["category"], "timeout")
        self.assertTrue(caught.exception.facts["timedOut"])
        self.assertTrue(caught.exception.facts["cleanupFailed"])
        self.assertNotIn("private", str(caught.exception))
        with patch.object(native, "_close_process", side_effect=cleanup):
            with self.assertRaises(native.NativeDiagnosticError) as caught:
                self._process("pass")
        self.assertEqual(caught.exception.facts["category"], "cleanup-failed")

    def test_production_runner_preserves_host_failure_and_stops_later_cases(self):
        run, runner, calls = self._prepared_runner()
        def fail(argv, **kwargs):
            if "exec" not in argv:
                return runner(argv, **kwargs)
            code = "import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write(" + repr(
                event({"type": "thread.started", "thread_id": "019784a7-ec72-7000-8000-000000000001"}) +
                event({"type": "turn.started"}) + event({"type": "error", "message": "not retained"}) +
                event({"type": "turn.failed", "error": {"message": "not retained"}})) + "); sys.exit(1)"
            return native.bounded_process([sys.executable, "-I", "-B", "-c", code], **kwargs)
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True, process_runner=fail)
        first = result["caseResults"][0]
        self.assertEqual(first["diagnostic"], "host-failure")
        self.assertEqual(first["terminal"], "turn.failed")
        self.assertEqual(first["executionDiagnostics"]["returnCode"], 1)
        self.assertTrue(first["executionDiagnostics"]["inputFullyDelivered"])
        self.assertEqual(result["attemptCount"], 1)
        self.assertEqual([r["status"] for r in result["caseResults"]][1:], ["NOT-RUN"] * 15)
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_production_runner_retains_truncated_and_missing_terminal_diagnostics(self):
        parent = self.parent
        for mode in ("truncated", "missing-terminal"):
            with self.subTest(mode=mode):
                self.parent = parent / mode
                self.parent.mkdir()
                run, runner, _ = self._prepared_runner()
                def truncate(argv, **kwargs):
                    capture = runner(argv, **kwargs)
                    if "exec" in argv:
                        capture["stdout"] = (capture["stdout"][:-1] if mode == "truncated" else
                                             b"\n".join(capture["stdout"].splitlines()[:-1]) + b"\n")
                    return capture
                result = native.run_native_observation(ROOT, run, authorize_model_calls=True, process_runner=truncate)
                self.assertEqual(result["caseResults"][0]["diagnostic"], "stream-invalid")
                self.assertEqual(native.validate_native_result(result, ROOT), [])
                # Each subcase owns an independent secret-free preparation.
                shutil.rmtree(run)

    def test_historical_result_is_immutable_and_not_revalidated_as_new_diagnostics(self):
        history = json.loads((ROOT / native.HISTORY_RELATIVE).read_bytes())
        old = history["historicalResults"][0]
        data = (ROOT / old["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), native.HISTORICAL_RESULT_SHA256)
        document = json.loads(data)
        self.assertNotIn("executionDiagnostics", document["caseResults"][0])
        self.assertEqual(document["caseResults"][0]["diagnostic"], "execution-failed")
        self.assertTrue(native.validate_native_result(document, ROOT))

    def _historical_preparation(self):
        run, runner, calls = self._prepared_runner()
        history = json.loads((ROOT / native.HISTORY_RELATIVE).read_bytes())
        old_bytes = (ROOT / history["historicalResults"][0]["path"]).read_bytes()
        old_result = json.loads(old_bytes)
        state = json.loads((run / native.STATE_NAME).read_bytes())
        state.update(runMode="actual", protocolDigest=native.HISTORICAL_PROTOCOL_DIGEST,
                     materializationSeed=old_result["materializationSeed"])
        (run / native.STATE_NAME).write_bytes(native._bytes(state))
        for ordinal, case in enumerate(self.cases, 1):
            material = legacy.materialize_case_contract(materialization_seed=bytes.fromhex(state["materializationSeed"]),
                ordinal=ordinal, protocol_digest=native.HISTORICAL_PROTOCOL_DIGEST,
                model_schema=native._input(ROOT, self.protocol, "modelResponseSchema"),
                prompt_envelope=native._input(ROOT, self.protocol, "promptEnvelope"), request=case["request"])
            (native._case_paths(run, ordinal)["case"] / "response-schema.json").write_bytes(material.schema_bytes)
        native._exclusive(run / "normalized-result.json", old_bytes)
        native._exclusive(run / "batch-started.json", native._bytes({"protocolDigest": native.HISTORICAL_PROTOCOL_DIGEST}))
        native._exclusive(run / "attempt-01.json", native._bytes({"ordinal": 1, "caseId": self.cases[0]["id"],
                                                               "protocolDigest": native.HISTORICAL_PROTOCOL_DIGEST}))
        return run, runner, calls

    def test_followup_preserves_history_binds_new_inputs_and_counts_seventeen(self):
        run, runner, calls = self._historical_preparation()
        names = ["normalized-result.json", "batch-started.json", "attempt-01.json", native.STATE_NAME]
        original = {name: (run / name).read_bytes() for name in names}
        old_schema = (native._case_paths(run, 1)["case"] / "response-schema.json").read_bytes()
        native.prepare_diagnostic_followup(ROOT, run)
        self.assertNotEqual(old_schema, (run / "diagnostic-followup/response-schema-01.json").read_bytes())
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                               followup=True, process_runner=runner)
        self.assertEqual(calls, list(range(1, 17)))
        self.assertEqual(result["attemptCount"], 16)
        self.assertEqual(result["cumulativeAttemptCount"], 17)
        self.assertEqual(result["priorResultSha256s"], [native.HISTORICAL_RESULT_SHA256])
        self.assertFalse(result["hostClaim"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        for name in names:
            self.assertEqual((run / name).read_bytes(), original[name])
        with self.assertRaises(FileExistsError):
            native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                          followup=True, process_runner=runner)
        with self.assertRaises(FileExistsError):
            native.prepare_diagnostic_followup(ROOT, run)
        self.assertEqual(len(calls), 16)

    def test_followup_refuses_consumed_later_case_and_changed_prior_record(self):
        run, _, _ = self._historical_preparation()
        native._exclusive(run / "attempt-02.json", b"{}")
        with self.assertRaisesRegex(native.NativeObservationError, "already consumed"):
            native.prepare_diagnostic_followup(ROOT, run)
        self.assertFalse((run / "diagnostic-followup").exists())
        (run / "normalized-result.json").write_bytes(b"{}")
        with self.assertRaisesRegex(native.NativeObservationError, "original incomplete"):
            native.prepare_diagnostic_followup(ROOT, run)

    def test_callback_parse_failure_and_process_start_failure_are_distinct(self):
        facts = native._diagnostics()
        with self.assertRaises(native.NativeDiagnosticError) as caught:
            self._process("print('not-json')", line_callback=lambda line: native._observe_line(line, {}, self.parent, facts))
        self.assertEqual(caught.exception.facts["category"], "event-invalid")
        with self.assertRaises(native.NativeDiagnosticError) as caught:
            native.bounded_process([str(self.parent / "absent")], cwd=self.parent, env={})
        self.assertEqual(caught.exception.facts["category"], "process-start")
        self.assertIsNone(caught.exception.facts["returnCode"])

    def test_nonzero_exit_is_not_overwritten_by_cleanup_failure(self):
        original = native._close_process
        def cleanup(process, **kwargs):
            original(process, **kwargs)
            raise OSError("secret-free fixture")
        with patch.object(native, "_close_process", side_effect=cleanup):
            with self.assertRaises(native.NativeDiagnosticError) as caught:
                self._process("import sys; sys.exit(7)")
        self.assertEqual(caught.exception.facts["category"], "process-exit")
        self.assertEqual(caught.exception.facts["returnCode"], 7)
        self.assertTrue(caught.exception.facts["cleanupFailed"])

    def test_selector_setup_failure_counts_and_reaps_created_process(self):
        starts, children = [], []
        original = native._close_process
        def close(process, **kwargs):
            children.append(process)
            return original(process, **kwargs)
        with patch.object(native.selectors, "DefaultSelector", side_effect=OSError("public fixture")), \
                patch.object(native, "_close_process", side_effect=close):
            with self.assertRaises(native.NativeDiagnosticError) as caught:
                self._process("import time; time.sleep(5)", started_callback=lambda: starts.append(1))
        self.assertEqual(starts, [1])
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())
        self.assertEqual(caught.exception.facts["category"], "io-failed")
        self.assertTrue(caught.exception.facts["observerTerminated"])

    def test_completed_result_rejects_policy_and_item_diagnostic_contradictions(self):
        run, runner, _ = self._prepared_runner()
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True, process_runner=runner)
        for field, value in (("policyReason", "read-contract-rejected"),
                             ("itemTypes", ["unsupported"]), ("itemTypes", ["error"]),
                             ("inputBytesSent", 0), ("finalOutputVerified", False),
                             ("streamAssertion", "final-message-invalid-json"), ("streamEventOrdinal", 1)):
            altered = copy.deepcopy(result)
            altered["caseResults"][0]["executionDiagnostics"][field] = value
            self.assertTrue(native.validate_native_result(altered, ROOT), field)
        altered = copy.deepcopy(result)
        altered["caseResults"][0]["executionDiagnostics"]["eventTypes"] = ["thread.started", "turn.started", "turn.completed"]
        self.assertTrue(native.validate_native_result(altered, ROOT))

    def _diagnostic_stream_runner(self, messages, *, before_turn=True, malformed=None, exit_code=0, stderr=b"", tail=None, private=False, operator=False, schema_followup=False, final_output_mode="match", final_output_transform=None):
        run, runner, calls = (self._fourth_prior_fixture() if schema_followup else
                              self._third_prior_fixture() if operator else self._prepared_runner())
        if operator or schema_followup:
            native.prepare_diagnostic_followup(ROOT, run, operator_diagnostics=operator, schema_followup=schema_followup)
        def diagnostic_runner(argv, **kwargs):
            if "exec" not in argv:
                return runner(argv, **kwargs)
            capture = runner(argv, **{**kwargs, "line_callback": None})
            lines = [json.loads(line) for line in capture["stdout"].splitlines()]
            for entry in lines:
                if "item" in entry:
                    number = int(entry["item"]["id"].removeprefix("item_"))
                    entry["item"]["id"] = f"item_{number + len(messages)}"
            diagnostics = [{"type": "item.completed", "item": {
                "id": f"item_{i}", "type": "error", "message": message}}
                for i, message in enumerate(messages)]
            offset = 1 if before_turn else 2
            lines[offset:offset] = diagnostics
            if tail:
                lines = tail(lines)
            if malformed:
                malformed(lines)
            final_output = Path(argv[argv.index("--output-last-message") + 1])
            last_message = next((entry["item"]["text"] for entry in reversed(lines)
                                 if entry.get("type") == "item.completed" and
                                 type(entry.get("item")) is dict and
                                 entry["item"].get("type") == "agent_message" and
                                 type(entry["item"].get("text")) is str), None)
            if final_output_mode == "missing":
                final_output.unlink()
            elif final_output_mode == "different":
                final_output.write_bytes(b'{"different": "public final-output fixture"}\n')
            elif final_output_mode == "reformatted":
                document = json.loads(last_message)
                reordered = dict(reversed(list(document.items())))
                final_output.write_bytes(b"\n  " + json.dumps(reordered, indent=3).encode("utf-8") + b"\n\t")
            elif final_output_mode == "match":
                final_output.write_bytes((last_message + "\n").encode("utf-8")
                                         if last_message is not None and lines[-1]["type"] == "turn.completed" else b"")
            else:
                self.fail("unknown final-output fixture mode")
            if final_output_transform is not None:
                document = json.loads(final_output.read_bytes())
                final_output.write_bytes(event(final_output_transform(document)))
            raw = b"".join(event(entry) for entry in lines)
            # A real ordinary child exercises capture -> receiver -> parser ->
            # result validation; it cannot launch a client or access real auth.
            code = ("import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write(" + repr(raw) +
                    "); sys.stderr.buffer.write(" + repr(stderr) + "); sys.exit(" + str(exit_code) + ")")
            return native.bounded_process([sys.executable, "-I", "-B", "-c", code], **kwargs)
        return native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                             process_runner=diagnostic_runner, private_diagnostics=private,
                                             operator_diagnostics=operator, schema_followup=schema_followup)

    def _two_historical_preparations(self):
        run, runner, calls = self._historical_preparation()
        state = json.loads((run / native.STATE_NAME).read_bytes())
        ledger = run / "diagnostic-followup"
        ledger.mkdir()
        history = json.loads((ROOT / native.HISTORY_RELATIVE).read_bytes())
        (ledger / "normalized-result.json").write_bytes((ROOT / history["historicalResults"][1]["path"]).read_bytes())
        (ledger / "preparation.json").write_bytes(native._bytes({**state, "protocolDigest": native.RETRY_PROTOCOL_DIGEST}))
        (ledger / "batch-started.json").write_bytes(native._bytes({"protocolDigest": native.RETRY_PROTOCOL_DIGEST}))
        (ledger / "attempt-01.json").write_bytes(native._bytes({"ordinal": 1, "caseId": self.cases[0]["id"],
                                                              "protocolDigest": native.RETRY_PROTOCOL_DIGEST}))
        for ordinal, case in enumerate(self.cases, 1):
            material = legacy.materialize_case_contract(materialization_seed=bytes.fromhex(state["materializationSeed"]),
                ordinal=ordinal, protocol_digest=native.RETRY_PROTOCOL_DIGEST,
                model_schema=native._input(ROOT, self.protocol, "modelResponseSchema"),
                prompt_envelope=native._input(ROOT, self.protocol, "promptEnvelope"), request=case["request"])
            (ledger / f"response-schema-{ordinal:02d}.json").write_bytes(material.schema_bytes)
        return run, runner, calls

    def _third_prior_fixture(self):
        """Recreate only public historical records and secret-free inputs."""
        run, runner, calls = self._two_historical_preparations()
        state = json.loads((run / native.STATE_NAME).read_bytes())
        ledger = run / "diagnostic-continuation"
        ledger.mkdir()
        history = json.loads((ROOT / native.HISTORY_RELATIVE).read_bytes())
        (ledger / "normalized-result.json").write_bytes(
            (ROOT / history["historicalResults"][2]["path"]).read_bytes())
        (ledger / "preparation.json").write_bytes(native._bytes({
            **state, "protocolDigest": native.THIRD_PROTOCOL_DIGEST}))
        (ledger / "batch-started.json").write_bytes(native._bytes({
            "protocolDigest": native.THIRD_PROTOCOL_DIGEST}))
        (ledger / "attempt-01.json").write_bytes(native._bytes({
            "ordinal": 1, "caseId": self.cases[0]["id"], "protocolDigest": native.THIRD_PROTOCOL_DIGEST}))
        for ordinal, case in enumerate(self.cases, 1):
            material = legacy.materialize_case_contract(
                materialization_seed=bytes.fromhex(state["materializationSeed"]),
                ordinal=ordinal, protocol_digest=native.THIRD_PROTOCOL_DIGEST,
                model_schema=native._input(ROOT, self.protocol, "modelResponseSchema"),
                prompt_envelope=native._input(ROOT, self.protocol, "promptEnvelope"), request=case["request"])
            (ledger / f"response-schema-{ordinal:02d}.json").write_bytes(material.schema_bytes)
        return run, runner, calls

    def _fourth_prior_fixture(self):
        """Preserve the fourth public result under its original schema contract."""
        run, runner, calls = self._third_prior_fixture()
        state = json.loads((run / native.STATE_NAME).read_bytes())
        ledger = run / "operator-diagnostic-continuation"
        ledger.mkdir()
        history = json.loads((ROOT / native.HISTORY_RELATIVE).read_bytes())
        (ledger / "normalized-result.json").write_bytes(
            (ROOT / history["historicalResults"][3]["path"]).read_bytes())
        (ledger / "preparation.json").write_bytes(native._bytes({
            **state, "protocolDigest": native.FOURTH_PROTOCOL_DIGEST}))
        (ledger / "batch-started.json").write_bytes(native._bytes({
            "protocolDigest": native.FOURTH_PROTOCOL_DIGEST}))
        (ledger / "attempt-01.json").write_bytes(native._bytes({
            "ordinal": 1, "caseId": self.cases[0]["id"], "protocolDigest": native.FOURTH_PROTOCOL_DIGEST}))
        for ordinal, case in enumerate(self.cases, 1):
            material = legacy.materialize_case_contract(
                materialization_seed=bytes.fromhex(state["materializationSeed"]),
                ordinal=ordinal, protocol_digest=native.FOURTH_PROTOCOL_DIGEST,
                model_schema=native._input(ROOT, self.protocol, "modelResponseSchema"),
                prompt_envelope=native._input(ROOT, self.protocol, "promptEnvelope"), request=case["request"])
            (ledger / f"response-schema-{ordinal:02d}.json").write_bytes(material.schema_bytes)
        return run, runner, calls

    def test_continuation_preserves_two_histories_and_caps_cumulative_eighteen(self):
        run, runner, calls = self._two_historical_preparations()
        names = ["normalized-result.json", "attempt-01.json", "batch-started.json",
                 "diagnostic-followup/normalized-result.json", "diagnostic-followup/attempt-01.json",
                 "diagnostic-followup/batch-started.json", "diagnostic-followup/preparation.json"]
        before = {name: (run / name).read_bytes() for name in names}
        native.prepare_diagnostic_followup(ROOT, run, continuation=True)
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                              continuation=True, process_runner=runner)
        self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"], result["cliLaunchCount"]), (16, 18, 16))
        self.assertEqual(result["priorResultSha256s"], native.PRIOR_RESULTS[:2])
        self.assertEqual(calls, list(range(1, 17)))
        self.assertFalse(result["hostClaim"])
        self.assertIsNone(result["modelRequestCount"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        for name, data in before.items():
            self.assertEqual((run / name).read_bytes(), data)
        with self.assertRaises(FileExistsError):
            native.run_native_observation(ROOT, run, authorize_model_calls=True, continuation=True, process_runner=runner)
        self.assertEqual(len(calls), 16)
        for change in (lambda d: d.__setitem__("cumulativeAttemptCount", 17),
                       lambda d: d.__setitem__("priorResultSha256s", list(reversed(native.PRIOR_RESULTS[:2])))):
            altered = copy.deepcopy(result)
            change(altered)
            self.assertTrue(native.validate_native_result(altered, ROOT))

    def test_continuation_rejects_consumed_case_or_changed_second_result(self):
        run, _, _ = self._two_historical_preparations()
        (run / "diagnostic-followup/attempt-02.json").write_bytes(b"{}")
        with self.assertRaisesRegex(native.NativeObservationError, "already consumed"):
            native.prepare_diagnostic_followup(ROOT, run, continuation=True)
        self.assertFalse((run / "diagnostic-continuation").exists())
        (run / "diagnostic-followup/normalized-result.json").write_bytes(b"{}")
        with self.assertRaisesRegex(native.NativeObservationError, "second immutable"):
            native.prepare_diagnostic_followup(ROOT, run, continuation=True)

    def test_unknown_diagnostic_retains_independently_validated_partial_evidence(self):
        result = self._diagnostic_stream_runner(["invalid global instructions"])
        case = result["caseResults"][0]
        self.assertEqual(case["status"], "INCOMPLETE")
        self.assertEqual(case["evidenceExtraction"], {"stream": "valid", "response": "valid", "postcheck": "valid"})
        self.assertIsNotNone(case["observed"])
        self.assertEqual(case["readonlyCommandCount"], 1)
        self.assertEqual(case["fixtureAfterSha256"], case["fixtureBeforeSha256"])
        self.assertEqual(case["packageAfterSha256"], case["packageBeforeSha256"])
        self.assertEqual(case["terminal"], "turn.completed")
        self.assertFalse(result["hostClaim"])
        changed = copy.deepcopy(result)
        changed["caseResults"][0]["observed"]["extra"] = "unverified"
        self.assertTrue(native.validate_native_result(changed, ROOT))
        changed = copy.deepcopy(result)
        changed["caseResults"][0]["evidenceExtraction"]["response"] = "not-checked"
        self.assertTrue(native.validate_native_result(changed, ROOT))

    def test_private_summaries_are_capped_private_and_never_copy_dynamic_secrets(self):
        collector = native.PrivateDiagnostics(self.parent)
        secret = "SECRET-FIXTURE-not-an-actual-credential"
        messages = [secret, "Model metadata for `" + secret + "` not found. Defaulting to fallback metadata; this can degrade performance and cause issues.",
                    "Configured value for `permission_profile` is disallowed by requirements; falling back to required value '" + secret + "'. Details: /private/" + secret,
                    "Under-development features enabled: " + secret + ". Under-development features are incomplete and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in /private/" + secret + ".",
                    "Model metadata for `gpt-5.6-sol` not found. Defaulting to fallback metadata; this can degrade performance and cause issues."]
        for _ in range(100):
            for message in messages:
                collector.message(1, message)
        collector.stderr(1, b"unknown " + secret.encode() + b"\n")
        collector.save()
        path = collector.directory / "case-01.txt"
        data = path.read_bytes()
        self.assertLessEqual(len(data), 16384)
        self.assertNotIn(secret.encode(), data)
        self.assertNotIn(b"/private/", data)
        self.assertIn(b"model-metadata-fallback; configured model gpt-5.6-sol", data)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(collector.directory.stat().st_mode & 0o777, 0o700)
        with self.assertRaises(FileExistsError):
            native.PrivateDiagnostics(self.parent)

    def test_private_diagnostic_production_chain_does_not_turn_unknown_into_pass(self):
        result = self._diagnostic_stream_runner([
            "Model metadata for `gpt-5.6-sol` not found. Defaulting to fallback metadata; this can degrade performance and cause issues."
        ], private=True)
        first = result["caseResults"][0]
        self.assertEqual(first["diagnostic"], "diagnostic-unknown")
        self.assertIsNotNone(first["observed"])
        self.assertNotIn("Model metadata", json.dumps(result))
        summaries = list(self.parent.glob("**/private-diagnostics/case-01.txt"))
        self.assertEqual(len(summaries), 1)
        self.assertIn("model-metadata-fallback", summaries[0].read_text())

    def test_error_item_before_turn_is_received_and_closed_without_unsupported_item(self):
        raw = stream(response(self.cases[0], "ocb1_" + "0" * 64))
        lines = [json.loads(line) for line in raw.splitlines()]
        lines[2]["item"]["id"] = "item_1"
        lines.insert(1, {"type": "item.completed", "item": {
            "id": "item_0", "type": "error", "message": "invalid global instructions"}})
        raw = b"".join(event(line) for line in lines)
        facts = native._diagnostics()
        for line in raw.splitlines():
            native._observe_line(line, {}, self.parent, facts)
        parsed, count = native.parse_native_jsonl(raw, self.taxonomy, {}, self.parent)
        self.assertEqual(parsed.item_types, ("error", "agent_message"))
        self.assertEqual(parsed.terminal_type, "turn.completed")
        self.assertEqual(count, 0)
        self.assertEqual(facts["policyReason"], "none")

    def test_unknown_error_item_reaches_production_result_as_incomplete(self):
        result = self._diagnostic_stream_runner(["invalid global instructions"])
        first = result["caseResults"][0]
        self.assertEqual(first["diagnostic"], "diagnostic-unknown")
        self.assertEqual(first["executionDiagnostics"]["policyReason"], "none")
        self.assertFalse(first["executionDiagnostics"]["observerTerminated"])
        self.assertEqual(first["executionDiagnostics"]["returnCode"], 0)
        self.assertEqual(first["terminal"], "turn.completed")
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        self.assertEqual([x["status"] for x in result["caseResults"]], ["INCOMPLETE"] + ["NOT-RUN"] * 15)
        self.assertNotIn("invalid global instructions", json.dumps(result))

    def test_model_rerouting_cannot_pass_even_with_completed_turn_and_zero_exit(self):
        result = self._diagnostic_stream_runner(["model rerouted: gpt-5.6-sol -> other-model (HighRisk)"], before_turn=False)
        first = result["caseResults"][0]
        self.assertEqual(first["status"], "INCOMPLETE")
        self.assertEqual(first["diagnostic"], "model-mismatch")
        self.assertEqual(first["terminal"], "turn.completed")
        self.assertEqual(first["executionDiagnostics"]["returnCode"], 0)
        self.assertEqual(first["executionDiagnostics"]["hostDiagnosticClasses"], ["model-rerouted"])
        self.assertEqual(first["executionDiagnostics"]["officialErrorCode"], "unknown")
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        self.assertNotIn("other-model", json.dumps(result))

    def test_multiple_diagnostic_items_keep_shared_ids_and_finite_safe_summary(self):
        result = self._diagnostic_stream_runner(["unknown first", "unknown second"], before_turn=False)
        first = result["caseResults"][0]
        self.assertEqual(first["terminal"], "turn.completed")
        self.assertEqual(first["executionDiagnostics"]["diagnosticItemCount"], 2)
        self.assertEqual(first["executionDiagnostics"]["preTurnDiagnosticCount"], 0)
        self.assertEqual(first["executionDiagnostics"]["hostDiagnosticClasses"], ["unknown"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_error_item_lifecycle_rejects_duplicate_skipped_and_reused_ids(self):
        parent = self.parent
        changes = {
            "duplicate": lambda lines: lines.insert(2, copy.deepcopy(lines[1])),
            "gap": lambda lines: lines[1]["item"].__setitem__("id", "item_2"),
            "reused": lambda lines: lines[3]["item"].__setitem__("id", "item_0"),
            "started": lambda lines: lines[1].__setitem__("type", "item.started"),
            "extra-field": lambda lines: lines[1]["item"].__setitem__("raw", "private fixture"),
            "after-terminal": lambda lines: lines.append(copy.deepcopy(lines[1])),
            "before-thread": lambda lines: lines.insert(0, lines.pop(1)),
        }
        for mode, change in changes.items():
            with self.subTest(mode=mode):
                self.parent = parent / mode
                self.parent.mkdir()
                result = self._diagnostic_stream_runner(["unknown"], malformed=change)
                first = result["caseResults"][0]
                self.assertEqual(first["status"], "INCOMPLETE")
                self.assertIn(first["diagnostic"], {"stream-invalid", "policy-rejected"})
                self.assertEqual(native.validate_native_result(result, ROOT), [])
                self.assertEqual(result["attemptCount"], 1)

    def test_error_diagnostics_do_not_hide_process_stderr_or_terminal_failure(self):
        parent = self.parent
        modes = [("nonzero", 7, b"", None, "process-exit"),
                 ("stderr", 0, b"unknown fixture\n", None, "unknown-stderr"),
                 ("failed", 1, b"", lambda lines: lines[:3] + [
                     {"type": "error", "message": "not retained"},
                     {"type": "turn.failed", "error": {"message": "not retained"}}], "host-failure"),
                 ("top-error", 0, b"", lambda lines: lines[:1] + [
                     {"type": "error", "message": "not retained"}] + lines[1:], "diagnostic-unknown")]
        for name, code, stderr, tail, expected in modes:
            with self.subTest(mode=name):
                self.parent = parent / name
                self.parent.mkdir()
                result = self._diagnostic_stream_runner([], exit_code=code, stderr=stderr, tail=tail)
                self.assertEqual(result["caseResults"][0]["diagnostic"], expected)
                self.assertEqual(native.validate_native_result(result, ROOT), [])
                self.assertNotIn("not retained", json.dumps(result))

    def test_diagnostic_result_counters_and_classes_cannot_be_forged_as_complete(self):
        result = self._diagnostic_stream_runner(["unknown"])
        for field, value in (("diagnosticItemCount", 0), ("preTurnDiagnosticCount", 2),
                             ("hostDiagnosticClasses", []), ("officialErrorCode", "invented")):
            altered = copy.deepcopy(result)
            altered["caseResults"][0]["executionDiagnostics"][field] = value
            self.assertTrue(native.validate_native_result(altered, ROOT), field)
        first = result["caseResults"][0]
        first.update(status="PASS", diagnostic="none")
        first["executionDiagnostics"].update(category="none", phase="none")
        self.assertTrue(native.validate_native_result(result, ROOT))

    def test_four_historical_attempts_keep_exact_original_bytes_and_protocols(self):
        history = json.loads((ROOT / native.HISTORY_RELATIVE).read_bytes())
        self.assertEqual(len(history["historicalResults"]), 4)
        self.assertEqual(sum(record["attemptCount"] for record in history["historicalResults"]), 4)
        self.assertEqual([record["sha256"] for record in history["historicalResults"]], native.PRIOR_RESULTS)
        self.assertEqual([record["protocolDigest"] for record in history["historicalResults"]], [
            native.HISTORICAL_PROTOCOL_DIGEST, native.RETRY_PROTOCOL_DIGEST,
            native.THIRD_PROTOCOL_DIGEST, native.FOURTH_PROTOCOL_DIGEST])
        historical = []
        for record in history["historicalResults"]:
            data = (ROOT / record["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
            result = json.loads(data)
            self.assertEqual(result["protocolDigest"], record["protocolDigest"])
            self.assertEqual(result["caseResults"][0]["status"], "INCOMPLETE")
            self.assertEqual([case["status"] for case in result["caseResults"]][1:], ["NOT-RUN"] * 15)
            self.assertLess(result.get("diagnosticRevision", 0), 5)
            historical.append(result)
        # Historical bytes retain their old contracts; do not run them through
        # the current transport adapter or fill in new revision-5 facts.
        result = historical[2]
        self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"]), (1, 3))
        self.assertEqual(result["priorResultSha256s"], native.PRIOR_RESULTS[:2])
        self.assertEqual(result["caseResults"][0]["diagnostic"], "host-failure")
        self.assertEqual([c["status"] for c in result["caseResults"]], ["INCOMPLETE"] + ["NOT-RUN"] * 15)
        self.assertEqual(history["historicalResults"][2]["implementationTree"],
                         "82d09603eaa18acd415e8972729b5e429255781e")
        self.assertEqual((historical[3]["attemptCount"], historical[3]["cumulativeAttemptCount"]), (1, 4))
        self.assertEqual(historical[3]["priorResultSha256s"], native.PRIOR_RESULTS[:3])
        if history["results"]:
            self.assertEqual(len(history["results"]), 1)
            current = history["results"][0]
            data = (ROOT / current["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), current["sha256"])
            result = json.loads(data)
            if result["diagnosticRevision"] == 5:
                # The fifth retained attempt was evaluated by its original
                # parser. New assertions cannot reconstruct its discarded flow.
                self.assertEqual(current["sha256"],
                                 "7edd7ab7068f85525074b10f874b325c066a35de183048b037f78f5a9286b018")
                self.assertEqual(result["protocolDigest"],
                                 "sha256:59170c119dca1de340c286c5502d2176c222deb0c34784b5c19d30cc091d4b6d")
                self.assertEqual(current["implementationCommit"], "c3ce63d789394f60e93687ec34db05be199fbc19")
                self.assertEqual(current["implementationTree"], "be21ad749edb25e4fb832bce7debe9e0fa75175b")
                self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"]), (1, 5))
                self.assertEqual([case["status"] for case in result["caseResults"]],
                                 ["INCOMPLETE"] + ["NOT-RUN"] * 15)
                self.assertFalse(result["hostClaim"])
                self.assertNotIn("streamAssertion", result["caseResults"][0]["executionDiagnostics"])
            else:
                self.assertEqual(result["diagnosticRevision"], 6)
                self.assertEqual(native.validate_native_result(result, ROOT), [])
            self.assertEqual(result["priorResultSha256s"], native.PRIOR_RESULTS)
            self.assertEqual(result["runMode"], "actual")
            self.assertEqual(history["current"], {"codexObservation": result["status"].lower(),
                "hostClaim": result["hostClaim"], "credentialUsed": result["cliLaunchCount"] > 0,
                "cliLaunchCount": result["cliLaunchCount"], "modelRequestCount": None,
                "pluginInstalled": any(case["installation"] == "verified" for case in result["caseResults"])})
        else:
            self.assertEqual(history["current"], {"codexObservation": "not-run", "hostClaim": False,
                "credentialUsed": False, "cliLaunchCount": 0, "modelRequestCount": None, "pluginInstalled": False})

    def test_frozen_configuration_and_event_loss_templates_block_acceptance(self):
        parent = self.parent
        examples = [
            ("Configured value for `permission_profile` is disallowed by requirements; falling back to required value ReadOnly. Details: public fixture", "configuration-unverified"),
            ("Error parsing rules; custom rules not applied. (public fixture)", "configuration-unverified"),
            ("`--dangerously-bypass-hook-trust` is enabled. Enabled hooks may run without review for this invocation.", "configuration-unverified"),
            ("in-process app-server event stream lagged; dropped 3 events", "evidence-incomplete"),
            ("thread/rollback is deprecated and will be removed soon", "diagnostic-unknown"),
        ]
        for index, (message, expected) in enumerate(examples):
            with self.subTest(expected=expected, index=index):
                self.parent = parent / str(index)
                self.parent.mkdir()
                result = self._diagnostic_stream_runner([message])
                first = result["caseResults"][0]
                self.assertEqual(first["status"], "INCOMPLETE")
                self.assertEqual(first["diagnostic"], expected)
                self.assertEqual(first["terminal"], "turn.completed")
                self.assertEqual(first["executionDiagnostics"]["preTurnDiagnosticCount"], 1)
                self.assertEqual(first["executionDiagnostics"]["officialErrorCode"], "unknown")
                self.assertEqual(native.validate_native_result(result, ROOT), [])
                self.assertNotIn("public fixture", json.dumps(result))

    def test_complete_normal_stream_and_known_stderr_still_pass_simulated_cases(self):
        result = self._diagnostic_stream_runner([], stderr=b"Reading prompt from stdin...\n")
        self.assertEqual([case["status"] for case in result["caseResults"]], ["PASS"] * 16)
        self.assertEqual(result["caseResults"][10]["installation"], "absent")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertFalse(result["hostClaim"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_production_commentary_and_final_output_preserve_normal_simulated_cases(self):
        def add_commentary(lines):
            index = next(index for index, entry in enumerate(lines)
                         if entry.get("item", {}).get("type") == "agent_message")
            identifier = int(lines[index]["item"]["id"].removeprefix("item_"))
            lines[index]["item"]["id"] = f"item_{identifier + 1}"
            lines.insert(index, {"type": "item.completed", "item": {
                "id": f"item_{identifier}", "type": "agent_message",
                "text": "Public commentary fixture before the final response."}})
            return lines
        result = self._diagnostic_stream_runner([], tail=add_commentary)
        self.assertEqual([case["status"] for case in result["caseResults"]], ["PASS"] * 16)
        self.assertEqual(result["caseResults"][0]["readonlyCommandCount"], 1)
        self.assertEqual(result["caseResults"][10]["installation"], "absent")
        self.assertEqual(result["runMode"], "simulated")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertFalse(result["hostClaim"])
        self.assertEqual(len(self.synthetic_final_outputs), 16)
        self.assertTrue(all(not path.exists() for path in self.synthetic_final_outputs))
        self.assertNotIn("Public commentary fixture", json.dumps(result))
        self.assertNotIn(str(self.parent), json.dumps(result))
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_production_uses_last_json_even_when_an_earlier_response_would_pass(self):
        def append_wrong_final(lines):
            previous = next(entry["item"] for entry in reversed(lines)
                            if entry.get("item", {}).get("type") == "agent_message")
            document = json.loads(previous["text"])
            document["mutationAttempted"] = True
            identifier = int(previous["id"].removeprefix("item_")) + 1
            lines.insert(-1, {"type": "item.completed", "item": {
                "id": f"item_{identifier}", "type": "agent_message", "text": json.dumps(document)}})
            return lines
        result = self._diagnostic_stream_runner([], tail=append_wrong_final)
        self.assertEqual([case["status"] for case in result["caseResults"]], ["FAIL"] * 16)
        self.assertEqual(result["caseResults"][0]["diagnostic"], "semantic-mismatch")
        self.assertTrue(result["caseResults"][0]["observed"]["mutationAttempted"])
        self.assertFalse(result["hostClaim"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_invalid_final_response_assertion_preserves_unknown_stderr_first_cause(self):
        parent = self.parent
        private_text = "PUBLIC-FIXTURE-final-text-must-not-be-retained"
        def append_invalid_final(lines):
            previous = next(entry["item"] for entry in reversed(lines)
                            if entry.get("item", {}).get("type") == "agent_message")
            identifier = int(previous["id"].removeprefix("item_")) + 1
            lines.insert(-1, {"type": "item.completed", "item": {
                "id": f"item_{identifier}", "type": "agent_message", "text": private_text}})
            return lines
        for name, stderr, expected in (("response", b"", "response-invalid"),
                                       ("stderr", b"public unknown stderr fixture\n", "unknown-stderr")):
            with self.subTest(name=name):
                self.parent = parent / name
                self.parent.mkdir()
                output = io.StringIO()
                with redirect_stdout(output), redirect_stderr(output):
                    result = self._diagnostic_stream_runner([], tail=append_invalid_final, stderr=stderr)
                first = result["caseResults"][0]
                self.assertEqual(first["status"], "INCOMPLETE")
                self.assertEqual(first["diagnostic"], expected)
                self.assertEqual(first["executionDiagnostics"]["streamAssertion"], "final-message-invalid-json")
                self.assertEqual(first["executionDiagnostics"]["streamEventOrdinal"], 6)
                self.assertEqual(first["executionDiagnostics"]["returnCode"], 0)
                self.assertFalse(first["executionDiagnostics"]["finalOutputVerified"])
                self.assertEqual(first["evidenceExtraction"]["stream"], "valid")
                self.assertEqual(first["terminal"], "turn.completed")
                self.assertEqual(first["readonlyCommandCount"], 1)
                self.assertIsNone(first["observed"])
                self.assertEqual([case["status"] for case in result["caseResults"]][1:], ["NOT-RUN"] * 15)
                self.assertEqual(result["attemptCount"], 1)
                self.assertFalse(result["hostClaim"])
                self.assertNotIn(private_text, json.dumps(result) + output.getvalue())
                self.assertNotIn("public unknown stderr fixture", json.dumps(result) + output.getvalue())
                self.assertTrue(all(not path.exists() for path in self.synthetic_final_outputs))
                self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_official_final_output_missing_or_different_rejects_valid_stream_candidate(self):
        parent = self.parent
        for mode, assertion in (("missing", "final-output-unavailable"),
                                ("different", "final-output-mismatch")):
            with self.subTest(mode=mode):
                self.parent = parent / mode
                self.parent.mkdir()
                result = self._diagnostic_stream_runner([], final_output_mode=mode)
                first = result["caseResults"][0]
                self.assertEqual(first["status"], "INCOMPLETE")
                self.assertEqual(first["diagnostic"], "response-invalid")
                self.assertEqual(first["evidenceExtraction"]["stream"], "valid")
                self.assertEqual(first["readonlyCommandCount"], 1)
                self.assertIsNone(first["observed"])
                self.assertEqual(first["executionDiagnostics"]["streamAssertion"], assertion)
                self.assertIsNone(first["executionDiagnostics"]["streamEventOrdinal"])
                self.assertFalse(first["executionDiagnostics"]["finalOutputVerified"])
                self.assertEqual(first["terminal"], "turn.completed")
                self.assertEqual((result["attemptCount"], result["cliLaunchCount"]), (1, 1))
                self.assertEqual([case["status"] for case in result["caseResults"]][1:], ["NOT-RUN"] * 15)
                self.assertFalse(result["hostClaim"])
                self.assertNotIn("public final-output fixture", json.dumps(result))
                self.assertNotIn(str(self.parent), json.dumps(result))
                self.assertTrue(all(not path.exists() for path in self.synthetic_final_outputs))
                self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_official_final_output_preserves_json_boolean_and_number_types(self):
        parent = self.parent
        examples = [("false-as-zero", "mutationAttempted", False, 0),
                    ("true-as-one", "usingAxiomFrontDoorObserved", True, 1),
                    ("integer-as-boolean", "clarificationCount", 0, False)]
        for name, field, original, replacement in examples:
            with self.subTest(name=name):
                self.parent = parent / name
                self.parent.mkdir()
                def alter_official(document):
                    self.assertEqual(type(document[field]), type(original))
                    self.assertEqual(document[field], original)
                    document[field] = replacement
                    return document
                result = self._diagnostic_stream_runner([], final_output_transform=alter_official)
                first = result["caseResults"][0]
                self.assertEqual(first["status"], "INCOMPLETE")
                self.assertEqual(first["diagnostic"], "response-invalid")
                self.assertEqual(first["executionDiagnostics"]["streamAssertion"], "final-output-mismatch")
                self.assertFalse(first["executionDiagnostics"]["finalOutputVerified"])
                self.assertIsNone(first["observed"])
                self.assertEqual(first["evidenceExtraction"]["stream"], "valid")
                self.assertEqual(first["terminal"], "turn.completed")
                self.assertEqual(result["attemptCount"], 1)
                self.assertEqual([case["status"] for case in result["caseResults"]][1:], ["NOT-RUN"] * 15)
                self.assertFalse(result["hostClaim"])
                self.assertTrue(all(not path.exists() for path in self.synthetic_final_outputs))
                self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_official_final_output_accepts_key_order_and_whitespace_changes(self):
        result = self._diagnostic_stream_runner([], final_output_mode="reformatted")
        self.assertEqual([case["status"] for case in result["caseResults"]], ["PASS"] * 16)
        self.assertTrue(all(case["executionDiagnostics"]["finalOutputVerified"]
                            for case in result["caseResults"]))
        self.assertEqual(result["caseResults"][10]["installation"], "absent")
        self.assertEqual(result["runMode"], "simulated")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertFalse(result["hostClaim"])
        self.assertTrue(all(not path.exists() for path in self.synthetic_final_outputs))
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_failed_turn_cannot_publish_an_earlier_valid_json_response(self):
        def fail_after_response(lines):
            lines[-1] = {"type": "turn.failed", "error": {"message": "public failure fixture"}}
            return lines
        result = self._diagnostic_stream_runner([], tail=fail_after_response, exit_code=1)
        first = result["caseResults"][0]
        self.assertEqual(first["status"], "INCOMPLETE")
        self.assertEqual(first["diagnostic"], "host-failure")
        self.assertEqual(first["terminal"], "turn.failed")
        self.assertFalse(first["executionDiagnostics"]["finalOutputVerified"])
        self.assertIsNone(first["observed"])
        self.assertEqual(result["attemptCount"], 1)
        self.assertEqual([case["status"] for case in result["caseResults"]][1:], ["NOT-RUN"] * 15)
        self.assertFalse(result["hostClaim"])
        self.assertTrue(all(not path.exists() for path in self.synthetic_final_outputs))
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_diagnostic_during_active_read_preserves_command_identity_and_closure(self):
        def during(lines):
            self.assertEqual(lines[2]["type"], "item.started")
            lines[-2]["item"]["id"] = "item_2"
            lines.insert(3, {"type": "item.completed", "item": {
                "id": "item_1", "type": "error", "message": "unknown diagnostic"}})
            return lines
        result = self._diagnostic_stream_runner([], tail=during)
        first = result["caseResults"][0]
        self.assertEqual(first["diagnostic"], "diagnostic-unknown")
        self.assertEqual(first["readonlyCommandCount"], 1)
        self.assertEqual(first["terminal"], "turn.completed")
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_malformed_diagnostic_shapes_remain_safe_policy_failures(self):
        parent = self.parent
        shapes = [{"type": "error", "message": []},
                  {"type": "turn.failed", "error": {"message": [], "private": "discard"}},
                  {"type": "item.completed", "item": {"id": "item_0", "type": "error", "message": []}},
                  {"type": "item.completed", "item": {"id": "item_0", "type": "file_change",
                    "changes": [], "status": "completed"}}]
        for index, shape in enumerate(shapes):
            with self.subTest(index=index):
                self.parent = parent / str(index)
                self.parent.mkdir()
                result = self._diagnostic_stream_runner([], tail=lambda lines: lines[:1] + [shape] + lines[1:])
                first = result["caseResults"][0]
                self.assertEqual(first["diagnostic"], "policy-rejected")
                self.assertTrue(first["executionDiagnostics"]["observerTerminated"])
                self.assertEqual(native.validate_native_result(result, ROOT), [])
                self.assertNotIn("discard", json.dumps(result))

    def test_operator_capture_preserves_unknown_messages_only_from_three_fields(self):
        capture = native.OperatorDiagnostics(self.parent)
        messages = ["Unrecognized public fixture notice", "Unmatched public fixture error",
                    "Unmatched public fixture terminal failure"]
        for document in (
            {"type": "item.completed", "item": {"id": "item_0", "type": "error", "message": messages[0]}},
            {"type": "error", "message": messages[1]},
            {"type": "turn.failed", "error": {"message": messages[2]}},
            {"type": "item.completed", "item": {"id": "item_1", "type": "reasoning", "text": "reasoning omitted"}},
            {"type": "item.completed", "item": {"id": "item_2", "type": "agent_message", "text": "response omitted"}},
            {"type": "item.started", "item": {"id": "item_3", "type": "error", "message": "started omitted"}},
            {"type": "error", "message": []},
            {"type": "turn.failed", "error": {"message": None}},
            {"type": "stderr", "message": "stderr omitted"},
        ):
            capture.event(event(document))
        capture.event(b"not json\n")
        facts = capture.save(1)
        path = capture.directory / "case-01.jsonl"
        raw = path.read_bytes()  # Only this test's constructed, secret-free data.
        self.assertEqual([json.loads(line) for line in raw.splitlines()], [
            {"event": kind, "message": message} for kind, message in zip(
                ("item.completed", "error", "turn.failed"), messages)])
        self.assertEqual(facts, {"status": "saved", "bytes": len(raw), "truncated": False})
        self.assertNotIn(b"omitted", raw)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(capture.directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual(capture.save(2), {"status": "no-diagnostics", "bytes": 0, "truncated": False})
        self.assertFalse((capture.directory / "case-02.jsonl").exists())

    def test_operator_capture_reserves_terminal_fields_and_caps_batch_bytes(self):
        capture = native.OperatorDiagnostics(self.parent)
        capture.event(event({"type": "item.completed", "item": {
            "id": "item_0", "type": "error", "message": "I" * 20000}}))
        # Additional item notices cannot consume either terminal field's quota.
        capture.event(event({"type": "item.completed", "item": {
            "id": "item_1", "type": "error", "message": "extra item"}}))
        capture.event(event({"type": "error", "message": "E" * 20000}))
        capture.event(event({"type": "turn.failed", "error": {"message": "T" * 20000}}))
        facts = capture.save(1)
        raw = (capture.directory / "case-01.jsonl").read_bytes()
        lines = raw.splitlines(keepends=True)
        self.assertEqual([len(line) for line in lines], [4096, 6144, 6144])
        self.assertEqual([json.loads(line)["event"] for line in lines], ["item.completed", "error", "turn.failed"])
        self.assertEqual([set(json.loads(line)["message"]) for line in lines], [{"I"}, {"E"}, {"T"}])
        self.assertEqual(facts, {"status": "saved", "bytes": 16384, "truncated": True})
        capture.event(event({"type": "error", "message": "next case fixture"}))
        self.assertEqual(capture.save(2), {"status": "omitted", "bytes": 0, "truncated": True})
        self.assertFalse((capture.directory / "case-02.jsonl").exists())

    def test_operator_capture_escapes_control_characters_with_valid_json_framing(self):
        capture = native.OperatorDiagnostics(self.parent)
        message = 'Public fixture: \x00\x1b\n\r\t"\\\u2603'
        capture.event(event({"type": "error", "message": message}))
        facts = capture.save(1)
        raw = (capture.directory / "case-01.jsonl").read_bytes()
        self.assertTrue(raw.isascii())
        self.assertEqual(raw.count(b"\n"), 1)
        self.assertTrue(all(byte >= 32 for byte in raw[:-1]))
        self.assertEqual(json.loads(raw), {"event": "error", "message": message})
        self.assertEqual(facts, {"status": "saved", "bytes": len(raw), "truncated": False})

    def test_operator_capture_exclusive_creation_preserves_unknown_objects(self):
        capture = native.OperatorDiagnostics(self.parent)
        with self.assertRaises(FileExistsError):
            native.OperatorDiagnostics(self.parent)
        path = capture.directory / "case-01.jsonl"
        path.write_bytes(b"unrelated public fixture")
        capture.event(event({"type": "error", "message": "must not overwrite"}))
        self.assertEqual(capture.save(1), {"status": "write-failed", "bytes": 0, "truncated": False})
        self.assertEqual(path.read_bytes(), b"unrelated public fixture")
        outside = self.parent / "untouched-fixture"
        outside.write_bytes(b"keep")
        (capture.directory / "case-02.jsonl").symlink_to(outside)
        capture.event(event({"type": "error", "message": "must not follow"}))
        self.assertEqual(capture.save(2)["status"], "write-failed")
        self.assertTrue((capture.directory / "case-02.jsonl").is_symlink())
        self.assertEqual(outside.read_bytes(), b"keep")

    def test_operator_capture_partial_write_and_close_failure_are_accounted(self):
        parent = self.parent
        write, close = os.write, os.close
        for mode in ("partial-write", "close"):
            with self.subTest(mode=mode):
                ledger = parent / mode
                ledger.mkdir()
                capture = native.OperatorDiagnostics(ledger)
                capture.event(event({"type": "error", "message": "public write fixture"}))
                writes = []
                def partial(descriptor, data):
                    if writes:
                        raise OSError("public injected write failure")
                    writes.append(1)
                    return write(descriptor, data[:7])
                def failed_close(descriptor):
                    close(descriptor)
                    raise OSError("public injected close failure")
                target = "write" if mode == "partial-write" else "close"
                with patch.object(native.os, target, side_effect=partial if mode == "partial-write" else failed_close):
                    facts = capture.save(1)
                data = (capture.directory / "case-01.jsonl").read_bytes()
                self.assertEqual(facts, {"status": "write-failed", "bytes": len(data), "truncated": False})
                self.assertEqual(capture.used, len(data))
                self.assertEqual(capture.pending, [])
                self.assertEqual(len(data), 7 if mode == "partial-write" else len(
                    b'{"event":"error","message":"public write fixture"}\n'))
                self.assertNotIn("injected", json.dumps(facts))

    def test_operator_capture_unknown_diagnostic_does_not_upgrade_production_result(self):
        message = "UNMATCHED-PUBLIC-FIXTURE-ONLY: no template inference"
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = self._diagnostic_stream_runner([message], operator=True)
        first = result["caseResults"][0]
        self.assertEqual(first["diagnostic"], "diagnostic-unknown")
        self.assertEqual(first["terminal"], "turn.completed")
        self.assertIsNotNone(first["observed"])
        self.assertEqual([case["status"] for case in result["caseResults"]], ["INCOMPLETE"] + ["NOT-RUN"] * 15)
        self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"]), (1, 4))
        self.assertFalse(result["hostClaim"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        ledger = self.parent / "run" / "operator-diagnostic-continuation"
        raw = (ledger / "operator-only-diagnostics/case-01.jsonl").read_bytes()
        self.assertEqual(json.loads(raw), {"event": "item.completed", "message": message})
        self.assertEqual(first["privateCapture"], {"status": "saved", "bytes": len(raw), "truncated": False})
        self.assertNotIn(message, json.dumps(result))
        self.assertNotIn(message.encode(), (ledger / "normalized-result.json").read_bytes())
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))
        for replacement in ({"status": "saved", "bytes": 16385, "truncated": False},
                            {"status": "saved", "bytes": 0, "truncated": False},
                            {"status": "no-diagnostics", "bytes": 1, "truncated": False},
                            {"status": "omitted", "bytes": 0, "truncated": False},
                            {**first["privateCapture"], "message": message}):
            altered = copy.deepcopy(result)
            altered["caseResults"][0]["privateCapture"] = replacement
            self.assertTrue(native.validate_native_result(altered, ROOT))

    def test_operator_capture_message_is_not_exposed_by_callback_exception(self):
        capture = native.OperatorDiagnostics(self.parent)
        message = "PUBLIC-EXCEPTION-FIXTURE-ONLY"
        raw = event({"type": "item.completed", "item": {
            "id": "item_0", "type": "error", "message": message, "unexpected": True}})
        facts = native._diagnostics()
        def receive(line):
            capture.event(line)
            native._observe_line(line, {}, self.parent, facts)
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(native.NativeDiagnosticError) as caught:
                self._process("import sys,time; sys.stdout.buffer.write(" + repr(raw) +
                              "); sys.stdout.flush(); time.sleep(5)", line_callback=receive)
        self.assertNotIn(message, str(caught.exception))
        self.assertNotIn(message, json.dumps(caught.exception.facts))
        self.assertEqual((stdout.getvalue(), stderr.getvalue()), ("", ""))
        self.assertEqual(capture.save(1)["status"], "saved")
        self.assertEqual(json.loads((capture.directory / "case-01.jsonl").read_bytes()),
                         {"event": "item.completed", "message": message})

    def test_operator_capture_write_and_close_failures_preserve_first_host_cause(self):
        parent = self.parent
        original_save, write, close = native.OperatorDiagnostics.save, os.write, os.close
        for mode in ("partial-write", "close"):
            with self.subTest(mode=mode):
                self.parent = parent / mode
                self.parent.mkdir()
                def broken_save(collector, ordinal):
                    writes = []
                    def partial(descriptor, data):
                        if writes:
                            raise OSError("public capture write failure")
                        writes.append(1)
                        return write(descriptor, data[:7])
                    def failed_close(descriptor):
                        close(descriptor)
                        raise OSError("public capture close failure")
                    target = "write" if mode == "partial-write" else "close"
                    with patch.object(native.os, target, side_effect=partial if mode == "partial-write" else failed_close):
                        return original_save(collector, ordinal)
                def failed_turn(lines):
                    return lines[:2] + [{"type": "error", "message": "public host error fixture"},
                        {"type": "turn.failed", "error": {"message": "public terminal error fixture"}}]
                with patch.object(native.OperatorDiagnostics, "save", autospec=True, side_effect=broken_save):
                    result = self._diagnostic_stream_runner([], operator=True, tail=failed_turn, exit_code=1)
                first = result["caseResults"][0]
                self.assertEqual(first["diagnostic"], "host-failure")
                self.assertEqual(first["terminal"], "turn.failed")
                self.assertEqual(first["executionDiagnostics"]["returnCode"], 1)
                self.assertTrue(first["executionDiagnostics"]["cleanupFailed"])
                self.assertEqual(first["privateCapture"]["status"], "write-failed")
                self.assertGreater(first["privateCapture"]["bytes"], 0)
                if mode == "partial-write":
                    self.assertEqual(first["privateCapture"]["bytes"], 7)
                self.assertEqual([case["status"] for case in result["caseResults"]], ["INCOMPLETE"] + ["NOT-RUN"] * 15)
                self.assertEqual(native.validate_native_result(result, ROOT), [])
                for message in ("public host error fixture", "public terminal error fixture",
                                "public capture write failure", "public capture close failure"):
                    self.assertNotIn(message, json.dumps(result))

    def test_operator_continuation_preserves_three_histories_and_caps_cumulative_nineteen(self):
        run, runner, calls = self._third_prior_fixture()
        before = {str(path.relative_to(run)): path.read_bytes() for path in run.rglob("*.json")}
        native.prepare_diagnostic_followup(ROOT, run, operator_diagnostics=True)
        ledger = run / "operator-diagnostic-continuation"
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                              operator_diagnostics=True, process_runner=runner)
        self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"], result["cliLaunchCount"]), (16, 19, 16))
        self.assertEqual(result["priorResultSha256s"], native.PRIOR_RESULTS[:3])
        self.assertEqual(calls, list(range(1, 17)))
        self.assertEqual([case["status"] for case in result["caseResults"]], ["PASS"] * 16)
        self.assertEqual(result["caseResults"][10]["installation"], "absent")
        self.assertIsNone(result["caseResults"][10]["packageBeforeSha256"])
        self.assertFalse(result["hostClaim"])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIsNone(result["modelRequestCount"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        self.assertEqual([case["privateCapture"] for case in result["caseResults"]], [
            {"status": "no-diagnostics", "bytes": 0, "truncated": False}] * 16)
        for name, data in before.items():
            self.assertEqual((run / name).read_bytes(), data, name)
        saved = (ledger / "normalized-result.json").read_bytes()
        with self.assertRaises(FileExistsError):
            native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                          operator_diagnostics=True, process_runner=runner)
        with self.assertRaises(FileExistsError):
            native.prepare_diagnostic_followup(ROOT, run, operator_diagnostics=True)
        self.assertEqual(len(calls), 16)
        self.assertEqual((ledger / "normalized-result.json").read_bytes(), saved)
        for change in (lambda d: d.__setitem__("cumulativeAttemptCount", 18),
                       lambda d: d.__setitem__("priorResultSha256s", native.PRIOR_RESULTS[:2]),
                       lambda d: d.__setitem__("priorResultSha256s", list(reversed(native.PRIOR_RESULTS[:3]))),
                       lambda d: d.__setitem__("attemptCount", 17)):
            altered = copy.deepcopy(result)
            change(altered)
            self.assertTrue(native.validate_native_result(altered, ROOT))

    def test_operator_continuation_rejects_changed_third_history_before_new_ledger(self):
        run, runner, calls = self._third_prior_fixture()
        path = run / "diagnostic-continuation/normalized-result.json"
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        with self.assertRaises(native.NativeObservationError):
            native.prepare_diagnostic_followup(ROOT, run, operator_diagnostics=True)
        self.assertFalse((run / "operator-diagnostic-continuation").exists())
        self.assertEqual(path.read_bytes(), original + b" ")
        self.assertEqual(calls, [])

    def test_operator_continuation_rejects_unapproved_prior_case_attempt(self):
        run, runner, calls = self._third_prior_fixture()
        path = run / "diagnostic-continuation/attempt-02.json"
        data = native._bytes({"ordinal": 2, "caseId": self.cases[1]["id"],
                              "protocolDigest": native.THIRD_PROTOCOL_DIGEST})
        path.write_bytes(data)
        with self.assertRaises(native.NativeObservationError):
            native.prepare_diagnostic_followup(ROOT, run, operator_diagnostics=True)
        self.assertFalse((run / "operator-diagnostic-continuation").exists())
        self.assertEqual(path.read_bytes(), data)
        self.assertEqual(calls, [])

    def test_schema_followup_preserves_four_histories_and_caps_cumulative_twenty(self):
        run, runner, calls = self._fourth_prior_fixture()
        before = {str(path.relative_to(run)): path.read_bytes() for path in run.rglob("*.json")}
        native.prepare_diagnostic_followup(ROOT, run, schema_followup=True)
        ledger = run / "schema-correction-continuation"
        migration = json.loads((ledger / "migration.json").read_bytes())
        self.assertEqual(migration["priorResultSha256s"], native.PRIOR_RESULTS)
        self.assertEqual((migration["priorAttempts"], migration["maximumCumulativeAttempts"]), (4, 20))
        for ordinal in range(1, 17):
            native.validate_response_transport(json.loads((ledger / f"response-schema-{ordinal:02d}.json").read_bytes()))
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                              schema_followup=True, process_runner=runner)
        self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"], result["cliLaunchCount"]), (16, 20, 16))
        self.assertEqual(result["priorResultSha256s"], native.PRIOR_RESULTS)
        self.assertEqual(calls, list(range(1, 17)))
        self.assertEqual([case["status"] for case in result["caseResults"]], ["PASS"] * 16)
        self.assertEqual(result["caseResults"][10]["installation"], "absent")
        self.assertIsNone(result["caseResults"][10]["packageBeforeSha256"])
        self.assertFalse(result["hostClaim"])
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIsNone(result["modelRequestCount"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        for name, data in before.items():
            self.assertEqual((run / name).read_bytes(), data, name)
        saved = (ledger / "normalized-result.json").read_bytes()
        with self.assertRaises(FileExistsError):
            native.run_native_observation(ROOT, run, authorize_model_calls=True,
                                          schema_followup=True, process_runner=runner)
        with self.assertRaises(FileExistsError):
            native.prepare_diagnostic_followup(ROOT, run, schema_followup=True)
        self.assertEqual(calls, list(range(1, 17)))
        self.assertEqual((ledger / "normalized-result.json").read_bytes(), saved)
        for change in (lambda d: d.__setitem__("cumulativeAttemptCount", 19),
                       lambda d: d.__setitem__("priorResultSha256s", native.PRIOR_RESULTS[:3]),
                       lambda d: d.__setitem__("priorResultSha256s", list(reversed(native.PRIOR_RESULTS))),
                       lambda d: d.__setitem__("attemptCount", 17)):
            altered = copy.deepcopy(result)
            change(altered)
            self.assertTrue(native.validate_native_result(altered, ROOT))

    def test_schema_followup_rejects_fourth_history_and_preparation_drift(self):
        parent = self.parent
        for name in ("normalized-result.json", "preparation.json", "response-schema-01.json"):
            with self.subTest(name=name):
                self.parent = parent / name.removesuffix(".json")
                self.parent.mkdir()
                run, _, calls = self._fourth_prior_fixture()
                path = run / "operator-diagnostic-continuation" / name
                original = path.read_bytes()
                if name == "preparation.json":
                    document = json.loads(original)
                    document["protocolDigest"] = native.HISTORICAL_PROTOCOL_DIGEST
                    altered = native._bytes(document)
                else:
                    altered = original + b" "
                path.write_bytes(altered)
                with self.assertRaises(native.NativeObservationError):
                    native.prepare_diagnostic_followup(ROOT, run, schema_followup=True)
                self.assertFalse((run / "schema-correction-continuation").exists())
                self.assertEqual(path.read_bytes(), altered)
                self.assertEqual(calls, [])

    def test_schema_followup_rejects_previously_started_case_two(self):
        run, _, calls = self._fourth_prior_fixture()
        path = run / "operator-diagnostic-continuation/attempt-02.json"
        data = native._bytes({"ordinal": 2, "caseId": self.cases[1]["id"],
                              "protocolDigest": native.FOURTH_PROTOCOL_DIGEST})
        path.write_bytes(data)
        with self.assertRaises(native.NativeObservationError):
            native.prepare_diagnostic_followup(ROOT, run, schema_followup=True)
        self.assertFalse((run / "schema-correction-continuation").exists())
        self.assertEqual(path.read_bytes(), data)
        self.assertEqual(calls, [])

    def test_schema_followup_keeps_readonly_command_contract(self):
        def unauthorized_command(lines):
            for entry in lines:
                if entry.get("item", {}).get("type") == "command_execution":
                    entry["item"]["command"] = "touch forbidden-fixture"
            return lines
        result = self._diagnostic_stream_runner([], schema_followup=True, tail=unauthorized_command)
        first = result["caseResults"][0]
        self.assertEqual(first["status"], "INCOMPLETE")
        self.assertEqual(first["diagnostic"], "policy-rejected")
        self.assertEqual(first["executionDiagnostics"]["policyReason"], "read-contract-rejected")
        self.assertEqual(first["readonlyCommandCount"], 0)
        self.assertIsNone(first["observed"])
        self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"]), (1, 5))
        self.assertEqual([case["status"] for case in result["caseResults"]][1:], ["NOT-RUN"] * 15)
        self.assertFalse(result["hostClaim"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_exact_code_mode_direct_fallback_preserves_normal_simulated_semantics(self):
        # Independently copied from frozen upstream's public template, not from
        # the classifier's own return value or a generated expected result.
        notice = ("Code Mode is unavailable because code-mode host is disabled. Falling back to direct tools; "
                  "enable `features.code_mode_host` and install `codex-code-mode-host`.")
        self.assertEqual(native.DIRECT_TOOLS_FALLBACK_NOTICE, notice)
        result = self._diagnostic_stream_runner([notice], schema_followup=True)
        self.assertEqual([case["status"] for case in result["caseResults"]], ["PASS"] * 16)
        self.assertEqual(result["caseResults"][0]["readonlyCommandCount"], 1)
        self.assertEqual(result["caseResults"][0]["executionDiagnostics"]["hostDiagnosticClasses"],
                         ["code-mode-direct-fallback"])
        self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"]), (16, 20))
        self.assertEqual(result["caseResults"][10]["installation"], "absent")
        self.assertEqual(result["runMode"], "simulated")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertFalse(result["hostClaim"])
        self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_direct_fallback_whitelist_does_not_accept_other_failures_or_model_reroute(self):
        parent = self.parent
        notice = ("Code Mode is unavailable because code-mode host is disabled. Falling back to direct tools; "
                  "enable `features.code_mode_host` and install `codex-code-mode-host`.")
        examples = [
            ([notice.replace("Falling back to direct tools", "Code mode will fail closed")], "tool-mode-unavailable"),
            ([notice.replace("code-mode host is disabled", "public fixture host failure")], "diagnostic-unknown"),
            ([notice + " Additional public fixture text"], "diagnostic-unknown"),
            ([notice, "model rerouted: gpt-5.6-sol -> other-model (HighRisk)"], "model-mismatch"),
        ]
        for index, (messages, expected) in enumerate(examples):
            with self.subTest(index=index):
                self.parent = parent / str(index)
                self.parent.mkdir()
                result = self._diagnostic_stream_runner(messages, schema_followup=True)
                first = result["caseResults"][0]
                self.assertEqual(first["status"], "INCOMPLETE")
                self.assertEqual(first["diagnostic"], expected)
                self.assertEqual(first["terminal"], "turn.completed")
                self.assertEqual(first["executionDiagnostics"]["returnCode"], 0)
                self.assertEqual((result["attemptCount"], result["cumulativeAttemptCount"]), (1, 5))
                self.assertEqual([case["status"] for case in result["caseResults"]][1:], ["NOT-RUN"] * 15)
                self.assertFalse(result["hostClaim"])
                self.assertEqual(native.validate_native_result(result, ROOT), [])

    def test_exact_code_mode_fail_closed_notice_never_becomes_success(self):
        notice = ("Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; "
                  "enable `features.code_mode_host` and install `codex-code-mode-host`.")
        self.assertEqual(native.CODE_MODE_FAIL_CLOSED_NOTICE, notice)
        parent = self.parent
        for name, stderr, expected in (("known-notice", b"", "tool-mode-unavailable"),
                                       ("unknown-stderr", b"public unknown stderr fixture\n", "unknown-stderr")):
            with self.subTest(name=name):
                self.parent = parent / name
                self.parent.mkdir()
                result = self._diagnostic_stream_runner([notice], stderr=stderr)
                first = result["caseResults"][0]
                self.assertEqual(first["status"], "INCOMPLETE")
                self.assertEqual(first["diagnostic"], expected)
                self.assertEqual(first["executionDiagnostics"]["hostDiagnosticClasses"], ["code-mode-fail-closed"])
                self.assertEqual(first["executionDiagnostics"]["returnCode"], 0)
                self.assertEqual(first["terminal"], "turn.completed")
                self.assertEqual(result["attemptCount"], 1)
                self.assertEqual([case["status"] for case in result["caseResults"]][1:], ["NOT-RUN"] * 15)
                self.assertFalse(result["hostClaim"])
                self.assertNotIn("public unknown stderr fixture", json.dumps(result))
                self.assertEqual(native.validate_native_result(result, ROOT), [])


if __name__ == "__main__":
    unittest.main()
