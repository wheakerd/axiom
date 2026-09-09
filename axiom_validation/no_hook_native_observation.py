"""Source-bound native CLI observation, independent of the retired v1 backend.

The operator owns a dedicated, non-concurrently-modified test root. Authentication
is performed only by the official client in each case's separate CODEX_HOME.
Only explicitly authorized test-auth reuse copies the official file as opaque
bytes between registered homes; it never parses, hashes or exposes it. Its
ordinary process timeout is not a claim of adversarial descendant containment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import time
import tomllib
from typing import Any, Callable, Mapping, Sequence

from . import no_hook_observation as legacy
from .context import REPOSITORY_ROOT


PROTOCOL_RELATIVE = Path("evals/no-hook-observation/codex-native-protocol-v2.json")
RESULT_SCHEMA_RELATIVE = Path("evals/no-hook-observation/codex-native-result-schema-v2.json")
HISTORY_RELATIVE = Path("evals/no-hook-observation/result-history-v2.json")
PROTOCOL_ID = "axiom-codex-native-observation-v2"
DISCOVERY_MECHANISM = "host-user-skills-from-installed-package"
STATE_NAME = "native-preparation.json"
CASE_COUNT = 16
AUTH_FILE_NAME = "auth.json"
AUTH_COPY_STATE = "test-auth-copy-state.json"
NativeObservationError = legacy.ObservationError
HISTORICAL_RESULT_SHA256 = "5a7b9965820612204138f140b404a9fb7fb018c7f07ada14e2e09ccc514ad4ef"
HISTORICAL_PROTOCOL_DIGEST = "sha256:735ad73170d6d1f3b4b6a21a4dfdc4dc280100a07e47bead22b2af9562a577dc"
EVENT_TYPES = ("thread.started", "turn.started", "turn.completed", "turn.failed", "error",
               "item.started", "item.updated", "item.completed", "unknown")


def _diagnostics() -> dict[str, Any]:
    return {"phase": "none", "category": "none", "returnCode": None, "signal": None,
            "timedOut": False, "observerTerminated": False, "cleanupFailed": False,
            "inputBytesSent": 0, "inputFullyDelivered": None, "stdoutBytes": 0,
            "stderrBytes": 0, "eventCount": 0, "eventTypes": [],
            "stderrClassification": "not-observed", "officialErrorCode": "unknown",
            "itemTypes": [], "policyReason": "none"}


def _first_failure(facts: dict[str, Any], phase: str, category: str) -> None:
    if facts["category"] == "none":
        facts.update(phase=phase, category=category)


class NativeDiagnosticError(NativeObservationError):
    """Only closed facts cross the capture boundary; never retain raw exceptions."""

    def __init__(self, facts: Mapping[str, Any]):
        self.facts = dict(facts)
        super().__init__("native " + self.facts["category"])


def _stderr_classification(data: bytes) -> str:
    if not data:
        return "empty"
    # Frozen exec reads '-' from stdin with this informational notice. Unknown
    # stderr is retained only as a classification and cannot establish success.
    fixed = {b"Reading prompt from stdin...", b"Reading additional input from stdin...",
             b"Could not create otel exporter: panicked during initialization"}
    prefixes = (b"Could not create otel exporter: ",
                b"WARNING: proceeding, even though we could not create PATH aliases: ",
                b"WARNING: failed to clean up stale arg0 temp dirs: ")
    if data.endswith(b"\n") and all(line in fixed or any(
            line.startswith(prefix) and len(line) > len(prefix) for prefix in prefixes)
            for line in data.splitlines()):
        return "known-nonfatal"
    return "unknown"


def _capture_facts(capture: Mapping[str, Any]) -> dict[str, Any]:
    facts = dict(capture.get("diagnostics", _diagnostics()))
    code = capture["returncode"]
    facts.update(returnCode=code, signal=-code if code is not None and code < 0 else None,
                 stdoutBytes=len(capture["stdout"]), stderrBytes=len(capture["stderr"]),
                 stderrClassification=_stderr_classification(capture["stderr"]))
    if code != 0:
        _first_failure(facts, "exit", "process-exit")
    if facts["stderrClassification"] == "unknown":
        _first_failure(facts, "exit", "unknown-stderr")
    return facts
IMPLEMENTATION_PATHS = (
    "axiom_validation/context.py", "axiom_validation/no_hook_bundle.py",
    "axiom_validation/no_hook_linux_isolation.py", "axiom_validation/no_hook_native_observation.py",
    "axiom_validation/no_hook_observation.py", "axiom_validation/no_hook_profile.py",
    "axiom_validation/release_versions.py", "axiom_validation/routing_evals/jsonio.py",
    "scripts/run-no-hook-native-observation.py",
)
INPUT_PATHS = {
    "goldenSet": legacy.GOLDEN_SET_RELATIVE.as_posix(),
    "modelResponseSchema": legacy.MODEL_RESPONSE_SCHEMA_RELATIVE.as_posix(),
    "promptEnvelope": "evals/no-hook-observation/codex-native-prompt-envelope-v2.json",
    "taxonomy": legacy.TAXONOMY_RELATIVE.as_posix(), "fixtureMatrix": legacy.FIXTURES_RELATIVE.as_posix(),
    "profile": legacy.PROFILE_RELATIVE.as_posix(), "benchmark": legacy.BENCHMARK_RELATIVE.as_posix(),
    "bundleSchema": "evals/no-hook/bundle-manifest-schema-v1.json",
    "staticBundleEvidence": legacy.STATIC_BUNDLE_EVIDENCE_RELATIVE.as_posix(),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise NativeObservationError(message)


def _json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=legacy._reject_duplicate_pairs)


def _bytes(document: Any) -> bytes:
    return legacy._canonical_json(document) + b"\n"


def _read(path: Path, maximum: int = legacy.MAX_CONTRACT_BYTES) -> bytes:
    return legacy._read_regular(path, "native non-sensitive input", maximum=maximum)


def _exclusive(path: Path, data: bytes, mode: int = 0o600) -> None:
    """Never overwrite a prior attempt, user object, or partial preparation."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        view = memoryview(data)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise OSError("short native-state write")
            view = view[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ordinary_directory(path: Path) -> Path:
    _require(path.is_absolute(), "native paths must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        _require(stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
                 "native directory contains a non-directory or symlink")
    return path


def _protocol(root: Path) -> dict[str, Any]:
    document = _json(_read(root / PROTOCOL_RELATIVE))
    _require(type(document) is dict, "native protocol must be an object")
    _require(document.get("schemaVersion") == "2" and document.get("protocolId") == PROTOCOL_ID,
             "native protocol identity mismatch")
    _require(document.get("protocolDigest") == legacy.self_digest(document, "protocolDigest"),
             "native protocol digest mismatch")
    _require(document.get("caseIds") == list(legacy.EXPECTED_CASE_IDS), "native case order mismatch")
    _require(document.get("discovery") == {
        "mechanism": DISCOVERY_MECHANISM, "pluginRuntimeEnabled": False,
        "root": "HOME/.agents/skills", "target": "installed-package/skills",
        "noPluginControlOrdinal": 11,
    }, "native discovery contract mismatch")
    _require(document.get("authentication") == {
        "modes": ["independent-official-login", "serial-test-auth-copy"],
        "fileName": AUTH_FILE_NAME, "sourceOrdinal": 1,
        "refreshHandoff": "after-successful-client-exit", "contentRecorded": False,
    }, "native authentication contract mismatch")
    _require(document.get("cli") == {
        "version": legacy.CODEX_VERSION, "sha256": legacy.CODEX_BINARY_SHA256,
        "model": legacy.MODEL, "reasoningEffort": legacy.REASONING_EFFORT,
    }, "native CLI/model identity mismatch")
    _require(document.get("limits") == {
        "maxCaseLaunches": 16, "timeoutSeconds": 120,
        "stdoutBytes": 1048576, "stderrBytes": 262144,
    }, "native execution limits mismatch")
    _require(document.get("diagnosticRevision") == 1 and document.get("followup") == {
        "priorResultSha256": HISTORICAL_RESULT_SHA256, "priorAttempts": 1,
        "maximumCumulativeAttempts": 17, "maximumCaseOneAttempts": 2,
        "remainingCaseAttempts": 1,
    }, "native diagnostic migration or retry budget mismatch")
    bindings = list(document.get("implementationBindings", []))
    _require([item.get("path") for item in bindings] == list(IMPLEMENTATION_PATHS),
             "native implementation binding owner set changed")
    inputs = document.get("inputs", {})
    _require(set(inputs) == set(INPUT_PATHS), "native input binding owner set changed")
    for key, relative in INPUT_PATHS.items():
        _require(inputs[key].get("path") == relative, "native input owner changed")
    _require(document.get("resultSchema", {}).get("path") == RESULT_SCHEMA_RELATIVE.as_posix(),
             "native result schema owner changed")
    bindings += list(inputs.values())
    bindings.append(document.get("resultSchema", {}))
    for binding in bindings:
        _require(type(binding) is dict and set(binding) == {"path", "sha256"},
                 "native file binding must be closed")
        relative = Path(binding["path"])
        _require(not relative.is_absolute() and ".." not in relative.parts,
                 "native binding is not repository-relative")
        _require(hashlib.sha256(_read(root / relative)).hexdigest() == binding["sha256"],
                 "native bound input changed")
    evidence = _json(_read(root / legacy.STATIC_BUNDLE_EVIDENCE_RELATIVE))
    bundle = document.get("bundle", {})
    _require(bundle.get("manifestDigest") == evidence["bundleManifest"]["bundleManifestDigest"] and
             bundle.get("archiveSha256") == evidence["builds"]["archiveSha256"] and
             bundle.get("profileRuntimeDigest") == evidence["bundleManifest"]["profileRuntimeDigest"],
             "native bundle references differ from static evidence")
    _require(type(bundle.get("packageSha256")) is str and
             legacy.SHA256_PATTERN.fullmatch(bundle["packageSha256"]) is not None,
             "native package identity is invalid")
    return document


def validate_native_protocol(root: Path = REPOSITORY_ROOT) -> list[str]:
    """Read-only default validation; no detector, process, install or login."""
    try:
        protocol = _protocol(root)
        legacy.load_golden_cases(root)
        legacy.load_codex_benchmark_contract(root)
        _require(protocol["inputs"]["goldenSet"]["path"] == legacy.GOLDEN_SET_RELATIVE.as_posix(),
                 "native Golden Set owner changed")
        _require(protocol["inputs"]["modelResponseSchema"]["path"] ==
                 legacy.MODEL_RESPONSE_SCHEMA_RELATIVE.as_posix(), "native model schema owner changed")
        _require(protocol["inputs"]["fixtureMatrix"]["path"] == legacy.FIXTURES_RELATIVE.as_posix(),
                 "native fixture owner changed")
        history = _json(_read(root / HISTORY_RELATIVE))
        _require(set(history) == {"schemaVersion", "kind", "protocol", "results", "current", "historicalResults"} and
                 history["schemaVersion"] == "2" and history["kind"] == "axiom-codex-native-result-history" and
                 history["protocol"] == {"path": PROTOCOL_RELATIVE.as_posix(), "digest": protocol["protocolDigest"]},
                 "native history identity is inconsistent")
        historical = history["historicalResults"]
        expected_historical = {"path": "evals/no-hook-observation/results/codex-native-" + HISTORICAL_RESULT_SHA256 + ".json",
            "sha256": HISTORICAL_RESULT_SHA256, "protocolDigest": HISTORICAL_PROTOCOL_DIGEST,
            "implementationCommit": "f7a590ad58e2a1200f64009e48556fa7448f2f86",
            "resultCommit": "5ac4c2b197bd4f3a32a9d50ca2de4814aefcf2c3", "attemptCount": 1}
        _require(historical == [expected_historical], "historical native evidence migration changed")
        _require(hashlib.sha256(_read(root / expected_historical["path"])).hexdigest() ==
                 HISTORICAL_RESULT_SHA256, "historical native result bytes changed")
        # The exact previously validated bytes retain their old contract. They
        # are not interpreted under the new schema or filled with new facts.
        records = history["results"]
        _require(type(records) is list and len(records) <= 1, "native history exceeds the single-batch budget")
        current = {"codexObservation": "not-run", "hostClaim": False, "credentialUsed": False,
                   "cliLaunchCount": 0, "modelRequestCount": None, "pluginInstalled": False}
        if records:
            binding = records[0]
            _require(type(binding) is dict and set(binding) == {"path", "sha256"}, "native history result reference is not closed")
            relative = Path(binding["path"])
            _require(relative.parent == Path("evals/no-hook-observation/results") and
                     relative.name.startswith("codex-native-") and relative.suffix == ".json",
                     "native history result owner is invalid")
            data = _read(root / relative)
            _require(hashlib.sha256(data).hexdigest() == binding["sha256"], "native history result bytes changed")
            result = _json(data)
            _require(not validate_native_result(result, root), "native history result is invalid")
            _require(result["priorResultSha256"] == HISTORICAL_RESULT_SHA256, "result does not continue the historical budget")
            _require(result["runMode"] == "actual", "simulated result is not a host-history observation")
            current = {"codexObservation": result["status"].lower(), "hostClaim": result["hostClaim"],
                       "credentialUsed": result["cliLaunchCount"] > 0, "cliLaunchCount": result["cliLaunchCount"],
                       "modelRequestCount": None, "pluginInstalled": any(
                           item["installation"] == "verified" for item in result["caseResults"])}
        _require(history["current"] == current, "native history summary differs from its result")
        return []
    except (OSError, ValueError, KeyError, TypeError, NativeObservationError) as error:
        return [str(error)]


def _input(root: Path, protocol: Mapping[str, Any], name: str) -> Any:
    return _json(_read(root / protocol["inputs"][name]["path"]))


def _case_paths(run_root: Path, ordinal: int) -> dict[str, Path]:
    case = run_root / f"case-{ordinal:02d}"
    return {"case": case, "home": case / "client-home", "user": case / "empty-user",
            "workspace": case / "workspace", "state": case / "state", "tmp": case / "tmp",
            "discovery": case / "empty-user/.agents/skills",
            "package": case / "client-home" / "plugins/cache" / legacy.MARKETPLACE_NAME /
            legacy.PLUGIN_NAME / legacy.PLUGIN_VERSION}


def case_environment(paths: Mapping[str, Path]) -> dict[str, str]:
    """An allowlist, never a filtered copy of the operator's environment."""
    return {"HOME": str(paths["user"]), "CODEX_HOME": str(paths["home"]),
            "XDG_CONFIG_HOME": str(paths["user"] / "config"),
            "XDG_CACHE_HOME": str(paths["user"] / "cache"),
            "XDG_DATA_HOME": str(paths["user"] / "data"),
            "TMPDIR": str(paths["tmp"]), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8", "NO_COLOR": "1", "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null", "PYTHONDONTWRITEBYTECODE": "1"}


def _config_args(paths: Mapping[str, Path], executable: Path, marketplace: Path,
                 installed: bool) -> list[str]:
    # Restricted profiles deny everything outside explicit read roots. A deny
    # on client-home itself is a final backend mask, not an overridable parent
    # rule: it would also hide the deliberately allowed installed package.
    filesystem = {":root": "deny", ":minimal": "read", str(executable): "read",
                  str(paths["workspace"]): "read"}
    if installed:
        filesystem[str(paths["package"])] = "read"
    quote = lambda value: json.dumps(value, ensure_ascii=True)
    fs_table = ",".join(f"{quote(key)}={quote(value)}" for key, value in filesystem.items())
    overrides = [
        'cli_auth_credentials_store="file"', 'history.persistence="none"',
        f'sqlite_home={quote(str(paths["state"]))}', f'log_dir={quote(str(paths["state"]))}',
        'model_reasoning_effort="medium"', 'web_search="disabled"', 'mcp_servers={}',
        'skills.bundled.enabled=false',
        'shell_environment_policy.inherit="none"',
        'shell_environment_policy.set={PATH="/usr/bin:/bin",LANG="C.UTF-8",LC_ALL="C.UTF-8"}',
        f'permissions={{native-case={{filesystem={{{fs_table}}},network={{enabled=false}}}}}}',
        'default_permissions="native-case"',
    ]
    for feature in legacy.ACTUAL_CASE_FEATURE_OVERRIDES:
        if feature.startswith("features.shell_tool="):
            feature = "features.shell_tool=true"
        elif feature.startswith("features.skip_host_skill_discovery="):
            feature = "features.skip_host_skill_discovery=false"
        elif feature.startswith("features.plugins="):
            feature = "features.plugins=false"
        overrides.append(feature)
    # remote_plugin=false controls the catalog, not account-installed plugin
    # synchronization. Native user Skill discovery does not need that subsystem.
    overrides.extend(["marketplaces={}", "plugins={}"])
    return [part for override in overrides for part in ("-c", override)]


def build_native_argv(executable: Path, run_root: Path, ordinal: int) -> list[str]:
    _require(type(ordinal) is int and 1 <= ordinal <= CASE_COUNT, "unknown native case ordinal")
    paths = _case_paths(run_root, ordinal)
    return [str(executable), "--ask-for-approval", "never", "exec", "--ephemeral", "--json", "--model", legacy.MODEL,
            "--skip-git-repo-check", "--ignore-user-config",
            "--ignore-rules", "--cd", str(paths["workspace"]),
            "--output-schema", str(paths["case"] / "response-schema.json"),
            *_config_args(paths, executable, run_root / "marketplace", ordinal != 11), "-"]


def _close_process(process: subprocess.Popen, *, terminate: bool, facts: dict[str, Any]) -> None:
    """Ordinary process-group cleanup; record failure separately from first cause."""
    if process.poll() is None or terminate:
        try:
            os.killpg(process.pid, signal.SIGINT)
            facts["observerTerminated"] = True
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                facts["observerTerminated"] = True
            except ProcessLookupError:
                pass
            process.wait(timeout=2)


def bounded_process(argv: Sequence[str], *, cwd: Path, env: Mapping[str, str],
                    stdin: bytes = b"", line_callback: Callable[[bytes], None] | None = None,
                    started_callback: Callable[[], None] | None = None,
                    timeout: int = 120) -> dict[str, Any]:
    """Capture bounded facts before discarding buffers, including on failure."""
    output, errors, pending = bytearray(), bytearray(), bytearray()
    facts = _diagnostics()
    sent = 0
    try:
        process = subprocess.Popen(list(argv), cwd=cwd, env=dict(env), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, close_fds=True)
    except OSError:
        _first_failure(facts, "launch", "process-start")
        raise NativeDiagnosticError(facts) from None
    selector = None
    try:
        if started_callback is not None:
            started_callback()
        selector = selectors.DefaultSelector()
        assert process.stdin is not None and process.stdout is not None and process.stderr is not None
        for stream in (process.stdin, process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        if stdin:
            selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
        else:
            process.stdin.close()
        deadline = time.monotonic() + timeout
        while selector.get_map():
            if time.monotonic() >= deadline:
                raise TimeoutError()
            for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                if key.data == "stdin":
                    sent += os.write(key.fd, stdin[sent:sent + 8192])
                    if sent == len(stdin):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    continue
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                target = output if key.data == "stdout" else errors
                limit = legacy.MAX_STDOUT_BYTES if key.data == "stdout" else legacy.MAX_STDERR_BYTES
                target.extend(chunk)
                if len(target) > limit:
                    _first_failure(facts, "io", "output-limit")
                    raise NativeDiagnosticError(facts)
                if key.data == "stdout" and line_callback is not None:
                    pending.extend(chunk)
                    while b"\n" in pending:
                        line, _, rest = pending.partition(b"\n")
                        pending[:] = rest
                        try:
                            line_callback(bytes(line))
                        except NativeDiagnosticError as error:
                            _first_failure(facts, error.facts["phase"], error.facts["category"])
                            for field in ("eventCount", "eventTypes", "itemTypes", "policyReason"):
                                facts[field] = error.facts[field]
                            raise
                        except Exception:
                            _first_failure(facts, "event", "policy-rejected")
                            raise NativeDiagnosticError(facts) from None
                    if len(pending) > legacy.MAX_JSONL_LINE_BYTES:
                        _first_failure(facts, "io", "output-limit")
                        raise NativeDiagnosticError(facts)
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
        if sent != len(stdin):
            _first_failure(facts, "io", "input-incomplete")
    except (TimeoutError, subprocess.TimeoutExpired):
        facts["timedOut"] = True
        _first_failure(facts, "io", "timeout")
    except NativeDiagnosticError:
        pass
    except (OSError, ValueError, NativeObservationError):
        _first_failure(facts, "io", "io-failed")
    finally:
        if process.poll() is not None and process.returncode != 0:
            _first_failure(facts, "exit", "process-exit")
        try:
            _close_process(process, terminate=facts["category"] != "none", facts=facts)
        except (OSError, subprocess.SubprocessError):
            facts["cleanupFailed"] = True
            _first_failure(facts, "cleanup", "cleanup-failed")
        try:
            if selector is not None:
                selector.close()
        except OSError:
            facts["cleanupFailed"] = True
            _first_failure(facts, "cleanup", "cleanup-failed")
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                facts["cleanupFailed"] = True
                _first_failure(facts, "cleanup", "cleanup-failed")
    facts.update(inputBytesSent=sent, inputFullyDelivered=sent == len(stdin))
    capture = {"returncode": process.returncode, "stdout": bytes(output), "stderr": bytes(errors),
               "diagnostics": facts}
    closed = _capture_facts(capture)
    # Nonzero exits and stderr are classified by the caller (login has its own
    # exact status grammar); capture/cleanup failures cannot lose their facts.
    if facts["category"] != "none":
        raise NativeDiagnosticError(closed) from None
    capture["diagnostics"] = facts
    return capture


def _definition(fixtures: Mapping[str, Any], ordinal: int) -> dict[str, Any]:
    case = fixtures["cases"][ordinal - 1]
    _require(case["caseId"] == legacy.EXPECTED_CASE_IDS[ordinal - 1], "fixture case order changed")
    definition = next(item for item in fixtures["definitions"] if item["templateId"] == case["workspaceTemplate"])
    legacy._validate_fixture_definition(definition)
    return definition


def materialize_fixture(workspace: Path, definition: Mapping[str, Any]) -> str:
    _require(not any(workspace.iterdir()), "native fixture workspace must be empty")
    files = {record["path"]: record["contentUtf8"].encode("utf-8") for record in definition["files"]}
    if definition["git"]["repository"]:
        for relative in (".git", ".git/objects", ".git/refs", ".git/refs/heads", ".git/info"):
            (workspace / relative).mkdir(exist_ok=True)
        files.update({".git/HEAD": b"ref: refs/heads/main\n",
                      ".git/config": b"[core]\n\trepositoryformatversion = 0\n\tbare = false\n\tfilemode = true\n",
                      ".git/info/exclude": b"*\n"})
    for relative, data in files.items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        _exclusive(path, data, 0o444)
    return fixture_identity(workspace, definition)


def fixture_identity(workspace: Path, definition: Mapping[str, Any]) -> str:
    legacy._fixture_observed_records(workspace, definition)
    legacy._observe_inert_git_facts(workspace, definition["git"]["repository"])
    return legacy._expected_realized_fixture_digest(definition)


def package_identity(package: Path) -> str:
    """Inspect only the selected public package, never its containing home."""
    _ordinary_directory(package)
    records = legacy._verify_bundle_surface(package, fake_only=False)
    manifest = _json(_read(package / "BUNDLE-MANIFEST.json"))
    by_path = {path: (mode, size, digest) for path, mode, size, digest in records}
    for expected in manifest["runtimeFiles"]:
        _require(by_path[expected["path"]] == (0o644, expected["size"], expected["sha256"]),
                 "installed runtime bytes differ from the source-bound manifest")
    return hashlib.sha256(legacy._canonical_json(records)).hexdigest()


def _successful(capture: Mapping[str, Any], purpose: str) -> bytes:
    facts = _capture_facts(capture)
    if facts["category"] != "none":
        raise NativeDiagnosticError(facts)
    return capture["stdout"]


def _verify_config(paths: Mapping[str, Path], marketplace: Path, installed: bool) -> None:
    """This one non-sensitive TOML file is the only client-home config read."""
    config_path = paths["home"] / "config.toml"
    if not installed:
        _require(not config_path.exists() and not (paths["home"] / "plugins").exists(),
                 "no-plugin control has unexpected discovery configuration")
        return
    document = tomllib.loads(_read(config_path).decode("utf-8"))
    _require(set(document) <= {"marketplaces", "plugins"}, "test config contains unowned settings")
    _require(document.get("marketplaces") == {
        legacy.MARKETPLACE_NAME: {"source_type": "local", "source": str(marketplace)}
    }, "test config marketplace differs from verified source")
    plugins = document.get("plugins", {})
    _require(set(plugins) == {legacy.PLUGIN_ID} and plugins[legacy.PLUGIN_ID] == {"enabled": True},
             "test config contains an unverified plugin")


def _verify_discovery(paths: Mapping[str, Path], installed: bool) -> None:
    """Bind the standard user Skill root to public installed bytes, not auth."""
    alias = paths["discovery"]
    if not installed:
        _require(not alias.exists() and not alias.is_symlink(),
                 "no-plugin control has an unexpected Skill discovery root")
        return
    _ordinary_directory(alias.parent)
    _require(alias.is_symlink() and os.readlink(alias) == str(paths["package"] / "skills") and
             alias.resolve(strict=True) == paths["package"] / "skills",
             "native Skill discovery no longer names the verified installed package")


def prepare_native_run(root: Path, run_root: Path, bundle_root: Path, executable: Path, *,
                       authorize_install: bool = False,
                       runner: Callable[..., Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Prepare once, before login. Failed preparations are retained, never retried."""
    _require(authorize_install is True, "explicit local-install authorization is required")
    protocol = _protocol(root)
    executable_identity = legacy.freeze_executable(executable, protocol["cli"]["sha256"])
    expected_package = package_identity(bundle_root)
    _require(expected_package == protocol["bundle"]["packageSha256"], "native package identity is not protocol-bound")
    _ordinary_directory(run_root.parent)
    _require(not run_root.exists() and not run_root.is_symlink(), "native test root already exists")
    _require(not run_root.is_relative_to(root.resolve()), "native test root must be repository-external")
    run_root.mkdir(mode=0o700)
    actual = runner is None
    invoke = bounded_process if runner is None else runner
    _exclusive(run_root / "preparation-started.json", _bytes({"protocolDigest": protocol["protocolDigest"]}))
    marketplace = run_root / "marketplace"
    (marketplace / ".agents/plugins").mkdir(parents=True)
    # The frozen client's local-source contract requires a normalized path
    # within this marketplace, not an absolute path to the build output.
    shutil.copytree(bundle_root, marketplace / "plugin")
    _require(package_identity(marketplace / "plugin") == expected_package,
             "marketplace copy differs from the verified bundle")
    _exclusive(marketplace / ".agents/plugins/marketplace.json", _bytes({
        "name": legacy.MARKETPLACE_NAME, "interface": {"displayName": "Axiom no-Hook observer"},
        "plugins": [{"name": legacy.PLUGIN_NAME,
                     "source": {"source": "local", "path": "./plugin"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                     "category": "Productivity"}],
    }))
    seed = legacy.create_materialization_seed()
    cases = legacy.load_golden_cases(root)
    fixtures = _input(root, protocol, "fixtureMatrix")
    model_schema = _input(root, protocol, "modelResponseSchema")
    envelope = _input(root, protocol, "promptEnvelope")
    prepared = []
    for ordinal, case in enumerate(cases, 1):
        paths = _case_paths(run_root, ordinal)
        for name in ("case", "home", "user", "workspace", "state", "tmp"):
            paths[name].mkdir(mode=0o700)
        for name in ("config", "cache", "data"):
            (paths["user"] / name).mkdir(mode=0o700)
        fixture = materialize_fixture(paths["workspace"], _definition(fixtures, ordinal))
        materialized = legacy.materialize_case_contract(
            materialization_seed=seed, ordinal=ordinal, protocol_digest=protocol["protocolDigest"],
            model_schema=model_schema, prompt_envelope=envelope, request=case["request"])
        _exclusive(paths["case"] / "response-schema.json", materialized.schema_bytes)
        if ordinal != 11:
            legacy.recheck_executable(executable_identity)
            receipt = _json(_successful(invoke(legacy.build_marketplace_add_argv(executable, marketplace),
                cwd=paths["workspace"], env=case_environment(paths)), "marketplace registration"))
            _require(receipt == {"marketplaceName": legacy.MARKETPLACE_NAME,
                                "installedRoot": str(marketplace), "alreadyAdded": False},
                     "marketplace receipt does not bind the selected local source")
            receipt = _json(_successful(invoke(legacy.build_plugin_add_argv(executable),
                cwd=paths["workspace"], env=case_environment(paths)), "plugin installation"))
            _require(set(receipt) == {"pluginId", "name", "marketplaceName", "version", "installedPath", "authPolicy"},
                     "plugin receipt is not closed")
            for key, expected in {"pluginId": legacy.PLUGIN_ID, "name": legacy.PLUGIN_NAME,
                                  "marketplaceName": legacy.MARKETPLACE_NAME,
                                  "version": legacy.PLUGIN_VERSION,
                                  "installedPath": str(paths["package"])}.items():
                _require(receipt[key] == expected, "plugin receipt differs from expected cache object")
            _require(receipt["authPolicy"] in {"ON_INSTALL", "ON_USE"}, "unknown plugin authentication policy")
            _require(package_identity(paths["package"]) == expected_package, "installed plugin differs from verified bundle")
            paths["discovery"].parent.mkdir(mode=0o700)
            paths["discovery"].symlink_to(paths["package"] / "skills", target_is_directory=True)
        _verify_config(paths, marketplace, ordinal != 11)
        _verify_discovery(paths, ordinal != 11)
        prepared.append({"ordinal": ordinal, "fixtureSha256": fixture,
                         "packageSha256": expected_package if ordinal != 11 else None})
    state = {"schemaVersion": "2", "protocolDigest": protocol["protocolDigest"],
             "runMode": "actual" if actual else "simulated", "executable": str(executable),
             "materializationSeed": seed.hex(), "cases": prepared}
    _exclusive(run_root / STATE_NAME, _bytes(state))
    return state


def _state(root: Path, run_root: Path, *, followup: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    _ordinary_directory(run_root)
    protocol = _protocol(root)
    state = _json(_read(run_root / "diagnostic-followup/preparation.json" if followup else run_root / STATE_NAME))
    _require(set(state) == {"schemaVersion", "protocolDigest", "runMode", "executable", "materializationSeed", "cases"},
             "native preparation record is not closed")
    _require(state["schemaVersion"] == "2" and state["protocolDigest"] == protocol["protocolDigest"],
             "prepared input identity changed")
    _require(state["runMode"] in {"actual", "simulated"}, "unknown preparation source")
    _require(type(state["cases"]) is list and len(state["cases"]) == 16, "incomplete preparation")
    for ordinal, item in enumerate(state["cases"], 1):
        _require(set(item) == {"ordinal", "fixtureSha256", "packageSha256"} and item["ordinal"] == ordinal,
                 "prepared case records are not canonical")
    _require(len(bytes.fromhex(state["materializationSeed"])) == 32, "invalid materialization seed")
    return protocol, state


def _verify_prior_attempt(run_root: Path) -> None:
    """Only the explicitly authorized, immutable first failure is retryable."""
    _require(hashlib.sha256(_read(run_root / "normalized-result.json")).hexdigest() ==
             HISTORICAL_RESULT_SHA256, "followup requires the original incomplete result")
    _require(_json(_read(run_root / "batch-started.json")) ==
             {"protocolDigest": HISTORICAL_PROTOCOL_DIGEST}, "historical batch marker changed")
    _require(_json(_read(run_root / "attempt-01.json")) == {
        "ordinal": 1, "caseId": legacy.EXPECTED_CASE_IDS[0],
        "protocolDigest": HISTORICAL_PROTOCOL_DIGEST}, "historical attempt marker changed")
    for ordinal in range(2, 17):
        path = run_root / f"attempt-{ordinal:02d}.json"
        _require(not path.exists() and not path.is_symlink(), "later case already consumed its attempt")


def prepare_diagnostic_followup(root: Path, run_root: Path) -> None:
    """Add an explicit second ledger; preserve prior preparation, auth and events."""
    _ordinary_directory(run_root)
    _verify_prior_attempt(run_root)
    protocol = _protocol(root)
    old = _json(_read(run_root / STATE_NAME))
    _require(old["protocolDigest"] == HISTORICAL_PROTOCOL_DIGEST and old["runMode"] == "actual",
             "followup preparation does not name the historical execution")
    prior = _json(_read(run_root / "normalized-result.json"))
    _require(old["materializationSeed"] == prior["materializationSeed"], "historical seed changed")
    legacy.freeze_executable(Path(old["executable"]), protocol["cli"]["sha256"])
    fixtures = _input(root, protocol, "fixtureMatrix")
    schema = _input(root, protocol, "modelResponseSchema")
    envelope = _input(root, protocol, "promptEnvelope")
    cases = legacy.load_golden_cases(root)
    prepared = []
    for ordinal, case in enumerate(cases, 1):
        paths = _case_paths(run_root, ordinal)
        _verify_config(paths, run_root / "marketplace", ordinal != 11)
        _verify_discovery(paths, ordinal != 11)
        fixture = fixture_identity(paths["workspace"], _definition(fixtures, ordinal))
        package = package_identity(paths["package"]) if ordinal != 11 else None
        _require(old["cases"][ordinal - 1] == {
            "ordinal": ordinal, "fixtureSha256": fixture, "packageSha256": package},
            "historical prepared inputs changed")
        _require(ordinal == 11 or package == protocol["bundle"]["packageSha256"], "followup package changed")
        previous = legacy.materialize_case_contract(materialization_seed=bytes.fromhex(old["materializationSeed"]),
            ordinal=ordinal, protocol_digest=HISTORICAL_PROTOCOL_DIGEST, model_schema=schema,
            prompt_envelope=envelope, request=case["request"])
        _require(_read(paths["case"] / "response-schema.json") == previous.schema_bytes,
                 "historical materialization changed")
        prepared.append(legacy.materialize_case_contract(materialization_seed=bytes.fromhex(old["materializationSeed"]),
            ordinal=ordinal, protocol_digest=protocol["protocolDigest"], model_schema=schema,
            prompt_envelope=envelope, request=case["request"]))
    ledger = run_root / "diagnostic-followup"
    ledger.mkdir(mode=0o700)  # exclusive; a partial migration is retained, not retried
    _exclusive(ledger / "migration.json", _bytes({"priorResultSha256": HISTORICAL_RESULT_SHA256,
        "priorProtocolDigest": HISTORICAL_PROTOCOL_DIGEST, "protocolDigest": protocol["protocolDigest"],
        "priorAttempts": 1, "maximumCumulativeAttempts": 17}))
    for ordinal, material in enumerate(prepared, 1):
        _exclusive(ledger / f"response-schema-{ordinal:02d}.json", material.schema_bytes)
    _exclusive(ledger / "preparation.json", _bytes({**old, "protocolDigest": protocol["protocolDigest"]}))



def _auth_metadata(descriptor: int) -> dict[str, int]:
    metadata = os.fstat(descriptor)
    _require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid() and
             stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_nlink == 1,
             "test authentication must be a single-link private regular file")
    return {"device": metadata.st_dev, "inode": metadata.st_ino}


def _auth_owner(run_root: Path, ordinal: int) -> Path:
    return run_root / f"test-auth-owner-{ordinal:02d}.json"


def _open_test_auth(run_root: Path, ordinal: int, flags: int) -> int:
    _require(type(ordinal) is int and 1 <= ordinal <= CASE_COUNT, "invalid test-auth case")
    home = _ordinary_directory(_case_paths(run_root, ordinal)["home"])
    descriptor = os.open(home / AUTH_FILE_NAME, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        identity = _auth_metadata(descriptor)
        owner = _json(_read(_auth_owner(run_root, ordinal)))
        _require(owner == {"ordinal": ordinal, **identity}, "test-auth object ownership changed")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _copy_test_auth(run_root: Path, source_ordinal: int, target_ordinal: int, *, create: bool) -> None:
    """Copy only the official credential file; bytes never enter any report/hash/parser.

    Supported only without concurrent operators/clients. The frozen client writes
    this file in place. After abnormal client termination the batch stops, so no
    subsequent case receives a possibly partial refresh.
    """
    _require(source_ordinal != target_ordinal and 2 <= target_ordinal <= CASE_COUNT,
             "invalid test-auth handoff")
    source = _open_test_auth(run_root, source_ordinal, os.O_RDONLY)
    target = None
    try:
        if create:
            home = _ordinary_directory(_case_paths(run_root, target_ordinal)["home"])
            target = os.open(home / AUTH_FILE_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            # Registration failure preserves the newly created file; it is never
            # silently retried or mistaken for a caller-owned object.
            _exclusive(_auth_owner(run_root, target_ordinal),
                       _bytes({"ordinal": target_ordinal, **_auth_metadata(target)}))
        else:
            target = _open_test_auth(run_root, target_ordinal, os.O_WRONLY)
            os.ftruncate(target, 0)
        with os.fdopen(os.dup(source), "rb") as reader, os.fdopen(os.dup(target), "wb") as writer:
            shutil.copyfileobj(reader, writer, length=64 * 1024)
            writer.flush()
        os.fsync(target)
    finally:
        os.close(source)
        if target is not None:
            os.close(target)


def share_test_authentication(root: Path, run_root: Path, *, authorize_copy: bool = False,
                              preserve_existing: Sequence[int] = ()) -> None:
    """An explicit one-time copy from the registered Case 1 test login only."""
    _require(authorize_copy is True, "explicit test-auth copy authorization is required")
    protocol, _ = _state(root, run_root)
    _require(not (run_root / AUTH_COPY_STATE).exists(), "test-auth copy state already exists")
    _require(not (run_root / "batch-started.json").exists() and all(
        not (run_root / f"attempt-{i:02d}.json").exists() for i in range(1, 17)),
        "test-auth preparation cannot reset an attempted batch")
    _require(len(set(preserve_existing)) == len(preserve_existing) and all(
        type(i) is int and 2 <= i <= CASE_COUNT for i in preserve_existing),
        "invalid explicitly retained test-auth set")
    retained = {}
    for ordinal in range(1, 17):
        paths = _case_paths(run_root, ordinal)
        home = _ordinary_directory(paths["home"])
        _require(not _auth_owner(run_root, ordinal).exists(), "test-auth ownership already registered")
        if ordinal != 1:
            destination = home / AUTH_FILE_NAME
            if ordinal in preserve_existing:
                backup = paths["case"] / "retained-auth-before-reuse"
                _require(not backup.exists() and not backup.is_symlink(), "test-auth retention destination exists")
                descriptor = os.open(destination, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                try:
                    retained[ordinal] = _auth_metadata(descriptor)
                finally:
                    os.close(descriptor)
            else:
                _require(not destination.exists() and not destination.is_symlink(),
                         "refusing to overwrite an unowned test-auth destination")
    # Only explicitly identified test logins are moved, without reading their
    # contents. They remain private and are never used as a refresh source.
    for ordinal, identity in retained.items():
        paths = _case_paths(run_root, ordinal)
        backup = paths["case"] / "retained-auth-before-reuse"
        backup.mkdir(mode=0o700)
        os.rename(paths["home"] / AUTH_FILE_NAME, backup / AUTH_FILE_NAME)
        descriptor = os.open(backup / AUTH_FILE_NAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            _require(_auth_metadata(descriptor) == identity, "retained test-auth object changed")
        finally:
            os.close(descriptor)
        _exclusive(backup / "ownership.json", _bytes({"ordinal": ordinal, **identity}))
    source = os.open(_case_paths(run_root, 1)["home"] / AUTH_FILE_NAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        _exclusive(_auth_owner(run_root, 1), _bytes({"ordinal": 1, **_auth_metadata(source)}))
    finally:
        os.close(source)
    for ordinal in range(2, 17):
        _copy_test_auth(run_root, 1, ordinal, create=True)
    _exclusive(run_root / AUTH_COPY_STATE, _bytes({
        "protocolDigest": protocol["protocolDigest"], "sourceOrdinal": 1, "copiedOrdinals": list(range(2, 17)),
    }))


def _require_test_auth_copy_state(run_root: Path, protocol: Mapping[str, Any]) -> None:
    _require(_json(_read(run_root / AUTH_COPY_STATE)) == {
        "protocolDigest": protocol["protocolDigest"], "sourceOrdinal": 1, "copiedOrdinals": list(range(2, 17)),
    }, "test-auth copy preparation is incomplete or stale")


def login_commands(root: Path, run_root: Path) -> list[dict[str, Any]]:
    """Return commands for an attended terminal; never start or inspect login."""
    _, state = _state(root, run_root)
    executable = Path(state["executable"])
    legacy.freeze_executable(executable, legacy.CODEX_BINARY_SHA256)
    commands = []
    for ordinal in range(1, 17):
        paths = _case_paths(run_root, ordinal)
        commands.append({"ordinal": ordinal, "cwd": str(paths["workspace"]),
                         "env": case_environment(paths), "argv": [str(executable), "-c",
                         'cli_auth_credentials_store="file"', "-c",
                         f'log_dir={json.dumps(str(paths["state"]))}', "login"],
                         "completion": "Official login status: Logged in using ChatGPT"})
    return commands


def _read_command(command: str, readable: Mapping[str, bytes], cwd: Path) -> bytes:
    """Recognize a finite source-visible read grammar, with exact output bytes."""
    words = shlex.split(command)
    if len(words) == 3 and Path(words[0]).name in {"bash", "sh"} and words[1] in {"-c", "-lc"}:
        words = shlex.split(words[2])
    _require(bool(words), "empty shell action")
    _require(not any(char in " ".join(words) for char in "\n\r;&|<>`$"), "unsupported shell grammar")
    name = Path(words[0]).name
    if name == "cat" and len(words) in {2, 3}:
        _require(len(words) == 2 or words[1] == "--", "unsupported cat option")
        selected = words[-1]
        bounds = None
    elif name == "sed" and len(words) == 4 and words[1] == "-n":
        import re
        match = re.fullmatch(r"([1-9][0-9]*),([1-9][0-9]*)p", words[2])
        _require(match is not None, "unsupported sed range")
        bounds = (int(match[1]), int(match[2]))
        _require(bounds[0] <= bounds[1] <= 100000, "invalid sed range")
        selected = words[3]
    else:
        raise NativeObservationError("unrecognized native shell action")
    path = Path(selected)
    if not path.is_absolute():
        path = cwd / path
    _require(".." not in path.parts and str(path) in readable, "shell read is outside bound public files")
    data = readable[str(path)]
    if bounds is not None:
        data = b"".join(data.splitlines(keepends=True)[bounds[0] - 1:bounds[1]])
    return data


def inspect_native_event(raw: bytes, readable: Mapping[str, bytes], cwd: Path) -> None:
    event = legacy._parse_json_line(raw)
    kind = event.get("type")
    _require(kind in EVENT_TYPES[:-1], "unknown native event")
    if kind == "error":
        _require(set(event) == {"type", "message"} and type(event["message"]) is str,
                 "invalid native error event")
        return
    if kind == "turn.failed":
        _require(set(event) == {"type", "error"} and type(event["error"]) is dict and
                 set(event["error"]) == {"message"} and type(event["error"]["message"]) is str,
                 "invalid native failed-turn event")
        return
    if kind.startswith("item."):
        item = event.get("item")
        _require(type(item) is dict, "native item missing")
        item_type = item.get("type")
        _require(item_type in {"reasoning", "agent_message", "command_execution"}, "unsupported native action")
        legacy._validate_item_payload(item, item_type)
        if item_type == "command_execution":
            expected = _read_command(item["command"], readable, cwd)
            if kind == "item.completed":
                _require(item["status"] == "completed" and item["exit_code"] == 0,
                         "native read command did not complete")
                _require(item["aggregated_output"].encode("utf-8") == expected,
                         "native read output differs from bound source")
            else:
                _require(item["status"] == "in_progress" and item["exit_code"] is None,
                         "native read lifecycle state mismatch")
                _require(expected.startswith(item["aggregated_output"].encode("utf-8")),
                         "native partial read output differs from bound source")


def _observe_line(raw: bytes, readable: Mapping[str, bytes], cwd: Path, facts: dict[str, Any]) -> None:
    facts["eventCount"] += 1
    try:
        event = legacy._parse_json_line(raw)
    except (ValueError, NativeObservationError):
        _first_failure(facts, "event", "event-invalid")
        raise NativeDiagnosticError(facts) from None
    kind = event.get("type")
    retained = kind if kind in EVENT_TYPES[:-1] else "unknown"
    if retained not in facts["eventTypes"]:
        facts["eventTypes"].append(retained)
    item = event.get("item")
    item_type = item.get("type") if type(item) is dict else None
    if type(kind) is str and kind.startswith("item."):
        retained_item = item_type if type(item_type) is str and item_type in {"reasoning", "agent_message", "command_execution", "error"} else "unsupported"
        if retained_item not in facts["itemTypes"]:
            facts["itemTypes"].append(retained_item)
    if facts["eventCount"] > legacy.MAX_EVENT_COUNT:
        _first_failure(facts, "event", "output-limit")
        raise NativeDiagnosticError(facts)
    try:
        inspect_native_event(raw, readable, cwd)
    except (ValueError, KeyError, TypeError, NativeObservationError):
        if facts["policyReason"] == "none":
            facts["policyReason"] = ("unknown-event" if retained == "unknown" else
                "read-contract-rejected" if item_type == "command_execution" else
                "unsupported-item" if type(kind) is str and kind.startswith("item.") and
                (type(item_type) is not str or item_type not in {"reasoning", "agent_message"}) else "event-shape-rejected")
        _first_failure(facts, "event", "policy-rejected")
        raise NativeDiagnosticError(facts) from None
    if kind == "turn.failed":
        _first_failure(facts, "event", "host-failure")
    # Top-level error loses upstream will_retry; it alone is not terminal.


def parse_native_jsonl(data: bytes, taxonomy: Mapping[str, Any], readable: Mapping[str, bytes],
                       cwd: Path) -> tuple[legacy.StreamFacts, int]:
    """Validate native commands, then reuse v1's strict non-tool stream closure."""
    _require(len(data) <= legacy.MAX_STDOUT_BYTES and data.endswith(b"\n") and b"\r" not in data,
             "native JSONL framing or size mismatch")
    lines = data.splitlines()
    _require(len(lines) <= legacy.MAX_EVENT_COUNT, "native event count exceeds limit")
    commands: dict[str, str] = {}
    completed: set[str] = set()
    translated: list[bytes] = []
    turn_started = False
    terminal_seen = False
    for raw in lines:
        _require(not terminal_seen, "native event appeared after terminal")
        inspect_native_event(raw, readable, cwd)
        event = legacy._parse_json_line(raw)
        if event["type"] == "turn.started":
            turn_started = True
        if event["type"] in {"turn.completed", "turn.failed"}:
            terminal_seen = True
        if event["type"] == "error":
            _require(turn_started, "native error appeared outside a turn")
            # Frozen JSONL does not expose retry disposition. Keep its type in
            # diagnostics while the final exit and complete stream decide status.
            continue
        item = event.get("item", {})
        if item.get("type") == "command_execution":
            identifier = item["id"]
            kind = event["type"]
            if kind == "item.started":
                _require(identifier not in commands and identifier not in completed, "duplicate native command")
                commands[identifier] = item["command"]
                continue
            _require(identifier in commands and commands[identifier] == item["command"], "native command lacks matching start")
            if kind == "item.updated":
                continue
            _require(identifier not in completed, "duplicate native command completion")
            completed.add(identifier)
            # The original identifier is retained: v1 checks canonical item order.
            event = {"type": "item.completed", "item": {"id": identifier, "type": "reasoning", "text": ""}}
        if event["type"] == "turn.completed":
            _require(set(commands) == completed, "terminal outcome left an active native command")
        translated.append(legacy._canonical_json(event) + b"\n")
    return legacy.parse_jsonl(b"".join(translated), taxonomy), len(completed)


def _readable(paths: Mapping[str, Path], definition: Mapping[str, Any], installed: bool) -> dict[str, bytes]:
    result = {str(paths["workspace"] / item["path"]): item["contentUtf8"].encode("utf-8")
              for item in definition["files"]}
    if installed:
        # Enumerate only the verified immutable public package, not CODEX_HOME.
        for relative, _, _, _ in legacy.snapshot_tree(paths["package"]):
            result[str(paths["package"] / relative)] = _read(paths["package"] / relative)
    return result


def _blank_case(case: Mapping[str, Any], materialized: legacy.CaseMaterialization,
                seed: bytes, protocol: Mapping[str, Any], definition: Mapping[str, Any]) -> dict[str, Any]:
    fields = legacy._case_materialization_fields(
        materialization=materialized, materialization_seed=seed, protocol_digest=protocol["protocolDigest"],
        case=case, realized_fixture_digest=legacy._expected_realized_fixture_digest(definition),
        realized_file_set_digest=definition["canonicalFileSetDigest"], prompt_fully_delivered=True)
    return {"ordinal": materialized.ordinal, "caseId": case["id"], "status": "NOT-RUN",
            "diagnostic": "not-run", "cliLaunchCount": 0, "attemptCount": 0, "modelRequestCount": None,
            "executionDiagnostics": _diagnostics(),
            "installation": "not-checked", "authentication": "not-checked",
            "fixtureBeforeSha256": None, "fixtureAfterSha256": None,
            "packageBeforeSha256": None, "packageAfterSha256": None,
            "readonlyCommandCount": 0, "observed": None, "terminal": "not-observed", **fields,
            "opaqueBindingSha256": materialized.opaque_binding_sha256}


def run_native_observation(root: Path, run_root: Path, *, authorize_model_calls: bool = False,
                           reuse_test_auth: bool = False, followup: bool = False,
                           process_runner: Callable[..., Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """One foreground batch; exclusive markers consume each case before spawn."""
    _require(authorize_model_calls is True, "explicit model-call authorization is required")
    protocol, state = _state(root, run_root, followup=followup)
    ledger = run_root / "diagnostic-followup" if followup else run_root
    if followup:
        _verify_prior_attempt(run_root)
    executable = Path(state["executable"])
    frozen = legacy.freeze_executable(executable, protocol["cli"]["sha256"])
    actual = process_runner is None and state["runMode"] == "actual"
    invoke = bounded_process if process_runner is None else process_runner
    cases = legacy.load_golden_cases(root)
    fixtures = _input(root, protocol, "fixtureMatrix")
    schema = _input(root, protocol, "modelResponseSchema")
    envelope = _input(root, protocol, "promptEnvelope")
    taxonomy = _input(root, protocol, "taxonomy")
    seed = bytes.fromhex(state["materializationSeed"])
    materials = [legacy.materialize_case_contract(materialization_seed=seed, ordinal=i,
        protocol_digest=protocol["protocolDigest"], model_schema=schema,
        prompt_envelope=envelope, request=case["request"]) for i, case in enumerate(cases, 1)]
    results = [_blank_case(case, material, seed, protocol, _definition(fixtures, i))
               for i, (case, material) in enumerate(zip(cases, materials), 1)]
    if reuse_test_auth:
        _require_test_auth_copy_state(run_root, {"protocolDigest": HISTORICAL_PROTOCOL_DIGEST} if followup else protocol)
    _exclusive(ledger / "batch-started.json", _bytes({"protocolDigest": protocol["protocolDigest"]}))
    for ordinal, (case, material, record) in enumerate(zip(cases, materials, results), 1):
        paths = _case_paths(run_root, ordinal)
        definition = _definition(fixtures, ordinal)
        installed = ordinal != 11
        diagnostic = "input-changed"
        phase = "precheck"
        events = _diagnostics()
        try:
            legacy.recheck_executable(frozen)
            _ordinary_directory(paths["workspace"])
            _ordinary_directory(paths["home"])
            _verify_config(paths, run_root / "marketplace", installed)
            _verify_discovery(paths, installed)
            record["fixtureBeforeSha256"] = fixture_identity(paths["workspace"], definition)
            _require(record["fixtureBeforeSha256"] == state["cases"][ordinal - 1]["fixtureSha256"], "prepared fixture changed")
            if installed:
                record["packageBeforeSha256"] = package_identity(paths["package"])
                _require(record["packageBeforeSha256"] == state["cases"][ordinal - 1]["packageSha256"] ==
                         protocol["bundle"]["packageSha256"], "prepared plugin changed")
            record["installation"] = "verified" if installed else "absent"
            _require(_read((ledger / f"response-schema-{ordinal:02d}.json") if followup else
                           paths["case"] / "response-schema.json") == material.schema_bytes,
                     "prepared response schema changed")
            diagnostic = "authentication-unavailable"
            phase = "login"
            if reuse_test_auth and ordinal > 1:
                # The prior iteration only advances after normal exit and closed
                # output/input validation. Never refill from the initial stale copy.
                _copy_test_auth(run_root, ordinal - 1, ordinal, create=False)
            if reuse_test_auth:
                # Validate Case 1 as well as copied destinations before handing
                # the path to the official client; never inspect credential bytes.
                descriptor = _open_test_auth(run_root, ordinal, os.O_RDONLY)
                os.close(descriptor)
            login = invoke([str(executable), "-c", 'cli_auth_credentials_store="file"', "login", "status"],
                           cwd=paths["workspace"], env=case_environment(paths))
            combined = login["stdout"] + login["stderr"]
            _require(login["returncode"] == 0 and combined.strip() == b"Logged in using ChatGPT",
                     "official client did not confirm test ChatGPT login")
            record["authentication"] = "chatgpt"
            readable = _readable(paths, definition, installed)
            diagnostic = "already-attempted"
            _exclusive(ledger / f"attempt-{ordinal:02d}.json", _bytes({
                "ordinal": ordinal, "caseId": case["id"], "protocolDigest": protocol["protocolDigest"]}))
            # The marker consumes budget even if spawn fails. CLI launch count
            # is separately recorded only once Popen has created the process.
            record["attemptCount"] = 1
            diagnostic = "execution-failed"
            phase = "launch"
            argv = build_native_argv(executable, run_root, ordinal)
            if followup:
                argv[argv.index("--output-schema") + 1] = str(ledger / f"response-schema-{ordinal:02d}.json")
            capture = invoke(argv, cwd=paths["workspace"],
                             env=case_environment(paths), stdin=material.prompt_bytes,
                             started_callback=lambda: record.__setitem__("cliLaunchCount", 1),
                             line_callback=lambda raw: _observe_line(raw, readable, paths["workspace"], events))
            _require(record["cliLaunchCount"] == 1, "client runner did not report a created process")
            facts = _capture_facts(capture)
            facts.update(eventCount=events["eventCount"], eventTypes=events["eventTypes"],
                         itemTypes=events["itemTypes"], policyReason=events["policyReason"])
            if events["category"] != "none":
                facts.update(phase=events["phase"], category=events["category"])
            record["executionDiagnostics"] = facts
            if "turn.failed" in events["eventTypes"]:
                record["terminal"] = "turn.failed"
            if facts["category"] != "none":
                raise NativeDiagnosticError(facts)
            diagnostic = "stream-invalid"
            phase = "stream"
            stream, count = parse_native_jsonl(capture["stdout"], taxonomy, readable, paths["workspace"])
            record["readonlyCommandCount"] = count
            record["terminal"] = stream.terminal_type
            phase = "response"
            observed = dict(stream.structured_result)
            materialized_schema = _json(material.schema_bytes)
            legacy._validate_schema_value(observed, materialized_schema, materialized_schema,
                                          "native structured response")
            record["observed"] = {key: value for key, value in observed.items() if key != "opaqueCaseBinding"}
            failures = legacy.validate_model_response(observed, case, material.token, schema)
            diagnostic = "input-changed"
            phase = "postcheck"
            record["fixtureAfterSha256"] = fixture_identity(paths["workspace"], definition)
            if installed:
                record["packageAfterSha256"] = package_identity(paths["package"])
            _require(record["fixtureAfterSha256"] == record["fixtureBeforeSha256"] and
                     record["packageAfterSha256"] == record["packageBeforeSha256"], "consumed inputs changed")
            _verify_config(paths, run_root / "marketplace", installed)
            _verify_discovery(paths, installed)
            record["status"] = "FAIL" if failures else "PASS"
            record["diagnostic"] = "semantic-mismatch" if failures else "none"
        except (OSError, ValueError, KeyError, NativeObservationError, subprocess.SubprocessError) as error:
            record["status"] = "INCOMPLETE"
            facts = dict(error.facts) if isinstance(error, NativeDiagnosticError) else dict(record["executionDiagnostics"])
            facts.update(eventCount=events["eventCount"], eventTypes=events["eventTypes"],
                         itemTypes=events["itemTypes"], policyReason=events["policyReason"])
            if events["category"] != "none":
                facts.update(phase=events["phase"], category=events["category"])
            _first_failure(facts, phase, "response-invalid" if phase == "response" else diagnostic)
            record["executionDiagnostics"] = facts
            record["diagnostic"] = facts["category"]
            if "turn.failed" in events["eventTypes"]:
                record["terminal"] = "turn.failed"
            if diagnostic == "authentication-unavailable":
                record["authentication"] = "unavailable"
                facts.update(phase="login", inputBytesSent=0, inputFullyDelivered=None)
            # Raw exceptions may contain private paths or output; do not retain them.
            del error
            break
    statuses = [item["status"] for item in results]
    status = "INCOMPLETE" if not actual or any(value in {"NOT-RUN", "INCOMPLETE"} for value in statuses) else (
        "FAIL" if "FAIL" in statuses else "PASS")
    result = {"schemaVersion": "2", "diagnosticRevision": 1, "protocolId": PROTOCOL_ID,
              "priorResultSha256": HISTORICAL_RESULT_SHA256 if followup else None,
              "attemptCount": sum(item["attemptCount"] for item in results),
              "cumulativeAttemptCount": int(followup) + sum(item["attemptCount"] for item in results),
              "discoveryMechanism": DISCOVERY_MECHANISM, "pluginRuntimeEnabled": False,
              "authenticationMode": "serial-test-auth-copy" if reuse_test_auth else "independent-official-login",
              "protocolDigest": protocol["protocolDigest"], "runMode": "actual" if actual else "simulated",
              "hostClaim": actual and status == "PASS", "status": status,
              "materializationSeed": seed.hex(), "cliLaunchCount": sum(item["cliLaunchCount"] for item in results),
              "modelRequestCount": None, "caseResults": results,
              "materializationCommitmentRoot": legacy._materialization_commitment_root(
                  [item["materializationCommitmentSha256"] for item in results]),
              "cleanup": "retained-test-state", "descendantClosure": "not-observed"}
    failures = validate_native_result(result, root)
    _require(not failures, "native normalized result failed semantic validation")
    _exclusive(ledger / "normalized-result.json", _bytes(result))
    return result


def _validate_native_schema(value: Any, node: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    """Add real union validation to the reused closed-schema subset."""
    if "anyOf" in node:
        matched = False
        for branch in node["anyOf"]:
            try:
                _validate_native_schema(value, branch, schema)
                matched = True
                break
            except NativeObservationError:
                continue
        _require(matched, "native value does not match any closed union member")
        return
    if "$ref" in node:
        reference = node["$ref"]
        _require(reference.startswith("#/$defs/"), "unsupported native schema reference")
        _validate_native_schema(value, schema["$defs"][reference.removeprefix("#/$defs/")], schema)
        return
    legacy._validate_schema_value(value, node, schema, "native result")
    if type(value) is dict:
        for key, child in value.items():
            if key in node.get("properties", {}):
                _validate_native_schema(child, node["properties"][key], schema)
    elif type(value) is list and "items" in node:
        for child in value:
            _validate_native_schema(child, node["items"], schema)


def validate_native_result(document: Any, root: Path = REPOSITORY_ROOT) -> list[str]:
    """Check retained evidence consistency, not authenticity of an editable file."""
    try:
        protocol = _protocol(root)
        result_schema = _json(_read(root / RESULT_SCHEMA_RELATIVE))
        _validate_native_schema(document, result_schema, result_schema)
        _require(document["protocolDigest"] == protocol["protocolDigest"], "native result protocol mismatch")
        prior_count = 1 if document["priorResultSha256"] == HISTORICAL_RESULT_SHA256 else 0
        _require(document["attemptCount"] == sum(item["attemptCount"] for item in document["caseResults"]),
                 "native attempt count mismatch")
        _require(document["cumulativeAttemptCount"] == prior_count + document["attemptCount"] <= 17,
                 "native cumulative attempt budget mismatch")
        cases = legacy.load_golden_cases(root)
        fixtures = _input(root, protocol, "fixtureMatrix")
        model_schema = _input(root, protocol, "modelResponseSchema")
        envelope = _input(root, protocol, "promptEnvelope")
        seed = bytes.fromhex(document["materializationSeed"])
        stopped = False
        for ordinal, (case, record) in enumerate(zip(cases, document["caseResults"]), 1):
            _require(record["ordinal"] == ordinal and record["caseId"] == case["id"], "native result case order mismatch")
            definition = _definition(fixtures, ordinal)
            material = legacy.materialize_case_contract(materialization_seed=seed, ordinal=ordinal,
                protocol_digest=protocol["protocolDigest"], model_schema=model_schema,
                prompt_envelope=envelope, request=case["request"])
            expected = _blank_case(case, material, seed, protocol, definition)
            for field in ("opaqueBindingSha256", "modelResponseSchemaSha256", "casePromptSha256", "materializationCommitmentSha256"):
                _require(record[field] == expected[field], "native materialization binding mismatch")
            status = record["status"]
            if stopped:
                _require(status == "NOT-RUN", "native result continued after unreliable failure")
            if status == "NOT-RUN":
                _require(record == expected, "unstarted native case carries observed facts")
                stopped = True
                continue
            facts = record["executionDiagnostics"]
            _require(record["cliLaunchCount"] <= record["attemptCount"], "launch lacks consumed attempt")
            _require(facts["eventCount"] >= len(facts["eventTypes"]), "event summary count mismatch")
            _require(not facts["itemTypes"] or (any(kind.startswith("item.") for kind in facts["eventTypes"]) and
                     len(facts["itemTypes"]) <= facts["eventCount"]), "item summary lacks matching events")
            _require(facts["inputBytesSent"] <= len(material.prompt_bytes), "input count exceeds prompt")
            if record["attemptCount"]:
                if facts["inputFullyDelivered"] is True:
                    _require(facts["inputBytesSent"] == len(material.prompt_bytes), "complete input count mismatch")
                elif facts["inputFullyDelivered"] is False:
                    _require(facts["inputBytesSent"] < len(material.prompt_bytes), "incomplete input count mismatch")
            _require(facts["signal"] == (-facts["returnCode"] if facts["returnCode"] is not None and
                     facts["returnCode"] < 0 else None), "signal and return code disagree")
            if facts["timedOut"]:
                _require(facts["category"] != "none", "timeout cannot succeed")
            if facts["cleanupFailed"]:
                _require(status == "INCOMPLETE" and facts["category"] != "none", "cleanup failure cannot complete")
            if status == "INCOMPLETE":
                _require(facts["category"] == record["diagnostic"] and facts["category"] != "none",
                         "incomplete diagnostic differs from first cause")
                stopped = True
                _require(record["diagnostic"] not in {"none", "not-run", "semantic-mismatch"}, "incomplete case lacks cause")
            for field in ("fixtureBeforeSha256", "fixtureAfterSha256"):
                if record[field] is not None:
                    _require(record[field] == legacy._expected_realized_fixture_digest(definition), "native fixture record mismatch")
            if ordinal == 11:
                _require(record["installation"] in {"absent", "not-checked"} and
                         record["packageBeforeSha256"] is None and record["packageAfterSha256"] is None,
                         "no-plugin control claimed an installation")
            else:
                for field in ("packageBeforeSha256", "packageAfterSha256"):
                    if record[field] is not None:
                        _require(record[field] == protocol["bundle"]["packageSha256"],
                                 "native package record is not bound to the verified bundle")
            if record["cliLaunchCount"]:
                _require(record["authentication"] == "chatgpt" and
                         record["installation"] == ("absent" if ordinal == 11 else "verified") and
                         record["fixtureBeforeSha256"] is not None and
                         (ordinal == 11 or record["packageBeforeSha256"] is not None),
                         "native launch lacks verified prerequisites")
            if status in {"PASS", "FAIL"}:
                _require(facts["category"] == "none" and facts["returnCode"] == 0 and
                         facts["policyReason"] == "none" and
                         set(facts["itemTypes"]) <= {"reasoning", "agent_message", "command_execution"} and
                         facts["inputFullyDelivered"] is True and not facts["observerTerminated"] and
                         facts["stderrClassification"] in {"empty", "known-nonfatal"} and
                         "turn.completed" in facts["eventTypes"] and "turn.failed" not in facts["eventTypes"] and
                         "unknown" not in facts["eventTypes"], "completed case lacks successful execution facts")
                _require(record["cliLaunchCount"] == 1 and record["authentication"] == "chatgpt" and
                         record["installation"] == ("absent" if ordinal == 11 else "verified") and
                         record["terminal"] == "turn.completed", "completed native case lacks required evidence")
                _require(record["fixtureBeforeSha256"] is not None and
                         record["fixtureBeforeSha256"] == record["fixtureAfterSha256"], "completed case lacks stable fixture")
                if ordinal != 11:
                    _require(record["packageBeforeSha256"] is not None and
                             record["packageBeforeSha256"] == record["packageAfterSha256"], "completed case lacks stable package")
                response = dict(record["observed"])
                response["opaqueCaseBinding"] = material.token
                mismatches = legacy.validate_model_response(response, case, material.token, model_schema)
                _require((status == "PASS") == (not mismatches), "native semantic outcome differs from frozen case")
                _require(record["diagnostic"] == ("none" if status == "PASS" else "semantic-mismatch"), "native outcome diagnostic mismatch")
            if record["cliLaunchCount"] == 0:
                _require(record["observed"] is None and record["terminal"] == "not-observed" and
                         record["readonlyCommandCount"] == 0, "unlaunched case has model observations")
        _require(document["cliLaunchCount"] == sum(item["cliLaunchCount"] for item in document["caseResults"]),
                 "native launch count mismatch")
        _require(document["materializationCommitmentRoot"] == legacy._materialization_commitment_root(
            [item["materializationCommitmentSha256"] for item in document["caseResults"]]), "native commitment root mismatch")
        statuses = [item["status"] for item in document["caseResults"]]
        expected_status = "INCOMPLETE" if document["runMode"] == "simulated" or any(
            value in {"NOT-RUN", "INCOMPLETE"} for value in statuses) else ("FAIL" if "FAIL" in statuses else "PASS")
        _require(document["status"] == expected_status, "native overall status mismatch")
        _require(document["hostClaim"] == (document["runMode"] == "actual" and expected_status == "PASS"),
                 "simulated or incomplete result cannot claim host PASS")
        return []
    except (OSError, ValueError, KeyError, TypeError, NativeObservationError) as error:
        return [str(error)]


def main(argv: Sequence[str] | None = None, *, root: Path = REPOSITORY_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--login-commands", action="store_true")
    group.add_argument("--share-test-auth", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--prepare-diagnostic-followup", action="store_true")
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--bundle-root", type=Path)
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--authorize-local-install", action="store_true")
    parser.add_argument("--authorize-model-calls", action="store_true")
    parser.add_argument("--authorize-test-auth-copy", action="store_true")
    parser.add_argument("--reuse-test-auth", action="store_true")
    parser.add_argument("--diagnostic-followup", action="store_true")
    parser.add_argument("--preserve-existing-test-auth", type=int, nargs="*", default=[])
    args = parser.parse_args(argv)
    try:
        if args.prepare_diagnostic_followup:
            _require(args.run_root is not None, "followup requires the existing test root")
            prepare_diagnostic_followup(root, args.run_root)
            print("Diagnostic followup prepared; historical state preserved; no client started.")
        elif args.prepare:
            _require(all(value is not None for value in (args.run_root, args.bundle_root, args.codex)),
                     "prepare requires explicit run root, bundle and CLI")
            prepare_native_run(root, args.run_root, args.bundle_root, args.codex,
                               authorize_install=args.authorize_local_install)
            print("Native preparation complete; no login or model request performed.")
        elif args.share_test_auth:
            _require(args.run_root is not None, "test-auth copy requires a prepared run root")
            share_test_authentication(root, args.run_root, authorize_copy=args.authorize_test_auth_copy,
                                      preserve_existing=args.preserve_existing_test_auth)
            print("Test authentication copied to registered homes; no content reported; no model started.")
        elif args.login_commands:
            _require(args.run_root is not None, "login commands require a prepared run root")
            print(json.dumps(login_commands(root, args.run_root), indent=2))
        elif args.run:
            _require(args.run_root is not None, "run requires a prepared run root")
            result = run_native_observation(root, args.run_root, authorize_model_calls=args.authorize_model_calls,
                                            reuse_test_auth=args.reuse_test_auth, followup=args.diagnostic_followup)
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "PASS" else 1
        else:
            failures = validate_native_protocol(root)
            if failures:
                print("\n".join(failures), file=sys.stderr)
                return 1
            print("Native observation protocol: PASS (static only; no client started).")
        return 0
    except (OSError, ValueError, KeyError, NativeObservationError) as error:
        print(f"Native observation incomplete: {error}", file=sys.stderr)
        return 1
