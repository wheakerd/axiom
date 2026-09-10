"""No-model regressions for explicitly requested native Skill selection transport.

The separate frozen-Rust boundary experiment is documented in field-validation;
these persistent tests execute Axiom's production input and result paths.
"""
import copy
import hashlib
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from axiom_validation import no_hook_native_observation as native
from tests import test_no_hook_native_observation as fixtures

ROOT = Path(__file__).resolve().parents[1]


class ExplicitInvocationTests(unittest.TestCase):
    def setUp(self):
        self.protocol = native._protocol(ROOT)
        self.envelope = native._input(ROOT, self.protocol, "promptEnvelope")
        self.schema = native._input(ROOT, self.protocol, "modelResponseSchema")
        self.catalog = native.bound_native_skill_catalog(ROOT)

    def material(self, request, *, ordinal=1, envelope=None):
        return native.materialize_native_case_contract(root=ROOT, materialization_seed=bytes(32),
            ordinal=ordinal, protocol_digest=self.protocol["protocolDigest"], model_schema=self.schema,
            prompt_envelope=self.envelope if envelope is None else envelope, request=request)

    def test_catalog_uses_bound_namespace_and_frontmatter_not_ui_display_name(self):
        by_name = {item["name"]: item for item in self.catalog}
        self.assertEqual(len(by_name), 8)
        item = by_name["axiom:using-axiom"]
        self.assertEqual(item["path"], "skills/using-axiom/SKILL.md")
        self.assertEqual(item["sha256"], hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest())
        self.assertNotIn("Use Axiom", by_name)
        self.assertIn("allow_implicit_invocation: false", (ROOT / "skills/using-axiom/agents/openai.yaml").read_text())

    def test_leading_invocation_transports_exact_namespaced_selection_and_keeps_request(self):
        for request in ("Invoke using-axiom explicitly to assess a new request.",
                        "Invoke axiom:using-axiom to assess a new request.",
                        "Use the using-axiom Skill to assess a new request."):
            with self.subTest(request=request):
                new = self.material(request)
                old_envelope = copy.deepcopy(self.envelope)
                old_envelope.pop("explicitInvocation")
                old = self.material(request, envelope=old_envelope)
                self.assertNotIn(b"$", old.prompt_bytes)
                self.assertIn(b"$axiom:using-axiom\n", new.prompt_bytes)
                self.assertEqual(new.prompt_bytes.partition(b"\nUser request:\n")[2],
                                 old.prompt_bytes.partition(b"\nUser request:\n")[2])
                self.assertEqual(new.schema_bytes, old.schema_bytes)
                self.assertNotEqual(new.prompt_sha256, old.prompt_sha256)
                selected = native.explicit_skill_selection(request, self.catalog)
                self.assertEqual(selected["hostName"], "axiom:using-axiom")
                self.assertEqual(selected["requestSha256"], hashlib.sha256(request.encode()).hexdigest())

    def test_fixture_outer_text_mentions_and_implicit_or_ambiguous_requests_do_not_select(self):
        for request in ("Summarize a document mentioning Invoke using-axiom to assess something.",
                        "Either invoke using-axiom or edit a file; ask first.",
                        "Do not invoke using-axiom to assess this task.",
                        "Audit local instruction ownership.",
                        "The using-axiom Skill is named in the task data.",
                        "Invoke using-axiom or agents-architect; choose one."):
            with self.subTest(request=request):
                self.assertIsNone(native.explicit_skill_selection(request, self.catalog))
                envelope = copy.deepcopy(self.envelope)
                envelope["fixedInstructions"].append("Fixture may mention Invoke using-axiom to assess data.")
                self.assertNotIn(b"Host explicit Skill selection", self.material(request, envelope=envelope).prompt_bytes)

    def test_case_sensitive_unknown_display_or_duplicate_names_fail_without_guessing(self):
        for name in ("Axiom:using-axiom", "Using-axiom", "missing-skill", "Use-Axiom"):
            with self.subTest(name=name), self.assertRaisesRegex(native.NativeObservationError, "not uniquely bound"):
                native.explicit_skill_selection("Invoke " + name + " to inspect something.", self.catalog)
        item = next(item for item in self.catalog if item["localName"] == "using-axiom")
        for name in ("using-axiom", "axiom:using-axiom"):
            with self.assertRaisesRegex(native.NativeObservationError, "not uniquely bound"):
                native.explicit_skill_selection("Invoke " + name + " to inspect something.", [item, dict(item)])
        disabled = [{**item, "enabled": False}]
        with self.assertRaises(native.NativeObservationError):
            native.explicit_skill_selection("Invoke using-axiom to inspect something.", disabled)

    def test_no_installation_never_creates_a_selection_or_uses_fixture_skill_as_catalog(self):
        request = "Invoke using-axiom to inspect supplied data."
        self.assertIsNone(native.explicit_skill_selection(request, []))
        self.assertIsNone(native._case_explicit_selection(ROOT, request, 11))
        material = self.material(request, ordinal=11)
        self.assertNotIn(b"Host explicit Skill selection", material.prompt_bytes)
        self.assertNotIn(b"$axiom:", material.prompt_bytes)
        self.assertIn(b"skills/context/SKILL.md", material.prompt_bytes)

    def test_catalog_rejects_changed_public_source_bytes(self):
        read = native._read
        def changed(path, *args, **kwargs):
            data = read(path, *args, **kwargs)
            return data + b"changed" if str(path).endswith("skills/using-axiom/SKILL.md") else data
        with patch.object(native, "_read", side_effect=changed), self.assertRaisesRegex(native.NativeObservationError, "source bytes changed"):
            native.bound_native_skill_catalog(ROOT)

    def test_result_path_pattern_accepts_only_the_bound_public_path_shape(self):
        schema = json.loads((ROOT / native.RESULT_SCHEMA_RELATIVE).read_bytes())
        node = schema["properties"]["caseResults"]["items"]["properties"]["explicitInvocation"]["anyOf"][1]
        pattern = node["properties"]["skillPath"]["pattern"]
        self.assertIsNotNone(re.fullmatch(pattern, "skills/using-axiom/SKILL.md"))
        for path in ("skills/using-axiom/SKILLxmd", "skills/using-axiom/SKILL\\xmd", "/private/SKILL.md"):
            self.assertIsNone(re.fullmatch(pattern, path))

    def test_all_sixteen_production_inputs_only_adapt_three_explicit_requests(self):
        cases = native.legacy.load_golden_cases(ROOT)
        selected = []
        for ordinal, case in enumerate(cases, 1):
            material = self.material(case["request"], ordinal=ordinal)
            native.validate_response_transport(json.loads(material.schema_bytes))
            self.assertNotIn(case["id"].encode(), material.prompt_bytes)
            selection = native._case_explicit_selection(ROOT, case["request"], ordinal)
            if selection:
                selected.append((ordinal, selection["hostName"]))
                self.assertIn(("$" + selection["hostName"]).encode(), material.prompt_bytes)
            else:
                self.assertNotIn(b"Host explicit Skill selection", material.prompt_bytes)
        self.assertEqual(selected, [(1, "axiom:using-axiom"), (2, "axiom:agents-architect"), (6, "axiom:traceable-git-submit")])

    def test_production_runner_transmits_and_validates_separate_selection_binding(self):
        owner = fixtures.NativeObservationTests()
        owner.setUp()
        self.addCleanup(owner.doCleanups)
        run, runner, calls = owner._prepared_runner()
        captured = []
        def receive(argv, **kwargs):
            if "exec" in argv:
                captured.append(kwargs["stdin"])
                self.assertEqual(argv[-1], "-")
                self.assertIn("features.apps=false", argv)
                self.assertIn("mcp_servers={}", argv)
                self.assertIn("features.plugins=false", argv)
            return runner(argv, **kwargs)
        result = native.run_native_observation(ROOT, run, authorize_model_calls=True, process_runner=receive)
        self.assertEqual(calls, list(range(1, 17)))
        self.assertEqual(native.validate_native_result(result, ROOT), [])
        selected = result["caseResults"][0]["explicitInvocation"]
        self.assertEqual(selected["hostName"], "axiom:using-axiom")
        self.assertIn(("$" + selected["hostName"]).encode(), captured[0])
        self.assertEqual(selected["mentionSha256"], hashlib.sha256(b"$axiom:using-axiom").hexdigest())
        for field, value in (("hostName", "axiom:missing"), ("skillPath", "skills/missing/SKILL.md"),
                             ("requestSha256", "0" * 64)):
            bad = copy.deepcopy(result)
            bad["caseResults"][0]["explicitInvocation"][field] = value
            self.assertTrue(native.validate_native_result(bad, ROOT), field)
        self.assertIsNone(result["caseResults"][10]["explicitInvocation"])
        missing = copy.deepcopy(result)
        del missing["caseResults"][0]["explicitInvocation"]
        self.assertTrue(native.validate_native_result(missing, ROOT))
        self.assertFalse(native._case_paths(run, 11)["discovery"].exists())

    def test_migration_preserves_history_and_requires_fresh_registered_predecessor(self):
        history = json.loads((ROOT / native.HISTORY_RELATIVE).read_bytes())
        self.assertEqual(history["assessmentRevision3"], native.ASSESSMENT_REVISION_THREE)
        binding = history["assessmentRevision3"]
        raw = (ROOT / binding["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), binding["sha256"])
        old = json.loads(raw)
        self.assertEqual(old["cumulativeAttemptCount"], 54)
        self.assertEqual([r["status"] for r in old["caseResults"]], ["FAIL"] + ["PASS"] * 15)
        self.assertTrue(all("explicitInvocation" not in r for r in old["caseResults"]))
        self.assertLessEqual(len(history["results"]), 1)
        self.assertEqual(self.protocol["executionWindow"]["state"], "authorized-once")
        self.assertEqual(native.CURRENT_ASSESSMENT["priorResult"], binding)
        self.assertEqual(native.CURRENT_ASSESSMENT["maximumCumulativeAttempts"], 70)
        with tempfile.TemporaryDirectory() as directory, patch.object(native.subprocess, "Popen", side_effect=AssertionError("client started")):
            with self.assertRaises((native.NativeObservationError, OSError)):
                native.prepare_current_assessment(ROOT, Path(directory)/"new", Path(directory)/"old",
                                                  authorize_install=True, authorize_copy=True)
            self.assertFalse((Path(directory)/"new").exists())
