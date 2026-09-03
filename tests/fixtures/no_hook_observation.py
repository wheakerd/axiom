"""Deterministic fake Codex surfaces for no-Hook observer tests."""

from __future__ import annotations

import json
import os
import sys
import time


MAX_FAKE_PROMPT_BYTES = 512 * 1024


def emit(value: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n")
    sys.stdout.flush()


def response() -> dict[str, object]:
    return {
        "profileId": "openai-hook-independent-v1",
        "contractBindings": {
            "profileContractSha256": "b693580201a51fb5ecc5058b2e6ee8e63ddb948580f7fee7ce6042215ec07a88",
            "goldenSetSha256": "05febacecdf36ac05ae95d55e835c4d207c4a24dc2bb68a44cb62aa3e108a40c",
            "responseSchemaSha256": "e1010ee20daeef5dae801f34d689dff6c0b063f969e254331ceedb670dcd2db4",
            "caseId": os.environ.get("AXIOM_FAKE_CASE_ID", "no-hook-no-route-summary-001"),
            "contractVersion": int(os.environ.get("AXIOM_FAKE_CONTRACT_VERSION", "2")),
        },
        "discoveryOutcome": os.environ.get("AXIOM_FAKE_OUTCOME", "no-route"),
        "selectedRoutes": json.loads(os.environ.get("AXIOM_FAKE_ROUTES", "[]")),
        "clarificationCount": int(os.environ.get("AXIOM_FAKE_CLARIFICATIONS", "0")),
        "usingAxiomFrontDoorObserved": os.environ.get("AXIOM_FAKE_FRONT_DOOR", "false") == "true",
        "sessionStartObserved": False,
        "mutationAttempted": False,
        "mutationObserved": False,
    }


def main() -> int:
    arguments = sys.argv[1:]
    if arguments[:3] == ["plugin", "marketplace", "add"] or arguments[:1] == ["marketplace-add"]:
        emit({"marketplaceName": "axiom-no-hook-observer", "installedRoot": os.environ["AXIOM_FAKE_MARKETPLACE_ROOT"], "alreadyAdded": False})
        return 0
    if arguments[:2] == ["plugin", "add"] or arguments[:1] == ["plugin-add"]:
        emit({"pluginId": "axiom@axiom-no-hook-observer", "name": "axiom", "marketplaceName": "axiom-no-hook-observer", "version": "0.10.0", "installedPath": os.environ["AXIOM_FAKE_INSTALLED_PATH"], "authPolicy": "on-install"})
        return 0
    if not arguments or arguments[0] != "exec":
        return 2
    prompt = sys.stdin.buffer.read(MAX_FAKE_PROMPT_BYTES + 1)
    if len(prompt) > MAX_FAKE_PROMPT_BYTES:
        return 4
    if not prompt:
        return 3
    scenario = os.environ.get("AXIOM_FAKE_SCENARIO", "happy")
    if scenario == "timeout":
        time.sleep(30)
        return 0
    if scenario == "oversized-stdout":
        sys.stdout.write("x" * (1024 * 1024 + 1))
        sys.stdout.flush()
        return 0
    if scenario == "oversized-stderr":
        sys.stderr.write("x" * (256 * 1024 + 1))
        sys.stderr.flush()
        return 0
    if scenario == "stderr":
        sys.stderr.write("unexpected diagnostic\n")
        sys.stderr.flush()
    drift_target = os.environ.get("AXIOM_FAKE_DRIFT_TARGET")
    if scenario.endswith("-drift") and drift_target:
        with open(drift_target, "ab") as stream:
            stream.write(b"drift")
    if scenario == "malformed":
        sys.stdout.write("{not-json}\n")
        return 0
    emit({"type": "thread.started", "thread_id": "private-test-id"})
    emit({"type": "turn.started"})
    if scenario == "unknown-event":
        emit({"type": "future.event"})
    elif scenario == "unknown-item":
        emit({"type": "item.completed", "item": {"type": "future_item"}})
    elif scenario == "unknown-status":
        emit({"type": "item.started", "item": {"type": "command_execution", "status": "future"}})
    elif scenario == "tool":
        emit({"type": "item.started", "item": {"type": "command_execution", "status": "in_progress"}})
    elif scenario == "error-item":
        emit({"type": "item.completed", "item": {"type": "error", "message": "private"}})
    else:
        text = json.dumps(response(), separators=(",", ":"), sort_keys=True)
        emit({"type": "item.completed", "item": {"type": "agent_message", "text": text}})
        if scenario == "duplicate-result":
            emit({"type": "item.completed", "item": {"type": "agent_message", "text": text}})
    if scenario != "missing-terminal":
        emit({"type": "turn.completed", "usage": {"private": True}})
    if scenario == "multiple-terminal":
        emit({"type": "turn.completed"})
    if scenario == "after-terminal":
        emit({"type": "item.completed", "item": {"type": "reasoning", "text": "private"}})
    return int(os.environ.get("AXIOM_FAKE_EXIT", "0"))


if __name__ == "__main__":
    raise SystemExit(main())
