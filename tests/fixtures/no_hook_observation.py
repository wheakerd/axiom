#!/usr/bin/python3
"""Independent deterministic Codex test double for the no-Hook observer."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import sys
import time
from pathlib import Path


MAX_FAKE_PROMPT_BYTES = 512 * 1024
MAX_FAKE_SCHEMA_BYTES = 64 * 1024
THREAD_ID = "01890f32-7abc-7def-8abc-0123456789ab"
FEATURE_OVERRIDES = {
    "features.shell_tool=false", "features.unified_exec=false",
    "features.shell_zsh_fork=false", "features.unified_exec_zsh_fork=false",
    "features.hooks=false", "features.plugin_hooks=false",
    "features.shell_snapshot=false", "features.shell_snapshot_v2=false",
    "features.deferred_executor=false", "features.code_mode=false",
    "features.code_mode_buffered_exec=false", "features.code_mode_host=false",
    "features.code_mode_prewarm=false", "features.code_mode_interrupt=false",
    "features.code_mode_only=false", "features.js_repl=false",
    "features.js_repl_tools_only=false", "features.codex_git_commit=false",
    "features.memories=false", "features.chronicle=false",
    "features.apply_patch_freeform=false",
    "features.apply_patch_streaming_events=false",
    "features.exec_permission_approvals=false", "features.write_stdin_approval=false",
    "features.request_permissions_tool=false", "features.request_rule=false",
    "features.remote_models=false", "features.unbounded_connection_retries=false",
    "features.multi_agent=false", "features.multi_agent_v2=false",
    "features.multi_agent_mode=false", "features.enable_fanout=false",
    "features.collaboration_modes=false", "features.send_async_message=false",
    "features.apps=false", "features.psp=false", "features.enable_mcp_apps=false",
    "features.mcp_2026_07_28=false", "features.mcp_oauth_refresh_coordination=false",
    "features.apps_mcp_path_override=false", "features.tool_search=false",
    "features.tool_search_always_defer_mcp_tools=false",
    "features.deferred_tool_world_state=false",
    "features.non_prefixed_mcp_tool_names=false", "features.tool_suggest=false",
    "features.unavailable_dummy_tools=false",
    "features.recommended_plugins=false", "features.plugins=true",
    "features.executor_capability_discovery=false",
    "features.skip_host_skill_discovery=true", "features.remote_plugin=false",
    "features.plugin_sharing=false", "features.external_migration=false",
    "features.view_image=false",
    "features.sleep_tool=false", "features.image_generation=false",
    "features.in_app_browser=false", "features.in_app_chat=false",
    "features.in_app_dictation=false",
    "features.in_app_local_automation=false", "features.in_app_updates=false",
    "features.browser_use=false", "features.browser_use_full_cdp_access=false",
    "features.browser_use_external=false", "features.computer_use=false",
    "features.skill_mcp_dependency_install=false",
    "features.skill_search=false", "features.skill_env_var_dependency_prompt=false",
    "features.mentions_v2=false", "features.steer=false",
    "features.default_mode_request_user_input=false",
    "features.tool_call_mcp_elicitation=false",
    "features.auth_elicitation=false", "features.guardian_approval=false",
    "features.guardian_reuse_parent_compaction=false",
    "features.guardian_enhanced_node_repl_transcripts=false",
    "features.guardian_node_repl_transcript_images=false",
    "features.guardianv2=false", "features.guardian_ext=false",
    "features.goals=false", "features.artifact=false",
    "features.step_model_switching=false",
    "features.remote_control=false", "features.realtime_conversation=false",
    "features.web_search_request=false", "features.web_search_cached=false",
    "features.standalone_web_search=false", "features.search_tool=false",
    "features.network_proxy=false", "features.respect_system_proxy=false",
    "features.external_agent_memory_import=false", "features.tui_app_server=false",
    "features.prevent_idle_sleep=false", "features.responses_websockets=false",
    "features.responses_websockets_v2=false", "features.use_agent_identity=false",
    "features.workspace_dependencies=false",
}


def emit(value: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n")
    sys.stdout.flush()


def emit_receipt(value: dict[str, object]) -> None:
    # Codex 0.153.0 uses serde_json::to_string_pretty for plugin receipts.
    sys.stdout.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    sys.stdout.flush()


def append_call_fact(kind: str, argv: list[str], prompt: bytes = b"") -> None:
    target = os.environ.get("AXIOM_FAKE_CALL_LOG")
    if not target:
        return
    fact = {
        "kind": kind,
        "stdinSentinel": bool(argv and argv[-1] == "-"),
        "promptSha256": hashlib.sha256(prompt).hexdigest() if prompt else None,
        "processDomainBound": (
            os.environ.get("AXIOM_FAKE_PROCESS_DOMAIN")
            == "deterministic-enrolled"
        ),
    }
    with open(target, "a", encoding="ascii", newline="\n") as stream:
        stream.write(json.dumps(fact, sort_keys=True, separators=(",", ":")) + "\n")


def response(prompt: bytes) -> dict[str, object]:
    text = prompt.decode("utf-8")
    binding_lines = [line for line in text.splitlines() if line.startswith("opaqueCaseBinding: ")]
    if len(binding_lines) != 1:
        raise ValueError("opaque binding missing or repeated")
    binding = binding_lines[0].split(": ", 1)[1]
    return {
        "profileId": "openai-hook-independent-v1",
        "opaqueCaseBinding": binding,
        "contractBindings": {
            "profileContractSha256": "b693580201a51fb5ecc5058b2e6ee8e63ddb948580f7fee7ce6042215ec07a88",
            "goldenSetSha256": "05febacecdf36ac05ae95d55e835c4d207c4a24dc2bb68a44cb62aa3e108a40c",
            "hostCaseSetSha256": "cceafef1e178bf46d145e86fb0a1768be86a5e47856c8bd6d4fa03f3ac3da13a",
        },
        "discoveryOutcome": os.environ["AXIOM_FAKE_OUTCOME"],
        "selectedRoutes": json.loads(os.environ["AXIOM_FAKE_ROUTES"]),
        "clarificationCount": int(os.environ["AXIOM_FAKE_CLARIFICATIONS"]),
        "usingAxiomFrontDoorObserved": os.environ["AXIOM_FAKE_FRONT_DOOR"] == "true",
        "sessionStartObserved": False,
        "mutationAttempted": False,
        "mutationObserved": False,
    }


def validate_fd_backed_schema(arguments: list[str], prompt: bytes) -> None:
    try:
        schema_path = arguments[arguments.index("--output-schema") + 1]
    except (ValueError, IndexError) as error:
        raise ValueError("output schema argument missing") from error
    if re.fullmatch(r"/proc/self/fd/[0-9]+", schema_path) is None:
        raise ValueError("output schema is not an inherited fd alias")
    descriptor = os.open(schema_path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_FAKE_SCHEMA_BYTES:
            raise ValueError("output schema object is invalid")
        chunks = bytearray()
        while len(chunks) <= MAX_FAKE_SCHEMA_BYTES:
            chunk = os.read(
                descriptor,
                min(8192, MAX_FAKE_SCHEMA_BYTES + 1 - len(chunks)),
            )
            if not chunk:
                break
            chunks.extend(chunk)
        if len(chunks) > MAX_FAKE_SCHEMA_BYTES or len(chunks) != metadata.st_size:
            raise ValueError("output schema exceeds its byte bound")
    finally:
        os.close(descriptor)

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate schema key")
            result[key] = value
        return result

    schema = json.loads(bytes(chunks), object_pairs_hook=reject_duplicates)
    binding_lines = [
        line for line in prompt.decode("utf-8").splitlines()
        if line.startswith("opaqueCaseBinding: ")
    ]
    if len(binding_lines) != 1:
        raise ValueError("prompt binding missing or repeated")
    binding = binding_lines[0].split(": ", 1)[1]
    # This independent fixture owns its expected source contract.  It does not
    # import parser constants or derive acceptance from production code.
    expected = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/wheakerd/axiom/blob/main/evals/no-hook-observation/codex-model-response-schema-v1.json",
        "title": "Axiom Codex blinded route-assessment response v1",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "profileId", "opaqueCaseBinding", "contractBindings",
            "discoveryOutcome", "selectedRoutes", "clarificationCount",
            "usingAxiomFrontDoorObserved", "sessionStartObserved",
            "mutationAttempted", "mutationObserved",
        ],
        "properties": {
            "profileId": {"const": "openai-hook-independent-v1"},
            "opaqueCaseBinding": {"type": "string", "const": binding},
            "contractBindings": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "profileContractSha256", "goldenSetSha256",
                    "hostCaseSetSha256",
                ],
                "properties": {
                    "profileContractSha256": {"const": "b693580201a51fb5ecc5058b2e6ee8e63ddb948580f7fee7ce6042215ec07a88"},
                    "goldenSetSha256": {"const": "05febacecdf36ac05ae95d55e835c4d207c4a24dc2bb68a44cb62aa3e108a40c"},
                    "hostCaseSetSha256": {"const": "cceafef1e178bf46d145e86fb0a1768be86a5e47856c8bd6d4fa03f3ac3da13a"},
                },
            },
            "discoveryOutcome": {
                "enum": ["selected", "clarification", "no-route", "unavailable"]
            },
            "selectedRoutes": {
                "type": "array", "minItems": 0, "maxItems": 2,
                "uniqueItems": True,
                "items": {"enum": [
                    "using-axiom", "agents-architect", "agent-plugin-architect",
                    "confirm-external-action", "optimize-codex-usage",
                    "reversible-system-change", "review-axiom-task",
                    "traceable-git-submit",
                ]},
            },
            "clarificationCount": {"type": "integer", "minimum": 0, "maximum": 1},
            "usingAxiomFrontDoorObserved": {"type": "boolean"},
            "sessionStartObserved": {"type": "boolean"},
            "mutationAttempted": {"type": "boolean"},
            "mutationObserved": {"type": "boolean"},
        },
    }
    if schema != expected:
        raise ValueError("output schema bytes do not materialize the exact source contract")


def validate_installed_object_visibility() -> None:
    """Independently require CODEX_HOME lookup to reach the frozen installed object."""
    codex_home = Path(os.environ["CODEX_HOME"])
    installed_alias = os.environ.get("AXIOM_FAKE_INSTALLED_OBJECT")
    no_plugin = os.environ.get("AXIOM_FAKE_NO_PLUGIN_CONTROL")
    if (installed_alias is None) == (no_plugin is None):
        raise ValueError("fake model launch lacks one closed plugin-state proof")
    if no_plugin is not None:
        if no_plugin != "true" or (codex_home / "plugins").exists():
            raise ValueError("fake no-plugin control is not empty")
        return
    installed = Path(installed_alias)
    visible = (
        codex_home
        / "plugins"
        / "cache"
        / "axiom-no-hook-observer"
        / "axiom"
        / "0.10.0"
    )
    installed_stat = installed.stat()
    visible_stat = visible.stat()
    if (
        not stat.S_ISDIR(installed_stat.st_mode)
        or not stat.S_ISDIR(visible_stat.st_mode)
        or (installed_stat.st_dev, installed_stat.st_ino)
        != (visible_stat.st_dev, visible_stat.st_ino)
    ):
        raise ValueError("fake child does not see the frozen installed object")


def main() -> int:
    arguments = sys.argv[1:]
    if "CODEX_API_KEY" in os.environ:
        return 41
    scenario = os.environ.get("AXIOM_FAKE_SCENARIO", "happy")
    isolated_plugin_arguments = (
        arguments[2:]
        if arguments[:2] == ["-c", 'cli_auth_credentials_store="file"']
        else None
    )
    if isolated_plugin_arguments is not None and isolated_plugin_arguments[:3] == [
        "plugin", "marketplace", "add"
    ]:
        marketplace_source = Path(os.environ["AXIOM_FAKE_MARKETPLACE_ROOT"])
        codex_home = Path(os.environ["CODEX_HOME"])
        metadata = marketplace_source.stat()
        if not stat.S_ISDIR(metadata.st_mode):
            return 44
        # Independently mirror the rust-v0.153.0 local-source effects: the
        # generic marketplace install root exists, while config points to the
        # source object itself rather than to a copied marketplace.
        (codex_home / ".tmp" / "marketplaces").mkdir(parents=True, exist_ok=False)
        (codex_home / "config.toml").write_text(
            "[marketplaces.axiom-no-hook-observer]\n"
            "source_type = \"local\"\n"
            f"source = {json.dumps(str(marketplace_source))}\n",
            encoding="utf-8",
            newline="\n",
        )
        append_call_fact("marketplace", arguments)
        emit_receipt({
            "marketplaceName": "axiom-no-hook-observer",
            "installedRoot": str(marketplace_source),
            "alreadyAdded": scenario == "invalid-marketplace-receipt",
        })
        return 0
    if isolated_plugin_arguments is not None and isolated_plugin_arguments[:2] == [
        "plugin", "add"
    ]:
        source = Path(os.environ["AXIOM_FAKE_BUNDLE"])
        destination = Path(os.environ["AXIOM_FAKE_INSTALLED_PATH"])
        destination.parent.mkdir(parents=True, exist_ok=False)
        shutil.copytree(source, destination, copy_function=shutil.copyfile)
        append_call_fact("plugin-install", arguments)
        emit_receipt({
            "pluginId": "axiom@axiom-no-hook-observer", "name": "axiom",
            "marketplaceName": "axiom-no-hook-observer", "version": "0.10.0",
            "installedPath": str(destination),
            "authPolicy": (
                "on-install"
                if scenario == "invalid-plugin-receipt"
                else "ON_INSTALL"
            ),
        })
        return 0
    if not arguments or arguments[0] != "exec" or arguments[-1] != "-":
        return 2
    supplied = {arguments[index + 1] for index, value in enumerate(arguments[:-1]) if value == "-c"}
    if not FEATURE_OVERRIDES <= supplied or "mcp_servers={}" not in supplied:
        return 42
    if scenario == "early-exit":
        return 0
    prompt = sys.stdin.buffer.read(MAX_FAKE_PROMPT_BYTES + 1)
    if len(prompt) > MAX_FAKE_PROMPT_BYTES or not prompt:
        return 4
    try:
        validate_fd_backed_schema(arguments, prompt)
        validate_installed_object_visibility()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return 43
    append_call_fact("model-case", arguments, prompt)
    if scenario == "timeout":
        time.sleep(30)
        return 0
    if scenario == "oversized-stdout":
        sys.stdout.write("x" * (1024 * 1024 + 1)); sys.stdout.flush(); return 0
    if scenario == "oversized-stderr":
        sys.stderr.write("x" * (256 * 1024 + 1)); sys.stderr.flush(); return 0
    if scenario == "stderr":
        sys.stderr.write("unexpected diagnostic\n"); sys.stderr.flush()
    if scenario == "malformed":
        sys.stdout.write("{not-json}\n"); return 0
    emit({"type": "thread.started", "thread_id": THREAD_ID})
    emit({"type": "turn.started"})
    item_id = "item_0"
    if scenario == "unknown-event":
        emit({"type": "future.event"})
    elif scenario == "unknown-item":
        emit({"type": "item.completed", "item": {"id": item_id, "type": "future_item"}})
    elif scenario == "unknown-status":
        emit({"type": "item.started", "item": {
            "id": item_id, "type": "command_execution", "command": "/bin/false",
            "aggregated_output": "", "exit_code": 1, "status": "future",
        }})
    elif scenario == "tool":
        emit({"type": "item.started", "item": {
            "id": item_id, "type": "command_execution", "command": "/bin/false",
            "aggregated_output": "", "exit_code": None, "status": "in_progress",
        }})
    elif scenario == "error-item":
        emit({"type": "item.completed", "item": {"id": item_id, "type": "error", "message": "discarded"}})
    else:
        result = response(prompt)
        if scenario == "binding-mismatch":
            result["opaqueCaseBinding"] = "0" * 32
        text = json.dumps(result, separators=(",", ":"), sort_keys=True)
        emit({"type": "item.completed", "item": {"id": item_id, "type": "agent_message", "text": text}})
        if scenario == "duplicate-result":
            emit({"type": "item.completed", "item": {"id": "item_1", "type": "agent_message", "text": text}})
    if scenario != "missing-terminal":
        emit({"type": "turn.completed", "usage": {
            "input_tokens": 1, "cached_input_tokens": 0, "cache_write_input_tokens": 0,
            "output_tokens": 1, "reasoning_output_tokens": 0,
        }})
    if scenario == "multiple-terminal":
        emit({"type": "turn.completed", "usage": {
            "input_tokens": 1, "cached_input_tokens": 0, "cache_write_input_tokens": 0,
            "output_tokens": 1, "reasoning_output_tokens": 0,
        }})
    if scenario == "after-terminal":
        emit({"type": "item.completed", "item": {"id": "item_1", "type": "reasoning", "text": "discarded"}})
    return int(os.environ.get("AXIOM_FAKE_EXIT", "0"))


if __name__ == "__main__":
    raise SystemExit(main())
