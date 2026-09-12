"""Three one-reply clarification observations; reuse the frozen native guard chain.

This is not another routing assessment, a resumed conversation, or an automatic
semantic grader. Public replies are assessed separately against the original
requests. No historical protocol, result, scoring rule or execution window changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
from typing import Any

from . import no_hook_native_observation as native
from . import no_hook_observation as legacy
from .context import REPOSITORY_ROOT

PROTOCOL = Path("evals/no-hook-observation/clarification-protocol-v1.json")
HISTORY = Path("evals/no-hook-observation/clarification-history-v1.json")
ORDINALS = (12, 13, 14)
PRIOR = "0307ab9a45698a3f4176f21bd30113307c9d3867c0bad069abd87e1c1a98c43a"
PRIOR_PATH = Path("evals/no-hook-observation/results/codex-native-" + PRIOR + ".json")
STATE = "clarification-preparation.json"
RESULT = "clarification-result.json"
REPLY_LIMIT = 8192
PRIOR_SUPPLEMENT = "5b6c943d2b68be63d2b6a08cbc29783935efa57cab818ba08d2da4015e4e37ae"
PRIOR_SUPPLEMENT_PATH = Path("evals/no-hook-observation/results/clarification-" + PRIOR_SUPPLEMENT + ".json")
ARCHIVE = Path("evals/no-hook-observation/historical-protocols/clarification-round-1")
RECORDED_PROTOCOL = Path("evals/no-hook-observation/historical-protocols/clarification-round-2/clarification-protocol-v1.json")
RUN_NAME = "cases-clarification-2"
INDEPENDENT = {
    "windowId": "independent-clarification-1",
    "runName": "cases-independent-clarification-1",
    "candidateCommit": "f8c6eadb1c4401f02d6310dda57995544af2a45d",
    "candidateTree": "3c274e88ef7db7a50afe2c4c59594cafd011dda3",
    "priorResultSha256": native.REVISION_FOUR_RESULT_SHA256,
    "priorAttempts": 98, "priorCliLaunches": 98,
    "ordinals": [12, 13, 14], "authenticationSourceOrdinal": 10,
    "requires": "independent explicit authorization; no routing continuation",
    "limits": {"newAttempts": 3, "maximumCumulativeAttempts": 101, "replyBytesPerCase": REPLY_LIMIT},
}
_require = native._require
_bytes = native._bytes
_read = native._read
_json = native._json
_exclusive = native._exclusive


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def protocol(root: Path) -> dict:
    p = _json(_read(root / PROTOCOL))
    check = dict(p)
    _require(check.pop("protocolDigest") == "sha256:" + digest(_bytes(check)), "supplement protocol digest changed")
    _require(p["ordinals"] == list(ORDINALS) and p["limits"] == {
        "newAttempts": 3, "maximumCumulativeAttempts": 76, "replyBytesPerCase": REPLY_LIMIT},
        "supplement budget or retained reply limit changed")
    _require(p["revision"] == 2 and p["priorSupplementSha256"] == PRIOR_SUPPLEMENT,
             "supplement segment identity changed")
    _require(p.get("fixedAcceptance") == {
        "windowId": native.FIXED_ACCEPTANCE["windowId"], "requires": "completed-fixed-routing",
        "limits": {"newAttempts": 3, "maximumCumulativeAttempts": 95, "replyBytesPerCase": REPLY_LIMIT}},
        "fixed clarification window changed")
    for binding in p["bindings"]:
        _require(digest(_read(root / binding["path"])) == binding["sha256"], "supplement source binding changed")
    _require(p["priorResultSha256"] == PRIOR and digest(_read(root / PRIOR_PATH)) == PRIOR,
             "prior routing result changed")
    _require(p.get("revisionFourAcceptance") == {
        "windowId": native.REVISION_FOUR_ACCEPTANCE["windowId"], "requires": "completed-fixed-routing",
        "limits": {"newAttempts": 3, "maximumCumulativeAttempts": 106, "replyBytesPerCase": REPLY_LIMIT}},
        "revision 4 clarification window changed")
    _require(p["nativeProtocolDigest"] == native._protocol(root)["protocolDigest"], "native guard protocol changed")
    _require(p.get("independentClarification") == INDEPENDENT, "independent clarification registration changed")
    old = _json(_read(root / ARCHIVE / PROTOCOL.name))
    _require(all(p[k] == old[k] for k in ("instructions", "replyEvidence", "assessment", "loadingEvidence")),
             "supplement observation contract changed")
    return p


def _prior_supplement(root: Path) -> dict:
    data = _read(root / PRIOR_SUPPLEMENT_PATH)
    _require(digest(data) == PRIOR_SUPPLEMENT, "prior supplementary result changed")
    return _json(data)


def _unrecorded(root: Path, p: dict, *, fixed_acceptance: bool = False, revision_four: bool = False,
                independent: bool = False) -> None:
    history = _json(_read(root / HISTORY))
    if independent:
        _require(history.get("independentClarification") == {
            "windowId": INDEPENDENT["windowId"], "protocolDigest": p["protocolDigest"], "results": []},
            "independent clarification already recorded or registration changed")
        return
    if fixed_acceptance:
        _require(history.get(native._fixed_history_key(revision_four)) == {
            "windowId": native._fixed_contract(revision_four)["windowId"], "protocolDigest": p["protocolDigest"], "results": []},
            "fixed clarification already recorded or registration changed")
        return
    old = _json(_read(root / ARCHIVE / HISTORY.name))
    _require(history.get("protocolDigest") == p["protocolDigest"] and
             history.get("results") == old["results"], "supplement already recorded or history changed")


def attempt_history(root: Path) -> dict:
    chain = native._attempt_history(root)
    identities = {tuple(key): (1, 1) for key in chain["identities"]}
    _require(chain["attempts"] == chain["cliLaunches"] == len(identities), "legacy attempt chain mismatch")
    prior = _json(_read(root / PRIOR_PATH))
    for record in prior["caseResults"]:
        key = (record["ordinal"], record["materializationCommitmentSha256"])
        value = (record["attemptCount"], record["cliLaunchCount"])
        _require(value == (1, 1) and key not in identities, "latest batch overlaps or is incomplete")
        identities[key] = value
    _require(len(identities) == prior["cumulativeAttemptCount"] == 70, "historical total is not 70")
    supplement = _prior_supplement(root)
    _require(supplement["priorAttemptCount"] == 70 and supplement["attemptCount"] ==
             supplement["cliLaunchCount"] == 3 and supplement["cumulativeAttemptCount"] ==
             supplement["cumulativeCliLaunchCount"] == 73, "prior supplement accounting mismatch")
    for record in supplement["caseResults"]:
        key = (record["ordinal"], PRIOR_SUPPLEMENT)
        _require(record["ordinal"] in ORDINALS and key not in identities and
                 record["attemptCount"] == record["cliLaunchCount"] == 1, "prior reply attempt overlap")
        identities[key] = (1, 1)
    _require(len(identities) == 73, "historical total is not 73")
    return {"attempts": len(identities), "cliLaunches": sum(v[1] for v in identities.values()),
            "priorResultSha256": PRIOR, "priorSupplementSha256": PRIOR_SUPPLEMENT,
            "identityDigest": digest(_bytes(sorted(identities)))}


def reply_prompt(request: str, definition: dict, instructions: str) -> bytes:
    paths = sorted((x["path"] for x in definition["files"]), key=lambda x: x.encode("utf-8"))
    # This function has no expected outcome, case ID, route catalog or scoring input.
    return (instructions + "\n\nTask materials:\n"
            "Paths are relative to the current working directory and identify supplied task data only, "
            "not installed Skills or the host discovery catalog. An empty list says nothing about Skill installation.\n"
            "taskMaterialPaths: " + json.dumps(paths, ensure_ascii=True) +
            "\n\nUser request:\n" + request + "\n").encode("utf-8")


def independent_attempt_history(root: Path) -> dict:
    """Inherit both stopped batches; none of their unstarted slots transfer."""
    old = native.revision_four_attempt_history(root)
    binding = native._fixed_result_binding(root, revision_four=True)
    _require(binding is not None and binding["sha256"] == INDEPENDENT["priorResultSha256"],
             "independent clarification predecessor changed")
    result = _json(_read(root / binding["path"]))
    identities = {tuple(k) for k in old["identities"]}
    for item in result["caseResults"]:
        if not item["attemptCount"]:
            _require(item["cliLaunchCount"] == 0, "unattempted predecessor launched")
            continue
        key = (item["ordinal"], item["materializationCommitmentSha256"])
        _require(key not in identities and item["attemptCount"] == item["cliLaunchCount"] == 1,
                 "independent predecessor overlaps or changed counts")
        identities.add(key)
    _require(len(identities) == result["cumulativeAttemptCount"] == INDEPENDENT["priorAttempts"] and
             old["cliLaunches"] + result["cliLaunchCount"] == INDEPENDENT["priorCliLaunches"],
             "independent historical total is not 98")
    return {"attempts": len(identities), "cliLaunches": INDEPENDENT["priorCliLaunches"],
            "routingResultSha256": binding["sha256"], "identityDigest": digest(_bytes(sorted(identities)))}


def _independent_source(root: Path, p: dict) -> dict:
    source = native._execution_source(root)
    env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
    for binding in p["bindings"]:
        data = subprocess.check_output(["git", "-C", str(root), "show",
            source["commit"] + ":" + binding["path"]], env=env)
        _require(digest(data) == binding["sha256"], "independent implementation is not committed")
    return source


def reply_argv(executable: Path, run_root: Path, ordinal: int, final_output: Path) -> list[str]:
    _require(ordinal in ORDINALS, "case outside clarification scope")
    args = native.build_native_argv(executable, run_root, ordinal, final_output=final_output)
    index = args.index("--output-schema")
    # Only the transport's JSON response restriction is absent. Permissions,
    # model, reasoning, fresh context, cwd, tools and JSONL are identical.
    del args[index:index + 2]
    return args


def reply_stream(data: bytes, taxonomy: dict, readable: dict, cwd: Path) -> dict:
    """Reuse the production strict lifecycle before its JSON-only response step.

    Only the two JSON-specific post-closure assertions are expected in this
    supplement. All framing, event, item, command and terminal checks still run
    in the unchanged native parser. No event is deleted, translated or forged.
    """
    try:
        stream, count = native.parse_native_jsonl(data, taxonomy, readable, cwd)
        terminal = stream.terminal_type
    except native.NativeStreamError as error:
        if (error.phase != "response" or error.closed_terminal != "turn.completed" or
                error.code not in {"final-message-invalid-json", "final-message-not-object"}):
            raise
        terminal, count = error.closed_terminal, error.completed_commands
    _require(terminal == "turn.completed", "reply turn did not complete")
    messages = [event["item"]["text"] for raw in data.splitlines()
                if (event := legacy._parse_json_line(raw)).get("type") == "item.completed" and
                event.get("item", {}).get("type") == "agent_message"]
    _require(messages and sum(len(x.encode("utf-8")) for x in messages) <= REPLY_LIMIT,
             "visible replies missing or exceed retention limit")
    return {"messages": messages, "terminal": terminal, "readonlyCommandCount": count}


def public_replies(messages: list[str]) -> dict:
    """Conservative output minimization, not proof arbitrary text cannot leak.

    Authentication exclusion is provided by the existing tool boundary. Known
    private-path forms and suspicious secret-bearing chunks are omitted without
    reading credentials. Every user-visible message remains represented; any
    omission is flagged for the separate semantic reviewer.
    """
    out, redacted = [], False
    patterns = [r"(?:/home/|/Users/|/tmp/|[A-Z]:\\Users\\)[^\s<>\"']+",
                r"(?i)(?:bearer\s+|(?:token|api[_-]?key|password|cookie)\s*[:=]\s*)[^\s,;]+",
                r"[A-Za-z0-9_+/=-]{48,}", r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
                r"https?://[^\s]*[?][^\s]+"]
    for message in messages:
        value = message
        for pattern in patterns:
            value = re.sub(pattern, "[redacted]", value)
        value = "".join(c if c in "\n\t" or ord(c) >= 32 else "[control]" for c in value)
        redacted |= value != message
        out.append(value)
    return {"messages": out, "redactionsApplied": redacted,
            "originalVisibleMessageCount": len(messages), "retentionComplete": not redacted}


def _final_output(path: Path, identity: tuple[int, int], candidate: str) -> None:
    metadata = path.lstat()
    _require(stat.S_ISREG(metadata.st_mode) and (metadata.st_dev, metadata.st_ino) == identity,
             "final reply output ownership changed")
    data = _read(path, maximum=REPLY_LIMIT)
    # Frozen write_last_message_to_file uses std::fs::write (no added newline).
    _require(data == candidate.encode("utf-8"), "official final reply differs from JSONL candidate")


def _verify_inputs(root: Path, run_root: Path, ordinal: int, record: dict) -> dict:
    paths = native._case_paths(run_root, ordinal)
    native._ordinary_directory(paths["workspace"])
    native._ordinary_directory(paths["home"])
    native._verify_config(paths, run_root / "marketplace", True)
    native._verify_discovery(paths, True)
    np = native._protocol(root)
    definition = native._definition(native._input(root, np, "fixtureMatrix"), ordinal)
    fixture = native.fixture_identity(paths["workspace"], definition)
    package = native.package_identity(paths["package"])
    _require(fixture == record["fixtureSha256"] and package == record["packageSha256"] == np["bundle"]["packageSha256"],
             "prepared public inputs changed")
    return {"fixtureSha256": fixture, "packageSha256": package, "modelMetadata": native._model_metadata(paths)}


def _prior_state(root: Path, previous: Path, *, fixed_acceptance: bool = False) -> dict:
    sha = native.FIXED_REPLY_PRIORS[-1] if fixed_acceptance else PRIOR_SUPPLEMENT
    relative = Path("evals/no-hook-observation/results/clarification-" + sha + ".json")
    data = _read(root / relative)
    _require(digest(data) == sha, "registered predecessor bytes changed")
    prior = _json(data)
    _require(previous.name == ("cases-clarification-2" if fixed_acceptance else "cases-clarification-1") and
             _read(previous / RESULT) == data,
             "registered predecessor result mismatch")
    state = _json(_read(previous / STATE))
    _require(state["protocolDigest"] == prior["protocolDigest"] and state["runMode"] == "actual" and
             [r["ordinal"] for r in state["cases"]] == list(ORDINALS),
             "predecessor preparation mismatch")
    _require(_json(_read(previous / "batch-started.json")) == {
        "protocolDigest": prior["protocolDigest"], "priorAttempts": 73 if fixed_acceptance else 70},
             "predecessor batch marker mismatch")
    for record in prior["caseResults"]:
        ordinal = record["ordinal"]
        _require(_json(_read(previous / f"attempt-{ordinal:02d}.json")) == {
            "ordinal": ordinal, "caseId": record["caseId"], "protocolDigest": prior["protocolDigest"]},
            "predecessor attempt marker mismatch")
        facts = record["executionDiagnostics"]
        _require(record["status"] == "CAPTURED" and facts["returnCode"] == 0 and
                 not any(facts[x] for x in ("cleanupFailed", "timedOut", "observerTerminated")) and
                 facts["inputFullyDelivered"] and facts["finalOutputVerified"] and
                 record["postcheck"] == "valid", "predecessor did not close normally")
        _require(not (previous / f"final-reply-{ordinal:02d}.txt").exists(), "predecessor output remains")
        prepared = next(r for r in state["cases"] if r["ordinal"] == ordinal)
        _require(all(prepared[k] == record[k] for k in
                     ("caseId", "promptSha256", "requestSha256", "fixtureSha256", "packageSha256")),
                 "predecessor input binding changed")
    source = prior["caseResults"][-1]
    paths = native._case_paths(previous, 14)
    native._verify_config(paths, previous / "marketplace", True)
    native._verify_discovery(paths, True)
    # Recheck only the old public installed package against its old recorded
    # bytes. Applying the new runtime identity here would rebind history.
    records = legacy.snapshot_tree(paths["package"])
    _require(digest(legacy._canonical_json(records)) == source["packageSha256"], "predecessor package changed")
    fixtures = native._input(root, native._protocol(root), "fixtureMatrix")
    _require(native.fixture_identity(paths["workspace"], native._definition(fixtures, 14)) ==
             source["fixtureSha256"], "predecessor fixture changed")
    native._model_metadata(paths)
    return state


def _login(executable: Path, paths: dict, invoke) -> None:
    # Only the official client reads credentials. Output is checked, not echoed.
    capture = invoke([str(executable), "-c", 'cli_auth_credentials_store="file"', "login", "status"],
                     cwd=paths["workspace"], env=native.case_environment(paths))
    _require(capture["returncode"] == 0 and (capture["stdout"] + capture["stderr"]).strip() == b"Logged in using ChatGPT",
             "official test login status unavailable")


def prepare(root: Path, run_root: Path, previous: Path, *, bundle_root: Path,
            authorized: bool = False, fixed_acceptance: bool = False, revision_four: bool = False,
            independent: bool = False, runner=None) -> dict:
    _require(sum((fixed_acceptance, revision_four, independent)) <= 1, "select one observation window")
    fixed_acceptance = fixed_acceptance or revision_four
    _require(authorized, "explicit preparation and opaque auth-copy authorization required")
    p = protocol(root)
    _unrecorded(root, p, fixed_acceptance=fixed_acceptance, revision_four=revision_four, independent=independent)
    if independent:
        chain = independent_attempt_history(root)
        old = native._revision_four_auth_source(root, previous, revision_four=True)
        source_ordinal = INDEPENDENT["authenticationSourceOrdinal"]
    elif fixed_acceptance:
        old, chain = native.completed_fixed_routing(root, previous, simulated=runner is not None, revision_four=revision_four)
        source_ordinal = 16
    else:
        chain = attempt_history(root)
        old = _prior_state(root, previous)
        source_ordinal = 14
    expected_name = INDEPENDENT["runName"] if independent else native._fixed_contract(revision_four)["clarificationRunName"] if fixed_acceptance else RUN_NAME
    _require(run_root.parent == previous.parent and run_root.name == expected_name and run_root != previous and
             not run_root.exists() and not run_root.is_symlink(), "fresh registered sibling required")
    if fixed_acceptance and runner is None:
        _require(native._execution_source(root) == native._fixed_registration(root, run_root.parent, revision_four=revision_four)["executionSource"],
                 "clarification execution commit differs from the fixed registration")
    source = _independent_source(root, p) if independent and runner is None else None
    executable = Path(old["executable"])
    legacy.freeze_executable(executable, legacy.CODEX_BINARY_SHA256)
    invoke = native.bounded_process if runner is None else runner
    _login(executable, native._case_paths(previous, source_ordinal), invoke)
    bundle = bundle_root
    np = native._protocol(root)
    _require(native.package_identity(bundle) == np["bundle"]["packageSha256"], "new frozen bundle mismatch")
    native._ordinary_directory(run_root.parent)
    run_root.mkdir(mode=0o700)
    _exclusive(run_root / "preparation-started.json", _bytes({"protocolDigest": p["protocolDigest"]}))
    marketplace = run_root / "marketplace"
    (marketplace / ".agents/plugins").mkdir(parents=True)
    shutil.copytree(bundle, marketplace / "plugin")
    _require(native.package_identity(marketplace / "plugin") == np["bundle"]["packageSha256"], "local bundle copy changed")
    _exclusive(marketplace / ".agents/plugins/marketplace.json", _bytes({
        "name": legacy.MARKETPLACE_NAME, "interface": {"displayName": "Axiom no-Hook observer"},
        "plugins": [{"name": legacy.PLUGIN_NAME, "source": {"source": "local", "path": "./plugin"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Productivity"}]}))
    cases, records = legacy.load_golden_cases(root), []
    fixtures = native._input(root, np, "fixtureMatrix")
    for ordinal in ORDINALS:
        paths = native._case_paths(run_root, ordinal)
        for name in ("case", "home", "user", "workspace", "state", "tmp"):
            paths[name].mkdir(mode=0o700)
        for name in ("config", "cache", "data"):
            (paths["user"] / name).mkdir(mode=0o700)
        definition = native._definition(fixtures, ordinal)
        fixture = native.materialize_fixture(paths["workspace"], definition)
        receipt = _json(native._successful(invoke(legacy.build_marketplace_add_argv(executable, marketplace),
            cwd=paths["workspace"], env=native.case_environment(paths)), "marketplace registration"))
        _require(receipt == {"marketplaceName": legacy.MARKETPLACE_NAME, "installedRoot": str(marketplace), "alreadyAdded": False},
                 "marketplace receipt mismatch")
        receipt = _json(native._successful(invoke(legacy.build_plugin_add_argv(executable),
            cwd=paths["workspace"], env=native.case_environment(paths)), "plugin installation"))
        _require(set(receipt) == {"pluginId", "name", "marketplaceName", "version", "installedPath", "authPolicy"} and
                 all(receipt[k] == v for k, v in {"pluginId": legacy.PLUGIN_ID, "name": legacy.PLUGIN_NAME,
                     "marketplaceName": legacy.MARKETPLACE_NAME, "version": native.PLUGIN_VERSION,
                     "installedPath": str(paths["package"])}.items()) and receipt["authPolicy"] in {"ON_INSTALL", "ON_USE"},
                 "installed receipt mismatch")
        paths["discovery"].parent.mkdir(mode=0o700)
        paths["discovery"].symlink_to(paths["package"] / "skills", target_is_directory=True)
        prompt = reply_prompt(cases[ordinal - 1]["request"], definition, p["instructions"])
        _exclusive(paths["case"] / "reply-prompt.txt", prompt)
        record = {"ordinal": ordinal, "caseId": cases[ordinal - 1]["id"], "promptSha256": digest(prompt),
                  "requestSha256": digest(cases[ordinal - 1]["request"].encode()), "fixtureSha256": fixture,
                  "packageSha256": np["bundle"]["packageSha256"]}
        _verify_inputs(root, run_root, ordinal, record)
        records.append(record)
    state = {"protocolDigest": p["protocolDigest"], "runMode": "actual" if runner is None else "simulated",
             "previousRunRoot": str(previous), "executable": str(executable), "attemptHistory": chain, "cases": records}
    if independent:
        state.update(independentClarification=INDEPENDENT, executionSource=source)
    _exclusive(run_root / STATE, _bytes(state))
    native._copy_test_auth(run_root, source_ordinal, 12, create=True, source_root=previous)
    return state


def _capture_case(root: Path, run_root: Path, ordinal: int, prepared: dict, executable: Path, operator, invoke) -> dict:
    record = {**prepared, "status": "NOT-RUN", "attemptCount": 0, "cliLaunchCount": 0,
              "modelRequestCount": None, "executionDiagnostics": native._diagnostics(),
              "terminal": "not-observed", "publicReads": [], "readonlyCommandCount": None,
              "nativeLoading": "not-observed", "semanticConsumption": "not-observed",
              "replies": None, "postcheck": "not-checked"}
    paths = native._case_paths(run_root, ordinal)
    final = run_root / f"final-reply-{ordinal:02d}.txt"
    identity = None
    events = native._diagnostics()
    phase = "precheck"
    try:
        frozen = legacy.freeze_executable(executable, legacy.CODEX_BINARY_SHA256)
        before = _verify_inputs(root, run_root, ordinal, prepared)
        record["inputsBefore"] = before
        if ordinal != 12:
            native._copy_test_auth(run_root, ordinal - 1, ordinal, create=True)
        descriptor = native._open_test_auth(run_root, ordinal, os.O_RDONLY)
        os.close(descriptor)
        _login(executable, paths, invoke)
        prompt = _read(paths["case"] / "reply-prompt.txt")
        _require(digest(prompt) == prepared["promptSha256"], "prepared reply prompt changed")
        definition = native._definition(native._input(root, native._protocol(root), "fixtureMatrix"), ordinal)
        readable = native._readable(paths, definition, True)
        identity = native._reserve_final_output(final)
        _exclusive(run_root / f"attempt-{ordinal:02d}.json", _bytes({
            "ordinal": ordinal, "caseId": prepared["caseId"], "protocolDigest": protocol(root)["protocolDigest"]}))
        record["attemptCount"] = 1
        legacy.recheck_executable(frozen)
        phase = "launch"
        def receive(raw):
            operator.event(raw)
            try:
                native._observe_line(raw, readable, paths["workspace"], events)
            except native.NativeDiagnosticError:
                if events["streamAssertion"] in native.READ_REJECTIONS:
                    operator.rejected_command(raw)
                raise
        try:
            capture = invoke(reply_argv(executable, run_root, ordinal, final), cwd=paths["workspace"],
                env=native.case_environment(paths), stdin=prompt, line_callback=receive,
                started_callback=lambda: record.__setitem__("cliLaunchCount", 1))
        except native.NativeDiagnosticError as error:
            if error.capture is None:
                raise
            capture = error.capture
        operator.stderr(capture["stderr"])
        facts = native._capture_facts(capture)
        for field in ("eventCount", "eventTypes", "itemTypes", "policyReason", "diagnosticItemCount",
                      "preTurnDiagnosticCount", "hostDiagnosticClasses"):
            facts[field] = events[field]
        if events["streamAssertion"] != "none":
            native._first_assertion(facts, events["streamAssertion"], events["streamEventOrdinal"])
        if events["category"] != "none":
            facts.update(phase=events["phase"], category=events["category"])
        record["executionDiagnostics"] = facts
        condition = native._diagnostic_outcome(facts)
        if condition is not None:
            native._first_failure(facts, "event", condition)
        phase = "stream"
        parsed = reply_stream(capture["stdout"], native._input(root, native._protocol(root), "taxonomy"), readable, paths["workspace"])
        record.update(terminal=parsed["terminal"], readonlyCommandCount=parsed["readonlyCommandCount"],
                      publicReads=native._public_reads(capture["stdout"], readable, paths))
        phase = "response"
        _final_output(final, identity, parsed["messages"][-1])
        facts["finalOutputVerified"] = True
        record["replies"] = public_replies(parsed["messages"])
        _require(record["cliLaunchCount"] == 1 and facts["inputFullyDelivered"], "prompt delivery incomplete")
        if facts["category"] != "none":
            raise native.NativeDiagnosticError(facts)
        record["status"] = "CAPTURED" if record["replies"]["retentionComplete"] else "INCOMPLETE"
        if record["status"] == "INCOMPLETE":
            native._first_failure(facts, "response", "reply-retention-incomplete")
    except (OSError, ValueError, KeyError, native.NativeObservationError, subprocess.SubprocessError) as error:
        record["status"] = "INCOMPLETE"
        facts = dict(error.facts) if isinstance(error, native.NativeDiagnosticError) else record["executionDiagnostics"]
        if isinstance(error, native.NativeStreamError):
            native._first_assertion(facts, error.code, error.event_ordinal)
        if events["streamAssertion"] != "none":
            native._first_assertion(facts, events["streamAssertion"], events["streamEventOrdinal"])
            facts.update(phase=events["phase"], category=events["category"], policyReason=events["policyReason"])
        native._first_failure(facts, phase, "reply-capture-incomplete")
        record["executionDiagnostics"] = facts
        del error
    finally:
        facts = record["executionDiagnostics"]
        if identity is not None:
            try:
                meta = final.lstat()
                _require(stat.S_ISREG(meta.st_mode) and (meta.st_dev, meta.st_ino) == identity, "final reply ownership changed")
                final.unlink()
            except (OSError, native.NativeObservationError):
                facts["cleanupFailed"] = True
                native._first_failure(facts, "cleanup", "cleanup-failed")
                record["status"] = "INCOMPLETE"
        for key, save in (("operatorCapture", operator.save), ("operatorStderrCapture", operator.save_stderr),
                          ("operatorReadCapture", operator.save_command)):
            record[key] = save(ordinal)
            if record[key]["status"] == "write-failed":
                facts["cleanupFailed"] = True
                native._first_failure(facts, "cleanup", "cleanup-failed")
                record["status"] = "INCOMPLETE"
        if "capture" in locals():
            del capture
        if record["cliLaunchCount"]:
            try:
                record["inputsAfter"] = _verify_inputs(root, run_root, ordinal, prepared)
                record["postcheck"] = "valid"
            except (OSError, ValueError, native.NativeObservationError):
                record["postcheck"] = "invalid"
                native._first_failure(facts, "postcheck", "input-changed")
                record["status"] = "INCOMPLETE"
    return record


def run(root: Path, run_root: Path, *, authorized: bool = False, fixed_acceptance: bool = False,
        revision_four: bool = False, independent: bool = False, runner=None) -> dict:
    _require(sum((fixed_acceptance, revision_four, independent)) <= 1, "select one observation window")
    fixed_acceptance = fixed_acceptance or revision_four
    _require(authorized, "explicit three-call authorization required")
    p = protocol(root)
    _require(run_root.name == (INDEPENDENT["runName"] if independent else native._fixed_contract(revision_four)["clarificationRunName"] if fixed_acceptance else RUN_NAME),
             "unregistered supplemental run root")
    _unrecorded(root, p, fixed_acceptance=fixed_acceptance, revision_four=revision_four, independent=independent)
    state = _json(_read(run_root / STATE))
    chain = independent_attempt_history(root) if independent else native.completed_fixed_routing(root, Path(state["previousRunRoot"]), simulated=runner is not None, revision_four=revision_four)[1] if fixed_acceptance else attempt_history(root)
    _require(state["protocolDigest"] == p["protocolDigest"] and state["attemptHistory"] == chain and
             [r["ordinal"] for r in state["cases"]] == list(ORDINALS), "supplement preparation changed")
    _require(state["runMode"] == ("actual" if runner is None else "simulated"), "preparation mode mismatch")
    limits = INDEPENDENT["limits"] if independent else p[native._fixed_history_key(revision_four)]["limits"] if fixed_acceptance else p["limits"]
    _require(chain["attempts"] + len(ORDINALS) <= limits["maximumCumulativeAttempts"], "budget exhausted")
    if fixed_acceptance or independent:
        for name in ["batch-started.json", RESULT, *[f"attempt-{i:02d}.json" for i in ORDINALS]]:
            _require(not (run_root / name).exists() and not (run_root / name).is_symlink(),
                     "fixed clarification already attempted")
    operator = native.OperatorDiagnostics(run_root)
    invoke = native.bounded_process if runner is None else runner
    source = None
    if independent:
        source = _independent_source(root, p) if runner is None else None
        _require(state.get("independentClarification") == INDEPENDENT and state.get("executionSource") == source,
                 "independent clarification execution or registration changed")
    elif runner is None and fixed_acceptance:
        source = native._execution_source(root)
        _require(source == native._fixed_registration(root, run_root.parent, revision_four=revision_four)["executionSource"],
                 "fixed clarification execution changed after registration")
    elif runner is None:
        git_env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
        values = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD", "HEAD^{tree}"], env=git_env).decode().splitlines()
        source = {"commit": values[0], "tree": values[1]}
        for b in p["bindings"]:
            data = subprocess.check_output(["git", "-C", str(root), "show", values[0] + ":" + b["path"]], env=git_env)
            _require(digest(data) == b["sha256"], "execution implementation is not committed")
        committed_protocol = subprocess.check_output(["git", "-C", str(root), "show", values[0] + ":" + PROTOCOL.as_posix()], env=git_env)
        _require(committed_protocol == _read(root / PROTOCOL), "supplement protocol is not committed")
    _exclusive(run_root / "batch-started.json", _bytes({"protocolDigest": p["protocolDigest"], "priorAttempts": chain["attempts"]}))
    cases = []
    for prepared in state["cases"]:
        if any(c["status"] == "INCOMPLETE" for c in cases):
            cases.append({**prepared, "status": "NOT-RUN", "attemptCount": 0, "cliLaunchCount": 0})
            continue
        cases.append(_capture_case(root, run_root, prepared["ordinal"], prepared, Path(state["executable"]), operator, invoke))
    doc = {"executionSource": source, "protocolDigest": p["protocolDigest"], "kind": "single-user-visible-reply", "runMode": state["runMode"],
           "priorResultSha256": chain["routingResultSha256"] if fixed_acceptance or independent else PRIOR,
           "priorSupplementSha256": native.FIXED_REPLY_PRIORS[-1] if fixed_acceptance or independent else PRIOR_SUPPLEMENT,
           "priorAttemptCount": chain["attempts"], "caseResults": cases,
           "attemptCount": sum(c["attemptCount"] for c in cases), "cliLaunchCount": sum(c["cliLaunchCount"] for c in cases),
           "modelRequestCount": None, "semanticAssessment": "separate-review-required",
           "loadingReceipt": "not-observed", "cleanup": "retained-dedicated-test-state"}
    doc["cumulativeAttemptCount"] = chain["attempts"] + doc["attemptCount"]
    doc["cumulativeCliLaunchCount"] = chain["cliLaunches"] + doc["cliLaunchCount"]
    if fixed_acceptance:
        doc["fixedAcceptanceWindow"] = native._fixed_contract(revision_four)["windowId"]
    if independent:
        doc["independentClarificationWindow"] = INDEPENDENT["windowId"]
    _exclusive(run_root / RESULT, _bytes(doc))
    return doc


def check(root: Path) -> list[str]:
    try:
        p = protocol(root)
        chain = attempt_history(root)
        history = _json(_read(root / HISTORY))
        prior_entries = _json(_read(root / ARCHIVE / HISTORY.name))["results"]
        recorded = p
        if history["protocolDigest"] != p["protocolDigest"]:
            recorded = _json(_read(root / RECORDED_PROTOCOL))
            unsigned = dict(recorded)
            _require(unsigned.pop("protocolDigest") == "sha256:" + digest(_bytes(unsigned)),
                     "recorded supplement protocol changed")
        _require(history["protocolDigest"] == recorded["protocolDigest"] and 1 <= len(history["results"]) <= 2 and
                 history["results"][:1] == prior_entries,
                 "supplement history mismatch")
        cases = legacy.load_golden_cases(root)
        fixtures = native._input(root, native._protocol(root), "fixtureMatrix")
        fixed = history["fixedAcceptance"]
        fixed_protocol = p
        if fixed["protocolDigest"] != p["protocolDigest"]:
            data = _read(root / native.FIXED_PROTOCOL_ARCHIVE / PROTOCOL.name)
            _require(digest(data) == "7585a36fb81f07a95f1fed58b8d3fba8689a096565990ab302a0068911b28e6f",
                     "recorded fixed clarification protocol bytes changed")
            fixed_protocol = _json(data)
        _require(set(fixed) == {"windowId", "protocolDigest", "results"} and
                 fixed["windowId"] == native.FIXED_ACCEPTANCE["windowId"] and
                 fixed["protocolDigest"] == fixed_protocol["protocolDigest"] and
                 type(fixed["results"]) is list and len(fixed["results"]) <= 1,
                 "fixed clarification registration changed")
        fourth = history["revisionFourAcceptance"]
        fourth_protocol = p
        if fourth["protocolDigest"] != p["protocolDigest"]:
            data = _read(root / native.REVISION_FOUR_PROTOCOL_ARCHIVE / PROTOCOL.name)
            _require(digest(data) == "83c4e48b6d3dffc162d6a35f5f036399df2b148f4afad32806d1c93fa10c40cd",
                     "recorded revision 4 clarification protocol bytes changed")
            fourth_protocol = _json(data)
        _require(set(fourth) == {"windowId", "protocolDigest", "results"} and
                 fourth["windowId"] == native.REVISION_FOUR_ACCEPTANCE["windowId"] and
                 fourth["protocolDigest"] == fourth_protocol["protocolDigest"] and
                 type(fourth["results"]) is list and len(fourth["results"]) <= 1,
                 "revision 4 clarification registration changed")
        separate = history["independentClarification"]
        separate_protocol = p
        if separate["protocolDigest"] != p["protocolDigest"]:
            data = _read(root / "evals/no-hook-observation/historical-protocols/independent-clarification-1/clarification-protocol-v1.json")
            _require(digest(data) == "63d9229687cb9be0f077bb902b810f94f5435d6fa46b052d184bf1a139981ad9", "recorded independent clarification protocol bytes changed")
            separate_protocol = _json(data)
        _require(set(separate) == {"windowId", "protocolDigest", "results"} and
                 separate["windowId"] == INDEPENDENT["windowId"] and
                 separate["protocolDigest"] == separate_protocol["protocolDigest"] and
                 type(separate["results"]) is list and len(separate["results"]) <= 1,
                 "independent clarification history changed")
        independent_attempt_history(root)
        for entry in [*history["results"], *fixed["results"], *fourth["results"], *separate["results"]]:
            independent = entry in separate["results"]
            revision_four = entry in fourth["results"]
            new_fixed = revision_four or entry in fixed["results"]
            historical = entry["sha256"] == PRIOR_SUPPLEMENT
            active = separate_protocol if independent else fourth_protocol if revision_four else fixed_protocol if new_fixed else _json(_read(root / ARCHIVE / PROTOCOL.name)) if historical else recorded
            prior_count = 98 if independent else 103 if revision_four else 92 if new_fixed else 70 if historical else chain["attempts"]
            prior_result = INDEPENDENT["priorResultSha256"] if independent else native._fixed_result_binding(root, revision_four=revision_four)["sha256"] if new_fixed else PRIOR
            data = _read(root / entry["path"])
            _require(digest(data) == entry["sha256"], "supplement result digest changed")
            d = _json(data)
            _require(d["protocolDigest"] == active["protocolDigest"] and d["priorResultSha256"] == prior_result and
                     d["priorAttemptCount"] == prior_count and
                     [c["ordinal"] for c in d["caseResults"]] == list(ORDINALS), "supplement result binding mismatch")
            if not historical:
                _require(d["priorSupplementSha256"] == (native.FIXED_REPLY_PRIORS[-1] if new_fixed or independent else PRIOR_SUPPLEMENT),
                         "new result lost prior supplement")
            if new_fixed:
                _require(d["fixedAcceptanceWindow"] == native._fixed_contract(revision_four)["windowId"] and
                         d["runMode"] == "actual" and d["executionSource"] == {
                             "commit": entry["implementationCommit"], "tree": entry["implementationTree"]},
                         "fixed clarification execution binding changed")
            if independent:
                _require(set(entry) == {"path", "sha256", "implementationCommit", "implementationTree"} and
                         entry["path"] == "evals/no-hook-observation/results/clarification-" + entry["sha256"] + ".json" and
                         d["independentClarificationWindow"] == INDEPENDENT["windowId"] and
                         "fixedAcceptanceWindow" not in d and d["runMode"] == "actual" and
                         d["executionSource"] == {"commit": entry["implementationCommit"], "tree": entry["implementationTree"]},
                         "independent clarification execution binding changed")
            stopped = False
            for c in d["caseResults"]:
                ordinal = c["ordinal"]
                case = cases[ordinal - 1]
                prompt = reply_prompt(case["request"], native._definition(fixtures, ordinal), active["instructions"])
                _require(c["caseId"] == case["id"] and c["requestSha256"] == digest(case["request"].encode()) and
                         c["promptSha256"] == digest(prompt), "supplement input changed")
                _require(type(c["attemptCount"]) is int and c["attemptCount"] in (0, 1) and
                         type(c["cliLaunchCount"]) is int and 0 <= c["cliLaunchCount"] <= c["attemptCount"], "invalid attempt accounting")
                _require(c["status"] in {"CAPTURED", "INCOMPLETE", "NOT-RUN"}, "invalid capture status")
                if c["status"] == "NOT-RUN":
                    _require(c["attemptCount"] == c["cliLaunchCount"] == 0, "unrun case consumed an attempt")
                _require(not stopped or c["status"] == "NOT-RUN", "supplement continued after reliability stop")
                stopped |= c["status"] == "INCOMPLETE"
                if c["status"] == "CAPTURED":
                    f = c["executionDiagnostics"]
                    _require(c["attemptCount"] == c["cliLaunchCount"] == 1 and f["category"] == "none" and
                             f["returnCode"] == 0 and f["inputFullyDelivered"] and f["finalOutputVerified"] and
                             not any(f[k] for k in ("timedOut", "observerTerminated", "cleanupFailed")) and
                             c["terminal"] == "turn.completed" and c["postcheck"] == "valid" and
                             c["replies"]["retentionComplete"], "incomplete capture claimed complete")
                    messages = c["replies"]["messages"]
                    _require(type(messages) is list and messages and all(type(x) is str and x for x in messages) and
                             c["replies"]["originalVisibleMessageCount"] == len(messages), "retained message count invalid")
                    _require(sum(len(x.encode()) for x in messages) <= REPLY_LIMIT and
                             public_replies(c["replies"]["messages"])["retentionComplete"], "retained reply not bounded/public")
            _require(d["attemptCount"] == sum(c["attemptCount"] for c in d["caseResults"]) and
                     d["cliLaunchCount"] == sum(c["cliLaunchCount"] for c in d["caseResults"]) and
                     d["cumulativeAttemptCount"] == prior_count + d["attemptCount"] <=
                     (INDEPENDENT["limits"] if independent else active[native._fixed_history_key(revision_four)]["limits"] if new_fixed else active["limits"])["maximumCumulativeAttempts"] and
                     d["cumulativeCliLaunchCount"] == prior_count + d["cliLaunchCount"] and d["modelRequestCount"] is None,
                     "supplement cumulative accounting mismatch")
    except (OSError, ValueError, KeyError, native.NativeObservationError):
        return ["clarification supplement contract or result invalid"]
    return []


def main(argv=None, *, root=REPOSITORY_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "prepare", "run"))
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--bundle-root", type=Path)
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--fixed-acceptance", action="store_true")
    parser.add_argument("--revision-four-acceptance", action="store_true")
    parser.add_argument("--independent-clarification", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.mode == "check":
            failures = check(root)
            print("Clarification check: " + ("FAIL" if failures else "PASS"))
            return int(bool(failures))
        _require(args.run_root is not None, "run root required")
        if args.mode == "prepare":
            _require(args.previous is not None and args.bundle_root is not None, "registered predecessor and new bundle required")
            prepare(root, args.run_root, args.previous, bundle_root=args.bundle_root,
                    authorized=args.authorize, fixed_acceptance=args.fixed_acceptance, revision_four=args.revision_four_acceptance,
                    independent=args.independent_clarification)
            print("Prepared three dedicated clarification states; no models started.")
        else:
            d = run(root, args.run_root, authorized=args.authorize, fixed_acceptance=args.fixed_acceptance, revision_four=args.revision_four_acceptance,
                    independent=args.independent_clarification)
            print(json.dumps({"attemptCount": d["attemptCount"], "cliLaunchCount": d["cliLaunchCount"],
                              "cumulativeAttemptCount": d["cumulativeAttemptCount"],
                              "cases": [{"ordinal": c["ordinal"], "status": c["status"],
                                         "diagnostic": c.get("executionDiagnostics", {}).get("category")} for c in d["caseResults"]]}))
        return 0
    except (OSError, ValueError, KeyError, native.NativeObservationError, subprocess.SubprocessError):
        print("Clarification operation stopped; no raw exception or client output retained in console.")
        return 1
