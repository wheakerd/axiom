#!/usr/bin/python3
"""Independent deterministic Codex test double for the no-Hook observer."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path


MAX_FAKE_PROMPT_BYTES = 512 * 1024
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


def main() -> int:
    arguments = sys.argv[1:]
    if "CODEX_API_KEY" in os.environ:
        return 41
    isolated_plugin_arguments = (
        arguments[2:]
        if arguments[:2] == ["-c", 'cli_auth_credentials_store="file"']
        else None
    )
    if isolated_plugin_arguments is not None and isolated_plugin_arguments[:3] == [
        "plugin", "marketplace", "add"
    ]:
        append_call_fact("marketplace", arguments)
        emit_receipt({
            "marketplaceName": "axiom-no-hook-observer",
            "installedRoot": os.environ["AXIOM_FAKE_MARKETPLACE_ROOT"],
            "alreadyAdded": False,
        })
        return 0
    if isolated_plugin_arguments is not None and isolated_plugin_arguments[:2] == [
        "plugin", "add"
    ]:
        source = Path(os.environ["AXIOM_FAKE_BUNDLE"])
        destination = Path(os.environ["AXIOM_FAKE_INSTALLED_PATH"])
        shutil.copytree(source, destination, copy_function=shutil.copyfile)
        append_call_fact("plugin-install", arguments)
        emit_receipt({
            "pluginId": "axiom@axiom-no-hook-observer", "name": "axiom",
            "marketplaceName": "axiom-no-hook-observer", "version": "0.10.0",
            "installedPath": str(destination), "authPolicy": "ON_INSTALL",
        })
        return 0
    if not arguments or arguments[0] != "exec" or arguments[-1] != "-":
        return 2
    supplied = {arguments[index + 1] for index, value in enumerate(arguments[:-1]) if value == "-c"}
    if not FEATURE_OVERRIDES <= supplied or "mcp_servers={}" not in supplied:
        return 42
    scenario = os.environ.get("AXIOM_FAKE_SCENARIO", "happy")
    if scenario == "early-exit":
        return 0
    prompt = sys.stdin.buffer.read(MAX_FAKE_PROMPT_BYTES + 1)
    if len(prompt) > MAX_FAKE_PROMPT_BYTES or not prompt:
        return 4
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
