"""Relay verified native empty-discovery facts without choosing a route.

The app-server query and exec must first have the same discovery scope. This
module accepts a complete native response, not an installation fixture or an
expected assessment. Nonempty responses retain the existing input verbatim.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class DiscoveryQueryError(ValueError):
    """A failed or unbound query cannot become an empty-discovery statement."""


class DiscoveryExchange:
    """The supported initialize/skills-list exchange; no thread or turn API."""

    def __init__(self, cwd: Path, codex_home: Path):
        self.cwd = cwd
        self.codex_home = codex_home
        self.initialized = False
        self.entry = None
        self.unauthenticated_notifications = 0
        self.disabled_remote_notifications = 0

    def receive(self, event: Any) -> list[dict[str, Any]]:
        if type(event) is not dict:
            raise DiscoveryQueryError("native query event is not an object")
        if "method" in event:
            envelope = (set(event) == {"method", "params", "emittedAtMs"}
                        and type(event["emittedAtMs"]) is int and 0 <= event["emittedAtMs"] < 2**63)
            # Every initialized client receives this documented status snapshot,
            # even with features.remote_control=false. Do not persist its local
            # identity fields or accept an enabled remote environment.
            if (self.initialized and envelope
                    and event["method"] == "remoteControl/status/changed"):
                params = event["params"]
                if (type(params) is dict and set(params) == {
                        "status", "serverName", "installationId", "environmentId"}
                        and params["status"] == "disabled"
                        and params["environmentId"] is None
                        and all(type(params[k]) is str for k in ("serverName", "installationId"))):
                    self.disabled_remote_notifications += 1
                    return []
                raise DiscoveryQueryError("native query remote environment is not disabled")
            # Accept an optional unauthenticated account update after initialize;
            # it is not a guaranteed startup receipt. Query precedes auth handoff.
            if (self.initialized and envelope
                    and event["method"] == "account/updated"
                    and event["params"] == {"authMode": None, "planType": None}):
                self.unauthenticated_notifications += 1
                return []
            raise DiscoveryQueryError("native query received an unexpected notification or request")
        if not self.initialized:
            if (set(event) != {"id", "result"} or type(event["id"]) is not int
                    or event["id"] != 1 or type(event["result"]) is not dict
                    or event["result"].get("codexHome") != str(self.codex_home)):
                raise DiscoveryQueryError("native initialization scope does not match")
            self.initialized = True
            return [{"method": "initialized", "params": {}},
                    {"id": 2, "method": "skills/list", "params": {
                        "cwds": [str(self.cwd)], "forceReload": True}}]
        if self.entry is not None:
            raise DiscoveryQueryError("native query returned more than one response")
        self.entry = checked_discovery_entry(event, cwd=self.cwd, request_id=2)
        return []


def checked_discovery_entry(response: Any, *, cwd: Path, request_id: int) -> dict[str, Any]:
    if (type(response) is not dict or set(response) != {"id", "result"}
            or type(response["id"]) is not int or response["id"] != request_id):
        raise DiscoveryQueryError("native discovery response does not match its request")
    result = response["result"]
    if type(result) is not dict or set(result) != {"data"}:
        raise DiscoveryQueryError("native discovery result is incomplete")
    data = result["data"]
    if type(data) is not list or len(data) != 1:
        raise DiscoveryQueryError("native discovery requires exactly its requested cwd")
    entry = data[0]
    if (type(entry) is not dict or set(entry) != {"cwd", "skills", "errors"}
            or not cwd.is_absolute() or entry["cwd"] != str(cwd)
            or type(entry["skills"]) is not list or type(entry["errors"]) is not list):
        raise DiscoveryQueryError("native discovery entry has an incomplete or different scope")
    if entry["errors"]:
        raise DiscoveryQueryError("native discovery reported an error")
    for skill in entry["skills"]:
        if (type(skill) is not dict
                or not {"name", "description", "path", "scope", "enabled"} <= set(skill)
                or any(type(skill[key]) is not str or not skill[key]
                       for key in ("name", "description", "path", "scope"))
                or type(skill["enabled"]) is not bool):
            raise DiscoveryQueryError("native discovery metadata is incomplete")
    # Never filter disabled, unknown, or nonmatching entries to manufacture zero.
    return entry


def relay_empty_discovery(material: Any, entry: Mapping[str, Any]) -> Any:
    """Use only an entry returned by checked_discovery_entry after scope checks.

    The cwd is bound by the caller's native receipt. Only the exact empty lists
    are relayed; a local absolute state path is not added to model context.
    This is compatibility-delivered metadata, never a synthetic tool call.
    """
    prompt = relay_prompt(material.prompt_bytes, entry)
    return material if prompt is material.prompt_bytes else replace(
        material, prompt_bytes=prompt, prompt_sha256=hashlib.sha256(prompt).hexdigest())


def relay_prompt(prompt: bytes, entry: Mapping[str, Any]) -> bytes:
    if entry["errors"]:
        raise DiscoveryQueryError("failed discovery cannot be relayed")
    if entry["skills"]:
        return prompt
    facts = json.dumps({key: entry[key] for key in ("skills", "errors")},
                       ensure_ascii=True, separators=(",", ":"))
    prefix, marker, request = prompt.partition(b"\nUser request:\n")
    if not marker:
        raise DiscoveryQueryError("request boundary is missing")
    fragment = ("\nNative skills/list query result relayed by the compatibility layer "
                "for the verified current working directory. This is discovery metadata, "
                "not a model tool call or an automatic exec context-delivery receipt.\n"
                + facts + "\n").encode("utf-8")
    return prefix + fragment + marker + request


def query_scope(paths, executable, marketplace, installed, definition):
    """Check only registered public inputs and absence of alternate environments.

    app-server uses the ordinary loader; exec ignores user config. Here the only
    permitted user config contains the registered marketplace/plugin tables,
    whose subsystem is disabled by their shared overrides. EnvironmentManager
    also agrees only when environments.toml is absent and the fixed environment
    allowlist selects the local host. This window's normally completed dedicated
    source is user-confirmed Pro, excluded by frozen cloud-config eligibility.
    This is an operator fact, not a native account/updated receipt. Never read
    environments.toml, cloud configuration caches or credentials.
    """
    from . import no_hook_native_observation as native
    native._verify_config(paths, marketplace, installed)
    native._verify_discovery(paths, installed)
    for path in (paths["home"] / "environments.toml", paths["home"] / "skills"):
        if path.exists() or path.is_symlink():
            raise DiscoveryQueryError("unregistered native discovery scope")
    config = paths["home"] / "config.toml"
    return {"cwd": str(paths["workspace"]),
            "executableSha256": native.legacy.CODEX_BINARY_SHA256,
            "environment": native.case_environment(paths),
            "overrides": native._config_args(paths, executable, marketplace, installed),
            "configSha256": hashlib.sha256(native._read(config)).hexdigest() if installed else None,
            "fixtureSha256": native.fixture_identity(paths["workspace"], definition),
            "packageSha256": native.package_identity(paths["package"]) if installed else None,
            "modelMetadata": native._model_metadata(paths)}


def query_once(paths, executable, marketplace, installed, definition, *, timeout=25):
    """One no-model native query in the same fresh case scope, before auth copy.

    An exclusive marker prevents another query of a failed scope. Only the
    skills/list response and non-sensitive scope are retained. No thread/turn
    call exists here; stderr is not read or retained by the compatibility layer.
    """
    import os
    import selectors
    import subprocess
    import time
    from . import no_hook_native_observation as native
    scope = query_scope(paths, executable, marketplace, installed, definition)
    auth = paths["home"] / native.AUTH_FILE_NAME
    if auth.exists() or auth.is_symlink():
        raise DiscoveryQueryError("native query requires the fresh pre-authentication scope")
    frozen = native.legacy.freeze_executable(executable, native.legacy.CODEX_BINARY_SHA256)
    native._exclusive(paths["case"] / "discovery-query-started.json", native._bytes({
        "scope": scope, "method": "skills/list", "forceReload": True}))
    receipt = {"queryStarts": 0, "status": "failed", "scope": scope,
               "forceReload": True, "threadStarts": 0, "turnStarts": 0,
               "returnCode": None, "response": None, "failure": None}
    process, selector = None, None
    try:
        process = subprocess.Popen([str(executable), "app-server", "--listen", "stdio://",
                                    *scope["overrides"]], cwd=paths["workspace"],
            env=scope["environment"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        receipt["queryStarts"] = 1
        exchange = DiscoveryExchange(paths["workspace"], paths["home"])
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        def send(message):
            process.stdin.write(native._bytes(message))
            process.stdin.flush()
        send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "axiom_discovery_check", "version": "1"},
            "capabilities": {"experimentalApi": False}}})
        deadline, pending, total = time.monotonic() + timeout, b"", 0
        while exchange.entry is None:
            if time.monotonic() >= deadline:
                raise DiscoveryQueryError("native query timed out")
            for key, _ in selector.select(min(.2, max(0, deadline - time.monotonic()))):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    raise DiscoveryQueryError("native query ended without a complete response")
                total += len(chunk)
                if total > 1048576:
                    raise DiscoveryQueryError("native query exceeded its response limit")
                pending += chunk
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    for message in exchange.receive(json.loads(line)):
                        send(message)
        process.stdin.close()
        # Drain through EOF: late warnings or a second response cannot be lost.
        while True:
            if time.monotonic() >= deadline:
                raise DiscoveryQueryError("native query did not close normally")
            readable = selector.select(min(.2, max(0, deadline - time.monotonic())))
            if not readable:
                continue
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk:
                break
            total += len(chunk)
            if total > 1048576:
                raise DiscoveryQueryError("native query exceeded its response limit")
            pending += chunk
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                exchange.receive(json.loads(line))
        if pending.strip():
            raise DiscoveryQueryError("native query ended with an incomplete response")
        process.wait(timeout=max(.01, deadline - time.monotonic()))
        if process.returncode != 0:
            raise DiscoveryQueryError("native query exited unsuccessfully")
        native.legacy.recheck_executable(frozen)
        if query_scope(paths, executable, marketplace, installed, definition) != scope:
            raise DiscoveryQueryError("native query changed its discovery or input scope")
        receipt.update(status="verified", response={"id": 2, "result": {"data": [exchange.entry]}},
                       disabledRemoteNotifications=exchange.disabled_remote_notifications,
                       unauthenticatedNotifications=exchange.unauthenticated_notifications)
    except (OSError, ValueError, subprocess.SubprocessError, native.NativeObservationError) as error:
        receipt["failure"] = str(error) if isinstance(error, DiscoveryQueryError) else "native query failed"
    finally:
        if selector is not None:
            selector.close()
        if process is not None:
            facts = native._diagnostics()
            native._close_process(process, terminate=process.poll() is None, facts=facts)
            receipt["returnCode"] = process.returncode
            for stream in (process.stdin, process.stdout):
                if stream is not None:
                    stream.close()
        native._exclusive(paths["case"] / "discovery-query.json", native._bytes(receipt))
    if receipt["status"] != "verified":
        raise DiscoveryQueryError(receipt["failure"] or "native query failed")
    return receipt


def prepared_discovery(paths, executable, marketplace, installed, definition):
    """Recheck the same scope without querying again or reading private state."""
    from . import no_hook_native_observation as native
    raw = native._read(paths["case"] / "discovery-query.json")
    receipt = native._json(raw)
    if (receipt["status"] != "verified" or receipt["queryStarts"] != 1
            or receipt["returnCode"] != 0 or receipt["threadStarts"] != 0 or receipt["turnStarts"] != 0
            or receipt["forceReload"] is not True
            or receipt["scope"] != query_scope(paths, executable, marketplace, installed, definition)):
        raise DiscoveryQueryError("native discovery receipt or scope changed")
    entry = checked_discovery_entry(receipt["response"], cwd=paths["workspace"], request_id=2)
    return entry, {"source": "native-skills-list-via-compatibility-layer", "queryStarts": 1,
                   "receiptSha256": hashlib.sha256(raw).hexdigest(),
                   "scopeSha256": hashlib.sha256(native._bytes(receipt["scope"])).hexdigest(),
                   "skillCount": len(entry["skills"]), "errorCount": 0,
                   "forceReload": True, "returnCode": 0}


def checked_summary(summary):
    if (type(summary) is not dict or set(summary) != {"source", "queryStarts", "receiptSha256",
            "scopeSha256", "skillCount", "errorCount", "forceReload", "returnCode"}
            or summary["source"] != "native-skills-list-via-compatibility-layer"
            or type(summary["queryStarts"]) is not int or summary["queryStarts"] != 1
            or type(summary["skillCount"]) is not int or summary["skillCount"] < 0
            or summary["errorCount"] != 0 or summary["returnCode"] != 0
            or summary["forceReload"] is not True
            or any(type(summary[k]) is not str or len(summary[k]) != 64
                   or any(c not in "0123456789abcdef" for c in summary[k])
                   for k in ("receiptSha256", "scopeSha256"))):
        raise DiscoveryQueryError("invalid native discovery summary")
    return summary


def relay_recorded(material, summary):
    """Reconstruct delivered bytes; an editable result is not a new host receipt."""
    checked_summary(summary)
    if summary["skillCount"]:
        return material
    return relay_empty_discovery(material, {"skills": [], "errors": []})
