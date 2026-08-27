"""Codex JSONL observer taxonomy and fail-closed classification."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .constants import (
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
