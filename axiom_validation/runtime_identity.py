"""Deterministic installed-runtime identity and repository-policy revision checks."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

from .context import REPOSITORY_ROOT, release_version
from .release_versions import parse_production_release_version


INPUT_MANIFEST_RELATIVE = "axiom_validation/runtime-contract-inputs-v1.json"
IDENTITY_RELATIVE = "evidence/runtime-identity.json"
HISTORY_RELATIVE = "evidence/runtime-contract-history-v1.json"
POLICY_REVISIONS_RELATIVE = "evidence/repository-policy-revisions-v1.json"
README_RELATIVE = "README.md"
RUNTIME_IDENTITY_SURFACES = (README_RELATIVE,)
RUNTIME_IDENTITY_START = "<!-- runtime-identity:current:start -->"
RUNTIME_IDENTITY_END = "<!-- runtime-identity:current:end -->"

MAX_JSON_BYTES = 512 * 1024
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
WINDOWS_RESERVED_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)


class DuplicateJsonKeyError(ValueError):
    """Raised when a protected JSON document repeats a key."""


@dataclass(frozen=True)
class RuntimeContract:
    """The canonical runtime-contract payload and its identity."""

    digest: str
    record_count: int
    payload: bytes


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _path_label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def load_json_document(
    path: Path,
    failures: list[str],
    *,
    root: Path = REPOSITORY_ROOT,
) -> dict[str, Any] | None:
    """Load one bounded regular JSON object with duplicate-key rejection."""
    label = _path_label(path, root)
    try:
        metadata = path.lstat()
    except OSError as error:
        failures.append(f"cannot inspect {label}: {error}")
        return None
    if stat.S_ISLNK(metadata.st_mode):
        failures.append(f"{label} must not be a symbolic link")
        return None
    if not stat.S_ISREG(metadata.st_mode):
        failures.append(f"{label} must be a regular file")
        return None
    if metadata.st_size > MAX_JSON_BYTES:
        failures.append(f"{label} exceeds the {MAX_JSON_BYTES}-byte JSON limit")
        return None
    try:
        text = path.read_text(encoding="utf-8")
        document = json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKeyError) as error:
        failures.append(f"invalid JSON in {label}: {error}")
        return None
    if type(document) is not dict:
        failures.append(f"{label} must contain a top-level object")
        return None
    return document


def _exact_object(
    value: Any,
    expected_keys: set[str] | frozenset[str],
    label: str,
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    missing = sorted(set(expected_keys) - set(value))
    unknown = sorted(set(value) - set(expected_keys))
    if missing:
        failures.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{label} contains unknown fields: {', '.join(unknown)}")
    return value


def _nonempty_string(value: Any, label: str, failures: list[str]) -> str | None:
    if type(value) is not str or not value:
        failures.append(f"{label} must be a non-empty string")
        return None
    return value


def _portable_relative_path(value: Any, label: str, failures: list[str]) -> str | None:
    path = _nonempty_string(value, label, failures)
    if path is None:
        return None
    if "\\" in path or path.startswith("/"):
        failures.append(f"{label} must be a repository-relative POSIX path")
        return None
    parsed = PurePosixPath(path)
    if (
        not parsed.parts
        or parsed.as_posix() != path
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        failures.append(f"{label} must be normalized without traversal segments")
        return None
    for part in parsed.parts:
        if unicodedata.normalize("NFC", part) != part:
            failures.append(f"{label} must use NFC-normalized path segments")
        if part.endswith((" ", ".")) or ":" in part:
            failures.append(f"{label} is not portable across supported filesystems")
        if any(unicodedata.category(character).startswith("C") for character in part):
            failures.append(f"{label} contains a control character")
        if part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
            failures.append(f"{label} contains a Windows-reserved path segment")
    return path


def _sorted_unique_strings(
    value: Any,
    label: str,
    failures: list[str],
    *,
    paths: bool = False,
) -> list[str] | None:
    if type(value) is not list or any(type(item) is not str for item in value):
        failures.append(f"{label} must be an array of strings")
        return None
    strings = list(value)
    if len(strings) != len(set(strings)):
        failures.append(f"{label} must not contain duplicates")
    expected = sorted(strings, key=lambda item: item.encode("utf-8"))
    if strings != expected:
        failures.append(f"{label} must use UTF-8 bytewise order")
    if paths:
        for index, item in enumerate(strings):
            _portable_relative_path(item, f"{label}[{index}]", failures)
    return strings


def _inspect_contained_path(
    root: Path,
    relative_path: str,
    failures: list[str],
) -> Path | None:
    root = root.resolve()
    current = root
    for part in PurePosixPath(relative_path).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as error:
            failures.append(f"cannot inspect {relative_path}: {error}")
            return None
        if stat.S_ISLNK(metadata.st_mode):
            failures.append(f"runtime surface {relative_path!r} contains a symbolic link")
            return None
    try:
        resolved = current.resolve(strict=True)
    except OSError as error:
        failures.append(f"cannot resolve runtime surface {relative_path!r}: {error}")
        return None
    if not resolved.is_relative_to(root):
        failures.append(f"runtime surface {relative_path!r} escapes the repository root")
        return None
    return current


def _path_entry_is_missing(path: Path) -> bool:
    """Return true only for a genuinely absent entry, never for a broken symlink."""
    try:
        path.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return False


def _walk_regular_files(
    root: Path,
    relative_path: str,
    failures: list[str],
) -> list[str]:
    start = _inspect_contained_path(root, relative_path, failures)
    if start is None:
        return []
    try:
        metadata = start.lstat()
    except OSError as error:
        failures.append(f"cannot inspect {relative_path}: {error}")
        return []
    if stat.S_ISREG(metadata.st_mode):
        return [relative_path]
    if not stat.S_ISDIR(metadata.st_mode):
        failures.append(f"runtime surface {relative_path!r} must be a file or directory")
        return []

    files: list[str] = []

    def visit(directory: Path) -> None:
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name.encode("utf-8"))
        except OSError as error:
            failures.append(f"cannot list {_path_label(directory, root)}: {error}")
            return
        casefolded: set[str] = set()
        for child in children:
            relative = child.relative_to(root).as_posix()
            folded = unicodedata.normalize("NFC", child.name).casefold()
            if folded in casefolded:
                failures.append(
                    f"runtime surface {_path_label(directory, root)!r} contains a portable-name collision"
                )
            casefolded.add(folded)
            _portable_relative_path(relative, f"runtime surface {relative!r}", failures)
            try:
                child_metadata = child.lstat()
            except OSError as error:
                failures.append(f"cannot inspect {relative}: {error}")
                continue
            if stat.S_ISLNK(child_metadata.st_mode):
                failures.append(f"runtime surface {relative!r} must not be a symbolic link")
            elif stat.S_ISDIR(child_metadata.st_mode):
                visit(child)
            elif stat.S_ISREG(child_metadata.st_mode):
                files.append(relative)
            else:
                failures.append(f"runtime surface {relative!r} must be a regular file")

    visit(start)
    return files


def _flatten_json_leaves(value: Any, prefix: str = "") -> dict[str, Any]:
    if type(value) is dict and value:
        flattened: dict[str, Any] = {}
        for key in sorted(value, key=lambda item: item.encode("utf-8")):
            child_prefix = f"{prefix}.{key}" if prefix else key
            flattened.update(_flatten_json_leaves(value[key], child_prefix))
        return flattened
    return {prefix: value}


def _normalized_text_bytes(path: Path, label: str, failures: list[str]) -> bytes | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read runtime input {label}: {error}")
        return None
    if "\x00" in text:
        failures.append(f"runtime input {label} must not contain NUL")
        return None
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _manifest_shape(
    document: dict[str, Any],
    failures: list[str],
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]]] | None:
    expected_keys = {
        "schemaVersion",
        "digestAlgorithm",
        "canonicalization",
        "installedSurfaceRoots",
        "inputs",
        "exclusions",
    }
    _exact_object(document, expected_keys, "runtime input manifest", failures)
    if document.get("schemaVersion") != "1":
        failures.append("runtime input manifest schemaVersion must be '1'")
    if document.get("digestAlgorithm") != "sha256":
        failures.append("runtime input manifest digestAlgorithm must be 'sha256'")
    canonical = _exact_object(
        document.get("canonicalization"),
        {"recordFormat", "textEncoding", "lineEndings", "pathOrder"},
        "runtime input manifest canonicalization",
        failures,
    )
    if canonical is not None:
        expected_canonical = {
            "recordFormat": "canonical-json-records-v1",
            "textEncoding": "utf-8",
            "lineEndings": "lf",
            "pathOrder": "utf-8-bytewise",
        }
        for key, expected in expected_canonical.items():
            if canonical.get(key) != expected:
                failures.append(f"runtime input manifest canonicalization.{key} drifted")

    roots = _sorted_unique_strings(
        document.get("installedSurfaceRoots"),
        "runtime input manifest installedSurfaceRoots",
        failures,
        paths=True,
    )
    inputs_value = document.get("inputs")
    exclusions_value = document.get("exclusions")
    if type(inputs_value) is not list or type(exclusions_value) is not list:
        failures.append("runtime input manifest inputs and exclusions must be arrays")
        return None
    inputs = [item for item in inputs_value if type(item) is dict]
    exclusions = [item for item in exclusions_value if type(item) is dict]
    if len(inputs) != len(inputs_value) or len(exclusions) != len(exclusions_value):
        failures.append("runtime input manifest entries must be objects")
    if roots is None:
        return None
    for label, entries in (("inputs", inputs), ("exclusions", exclusions)):
        entry_paths = [item.get("path") for item in entries]
        if any(type(path) is not str for path in entry_paths):
            failures.append(f"runtime input manifest {label} paths must be strings")
            continue
        if len(entry_paths) != len(set(entry_paths)):
            failures.append(f"runtime input manifest {label} paths must be unique")
        if entry_paths != sorted(entry_paths, key=lambda item: item.encode("utf-8")):
            failures.append(f"runtime input manifest {label} must be ordered by path")
    return roots, inputs, exclusions


def compute_runtime_contract(
    root: Path,
    manifest: dict[str, Any],
    failures: list[str],
    *,
    historical: bool = False,
) -> RuntimeContract | None:
    """Compute one canonical runtime digest from a checked package tree."""
    initial_failure_count = len(failures)
    root = root.resolve()
    shape = _manifest_shape(manifest, failures)
    if shape is None:
        return None
    roots, inputs, exclusions = shape

    inventory: set[str] = set()
    for relative_path in roots:
        path = root / relative_path
        if historical and _path_entry_is_missing(path):
            continue
        inventory.update(_walk_regular_files(root, relative_path, failures))

    records: list[dict[str, Any]] = []
    classifications: dict[str, list[str]] = {}

    def classify(relative_path: str, owner: str) -> None:
        classifications.setdefault(relative_path, []).append(owner)

    for index, entry in enumerate(inputs):
        label = f"runtime input manifest inputs[{index}]"
        kind = entry.get("kind")
        expected = (
            {"path", "kind", "includedFields", "excludedFields", "rationale"}
            if kind == "json-fields"
            else {"path", "kind", "rationale"}
        )
        _exact_object(entry, expected, label, failures)
        relative_path = _portable_relative_path(entry.get("path"), f"{label}.path", failures)
        _nonempty_string(entry.get("rationale"), f"{label}.rationale", failures)
        if kind not in {"tree", "json-fields"}:
            failures.append(f"{label}.kind must be 'tree' or 'json-fields'")
        if relative_path is None:
            continue
        if not any(
            relative_path == root_path or relative_path.startswith(f"{root_path}/")
            for root_path in roots
        ):
            failures.append(f"{label}.path is outside installedSurfaceRoots")
        if kind == "tree":
            files = _walk_regular_files(root, relative_path, failures)
            if not files:
                failures.append(f"runtime input tree {relative_path!r} must contain a file")
            for file_path in files:
                classify(file_path, f"input:{relative_path}")
                content = _normalized_text_bytes(root / file_path, file_path, failures)
                if content is None:
                    continue
                records.append(
                    {
                        "kind": "text-file",
                        "path": file_path,
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "utf8Bytes": len(content),
                    }
                )
        elif kind == "json-fields":
            classify(relative_path, f"input:{relative_path}")
            included = _sorted_unique_strings(
                entry.get("includedFields"), f"{label}.includedFields", failures
            )
            excluded = _sorted_unique_strings(
                entry.get("excludedFields"), f"{label}.excludedFields", failures
            )
            document = load_json_document(root / relative_path, failures, root=root)
            if included is None or excluded is None or document is None:
                continue
            overlap = sorted(set(included) & set(excluded))
            if overlap:
                failures.append(f"{label} classifies fields twice: {', '.join(overlap)}")
            flattened = _flatten_json_leaves(document)
            classified_fields = set(included) | set(excluded)
            unclassified = sorted(set(flattened) - classified_fields)
            if unclassified:
                failures.append(
                    f"{relative_path} has unclassified manifest fields: {', '.join(unclassified)}"
                )
            missing_included = sorted(set(included) - set(flattened))
            if missing_included and not historical:
                failures.append(
                    f"{relative_path} is missing included fields: {', '.join(missing_included)}"
                )
            for field in included:
                present = field in flattened
                records.append(
                    {
                        "kind": "json-field",
                        "path": f"{relative_path}#{field}",
                        "present": present,
                        "value": flattened.get(field),
                    }
                )

    for index, entry in enumerate(exclusions):
        label = f"runtime input manifest exclusions[{index}]"
        _exact_object(
            entry,
            {"path", "kind", "classification", "rationale"},
            label,
            failures,
        )
        relative_path = _portable_relative_path(entry.get("path"), f"{label}.path", failures)
        kind = entry.get("kind")
        if kind not in {"file", "tree"}:
            failures.append(f"{label}.kind must be 'file' or 'tree'")
        _nonempty_string(entry.get("classification"), f"{label}.classification", failures)
        _nonempty_string(entry.get("rationale"), f"{label}.rationale", failures)
        if relative_path is None:
            continue
        target = root / relative_path
        if historical and _path_entry_is_missing(target):
            continue
        files = _walk_regular_files(root, relative_path, failures)
        if kind == "file" and files != [relative_path]:
            failures.append(f"runtime exclusion {relative_path!r} must identify one file")
        for file_path in files:
            classify(file_path, f"exclusion:{relative_path}")

    unclassified_files = sorted(inventory - set(classifications))
    if unclassified_files:
        failures.append(
            "installed package surfaces are unclassified: " + ", ".join(unclassified_files)
        )
    duplicate_files = sorted(
        path for path, owners in classifications.items() if len(owners) != 1
    )
    if duplicate_files:
        failures.append(
            "installed package surfaces are classified more than once: "
            + ", ".join(duplicate_files)
        )
    classified_outside_inventory = sorted(set(classifications) - inventory)
    if classified_outside_inventory:
        failures.append(
            "runtime classifications fall outside installedSurfaceRoots: "
            + ", ".join(classified_outside_inventory)
        )

    record_paths = [record["path"] for record in records]
    if len(record_paths) != len(set(record_paths)):
        failures.append("runtime digest records contain duplicate paths")
    records.sort(key=lambda record: record["path"].encode("utf-8"))
    payload = json.dumps(
        {
            "contract": "axiom-runtime-contract",
            "schemaVersion": manifest.get("schemaVersion"),
            "records": records,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(failures) != initial_failure_count:
        return None
    return RuntimeContract(
        digest=f"sha256:{hashlib.sha256(payload).hexdigest()}",
        record_count=len(records),
        payload=payload,
    )


def _manifest_sha256(root: Path) -> str:
    # Universal-newline decoding keeps this binding stable for LF and CRLF
    # checkouts while preserving every other manifest byte as policy evidence.
    text = (root / INPUT_MANIFEST_RELATIVE).read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_identity(
    document: dict[str, Any],
    contract: RuntimeContract,
    root: Path,
    failures: list[str],
) -> tuple[str | None, int | None]:
    label = IDENTITY_RELATIVE
    _exact_object(
        document,
        {"schemaVersion", "pluginVersion", "repositoryPolicyRevision", "runtimeContract"},
        label,
        failures,
    )
    if document.get("schemaVersion") != "1":
        failures.append(f"{label}.schemaVersion must be '1'")
    plugin_version = document.get("pluginVersion")
    if parse_production_release_version(plugin_version) is None:
        failures.append(f"{label}.pluginVersion must be stable strict SemVer")
        plugin_version = None
    manifest_version = release_version(root)
    if plugin_version != manifest_version:
        failures.append(f"{label}.pluginVersion must match both plugin manifests")
    revision = document.get("repositoryPolicyRevision")
    if type(revision) is not int or revision < 1:
        failures.append(f"{label}.repositoryPolicyRevision must be a positive integer")
        revision = None
    runtime = _exact_object(
        document.get("runtimeContract"),
        {"schemaVersion", "inputManifest", "inputManifestSha256", "digest", "recordCount"},
        f"{label}.runtimeContract",
        failures,
    )
    if runtime is not None:
        if runtime.get("schemaVersion") != "1":
            failures.append(f"{label}.runtimeContract.schemaVersion must be '1'")
        if runtime.get("inputManifest") != INPUT_MANIFEST_RELATIVE:
            failures.append(f"{label}.runtimeContract.inputManifest drifted")
        if runtime.get("inputManifestSha256") != _manifest_sha256(root):
            failures.append(f"{label}.runtimeContract.inputManifestSha256 drifted")
        if runtime.get("digest") != contract.digest:
            failures.append(f"{label}.runtimeContract.digest does not match computed inputs")
        if runtime.get("recordCount") != contract.record_count:
            failures.append(f"{label}.runtimeContract.recordCount does not match computed inputs")
    return plugin_version, revision


def _version_key(version: str) -> tuple[int, int, int]:
    parsed = parse_production_release_version(version)
    if parsed is None:
        return (-1, -1, -1)
    return tuple(int(part) for part in version.split("."))


def _validate_history(
    document: dict[str, Any],
    manifest_sha256: str,
    current_version: str | None,
    current_digest: str,
    failures: list[str],
) -> dict[str, dict[str, Any]]:
    label = HISTORY_RELATIVE
    _exact_object(
        document,
        {"schemaVersion", "inputManifest", "inputManifestSha256", "entries", "characterizations"},
        label,
        failures,
    )
    if document.get("schemaVersion") != "1":
        failures.append(f"{label}.schemaVersion must be '1'")
    if document.get("inputManifest") != INPUT_MANIFEST_RELATIVE:
        failures.append(f"{label}.inputManifest drifted")
    if document.get("inputManifestSha256") != manifest_sha256:
        failures.append(f"{label}.inputManifestSha256 drifted")
    entries_value = document.get("entries")
    if type(entries_value) is not list or not entries_value:
        failures.append(f"{label}.entries must be a non-empty array")
        return {}
    entries: dict[str, dict[str, Any]] = {}
    ordered_versions: list[str] = []
    for index, value in enumerate(entries_value):
        item_label = f"{label}.entries[{index}]"
        entry = _exact_object(
            value,
            {"pluginVersion", "tag", "commit", "runtimeContractDigest", "derivation"},
            item_label,
            failures,
        )
        if entry is None:
            continue
        version = entry.get("pluginVersion")
        if parse_production_release_version(version) is None:
            failures.append(f"{item_label}.pluginVersion must be stable strict SemVer")
            continue
        if version in entries:
            failures.append(f"{label}.entries repeats pluginVersion {version}")
        entries[version] = entry
        ordered_versions.append(version)
        if entry.get("tag") != f"v{version}":
            failures.append(f"{item_label}.tag must match pluginVersion")
        if type(entry.get("commit")) is not str or COMMIT_PATTERN.fullmatch(entry["commit"]) is None:
            failures.append(f"{item_label}.commit must be a lowercase full Git SHA")
        if type(entry.get("runtimeContractDigest")) is not str or DIGEST_PATTERN.fullmatch(entry["runtimeContractDigest"]) is None:
            failures.append(f"{item_label}.runtimeContractDigest must be a SHA-256 identity")
        if entry.get("derivation") != "derived-from-immutable-tag-with-schema-v1":
            failures.append(f"{item_label}.derivation drifted")
    if ordered_versions != sorted(ordered_versions, key=_version_key):
        failures.append(f"{label}.entries must be ordered by pluginVersion")

    characterizations = document.get("characterizations")
    characterized_pairs: set[tuple[str, str]] = set()
    if type(characterizations) is not list:
        failures.append(f"{label}.characterizations must be an array")
    else:
        pairs = []
        for index, value in enumerate(characterizations):
            item_label = f"{label}.characterizations[{index}]"
            item = _exact_object(
                value,
                {"fromVersion", "toVersion", "changeClass", "expectedDigestRelation", "rationale"},
                item_label,
                failures,
            )
            if item is None:
                continue
            from_version = item.get("fromVersion")
            to_version = item.get("toVersion")
            if from_version not in entries or to_version not in entries:
                failures.append(f"{item_label} must reference history entries")
                continue
            pair = (from_version, to_version)
            if pair in characterized_pairs:
                failures.append(f"{label}.characterizations repeats {pair}")
            characterized_pairs.add(pair)
            pairs.append(pair)
            relation = item.get("expectedDigestRelation")
            if relation not in {"equal", "different"}:
                failures.append(f"{item_label}.expectedDigestRelation is invalid")
            actual_equal = (
                entries[from_version].get("runtimeContractDigest")
                == entries[to_version].get("runtimeContractDigest")
            )
            if (relation == "equal") is not actual_equal:
                failures.append(f"{item_label} digest relation does not match its history entries")
            change_class = item.get("changeClass")
            if change_class not in {"installed-runtime-change", "repository-policy-only"}:
                failures.append(f"{item_label}.changeClass is invalid")
            if change_class == "installed-runtime-change" and relation != "different":
                failures.append(f"{item_label} installed-runtime change must alter the digest")
            if change_class == "repository-policy-only" and relation != "equal":
                failures.append(f"{item_label} repository-policy change must retain the digest")
            _nonempty_string(item.get("rationale"), f"{item_label}.rationale", failures)
        if pairs != sorted(pairs, key=lambda pair: (_version_key(pair[0]), _version_key(pair[1]))):
            failures.append(f"{label}.characterizations must be ordered by version pair")

    adjacent_recent_pairs = {
        (first, second)
        for first, second in zip(ordered_versions, ordered_versions[1:])
        if _version_key(first)[:2] == _version_key(second)[:2]
        and _version_key(second)[2] == _version_key(first)[2] + 1
    }
    if characterized_pairs != adjacent_recent_pairs:
        failures.append(f"{label}.characterizations must cover every contiguous recorded release")

    if entries and current_version is not None:
        latest_version = max(entries, key=_version_key)
        if _version_key(current_version) < _version_key(latest_version):
            failures.append(f"current pluginVersion predates runtime-contract history")
        elif current_version == latest_version:
            if entries[latest_version].get("runtimeContractDigest") != current_digest:
                failures.append(
                    "installed runtime changed without advancing pluginVersion from its immutable tag"
                )
        elif entries[latest_version].get("runtimeContractDigest") == current_digest:
            failures.append(
                "pluginVersion advanced while runtimeContractDigest stayed unchanged; use repositoryPolicyRevision"
            )
    return entries


def _validate_policy_revisions(
    document: dict[str, Any],
    current_revision: int | None,
    current_digest: str,
    failures: list[str],
) -> None:
    label = POLICY_REVISIONS_RELATIVE
    _exact_object(document, {"schemaVersion", "revisions"}, label, failures)
    if document.get("schemaVersion") != "1":
        failures.append(f"{label}.schemaVersion must be '1'")
    revisions = document.get("revisions")
    if type(revisions) is not list or not revisions:
        failures.append(f"{label}.revisions must be a non-empty append-only array")
        return
    observed: list[int] = []
    for index, value in enumerate(revisions):
        item_label = f"{label}.revisions[{index}]"
        item = _exact_object(
            value,
            {
                "revision",
                "recordedOn",
                "baselineCommit",
                "sourceIssue",
                "summary",
                "runtimeContractDigest",
            },
            item_label,
            failures,
        )
        if item is None:
            continue
        revision = item.get("revision")
        if type(revision) is not int or revision < 1:
            failures.append(f"{item_label}.revision must be a positive integer")
        else:
            observed.append(revision)
        recorded_on = item.get("recordedOn")
        try:
            if type(recorded_on) is not str:
                raise ValueError
            date.fromisoformat(recorded_on)
        except ValueError:
            failures.append(f"{item_label}.recordedOn must be an ISO calendar date")
        if type(item.get("baselineCommit")) is not str or COMMIT_PATTERN.fullmatch(item["baselineCommit"]) is None:
            failures.append(f"{item_label}.baselineCommit must be a lowercase full Git SHA")
        if type(item.get("sourceIssue")) is not int or item["sourceIssue"] < 1:
            failures.append(f"{item_label}.sourceIssue must be a positive integer")
        summary = _nonempty_string(item.get("summary"), f"{item_label}.summary", failures)
        if summary is not None and len(summary) > 200:
            failures.append(f"{item_label}.summary must contain at most 200 characters")
        if type(item.get("runtimeContractDigest")) is not str or DIGEST_PATTERN.fullmatch(item["runtimeContractDigest"]) is None:
            failures.append(f"{item_label}.runtimeContractDigest must be a SHA-256 identity")
    if observed != list(range(1, len(revisions) + 1)):
        failures.append(f"{label}.revisions must be contiguous, ordered, and append-only")
    last = revisions[-1] if type(revisions[-1]) is dict else {}
    if current_revision is not None and last.get("revision") != current_revision:
        failures.append(f"{label} latest revision must match runtime identity")
    if last.get("runtimeContractDigest") != current_digest:
        failures.append(f"{label} latest revision must bind the current runtime digest")


def render_runtime_identity(document: dict[str, Any]) -> str:
    """Render the current three-subject identity as stable Markdown."""
    runtime = document["runtimeContract"]
    return "\n".join(
        (
            f"- `pluginVersion`: `{document['pluginVersion']}`",
            f"- `repositoryPolicyRevision`: `{document['repositoryPolicyRevision']}`",
            f"- `runtimeContractDigest` (schema v{runtime['schemaVersion']}): `{runtime['digest']}`",
            f"- Digest input manifest: [`{runtime['inputManifest']}`]({runtime['inputManifest']})",
        )
    )


def replace_runtime_identity_block(text: str, document: dict[str, Any]) -> str:
    """Replace the one managed README identity block."""
    if text.count(RUNTIME_IDENTITY_START) != 1 or text.count(RUNTIME_IDENTITY_END) != 1:
        raise ValueError("README runtime-identity markers must each appear exactly once")
    start = text.index(RUNTIME_IDENTITY_START) + len(RUNTIME_IDENTITY_START)
    end = text.index(RUNTIME_IDENTITY_END, start)
    return text[:start] + "\n" + render_runtime_identity(document) + "\n" + text[end:]


def check_runtime_identity(
    failures: list[str],
    *,
    root: Path = REPOSITORY_ROOT,
    check_surfaces: bool = True,
) -> int:
    """Validate the current runtime identity, append-only records, and rendered facts."""
    root = root.resolve()
    manifest = load_json_document(root / INPUT_MANIFEST_RELATIVE, failures, root=root)
    if manifest is None:
        return 0
    contract = compute_runtime_contract(root, manifest, failures)
    if contract is None:
        return 0
    identity = load_json_document(root / IDENTITY_RELATIVE, failures, root=root)
    history = load_json_document(root / HISTORY_RELATIVE, failures, root=root)
    revisions = load_json_document(root / POLICY_REVISIONS_RELATIVE, failures, root=root)
    if identity is None or history is None or revisions is None:
        return contract.record_count
    plugin_version, policy_revision = _validate_identity(
        identity, contract, root, failures
    )
    _validate_history(
        history,
        _manifest_sha256(root),
        plugin_version,
        contract.digest,
        failures,
    )
    _validate_policy_revisions(
        revisions,
        policy_revision,
        contract.digest,
        failures,
    )
    if check_surfaces:
        readme_path = root / README_RELATIVE
        try:
            readme = readme_path.read_text(encoding="utf-8")
            expected = replace_runtime_identity_block(readme, identity)
        except (OSError, UnicodeError, ValueError) as error:
            failures.append(f"cannot validate {README_RELATIVE} runtime identity: {error}")
        else:
            if readme != expected:
                failures.append(f"{README_RELATIVE} runtime identity block is stale")
    return contract.record_count


__all__ = [
    "HISTORY_RELATIVE",
    "IDENTITY_RELATIVE",
    "INPUT_MANIFEST_RELATIVE",
    "POLICY_REVISIONS_RELATIVE",
    "RUNTIME_IDENTITY_SURFACES",
    "RuntimeContract",
    "check_runtime_identity",
    "compute_runtime_contract",
    "load_json_document",
    "render_runtime_identity",
    "replace_runtime_identity_block",
]
