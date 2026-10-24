"""Codex JSONL and Claude Code stream-json observer taxonomies and fail-closed classification."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .constants import (
    CLAUDE_CODE_STREAM_JSON_CATEGORIES,
    CLAUDE_CODE_STREAM_JSON_EVENT_TYPES,
    CLAUDE_CODE_STREAM_JSON_TAXONOMY_PATH,
    CLAUDE_CODE_STREAM_JSON_TAXONOMY_VERSION,
    CLAUDE_CODE_STRUCTURED_OUTPUT_TOOL,
    CODEX_EXEC_JSONL_CATEGORIES,
    CODEX_EXEC_JSONL_ITEM_TYPES,
    CODEX_EXEC_JSONL_TAXONOMY_PATH,
    CODEX_EXEC_JSONL_TAXONOMY_VERSION,
    CODEX_EXEC_JSONL_TOP_LEVEL_TYPES,
)
from .jsonio import (
    DuplicateJsonKeyError,
    load_json_object,
    reject_duplicate_json_keys,
)
def _expected_codex_exec_jsonl_taxonomy() -> dict[str, Any]:
    return {
        "schemaVersion": "2",
        "taxonomyVersion": CODEX_EXEC_JSONL_TAXONOMY_VERSION,
        "host": {"name": "codex-cli", "version": "0.149.1"},
        "source": {
            "repository": "openai/codex",
            "tag": "rust-v0.149.1",
            "tagObject": "980a6d12110b110d29ec13bdcbe14011100b3566",
            "commit": "ff29a44391deccde0aba0f8390337d7f3c319ea4",
            "files": [
                {
                    "path": "codex-rs/exec/src/exec_events.rs",
                    "blob": "30df7f176a02c5283405a70fac2d5ef9acdcb66e",
                    "sha256": "c404928e0f2a463e19d1b263081c9d5e0380aec9f651a05ee0766f7bb7527f32",
                    "lines": "8-133,148-228",
                    "authority": "closed top-level and item enums plus public action statuses",
                },
                {
                    "path": "codex-rs/exec/src/event_processor_with_jsonl_output.rs",
                    "blob": "e8b1375114339d25c83f13fc1f6b1ac1c5c73ad8",
                    "sha256": "d43476319a61c53369055fdbbd7c093100b23bc93f9b01365db0af4c96df3e2c",
                    "lines": "142-392,397-616",
                    "authority": "item mapping, lifecycle emission, and terminal behavior",
                },
                {
                    "path": "codex-rs/exec/src/event_processor_with_jsonl_output_tests.rs",
                    "blob": "60ebd532604218bcdae7ca54f5fd949ab974ae44",
                    "sha256": "6a857b12a12e5fdc0929c9b213262334105c885b4c87eb08cde8efb4b80850a1",
                    "lines": "64-87",
                    "authority": "runtime warning maps to a non-fatal error item",
                },
            ],
        },
        "categories": list(CODEX_EXEC_JSONL_CATEGORIES),
        "topLevelTypes": {
            event_type: {"category": category, "role": role}
            for event_type, (category, role) in CODEX_EXEC_JSONL_TOP_LEVEL_TYPES.items()
        },
        "itemTypes": {
            item_type: {
                "category": category,
                "allowedEvents": sorted(allowed_events),
                **(
                    {"statuses": sorted(statuses)}
                    if statuses is not None
                    else {}
                ),
            }
            for item_type, (
                category,
                allowed_events,
                statuses,
            ) in CODEX_EXEC_JSONL_ITEM_TYPES.items()
        },
        "lifecycle": {
            "threadStartedIsFirstNormalEvent": True,
            "classifyItemBeforeSequencing": True,
            "knownItemsAllowedBetweenThreadAndTurn": True,
            "benignItemBeforeThread": "forbidden-unknown",
            "toolOrErrorBeforeThreadOrTurn": "classify-and-terminate",
            "unknownMalformedOrInvalidStatus": "fail-closed",
            "eventAfterTerminal": "fail-closed",
        },
        "batchLedger": {
            "persistCallCountBeforeLaunch": True,
            "terminalStates": ["pass", "fail", "unknown"],
            "terminalStateIsIrreversible": True,
        },
        "retention": {
            "allowedJournalFields": [
                "ordinal",
                "eventType",
                "itemType",
                "category",
                "role",
                "status",
            ],
            "forbidden": [
                "response text",
                "reasoning text",
                "tool arguments",
                "tool output",
                "identifiers",
                "credentials",
                "paths",
                "session or config content",
                "raw payload",
            ],
        },
    }


def check_codex_exec_jsonl_taxonomy(root: Path, failures: list[str]) -> None:
    """Validate the exact-version public discriminator contract."""
    path = root / "evals" / CODEX_EXEC_JSONL_TAXONOMY_PATH.name
    taxonomy = load_json_object(path, failures, root)
    if taxonomy is not None and taxonomy != _expected_codex_exec_jsonl_taxonomy():
        failures.append(
            "evals/codex-exec-jsonl-observer-v2.json drifted from the reviewed Codex 0.149.1 contract"
        )


def classify_codex_exec_jsonl_lines(lines: Iterable[bytes | str]) -> dict[str, Any]:
    """Fail closed while retaining only public discriminator metadata.

    The caller supplies a streaming iterable. Each raw line is parsed, classified,
    and discarded before the next line is requested. Item category is resolved
    before lifecycle sequencing so a pre-turn action or error cannot be treated as
    benign progress.
    """
    journal: list[dict[str, Any]] = []
    event_counts: Counter[str] = Counter()
    item_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    seen_item_phases: set[tuple[str, str, str]] = set()
    tool_ids: set[tuple[str, str]] = set()
    thread_started = False
    turn_started = False
    terminal = False
    outcome: str | None = None
    terminal_reason: str | None = None
    tool_event_count = 0
    failure_seen = False
    forbidden_seen = False
    turn_completed = False

    def record(
        event_type: str,
        category: str,
        role: str,
        *,
        item_type: str | None = None,
        status: str | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "ordinal": len(journal) + 1,
            "eventType": event_type,
            "category": category,
            "role": role,
        }
        if item_type is not None:
            entry["itemType"] = item_type
        if status is not None:
            entry["status"] = status
        journal.append(entry)
        event_counts[event_type] += 1
        category_counts[category] += 1
        if item_type is not None:
            item_counts[item_type] += 1

    def stop(next_outcome: str, reason: str) -> None:
        nonlocal terminal, outcome, terminal_reason
        terminal = True
        outcome = next_outcome
        terminal_reason = reason

    def forbid(
        event_type: str,
        role: str,
        *,
        item_type: str | None = None,
        category: str = "forbidden-unknown",
        status: str | None = None,
    ) -> None:
        nonlocal forbidden_seen
        record(
            event_type,
            category,
            role,
            item_type=item_type,
            status=status,
        )
        forbidden_seen = True
        stop("unknown", role)

    for raw_line in lines:
        try:
            if isinstance(raw_line, bytes):
                text = raw_line.decode("utf-8", errors="strict")
            elif type(raw_line) is str:
                text = raw_line
            else:
                raise TypeError
            event = json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
        except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJsonKeyError, TypeError):
            forbid("malformed", "malformed-json-event")
            break
        finally:
            raw_line = None

        if terminal:
            forbid("unknown", "event-after-terminal")
            break
        if type(event) is not dict:
            forbid("malformed", "wrong-top-level-shape")
            break
        event_type = event.get("type")
        if type(event_type) is not str or not event_type:
            forbid("malformed", "missing-top-level-discriminator")
            break
        if event_type not in CODEX_EXEC_JSONL_TOP_LEVEL_TYPES:
            forbid("unknown", "unknown-top-level-discriminator")
            break
        category, role = CODEX_EXEC_JSONL_TOP_LEVEL_TYPES[event_type]

        if event_type == "error":
            if type(event.get("message")) is not str:
                forbid(event_type, "malformed-error-event")
            else:
                record(event_type, category, role)
                failure_seen = True
                stop("fail", "stream-error")
            break
        if event_type == "turn.failed":
            error = event.get("error")
            if type(error) is not dict or type(error.get("message")) is not str:
                forbid(event_type, "malformed-error-event")
            else:
                record(event_type, category, role)
                failure_seen = True
                stop("fail", "turn-failed")
            break
        if event_type == "thread.started":
            if thread_started or turn_started or type(event.get("thread_id")) is not str or not event["thread_id"]:
                forbid(event_type, "thread-start-order")
                break
            thread_started = True
            record(event_type, category, role)
            continue
        if event_type == "turn.started":
            if not thread_started or turn_started:
                forbid(event_type, "turn-start-order")
                break
            turn_started = True
            record(event_type, category, role)
            continue
        if event_type == "turn.completed":
            usage = event.get("usage")
            usage_fields = (
                "input_tokens",
                "cached_input_tokens",
                "cache_write_input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
            )
            if (
                not thread_started
                or not turn_started
                or type(usage) is not dict
                or any(
                    type(usage.get(field)) is not int or usage[field] < 0
                    for field in usage_fields
                )
            ):
                forbid(event_type, "malformed-turn-completion")
                break
            record(event_type, category, role)
            turn_completed = True
            stop("pass", "turn-completed")
            continue

        item = event.get("item")
        if type(item) is not dict:
            forbid(event_type, "malformed-item-envelope")
            break
        item_type = item.get("type")
        if type(item_type) is not str or not item_type:
            forbid(event_type, "malformed-item-discriminator")
            break
        if item_type not in CODEX_EXEC_JSONL_ITEM_TYPES:
            forbid(event_type, "unknown-item-discriminator")
            break
        item_category, allowed_events, statuses = CODEX_EXEC_JSONL_ITEM_TYPES[item_type]
        item_id = item.get("id")
        id_valid = type(item_id) is str and bool(item_id)
        status = item.get("status") if statuses is not None else None
        status_valid = statuses is None or status in statuses

        # Category wins over lifecycle. Action/error items cannot hide in a
        # source-valid pre-turn position.
        if item_category == "tool-action-capable":
            tool_event_count += 1
            tool_ids.add((item_type, item_id if id_valid else f"ordinal-{len(journal) + 1}"))
            if not id_valid or not status_valid:
                forbid(
                    event_type,
                    "missing-item-id" if not id_valid else "unknown-item-status",
                    item_type=item_type,
                    category=item_category,
                    status=status if status_valid else None,
                )
            else:
                record(
                    event_type,
                    item_category,
                    role,
                    item_type=item_type,
                    status=status,
                )
                stop("fail", "tool-action-capable")
            break
        if item_category == "failure-error":
            if not id_valid:
                forbid(
                    event_type,
                    "missing-item-id",
                    item_type=item_type,
                    category=item_category,
                )
            else:
                record(event_type, item_category, role, item_type=item_type)
                failure_seen = True
                stop("fail", "error-item")
            break

        if not id_valid:
            forbid(event_type, "missing-item-id", item_type=item_type)
            break
        if event_type not in allowed_events:
            forbid(event_type, "invalid-benign-item-phase", item_type=item_type)
            break
        if not thread_started:
            forbid(event_type, "item-before-thread", item_type=item_type)
            break
        phase = (item_type, item_id, event_type)
        if phase in seen_item_phases:
            forbid(event_type, "duplicate-item-phase", item_type=item_type)
            break
        seen_item_phases.add(phase)
        record(event_type, item_category, role, item_type=item_type)

    if not terminal:
        forbidden_seen = True
        outcome = "unknown"
        terminal_reason = "abrupt-input"

    result = {
        "taxonomyVersion": CODEX_EXEC_JSONL_TAXONOMY_VERSION,
        "outcome": outcome,
        "terminalReason": terminal_reason,
        "turnCompleted": turn_completed,
        "eventTypeCounts": dict(sorted(event_counts.items())),
        "itemTypeCounts": dict(sorted(item_counts.items())),
        "categoryCounts": dict(sorted(category_counts.items())),
        "toolActionEventCount": tool_event_count,
        "uniqueToolActionCount": len(tool_ids),
        "failureSeen": failure_seen,
        "forbiddenUnknownSeen": forbidden_seen,
        "journal": journal,
    }
    tool_ids.clear()
    seen_item_phases.clear()
    event = None
    text = None
    return result


def _expected_claude_code_stream_json_taxonomy() -> dict[str, Any]:
    return {
        "schemaVersion": "1",
        "taxonomyVersion": CLAUDE_CODE_STREAM_JSON_TAXONOMY_VERSION,
        "host": {"name": "claude-code", "version": "2.1.308"},
        "source": {
            "documentation": [
                {
                    "url": "https://code.claude.com/docs/en/headless",
                    "authority": "stream-json events, session metadata, structured output, and permission denials",
                },
                {
                    "url": "https://code.claude.com/docs/en/cli-reference",
                    "authority": "print-mode flags, input and output formats, and hook event inclusion",
                },
                {
                    "url": "https://code.claude.com/docs/en/hooks",
                    "authority": "SessionStart sources and command hook execution",
                },
            ],
            "verifiedOn": "2026-10-23",
        },
        "invocation": {
            "required": [
                "-p",
                "--output-format stream-json",
                "--verbose",
                "--json-schema",
                "--append-system-prompt",
                "--permission-mode dontAsk",
                "--no-session-persistence",
                "--model",
                "--effort",
            ],
            "multiTurn": "--input-format stream-json",
            "environment": {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        },
        "categories": list(CLAUDE_CODE_STREAM_JSON_CATEGORIES),
        "eventTypes": {
            event_key: {"category": category, "role": role}
            for event_key, (category, role) in CLAUDE_CODE_STREAM_JSON_EVENT_TYPES.items()
        },
        "toolUse": {
            "structuredOutputTool": CLAUDE_CODE_STRUCTURED_OUTPUT_TOOL,
            "otherToolUse": "tool-action-capable",
            "permissionDenial": "tool-action-capable",
        },
        "lifecycle": {
            "startupHookBeforeSessionStart": True,
            "sessionStartBeforeModelOutput": True,
            "resultIsTerminal": True,
            "unknownOrMalformedEvent": "fail-closed",
            "eventAfterResult": "fail-closed",
            "missingResult": "fail-closed",
        },
        "facts": {
            "startupHookVerified": "exactly one SessionStart hook_response with outcome success, exit code 0, and output equal to the reviewed preamble and routing gate",
            "installedPluginVerified": "system/init lists plugin axiom with the expected version, a field Claude Code 2.1.308 emits beside the documented name and path, every bundled axiom skill, and no plugin_errors",
            "turnCompleted": "one terminal result with subtype success, is_error false, terminal_reason completed, and no api_error_status",
            "failureEvent": "a result with is_error true or another subtype, or a failed SessionStart hook",
            "unexpectedTools": "tool_use blocks other than the structured-output tool, plus permission denials",
            "structuredOutput": "result.structured_output validated against the bound host-response schema",
        },
        "retention": {
            "allowedJournalFields": ["ordinal", "eventType", "category", "role", "toolName"],
            "forbidden": [
                "response text",
                "reasoning text",
                "tool arguments",
                "tool output",
                "identifiers",
                "credentials",
                "paths",
                "session or config content",
                "raw payload",
            ],
        },
    }


def check_claude_code_stream_json_taxonomy(root: Path, failures: list[str]) -> None:
    """Validate the reviewed Claude Code stream contract."""
    path = root / "evals" / CLAUDE_CODE_STREAM_JSON_TAXONOMY_PATH.name
    taxonomy = load_json_object(path, failures, root)
    if taxonomy is not None and taxonomy != _expected_claude_code_stream_json_taxonomy():
        failures.append(
            f"evals/{CLAUDE_CODE_STREAM_JSON_TAXONOMY_PATH.name} drifted from the reviewed Claude Code 2.1.308 contract"
        )


def classify_claude_code_stream_json_lines(
    lines: Iterable[bytes | str],
    *,
    expected_startup_output: str | None = None,
    expected_plugin_version: str | None = None,
    expected_skills: Iterable[str] = (),
) -> dict[str, Any]:
    """Fail closed on a Claude Code stream-json run, keeping public discriminators only.

    Startup output and session metadata are compared in memory and discarded;
    the result retains only booleans, counts, and the closed journal fields.
    """
    journal: list[dict[str, Any]] = []
    event_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    required_skills = frozenset(expected_skills)
    hook_responses = 0
    hook_succeeded = False
    hook_output_matches = False
    session_started = False
    plugin_verified = False
    terminal = False
    outcome: str | None = None
    terminal_reason: str | None = None
    turn_completed = False
    failure_seen = False
    forbidden_seen = False
    other_tool_uses = 0
    structured_output_calls = 0
    denial_events = 0
    result_denials = 0

    def record(event_key: str, category: str, role: str, *, tool_name: str | None = None) -> None:
        entry: dict[str, Any] = {
            "ordinal": len(journal) + 1,
            "eventType": event_key,
            "category": category,
            "role": role,
        }
        if tool_name is not None:
            entry["toolName"] = tool_name
        journal.append(entry)
        event_counts[event_key] += 1
        category_counts[category] += 1

    def stop(next_outcome: str, reason: str) -> None:
        nonlocal terminal, outcome, terminal_reason
        terminal = True
        outcome = next_outcome
        terminal_reason = reason

    def forbid(event_key: str, role: str) -> None:
        nonlocal forbidden_seen
        record(event_key, "forbidden-unknown", role)
        forbidden_seen = True
        stop("unknown", role)

    for raw_line in lines:
        try:
            if isinstance(raw_line, bytes):
                text = raw_line.decode("utf-8", errors="strict")
            elif type(raw_line) is str:
                text = raw_line
            else:
                raise TypeError
            event = json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
        except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJsonKeyError, TypeError):
            forbid("malformed", "malformed-json-event")
            break
        finally:
            raw_line = None

        if terminal:
            forbid("unknown", "event-after-terminal")
            break
        if type(event) is not dict:
            forbid("malformed", "wrong-top-level-shape")
            break
        event_type = event.get("type")
        if type(event_type) is not str or not event_type:
            forbid("malformed", "missing-top-level-discriminator")
            break
        if event_type == "system":
            subtype = event.get("subtype")
            if type(subtype) is not str or not subtype:
                forbid("malformed", "missing-system-subtype")
                break
            event_key = f"system/{subtype}"
        else:
            event_key = event_type
        if event_key not in CLAUDE_CODE_STREAM_JSON_EVENT_TYPES:
            forbid("unknown", "unknown-top-level-discriminator")
            break
        category, role = CLAUDE_CODE_STREAM_JSON_EVENT_TYPES[event_key]

        if event_key in {"system/hook_started", "system/hook_progress", "system/hook_response"}:
            if event.get("hook_event") != "SessionStart" or session_started:
                forbid(event_key, "hook-outside-startup")
                break
            if event_key == "system/hook_response":
                hook_responses += 1
                hook_succeeded = event.get("outcome") == "success" and event.get("exit_code") == 0
                hook_output_matches = (
                    expected_startup_output is not None
                    and event.get("output") == expected_startup_output
                )
                if not hook_succeeded:
                    failure_seen = True
            record(event_key, category, role)
            continue
        if event_key == "system/init":
            if session_started:
                forbid(event_key, "duplicate-session-start")
                break
            session_started = True
            plugins = event.get("plugins")
            skills = event.get("skills")
            plugin_verified = (
                expected_plugin_version is not None
                and "plugin_errors" not in event
                and type(plugins) is list
                and any(
                    type(plugin) is dict
                    and plugin.get("name") == "axiom"
                    and plugin.get("version") == expected_plugin_version
                    for plugin in plugins
                )
                and type(skills) is list
                and required_skills <= {skill for skill in skills if type(skill) is str}
            )
            record(event_key, category, role)
            continue
        if not session_started:
            forbid(event_key, "event-before-session-start")
            break
        if event_key == "assistant":
            message = event.get("message")
            content = message.get("content") if type(message) is dict else None
            if type(content) is not list:
                forbid(event_key, "malformed-model-message")
                break
            record(event_key, category, role)
            for block in content:
                if type(block) is not dict or block.get("type") != "tool_use":
                    continue
                tool_name = block.get("name") if type(block.get("name")) is str else None
                if tool_name == CLAUDE_CODE_STRUCTURED_OUTPUT_TOOL and event.get("parent_tool_use_id") is None:
                    structured_output_calls += 1
                    record(event_key, category, "structured-output", tool_name=tool_name)
                else:
                    other_tool_uses += 1
                    record(event_key, "tool-action-capable", "tool-action", tool_name=tool_name)
            continue
        if event_key == "system/permission_denied":
            denial_events += 1
            record(event_key, category, role)
            continue
        if event_key == "result":
            denials = event.get("permission_denials")
            result_denials = len(denials) if type(denials) is list else 0
            if (
                event.get("subtype") == "success"
                and event.get("is_error") is False
                and event.get("terminal_reason") == "completed"
                and event.get("api_error_status") is None
            ):
                turn_completed = True
                record(event_key, category, role)
                stop("pass", "terminal-success")
            else:
                failure_seen = True
                record(event_key, "failure-error", "terminal-failure")
                stop("fail", "terminal-failure")
            continue
        record(event_key, category, role)

    if not terminal:
        forbidden_seen = True
        outcome = "unknown"
        terminal_reason = "abrupt-input"

    result = {
        "taxonomyVersion": CLAUDE_CODE_STREAM_JSON_TAXONOMY_VERSION,
        "outcome": outcome,
        "terminalReason": terminal_reason,
        "turnCompleted": turn_completed,
        "startupHookVerified": hook_responses == 1 and hook_succeeded and hook_output_matches,
        "installedPluginVerified": plugin_verified,
        "structuredOutputCalls": structured_output_calls,
        "unexpectedTools": other_tool_uses + max(denial_events, result_denials),
        "eventTypeCounts": dict(sorted(event_counts.items())),
        "categoryCounts": dict(sorted(category_counts.items())),
        "failureSeen": failure_seen,
        "forbiddenUnknownSeen": forbidden_seen,
        "journal": journal,
    }
    event = None
    text = None
    return result
