"""Secret-free regressions through the existing receiver, parser and capture path."""
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from axiom_validation import no_hook_clarification as supplement
from axiom_validation import no_hook_native_observation as native
from tests.test_no_hook_native_observation import event, stream

ROOT = Path(__file__).resolve().parents[1]
QUESTION = "Which outcome do you want: redesign the plugin's packaged routes, or install it on this host?"


def text_stream(messages=(QUESTION,), *, command=None, output="", terminal=True):
    data = stream({}, command, output)
    events = [json.loads(x) for x in data.splitlines()]
    first_id = int(events[-2]["item"]["id"].split("_")[1])
    events[-2:-1] = [{"type": "item.completed", "item": {"id": f"item_{first_id+i}",
        "type": "agent_message", "text": text}} for i, text in enumerate(messages)]
    if not terminal:
        events.pop()
    return b"".join(event(e) for e in events)


class ClarificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="axiom-reply-test-")
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name) / supplement.RUN_NAME
        self.run.mkdir()
        self.paths = native._case_paths(self.run, 12)
        self.paths["workspace"].mkdir(parents=True)
        self.paths["home"].mkdir()
        (self.paths["workspace"] / "document.txt").write_text("Public test material.\n")
        self.readable = {str(self.paths["workspace"] / "document.txt"): b"Public test material.\n"}
        (self.paths["case"] / "reply-prompt.txt").write_text("A bounded original request.\n")
        self.prepared = {"ordinal": 12, "caseId": native.legacy.EXPECTED_CASE_IDS[11],
            "promptSha256": supplement.digest(b"A bounded original request.\n"),
            "requestSha256": "0" * 64, "fixtureSha256": "1" * 64, "packageSha256": "2" * 64}
        self.taxonomy = native._input(ROOT, native._protocol(ROOT), "taxonomy")
        # These tests construct a new secret-free simulated batch, independently
        # of whether the real three-call window has already been recorded.
        if self._testMethodName in {"test_batch_stops_after_incomplete_and_cannot_reopen",
                "test_capture_accounting_maximum_three_without_auto_semantic_pass",
                "test_uncommitted_protocol_cannot_consume_batch_marker"}:
            actual_read=supplement._read
            empty=native._bytes({"protocolDigest":supplement.protocol(ROOT)["protocolDigest"],"results":json.loads((ROOT/supplement.ARCHIVE/supplement.HISTORY.name).read_text())["results"]})
            self.enterContext(patch.object(supplement,"_read",side_effect=lambda p,*a,**kw:
                empty if p==ROOT/supplement.HISTORY else actual_read(p,*a,**kw)))


    def capture(self, data=None, *, stderr=b"", code=0, mismatch=False, cleanup=False, timeout=False):
        data = text_stream() if data is None else data
        def runner(argv, **kwargs):
            self.assertNotIn("--output-schema", argv)
            self.assertIn("--json", argv)
            self.assertIn("features.plugins=false", argv)
            self.assertIn("--ephemeral", argv)
            final = argv[argv.index("--output-last-message") + 1]
            program = "import sys,time,pathlib;sys.stdin.buffer.read();"
            if timeout:
                program += "time.sleep(1)"
            else:
                program += ("pathlib.Path(sys.argv[1]).write_bytes(" + repr(("different" if mismatch else QUESTION).encode()) + ");"
                    "sys.stdout.buffer.write(" + repr(data) + ");sys.stdout.buffer.flush();"
                    "sys.stderr.buffer.write(" + repr(stderr) + ");sys.exit(" + str(code) + ")")
            return native.bounded_process([sys.executable, "-I", "-B", "-c", program, final],
                **kwargs, timeout=0.01 if timeout else 10)
        operator = native.OperatorDiagnostics(self.run)
        with ExitStack() as stack:
            stack.enter_context(patch.object(native.legacy, "freeze_executable", return_value={}))
            stack.enter_context(patch.object(native.legacy, "recheck_executable"))
            stack.enter_context(patch.object(supplement, "_verify_inputs", return_value={
                "fixtureSha256": "1"*64, "packageSha256": "2"*64, "modelMetadata": {"derivedEffectiveToolMode": "direct"}}))
            stack.enter_context(patch.object(native, "_open_test_auth", side_effect=lambda *a: os.open(os.devnull, os.O_RDONLY)))
            stack.enter_context(patch.object(supplement, "_login"))
            stack.enter_context(patch.object(native, "_readable", return_value=self.readable))
            if cleanup:
                original = Path.unlink
                stack.enter_context(patch.object(Path, "unlink", autospec=True,
                    side_effect=lambda path, *a, **kw: (_ for _ in ()).throw(OSError()) if path.name.startswith("final-reply") else original(path,*a,**kw)))
            return supplement._capture_case(ROOT, self.run, 12, self.prepared, Path("/fixture/codex"), operator, runner)

    def test_natural_reply_production_receiver_final_file_and_capture(self):
        record = self.capture()
        self.assertEqual(record["status"], "CAPTURED")
        self.assertEqual(record["replies"]["messages"], [QUESTION])
        self.assertTrue(record["executionDiagnostics"]["finalOutputVerified"])
        self.assertEqual(record["postcheck"], "valid")
        self.assertEqual(record["attemptCount"], 1)
        self.assertEqual(record["cliLaunchCount"], 1)
        self.assertFalse((self.run / "final-reply-12.txt").exists())

    def test_old_route_parser_still_rejects_natural_text(self):
        with self.assertRaises(native.NativeStreamError) as found:
            native.parse_native_jsonl(text_stream(), self.taxonomy, self.readable, self.paths["workspace"])
        self.assertEqual(found.exception.code, "final-message-invalid-json")
        self.assertEqual(supplement.reply_stream(text_stream(), self.taxonomy, self.readable,
                                               self.paths["workspace"])["messages"], [QUESTION])

    def test_all_visible_messages_retained_not_just_last_question(self):
        messages = ["I choose installation.", QUESTION]
        parsed = supplement.reply_stream(text_stream(messages), self.taxonomy, {}, self.paths["workspace"])
        self.assertEqual(parsed["messages"], messages)
        self.assertEqual(supplement.public_replies(messages)["originalVisibleMessageCount"], 2)

    def test_real_public_read_bytes_flow_through_receiving_and_record(self):
        data = subprocess.check_output(["cat", "document.txt"], cwd=self.paths["workspace"])
        record = self.capture(text_stream(command="cat document.txt", output=data.decode()))
        self.assertEqual(record["status"], "CAPTURED")
        self.assertEqual(record["readonlyCommandCount"], 1)
        self.assertEqual(record["publicReads"][0]["source"], "fixture")

    def test_unbound_target_rejection_and_ordinal_survive_cleanup(self):
        record = self.capture(text_stream(command="cat /unbound/client/path"), cleanup=True)
        self.assertEqual(record["status"], "INCOMPLETE")
        facts = record["executionDiagnostics"]
        self.assertEqual(facts["streamAssertion"], "read-target-unbound")
        self.assertEqual(facts["streamEventOrdinal"], 3)
        self.assertEqual(facts["category"], "policy-rejected")
        self.assertTrue(facts["cleanupFailed"])

    def test_unknown_stderr_retains_reply_but_never_auto_passes(self):
        record = self.capture(stderr=b"Unknown fixture diagnostic\n")
        self.assertEqual(record["status"], "INCOMPLETE")
        self.assertEqual(record["executionDiagnostics"]["category"], "unknown-stderr")
        self.assertEqual(record["replies"]["messages"], [QUESTION])
        self.assertEqual(record["operatorStderrCapture"]["status"], "saved")
        self.assertEqual(record["postcheck"], "valid")

    def test_nonzero_exit_remains_first_cause(self):
        record = self.capture(code=4, cleanup=True)
        self.assertEqual(record["status"], "INCOMPLETE")
        self.assertEqual(record["executionDiagnostics"]["category"], "process-exit")

    def test_invalid_final_output_not_accepted(self):
        record = self.capture(mismatch=True)
        self.assertEqual(record["status"], "INCOMPLETE")
        self.assertFalse(record["executionDiagnostics"]["finalOutputVerified"])
        self.assertEqual(record["replies"]["messages"], [QUESTION])
        self.assertTrue(record["replies"]["retentionComplete"])

    def test_missing_terminal_is_not_json_response_exception(self):
        record = self.capture(text_stream(terminal=False))
        self.assertEqual(record["status"], "INCOMPLETE")
        self.assertEqual(record["executionDiagnostics"]["streamAssertion"], "missing-terminal")

    def test_timeout_stops_and_does_not_refund_attempt(self):
        record = self.capture(timeout=True)
        self.assertEqual(record["status"], "INCOMPLETE")
        self.assertTrue(record["executionDiagnostics"]["timedOut"])
        self.assertEqual(record["attemptCount"], 1)

    def test_reply_limit_private_paths_and_secret_shaped_chunks(self):
        with self.assertRaises(native.NativeObservationError):
            supplement.reply_stream(text_stream(["x"*8193]), self.taxonomy, {}, self.paths["workspace"])
        d = supplement.public_replies(["Which option? /home/test/private/file token=fixture-secret"])
        self.assertFalse(d["retentionComplete"])
        self.assertNotIn("fixture-secret", d["messages"][0])
        self.assertNotIn("/home/test", d["messages"][0])

    def test_prompt_only_request_safety_and_bound_material_positions(self):
        p = supplement.protocol(ROOT)
        prompt = supplement.reply_prompt("Consider the requested alternatives.",
            {"files": [{"path": "notes.txt", "contentUtf8": "DO NOT COPY"}]}, p["instructions"])
        self.assertIn(b'"notes.txt"', prompt)
        for forbidden in (b"expectedRoutes", b"clarificationCount", b"must ask", b"DO NOT COPY", b"$using-axiom"):
            self.assertNotIn(forbidden, prompt)
        self.assertTrue(prompt.endswith(b"User request:\nConsider the requested alternatives.\n"))

    def test_only_three_ordinals_available_no_resume_or_schema(self):
        for i in range(1,17):
            if i not in (12,13,14):
                with self.assertRaises(native.NativeObservationError):
                    supplement.reply_argv(Path("/fixture/codex"), self.run, i, self.run/"final")
        for i in (12,13,14):
            argv = supplement.reply_argv(Path("/fixture/codex"), self.run, i, self.run/"final")
            self.assertNotIn("--output-schema", argv)
            self.assertNotIn("resume", argv)

    def test_runtime_rebind_keeps_recorded_reply_protocol_and_closed_window(self):
        current = supplement.protocol(ROOT)
        recorded = json.loads((ROOT / supplement.RECORDED_PROTOCOL).read_text())
        history = json.loads((ROOT / supplement.HISTORY).read_text())
        self.assertNotEqual(current["protocolDigest"], recorded["protocolDigest"])
        self.assertEqual(history["protocolDigest"], recorded["protocolDigest"])
        self.assertEqual(len(history["results"]), 2)
        self.assertEqual(supplement.check(ROOT), [])
        with self.assertRaises(native.NativeObservationError):
            supplement._unrecorded(ROOT, current)
        relabeled = dict(history, protocolDigest=current["protocolDigest"])
        actual_read = supplement._read
        with patch.object(supplement, "_read", side_effect=lambda path, *args, **kwargs:
                native._bytes(relabeled) if path == ROOT / supplement.HISTORY
                else actual_read(path, *args, **kwargs)):
            self.assertTrue(supplement.check(ROOT))

    def test_exact_seventy_three_history_and_three_budget(self):
        chain = supplement.attempt_history(ROOT)
        self.assertEqual((chain["attempts"], chain["cliLaunches"]), (73,73))
        self.assertEqual(supplement.protocol(ROOT)["limits"]["maximumCumulativeAttempts"],76)

    def test_batch_stops_after_incomplete_and_cannot_reopen(self):
        p = supplement.protocol(ROOT)
        state = {"protocolDigest": p["protocolDigest"], "attemptHistory": supplement.attempt_history(ROOT),
            "runMode": "simulated", "executable": "/fixture/codex", "cases": [{"ordinal":i} for i in (12,13,14)]}
        native._exclusive(self.run/supplement.STATE,native._bytes(state))
        with patch.object(supplement,"_capture_case",return_value={"ordinal":12,"status":"INCOMPLETE","attemptCount":1,"cliLaunchCount":0}) as capture:
            d=supplement.run(ROOT,self.run,authorized=True,runner=lambda:None)
            self.assertEqual(capture.call_count,1)
            self.assertEqual([c["status"] for c in d["caseResults"]],["INCOMPLETE","NOT-RUN","NOT-RUN"])
            self.assertEqual(d["cumulativeAttemptCount"],74)
            self.assertEqual(d["cumulativeCliLaunchCount"],73)
            with self.assertRaises(FileExistsError):
                supplement.run(ROOT,self.run,authorized=True,runner=lambda:None)

    def test_capture_accounting_maximum_three_without_auto_semantic_pass(self):
        p = supplement.protocol(ROOT)
        state = {"protocolDigest":p["protocolDigest"],"attemptHistory":supplement.attempt_history(ROOT),
            "runMode":"simulated","executable":"/fixture/codex","cases":[{"ordinal":i} for i in (12,13,14)]}
        native._exclusive(self.run/supplement.STATE,native._bytes(state))
        def captured(root,run,ordinal,*args):
            return {"ordinal":ordinal,"status":"CAPTURED","attemptCount":1,"cliLaunchCount":1}
        with patch.object(supplement,"_capture_case",side_effect=captured):
            d=supplement.run(ROOT,self.run,authorized=True,runner=lambda:None)
        self.assertEqual(d["attemptCount"],3)
        self.assertEqual(d["cumulativeAttemptCount"],76)
        self.assertEqual(d["semanticAssessment"],"separate-review-required")

    def test_recognized_condition_precedes_final_artifact_failure(self):
        events = [json.loads(x) for x in text_stream().splitlines()]
        events[-2]["item"]["id"] = "item_1"
        events.insert(1, {"type":"item.completed", "item":{"id":"item_0", "type":"error",
            "message":native.CODE_MODE_FAIL_CLOSED_NOTICE}})
        record = self.capture(b"".join(event(e) for e in events), mismatch=True)
        self.assertEqual(record["executionDiagnostics"]["category"],"tool-mode-unavailable")
        self.assertFalse(record["executionDiagnostics"]["finalOutputVerified"])

    def test_uncommitted_protocol_cannot_consume_batch_marker(self):
        p = supplement.protocol(ROOT)
        state = {"protocolDigest":p["protocolDigest"], "attemptHistory":supplement.attempt_history(ROOT),
                 "runMode":"actual", "executable":"/fixture/codex", "cases":[{"ordinal":i} for i in (12,13,14)]}
        native._exclusive(self.run/supplement.STATE,native._bytes(state))
        def git(argv, **kwargs):
            if "rev-parse" in argv:return b"1"*40+b"\n"+b"2"*40+b"\n"
            path=argv[-1].split(":",1)[1]
            return b"different" if path==supplement.PROTOCOL.as_posix() else (ROOT/path).read_bytes()
        with patch.object(subprocess,"check_output",side_effect=git):
            with self.assertRaisesRegex(native.NativeObservationError,"protocol is not committed"):
                supplement.run(ROOT,self.run,authorized=True)
        self.assertFalse((self.run/"batch-started.json").exists())

    def test_retained_status_and_message_invariants(self):
        p = supplement.protocol(ROOT)
        cases=native.legacy.load_golden_cases(ROOT)
        fixtures=native._input(ROOT,native._protocol(ROOT),"fixtureMatrix")
        c=self.capture()
        records=[]
        for i in (12,13,14):
            case=cases[i-1];record=copy.deepcopy(c)
            record.update(ordinal=i,caseId=case["id"],requestSha256=supplement.digest(case["request"].encode()),
                promptSha256=supplement.digest(supplement.reply_prompt(case["request"],native._definition(fixtures,i),p["instructions"])))
            records.append(record)
        d={"protocolDigest":p["protocolDigest"],"priorResultSha256":supplement.PRIOR,"priorAttemptCount":73,"priorSupplementSha256":supplement.PRIOR_SUPPLEMENT,
           "caseResults":records,"attemptCount":3,"cliLaunchCount":3,"cumulativeAttemptCount":76,
           "cumulativeCliLaunchCount":76,"modelRequestCount":None}
        actual_read=supplement._read
        def check(doc):
            data=native._bytes(doc);relative="evals/no-hook-observation/results/clarification-fixture.json"
            history={"protocolDigest":p["protocolDigest"],"results":[*json.loads((ROOT/supplement.ARCHIVE/supplement.HISTORY.name).read_text())["results"],{"path":relative,"sha256":supplement.digest(data)}]}
            history["fixedAcceptance"] = {"windowId": native.FIXED_ACCEPTANCE["windowId"],
                "protocolDigest": p["protocolDigest"], "results": []}
            history["revisionFourAcceptance"] = {"windowId": native.REVISION_FOUR_ACCEPTANCE["windowId"],
                "protocolDigest": p["protocolDigest"], "results": []}
            history["hostContextAcceptance"] = {"windowId": native.HOST_CONTEXT_ACCEPTANCE["windowId"],
                "protocolDigest": p["protocolDigest"], "results": []}
            history["independentClarification"] = {"windowId": supplement.INDEPENDENT["windowId"],
                "protocolDigest": p["protocolDigest"], "results": []}
            def read(path,*args,**kw):
                if path==ROOT/supplement.HISTORY:return native._bytes(history)
                if path==ROOT/relative:return data
                return actual_read(path,*args,**kw)
            with patch.object(supplement,"_read",side_effect=read):return supplement.check(ROOT)
        self.assertEqual(check(d),[])
        for bad in ("PASS","unknown","NOT-RUN"):
            changed=copy.deepcopy(d);changed["caseResults"][0]["status"]=bad
            self.assertTrue(check(changed),bad)
        changed=copy.deepcopy(d);changed["caseResults"][0]["replies"]["messages"]=[]
        self.assertTrue(check(changed))
        changed=copy.deepcopy(d);changed["caseResults"][0]["replies"]["originalVisibleMessageCount"]=2
        self.assertTrue(check(changed))

    def test_merged_routing_bytes_use_original_protocol_and_reject_tampering(self):
        original=json.loads((ROOT/supplement.PRIOR_PATH).read_text())
        self.assertEqual(native.validate_native_result(original,ROOT),[])
        changed=copy.deepcopy(original);changed["caseResults"][0]["status"]="FAIL"
        self.assertTrue(native.validate_native_result(changed,ROOT))
        self.assertNotEqual(native._protocol(ROOT)["protocolDigest"],original["protocolDigest"])

    def test_recorded_supplement_refuses_a_new_window_before_launch(self):
        actual_read=supplement._read
        recorded=native._bytes({"results":[{"path":"immutable-existing-result"}]})
        with patch.object(supplement,"_read",side_effect=lambda p,*a,**kw:
                recorded if p==ROOT/supplement.HISTORY else actual_read(p,*a,**kw)):
            with self.assertRaisesRegex(native.NativeObservationError,"supplement already recorded"):
                supplement.run(ROOT,self.run,authorized=True,runner=lambda:None)
        self.assertFalse((self.run/"batch-started.json").exists())

    def test_original_reply_result_and_contract_are_retained(self):
        old = supplement._prior_supplement(ROOT)
        archived = json.loads((ROOT/supplement.ARCHIVE/supplement.PROTOCOL.name).read_text())
        self.assertEqual(old["protocolDigest"], archived["protocolDigest"])
        self.assertEqual(old["cumulativeAttemptCount"], 73)
        self.assertEqual(old["caseResults"][1]["publicReads"][0]["bytes"], 8186)
        current = supplement.protocol(ROOT)
        self.assertNotEqual(current["protocolDigest"], old["protocolDigest"])
        for key in ("instructions", "replyEvidence", "assessment", "loadingEvidence"):
            self.assertEqual(current[key], archived[key])

    def test_old_run_root_cannot_receive_new_attempts(self):
        old = self.run.parent/"cases-clarification-1"
        old.mkdir()
        with self.assertRaisesRegex(native.NativeObservationError, "unregistered"):
            supplement.run(ROOT, old, authorized=True, runner=lambda: None)
        self.assertFalse(list(old.iterdir()))

    def test_same_version_wrong_runtime_rejected_before_preparation(self):
        package = self.run.parent/"public-package"
        manifest = json.loads((ROOT/native.STATIC_BUNDLE_EVIDENCE_RELATIVE).read_text())["bundleManifest"]
        for item in manifest["runtimeFiles"]:
            target = package/item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT/item["path"]).read_bytes())
        target = package/".codex-plugin/plugin.json"
        target.parent.mkdir()
        target.write_text(json.dumps(manifest["derivedPluginManifest"]["fields"], indent=2)+"\n")
        (package/"BUNDLE-MANIFEST.json").write_text(json.dumps(manifest, indent=2)+"\n")
        self.assertEqual(native.package_identity(package), native._protocol(ROOT)["bundle"]["packageSha256"])
        with (package/"skills/traceable-git-submit/SKILL.md").open("ab") as stream:
            stream.write(b"Unexpected old or changed runtime bytes.\n")
        new_run = self.run.parent/"fresh"/supplement.RUN_NAME
        previous = new_run.parent/"cases-clarification-1"
        with patch.object(supplement, "_unrecorded"), \
                patch.object(supplement, "_prior_state", return_value={"executable":"/fixture/codex"}), \
                patch.object(native.legacy, "freeze_executable"), patch.object(supplement, "_login"):
            with self.assertRaises(native.NativeObservationError):
                supplement.prepare(ROOT, new_run, previous, bundle_root=package,
                                   authorized=True, runner=lambda: None)
        self.assertFalse(new_run.exists())

    def test_independent_count_and_both_stopped_windows_remain_closed(self):
        chain = supplement.independent_attempt_history(ROOT)
        self.assertEqual((chain["attempts"], chain["cliLaunches"]), (98, 98))
        self.assertEqual(supplement.INDEPENDENT["limits"]["maximumCumulativeAttempts"], 101)
        self.assertEqual(supplement.INDEPENDENT["ordinals"], [12, 13, 14])
        self.assertEqual(supplement.INDEPENDENT["authenticationSourceOrdinal"], 10)
        with patch.object(native.subprocess, "Popen", side_effect=AssertionError("client started")):
            for fourth in (False, True):
                with self.assertRaises(native.NativeObservationError):
                    supplement._unrecorded(ROOT, supplement.protocol(ROOT), fixed_acceptance=True, revision_four=fourth)
                with self.assertRaisesRegex(native.NativeObservationError, "already recorded"):
                    native.prepare_fixed_acceptance(ROOT, self.run.parent/"never-created", self.run.parent/"old",
                        self.run.parent/"bundle", authorize_install=True, authorize_copy=True, revision_four=fourth)
        for fourth in (False, True):
            binding = native._fixed_result_binding(ROOT, revision_four=fourth)
            old = json.loads((ROOT/binding["path"]).read_bytes())
            self.assertEqual(old["caseResults"][10]["status"], "INCOMPLETE")
            self.assertEqual(native.validate_native_result(old, ROOT), [])

    def independent_capture(self, rejected=False, after_visible=False):
        run = self.run.parent/supplement.INDEPENDENT["runName"]
        run.mkdir()
        p = supplement.protocol(ROOT)
        cases = native.legacy.load_golden_cases(ROOT)
        fixtures = native._input(ROOT, native._protocol(ROOT), "fixtureMatrix")
        records = []
        for ordinal in supplement.ORDINALS:
            paths = native._case_paths(run, ordinal)
            paths["workspace"].mkdir(parents=True)
            paths["home"].mkdir()
            prompt = supplement.reply_prompt(cases[ordinal-1]["request"], native._definition(fixtures, ordinal), p["instructions"])
            (paths["case"]/"reply-prompt.txt").write_bytes(prompt)
            records.append(dict(self.prepared, ordinal=ordinal, caseId=cases[ordinal-1]["id"],
                requestSha256=supplement.digest(cases[ordinal-1]["request"].encode()), promptSha256=supplement.digest(prompt)))
        state = {"protocolDigest":p["protocolDigest"], "attemptHistory":supplement.independent_attempt_history(ROOT),
                 "runMode":"simulated", "executable":"/fixture/codex", "cases":records,
                 "independentClarification":supplement.INDEPENDENT, "executionSource":None}
        native._exclusive(run/supplement.STATE, native._bytes(state))
        calls = []
        messages = ["I choose installation.", QUESTION]
        def runner(argv, **kwargs):
            ordinal = int(Path(kwargs["cwd"]).parent.name.removeprefix("case-"))
            calls.append(ordinal)
            self.assertNotIn("--output-schema", argv)
            data = text_stream(messages, command="cat /unbound/client/path" if rejected else None)
            if rejected and after_visible:
                events = [json.loads(raw) for raw in text_stream(messages).splitlines()]
                events.insert(-1, {"type": "item.started", "item": {"id": "item_2",
                    "type": "command_execution", "command": "cat /unbound/client/path",
                    "aggregated_output": "", "exit_code": None, "status": "in_progress"}})
                data = b"".join(event(item) for item in events)
            final = argv[argv.index("--output-last-message")+1]
            program = ("import pathlib,sys;sys.stdin.buffer.read();pathlib.Path(sys.argv[1]).write_bytes(" +
                repr(QUESTION.encode()) + ");sys.stdout.buffer.write(" + repr(data) + ")")
            return native.bounded_process([sys.executable,"-I","-B","-c",program,final], **kwargs, timeout=10)
        actual_read = supplement._read
        history = json.loads((ROOT/supplement.HISTORY).read_bytes())
        history["independentClarification"]["results"] = []
        history["independentClarification"]["protocolDigest"] = p["protocolDigest"]
        with ExitStack() as stack:
            stack.enter_context(patch.object(supplement,"_read",side_effect=lambda path,*a,**kw:
                native._bytes(history) if path==ROOT/supplement.HISTORY else actual_read(path,*a,**kw)))
            stack.enter_context(patch.object(native.legacy,"freeze_executable",return_value={}))
            stack.enter_context(patch.object(native.legacy,"recheck_executable"))
            stack.enter_context(patch.object(supplement,"_verify_inputs",return_value={"fixtureSha256":"1"*64,
                "packageSha256":"2"*64,"modelMetadata":{"derivedEffectiveToolMode":"direct"}}))
            stack.enter_context(patch.object(native,"_open_test_auth",side_effect=lambda *a:os.open(os.devnull,os.O_RDONLY)))
            stack.enter_context(patch.object(native,"_readable",return_value={}))
            stack.enter_context(patch.object(supplement,"_login"))
            handoff = stack.enter_context(patch.object(native,"_copy_test_auth"))
            stack.enter_context(patch.object(native,"completed_fixed_routing",side_effect=AssertionError("A continuation requested")))
            d = supplement.run(ROOT,run,authorized=True,independent=True,runner=runner)
            with self.assertRaisesRegex(native.NativeObservationError,"already attempted"):
                supplement.run(ROOT,run,authorized=True,independent=True,runner=runner)
        self.assertEqual(d["semanticAssessment"],"separate-review-required")
        self.assertNotIn("fixedAcceptanceWindow",d)
        self.assertEqual(d["independentClarificationWindow"],supplement.INDEPENDENT["windowId"])
        return d,calls,handoff.call_count,messages

    def test_independent_real_receiver_retains_whole_reply_and_does_not_grade(self):
        d,calls,handoffs,messages = self.independent_capture()
        self.assertEqual(calls,[12,13,14])
        self.assertEqual(handoffs,2)
        self.assertEqual([c["status"] for c in d["caseResults"]],["CAPTURED"]*3)
        self.assertEqual((d["cumulativeAttemptCount"],d["cumulativeCliLaunchCount"]),(101,101))
        self.assertTrue(all(c["replies"]["messages"]==messages and
            c["executionDiagnostics"]["finalOutputVerified"] for c in d["caseResults"]))

    def test_independent_read_rejection_stops_remaining_and_auth_handoff(self):
        d,calls,handoffs,_ = self.independent_capture(rejected=True)
        self.assertEqual(calls,[12])
        self.assertEqual(handoffs,0)
        self.assertEqual([c["status"] for c in d["caseResults"]],["INCOMPLETE","NOT-RUN","NOT-RUN"])
        self.assertEqual(d["caseResults"][0]["executionDiagnostics"]["streamAssertion"],"read-target-unbound")
        self.assertEqual((d["cumulativeAttemptCount"],d["cumulativeCliLaunchCount"]),(99,99))

    def test_visible_replies_survive_later_read_rejection_without_handoff(self):
        d, calls, handoffs, messages = self.independent_capture(rejected=True, after_visible=True)
        self.assertEqual(calls, [12])
        self.assertEqual(handoffs, 0)
        self.assertEqual([c["status"] for c in d["caseResults"]], ["INCOMPLETE", "NOT-RUN", "NOT-RUN"])
        first = d["caseResults"][0]
        self.assertEqual(first["replies"]["messages"], messages)
        self.assertEqual(first["replies"]["originalVisibleMessageCount"], len(messages))
        self.assertTrue(first["replies"]["retentionComplete"])
        self.assertEqual(first["executionDiagnostics"]["streamAssertion"], "read-target-unbound")
        self.assertFalse(first["executionDiagnostics"]["finalOutputVerified"])

    def test_independent_source_cannot_use_abnormal_case_or_consume_preparation(self):
        new = self.run.parent/supplement.INDEPENDENT["runName"]
        with patch.object(native,"_revision_four_auth_source",side_effect=native.NativeObservationError("source did not close normally")), \
                patch.object(supplement,"_login",side_effect=AssertionError("login started")), \
                patch.object(native,"_copy_test_auth",side_effect=AssertionError("auth handed off")), \
                patch.object(supplement,"_unrecorded"):
            with self.assertRaisesRegex(native.NativeObservationError,"source did not close normally"):
                supplement.prepare(ROOT,new,self.run.parent/"case-11",bundle_root=self.run.parent/"bundle",
                    authorized=True,independent=True,runner=lambda:None)
        self.assertFalse(new.exists())

    def test_independent_preparation_delivers_only_three_original_inputs(self):
        bundle = self.run.parent/"bundle"
        manifest = json.loads((ROOT/native.STATIC_BUNDLE_EVIDENCE_RELATIVE).read_bytes())["bundleManifest"]
        files = {x["path"]:(ROOT/x["path"]).read_bytes() for x in manifest["runtimeFiles"]}
        files[".codex-plugin/plugin.json"] = (json.dumps(manifest["derivedPluginManifest"]["fields"],indent=2)+"\n").encode()
        files["BUNDLE-MANIFEST.json"] = (json.dumps(manifest,indent=2)+"\n").encode()
        for name,data in files.items():
            target = bundle/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        new = self.run.parent/supplement.INDEPENDENT["runName"]
        previous = self.run.parent/native.REVISION_FOUR_ACCEPTANCE["routingRunName"]
        calls = []
        def install(argv,*,cwd,env,**kwargs):
            ordinal = int(Path(cwd).parent.name.removeprefix("case-"));self.assertIn(ordinal,[12,13,14])
            paths = native._case_paths(new,ordinal);marketplace = new/"marketplace"
            calls.append((ordinal,"marketplace" if "marketplace" in argv else "plugin"))
            if "marketplace" in argv:
                (paths["home"]/"config.toml").write_text('[marketplaces."'+native.legacy.MARKETPLACE_NAME+'"]\nsource_type="local"\nsource='+json.dumps(str(marketplace))+'\n')
                receipt = {"marketplaceName":native.legacy.MARKETPLACE_NAME,"installedRoot":str(marketplace),"alreadyAdded":False}
            else:
                self.assertIn("plugin",argv);self.assertNotIn("exec",argv)
                shutil.copytree(marketplace/"plugin",paths["package"])
                with (paths["home"]/"config.toml").open("a") as f:f.write('\n[plugins."'+native.legacy.PLUGIN_ID+'"]\nenabled=true\n')
                receipt = {"pluginId":native.legacy.PLUGIN_ID,"name":native.legacy.PLUGIN_NAME,
                    "marketplaceName":native.legacy.MARKETPLACE_NAME,"version":native.PLUGIN_VERSION,
                    "installedPath":str(paths["package"]),"authPolicy":"ON_INSTALL"}
            return {"returncode":0,"stdout":native._bytes(receipt),"stderr":b""}
        with patch.object(supplement,"_unrecorded"), patch.object(supplement,"_login"), \
                patch.object(native,"_revision_four_auth_source",return_value={"executable":"/fixture/codex"}) as source, \
                patch.object(native.legacy,"freeze_executable"), patch.object(native,"_model_metadata",return_value={}), \
                patch.object(native,"_copy_test_auth") as auth, \
                patch.object(native,"completed_fixed_routing",side_effect=AssertionError("A requested")):
            state = supplement.prepare(ROOT,new,previous,bundle_root=bundle,authorized=True,independent=True,runner=install)
        source.assert_called_once_with(ROOT,previous,revision_four=True)
        auth.assert_called_once_with(new,10,12,create=True,source_root=previous)
        self.assertEqual(calls,[(i,action) for i in (12,13,14) for action in ("marketplace","plugin")])
        self.assertEqual([c["ordinal"] for c in state["cases"]],[12,13,14])
        self.assertEqual(state["independentClarification"],supplement.INDEPENDENT)
        self.assertEqual(state["attemptHistory"]["attempts"],98)
        self.assertFalse(list(new.glob("attempt-*")))
        self.assertFalse(previous.exists())
        old = json.loads((ROOT/supplement.ARCHIVE/supplement.PROTOCOL.name).read_bytes())
        for c in state["cases"]:
            i=c["ordinal"];case=native.legacy.load_golden_cases(ROOT)[i-1]
            definition=native._definition(native._input(ROOT,native._protocol(ROOT),"fixtureMatrix"),i)
            self.assertEqual((native._case_paths(new,i)["case"]/"reply-prompt.txt").read_bytes(),
                supplement.reply_prompt(case["request"],definition,old["instructions"]))
