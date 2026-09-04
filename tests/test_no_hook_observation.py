"""Adversarial tests for the fake-only Codex no-Hook observation protocol."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation import no_hook_observation as observer


FIXTURE = REPOSITORY_ROOT / "tests/fixtures/no_hook_observation.py"
TAXONOMY = REPOSITORY_ROOT / "evals/codex-exec-jsonl-observer-v3.json"
PROTOCOL = REPOSITORY_ROOT / "evals/no-hook-observation/codex-protocol-v1.json"
PROMPT = REPOSITORY_ROOT / "evals/no-hook-observation/codex-prompt-envelope-v1.json"
FIXTURES = REPOSITORY_ROOT / "evals/no-hook-observation/codex-fixtures-v1.json"
MODEL_SCHEMA = REPOSITORY_ROOT / "evals/no-hook-observation/codex-model-response-schema-v1.json"
RESULT_SCHEMA = REPOSITORY_ROOT / "evals/no-hook-observation/codex-result-schema-v1.json"
HISTORY = REPOSITORY_ROOT / "evals/no-hook-observation/result-history-v1.json"
ENTRYPOINT = REPOSITORY_ROOT / "scripts/run-no-hook-codex-observation.py"
MODULE = REPOSITORY_ROOT / "axiom_validation/no_hook_observation.py"
THREAD_ID = "01890f32-7abc-7def-8abc-0123456789ab"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def event(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def usage() -> dict[str, int]:
    return {
        "input_tokens": 1,
        "cached_input_tokens": 0,
        "cache_write_input_tokens": 0,
        "output_tokens": 1,
        "reasoning_output_tokens": 0,
    }


def response_for(case: dict[str, object], binding: str) -> dict[str, object]:
    return {
        "profileId": observer.PROFILE_ID,
        "opaqueCaseBinding": binding,
        "contractBindings": {
            "profileContractSha256": observer.PROFILE_SHA256,
            "goldenSetSha256": observer.GOLDEN_SET_SHA256,
            "hostCaseSetSha256": observer.HOST_CASE_SET_SHA256,
        },
        "discoveryOutcome": case["expectedOutcome"],
        "selectedRoutes": case["expectedRoutes"],
        "clarificationCount": case["expectedClarificationCount"],
        "usingAxiomFrontDoorObserved": case[
            "expectedUsingAxiomFrontDoorObserved"
        ],
        "sessionStartObserved": False,
        "mutationAttempted": False,
        "mutationObserved": False,
    }


def happy_stream(response: dict[str, object], *, reasoning: bool = False) -> bytes:
    records = [
        event({"type": "thread.started", "thread_id": THREAD_ID}),
        event({"type": "turn.started"}),
    ]
    if reasoning:
        records.append(
            event(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item_0",
                        "type": "reasoning",
                        "text": "discarded",
                    },
                }
            )
        )
    records.extend(
        [
            event(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item_1" if reasoning else "item_0",
                        "type": "agent_message",
                        "text": json.dumps(response, sort_keys=True, separators=(",", ":")),
                    },
                }
            ),
            event({"type": "turn.completed", "usage": usage()}),
        ]
    )
    return b"".join(records)


def fake_run(scenarios: dict[str, str] | None = None) -> dict[str, object]:
    run_root = Path(tempfile.mkdtemp(prefix="axiom-observer-fake-"))
    os.chmod(run_root, 0o700)
    fake = run_root / "fake-codex"
    shutil.copyfile(FIXTURE, fake)
    os.chmod(fake, 0o755)
    digest = hashlib.sha256(fake.read_bytes()).hexdigest()
    try:
        return observer.run_fake_validation(
            repository_root=REPOSITORY_ROOT,
            run_root=run_root,
            fake_executable=fake,
            fake_executable_sha256=digest,
            scenarios=scenarios,
        )
    finally:
        if run_root.exists():
            shutil.rmtree(run_root)


def host_pass_from_fake(document: dict[str, object]) -> dict[str, object]:
    candidate = copy.deepcopy(document)
    candidate["runMode"] = "host-observation"
    candidate["overallStatus"] = "pass"
    candidate["diagnosticCodes"] = ["host-telemetry-not-exposed"]
    candidate["executionFacts"] = {
        "executableKind": "codex-cli",
        "executedBinarySha256": observer.CODEX_BINARY_SHA256,
        "credentialBoundary": "dedicated-inline-process-only",
        "authorizedModelCallCount": 16,
        "modelProcessStartedCount": 16,
        "promptFullyDeliveredCount": 16,
        "marketplaceProcessCount": 15,
        "pluginInstallProcessCount": 15,
    }
    return candidate


class ProtocolContractTests(unittest.TestCase):
    def test_protocol_documents_are_closed_and_observation_is_not_run(self):
        identities = observer.validate_protocol_documents(REPOSITORY_ROOT)
        self.assertEqual(16, identities["caseCount"])
        self.assertEqual(12, identities["sourceBindingCount"])
        failures: list[str] = []
        self.assertEqual((16, 12), observer.check_no_hook_observation(failures))
        self.assertEqual([], failures)
        history = load_json(HISTORY)
        self.assertEqual([], history["results"])
        self.assertEqual("not-run", history["current"]["codexObservation"])
        self.assertFalse(history["current"]["hostClaim"])
        self.assertFalse((REPOSITORY_ROOT / history["canonicalResultPath"]).exists())

    def test_source_bindings_include_action_surfaces_and_exact_tag(self):
        taxonomy = load_json(TAXONOMY)
        source = taxonomy["source"]
        self.assertEqual("rust-v0.153.0", source["tag"])
        self.assertEqual("41e22fee981a63b3698df7ed36bad393cda24715", source["commit"])
        observed = {
            item["path"]: (item["blob"], item["sha256"])
            for item in source["files"]
        }
        expected = {
            path: (blob, digest)
            for path, blob, digest in observer.SOURCE_FILES
        }
        self.assertEqual(expected, observed)
        self.assertIn("codex-rs/cli/src/plugin_cmd.rs", observed)
        self.assertIn("codex-rs/cli/src/marketplace_cmd.rs", observed)
        self.assertIn("codex-rs/features/src/lib.rs", observed)
        self.assertIn("codex-rs/app-server-protocol/src/protocol/v2/item.rs", observed)
        self.assertIn("codex-rs/protocol/src/models.rs", observed)
        self.assertIn("codex-rs/app-server-protocol/src/protocol/common.rs", observed)
        suppression = taxonomy["sourceSuppressionAudit"]
        self.assertEqual(19, suppression["itemVariantAudit"]["sourceVariantCount"])
        self.assertEqual(
            83, suppression["notificationCatchAllAudit"]["sourceVariantCount"]
        )
        self.assertEqual(
            list(observer.ACTUAL_CASE_FEATURE_OVERRIDES),
            taxonomy["requiredFeatureOverrides"],
        )
        self.assertEqual(
            ["item.started", "item.completed"],
            taxonomy["itemTypes"]["file_change"]["allowedEvents"],
        )
        item_audit = suppression["itemVariantAudit"]
        item_partitions = (
            set(item_audit["publiclyMappedVariants"]),
            set(item_audit["suppressedActionVariants"]),
            set(item_audit["suppressedNonActionVariants"]),
        )
        self.assertTrue(all(
            not left & right
            for index, left in enumerate(item_partitions)
            for right in item_partitions[index + 1 :]
        ))
        self.assertEqual(19, len(set().union(*item_partitions)))
        notification = suppression["notificationCatchAllAudit"]
        mapped = set(notification["explicitlyMappedVariants"])
        catch_all = set(notification["catchAllVariants"])
        self.assertFalse(mapped & catch_all)
        self.assertEqual(83, len(mapped | catch_all))
        self.assertTrue(
            set(notification["pairedActionVariants"]) <= catch_all
        )

    def test_probe_notice_is_narrow_and_not_runtime_evidence(self):
        taxonomy = load_json(TAXONOMY)
        probe = taxonomy["probeAdjudication"]
        self.assertEqual("pass", probe["adjudicatedStatus"])
        self.assertEqual("not-run", probe["hostObservation"])
        self.assertEqual(39, len(observer.PROBE_NOTICE))
        self.assertEqual(
            observer.PROBE_NOTICE_SHA256,
            hashlib.sha256(observer.PROBE_NOTICE).hexdigest(),
        )
        self.assertEqual(
            "codex-cli-stdin-additional-context-notice",
            observer.classify_stderr(
                observer.PROBE_NOTICE, prompt_transport="positional-optional-stdin"
            ),
        )
        self.assertEqual(
            "unknown-nonempty",
            observer.classify_stderr(
                observer.PROBE_NOTICE, prompt_transport="stdin-sentinel"
            ),
        )

    def test_canonical_argv_closes_source_suppressed_action_surfaces(self):
        argv = observer.build_codex_argv(
            Path("/opt/codex"), Path("/tmp/schema"), Path("/tmp/workspace")
        )
        self.assertEqual("-", argv[-1])
        self.assertEqual(1, argv.count("-"))
        self.assertIn("--json", argv)
        self.assertIn("--ephemeral", argv)
        self.assertIn("--ignore-user-config", argv)
        self.assertIn("--ignore-rules", argv)
        supplied = {
            argv[index + 1]
            for index, value in enumerate(argv[:-1])
            if value == "-c"
        }
        self.assertTrue(set(observer.ACTUAL_CASE_FEATURE_OVERRIDES) <= supplied)
        self.assertIn("mcp_servers={}", supplied)
        self.assertIn('shell_environment_policy.inherit="none"', supplied)
        marketplace = observer.build_marketplace_add_argv(
            Path("/opt/codex"), Path("/isolated/marketplace")
        )
        plugin = observer.build_plugin_add_argv(Path("/opt/codex"))
        self.assertEqual(
            ["/opt/codex", "-c", 'cli_auth_credentials_store="file"'],
            marketplace[:3],
        )
        self.assertEqual(
            ["/opt/codex", "-c", 'cli_auth_credentials_store="file"'],
            plugin[:3],
        )

    def test_model_facing_prompt_and_schema_are_blinded_for_all_cases(self):
        envelope = load_json(PROMPT)
        schema = load_json(MODEL_SCHEMA)
        cases = observer.load_golden_cases(REPOSITORY_ROOT)
        forbidden_keys = {
            "caseId",
            "caseClass",
            "contractVersion",
            "expectedRoutes",
            "expectedOutcome",
            "expectedClarificationCount",
        }
        self.assertFalse(forbidden_keys & set(schema["properties"]))
        self.assertEqual(
            observer.MODEL_RESPONSE_SCHEMA_SHA256,
            hashlib.sha256(MODEL_SCHEMA.read_bytes()).hexdigest(),
        )
        seen_prompts: set[str] = set()
        seen_schemas: set[str] = set()
        for ordinal, case in enumerate(cases, 1):
            token = f"{ordinal:032x}"
            prompt = observer.render_case_prompt(envelope, case["request"], token)
            materialized = observer.materialize_model_response_schema(schema, token)
            prompt_lower = prompt.lower()
            schema_lower = materialized.lower()
            self.assertNotIn(case["id"].encode(), prompt_lower)
            self.assertNotIn(case["id"].encode(), schema_lower)
            for label in (b"positive", b"negative", b"ambiguous", b"no-route"):
                self.assertNotIn(label, prompt_lower)
            for key in forbidden_keys:
                self.assertNotIn(key.encode(), prompt)
            self.assertIn(token.encode(), prompt)
            self.assertIn(token.encode(), materialized)
            prefix, request_bytes = prompt.split(b"User request:\n", 1)
            self.assertEqual(case["request"].encode() + b"\n", request_bytes)
            # The observer-owned prefix carries no per-case expected route.
            # An explicit Skill name may occur only in the frozen user request.
            for route in case["expectedRoutes"]:
                self.assertNotIn(route.encode(), prefix)
            self.assertEqual(
                list(observer.ALLOWED_ROUTES),
                schema["properties"]["selectedRoutes"]["items"]["enum"],
            )
            seen_prompts.add(hashlib.sha256(prompt).hexdigest())
            seen_schemas.add(hashlib.sha256(materialized).hexdigest())
        self.assertEqual(16, len(seen_prompts))
        self.assertEqual(16, len(seen_schemas))

    def test_default_validation_never_launches_or_probes_credentials(self):
        with mock.patch.object(observer.subprocess, "Popen") as launch, mock.patch.dict(
            os.environ, {"CODEX_API_KEY": "must-not-be-read"}, clear=False
        ):
            self.assertEqual(0, observer.main(["--check"]))
        launch.assert_not_called()

    def test_environment_is_exactly_allowlisted(self):
        with mock.patch.dict(os.environ, {"PARENT_SECRET": "forbidden"}, clear=False):
            model_environment = observer.build_isolated_environment(
                codex_home=Path("/isolated/codex"),
                home=Path("/isolated/home"),
                xdg_config_home=Path("/isolated/config"),
                xdg_cache_home=Path("/isolated/cache"),
                xdg_data_home=Path("/isolated/data"),
                credential="opaque-test-credential",
            )
            install_environment = observer.build_isolated_environment(
                codex_home=Path("/isolated/codex"),
                home=Path("/isolated/home"),
                xdg_config_home=Path("/isolated/config"),
                xdg_cache_home=Path("/isolated/cache"),
                xdg_data_home=Path("/isolated/data"),
            )
        self.assertNotIn("PARENT_SECRET", model_environment)
        self.assertEqual("opaque-test-credential", model_environment["CODEX_API_KEY"])
        self.assertNotIn("CODEX_API_KEY", install_environment)
        with self.assertRaisesRegex(observer.ObservationError, "credential"):
            observer.build_isolated_environment(
                codex_home=Path("/isolated/codex"),
                home=Path("/isolated/home"),
                xdg_config_home=Path("/isolated/config"),
                xdg_cache_home=Path("/isolated/cache"),
                xdg_data_home=Path("/isolated/data"),
                credential="",
            )

    def test_model_and_result_schemas_are_recursively_closed(self):
        model_schema = load_json(MODEL_SCHEMA)
        result_schema = load_json(RESULT_SCHEMA)
        observer._validate_model_response_schema(model_schema)
        observer._validate_result_schema(result_schema)

        mutations: list[tuple[dict[str, object], str]] = []
        candidate = copy.deepcopy(result_schema)
        candidate["properties"]["runner"]["additionalProperties"] = True
        mutations.append((candidate, "closed"))
        candidate = copy.deepcopy(result_schema)
        candidate["properties"]["summary"]["properties"]["hardStop"]["oneOf"] = [
            {"type": "boolean"}
        ]
        mutations.append((candidate, "unsupported"))
        candidate = copy.deepcopy(result_schema)
        candidate["properties"]["cases"]["items"]["type"] = "object"
        mutations.append((candidate, "reference"))
        for candidate, diagnostic in mutations:
            with self.subTest(diagnostic=diagnostic), self.assertRaises(
                observer.ObservationError
            ):
                observer._validate_result_schema(candidate)

        candidate = copy.deepcopy(model_schema)
        candidate["properties"]["contractBindings"]["required"].pop()
        with self.assertRaisesRegex(observer.ObservationError, "close"):
            observer._validate_model_response_schema(candidate)


class JsonlClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = load_json(TAXONOMY)
        cls.case = observer.load_golden_cases(REPOSITORY_ROOT)[0]
        cls.binding = "a" * 32
        cls.response = response_for(cls.case, cls.binding)

    def test_minimal_source_valid_lifecycle_discards_identifiers_and_payload(self):
        facts = observer.parse_jsonl(happy_stream(self.response), self.taxonomy)
        self.assertEqual(
            ("thread.started", "turn.started", "item.completed", "turn.completed"),
            facts.ordered_event_types,
        )
        self.assertEqual(("agent_message",), facts.item_types)
        self.assertEqual("turn.completed", facts.terminal_type)
        self.assertEqual(1, facts.terminal_count)
        self.assertEqual(1, facts.structured_result_count)
        retained = json.dumps(facts.journal, sort_keys=True)
        for forbidden in (
            THREAD_ID,
            "item_0",
            "opaqueCaseBinding",
            "text",
            "thread_id",
        ):
            self.assertNotIn(forbidden, retained)

    def test_benign_reasoning_requires_active_turn(self):
        facts = observer.parse_jsonl(
            happy_stream(self.response, reasoning=True), self.taxonomy
        )
        self.assertEqual(("reasoning", "agent_message"), facts.item_types)
        before_turn = b"".join(
            [
                event({"type": "thread.started", "thread_id": THREAD_ID}),
                event(
                    {
                        "type": "item.completed",
                        "item": {"id": "item_0", "type": "reasoning", "text": "x"},
                    }
                ),
                event({"type": "turn.started"}),
                happy_stream(self.response).split(b"\n", 2)[2],
            ]
        )
        with self.assertRaisesRegex(observer.ObservationError, "active turn"):
            observer.parse_jsonl(before_turn, self.taxonomy)

    def test_closed_payload_and_lifecycle_negative_matrix(self):
        start = event({"type": "thread.started", "thread_id": THREAD_ID})
        turn = event({"type": "turn.started"})
        result = event(
            {
                "type": "item.completed",
                "item": {
                    "id": "item_0",
                    "type": "agent_message",
                    "text": json.dumps(self.response, separators=(",", ":")),
                },
            }
        )
        terminal = event({"type": "turn.completed", "usage": usage()})
        bad_usage = dict(usage())
        bad_usage["input_tokens"] = True
        negative_usage = dict(usage(), input_tokens=-1)
        float_usage = dict(usage(), input_tokens=1.5)
        extra_usage = dict(usage(), future_tokens=0)
        missing_usage_field = dict(usage())
        del missing_usage_field["cached_input_tokens"]
        duplicate_keys = (
            b'{"type":"thread.started","type":"thread.started","thread_id":"x"}\n'
        )
        cases = {
            "malformed": b"{oops}\n",
            "non-object": b"[]\n",
            "duplicate-key": duplicate_keys,
            "partial-utf8": b'{"type":"thread.started","thread_id":"\xff"}\n',
            "missing-final-record-newline": (start + turn + result + terminal).rstrip(b"\n"),
            "missing-thread-id": event({"type": "thread.started"}) + turn + result + terminal,
            "non-v7-thread-id": event(
                {"type": "thread.started", "thread_id": "01890f32-7abc-4def-8abc-0123456789ab"}
            ) + turn + result + terminal,
            "noncanonical-thread-id": event(
                {"type": "thread.started", "thread_id": THREAD_ID.upper()}
            ) + turn + result + terminal,
            "duplicate-thread": start + start + turn + result + terminal,
            "duplicate-turn": start + turn + turn + result + terminal,
            "missing-item-id": start + turn + event(
                {"type": "item.completed", "item": {"type": "reasoning", "text": "x"}}
            ) + result + terminal,
            "item-id-gap": start + turn + event(
                {"type": "item.completed", "item": {"id": "item_1", "type": "reasoning", "text": "x"}}
            ) + result + terminal,
            "item-id-leading-zero": start + turn + event(
                {"type": "item.completed", "item": {"id": "item_00", "type": "reasoning", "text": "x"}}
            ) + result + terminal,
            "duplicate-item-id": start + turn + result + result + terminal,
            "missing-usage": start + turn + result + event({"type": "turn.completed"}),
            "bad-usage": start + turn + result + event(
                {"type": "turn.completed", "usage": bad_usage}
            ),
            "negative-usage": start + turn + result + event(
                {"type": "turn.completed", "usage": negative_usage}
            ),
            "float-usage": start + turn + result + event(
                {"type": "turn.completed", "usage": float_usage}
            ),
            "extra-usage": start + turn + result + event(
                {"type": "turn.completed", "usage": extra_usage}
            ),
            "missing-usage-field": start + turn + result + event(
                {"type": "turn.completed", "usage": missing_usage_field}
            ),
            "missing-result": start + turn + terminal,
            "multiple-result": start + turn + result + event(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item_1",
                        "type": "agent_message",
                        "text": json.dumps(self.response),
                    },
                }
            ) + terminal,
            "missing-terminal": start + turn + result,
            "event-after-terminal": start + turn + result + terminal + event(
                {
                    "type": "item.completed",
                    "item": {"id": "item_1", "type": "reasoning", "text": "x"},
                }
            ),
            "unknown-event": start + turn + event({"type": "future.event"}) + terminal,
            "unknown-item": start + turn + event(
                {"type": "item.completed", "item": {"id": "item_0", "type": "future"}}
            ) + terminal,
        }
        for name, stream in cases.items():
            with self.subTest(name=name), self.assertRaises(observer.ObservationError):
                observer.parse_jsonl(stream, self.taxonomy)

    def test_tool_event_is_classified_before_lifecycle_rejection(self):
        item = {
            "id": "item_0", "type": "command_execution",
            "command": "touch forbidden", "aggregated_output": "",
            "exit_code": None, "status": "in_progress",
        }
        with self.assertRaises(observer.StreamBoundaryError) as caught:
            observer.parse_jsonl(
                event({"type": "item.started", "item": item}), self.taxonomy
            )
        self.assertEqual(1, caught.exception.tool_action_count)
        self.assertEqual(1, caught.exception.mutation_attempt_count)

    def test_every_source_visible_action_surface_hard_stops_before_acceptance(self):
        start = event({"type": "thread.started", "thread_id": THREAD_ID}) + event(
            {"type": "turn.started"}
        )
        tool_items = [
            {
                "id": "item_0",
                "type": "command_execution",
                "command": "touch forbidden",
                "aggregated_output": "",
                "exit_code": 1,
                "status": "failed",
            },
            {
                "id": "item_0",
                "type": "file_change",
                "changes": [{"path": "forbidden", "kind": "add"}],
                "status": "completed",
            },
            {
                "id": "item_0",
                "type": "mcp_tool_call",
                "server": "x",
                "tool": "y",
                "arguments": {},
                "result": None,
                "error": None,
                "status": "failed",
            },
            {
                "id": "item_0",
                "type": "collab_tool_call",
                "tool": "spawn_agent",
                "sender_thread_id": "sender",
                "receiver_thread_ids": [],
                "prompt": None,
                "agents_states": {},
                "status": "failed",
            },
            {
                "id": "item_0",
                "type": "web_search",
                "query": "x",
                "action": {"type": "search", "query": "x", "queries": ["x"]},
            },
        ]
        for item in tool_items:
            event_type = "item.started" if item["type"] in {
                "command_execution",
                "mcp_tool_call",
                "collab_tool_call",
            } else "item.completed"
            with self.subTest(item=item["type"]), self.assertRaises(
                observer.StreamBoundaryError
            ) as caught:
                observer.parse_jsonl(
                    start + event({"type": event_type, "item": item}), self.taxonomy
                )
            self.assertEqual(1, caught.exception.tool_action_count)

    def test_action_classifier_never_promotes_unknown_or_failed_write_to_read_only(self):
        cases = (
            ("command_execution", "failed", {"command": "touch denied"}, "mutation-attempt"),
            ("command_execution", "declined", {"command": "touch denied"}, "denied-operation"),
            ("command_execution", "failed", {"command": ""}, "unknown-action"),
            ("command_execution", "completed", {"command": "cat /opaque/protected"}, "unknown-action"),
            ("file_change", "failed", {}, "mutation-attempt"),
            ("file_change", "completed", {}, "mutation-observed"),
            ("mcp_tool_call", "failed", {}, "external-action"),
            ("web_search", None, {}, "external-action"),
        )
        for item_type, status, item, expected in cases:
            with self.subTest(item_type=item_type, status=status):
                self.assertEqual(
                    expected,
                    observer.classify_action_item(item_type, status, item),
                )


class FixtureAndReceiptTests(unittest.TestCase):
    def test_all_fixtures_materialize_with_closed_logical_facts(self):
        fixture_document = load_json(FIXTURES)
        cases = observer.load_golden_cases(REPOSITORY_ROOT)
        observed: list[str] = []
        with tempfile.TemporaryDirectory(prefix="axiom-fixtures-") as directory:
            root = Path(directory)
            for ordinal, case in enumerate(cases, 1):
                workspace = root / f"case-{ordinal:02d}"
                workspace.mkdir(mode=0o700)
                fact = observer.materialize_fixture(
                    workspace, fixture_document, case["id"]
                )
                self.assertRegex(fact.definition_digest, r"^[0-9a-f]{64}$")
                self.assertRegex(fact.file_set_digest, r"^[0-9a-f]{64}$")
                self.assertRegex(fact.realized_digest, r"^[0-9a-f]{64}$")
                self.assertEqual(0, fact.git_remote_count)
                observed.append(case["id"])
        self.assertEqual(list(observer.EXPECTED_CASE_IDS), observed)
        self.assertEqual("absent", fixture_document["cases"][10]["pluginState"])
        self.assertTrue(
            all(
                entry["pluginState"] == "installed-derived-profile"
                for index, entry in enumerate(fixture_document["cases"])
                if index != 10
            )
        )

    def test_fixture_definitions_do_not_leak_case_class_or_expected_route(self):
        fixture_document = load_json(FIXTURES)
        serialized_definitions = json.dumps(
            fixture_document["definitions"], sort_keys=True
        ).lower()
        for token in (
            "positive",
            "negative",
            "ambiguous",
            "no-route",
            "expectedroute",
            "expectedoutcome",
        ):
            self.assertNotIn(token, serialized_definitions)
        for definition in fixture_document["definitions"]:
            self.assertEqual(
                definition["fixtureDefinitionDigest"],
                observer.self_digest(definition, "fixtureDefinitionDigest"),
            )

    def test_receipts_accept_pretty_json_and_exact_source_enums(self):
        with tempfile.TemporaryDirectory(prefix="axiom-receipts-") as directory:
            root = Path(directory)
            codex_home = root / "codex-home"
            marketplace = codex_home / "marketplaces" / observer.MARKETPLACE_NAME
            plugin = codex_home / "plugins" / "axiom"
            marketplace.mkdir(parents=True)
            plugin.mkdir(parents=True)
            marketplace_receipt = json.dumps(
                {
                    "marketplaceName": observer.MARKETPLACE_NAME,
                    "installedRoot": str(marketplace),
                    "alreadyAdded": False,
                },
                indent=2,
            ).encode()
            plugin_document = {
                "pluginId": observer.PLUGIN_ID,
                "name": "axiom",
                "marketplaceName": observer.MARKETPLACE_NAME,
                "version": observer.PLUGIN_VERSION,
                "installedPath": str(plugin),
                "authPolicy": "ON_INSTALL",
            }
            normalized = observer.parse_marketplace_receipt(
                marketplace_receipt, codex_home
            )
            self.assertTrue(normalized["installedRootWithinTemporaryHome"])
            receipt, installed = observer.parse_plugin_receipt(
                json.dumps(plugin_document, indent=2).encode(), codex_home
            )
            self.assertEqual("ON_INSTALL", receipt["authPolicy"])
            self.assertEqual(plugin.resolve(), installed)
            on_use = dict(plugin_document, authPolicy="ON_USE")
            receipt, _ = observer.parse_plugin_receipt(
                json.dumps(on_use, indent=2).encode(), codex_home
            )
            self.assertEqual("ON_USE", receipt["authPolicy"])
            for bad_policy in ("on-install", "ON-USE", "ALWAYS"):
                candidate = dict(plugin_document, authPolicy=bad_policy)
                with self.subTest(policy=bad_policy), self.assertRaises(
                    observer.ObservationError
                ):
                    observer.parse_plugin_receipt(
                        json.dumps(candidate).encode(), codex_home
                    )

    def test_receipts_reject_duplicate_multiple_trailing_and_unconfined_paths(self):
        with tempfile.TemporaryDirectory(prefix="axiom-receipts-") as directory:
            root = Path(directory)
            codex_home = root / "codex-home"
            inside = codex_home / "plugins" / "axiom"
            outside = root / "outside"
            inside.mkdir(parents=True)
            outside.mkdir()
            base = {
                "pluginId": observer.PLUGIN_ID,
                "name": "axiom",
                "marketplaceName": observer.MARKETPLACE_NAME,
                "version": observer.PLUGIN_VERSION,
                "installedPath": str(inside),
                "authPolicy": "ON_INSTALL",
            }
            bad = [
                (json.dumps(base) + json.dumps(base)).encode(),
                (json.dumps(base) + " trailing").encode(),
                json.dumps(dict(base, installedPath=str(outside))).encode(),
                b'{"pluginId":"a","pluginId":"b"}',
            ]
            for ordinal, data in enumerate(bad):
                with self.subTest(ordinal=ordinal), self.assertRaises(
                    observer.ObservationError
                ):
                    observer.parse_plugin_receipt(data, codex_home)
            with self.assertRaisesRegex(observer.ObservationError, "byte limit"):
                observer.parse_plugin_receipt(
                    b" " * (observer.MAX_RECEIPT_BYTES + 1), codex_home
                )

    def test_inert_git_fixture_rejects_unknown_internal_state(self):
        fixture_document = load_json(FIXTURES)
        with tempfile.TemporaryDirectory(prefix="axiom-fixture-git-") as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir(mode=0o700)
            fact = observer.materialize_fixture(
                workspace,
                fixture_document,
                observer.EXPECTED_CASE_IDS[0],
            )
            self.assertTrue(fact.git_repository)
            os.chmod(workspace, 0o700)
            os.chmod(workspace / ".git", 0o700)
            (workspace / ".git" / "unknown").write_text("reject\n", encoding="ascii")
            with self.assertRaisesRegex(observer.ObservationError, "unknown child"):
                observer._observe_inert_git_facts(workspace, True)


class WriteAllAndCapabilityTests(unittest.TestCase):
    class ShortWriter:
        def __init__(
            self,
            writes: list[int | None | BaseException],
            *,
            flush_error: BaseException | None = None,
            close_error: BaseException | None = None,
        ) -> None:
            self.writes = list(writes)
            self.data = bytearray()
            self.flush_error = flush_error
            self.close_error = close_error
            self.closed = False

        def write(self, value: memoryview) -> int | None:
            outcome = self.writes.pop(0) if self.writes else len(value)
            if isinstance(outcome, BaseException):
                raise outcome
            if type(outcome) is int and outcome > 0:
                self.data.extend(value[: min(outcome, len(value))])
            return outcome

        def flush(self) -> None:
            if self.flush_error is not None:
                raise self.flush_error

        def close(self) -> None:
            self.closed = True
            if self.close_error is not None:
                raise self.close_error

    def test_write_all_handles_repeated_short_writes_and_closes(self):
        writer = self.ShortWriter([1, 2, 1, 3])
        observer._write_all_prompt(writer, b"123456789")
        self.assertEqual(b"123456789", bytes(writer.data))
        self.assertTrue(writer.closed)

    def test_write_all_fails_closed_on_invalid_progress_and_io_failures(self):
        cases = (
            self.ShortWriter([0]),
            self.ShortWriter([None]),
            self.ShortWriter([-1]),
            self.ShortWriter([99]),
            self.ShortWriter([BrokenPipeError()]),
            self.ShortWriter([], flush_error=OSError("flush")),
            self.ShortWriter([], close_error=OSError("close")),
        )
        for writer in cases:
            with self.subTest(writer=writer), self.assertRaisesRegex(
                observer.ObservationError, "complete prompt"
            ):
                observer._write_all_prompt(writer, b"prompt")
            self.assertTrue(writer.closed)

    def test_execution_capability_cannot_be_constructed_normally(self):
        with self.assertRaisesRegex(
            observer.ObservationError, "cannot be constructed"
        ):
            observer._ExecutionCapability()
        self.assertNotIn("run_bounded_process", observer.__all__)
        self.assertNotIn("observe_case_process", observer.__all__)

    def test_real_guard_requires_every_bound_authorization_fact(self):
        with tempfile.TemporaryDirectory(prefix="axiom-capability-") as directory:
            root = Path(directory)
            os.chmod(root, 0o700)
            executable_path = root / "codex"
            executable_path.write_bytes(b"not-the-real-codex")
            executable_path.chmod(0o755)
            executable = observer.freeze_executable(
                executable_path,
                hashlib.sha256(executable_path.read_bytes()).hexdigest(),
            )
            common = {
                "execute": True,
                "expected_protocol_digest": "sha256:" + "1" * 64,
                "actual_protocol_digest": "sha256:" + "1" * 64,
                "expected_entrypoint_sha256": "2" * 64,
                "actual_entrypoint_sha256": "2" * 64,
                "expected_module_sha256": "3" * 64,
                "actual_module_sha256": "3" * 64,
                "expected_binary_digest": executable.sha256,
                "executable": executable,
                "expected_cli_version": observer.CODEX_VERSION,
                "actual_cli_version": observer.CODEX_VERSION,
                "source_commit": observer.SOURCE_COMMIT,
                "source_tree": observer.SOURCE_TREE,
                "run_root": observer.freeze_owned_root(root),
                "model": observer.MODEL,
                "reasoning_effort": observer.REASONING_EFFORT,
                "authorized_call_count": 16,
                "credential_present": True,
            }
            # A fake digest cannot be promoted to the real execution capability.
            with self.assertRaisesRegex(observer.ObservationError, "binary digest"):
                observer._validate_execution_guard(**common)
            mutations = (
                ("execute", False),
                ("expected_protocol_digest", None),
                ("expected_entrypoint_sha256", "0" * 64),
                ("expected_module_sha256", "0" * 64),
                ("expected_cli_version", "0.0.0"),
                ("source_commit", "0" * 40),
                ("source_tree", "0" * 40),
                ("model", "other"),
                ("reasoning_effort", "low"),
                ("authorized_call_count", 15),
                ("credential_present", False),
            )
            for field, value in mutations:
                candidate = dict(common)
                candidate[field] = value
                with self.subTest(field=field), self.assertRaises(
                    observer.ObservationError
                ):
                    observer._validate_execution_guard(**candidate)


class ProcessBoundaryTests(unittest.TestCase):
    def make_capability(
        self, script: Path = FIXTURE
    ) -> tuple[Path, Path, observer.ExecutableIdentity, object]:
        run_root = Path(tempfile.mkdtemp(prefix="axiom-process-boundary-"))
        os.chmod(run_root, 0o700)
        executable_path = run_root / "fake-codex"
        shutil.copyfile(script, executable_path)
        executable_path.chmod(0o755)
        executable = observer.freeze_executable(
            executable_path,
            hashlib.sha256(executable_path.read_bytes()).hexdigest(),
        )
        identities = observer.validate_protocol_documents(REPOSITORY_ROOT)
        capability = observer._mint_fake_execution_capability(
            protocol_digest=identities["protocolDigest"],
            entrypoint_sha256=hashlib.sha256(ENTRYPOINT.read_bytes()).hexdigest(),
            module_sha256=hashlib.sha256(MODULE.read_bytes()).hexdigest(),
            executable=executable,
            run_root=observer.freeze_owned_root(run_root),
            test_launch_sequence=(("model-case", observer.EXPECTED_CASE_IDS[0]),),
        )
        return run_root, executable_path, executable, capability

    def close_capability(self, run_root: Path, capability: object) -> None:
        observer._retire_capability(capability)
        if run_root.exists():
            shutil.rmtree(run_root)

    def model_environment(self, run_root: Path, scenario: str) -> dict[str, str]:
        roots = []
        for name in ("codex-home", "home", "config", "cache", "data", "workspace"):
            path = run_root / name
            path.mkdir(exist_ok=True)
            roots.append(path)
        return observer.build_isolated_environment(
            codex_home=roots[0],
            home=roots[1],
            xdg_config_home=roots[2],
            xdg_cache_home=roots[3],
            xdg_data_home=roots[4],
            additions={
                "AXIOM_FAKE_SCENARIO": scenario,
                "AXIOM_FAKE_OUTCOME": "selected",
                "AXIOM_FAKE_ROUTES": '["using-axiom"]',
                "AXIOM_FAKE_CLARIFICATIONS": "0",
                "AXIOM_FAKE_FRONT_DOOR": "true",
            },
        )

    def launch(
        self,
        *,
        run_root: Path,
        executable_path: Path,
        executable: observer.ExecutableIdentity,
        capability: object,
        environment: dict[str, str],
        timeout: int = 3,
        maximum_stdout: int = observer.MAX_STDOUT_BYTES,
        maximum_stderr: int = observer.MAX_STDERR_BYTES,
        factory: object = subprocess.Popen,
        prompt: bytes = b"opaqueCaseBinding: 00000000000000000000000000000001\n",
        case_id: str = observer.EXPECTED_CASE_IDS[0],
    ) -> observer.ProcessCapture:
        workspace = run_root / "workspace"
        schema = run_root / "model-response-schema.json"
        schema.write_text("{}\n", encoding="ascii")
        argv = observer.build_codex_argv(executable_path, schema, workspace)
        return observer._launch_bounded_process(
            capability,
            executable,
            argv,
            purpose="model-case",
            case_id=case_id,
            prompt=prompt,
            cwd=workspace,
            env=environment,
            timeout_seconds=timeout,
            maximum_stdout=maximum_stdout,
            maximum_stderr=maximum_stderr,
            popen_factory=factory,
        )

    def test_timeout_terminates_and_reaps_exact_child(self):
        run_root, executable_path, executable, capability = self.make_capability()
        processes: list[subprocess.Popen[bytes]] = []

        def factory(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
            process = subprocess.Popen(*args, **kwargs)
            processes.append(process)
            return process

        try:
            capture = self.launch(
                run_root=run_root,
                executable_path=executable_path,
                executable=executable,
                capability=capability,
                environment=self.model_environment(run_root, "timeout"),
                timeout=1,
                factory=factory,
            )
            self.assertTrue(capture.timed_out)
            self.assertEqual(1, len(processes))
            self.assertIsNotNone(processes[0].poll())
        finally:
            self.close_capability(run_root, capability)

    def test_stream_overflow_reads_at_most_limit_plus_one_and_reaps(self):
        for scenario, stream_name in (
            ("oversized-stdout", "stdout"),
            ("oversized-stderr", "stderr"),
        ):
            run_root, executable_path, executable, capability = self.make_capability()
            wrappers: list[object] = []
            processes: list[subprocess.Popen[bytes]] = []

            class CountingReader:
                def __init__(self, raw: object) -> None:
                    self.raw = raw
                    self.bytes_read = 0
                    self.maximum_request = 0

                def read(self, amount: int) -> bytes:
                    self.maximum_request = max(self.maximum_request, amount)
                    data = self.raw.read(amount)
                    self.bytes_read += len(data)
                    return data

                def close(self) -> None:
                    self.raw.close()

            def factory(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
                process = subprocess.Popen(*args, **kwargs)
                wrapper = CountingReader(getattr(process, stream_name))
                setattr(process, stream_name, wrapper)
                wrappers.append(wrapper)
                processes.append(process)
                return process

            try:
                with self.subTest(scenario=scenario), self.assertRaises(
                    observer.ProcessBoundaryError
                ):
                    self.launch(
                        run_root=run_root,
                        executable_path=executable_path,
                        executable=executable,
                        capability=capability,
                        environment=self.model_environment(run_root, scenario),
                        maximum_stdout=1024,
                        maximum_stderr=1024,
                        factory=factory,
                    )
                self.assertEqual(1, len(wrappers))
                self.assertLessEqual(wrappers[0].bytes_read, 1025)
                self.assertLessEqual(wrappers[0].maximum_request, 1025)
                self.assertIsNotNone(processes[0].poll())
            finally:
                self.close_capability(run_root, capability)

    def test_early_child_exit_causes_prompt_integrity_failure_and_reap(self):
        run_root, executable_path, executable, capability = self.make_capability()
        processes: list[subprocess.Popen[bytes]] = []

        def factory(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
            process = subprocess.Popen(*args, **kwargs)
            processes.append(process)
            return process

        try:
            with self.assertRaises(observer.ProcessBoundaryError) as caught:
                self.launch(
                    run_root=run_root,
                    executable_path=executable_path,
                    executable=executable,
                    capability=capability,
                    environment=self.model_environment(run_root, "early-exit"),
                    factory=factory,
                    prompt=b"x" * observer.MAX_CONTRACT_BYTES,
                )
            self.assertTrue(caught.exception.model_call_authorized)
            self.assertTrue(caught.exception.process_started)
            self.assertFalse(caught.exception.prompt_fully_delivered)
            self.assertIsNotNone(processes[0].poll())
        finally:
            self.close_capability(run_root, capability)

    def test_only_capability_launcher_can_start_and_reuse_or_wrong_order_cannot(self):
        run_root, executable_path, executable, capability = self.make_capability()
        starts = 0

        def factory(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
            nonlocal starts
            starts += 1
            return subprocess.Popen(*args, **kwargs)

        try:
            environment = self.model_environment(run_root, "happy")
            with self.assertRaises(observer.ObservationError):
                self.launch(
                    run_root=run_root,
                    executable_path=executable_path,
                    executable=executable,
                    capability=object(),
                    environment=environment,
                    factory=factory,
                )
            self.assertEqual(0, starts)
            capture = self.launch(
                run_root=run_root,
                executable_path=executable_path,
                executable=executable,
                capability=capability,
                environment=environment,
                factory=factory,
            )
            self.assertEqual(0, capture.returncode)
            with self.assertRaises(observer.ProcessBoundaryError):
                self.launch(
                    run_root=run_root,
                    executable_path=executable_path,
                    executable=executable,
                    capability=capability,
                    environment=environment,
                    factory=factory,
                )
            self.assertEqual(1, starts)
        finally:
            self.close_capability(run_root, capability)

        run_root, executable_path, executable, capability = self.make_capability()
        try:
            with self.assertRaises(observer.ProcessBoundaryError):
                self.launch(
                    run_root=run_root,
                    executable_path=executable_path,
                    executable=executable,
                    capability=capability,
                    environment=self.model_environment(run_root, "happy"),
                    case_id=observer.EXPECTED_CASE_IDS[1],
                    factory=factory,
                )
            self.assertEqual(1, starts)
            self.assertTrue(observer._capability_state(capability).hard_stopped)
        finally:
            self.close_capability(run_root, capability)

    def test_sixteen_call_capability_refuses_a_seventeenth_launch(self):
        run_root = Path(tempfile.mkdtemp(prefix="axiom-sixteen-call-boundary-"))
        os.chmod(run_root, 0o700)
        executable_path = run_root / "fake-codex"
        shutil.copyfile(FIXTURE, executable_path)
        executable_path.chmod(0o755)
        executable = observer.freeze_executable(
            executable_path, hashlib.sha256(executable_path.read_bytes()).hexdigest()
        )
        identities = observer.validate_protocol_documents(REPOSITORY_ROOT)
        capability = observer._mint_fake_execution_capability(
            protocol_digest=identities["protocolDigest"],
            entrypoint_sha256=hashlib.sha256(ENTRYPOINT.read_bytes()).hexdigest(),
            module_sha256=hashlib.sha256(MODULE.read_bytes()).hexdigest(),
            executable=executable,
            run_root=observer.freeze_owned_root(run_root),
            test_launch_sequence=tuple(
                ("model-case", case_id) for case_id in observer.EXPECTED_CASE_IDS
            ),
        )
        starts = 0

        def factory(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
            nonlocal starts
            starts += 1
            return subprocess.Popen(*args, **kwargs)

        try:
            environment = self.model_environment(run_root, "happy")
            for case_id in observer.EXPECTED_CASE_IDS:
                capture = self.launch(
                    run_root=run_root,
                    executable_path=executable_path,
                    executable=executable,
                    capability=capability,
                    environment=environment,
                    case_id=case_id,
                    factory=factory,
                )
                self.assertEqual(0, capture.returncode)
            self.assertEqual(16, starts)
            self.assertEqual(0, observer._capability_state(capability).remaining_calls)
            with self.assertRaises(observer.ProcessBoundaryError):
                self.launch(
                    run_root=run_root,
                    executable_path=executable_path,
                    executable=executable,
                    capability=capability,
                    environment=environment,
                    case_id=observer.EXPECTED_CASE_IDS[0],
                    factory=factory,
                )
            self.assertEqual(16, starts)
        finally:
            self.close_capability(run_root, capability)

    def test_fake_validation_rejects_path_symlink_and_byte_substitution(self):
        run_root = Path(tempfile.mkdtemp(prefix="axiom-fake-binding-"))
        os.chmod(run_root, 0o700)
        outside = run_root.parent / f"{run_root.name}-outside"
        shutil.copyfile(FIXTURE, outside)
        outside.chmod(0o755)
        digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        try:
            with self.assertRaises(observer.ObservationError):
                observer.run_fake_validation(
                    repository_root=REPOSITORY_ROOT,
                    run_root=run_root,
                    fake_executable=outside,
                    fake_executable_sha256=digest,
                )
            link = run_root / "fake-codex"
            link.symlink_to(outside)
            with self.assertRaises(observer.ObservationError):
                observer.run_fake_validation(
                    repository_root=REPOSITORY_ROOT,
                    run_root=run_root,
                    fake_executable=link,
                    fake_executable_sha256=digest,
                )
            link.unlink()
            link.write_bytes(FIXTURE.read_bytes() + b"\n")
            link.chmod(0o755)
            with self.assertRaisesRegex(observer.ObservationError, "digest"):
                observer.run_fake_validation(
                    repository_root=REPOSITORY_ROOT,
                    run_root=run_root,
                    fake_executable=link,
                    fake_executable_sha256=hashlib.sha256(link.read_bytes()).hexdigest(),
                )
        finally:
            outside.unlink(missing_ok=True)
            if run_root.exists():
                shutil.rmtree(run_root)


class CleanupConfinementTests(unittest.TestCase):
    def make_root(self) -> tuple[Path, Path, observer.OwnedRootIdentity]:
        parent = Path(tempfile.mkdtemp(prefix="axiom-cleanup-parent-"))
        root = parent / "owned"
        root.mkdir(mode=0o700)
        (root / "nested").mkdir()
        (root / "nested" / "file").write_text("owned", encoding="ascii")
        return parent, root, observer.freeze_owned_root(root)

    def tear_down_parent(self, parent: Path) -> None:
        if parent.exists():
            for directory, subdirectories, files in os.walk(
                parent, topdown=False, followlinks=False
            ):
                for name in files:
                    path = Path(directory) / name
                    if path.is_symlink():
                        path.unlink()
                    else:
                        path.chmod(0o600)
                        path.unlink()
                for name in subdirectories:
                    path = Path(directory) / name
                    if path.is_symlink():
                        path.unlink()
                    else:
                        path.chmod(0o700)
                        path.rmdir()
            parent.rmdir()

    def test_descriptor_cleanup_removes_exact_owned_tree(self):
        parent, root, identity = self.make_root()
        try:
            observer.cleanup_owned_root(identity)
            self.assertFalse(root.exists())
            self.assertEqual([], list(parent.iterdir()))
        finally:
            self.tear_down_parent(parent)

    def test_cleanup_rejects_missing_rename_and_replacement(self):
        scenarios = ("missing", "rename", "replacement", "symlink")
        for scenario in scenarios:
            parent, root, identity = self.make_root()
            moved = parent / "moved"
            try:
                if scenario == "missing":
                    shutil.rmtree(root)
                else:
                    root.rename(moved)
                    if scenario == "replacement":
                        root.mkdir()
                        (root / "unknown").write_text("preserve", encoding="ascii")
                    elif scenario == "symlink":
                        root.symlink_to(moved, target_is_directory=True)
                with self.assertRaisesRegex(
                    observer.ObservationError, "manual cleanup required|identity changed"
                ):
                    observer.cleanup_owned_root(identity)
                if scenario == "replacement":
                    self.assertEqual("preserve", (root / "unknown").read_text())
                if scenario == "symlink":
                    self.assertTrue(root.is_symlink())
            finally:
                self.tear_down_parent(parent)

    def test_replacement_appearing_after_root_quarantine_is_preserved(self):
        parent, root, identity = self.make_root()
        original_rename = observer._rename_noreplace
        calls = 0

        def replace_after_rename(*args: object) -> None:
            nonlocal calls
            original_rename(*args)
            calls += 1
            if calls == 1:
                root.mkdir()
                (root / "unknown").write_text("preserve", encoding="ascii")

        try:
            with mock.patch.object(observer, "_rename_noreplace", replace_after_rename):
                with self.assertRaisesRegex(
                    observer.ObservationError, "replaced|manual cleanup"
                ):
                    observer.cleanup_owned_root(identity)
            self.assertEqual("preserve", (root / "unknown").read_text())
        finally:
            self.tear_down_parent(parent)

    def test_nested_replacement_after_child_quarantine_is_preserved(self):
        parent, root, identity = self.make_root()
        original_rename = observer._rename_noreplace
        calls = 0

        def replace_nested(*args: object) -> None:
            nonlocal calls
            original_rename(*args)
            calls += 1
            if calls == 2:
                # The root has already been quarantined. Locate it and replace
                # the just-quarantined nested child at its old name.
                quarantined_root = next(
                    candidate
                    for candidate in parent.iterdir()
                    if candidate.name.startswith(".axiom-owned-cleanup-")
                )
                replacement = quarantined_root / "nested"
                replacement.mkdir()
                (replacement / "unknown").write_text("preserve", encoding="ascii")

        try:
            with mock.patch.object(observer, "_rename_noreplace", replace_nested):
                with self.assertRaisesRegex(
                    observer.ObservationError, "replaced|manual cleanup"
                ):
                    observer.cleanup_owned_root(identity)
            preserved = [
                candidate
                for candidate in parent.iterdir()
                if candidate.is_dir()
                and candidate.name.startswith(".axiom-owned-cleanup-")
            ]
            self.assertEqual(1, len(preserved))
            self.assertEqual(
                "preserve", (preserved[0] / "nested" / "unknown").read_text()
            )
        finally:
            self.tear_down_parent(parent)

    def test_busy_child_failure_is_not_reported_as_cleanup_success(self):
        parent, root, identity = self.make_root()
        original_rmdir = os.rmdir

        def busy(path: object, *args: object, **kwargs: object) -> None:
            if str(path).startswith(".axiom-child-cleanup-"):
                raise OSError(16, "busy")
            original_rmdir(path, *args, **kwargs)

        try:
            with mock.patch.object(observer.os, "rmdir", busy):
                with self.assertRaisesRegex(observer.ObservationError, "cannot remove"):
                    observer.cleanup_owned_root(identity)
        finally:
            self.tear_down_parent(parent)

    def test_cleanup_rejects_cross_device_children_before_deletion(self):
        parent, root, identity = self.make_root()
        original_stat = observer.os.stat

        def cross_device(path: object, *args: object, **kwargs: object) -> os.stat_result:
            observed = original_stat(path, *args, **kwargs)
            if path == "nested" and kwargs.get("dir_fd") is not None:
                values = list(observed)
                values[2] = observed.st_dev + 1
                return os.stat_result(values)
            return observed

        try:
            with mock.patch.object(observer.os, "stat", side_effect=cross_device):
                with self.assertRaisesRegex(
                    observer.ObservationError, "filesystem boundary"
                ):
                    observer.cleanup_owned_root(identity)
            quarantined = [
                candidate
                for candidate in parent.iterdir()
                if candidate.name.startswith(".axiom-owned-cleanup-")
            ]
            self.assertEqual(1, len(quarantined))
            self.assertTrue((quarantined[0] / "nested" / "file").exists())
        finally:
            self.tear_down_parent(parent)

    def test_protected_snapshot_rejects_hard_linked_files(self):
        parent = Path(tempfile.mkdtemp(prefix="axiom-hardlink-snapshot-"))
        try:
            first = parent / "first"
            second = parent / "second"
            first.write_bytes(b"shared")
            os.link(first, second)
            with self.assertRaisesRegex(observer.ObservationError, "hard-linked"):
                observer.snapshot_tree(parent)
        finally:
            self.tear_down_parent(parent)


class ResultIntegrityAndEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_result = fake_run()
        cls.host_pass = host_pass_from_fake(cls.fake_result)
        observer.validate_normalized_result(cls.fake_result, REPOSITORY_ROOT)
        observer.validate_normalized_result(cls.host_pass, REPOSITORY_ROOT)

    def test_full_fake_orchestration_runs_all_cases_through_production_path(self):
        result = self.fake_result
        self.assertEqual("fake-validation", result["runMode"])
        self.assertEqual("incomplete", result["overallStatus"])
        self.assertEqual(list(observer.EXPECTED_CASE_IDS), [
            item["caseId"] for item in result["cases"]
        ])
        self.assertEqual(16, result["summary"]["evaluatedCases"])
        self.assertEqual(16, result["summary"]["passCount"])
        self.assertEqual(16, result["summary"]["modelCallCount"])
        self.assertEqual(16, result["summary"]["modelCallBudgetConsumed"])
        self.assertEqual(0, result["summary"]["remainingCallBudget"])
        self.assertFalse(result["summary"]["hardStop"])
        self.assertEqual(15, result["installationFacts"]["installedCaseCount"])
        self.assertEqual(1, result["installationFacts"]["noPluginControlCaseCount"])
        self.assertTrue(result["cleanup"]["temporaryRootsRemoved"])
        self.assertTrue(result["cleanup"]["sourceBundleUnchanged"])
        self.assertFalse(result["cleanup"]["manualCleanupRequired"])
        self.assertEqual(
            {
                "authorizedModelCallCount": 16,
                "modelProcessStartedCount": 16,
                "promptFullyDeliveredCount": 16,
                "marketplaceProcessCount": 15,
                "pluginInstallProcessCount": 15,
            },
            {
                key: result["executionFacts"][key]
                for key in (
                    "authorizedModelCallCount",
                    "modelProcessStartedCount",
                    "promptFullyDeliveredCount",
                    "marketplaceProcessCount",
                    "pluginInstallProcessCount",
                )
            },
        )
        self.assertTrue(all(
            case["marketplaceProcessStarted"]
            and case["pluginInstallProcessStarted"]
            for index, case in enumerate(result["cases"])
            if index != 10
        ))
        self.assertFalse(result["cases"][10]["marketplaceProcessStarted"])
        self.assertFalse(result["cases"][10]["pluginInstallProcessStarted"])
        self.assertEqual(
            "not-exposed-by-codex-0.153.0",
            result["noHookProof"]["publicJsonlHookTelemetry"],
        )
        opaque = {item["opaqueBindingSha256"] for item in result["cases"]}
        prompts = {item["casePromptSha256"] for item in result["cases"]}
        schemas = {item["modelResponseSchemaSha256"] for item in result["cases"]}
        self.assertEqual((16, 16, 16), (len(opaque), len(prompts), len(schemas)))

    def test_result_pass_is_observer_derived_not_status_or_summary_owned(self):
        fields = (
            ("discoveryOutcome", "unavailable"),
            ("selectedRoutes", []),
            ("clarificationCount", 1),
            ("usingAxiomFrontDoorObserved", False),
            ("sessionStartObserved", True),
            ("mutationAttempted", True),
            ("mutationObserved", True),
            ("responseDiagnostic", "schema-mismatch"),
            ("opaqueBindingMatched", False),
            ("modelResponseSchemaMatched", False),
            ("fixtureMatched", False),
            ("toolActionCount", 1),
            ("mutationAttemptCount", 1),
            ("mutationObservationCount", 1),
            ("externalActionCount", 1),
            ("deniedOperationCount", 1),
            ("unknownEventCount", 1),
            ("malformedEventCount", 1),
            ("workspaceUnchanged", False),
            ("bundleUnchanged", False),
            ("installedCopyUnchanged", False),
            ("temporaryUserStateUnchanged", False),
            ("modelCallAuthorized", False),
            ("modelProcessStarted", False),
            ("promptFullyDelivered", False),
            ("marketplaceProcessStarted", False),
            ("pluginInstallProcessStarted", False),
        )
        for field, value in fields:
            candidate = copy.deepcopy(self.host_pass)
            candidate["cases"][0][field] = value
            # Simulate an attacker synchronizing claimed status and summary arithmetic.
            candidate["cases"][0]["status"] = "pass"
            candidate["summary"] = observer._derive_summary(
                candidate["cases"], candidate["cleanup"]
            )
            candidate["overallStatus"] = "pass"
            with self.subTest(field=field), self.assertRaises(
                observer.ObservationError
            ):
                observer.validate_normalized_result(candidate, REPOSITORY_ROOT)

    def test_cleanup_and_installation_claims_are_required_for_overall_pass(self):
        mutations = (
            ("cleanup", "temporaryRootsRemoved", False),
            ("cleanup", "userCodexStateUnchanged", False),
            ("cleanup", "sourceBundleUnchanged", False),
            ("cleanup", "manualCleanupRequired", True),
            ("installationFacts", "installedTreeVerified", False),
            ("installationFacts", "installedPathWithinTemporaryHome", False),
            ("installationFacts", "cleanupVerified", False),
            ("installationFacts", "installedCaseCount", 14),
            ("installationFacts", "noPluginControlCaseCount", 0),
            ("installationFacts", "persistentUserStateChanged", True),
            ("noHookProof", "packageHookSurfaceAbsent", False),
            ("noHookProof", "installedHookSurfaceAbsent", False),
            ("noHookProof", "temporaryConfigHookRegistrationAbsent", False),
            ("noHookProof", "fullProfileWrapperAbsent", False),
            ("noHookProof", "modelReportedSessionStartObservedCount", 1),
        )
        for owner, field, value in mutations:
            candidate = copy.deepcopy(self.host_pass)
            candidate[owner][field] = value
            candidate["summary"] = observer._derive_summary(
                candidate["cases"], candidate["cleanup"]
            )
            candidate["overallStatus"] = "pass"
            if candidate["cleanup"]["manualCleanupRequired"]:
                candidate["diagnosticCodes"] = [
                    "host-telemetry-not-exposed",
                    "cleanup-manual-required",
                ]
            with self.subTest(owner=owner, field=field), self.assertRaises(
                observer.ObservationError
            ):
                observer.validate_normalized_result(candidate, REPOSITORY_ROOT)

    def test_execution_facts_cannot_be_rewritten_into_host_pass(self):
        mutations = (
            ("executableKind", "repository-fake-cli"),
            ("executedBinarySha256", "0" * 64),
            ("credentialBoundary", "not-used-fake-validation"),
            ("authorizedModelCallCount", 15),
            ("modelProcessStartedCount", 15),
            ("promptFullyDeliveredCount", 15),
            ("marketplaceProcessCount", 14),
            ("pluginInstallProcessCount", 14),
        )
        for field, value in mutations:
            candidate = copy.deepcopy(self.host_pass)
            candidate["executionFacts"][field] = value
            with self.subTest(field=field), self.assertRaises(
                observer.ObservationError
            ):
                observer.validate_normalized_result(candidate, REPOSITORY_ROOT)

    def test_identity_binding_mutations_fail(self):
        mutations = (
            ("axiomIdentity", "sourceCommit"),
            ("axiomIdentity", "bundleManifestDigest"),
            ("observationProtocol", "digest"),
            ("runner", "moduleSha256"),
            ("runner", "taxonomySha256"),
            ("contractBindings", "promptEnvelopeDigest"),
            ("contractBindings", "fixtureMatrixSha256"),
        )
        for owner, field in mutations:
            candidate = copy.deepcopy(self.host_pass)
            current = candidate[owner][field]
            candidate[owner][field] = (
                "sha256:" + "0" * 64 if str(current).startswith("sha256:") else "0" * 64
            )
            with self.subTest(owner=owner, field=field), self.assertRaises(
                observer.ObservationError
            ):
                observer.validate_normalized_result(candidate, REPOSITORY_ROOT)

    def test_free_form_or_sensitive_retention_is_rejected(self):
        payloads = (
            "credential=secret-fragment",
            "raw model response text",
            "request-id=req_123456",
            "rm -rf /tmp/example",
            "/home/person/private",
        )
        for payload in payloads:
            candidate = copy.deepcopy(self.fake_result)
            candidate["limitations"] = [payload]
            with self.subTest(payload=payload), self.assertRaises(
                observer.ObservationError
            ):
                observer.validate_normalized_result(candidate, REPOSITORY_ROOT)
        candidate = copy.deepcopy(self.fake_result)
        candidate["cases"][0]["diagnosticCodes"] = ["credential=secret"]
        with self.assertRaises(observer.ObservationError):
            observer.validate_normalized_result(candidate, REPOSITORY_ROOT)
        diagnostic_mutations = (
            ("host-observation", "pass", ["host-capability-unavailable"]),
            ("host-observation", "pass", ["fake-validation-only"]),
            ("host-observation", "pass", ["cleanup-manual-required"]),
        )
        for run_mode, status, codes in diagnostic_mutations:
            candidate = copy.deepcopy(self.host_pass)
            candidate["runMode"] = run_mode
            candidate["overallStatus"] = status
            candidate["diagnosticCodes"] = codes
            with self.subTest(codes=codes), self.assertRaises(
                observer.ObservationError
            ):
                observer.validate_normalized_result(candidate, REPOSITORY_ROOT)

    def test_incomplete_prompt_never_claims_complete_prompt_digest(self):
        fixtures = load_json(FIXTURES)
        cases = observer.load_golden_cases(REPOSITORY_ROOT)
        error = observer.ProcessBoundaryError(
            "partial prompt",
            model_call_authorized=True,
            process_started=True,
            prompt_fully_delivered=False,
        )
        record = observer._incomplete_case_record(
            cases[0],
            fixtures,
            None,
            "a" * 64,
            "b" * 64,
            "c" * 32,
            error,
        )
        self.assertEqual("0" * 64, record["casePromptSha256"])
        self.assertTrue(record["modelCallAuthorized"])
        self.assertTrue(record["modelProcessStarted"])
        self.assertFalse(record["promptFullyDelivered"])

    def test_installed_copy_must_match_bundle_again_at_launch_boundary(self):
        with tempfile.TemporaryDirectory(prefix="axiom-install-boundary-") as directory:
            root = Path(directory)
            for name in ("workspace", "bundle", "installed", "codex-home"):
                (root / name).mkdir()
            (root / "bundle" / "content").write_bytes(b"expected")
            (root / "installed" / "content").write_bytes(b"replacement")
            fixture = observer.FixtureMaterialization(
                definition_digest="a" * 64,
                file_set_digest="b" * 64,
                realized_digest="c" * 64,
                git_repository=False,
                git_head_state="absent",
                git_clean=False,
                git_remote_count=0,
            )
            with mock.patch.object(observer, "_launch_bounded_process") as launch:
                with self.assertRaisesRegex(observer.ObservationError, "installed plugin tree"):
                    observer._observe_case_process(
                        capability=object(),
                        executable=object(),
                        output_schema=root / "schema",
                        prompt=b"prompt",
                        cwd=root / "workspace",
                        env={},
                        taxonomy={},
                        case={"id": observer.EXPECTED_CASE_IDS[0]},
                        case_prompt_sha256="d" * 64,
                        model_response_schema_sha256="e" * 64,
                        model_response_schema={},
                        opaque_binding="f" * 32,
                        fixture=fixture,
                        plugin_state="installed-derived-profile",
                        workspace=root / "workspace",
                        bundle=root / "bundle",
                        installed_copy=root / "installed",
                        temporary_user_state=root / "codex-home",
                        marketplace_process_started=True,
                        plugin_install_process_started=True,
                    )
            launch.assert_not_called()

    def test_hard_stop_records_every_remaining_case_not_run_and_stops_launches(self):
        first = observer.EXPECTED_CASE_IDS[0]
        result = fake_run({first: "tool"})
        self.assertEqual("incomplete", result["cases"][0]["status"])
        self.assertEqual(1, result["cases"][0]["toolActionCount"])
        self.assertTrue(
            all(item["status"] == "not-run" for item in result["cases"][1:])
        )
        self.assertEqual(1, result["summary"]["modelCallCount"])
        self.assertEqual(0, result["summary"]["remainingCallBudget"])
        self.assertTrue(result["summary"]["hardStop"])
        self.assertEqual("incomplete", result["overallStatus"])

    def test_schema_binding_and_unexpected_stderr_hard_stop(self):
        for scenario in ("binding-mismatch", "stderr", "malformed", "unknown-event"):
            with self.subTest(scenario=scenario):
                result = fake_run({observer.EXPECTED_CASE_IDS[0]: scenario})
                self.assertEqual("incomplete", result["overallStatus"])
                self.assertEqual("incomplete", result["cases"][0]["status"])
                self.assertTrue(
                    all(item["status"] == "not-run" for item in result["cases"][1:])
                )

    def test_normalized_output_contains_no_raw_or_local_material(self):
        with tempfile.TemporaryDirectory(prefix="axiom-normalized-") as directory:
            output = Path(directory) / "result.json"
            digest = observer.write_normalized_result(
                self.fake_result, output, REPOSITORY_ROOT
            )
            data = output.read_bytes()
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            lowered = data.lower()
            for forbidden in (
                b"rawjsonl",
                b"rawstderr",
                b"responsetext",
                b"reasoningtext",
                b"threadid",
                b"itemid",
                b"codex_api_key",
                b"/tmp/",
                b"/home/",
                b"argv",
            ):
                self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    unittest.main()
