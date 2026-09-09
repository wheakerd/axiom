"""Ordinary offline regressions for the native observer's actual entrypoints."""

import copy
import hashlib
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
        self.assertEqual(args[-1], "-")
        self.assertNotIn(self.cases[0]["request"], " ".join(args))

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
            material = legacy.materialize_case_contract(materialization_seed=seed, ordinal=ordinal,
                protocol_digest=self.protocol["protocolDigest"], model_schema=schema,
                prompt_envelope=envelope, request=case["request"])
            records.append(native._blank_case(case, material, seed, self.protocol, definition))
        return {"schemaVersion": "2", "protocolId": native.PROTOCOL_ID,
                "discoveryMechanism": native.DISCOVERY_MECHANISM, "pluginRuntimeEnabled": False,
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
                self.assertTrue((run_root / f"attempt-{ordinal:02d}.json").is_file())
                calls.append(ordinal)
                if started_callback:
                    started_callback()
                material_schema = json.loads((paths["case"] / "response-schema.json").read_bytes())
                token = material_schema["properties"]["opaqueCaseBinding"]["const"]
                self.assertIn(self.cases[ordinal - 1]["request"].encode(), stdin)
                self.assertNotIn(self.cases[ordinal - 1]["id"].encode(), stdin)
                document = response(self.cases[ordinal - 1], token)
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
                return {"returncode": 0, "stdout": raw, "stderr": b""}
            return {"returncode": 0, "stdout": event(receipt), "stderr": b""}

        state = native.prepare_native_run(ROOT, run_root, bundle, executable,
                                          authorize_install=True, runner=runner)
        self.assertEqual(state["runMode"], "simulated")
        return run_root, runner, calls

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
        self.assertEqual(capture, {"returncode": 0, "stdout": b"ordinary fixture\n", "stderr": b""})
        self.assertEqual(starts, [True])
        self.assertEqual(lines, [b"ordinary fixture"])

    def test_bounded_process_deadline_reaps_child_even_when_output_pipes_are_closed(self):
        for script in ("import time; time.sleep(5)", "import os,time; os.close(1); os.close(2); time.sleep(5)"):
            with self.subTest(script=script), self.assertRaises((TimeoutError, subprocess.TimeoutExpired)):
                native.bounded_process([sys.executable, "-I", "-B", "-c", script], cwd=self.parent,
                                       env={"PATH": "/usr/bin:/bin"}, timeout=0.1)

    def test_bounded_process_refuses_output_overflow_and_does_not_retain_raw_file(self):
        with self.assertRaisesRegex(native.NativeObservationError, "output limit"):
            native.bounded_process([sys.executable, "-I", "-B", "-c",
                "import sys; sys.stdout.buffer.write(b'x' * (2 * 1024 * 1024))"],
                cwd=self.parent, env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(list(self.parent.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
