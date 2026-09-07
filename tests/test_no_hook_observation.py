"""Adversarial tests for the fake-only Codex no-Hook observation protocol."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import stat
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
GIT_EXECUTABLE = Path(shutil.which("git") or "/nonexistent/git").resolve()
BUILDER_SOURCE_REPOSITORY = Path(
    os.environ.get("AXIOM_TEST_BUNDLE_SOURCE_REPOSITORY", REPOSITORY_ROOT)
).resolve()


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


def fake_run(
    scenarios: dict[str, str] | None = None,
    *,
    hook: object | None = None,
    seed: bytes | None = None,
    real_builder: bool = False,
) -> dict[str, object]:
    test_parent = Path(tempfile.mkdtemp(prefix="axiom-observer-fake-parent-"))
    source_repository: Path | None = None
    if real_builder:
        source_repository = test_parent / "source"
        clone_environment = {
            "LANG": "C",
            "LC_ALL": "C",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
        subprocess.run(
            [
                str(GIT_EXECUTABLE), "clone", "--quiet",
                str(BUILDER_SOURCE_REPOSITORY), str(source_repository),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=clone_environment,
        )
        subprocess.run(
            [
                str(GIT_EXECUTABLE), "-C", str(source_repository), "checkout", "--quiet",
                observer.BUNDLE_RUNTIME_SOURCE_COMMIT,
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=clone_environment,
        )
    run_root = test_parent / "run"
    run_root.mkdir(mode=0o700)
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
            _test_source_repository=source_repository,
            _test_git_executable=GIT_EXECUTABLE if real_builder else None,
            _test_materialization_seed=seed,
            _test_hook=hook,
        )
    finally:
        if test_parent.exists():
            shutil.rmtree(test_parent)


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
    candidate["objectBindingFacts"].update({
        "externalOutputObjectBinding": "verified",
        "bundleDestinationDescriptorBound": True,
        "bundleCreationLedgerVerified": True,
        "bundleFailureCleanupIdentityBound": True,
        "bundleGitCredentialExcluded": True,
        "marketplaceSourceObjectVerified": True,
        "installedCacheLayoutVerified": True,
    })
    return candidate


def remove_test_tree(path: Path) -> None:
    """Remove only a test-owned path after a deliberate cleanup-integrity failure."""
    if path.is_symlink():
        path.unlink()
        return
    if not path.exists():
        return
    for directory, subdirectories, _ in os.walk(path, topdown=True, followlinks=False):
        Path(directory).chmod(0o700)
        for name in subdirectories:
            child = Path(directory) / name
            if not child.is_symlink():
                child.chmod(0o700)
    for directory, subdirectories, files in os.walk(
        path, topdown=False, followlinks=False
    ):
        for name in files:
            child = Path(directory) / name
            if child.is_symlink():
                child.unlink()
            else:
                child.chmod(0o600)
                child.unlink()
        for name in subdirectories:
            child = Path(directory) / name
            if child.is_symlink():
                child.unlink()
            else:
                child.chmod(0o700)
                child.rmdir()
    path.chmod(0o700)
    path.rmdir()


def remove_preserved_run_objects(identity: observer.OwnedRootIdentity) -> None:
    remove_test_tree(identity.path)
    remove_test_tree(identity.path.with_name(identity.path.name + "-moved"))
    for path in identity.path.parent.glob(".axiom-owned-cleanup-*"):
        remove_test_tree(path)


def find_objects_by_identity(
    root: Path, expected: tuple[int, int]
) -> list[Path]:
    """Find one physical object without following links or trusting name order."""
    matches: list[Path] = []
    pending = [root]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                metadata = entry.stat(follow_symlinks=False)
                candidate = Path(entry.path)
                if (metadata.st_dev, metadata.st_ino) == expected:
                    matches.append(candidate)
                if stat.S_ISDIR(metadata.st_mode):
                    pending.append(candidate)
    return matches


class ProtocolContractTests(unittest.TestCase):
    def test_protocol_documents_are_closed_and_observation_is_not_run(self):
        identities = observer.validate_protocol_documents(REPOSITORY_ROOT)
        self.assertEqual(16, identities["caseCount"])
        self.assertEqual(14, identities["sourceBindingCount"])
        failures: list[str] = []
        self.assertEqual((16, 14), observer.check_no_hook_observation(failures))
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
        identities = observer.validate_protocol_documents(REPOSITORY_ROOT)
        seed = bytes(range(32))
        for ordinal, case in enumerate(cases, 1):
            contract = observer.materialize_case_contract(
                materialization_seed=seed,
                ordinal=ordinal,
                protocol_digest=identities["protocolDigest"],
                model_schema=schema,
                prompt_envelope=envelope,
                request=case["request"],
            )
            token = contract.token
            prompt = contract.prompt_bytes
            materialized = contract.schema_bytes
            expected_token = "ocb1_" + hashlib.sha256(
                observer.OPAQUE_BINDING_DOMAIN
                + seed
                + ordinal.to_bytes(2, "big")
                + bytes.fromhex(identities["protocolDigest"].removeprefix("sha256:"))
            ).hexdigest()
            self.assertEqual(expected_token, token)
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
            root = Path(directory) / "owned"
            root.mkdir(mode=0o700)
            identity = observer.freeze_owned_root(root)
            session = observer.OwnedRootSession(identity)
            try:
                for ordinal, case in enumerate(cases, 1):
                    relative = f"case-{ordinal:02d}"
                    session.mkdir(relative, phase="fixture-test-workspace")
                    fact = observer.materialize_fixture_owned(
                        session, relative, fixture_document, case["id"]
                    )
                    self.assertRegex(fact.definition_digest, r"^[0-9a-f]{64}$")
                    self.assertRegex(fact.file_set_digest, r"^[0-9a-f]{64}$")
                    self.assertRegex(fact.realized_digest, r"^[0-9a-f]{64}$")
                    self.assertEqual(0, fact.git_remote_count)
                    observed.append(case["id"])
            finally:
                ledger = session.ledger
                session.close()
                observer.cleanup_owned_root(identity, ledger)
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
        parent = Path(tempfile.mkdtemp(prefix="axiom-receipts-parent-"))
        root = parent / "owned"
        root.mkdir(mode=0o700)
        identity = observer.freeze_owned_root(root)
        session = observer.OwnedRootSession(identity)
        codex_home: observer.FrozenDirectoryIdentity | None = None
        marketplace_source: observer.FrozenDirectoryIdentity | None = None
        other_marketplace: observer.FrozenDirectoryIdentity | None = None
        try:
            session.mkdir(
                "marketplace/.agents/plugins",
                parents=True,
                phase="receipt-test",
            )
            installed_relative = (
                f"codex-home/plugins/cache/{observer.MARKETPLACE_NAME}/"
                f"{observer.PLUGIN_NAME}/{observer.PLUGIN_VERSION}"
            )
            session.mkdir(installed_relative, parents=True, phase="receipt-test")
            codex_home = session.open_directory(
                "codex-home", phase="receipt-test", freeze_tree=False
            )
            marketplace_source = session.open_directory(
                "marketplace", phase="receipt-test", freeze_tree=False
            )
            session.mkdir("other-marketplace", phase="receipt-test")
            other_marketplace = session.open_directory(
                "other-marketplace", phase="receipt-test", freeze_tree=False
            )
            marketplace = f"/proc/self/fd/{marketplace_source.descriptor}"
            plugin = (
                f"/proc/self/fd/{codex_home.descriptor}/plugins/cache/"
                f"{observer.MARKETPLACE_NAME}/{observer.PLUGIN_NAME}/"
                f"{observer.PLUGIN_VERSION}"
            )
            marketplace_receipt = json.dumps(
                {
                    "marketplaceName": observer.MARKETPLACE_NAME,
                    "installedRoot": marketplace,
                    "alreadyAdded": False,
                },
                indent=2,
            ).encode()
            plugin_document = {
                "pluginId": observer.PLUGIN_ID,
                "name": "axiom",
                "marketplaceName": observer.MARKETPLACE_NAME,
                "version": observer.PLUGIN_VERSION,
                "installedPath": plugin,
                "authPolicy": "ON_INSTALL",
            }
            normalized = observer.parse_marketplace_receipt(
                marketplace_receipt, marketplace_source
            )
            self.assertTrue(normalized["localSourceObjectVerified"])
            invented_copy = dict(
                json.loads(marketplace_receipt),
                installedRoot=f"/proc/self/fd/{other_marketplace.descriptor}",
            )
            with self.assertRaisesRegex(
                observer.ObservationError,
                "different inherited descriptor|frozen marketplace source",
            ):
                observer.parse_marketplace_receipt(
                    json.dumps(invented_copy).encode(), marketplace_source
                )
            receipt, installed = observer.parse_plugin_receipt(
                json.dumps(plugin_document, indent=2).encode(),
                session,
                codex_home,
                expected_tree=(),
            )
            try:
                self.assertEqual("ON_INSTALL", receipt["authPolicy"])
                self.assertTrue(receipt["installedPathWithinTemporaryHome"])
                self.assertEqual((), observer._verify_frozen_directory(installed))
            finally:
                observer._close_frozen_directory(installed)
            on_use = dict(plugin_document, authPolicy="ON_USE")
            receipt, installed = observer.parse_plugin_receipt(
                json.dumps(on_use, indent=2).encode(),
                session,
                codex_home,
                expected_tree=(),
            )
            try:
                self.assertEqual("ON_USE", receipt["authPolicy"])
            finally:
                observer._close_frozen_directory(installed)
            for bad_policy in ("on-install", "ON-USE", "ALWAYS"):
                candidate = dict(plugin_document, authPolicy=bad_policy)
                with self.subTest(policy=bad_policy), self.assertRaises(
                    observer.ObservationError
                ):
                    observer.parse_plugin_receipt(
                        json.dumps(candidate).encode(),
                        session,
                        codex_home,
                        expected_tree=(),
                    )
        finally:
            observer._close_frozen_directory(other_marketplace)
            observer._close_frozen_directory(marketplace_source)
            observer._close_frozen_directory(codex_home)
            ledger = session.ledger
            session.close()
            observer.cleanup_owned_root(identity, ledger)
            parent.rmdir()

    def test_receipts_reject_duplicate_multiple_trailing_and_unconfined_paths(self):
        parent = Path(tempfile.mkdtemp(prefix="axiom-receipts-parent-"))
        root = parent / "owned"
        root.mkdir(mode=0o700)
        identity = observer.freeze_owned_root(root)
        session = observer.OwnedRootSession(identity)
        codex_home: observer.FrozenDirectoryIdentity | None = None
        try:
            installed_relative = (
                f"codex-home/plugins/cache/{observer.MARKETPLACE_NAME}/"
                f"{observer.PLUGIN_NAME}/{observer.PLUGIN_VERSION}"
            )
            session.mkdir(installed_relative, parents=True, phase="receipt-test")
            session.mkdir("outside", phase="receipt-test")
            codex_home = session.open_directory(
                "codex-home", phase="receipt-test", freeze_tree=False
            )
            inside = (
                f"/proc/self/fd/{codex_home.descriptor}/plugins/cache/"
                f"{observer.MARKETPLACE_NAME}/{observer.PLUGIN_NAME}/"
                f"{observer.PLUGIN_VERSION}"
            )
            outside = f"/proc/self/fd/{codex_home.descriptor}/outside"
            base = {
                "pluginId": observer.PLUGIN_ID,
                "name": "axiom",
                "marketplaceName": observer.MARKETPLACE_NAME,
                "version": observer.PLUGIN_VERSION,
                "installedPath": inside,
                "authPolicy": "ON_INSTALL",
            }
            bad = [
                (json.dumps(base) + json.dumps(base)).encode(),
                (json.dumps(base) + " trailing").encode(),
                json.dumps(dict(base, installedPath=outside)).encode(),
                json.dumps(dict(
                    base,
                    installedPath=(
                        f"/proc/self/fd/{codex_home.descriptor}/plugins/axiom"
                    ),
                )).encode(),
                json.dumps(dict(
                    base,
                    installedPath=(
                        f"/proc/self/fd/{codex_home.descriptor}/plugins/cache/"
                        f"{observer.MARKETPLACE_NAME}/{observer.PLUGIN_ID}/"
                        f"{observer.PLUGIN_VERSION}"
                    ),
                )).encode(),
                json.dumps(dict(base, name="other-plugin")).encode(),
                json.dumps(dict(base, marketplaceName="other-marketplace")).encode(),
                json.dumps(dict(base, version="0.10.1")).encode(),
                b'{"pluginId":"a","pluginId":"b"}',
            ]
            for ordinal, data in enumerate(bad):
                with self.subTest(ordinal=ordinal), self.assertRaises(
                    observer.ObservationError
                ):
                    observer.parse_plugin_receipt(
                        data, session, codex_home, expected_tree=()
                    )
            with self.assertRaisesRegex(observer.ObservationError, "byte limit"):
                observer.parse_plugin_receipt(
                    b" " * (observer.MAX_RECEIPT_BYTES + 1),
                    session,
                    codex_home,
                    expected_tree=(),
                )
        finally:
            observer._close_frozen_directory(codex_home)
            ledger = session.ledger
            session.close()
            observer.cleanup_owned_root(identity, ledger)
            parent.rmdir()

    def test_inert_git_fixture_rejects_unknown_internal_state(self):
        fixture_document = load_json(FIXTURES)
        with tempfile.TemporaryDirectory(prefix="axiom-fixture-git-") as directory:
            root = Path(directory) / "owned"
            root.mkdir(mode=0o700)
            identity = observer.freeze_owned_root(root)
            session = observer.OwnedRootSession(identity)
            unknown: Path | None = None
            try:
                session.mkdir("workspace", phase="fixture-test-workspace")
                fact = observer.materialize_fixture_owned(
                    session,
                    "workspace",
                    fixture_document,
                    observer.EXPECTED_CASE_IDS[0],
                )
                self.assertTrue(fact.git_repository)
                workspace = session.alias("workspace")
                git_directory = workspace / ".git"
                os.chmod(git_directory, 0o700)
                unknown = git_directory / "unknown"
                unknown.write_text("reject\n", encoding="ascii")
                with self.assertRaisesRegex(observer.ObservationError, "unknown child"):
                    observer._observe_inert_git_facts(workspace, True)
            finally:
                if unknown is not None and unknown.exists():
                    unknown.unlink()
                    os.chmod(unknown.parent, 0o555)
                ledger = session.ledger
                session.close()
                observer.cleanup_owned_root(identity, ledger)


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
    def setUp(self) -> None:
        self._directory_fds: dict[int, tuple[int, ...]] = {}
        self._schema_ordinal = 0

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
        directories = {}
        for name in ("codex-home", "home", "config", "cache", "data", "workspace"):
            path = run_root / name
            path.mkdir(mode=0o700)
            directories[name] = os.open(path, observer._directory_flags())
        identities = observer.validate_protocol_documents(REPOSITORY_ROOT)
        capability = observer._mint_fake_execution_capability(
            protocol_digest=identities["protocolDigest"],
            entrypoint_sha256=hashlib.sha256(ENTRYPOINT.read_bytes()).hexdigest(),
            module_sha256=hashlib.sha256(MODULE.read_bytes()).hexdigest(),
            executable=executable,
            run_root=observer.freeze_owned_root(run_root),
            test_launch_sequence=(("model-case", observer.EXPECTED_CASE_IDS[0]),),
        )
        self._directory_fds[id(capability)] = tuple(directories.values())
        return run_root, executable_path, executable, capability

    def close_capability(self, run_root: Path, capability: object) -> None:
        observer._retire_capability(capability)
        for descriptor in self._directory_fds.pop(id(capability), ()):
            os.close(descriptor)
        if run_root.exists():
            shutil.rmtree(run_root)

    def model_environment(self, capability: object, scenario: str) -> dict[str, str]:
        roots = self._directory_fds.get(id(capability))
        if roots is None:
            roots = next(iter(self._directory_fds.values()))
        return observer.build_isolated_environment(
            codex_home=Path(f"/proc/self/fd/{roots[0]}"),
            home=Path(f"/proc/self/fd/{roots[1]}"),
            xdg_config_home=Path(f"/proc/self/fd/{roots[2]}"),
            xdg_cache_home=Path(f"/proc/self/fd/{roots[3]}"),
            xdg_data_home=Path(f"/proc/self/fd/{roots[4]}"),
            additions={
                "AXIOM_FAKE_SCENARIO": scenario,
                "AXIOM_FAKE_OUTCOME": "selected",
                "AXIOM_FAKE_ROUTES": '["using-axiom"]',
                "AXIOM_FAKE_CLARIFICATIONS": "0",
                "AXIOM_FAKE_FRONT_DOOR": "true",
                "AXIOM_FAKE_NO_PLUGIN_CONTROL": "true",
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
        prompt: bytes | None = None,
        case_id: str = observer.EXPECTED_CASE_IDS[0],
        schema_argument: Path | None = None,
    ) -> observer.ProcessCapture:
        roots = self._directory_fds.get(id(capability))
        if roots is None:
            roots = next(iter(self._directory_fds.values()))
        workspace = Path(f"/proc/self/fd/{roots[5]}")
        identities = observer.validate_protocol_documents(REPOSITORY_ROOT)
        cases = observer.load_golden_cases(REPOSITORY_ROOT)
        case_index = observer.EXPECTED_CASE_IDS.index(case_id)
        materialization = observer.materialize_case_contract(
            materialization_seed=b"\x01" * 32,
            ordinal=case_index + 1,
            protocol_digest=identities["protocolDigest"],
            model_schema=load_json(MODEL_SCHEMA),
            prompt_envelope=load_json(PROMPT),
            request=cases[case_index]["request"],
        )
        self._schema_ordinal += 1
        schema_path = run_root / f"model-response-schema-{self._schema_ordinal}.json"
        schema_path.write_bytes(materialization.schema_bytes)
        schema_path.chmod(0o400)
        schema_fd = os.open(
            schema_path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        metadata = os.fstat(schema_fd)
        schema = observer.FrozenFileIdentity(
            descriptor=schema_fd,
            device=metadata.st_dev,
            inode=metadata.st_ino,
            mode=metadata.st_mode,
            size=metadata.st_size,
            sha256=hashlib.sha256(materialization.schema_bytes).hexdigest(),
        )
        argv = observer.build_codex_argv(
            executable_path,
            (
                Path(f"/proc/self/fd/{schema_fd}")
                if schema_argument is None
                else schema_argument
            ),
            workspace,
        )
        try:
            return observer._launch_bounded_process(
                capability,
                executable,
                argv,
                purpose="model-case",
                case_id=case_id,
                prompt=materialization.prompt_bytes if prompt is None else prompt,
                cwd=workspace,
                env=environment,
                timeout_seconds=timeout,
                maximum_stdout=maximum_stdout,
                maximum_stderr=maximum_stderr,
                inherited_fds=roots,
                schema_object=schema,
                expected_schema_bytes=materialization.schema_bytes,
                popen_factory=factory,
            )
        finally:
            os.close(schema_fd)

    def test_model_launch_rejects_plain_schema_path_without_starting_child(self):
        run_root, executable_path, executable, capability = self.make_capability()
        starts = 0

        def factory(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
            nonlocal starts
            starts += 1
            return subprocess.Popen(*args, **kwargs)

        try:
            with self.assertRaises(observer.ProcessBoundaryError):
                self.launch(
                    run_root=run_root,
                    executable_path=executable_path,
                    executable=executable,
                    capability=capability,
                    environment=self.model_environment(capability, "happy"),
                    schema_argument=run_root / "ordinary-path-schema.json",
                    factory=factory,
                )
            self.assertEqual(0, starts)
            self.assertTrue(observer._capability_state(capability).hard_stopped)
        finally:
            self.close_capability(run_root, capability)

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
                environment=self.model_environment(capability, "timeout"),
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
                        environment=self.model_environment(capability, scenario),
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
                    environment=self.model_environment(capability, "early-exit"),
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
            environment = self.model_environment(capability, "happy")
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
                    environment=self.model_environment(capability, "happy"),
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
        directory_fds = []
        for name in ("codex-home", "home", "config", "cache", "data", "workspace"):
            path = run_root / name
            path.mkdir(mode=0o700)
            directory_fds.append(os.open(path, observer._directory_flags()))
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
        self._directory_fds[id(capability)] = tuple(directory_fds)
        starts = 0

        def factory(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
            nonlocal starts
            starts += 1
            return subprocess.Popen(*args, **kwargs)

        try:
            environment = self.model_environment(capability, "happy")
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
    def make_root(
        self,
    ) -> tuple[
        Path,
        Path,
        observer.OwnedRootIdentity,
        observer.OwnedObjectLedger,
    ]:
        parent = Path(tempfile.mkdtemp(prefix="axiom-cleanup-parent-"))
        root = parent / "owned"
        root.mkdir(mode=0o700)
        identity = observer.freeze_owned_root(root)
        session = observer.OwnedRootSession(identity)
        try:
            session.mkdir("nested", phase="cleanup-test")
            session.create_file(
                "nested/file", b"owned", phase="cleanup-test"
            )
            return parent, root, identity, session.ledger
        finally:
            session.close()

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
        parent, root, identity, ledger = self.make_root()
        try:
            observer.cleanup_owned_root(identity, ledger)
            self.assertFalse(root.exists())
            self.assertEqual([], list(parent.iterdir()))
        finally:
            self.tear_down_parent(parent)

    def test_cleanup_rejects_missing_rename_and_replacement(self):
        scenarios = ("missing", "rename", "replacement", "symlink")
        for scenario in scenarios:
            parent, root, identity, ledger = self.make_root()
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
                    observer.cleanup_owned_root(identity, ledger)
                if scenario == "replacement":
                    self.assertEqual("preserve", (root / "unknown").read_text())
                if scenario == "symlink":
                    self.assertTrue(root.is_symlink())
            finally:
                self.tear_down_parent(parent)

    def test_replacement_appearing_after_root_quarantine_is_preserved(self):
        parent, root, identity, ledger = self.make_root()
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
                    observer.cleanup_owned_root(identity, ledger)
            self.assertEqual("preserve", (root / "unknown").read_text())
        finally:
            self.tear_down_parent(parent)

    def test_nested_replacement_after_child_quarantine_is_preserved(self):
        parent, root, identity, ledger = self.make_root()
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
                    observer.cleanup_owned_root(identity, ledger)
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

    def test_replacement_before_first_child_stat_is_never_adopted_or_deleted(self):
        parent, root, identity, ledger = self.make_root()
        original_stat = observer.os.stat
        replaced = False

        def replace_before_stat(
            path: object, *args: object, **kwargs: object
        ) -> os.stat_result:
            nonlocal replaced
            descriptor = kwargs.get("dir_fd")
            if path == "nested" and descriptor is not None and not replaced:
                os.rename(
                    "nested",
                    "moved-original",
                    src_dir_fd=descriptor,
                    dst_dir_fd=descriptor,
                )
                os.mkdir("nested", mode=0o700, dir_fd=descriptor)
                unknown = os.open(
                    "nested/unknown",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=descriptor,
                )
                os.write(unknown, b"preserve")
                os.close(unknown)
                replaced = True
            return original_stat(path, *args, **kwargs)

        try:
            with mock.patch.object(observer.os, "stat", side_effect=replace_before_stat):
                with self.assertRaisesRegex(
                    observer.ObservationError, "creation ledger|manual cleanup"
                ):
                    observer.cleanup_owned_root(identity, ledger)
            quarantine = next(parent.glob(".axiom-owned-cleanup-*"))
            self.assertEqual(
                b"preserve", (quarantine / "nested" / "unknown").read_bytes()
            )
            self.assertEqual(
                b"owned", (quarantine / "moved-original" / "file").read_bytes()
            )
        finally:
            self.tear_down_parent(parent)

    def test_identity_mismatch_after_quarantine_restores_unknown_replacement(self):
        parent, root, identity, ledger = self.make_root()
        original_rename = observer._rename_noreplace
        calls = 0

        def replace_quarantine(
            source_parent_fd: int,
            source_name: str,
            destination_parent_fd: int,
            destination_name: str,
        ) -> None:
            nonlocal calls
            original_rename(
                source_parent_fd,
                source_name,
                destination_parent_fd,
                destination_name,
            )
            calls += 1
            if calls == 2:
                os.rename(
                    destination_name,
                    "moved-original",
                    src_dir_fd=destination_parent_fd,
                    dst_dir_fd=destination_parent_fd,
                )
                os.mkdir(destination_name, mode=0o700, dir_fd=destination_parent_fd)
                unknown = os.open(
                    f"{destination_name}/unknown",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=destination_parent_fd,
                )
                os.write(unknown, b"preserve")
                os.close(unknown)

        try:
            with mock.patch.object(observer, "_rename_noreplace", replace_quarantine):
                with self.assertRaisesRegex(
                    observer.ObservationError, "unknown and was preserved"
                ):
                    observer.cleanup_owned_root(identity, ledger)
            quarantine = next(parent.glob(".axiom-owned-cleanup-*"))
            self.assertEqual(b"preserve", (quarantine / "nested" / "unknown").read_bytes())
            self.assertEqual(
                b"owned", (quarantine / "moved-original" / "file").read_bytes()
            )
        finally:
            self.tear_down_parent(parent)

    def test_busy_child_failure_is_not_reported_as_cleanup_success(self):
        parent, root, identity, ledger = self.make_root()
        original_rmdir = os.rmdir

        def busy(path: object, *args: object, **kwargs: object) -> None:
            if str(path).startswith(".axiom-child-cleanup-"):
                raise OSError(16, "busy")
            original_rmdir(path, *args, **kwargs)

        try:
            with mock.patch.object(observer.os, "rmdir", busy):
                with self.assertRaisesRegex(observer.ObservationError, "cannot remove"):
                    observer.cleanup_owned_root(identity, ledger)
        finally:
            self.tear_down_parent(parent)

    def test_cleanup_rejects_cross_device_children_before_deletion(self):
        parent, root, identity, ledger = self.make_root()
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
                    observer.cleanup_owned_root(identity, ledger)
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


class DescriptorObjectBindingTests(unittest.TestCase):
    def test_unaccepted_child_receipt_objects_are_preserved_not_adopted(self):
        for scenario in ("invalid-marketplace-receipt", "invalid-plugin-receipt"):
            state = {"preserved": False}

            def hook(phase: str, facts: dict[str, object]) -> None:
                if phase == "before-cleanup":
                    session = facts["session"]
                    if scenario == "invalid-marketplace-receipt":
                        unknown = session.alias("case-01/codex-home/config.toml")
                    else:
                        unknown = session.alias(
                            "case-01/codex-home/plugins/cache/"
                            f"{observer.MARKETPLACE_NAME}/{observer.PLUGIN_NAME}/"
                            f"{observer.PLUGIN_VERSION}"
                        )
                    metadata = unknown.stat(follow_symlinks=False)
                    state["identity"] = (metadata.st_dev, metadata.st_ino)
                    state["type"] = stat.S_IFMT(metadata.st_mode)
                    if stat.S_ISREG(metadata.st_mode):
                        state["size"] = metadata.st_size
                        state["sha256"] = hashlib.sha256(
                            unknown.read_bytes()
                        ).hexdigest()
                elif phase == "after-cleanup":
                    identity = facts["rootIdentity"]
                    quarantine = next(identity.path.parent.glob(".axiom-owned-cleanup-*"))
                    matches = find_objects_by_identity(quarantine, state["identity"])
                    self.assertEqual(1, len(matches))
                    preserved = matches[0].stat(follow_symlinks=False)
                    self.assertEqual(state["type"], stat.S_IFMT(preserved.st_mode))
                    if stat.S_ISREG(preserved.st_mode):
                        self.assertEqual(state["size"], preserved.st_size)
                        self.assertEqual(
                            state["sha256"],
                            hashlib.sha256(matches[0].read_bytes()).hexdigest(),
                        )
                    state["preserved"] = True
                    remove_preserved_run_objects(identity)

            with self.subTest(scenario=scenario):
                result = fake_run(
                    {observer.EXPECTED_CASE_IDS[0]: scenario},
                    hook=hook,
                    seed=b"\x10" * 32,
                )
                self.assertTrue(state["preserved"])
                self.assertEqual("incomplete", result["overallStatus"])
                self.assertTrue(result["cleanup"]["manualCleanupRequired"])
                self.assertEqual(0, result["summary"]["modelCallCount"])

    def test_schema_path_replacement_cannot_change_child_consumed_object(self):
        replacement_bytes = b'{"type":"object"}\n'

        def object_identity(path: Path) -> tuple[int, int]:
            facts = path.stat(follow_symlinks=False)
            return (facts.st_dev, facts.st_ino)

        def matching_identity(
            paths: list[Path], expected: tuple[int, int]
        ) -> list[Path]:
            return [
                path
                for path in paths
                if object_identity(path) == expected
            ]

        for scenario in ("rename-away", "replacement", "symlink"):
            state = {"mutated": False, "preserved": False}

            def hook(phase: str, facts: dict[str, object]) -> None:
                if phase == "after-schema-create" and not state["mutated"]:
                    session = facts["session"]
                    schema_relative = Path(facts["schemaRelative"])
                    schema_path = session.alias(schema_relative)
                    original_facts = schema_path.stat(follow_symlinks=False)
                    self.assertTrue(stat.S_ISREG(original_facts.st_mode))
                    state["originalIdentity"] = (
                        original_facts.st_dev,
                        original_facts.st_ino,
                    )
                    state["originalMode"] = stat.S_IFMT(original_facts.st_mode)
                    state["originalSize"] = original_facts.st_size
                    state["originalSha256"] = hashlib.sha256(
                        schema_path.read_bytes()
                    ).hexdigest()
                    state["schemaParentIdentity"] = object_identity(
                        schema_path.parent
                    )
                    moved = schema_path.with_name("original-schema")
                    schema_path.rename(moved)
                    self.assertEqual(
                        state["originalIdentity"], object_identity(moved)
                    )
                    if scenario == "replacement":
                        schema_path.write_bytes(replacement_bytes)
                        replacement_facts = schema_path.stat(follow_symlinks=False)
                        self.assertTrue(stat.S_ISREG(replacement_facts.st_mode))
                        state["replacementIdentity"] = (
                            replacement_facts.st_dev,
                            replacement_facts.st_ino,
                        )
                        state["replacementMode"] = stat.S_IFMT(
                            replacement_facts.st_mode
                        )
                        state["replacementSha256"] = hashlib.sha256(
                            schema_path.read_bytes()
                        ).hexdigest()
                    elif scenario == "symlink":
                        schema_path.symlink_to(moved.name)
                        replacement_facts = schema_path.stat(follow_symlinks=False)
                        self.assertTrue(stat.S_ISLNK(replacement_facts.st_mode))
                        state["replacementIdentity"] = (
                            replacement_facts.st_dev,
                            replacement_facts.st_ino,
                        )
                        state["replacementMode"] = stat.S_IFMT(
                            replacement_facts.st_mode
                        )
                        state["replacementLinkTarget"] = os.readlink(schema_path)
                    state["mutated"] = True
                elif phase == "after-cleanup" and state["mutated"]:
                    identity = facts["rootIdentity"]
                    quarantines = list(
                        identity.path.parent.glob(".axiom-owned-cleanup-*")
                    )
                    self.assertEqual(1, len(quarantines))
                    (quarantine,) = quarantines

                    originals = list(quarantine.rglob("original-schema"))
                    original_matches = matching_identity(
                        originals, state["originalIdentity"]
                    )
                    self.assertEqual(1, len(original_matches))
                    (original,) = original_matches
                    original_facts = original.stat(follow_symlinks=False)
                    self.assertEqual(
                        state["originalMode"], stat.S_IFMT(original_facts.st_mode)
                    )
                    self.assertEqual(state["originalSize"], original_facts.st_size)
                    self.assertEqual(
                        state["originalSha256"],
                        hashlib.sha256(original.read_bytes()).hexdigest(),
                    )
                    self.assertEqual(
                        state["schemaParentIdentity"],
                        object_identity(original.parent),
                    )

                    candidates = list(
                        quarantine.rglob("model-response-schema.json")
                    )
                    if scenario == "replacement":
                        self.assertGreater(len(candidates), 1)
                        decoys = [
                            path
                            for path in candidates
                            if object_identity(path)
                            != state["replacementIdentity"]
                        ]
                        self.assertGreaterEqual(len(decoys), 1)
                        (decoy, *_) = decoys
                        adversarial_order = [
                            decoy,
                            *(path for path in candidates if path != decoy),
                        ]
                        self.assertNotEqual(
                            state["replacementIdentity"],
                            object_identity(adversarial_order[0]),
                        )
                        replacement_matches = matching_identity(
                            candidates, state["replacementIdentity"]
                        )
                        self.assertEqual(1, len(replacement_matches))
                        (replacement,) = replacement_matches
                        self.assertEqual(
                            replacement_matches,
                            matching_identity(
                                adversarial_order,
                                state["replacementIdentity"],
                            ),
                        )
                        replacement_facts = replacement.stat(follow_symlinks=False)
                        self.assertEqual(
                            state["replacementMode"],
                            stat.S_IFMT(replacement_facts.st_mode),
                        )
                        self.assertTrue(stat.S_ISREG(replacement_facts.st_mode))
                        self.assertEqual(
                            state["schemaParentIdentity"],
                            object_identity(replacement.parent),
                        )
                        self.assertEqual(
                            state["replacementSha256"],
                            hashlib.sha256(replacement.read_bytes()).hexdigest(),
                        )
                        self.assertEqual(replacement_bytes, replacement.read_bytes())
                        state["preserved"] = True
                    elif scenario == "symlink":
                        replacement_matches = matching_identity(
                            candidates, state["replacementIdentity"]
                        )
                        self.assertEqual(1, len(replacement_matches))
                        (replacement,) = replacement_matches
                        replacement_facts = replacement.stat(follow_symlinks=False)
                        self.assertEqual(
                            state["replacementMode"],
                            stat.S_IFMT(replacement_facts.st_mode),
                        )
                        self.assertTrue(stat.S_ISLNK(replacement_facts.st_mode))
                        self.assertEqual(
                            state["schemaParentIdentity"],
                            object_identity(replacement.parent),
                        )
                        self.assertEqual(
                            state["replacementLinkTarget"], os.readlink(replacement)
                        )
                        self.assertEqual("original-schema", os.readlink(replacement))
                        state["preserved"] = True
                    else:
                        self.assertNotIn("replacementIdentity", state)
                        state["preserved"] = True
                    remove_preserved_run_objects(identity)

            with self.subTest(scenario=scenario):
                result = fake_run(hook=hook, seed=b"\x11" * 32)
                self.assertTrue(state["mutated"])
                self.assertTrue(state["preserved"])
                expected_calls = 0 if scenario == "symlink" else 16
                self.assertEqual(expected_calls, result["summary"]["modelCallCount"])
                self.assertEqual(
                    scenario != "symlink",
                    result["cases"][0]["schemaObjectVerified"],
                )
                self.assertEqual("incomplete", result["overallStatus"])
                self.assertTrue(result["cleanup"]["manualCleanupRequired"])

    def test_mutating_the_open_schema_object_fails_before_model_launch(self):
        state = {"mutated": False}

        def hook(phase: str, facts: dict[str, object]) -> None:
            if phase == "after-schema-create" and not state["mutated"]:
                schema = facts["schema"]
                alias = Path(f"/proc/self/fd/{schema.descriptor}")
                os.chmod(alias, 0o600)
                alias.write_bytes(b'{"type":"object"}\n')
                state["mutated"] = True
            elif phase == "after-cleanup" and state["mutated"]:
                remove_preserved_run_objects(facts["rootIdentity"])

        result = fake_run(hook=hook, seed=b"\x12" * 32)
        self.assertTrue(state["mutated"])
        self.assertEqual(0, result["summary"]["modelCallCount"])
        self.assertEqual("0" * 64, result["cases"][0]["casePromptSha256"])
        self.assertEqual("incomplete", result["overallStatus"])

    def test_run_root_rename_and_repository_symlink_receive_no_writes(self):
        repository_before = observer.snapshot_tree(REPOSITORY_ROOT)
        state = {"moved_has_bundle": False, "repository_unchanged": False}

        def hook(phase: str, facts: dict[str, object]) -> None:
            if phase == "before-first-root-write":
                session = facts["session"]
                identity = session.identity
                moved = identity.path.with_name(identity.path.name + "-moved")
                identity.path.rename(moved)
                identity.path.symlink_to(REPOSITORY_ROOT, target_is_directory=True)
            elif phase == "after-cleanup":
                identity = facts["rootIdentity"]
                moved = identity.path.with_name(identity.path.name + "-moved")
                state["moved_has_bundle"] = (moved / "bundle-build").is_dir()
                state["repository_unchanged"] = (
                    observer.snapshot_tree(REPOSITORY_ROOT) == repository_before
                )
                remove_preserved_run_objects(identity)

        result = fake_run(hook=hook, seed=b"\x13" * 32)
        self.assertTrue(state["moved_has_bundle"])
        self.assertTrue(state["repository_unchanged"])
        self.assertEqual(0, result["summary"]["modelCallCount"])
        self.assertEqual("incomplete", result["overallStatus"])
        self.assertTrue(result["cleanup"]["manualCleanupRequired"])

    def test_nested_parent_substitution_is_rejected_before_descriptor_write(self):
        parent = Path(tempfile.mkdtemp(prefix="axiom-parent-binding-"))
        root = parent / "owned"
        root.mkdir(mode=0o700)
        identity = observer.freeze_owned_root(root)
        session = observer.OwnedRootSession(identity)
        repository_before = observer.snapshot_tree(REPOSITORY_ROOT)
        moved = root / "moved-safe"
        try:
            session.mkdir("safe/child", parents=True, phase="parent-binding-test")
            (root / "safe").rename(moved)
            (root / "safe").symlink_to(REPOSITORY_ROOT, target_is_directory=True)
            with self.assertRaisesRegex(observer.ObservationError, "parent"):
                session.create_file(
                    "safe/child/forbidden",
                    b"must-not-write",
                    phase="parent-binding-test",
                )
            self.assertEqual(
                repository_before, observer.snapshot_tree(REPOSITORY_ROOT)
            )
            self.assertFalse((REPOSITORY_ROOT / "child" / "forbidden").exists())
        finally:
            session.close()
            remove_test_tree(root / "safe")
            remove_test_tree(moved)
            remove_test_tree(root)
            parent.rmdir()

    def test_installed_object_replacement_and_tree_drift_hard_stop_before_launch(self):
        scenarios = (
            ("installed-after-receipt", "after-plugin-receipt"),
            ("installed-symlink-after-receipt", "after-plugin-receipt"),
            ("installed-after-snapshot", "after-protected-snapshot"),
            ("codex-home-after-receipt", "after-plugin-receipt"),
        )
        for scenario, phase_to_mutate in scenarios:
            state = {"mutated": False, "preserved": False}

            def hook(phase: str, facts: dict[str, object]) -> None:
                if phase == phase_to_mutate and not state["mutated"]:
                    installed = facts["installed"]
                    root = Path(f"/proc/self/fd/{installed.root_descriptor}")
                    path = root / installed.relative_path
                    if scenario == "codex-home-after-receipt":
                        path = root.joinpath(*Path(installed.relative_path).parts[:2])
                        moved = path.with_name("codex-home-owned-moved")
                        path.rename(moved)
                        path.mkdir(mode=0o700)
                        (path / "unknown").write_bytes(b"preserve")
                    elif phase_to_mutate == "after-plugin-receipt":
                        moved = path.with_name("axiom-owned-moved")
                        path.rename(moved)
                        if scenario == "installed-symlink-after-receipt":
                            path.symlink_to(moved.name, target_is_directory=True)
                        else:
                            path.mkdir(mode=0o700)
                            (path / "unknown").write_bytes(b"preserve")
                        replacement = path.stat(follow_symlinks=False)
                        state["replacementIdentity"] = (
                            replacement.st_dev,
                            replacement.st_ino,
                        )
                        state["replacementType"] = stat.S_IFMT(
                            replacement.st_mode
                        )
                        if path.is_symlink():
                            state["replacementTarget"] = os.readlink(path)
                    else:
                        target = path / ".codex-plugin" / "plugin.json"
                        target.chmod(0o600)
                        target.write_bytes(b"{}\n")
                    state["mutated"] = True
                elif phase == "after-cleanup" and state["mutated"]:
                    identity = facts["rootIdentity"]
                    quarantines = list(identity.path.parent.glob(".axiom-owned-cleanup-*"))
                    self.assertEqual(1, len(quarantines))
                    if scenario == "installed-symlink-after-receipt":
                        matches = find_objects_by_identity(
                            quarantines[0], state["replacementIdentity"]
                        )
                        self.assertEqual(1, len(matches))
                        replacement = matches[0].stat(follow_symlinks=False)
                        self.assertEqual(
                            state["replacementType"], stat.S_IFMT(replacement.st_mode)
                        )
                        self.assertTrue(stat.S_ISLNK(replacement.st_mode))
                        self.assertEqual(
                            state["replacementTarget"], os.readlink(matches[0])
                        )
                        state["preserved"] = True
                    elif phase_to_mutate == "after-plugin-receipt":
                        state["preserved"] = any(
                            path.read_bytes() == b"preserve"
                            for path in quarantines[0].rglob("unknown")
                        )
                    else:
                        state["preserved"] = any(
                            path.read_bytes() == b"{}\n"
                            for path in quarantines[0].rglob("plugin.json")
                        )
                    remove_preserved_run_objects(identity)

            with self.subTest(scenario=scenario):
                result = fake_run(hook=hook, seed=b"\x14" * 32)
                self.assertTrue(state["mutated"])
                self.assertTrue(state["preserved"])
                self.assertEqual(0, result["summary"]["modelCallCount"])
                self.assertEqual("incomplete", result["overallStatus"])
                self.assertTrue(result["cleanup"]["manualCleanupRequired"])


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
        commitments = [
            item["materializationCommitmentSha256"] for item in result["cases"]
        ]
        self.assertEqual(16, len(set(commitments)))
        self.assertEqual(
            observer._materialization_commitment_root(commitments),
            result["materialization"]["materializationCommitmentRootSha256"],
        )
        self.assertTrue(result["objectBindingFacts"]["schemaObjectConsumptionVerified"])
        self.assertTrue(result["objectBindingFacts"]["runRootWritesDescriptorAnchored"])
        self.assertTrue(result["objectBindingFacts"]["installedDirectoryIdentityVerified"])

    def test_real_builder_fake_orchestration_uses_source_compatible_receipts(self):
        synthetic_environment = {
            "CODEX_API_KEY": "sentinel-not-a-real-secret",
            "OPENAI_API_KEY": "second-synthetic-value",
            "AXIOM_TEST_TOKEN": "third-synthetic-value",
            "AXIOM_TEST_SECRET": "fourth-synthetic-value",
        }
        with mock.patch.object(observer.os, "environ", synthetic_environment):
            result = fake_run(real_builder=True, seed=b"\x31" * 32)
        self.assertEqual("fake-validation", result["runMode"])
        self.assertEqual("incomplete", result["overallStatus"])
        self.assertEqual(16, result["summary"]["passCount"])
        self.assertEqual(16, result["summary"]["modelCallCount"])
        self.assertEqual(15, result["executionFacts"]["marketplaceProcessCount"])
        self.assertEqual(15, result["executionFacts"]["pluginInstallProcessCount"])
        self.assertEqual(1, result["installationFacts"]["noPluginControlCaseCount"])
        for key in (
            "bundleDestinationDescriptorBound",
            "bundleCreationLedgerVerified",
            "bundleFailureCleanupIdentityBound",
            "bundleGitCredentialExcluded",
            "marketplaceSourceObjectVerified",
            "installedCacheLayoutVerified",
        ):
            self.assertTrue(result["objectBindingFacts"][key], key)
        self.assertTrue(result["cleanup"]["temporaryRootsRemoved"])
        self.assertTrue(result["cleanup"]["sourceBundleUnchanged"])
        self.assertFalse(result["cleanup"]["manualCleanupRequired"])

    def test_real_builder_failure_hard_stops_before_any_model_case(self):
        injected = False

        def hook(phase: str, facts: dict[str, object]) -> None:
            nonlocal injected
            if (
                not injected
                and phase == "builder-after-create-before-ledger"
                and facts["relativePath"] == ".axiom-no-hook-bundle-staging"
            ):
                injected = True
                raise OSError("injected builder preflight failure")

        result = fake_run(real_builder=True, hook=hook, seed=b"\x32" * 32)
        self.assertTrue(injected)
        self.assertEqual("incomplete", result["overallStatus"])
        self.assertEqual(0, result["summary"]["modelCallCount"])
        self.assertEqual("incomplete", result["cases"][0]["status"])
        self.assertTrue(
            all(case["status"] == "not-run" for case in result["cases"][1:])
        )
        self.assertTrue(result["summary"]["hardStop"])
        self.assertTrue(result["cleanup"]["manualCleanupRequired"])

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
            ("installationFacts", "installedDirectoryIdentityVerified", False),
            ("objectBindingFacts", "schemaObjectConsumptionVerified", False),
            ("objectBindingFacts", "runRootWritesDescriptorAnchored", False),
            ("objectBindingFacts", "installedDirectoryIdentityVerified", False),
            ("objectBindingFacts", "externalOutputObjectBinding", "pending"),
            ("objectBindingFacts", "bundleDestinationDescriptorBound", False),
            ("objectBindingFacts", "bundleCreationLedgerVerified", False),
            ("objectBindingFacts", "bundleFailureCleanupIdentityBound", False),
            ("objectBindingFacts", "bundleGitCredentialExcluded", False),
            ("objectBindingFacts", "marketplaceSourceObjectVerified", False),
            ("objectBindingFacts", "installedCacheLayoutVerified", False),
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

    def test_materialization_commitments_are_recomputed_not_format_checked(self):
        protocol = load_json(PROTOCOL)
        golden = observer.load_golden_cases(REPOSITORY_ROOT)

        def reset_root(candidate: dict[str, object]) -> None:
            candidate["materialization"]["materializationCommitmentRootSha256"] = (
                observer._materialization_commitment_root(
                    [item["materializationCommitmentSha256"] for item in candidate["cases"]]
                )
            )

        candidates: list[tuple[str, dict[str, object]]] = []

        candidate = copy.deepcopy(self.fake_result)
        case = candidate["cases"][0]
        case["opaqueBindingSha256"] = "1" * 64
        case["modelResponseSchemaSha256"] = "2" * 64
        case["casePromptSha256"] = "3" * 64
        case["materializationCommitmentSha256"] = "4" * 64
        reset_root(candidate)
        candidates.append(("arbitrary-unique-digests", candidate))

        candidate = copy.deepcopy(self.fake_result)
        candidate["materialization"]["materializationSeed"] = "5" * 64
        candidates.append(("seed-with-stale-case-digests", candidate))

        candidate = copy.deepcopy(self.fake_result)
        candidate["cases"][0]["materializationCommitmentSha256"] = "6" * 64
        reset_root(candidate)
        candidates.append(("forged-case-and-root", candidate))

        candidate = copy.deepcopy(self.fake_result)
        fields = (
            "opaqueBindingSha256",
            "modelResponseSchemaSha256",
            "casePromptSha256",
            "materializationCommitmentSha256",
        )
        for field in fields:
            candidate["cases"][0][field], candidate["cases"][1][field] = (
                candidate["cases"][1][field],
                candidate["cases"][0][field],
            )
        reset_root(candidate)
        candidates.append(("ordinal-exchange", candidate))

        candidate = copy.deepcopy(self.fake_result)
        candidate["cases"][0]["caseId"] = observer.EXPECTED_CASE_IDS[1]
        candidate["cases"][0]["contractVersion"] = "future"
        candidates.append(("case-identity-substitution", candidate))

        for label, replacement in (
            ("request", {"request": "different request bytes"}),
            ("fixture", {"realizedFixtureDigest": "7" * 64}),
            ("schema", {"modelResponseSchemaSha256": "8" * 64}),
            ("prompt", {"casePromptSha256": "9" * 64}),
        ):
            candidate = copy.deepcopy(self.fake_result)
            retained = candidate["cases"][0]
            case_contract = dict(golden[0])
            case_contract.update(replacement if label == "request" else {})
            for field, value in replacement.items():
                if field != "request":
                    retained[field] = value
            seed = bytes.fromhex(candidate["materialization"]["materializationSeed"])
            retained["materializationCommitmentSha256"] = (
                observer._case_materialization_commitment(
                    protocol_digest=protocol["protocolDigest"],
                    materialization_seed=seed,
                    ordinal=1,
                    case=case_contract,
                    realized_fixture_digest=retained["realizedFixtureDigest"],
                    realized_file_set_digest=retained["realizedFileSetDigest"],
                    opaque_binding_sha256=retained["opaqueBindingSha256"],
                    model_response_schema_sha256=retained["modelResponseSchemaSha256"],
                    case_prompt_sha256=retained["casePromptSha256"],
                )
            )
            reset_root(candidate)
            candidates.append((label + "-substitution", candidate))

        for label, candidate in candidates:
            with self.subTest(label=label), self.assertRaises(
                observer.ObservationError
            ):
                observer.validate_normalized_result(candidate, REPOSITORY_ROOT)

    def test_materialization_root_and_raw_token_fail_closed(self):
        candidate = copy.deepcopy(self.fake_result)
        del candidate["materialization"]["materializationCommitmentRootSha256"]
        with self.assertRaises(observer.ObservationError):
            observer.validate_normalized_result(candidate, REPOSITORY_ROOT)

        candidate = copy.deepcopy(self.fake_result)
        candidate["recordedAt"] = observer.derive_opaque_case_binding(
            bytes.fromhex(candidate["materialization"]["materializationSeed"]),
            1,
            candidate["observationProtocol"]["digest"],
        )
        with self.assertRaises(observer.ObservationError):
            observer.validate_normalized_result(candidate, REPOSITORY_ROOT)

        with tempfile.TemporaryDirectory(prefix="axiom-duplicate-root-") as directory:
            path = Path(directory) / "result.json"
            path.write_text(
                '{"materializationCommitmentRootSha256":"%s",'
                '"materializationCommitmentRootSha256":"%s"}\n'
                % ("a" * 64, "b" * 64),
                encoding="ascii",
            )
            with self.assertRaisesRegex(observer.ObservationError, "duplicate"):
                observer._load_json(Path(directory), Path("result.json"))

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
        protocol = load_json(PROTOCOL)
        seed = b"\x03" * 32
        materialization = observer.materialize_case_contract(
            materialization_seed=seed,
            ordinal=1,
            protocol_digest=protocol["protocolDigest"],
            model_schema=load_json(MODEL_SCHEMA),
            prompt_envelope=load_json(PROMPT),
            request=cases[0]["request"],
        )
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
            materialization,
            seed,
            protocol["protocolDigest"],
            error,
        )
        self.assertEqual("0" * 64, record["casePromptSha256"])
        self.assertTrue(record["modelCallAuthorized"])
        self.assertTrue(record["modelProcessStarted"])
        self.assertFalse(record["promptFullyDelivered"])

    def test_installed_copy_must_match_bundle_again_at_launch_boundary(self):
        mutated = False
        preserved = False

        def hook(phase: str, facts: dict[str, object]) -> None:
            nonlocal mutated, preserved
            if phase == "after-plugin-receipt" and not mutated:
                installed = facts["installed"]
                root = Path(f"/proc/self/fd/{installed.root_descriptor}")
                path = root / installed.relative_path
                moved = path.with_name("axiom-owned-moved")
                path.rename(moved)
                path.mkdir(mode=0o700)
                (path / "unknown").write_bytes(b"preserve")
                mutated = True
            elif phase == "after-cleanup" and mutated:
                identity = facts["rootIdentity"]
                quarantines = list(
                    identity.path.parent.glob(".axiom-owned-cleanup-*")
                )
                self.assertEqual(1, len(quarantines))
                unknown = next(quarantines[0].rglob("unknown"))
                preserved = unknown.read_bytes() == b"preserve"
                remove_preserved_run_objects(identity)

        result = fake_run(hook=hook)
        self.assertTrue(mutated)
        self.assertTrue(preserved)
        self.assertEqual("incomplete", result["overallStatus"])
        self.assertTrue(result["cleanup"]["manualCleanupRequired"])
        self.assertEqual(0, result["summary"]["modelCallCount"])

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

    def test_external_output_parent_and_name_replacements_fail_closed(self):
        scenarios = ("parent-replacement", "parent-symlink", "name-replacement")
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                top = Path(tempfile.mkdtemp(prefix="axiom-output-race-"))
                parent = top / "output-parent"
                parent.mkdir(mode=0o700)
                moved = top / "moved-parent"
                candidate = copy.deepcopy(self.fake_result)
                repository_before = observer.snapshot_tree(REPOSITORY_ROOT)

                def hook(phase: str, facts: dict[str, object]) -> None:
                    frozen = facts["parent"]
                    if scenario in {"parent-replacement", "parent-symlink"} and phase == "after-output-create":
                        parent.rename(moved)
                        if scenario == "parent-symlink":
                            parent.symlink_to(REPOSITORY_ROOT, target_is_directory=True)
                        else:
                            parent.mkdir(mode=0o700)
                            (parent / "preserve").write_bytes(b"unknown-parent")
                    elif scenario == "name-replacement" and phase == "after-output-create":
                        os.rename(
                            frozen.basename,
                            "moved-result.json",
                            src_dir_fd=frozen.descriptor,
                            dst_dir_fd=frozen.descriptor,
                        )
                        replacement = os.open(
                            frozen.basename,
                            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                            0o600,
                            dir_fd=frozen.descriptor,
                        )
                        os.write(replacement, b"preserve")
                        os.close(replacement)

                try:
                    with self.assertRaises(observer.ObservationError):
                        observer.write_normalized_result(
                            candidate,
                            parent / "result.json",
                            REPOSITORY_ROOT,
                            _test_hook=hook,
                        )
                    self.assertEqual("incomplete", candidate["overallStatus"])
                    self.assertTrue(candidate["cleanup"]["manualCleanupRequired"])
                    self.assertEqual(
                        "failed",
                        candidate["objectBindingFacts"]["externalOutputObjectBinding"],
                    )
                    self.assertEqual(
                        observer.snapshot_tree(REPOSITORY_ROOT), repository_before
                    )
                    if scenario == "parent-symlink":
                        self.assertFalse((REPOSITORY_ROOT / "result.json").exists())
                    elif scenario == "parent-replacement":
                        self.assertEqual(
                            b"unknown-parent", (parent / "preserve").read_bytes()
                        )
                        self.assertFalse((parent / "result.json").exists())
                    else:
                        self.assertEqual(
                            b"preserve", (parent / "result.json").read_bytes()
                        )
                        self.assertTrue((parent / "moved-result.json").exists())
                finally:
                    remove_test_tree(parent)
                    remove_test_tree(moved)
                    top.rmdir()


if __name__ == "__main__":
    unittest.main()
