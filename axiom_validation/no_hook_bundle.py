"""Build and validate Axiom's deterministic Hook-independent derived bundle."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_RELATIVE = Path("evals/no-hook/bundle-manifest-schema-v1.json")
EVIDENCE_RELATIVE = Path(
    "evidence/profiles/openai-hook-independent-v1/bundle-v1.json"
)
ENTRYPOINT_RELATIVE = Path("scripts/build-no-hook-bundle.py")
MODULE_RELATIVE = Path("axiom_validation/no_hook_bundle.py")

PROFILE_ID = "openai-hook-independent-v1"
BUNDLE_MANIFEST_NAME = "BUNDLE-MANIFEST.json"
BUNDLE_ENVELOPE_NAME = "BUNDLE-ENVELOPE.json"
PLUGIN_DIRECTORY_NAME = "plugin"
STAGING_DIRECTORY_NAME = ".axiom-no-hook-bundle-staging"
RUNTIME_CANONICALIZATION_VERSION = "1"
BUNDLE_SCHEMA_VERSION = "1"
BUILDER_ID = "axiom-no-hook-bundle-builder"
BUILDER_VERSION = "1"
SOURCE_REPOSITORY_SLUG = "wheakerd/axiom"

MAX_RUNTIME_FILES = 128
MAX_RUNTIME_FILE_BYTES = 256 * 1024
MAX_RUNTIME_BYTES = 2 * 1024 * 1024
MAX_BUNDLE_MANIFEST_BYTES = 512 * 1024
MAX_ARCHIVE_BYTES = 4 * 1024 * 1024
MAX_PATH_BYTES = 240
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_TIMESTAMP_TEXT = "1980-01-01T00:00:00"
FILE_MODE = 0o100644
DIRECTORY_MODE = 0o040755

OID_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
SEMVER_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z"
)
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
ALLOWED_GIT_COMMANDS = frozenset(
    {"cat-file", "for-each-ref", "hash-object", "ls-tree", "rev-parse", "status"}
)
DANGEROUS_GIT_ENVIRONMENT = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_SYSTEM",
        "GIT_DIR",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_INDEX_FILE",
        "GIT_NAMESPACE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_REPLACE_REF_BASE",
        "GIT_WORK_TREE",
    }
)
DANGEROUS_GIT_ENVIRONMENT_PREFIXES = (
    "GIT_CONFIG_KEY_",
    "GIT_CONFIG_VALUE_",
)
FORBIDDEN_DERIVED_MANIFEST_FIELDS = frozenset(
    {"apps", "assets", "hooks", "interface", "mcpServers"}
)

PROFILE_ARTIFACT_KEYS = (
    "profileContract",
    "goldenSet",
    "responseSchema",
    "benchmark",
)
SOURCE_SUPPORT_PATHS = (
    ".codex-plugin/plugin.json",
    "evidence/runtime-identity.json",
)

INCLUDED_SURFACES = (
    {
        "surface": ".codex-plugin/plugin.json",
        "rationale": "A minimal derived manifest exposes only package identity and the shared Skill root.",
    },
    {
        "surface": "skills/**",
        "rationale": "All eight canonical Skill roots and their complete tracked reference and resource closure are runtime payload.",
    },
    {
        "surface": "BUNDLE-MANIFEST.json",
        "rationale": "The closed manifest binds runtime identity, source provenance, contract inputs, builder identity, and transport policy.",
    },
)
EXCLUDED_SURFACES = (
    {
        "surface": "hooks/**",
        "rationale": "The compatibility profile is Hook-independent and never executes a Hook lifecycle.",
    },
    {
        "surface": "source .codex-plugin full-profile fields",
        "rationale": "Hooks, interface presentation, assets, apps, and MCP declarations are not copied into the derived manifest.",
    },
    {
        "surface": ".claude-plugin/**",
        "rationale": "Claude Code is excluded from the Hook-independent profile and its full-profile wrapper is not transported.",
    },
    {
        "surface": ".agents/plugins/**",
        "rationale": "Marketplace installation metadata is distribution policy rather than profile runtime payload.",
    },
    {
        "surface": "assets/**",
        "rationale": "No asset field exists in the minimal derived manifest.",
    },
    {
        "surface": "evals/**",
        "rationale": "Contract artifacts are digest-bound metadata and are not copied into the runtime package.",
    },
    {
        "surface": "evidence/**",
        "rationale": "Repository evidence is not installed or transported as Skill runtime.",
    },
    {
        "surface": "tests/**",
        "rationale": "Tests validate the builder but are not runtime payload.",
    },
    {
        "surface": "scripts/**",
        "rationale": "The builder entrypoint is identity-bound but is not included in its generated package.",
    },
    {
        "surface": "axiom_validation/**",
        "rationale": "Repository validators and builder implementation are identity-bound tooling, not packaged Skill behavior.",
    },
    {
        "surface": ".github/**",
        "rationale": "Repository automation is excluded from the compatibility artifact.",
    },
    {
        "surface": "private maintenance content",
        "rationale": "The private maintenance repository is outside the public source tree and cannot enter generated output.",
    },
    {
        "surface": "untracked, ignored, and cache paths",
        "rationale": "Git-tree extraction includes only validated tracked blobs from the exact source commit.",
    },
)


class BundleContractError(ValueError):
    """Raised when a source, destination, identity, or artifact is unsafe."""


class DuplicateJsonKeyError(ValueError):
    """Raised when a protected JSON document repeats a key."""


@dataclass(frozen=True)
class GitEntry:
    """One validated regular file from an exact Git tree."""

    path: str
    mode: str
    object_type: str
    oid: str
    size: int
    data: bytes


@dataclass(frozen=True)
class BundleInputs:
    """All immutable inputs needed to construct one bundle."""

    source: "GitObjectSource"
    source_commit: str
    source_tree: str
    source_status: bytes
    schema: dict[str, Any]
    schema_bytes: bytes
    schema_contract: dict[str, Any]
    plugin_version: str
    source_repository_policy_revision: int
    full_profile_runtime_digest: str
    minimal_manifest: dict[str, str]
    minimal_manifest_bytes: bytes
    contract_bindings: dict[str, Any]
    runtime_records: tuple[dict[str, Any], ...]
    runtime_files: tuple[GitEntry, ...]
    behavior_dependencies: tuple[dict[str, Any], ...]

    def verify_source_unchanged(self) -> None:
        """Re-read the source boundary after output construction."""
        self.source.verify_snapshot(
            self.source_commit,
            self.source_tree,
            self.source_status,
        )


@dataclass(frozen=True)
class BuildResult:
    """Deterministic identities and counts for one completed build."""

    profile_runtime_digest: str
    bundle_manifest_digest: str
    archive_sha256: str
    archive_size: int
    archive_filename: str
    directory_file_count: int
    directory_total_bytes: int
    bundle_manifest: dict[str, Any]
    envelope: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        return {
            "profileRuntimeDigest": self.profile_runtime_digest,
            "bundleManifestDigest": self.bundle_manifest_digest,
            "archiveSha256": self.archive_sha256,
            "archiveSize": self.archive_size,
            "archiveFilename": self.archive_filename,
            "directoryFileCount": self.directory_file_count,
            "directoryTotalBytes": self.directory_total_bytes,
        }


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _load_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    if len(data) > MAX_BUNDLE_MANIFEST_BYTES:
        raise BundleContractError(
            f"{label} exceeds the {MAX_BUNDLE_MANIFEST_BYTES}-byte JSON limit"
        )
    if data.startswith(b"\xef\xbb\xbf"):
        raise BundleContractError(f"{label} must not contain a UTF-8 BOM")
    try:
        text = data.decode("utf-8")
        document = json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except (UnicodeError, json.JSONDecodeError, DuplicateJsonKeyError) as error:
        raise BundleContractError(f"invalid JSON in {label}: {error}") from error
    if type(document) is not dict:
        raise BundleContractError(f"{label} must contain a top-level object")
    return document


def _read_regular_file(path: Path, label: str, *, maximum: int) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise BundleContractError(f"cannot inspect {label}: {error}") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise BundleContractError(f"{label} must not be a symbolic link")
    if not stat.S_ISREG(metadata.st_mode):
        raise BundleContractError(f"{label} must be a regular file")
    if metadata.st_size > maximum:
        raise BundleContractError(f"{label} exceeds its {maximum}-byte limit")
    try:
        return path.read_bytes()
    except OSError as error:
        raise BundleContractError(f"cannot read {label}: {error}") from error


def _pretty_json_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=True, indent=2) + "\n").encode("ascii")


def _canonical_json_bytes(document: Any) -> bytes:
    return json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest_identity(data: bytes) -> str:
    return f"sha256:{_sha256(data)}"


def _exact_object(value: Any, keys: Iterable[str], label: str) -> dict[str, Any]:
    expected = set(keys)
    if type(value) is not dict:
        raise BundleContractError(f"{label} must be an object")
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        raise BundleContractError(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        raise BundleContractError(f"{label} contains unknown fields: {', '.join(unknown)}")
    return value


def validate_portable_path(value: str, *, label: str = "path") -> str:
    """Require one portable, NFC-preserved, relative POSIX path."""
    if type(value) is not str or not value:
        raise BundleContractError(f"{label} must be a non-empty string")
    if len(value.encode("utf-8")) > MAX_PATH_BYTES:
        raise BundleContractError(f"{label} exceeds the {MAX_PATH_BYTES}-byte path limit")
    if value.startswith("/") or "\\" in value:
        raise BundleContractError(f"{label} must be a relative POSIX path")
    parsed = PurePosixPath(value)
    if parsed.as_posix() != value or any(part in {"", ".", ".."} for part in parsed.parts):
        raise BundleContractError(f"{label} contains traversal or non-canonical segments")
    if unicodedata.normalize("NFC", value) != value:
        raise BundleContractError(f"{label} must already be NFC-normalized")
    for part in parsed.parts:
        if part.endswith((" ", ".")) or ":" in part:
            raise BundleContractError(f"{label} is not portable across supported filesystems")
        if any(unicodedata.category(character).startswith("C") for character in part):
            raise BundleContractError(f"{label} contains a control character")
        if part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
            raise BundleContractError(f"{label} contains a Windows-reserved name")
    return value


def validate_path_set(paths: Iterable[str], *, label: str = "paths") -> tuple[str, ...]:
    """Reject duplicates, normalization collisions, and casefold collisions."""
    values = tuple(paths)
    for index, path in enumerate(values):
        validate_portable_path(path, label=f"{label}[{index}]")
    if len(values) != len(set(values)):
        raise BundleContractError(f"{label} contains a duplicate path")
    normalized: dict[str, str] = {}
    casefolded: dict[str, str] = {}
    for path in values:
        nfc = unicodedata.normalize("NFC", path)
        folded = nfc.casefold()
        if nfc in normalized and normalized[nfc] != path:
            raise BundleContractError(f"{label} contains a Unicode-normalization collision")
        if folded in casefolded and casefolded[folded] != path:
            raise BundleContractError(f"{label} contains a Unicode casefold collision")
        normalized[nfc] = path
        casefolded[folded] = path
    ordered = tuple(sorted(values, key=lambda item: item.encode("utf-8")))
    if values != ordered:
        raise BundleContractError(f"{label} must use UTF-8 bytewise order")
    return values


def _validate_runtime_text(data: bytes, path: str) -> None:
    if data.startswith(b"\xef\xbb\xbf"):
        raise BundleContractError(f"runtime file {path} must not contain a UTF-8 BOM")
    if b"\x00" in data:
        raise BundleContractError(f"runtime file {path} must not contain NUL")
    if b"\r" in data:
        raise BundleContractError(f"runtime file {path} must use LF line endings")
    try:
        data.decode("utf-8")
    except UnicodeError as error:
        raise BundleContractError(f"runtime file {path} must be UTF-8: {error}") from error
    if not data.endswith(b"\n"):
        raise BundleContractError(f"runtime file {path} must end with LF")


def _ensure_no_symlink_components(path: Path, label: str) -> Path:
    absolute = Path(os.path.abspath(os.fspath(path)))
    anchor = Path(absolute.anchor)
    current = anchor
    for part in absolute.parts[1:]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as error:
            raise BundleContractError(f"cannot inspect {label} component {current}: {error}") from error
        if stat.S_ISLNK(metadata.st_mode):
            raise BundleContractError(f"{label} component {current} must not be a symbolic link")
    return absolute


def _validate_destination(source_repository: Path, destination: Path) -> Path:
    destination = _ensure_no_symlink_components(destination, "destination")
    metadata = destination.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise BundleContractError("destination must be an existing ordinary directory")
    source_repository = Path(os.path.abspath(os.fspath(source_repository)))
    if destination == source_repository or source_repository in destination.parents:
        raise BundleContractError("destination must be outside the source repository")
    entries = list(destination.iterdir())
    if entries:
        raise BundleContractError("destination must be empty")
    return destination


class GitObjectSource:
    """Read an exact commit/tree/blob snapshot without Git replacement semantics."""

    def __init__(self, repository: Path) -> None:
        self.repository = _ensure_no_symlink_components(repository, "source repository")
        if not self.repository.is_dir():
            raise BundleContractError("source repository must be an existing directory")
        dangerous = sorted(
            key
            for key in os.environ
            if key in DANGEROUS_GIT_ENVIRONMENT
            or key.startswith(DANGEROUS_GIT_ENVIRONMENT_PREFIXES)
        )
        if dangerous:
            raise BundleContractError(
                "dangerous ambient Git environment is not allowed: " + ", ".join(dangerous)
            )
        self.environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        self.environment.update(
            {
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_SYSTEM": os.devnull,
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        actual_root = Path(
            self.run(("rev-parse", "--show-toplevel")).decode("utf-8").strip()
        )
        if Path(os.path.abspath(os.fspath(actual_root))) != self.repository:
            raise BundleContractError("source repository must be the exact Git worktree root")
        replace_refs = self.run(("for-each-ref", "--format=%(refname)", "refs/replace/"))
        if replace_refs.strip():
            raise BundleContractError("Git replace refs are not allowed for bundle source")
        alternates_path = Path(
            self.run(("rev-parse", "--git-path", "objects/info/alternates"))
            .decode("utf-8")
            .strip()
        )
        if not alternates_path.is_absolute():
            alternates_path = self.repository / alternates_path
        if alternates_path.exists():
            raise BundleContractError("Git object alternates are not allowed for bundle source")

    def run(self, arguments: tuple[str, ...], *, input_bytes: bytes | None = None) -> bytes:
        if not arguments or arguments[0] not in ALLOWED_GIT_COMMANDS:
            raise BundleContractError("builder attempted a non-read-only Git command")
        command = [
            "git",
            "--no-replace-objects",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-c",
            "protocol.allow=never",
            "-C",
            str(self.repository),
            *arguments,
        ]
        try:
            result = subprocess.run(
                command,
                input=input_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.environment,
                shell=False,
                check=False,
            )
        except OSError as error:
            raise BundleContractError(f"read-only Git command could not run: {error}") from error
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise BundleContractError(
                f"read-only Git command failed ({arguments[0]}): {detail or 'no diagnostic'}"
            )
        return result.stdout

    def object_type(self, oid: str) -> str:
        return self.run(("cat-file", "-t", oid)).decode("ascii").strip()

    def tree_for_commit(self, commit: str) -> str:
        return self.run(("rev-parse", f"{commit}^{{tree}}")).decode("ascii").strip()

    def status(self) -> bytes:
        return self.run(
            (
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--ignored=matching",
                "--",
                "skills",
            )
        )

    def verify_snapshot(self, commit: str, tree: str, initial_status: bytes) -> None:
        if self.object_type(commit) != "commit":
            raise BundleContractError("source commit object changed or became unavailable")
        if self.tree_for_commit(commit) != tree:
            raise BundleContractError("source commit/tree changed during build")
        if self.object_type(tree) != "tree":
            raise BundleContractError("source tree object changed or became unavailable")
        if self.status() != initial_status or initial_status:
            raise BundleContractError("runtime path working-tree state changed during build")

    @staticmethod
    def _parse_ls_tree(output: bytes) -> tuple[tuple[str, str, str, int, str], ...]:
        parsed: list[tuple[str, str, str, int, str]] = []
        for record in output.split(b"\0"):
            if not record:
                continue
            try:
                metadata, raw_path = record.split(b"\t", 1)
                mode, object_type, oid, raw_size = metadata.split(b" ", 3)
                path = raw_path.decode("utf-8")
                size = int(raw_size)
            except (ValueError, UnicodeError) as error:
                raise BundleContractError(f"invalid git ls-tree record: {error}") from error
            parsed.append(
                (
                    mode.decode("ascii"),
                    object_type.decode("ascii"),
                    oid.decode("ascii"),
                    size,
                    path,
                )
            )
        return tuple(parsed)

    def list_files(self, commit: str, prefix: str) -> tuple[GitEntry, ...]:
        output = self.run(
            ("ls-tree", "-r", "-z", "-l", "--full-tree", commit, "--", prefix)
        )
        entries: list[GitEntry] = []
        for mode, object_type, oid, size, path in self._parse_ls_tree(output):
            if mode != "100644" or object_type != "blob":
                raise BundleContractError(
                    f"source path {path} must be a non-executable 100644 blob; found {mode} {object_type}"
                )
            if self.object_type(oid) != "blob":
                raise BundleContractError(f"source object {oid} for {path} is not a blob")
            data = self.run(("cat-file", "blob", oid))
            if len(data) != size:
                raise BundleContractError(f"source blob size mismatch for {path}")
            computed_oid = self.run(("hash-object", "--stdin"), input_bytes=data).decode("ascii").strip()
            if computed_oid != oid:
                raise BundleContractError(f"source blob OID mismatch for {path}")
            entries.append(GitEntry(path, mode, object_type, oid, size, data))
        return tuple(entries)

    def read_file(self, commit: str, path: str) -> GitEntry:
        entries = self.list_files(commit, path)
        exact = [entry for entry in entries if entry.path == path]
        if len(exact) != 1 or len(entries) != 1:
            raise BundleContractError(f"source path {path} must resolve to exactly one regular blob")
        return exact[0]


def _schema_contract(schema: dict[str, Any]) -> dict[str, Any]:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise BundleContractError("bundle schema must use JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        raise BundleContractError("bundle schema top-level must be closed")
    contract = _exact_object(
        schema.get("x-axiom-contract"),
        {
            "candidateRepositoryPolicyRevision",
            "sourceRepositoryPolicyRevision",
            "runtimeInventory",
            "contractBindings",
        },
        "bundle schema x-axiom-contract",
    )
    inventory = _exact_object(
        contract["runtimeInventory"],
        {"directSkillRoots", "runtimeFiles", "runtimeBytes", "allowedExtensions"},
        "bundle schema runtimeInventory",
    )
    if inventory != {
        "directSkillRoots": 8,
        "runtimeFiles": 50,
        "runtimeBytes": 230826,
        "allowedExtensions": [".md", ".yaml"],
    }:
        raise BundleContractError("bundle schema runtime inventory contract drifted")
    if contract["candidateRepositoryPolicyRevision"] != 6:
        raise BundleContractError("bundle schema candidate repository policy revision drifted")
    if contract["sourceRepositoryPolicyRevision"] != 5:
        raise BundleContractError("bundle schema source repository policy revision drifted")
    bindings = _exact_object(
        contract["contractBindings"],
        {*PROFILE_ARTIFACT_KEYS, "hostCaseSets"},
        "bundle schema contractBindings",
    )
    for key in PROFILE_ARTIFACT_KEYS:
        binding = _exact_object(bindings[key], {"path", "sha256"}, f"bundle schema {key}")
        validate_portable_path(binding["path"], label=f"bundle schema {key}.path")
        if SHA256_PATTERN.fullmatch(str(binding["sha256"])) is None:
            raise BundleContractError(f"bundle schema {key}.sha256 must be SHA-256")
    host_sets = bindings["hostCaseSets"]
    if type(host_sets) is not list or len(host_sets) != 2:
        raise BundleContractError("bundle schema must bind exactly two ordered host case sets")
    for index, host_set in enumerate(host_sets):
        item = _exact_object(host_set, {"id", "host", "sha256"}, f"hostCaseSets[{index}]")
        if item["host"] not in {"codex", "chatgpt"}:
            raise BundleContractError("bundle schema hostCaseSets contains an unknown host")
        if SHA256_PATTERN.fullmatch(str(item["sha256"])) is None:
            raise BundleContractError("bundle schema hostCaseSets sha256 must be SHA-256")
    if [item["host"] for item in host_sets] != ["codex", "chatgpt"]:
        raise BundleContractError("bundle schema host case sets must remain Codex then ChatGPT")
    return contract


def load_bundle_schema(path: Path) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    data = _read_regular_file(path, SCHEMA_RELATIVE.as_posix(), maximum=MAX_BUNDLE_MANIFEST_BYTES)
    document = _load_json_bytes(data, SCHEMA_RELATIVE.as_posix())
    return document, data, _schema_contract(document)


def _host_case_set_sha256(
    case_set: dict[str, Any], contract_versions: dict[str, int]
) -> str:
    case_ids = case_set.get("caseIds")
    if type(case_ids) is not list:
        raise BundleContractError("benchmark host case set caseIds must be an array")
    payload = {
        "id": case_set.get("id"),
        "host": case_set.get("host"),
        "requiredRoutes": case_set.get("requiredRoutes"),
        "matrix": case_set.get("matrix"),
        "caseContracts": [
            {"id": case_id, "contractVersion": contract_versions.get(case_id)}
            for case_id in case_ids
        ],
    }
    return _sha256(_canonical_json_bytes(payload))


def _load_contract_versions(data: bytes) -> dict[str, int]:
    versions: dict[str, int] = {}
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeError as error:
        raise BundleContractError(f"Golden Set must be UTF-8: {error}") from error
    if not lines or not data.endswith(b"\n"):
        raise BundleContractError("Golden Set must be non-empty and end with LF")
    for line_number, line in enumerate(lines, start=1):
        try:
            case = json.loads(line, object_pairs_hook=_reject_duplicate_json_keys)
        except (json.JSONDecodeError, DuplicateJsonKeyError) as error:
            raise BundleContractError(f"invalid Golden Set line {line_number}: {error}") from error
        if type(case) is not dict or type(case.get("id")) is not str:
            raise BundleContractError(f"Golden Set line {line_number} has no stable case ID")
        version = case.get("contractVersion")
        if type(version) is not int or version < 1 or version > 1_000_000:
            raise BundleContractError(f"Golden Set case {case['id']} has invalid contractVersion")
        if case["id"] in versions:
            raise BundleContractError(f"Golden Set repeats case ID {case['id']}")
        versions[case["id"]] = version
    return versions


def _runtime_kind(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) == 3 and parts[-1] == "SKILL.md":
        return "skill"
    if "agents" in parts:
        return "agent-metadata"
    if "references" in parts:
        return "reference"
    return "resource"


def _validate_reference_closure(entries: tuple[GitEntry, ...], skill_roots: tuple[str, ...]) -> None:
    by_path = {entry.path: entry for entry in entries}
    markdown_link = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
    inline_resource = re.compile(
        r"`((?:references|agents|resources|assets)/[^`\s]+\.(?:md|yaml|yml|json|txt))`"
    )
    for root in skill_roots:
        root_prefix = f"skills/{root}/"
        skill_path = root_prefix + "SKILL.md"
        if skill_path not in by_path:
            raise BundleContractError(f"canonical Skill root {root} is missing SKILL.md")
        nested = [
            path
            for path in by_path
            if path.startswith(root_prefix)
            and path != skill_path
            and path.endswith("/SKILL.md")
        ]
        if nested:
            raise BundleContractError(f"canonical Skill root {root} contains nested SKILL.md")
        agent_metadata = root_prefix + "agents/openai.yaml"
        if agent_metadata not in by_path:
            raise BundleContractError(f"canonical Skill root {root} is missing agents/openai.yaml")
        for entry in entries:
            if not entry.path.startswith(root_prefix) or not entry.path.endswith(".md"):
                continue
            text = entry.data.decode("utf-8")
            candidates: list[str] = []
            if entry.path == skill_path:
                candidates.extend(inline_resource.findall(text))
            candidates.extend(markdown_link.findall(text))
            for target in candidates:
                if "://" in target or target.startswith(("/", "#")):
                    continue
                if entry.path == skill_path and target.startswith(
                    ("references/", "agents/", "resources/", "assets/")
                ):
                    resolved = root_prefix + target
                else:
                    resolved = (
                        PurePosixPath(entry.path).parent / PurePosixPath(target)
                    ).as_posix()
                validate_portable_path(resolved, label=f"reference from {entry.path}")
                if resolved not in by_path:
                    raise BundleContractError(
                        f"referenced resource {target} from {entry.path} is missing"
                    )


def _implementation_identity(path: Path, relative: Path, role: str) -> dict[str, Any]:
    data = _read_regular_file(path, relative.as_posix(), maximum=2 * 1024 * 1024)
    _validate_runtime_text(data, relative.as_posix())
    return {
        "path": relative.as_posix(),
        "role": role,
        "size": len(data),
        "sha256": _sha256(data),
    }


def validate_derived_plugin_manifest(document: Any) -> dict[str, str]:
    manifest = _exact_object(
        document,
        {"name", "version", "description", "skills"},
        "derived plugin manifest",
    )
    if FORBIDDEN_DERIVED_MANIFEST_FIELDS & set(manifest):
        raise BundleContractError("derived plugin manifest contains a forbidden full-profile field")
    for key in ("name", "description"):
        if type(manifest[key]) is not str or not manifest[key]:
            raise BundleContractError(f"derived plugin manifest {key} must be a non-empty string")
    if type(manifest["version"]) is not str or SEMVER_PATTERN.fullmatch(manifest["version"]) is None:
        raise BundleContractError("derived plugin manifest version must be strict SemVer")
    if manifest["skills"] != "./skills/":
        raise BundleContractError("derived plugin manifest skills must be './skills/'")
    return manifest


def inspect_source(
    source_repository: Path,
    source_commit: str,
    expected_source_tree: str,
    *,
    schema_path: Path,
    entrypoint_path: Path,
    module_path: Path | None = None,
) -> BundleInputs:
    """Freeze and inspect all Git-object and implementation inputs."""
    if OID_PATTERN.fullmatch(source_commit) is None:
        raise BundleContractError("source commit must be a full lowercase 40-hex OID")
    if OID_PATTERN.fullmatch(expected_source_tree) is None:
        raise BundleContractError("expected source tree must be a full lowercase 40-hex OID")
    schema, schema_bytes, contract = load_bundle_schema(schema_path)
    source = GitObjectSource(source_repository)
    if source.object_type(source_commit) != "commit":
        raise BundleContractError("source OID must identify a commit")
    actual_tree = source.tree_for_commit(source_commit)
    if actual_tree != expected_source_tree:
        raise BundleContractError(
            f"source tree mismatch: expected {expected_source_tree}, found {actual_tree}"
        )
    if source.object_type(expected_source_tree) != "tree":
        raise BundleContractError("expected source tree OID must identify a tree")
    source_status = source.status()
    if source_status:
        raise BundleContractError(
            "runtime path contains dirty, untracked, or ignored working-tree state"
        )

    frozen_bindings = contract["contractBindings"]
    artifact_bytes: dict[str, bytes] = {}
    for key in PROFILE_ARTIFACT_KEYS:
        binding = frozen_bindings[key]
        entry = source.read_file(source_commit, binding["path"])
        artifact_bytes[key] = entry.data
        if _sha256(entry.data) != binding["sha256"]:
            raise BundleContractError(f"stale {key} digest or source bytes")

    profile = _load_json_bytes(artifact_bytes["profileContract"], "profile contract")
    benchmark = _load_json_bytes(artifact_bytes["benchmark"], "no-Hook benchmark")
    _load_json_bytes(artifact_bytes["responseSchema"], "model response schema")
    contract_versions = _load_contract_versions(artifact_bytes["goldenSet"])

    if profile.get("profileId") != PROFILE_ID or benchmark.get("profileId") != PROFILE_ID:
        raise BundleContractError("profile identifier drifted from the v1 bundle contract")
    package = profile.get("package")
    if type(package) is not dict or package.get("model") != "deterministic-derived-package":
        raise BundleContractError("profile no longer selects a deterministic derived package")
    if package.get("canonicalSkillRoot") != "skills" or package.get("editableSkillSourceCount") != 1:
        raise BundleContractError("profile must retain one canonical editable skills/ source")
    if package.get("includedRuntimeSurface") != "canonical-skills":
        raise BundleContractError("profile runtime inventory no longer owns all canonical Skills")
    if package.get("excludedRuntimeSurfaces") != ["hooks", "full-profile-host-wrappers"]:
        raise BundleContractError("profile excluded runtime surfaces drifted")

    for benchmark_key, artifact_key in (
        ("profileContract", "profileContract"),
        ("caseFile", "goldenSet"),
        ("responseSchema", "responseSchema"),
    ):
        binding = benchmark.get(benchmark_key)
        frozen = frozen_bindings[artifact_key]
        if binding != frozen:
            raise BundleContractError(f"benchmark {benchmark_key} binding drifted")
    host_case_sets = benchmark.get("hostCaseSets")
    if type(host_case_sets) is not list or len(host_case_sets) != 2:
        raise BundleContractError("benchmark must contain two ordered host case sets")
    compact_host_sets: list[dict[str, str]] = []
    for index, case_set in enumerate(host_case_sets):
        computed = _host_case_set_sha256(case_set, contract_versions)
        expected = frozen_bindings["hostCaseSets"][index]
        actual = {
            "id": case_set.get("id"),
            "host": case_set.get("host"),
            "sha256": case_set.get("sha256"),
        }
        if actual != expected or computed != expected["sha256"]:
            raise BundleContractError(f"stale hostCaseSet digest for {expected['host']}")
        compact_host_sets.append(actual)

    source_documents: dict[str, dict[str, Any]] = {}
    for path in SOURCE_SUPPORT_PATHS:
        source_documents[path] = _load_json_bytes(
            source.read_file(source_commit, path).data,
            path,
        )
    full_manifest = source_documents[".codex-plugin/plugin.json"]
    identity = source_documents["evidence/runtime-identity.json"]
    if identity.get("repositoryPolicyRevision") != contract["sourceRepositoryPolicyRevision"]:
        raise BundleContractError("source repositoryPolicyRevision does not match bundle schema")
    plugin_version = identity.get("pluginVersion")
    if type(plugin_version) is not str or SEMVER_PATTERN.fullmatch(plugin_version) is None:
        raise BundleContractError("source pluginVersion must be strict SemVer")
    runtime_contract = identity.get("runtimeContract")
    if type(runtime_contract) is not dict:
        raise BundleContractError("source runtime identity is missing runtimeContract")
    full_profile_digest = runtime_contract.get("digest")
    if type(full_profile_digest) is not str or DIGEST_PATTERN.fullmatch(full_profile_digest) is None:
        raise BundleContractError("source full-profile runtime digest is invalid")
    if runtime_contract.get("recordCount") != 61:
        raise BundleContractError("source installed input count must remain 61")
    minimal_manifest = {
        "name": full_manifest.get("name"),
        "version": plugin_version,
        "description": full_manifest.get("description"),
        "skills": full_manifest.get("skills"),
    }
    minimal_manifest = validate_derived_plugin_manifest(minimal_manifest)
    if full_manifest.get("version") != plugin_version:
        raise BundleContractError("source manifest and runtime identity versions disagree")
    identifier = profile.get("identifier")
    if type(identifier) is not dict or identifier.get("owner") != minimal_manifest["name"]:
        raise BundleContractError("profile owner and canonical plugin name disagree")
    minimal_manifest_bytes = _pretty_json_bytes(minimal_manifest)

    profile_skills = profile.get("skills")
    if type(profile_skills) is not list:
        raise BundleContractError("profile skills inventory must be an array")
    skill_roots: list[str] = []
    for index, item in enumerate(profile_skills):
        if type(item) is not dict or type(item.get("id")) is not str:
            raise BundleContractError(f"profile skills[{index}] must declare an ID")
        skill_roots.append(item["id"])
    if len(skill_roots) != contract["runtimeInventory"]["directSkillRoots"]:
        raise BundleContractError("profile direct Skill root count drifted")
    if len(skill_roots) != len(set(skill_roots)):
        raise BundleContractError("profile Skill inventory contains duplicates")

    runtime_files = source.list_files(source_commit, "skills")
    inventory = contract["runtimeInventory"]
    if len(runtime_files) > MAX_RUNTIME_FILES:
        raise BundleContractError("runtime file count exceeds the builder safety maximum")
    if len(runtime_files) != inventory["runtimeFiles"]:
        raise BundleContractError("runtime file count drifted from the frozen bundle inventory")
    total_bytes = sum(entry.size for entry in runtime_files)
    if total_bytes > MAX_RUNTIME_BYTES:
        raise BundleContractError("runtime byte count exceeds the builder safety maximum")
    if total_bytes != inventory["runtimeBytes"]:
        raise BundleContractError("runtime byte count drifted from the frozen bundle inventory")
    paths = tuple(entry.path for entry in runtime_files)
    validate_path_set(paths, label="runtime source paths")
    roots = sorted({PurePosixPath(path).parts[1] for path in paths})
    if roots != sorted(skill_roots):
        raise BundleContractError("tracked Skill roots differ from the Phase 1 inventory")
    allowed_extensions = set(inventory["allowedExtensions"])
    records: list[dict[str, Any]] = []
    for entry in runtime_files:
        if entry.size > MAX_RUNTIME_FILE_BYTES:
            raise BundleContractError(f"runtime file {entry.path} exceeds the per-file limit")
        if PurePosixPath(entry.path).suffix not in allowed_extensions:
            raise BundleContractError(f"runtime file {entry.path} has an unapproved extension")
        _validate_runtime_text(entry.data, entry.path)
        records.append(
            {
                "path": entry.path,
                "kind": _runtime_kind(entry.path),
                "mode": entry.mode,
                "size": entry.size,
                "sha256": _sha256(entry.data),
            }
        )
    _validate_reference_closure(runtime_files, tuple(skill_roots))

    module_path = module_path or Path(__file__)
    behavior_dependencies = (
        _implementation_identity(entrypoint_path, ENTRYPOINT_RELATIVE, "entrypoint"),
        _implementation_identity(module_path, MODULE_RELATIVE, "implementation"),
        {
            "path": SCHEMA_RELATIVE.as_posix(),
            "role": "contract-schema",
            "size": len(schema_bytes),
            "sha256": _sha256(schema_bytes),
        },
    )
    contract_bindings = {
        "profileContract": dict(frozen_bindings["profileContract"]),
        "goldenSet": dict(frozen_bindings["goldenSet"]),
        "responseSchema": dict(frozen_bindings["responseSchema"]),
        "benchmark": dict(frozen_bindings["benchmark"]),
        "hostCaseSets": compact_host_sets,
        "bundleSchema": {
            "path": SCHEMA_RELATIVE.as_posix(),
            "sha256": _sha256(schema_bytes),
        },
    }
    return BundleInputs(
        source=source,
        source_commit=source_commit,
        source_tree=expected_source_tree,
        source_status=source_status,
        schema=schema,
        schema_bytes=schema_bytes,
        schema_contract=contract,
        plugin_version=plugin_version,
        source_repository_policy_revision=identity["repositoryPolicyRevision"],
        full_profile_runtime_digest=full_profile_digest,
        minimal_manifest=minimal_manifest,
        minimal_manifest_bytes=minimal_manifest_bytes,
        contract_bindings=contract_bindings,
        runtime_records=tuple(records),
        runtime_files=runtime_files,
        behavior_dependencies=behavior_dependencies,
    )


def _profile_runtime_digest(inputs: BundleInputs) -> str:
    payload = {
        "domainSeparator": "axiom-profile-runtime",
        "schemaVersion": BUNDLE_SCHEMA_VERSION,
        "profileId": PROFILE_ID,
        "runtimeCanonicalizationVersion": RUNTIME_CANONICALIZATION_VERSION,
        "derivedPluginManifestBehavior": {
            "name": inputs.minimal_manifest["name"],
            "skills": inputs.minimal_manifest["skills"],
            "hooks": "absent",
            "apps": "absent",
            "mcpServers": "absent",
        },
        "runtimeFiles": list(inputs.runtime_records),
    }
    return _digest_identity(_canonical_json_bytes(payload))


def _runtime_canonicalization() -> dict[str, Any]:
    return {
        "version": RUNTIME_CANONICALIZATION_VERSION,
        "domainSeparator": "axiom-profile-runtime",
        "pathOrder": "utf-8-bytewise",
        "pathNormalization": "utf-8-nfc-preserved",
        "textEncoding": "utf-8",
        "lineEndings": "lf",
        "finalNewline": "required",
        "fileMode": "100644",
        "directoryMode": "040755",
        "serialization": "canonical-json-sort-keys-v1",
    }


def _transport(plugin_version: str) -> dict[str, Any]:
    return {
        "directoryRoot": "plugin/",
        "archiveFilename": f"axiom-{PROFILE_ID}-{plugin_version}.zip",
        "archiveContentRoot": ".",
        "format": "zip",
        "compression": "stored",
        "memberOrder": "utf-8-bytewise",
        "timestamp": ZIP_TIMESTAMP_TEXT,
        "fileMode": "100644",
        "directoryMode": "040755",
        "creatorSystem": "unix",
        "explicitDirectoryMembers": False,
        "extraFields": "empty",
        "comments": "empty",
        "uidGid": "absent",
        "encryption": False,
        "dataDescriptor": False,
        "archiveDigestLocation": BUNDLE_ENVELOPE_NAME,
    }


def _builder_identity(inputs: BundleInputs) -> dict[str, Any]:
    return {
        "id": BUILDER_ID,
        "version": BUILDER_VERSION,
        "implementation": "python-standard-library-only",
        "gitAccess": "read-only-commit-tree-blob",
        "network": "disabled",
        "behaviorDependencies": list(inputs.behavior_dependencies),
    }


def create_bundle_manifest(inputs: BundleInputs) -> dict[str, Any]:
    """Create the final self-bound bundle manifest document."""
    profile_runtime_digest = _profile_runtime_digest(inputs)
    if profile_runtime_digest == inputs.full_profile_runtime_digest:
        raise BundleContractError("full-profile runtime digest cannot be reused as profileRuntimeDigest")
    document: dict[str, Any] = {
        "schemaVersion": BUNDLE_SCHEMA_VERSION,
        "kind": "axiom-hook-independent-derived-bundle",
        "profileId": PROFILE_ID,
        "pluginVersion": inputs.plugin_version,
        "repositoryPolicyRevision": inputs.schema_contract[
            "candidateRepositoryPolicyRevision"
        ],
        "source": {
            "repository": SOURCE_REPOSITORY_SLUG,
            "commit": inputs.source_commit,
            "tree": inputs.source_tree,
            "repositoryPolicyRevision": inputs.source_repository_policy_revision,
        },
        "contractBindings": inputs.contract_bindings,
        "runtimeCanonicalization": _runtime_canonicalization(),
        "derivedPluginManifest": {
            "path": ".codex-plugin/plugin.json",
            "size": len(inputs.minimal_manifest_bytes),
            "sha256": _sha256(inputs.minimal_manifest_bytes),
            "fields": inputs.minimal_manifest,
        },
        "runtimeFiles": list(inputs.runtime_records),
        "profileRuntimeDigest": profile_runtime_digest,
        "includedSurfaces": list(INCLUDED_SURFACES),
        "excludedSurfaces": list(EXCLUDED_SURFACES),
        "builder": _builder_identity(inputs),
        "transport": _transport(inputs.plugin_version),
    }
    document["bundleManifestDigest"] = _digest_identity(_canonical_json_bytes(document))
    validate_bundle_manifest(document, full_profile_runtime_digest=inputs.full_profile_runtime_digest)
    return document


def validate_bundle_manifest(
    document: Any,
    *,
    full_profile_runtime_digest: str | None = None,
) -> dict[str, Any]:
    """Validate the closed manifest and its one-field self-reference rule."""
    manifest = _exact_object(
        document,
        {
            "schemaVersion",
            "kind",
            "profileId",
            "pluginVersion",
            "repositoryPolicyRevision",
            "source",
            "contractBindings",
            "runtimeCanonicalization",
            "derivedPluginManifest",
            "runtimeFiles",
            "profileRuntimeDigest",
            "includedSurfaces",
            "excludedSurfaces",
            "builder",
            "transport",
            "bundleManifestDigest",
        },
        "BUNDLE-MANIFEST.json",
    )
    if manifest["schemaVersion"] != BUNDLE_SCHEMA_VERSION:
        raise BundleContractError("bundle manifest schemaVersion drifted")
    if manifest["kind"] != "axiom-hook-independent-derived-bundle":
        raise BundleContractError("bundle manifest kind drifted")
    if manifest["profileId"] != PROFILE_ID:
        raise BundleContractError("bundle manifest profileId drifted")
    if type(manifest["pluginVersion"]) is not str or SEMVER_PATTERN.fullmatch(manifest["pluginVersion"]) is None:
        raise BundleContractError("bundle manifest pluginVersion must be strict SemVer")
    if manifest["repositoryPolicyRevision"] != 6:
        raise BundleContractError("bundle manifest repositoryPolicyRevision must be 6")
    source = _exact_object(
        manifest["source"],
        {"repository", "commit", "tree", "repositoryPolicyRevision"},
        "bundle manifest source",
    )
    if source["repository"] != SOURCE_REPOSITORY_SLUG:
        raise BundleContractError("bundle manifest source repository drifted")
    if OID_PATTERN.fullmatch(str(source["commit"])) is None or OID_PATTERN.fullmatch(str(source["tree"])) is None:
        raise BundleContractError("bundle manifest source commit and tree must be full OIDs")
    if source["repositoryPolicyRevision"] != 5:
        raise BundleContractError("bundle manifest source repositoryPolicyRevision must be 5")
    derived = _exact_object(
        manifest["derivedPluginManifest"],
        {"path", "size", "sha256", "fields"},
        "bundle manifest derivedPluginManifest",
    )
    if derived["path"] != ".codex-plugin/plugin.json":
        raise BundleContractError("derived plugin manifest path drifted")
    fields = validate_derived_plugin_manifest(derived["fields"])
    raw_manifest = _pretty_json_bytes(fields)
    if derived["size"] != len(raw_manifest) or derived["sha256"] != _sha256(raw_manifest):
        raise BundleContractError("derived plugin manifest raw identity mismatch")
    records = manifest["runtimeFiles"]
    if type(records) is not list or len(records) != 50:
        raise BundleContractError("bundle manifest must contain exactly 50 runtime records")
    record_paths: list[str] = []
    for index, value in enumerate(records):
        record = _exact_object(value, {"path", "kind", "mode", "size", "sha256"}, f"runtimeFiles[{index}]")
        record_paths.append(record["path"])
        if record["kind"] not in {"skill", "agent-metadata", "reference", "resource"}:
            raise BundleContractError(f"runtimeFiles[{index}].kind is invalid")
        if record["mode"] != "100644":
            raise BundleContractError(f"runtimeFiles[{index}].mode must be 100644")
        if type(record["size"]) is not int or not 0 < record["size"] <= MAX_RUNTIME_FILE_BYTES:
            raise BundleContractError(f"runtimeFiles[{index}].size is invalid")
        if SHA256_PATTERN.fullmatch(str(record["sha256"])) is None:
            raise BundleContractError(f"runtimeFiles[{index}].sha256 is invalid")
    validate_path_set(tuple(record_paths), label="bundle manifest runtime paths")
    profile_digest = manifest["profileRuntimeDigest"]
    if type(profile_digest) is not str or DIGEST_PATTERN.fullmatch(profile_digest) is None:
        raise BundleContractError("profileRuntimeDigest must be a SHA-256 identity")
    if full_profile_runtime_digest is not None and profile_digest == full_profile_runtime_digest:
        raise BundleContractError("profileRuntimeDigest must not reuse the full-profile digest")
    stored_digest = manifest["bundleManifestDigest"]
    if type(stored_digest) is not str or DIGEST_PATTERN.fullmatch(stored_digest) is None:
        raise BundleContractError("bundleManifestDigest must be a SHA-256 identity")
    digest_input = dict(manifest)
    del digest_input["bundleManifestDigest"]
    if stored_digest != _digest_identity(_canonical_json_bytes(digest_input)):
        raise BundleContractError("bundleManifestDigest self-reference validation failed")
    builder = _exact_object(
        manifest["builder"],
        {"id", "version", "implementation", "gitAccess", "network", "behaviorDependencies"},
        "bundle manifest builder",
    )
    if (
        builder["id"] != BUILDER_ID
        or builder["version"] != BUILDER_VERSION
        or builder["implementation"] != "python-standard-library-only"
        or builder["gitAccess"] != "read-only-commit-tree-blob"
        or builder["network"] != "disabled"
    ):
        raise BundleContractError("bundle builder identity drifted")
    dependencies = builder["behaviorDependencies"]
    if type(dependencies) is not list or [item.get("role") for item in dependencies if type(item) is dict] != [
        "entrypoint",
        "implementation",
        "contract-schema",
    ]:
        raise BundleContractError("builder behavior dependency closure drifted")
    return manifest


def _file_map(inputs: BundleInputs, manifest_bytes: bytes) -> dict[str, bytes]:
    files = {entry.path: entry.data for entry in inputs.runtime_files}
    files[".codex-plugin/plugin.json"] = inputs.minimal_manifest_bytes
    files[BUNDLE_MANIFEST_NAME] = manifest_bytes
    ordered_paths = tuple(sorted(files, key=lambda item: item.encode("utf-8")))
    validate_path_set(ordered_paths, label="bundle file paths")
    return {path: files[path] for path in ordered_paths}


def build_archive_bytes(files: dict[str, bytes]) -> bytes:
    """Serialize exact bundle members as a deterministic ZIP_STORED archive."""
    ordered_paths = tuple(files)
    validate_path_set(ordered_paths, label="ZIP member paths")
    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_STORED,
        allowZip64=False,
    ) as archive:
        archive.comment = b""
        for path in ordered_paths:
            info = zipfile.ZipInfo(path, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.create_version = 20
            info.extract_version = 10
            info.external_attr = FILE_MODE << 16
            info.internal_attr = 0
            info.extra = b""
            info.comment = b""
            info.flag_bits = 0
            archive.writestr(info, files[path])
    data = output.getvalue()
    if len(data) > MAX_ARCHIVE_BYTES:
        raise BundleContractError("final ZIP exceeds the 4 MiB safety limit")
    return data


def validate_archive_bytes(data: bytes, expected_files: dict[str, bytes]) -> str:
    """Validate ZIP bytes against the complete transport contract."""
    if len(data) > MAX_ARCHIVE_BYTES:
        raise BundleContractError("final ZIP exceeds the 4 MiB safety limit")
    try:
        with zipfile.ZipFile(io.BytesIO(data), mode="r") as archive:
            if archive.comment:
                raise BundleContractError("ZIP archive comment must be empty")
            infos = archive.infolist()
            names = tuple(info.filename for info in infos)
            if names != tuple(expected_files):
                raise BundleContractError("ZIP member order or file set drifted")
            if len(names) != len(set(names)):
                raise BundleContractError("ZIP contains a duplicate member")
            validate_path_set(names, label="ZIP member paths")
            for info in infos:
                if info.is_dir() or info.filename.endswith("/"):
                    raise BundleContractError("ZIP must not contain explicit directory members")
                if info.date_time != ZIP_TIMESTAMP:
                    raise BundleContractError("ZIP member timestamp drifted")
                if info.compress_type != zipfile.ZIP_STORED:
                    raise BundleContractError("ZIP member compression must be ZIP_STORED")
                if info.create_system != 3:
                    raise BundleContractError("ZIP creator metadata must be Unix")
                if (info.external_attr >> 16) != FILE_MODE:
                    raise BundleContractError("ZIP member mode must be 100644")
                if info.extra or info.comment:
                    raise BundleContractError("ZIP member extra fields and comments must be empty")
                if info.flag_bits & 0x1:
                    raise BundleContractError("ZIP encryption is forbidden")
                if info.flag_bits & 0x8:
                    raise BundleContractError("ZIP data descriptors are forbidden")
                if archive.read(info) != expected_files[info.filename]:
                    raise BundleContractError(f"ZIP member bytes drifted for {info.filename}")
    except (OSError, zipfile.BadZipFile) as error:
        raise BundleContractError(f"invalid deterministic ZIP: {error}") from error
    return _sha256(data)


def _create_envelope(
    inputs: BundleInputs,
    manifest: dict[str, Any],
    files: dict[str, bytes],
    archive_bytes: bytes,
) -> dict[str, Any]:
    return {
        "schemaVersion": "1",
        "kind": "axiom-hook-independent-bundle-envelope",
        "profileId": PROFILE_ID,
        "pluginVersion": inputs.plugin_version,
        "source": {
            "commit": inputs.source_commit,
            "tree": inputs.source_tree,
        },
        "profileRuntimeDigest": manifest["profileRuntimeDigest"],
        "bundleManifestDigest": manifest["bundleManifestDigest"],
        "archive": {
            "filename": manifest["transport"]["archiveFilename"],
            "size": len(archive_bytes),
            "sha256": _sha256(archive_bytes),
        },
        "directory": {
            "root": "plugin/",
            "fileCount": len(files),
            "totalBytes": sum(len(data) for data in files.values()),
        },
        "complete": True,
    }


def validate_envelope(
    envelope: Any,
    *,
    manifest: dict[str, Any],
    files: dict[str, bytes],
    archive_bytes: bytes,
) -> dict[str, Any]:
    document = _exact_object(
        envelope,
        {
            "schemaVersion",
            "kind",
            "profileId",
            "pluginVersion",
            "source",
            "profileRuntimeDigest",
            "bundleManifestDigest",
            "archive",
            "directory",
            "complete",
        },
        BUNDLE_ENVELOPE_NAME,
    )
    source = _exact_object(document["source"], {"commit", "tree"}, "bundle envelope source")
    archive = _exact_object(document["archive"], {"filename", "size", "sha256"}, "bundle envelope archive")
    directory = _exact_object(document["directory"], {"root", "fileCount", "totalBytes"}, "bundle envelope directory")
    expected = {
        "schemaVersion": "1",
        "kind": "axiom-hook-independent-bundle-envelope",
        "profileId": manifest["profileId"],
        "pluginVersion": manifest["pluginVersion"],
        "source": {
            "commit": manifest["source"]["commit"],
            "tree": manifest["source"]["tree"],
        },
        "profileRuntimeDigest": manifest["profileRuntimeDigest"],
        "bundleManifestDigest": manifest["bundleManifestDigest"],
        "archive": {
            "filename": manifest["transport"]["archiveFilename"],
            "size": len(archive_bytes),
            "sha256": _sha256(archive_bytes),
        },
        "directory": {
            "root": "plugin/",
            "fileCount": len(files),
            "totalBytes": sum(len(data) for data in files.values()),
        },
        "complete": True,
    }
    if document != expected or source != expected["source"] or archive != expected["archive"] or directory != expected["directory"]:
        raise BundleContractError("bundle envelope does not bind the exact completed archive and directory")
    return document


def _write_plugin_tree(root: Path, files: dict[str, bytes]) -> None:
    root.mkdir(mode=0o755)
    os.chmod(root, 0o755)
    created_directories = {root}
    for relative_path, data in files.items():
        destination = root.joinpath(*PurePosixPath(relative_path).parts)
        missing: list[Path] = []
        parent = destination.parent
        while parent not in created_directories and parent != root.parent:
            missing.append(parent)
            parent = parent.parent
        for directory in reversed(missing):
            directory.mkdir(mode=0o755)
            os.chmod(directory, 0o755)
            created_directories.add(directory)
        with destination.open("xb") as handle:
            handle.write(data)
        os.chmod(destination, 0o644)


def _read_plugin_tree(root: Path) -> dict[str, bytes]:
    if root.is_symlink() or not root.is_dir():
        raise BundleContractError("generated plugin root must be an ordinary directory")
    if stat.S_IMODE(root.stat().st_mode) != 0o755:
        raise BundleContractError("generated plugin root mode must be 0755")
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        relative = path.relative_to(root).as_posix()
        validate_portable_path(relative, label="generated plugin path")
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise BundleContractError(f"generated plugin path {relative} must not be a symlink")
        if stat.S_ISDIR(metadata.st_mode):
            if stat.S_IMODE(metadata.st_mode) != 0o755:
                raise BundleContractError(f"generated directory {relative} mode must be 0755")
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise BundleContractError(f"generated path {relative} must be a regular file")
        if stat.S_IMODE(metadata.st_mode) != 0o644:
            raise BundleContractError(f"generated file {relative} mode must be 0644")
        files[relative] = path.read_bytes()
    return {path: files[path] for path in sorted(files, key=lambda item: item.encode("utf-8"))}


def _validate_published_outputs(
    plugin_root: Path,
    archive_path: Path,
    expected_files: dict[str, bytes],
    envelope: dict[str, Any],
) -> bytes:
    actual_files = _read_plugin_tree(plugin_root)
    if actual_files != expected_files:
        raise BundleContractError("generated directory file set or bytes drifted")
    archive_bytes = _read_regular_file(
        archive_path,
        archive_path.name,
        maximum=MAX_ARCHIVE_BYTES,
    )
    validate_archive_bytes(archive_bytes, expected_files)
    validate_envelope(
        envelope,
        manifest=_load_json_bytes(expected_files[BUNDLE_MANIFEST_NAME], BUNDLE_MANIFEST_NAME),
        files=expected_files,
        archive_bytes=archive_bytes,
    )
    return archive_bytes


def _remove_builder_owned(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(metadata.st_mode):
        path.unlink()
    elif stat.S_ISDIR(metadata.st_mode):
        shutil.rmtree(path)
    elif stat.S_ISREG(metadata.st_mode):
        path.unlink()


def build_bundle(
    source_repository: Path,
    source_commit: str,
    expected_source_tree: str,
    destination: Path,
    *,
    schema_path: Path | None = None,
    entrypoint_path: Path | None = None,
    module_path: Path | None = None,
) -> BuildResult:
    """Build one deterministic directory, ZIP, and last-published envelope."""
    source_repository = Path(source_repository)
    destination = _validate_destination(source_repository, Path(destination))
    schema_path = schema_path or REPOSITORY_ROOT / SCHEMA_RELATIVE
    entrypoint_path = entrypoint_path or REPOSITORY_ROOT / ENTRYPOINT_RELATIVE
    inputs = inspect_source(
        source_repository,
        source_commit,
        expected_source_tree,
        schema_path=schema_path,
        entrypoint_path=entrypoint_path,
        module_path=module_path,
    )
    manifest = create_bundle_manifest(inputs)
    manifest_bytes = _pretty_json_bytes(manifest)
    if len(manifest_bytes) > MAX_BUNDLE_MANIFEST_BYTES:
        raise BundleContractError("BUNDLE-MANIFEST.json exceeds the 512 KiB limit")
    files = _file_map(inputs, manifest_bytes)
    archive_bytes = build_archive_bytes(files)
    validate_archive_bytes(archive_bytes, files)
    envelope = _create_envelope(inputs, manifest, files, archive_bytes)
    envelope_bytes = _pretty_json_bytes(envelope)
    archive_filename = manifest["transport"]["archiveFilename"]

    staging = destination / STAGING_DIRECTORY_NAME
    plugin_output = destination / PLUGIN_DIRECTORY_NAME
    archive_output = destination / archive_filename
    envelope_output = destination / BUNDLE_ENVELOPE_NAME
    for output in (staging, plugin_output, archive_output, envelope_output):
        if output.exists() or output.is_symlink():
            raise BundleContractError(f"fixed output already exists: {output.name}")
    published: list[Path] = []
    try:
        staging.mkdir(mode=0o700)
        staged_plugin = staging / PLUGIN_DIRECTORY_NAME
        staged_archive = staging / archive_filename
        staged_envelope = staging / BUNDLE_ENVELOPE_NAME
        _write_plugin_tree(staged_plugin, files)
        with staged_archive.open("xb") as handle:
            handle.write(archive_bytes)
        os.chmod(staged_archive, 0o644)
        with staged_envelope.open("xb") as handle:
            handle.write(envelope_bytes)
        os.chmod(staged_envelope, 0o644)
        _validate_published_outputs(staged_plugin, staged_archive, files, envelope)
        inputs.verify_source_unchanged()
        if set(destination.iterdir()) != {staging}:
            raise BundleContractError("destination changed while the bundle was staged")

        os.replace(staged_plugin, plugin_output)
        published.append(plugin_output)
        os.replace(staged_archive, archive_output)
        published.append(archive_output)
        _validate_published_outputs(plugin_output, archive_output, files, envelope)
        inputs.verify_source_unchanged()
        os.replace(staged_envelope, envelope_output)
        published.append(envelope_output)
        staging.rmdir()
    except Exception:
        for output in reversed(published):
            _remove_builder_owned(output)
        _remove_builder_owned(staging)
        raise

    result = BuildResult(
        profile_runtime_digest=manifest["profileRuntimeDigest"],
        bundle_manifest_digest=manifest["bundleManifestDigest"],
        archive_sha256=_sha256(archive_bytes),
        archive_size=len(archive_bytes),
        archive_filename=archive_filename,
        directory_file_count=len(files),
        directory_total_bytes=sum(len(data) for data in files.values()),
        bundle_manifest=manifest,
        envelope=envelope,
    )
    return result


def _filesystem_runtime(
    root: Path,
    expected_inventory: dict[str, Any],
) -> tuple[tuple[dict[str, Any], ...], tuple[GitEntry, ...]]:
    skills_root = root / "skills"
    if not skills_root.is_dir() or skills_root.is_symlink():
        raise BundleContractError("current skills/ must be an ordinary directory")
    entries: list[GitEntry] = []
    for path in sorted(skills_root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        metadata = path.lstat()
        relative = path.relative_to(root).as_posix()
        if stat.S_ISLNK(metadata.st_mode):
            raise BundleContractError(f"current runtime path {relative} must not be a symlink")
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise BundleContractError(f"current runtime path {relative} must be a regular file")
        if stat.S_IMODE(metadata.st_mode) & 0o111:
            raise BundleContractError(f"current runtime path {relative} must not be executable")
        data = path.read_bytes()
        entries.append(GitEntry(relative, "100644", "blob", "0" * 40, len(data), data))
    paths = tuple(entry.path for entry in entries)
    validate_path_set(paths, label="current runtime paths")
    if len(entries) != expected_inventory["runtimeFiles"]:
        raise BundleContractError("current runtime file count differs from bundle evidence")
    if sum(entry.size for entry in entries) != expected_inventory["runtimeBytes"]:
        raise BundleContractError("current runtime bytes differ from bundle evidence")
    allowed_extensions = set(expected_inventory["allowedExtensions"])
    records: list[dict[str, Any]] = []
    for entry in entries:
        if PurePosixPath(entry.path).suffix not in allowed_extensions:
            raise BundleContractError(f"current runtime path {entry.path} has an unapproved extension")
        _validate_runtime_text(entry.data, entry.path)
        records.append(
            {
                "path": entry.path,
                "kind": _runtime_kind(entry.path),
                "mode": "100644",
                "size": entry.size,
                "sha256": _sha256(entry.data),
            }
        )
    roots = tuple(sorted({PurePosixPath(path).parts[1] for path in paths}))
    if len(roots) != expected_inventory["directSkillRoots"]:
        raise BundleContractError("current direct Skill root count differs from bundle evidence")
    _validate_reference_closure(tuple(entries), roots)
    return tuple(records), tuple(entries)


def _evidence_inputs(
    root: Path,
    evidence: dict[str, Any],
    schema: dict[str, Any],
    schema_bytes: bytes,
    contract: dict[str, Any],
) -> BundleInputs:
    manifest = evidence["bundleManifest"]
    source = manifest["source"]
    full_manifest = _load_json_bytes(
        _read_regular_file(root / ".codex-plugin/plugin.json", ".codex-plugin/plugin.json", maximum=MAX_BUNDLE_MANIFEST_BYTES),
        ".codex-plugin/plugin.json",
    )
    identity = _load_json_bytes(
        _read_regular_file(root / "evidence/runtime-identity.json", "evidence/runtime-identity.json", maximum=MAX_BUNDLE_MANIFEST_BYTES),
        "evidence/runtime-identity.json",
    )
    minimal = validate_derived_plugin_manifest(
        {
            "name": full_manifest.get("name"),
            "version": identity.get("pluginVersion"),
            "description": full_manifest.get("description"),
            "skills": full_manifest.get("skills"),
        }
    )
    records, runtime_files = _filesystem_runtime(root, contract["runtimeInventory"])
    dependencies = (
        _implementation_identity(root / ENTRYPOINT_RELATIVE, ENTRYPOINT_RELATIVE, "entrypoint"),
        _implementation_identity(root / MODULE_RELATIVE, MODULE_RELATIVE, "implementation"),
        {
            "path": SCHEMA_RELATIVE.as_posix(),
            "role": "contract-schema",
            "size": len(schema_bytes),
            "sha256": _sha256(schema_bytes),
        },
    )
    runtime_contract = identity.get("runtimeContract")
    if type(runtime_contract) is not dict:
        raise BundleContractError("current runtime identity is missing runtimeContract")
    return BundleInputs(
        source=None,  # type: ignore[arg-type]
        source_commit=source["commit"],
        source_tree=source["tree"],
        source_status=b"",
        schema=schema,
        schema_bytes=schema_bytes,
        schema_contract=contract,
        plugin_version=identity["pluginVersion"],
        source_repository_policy_revision=source["repositoryPolicyRevision"],
        full_profile_runtime_digest=runtime_contract["digest"],
        minimal_manifest=minimal,
        minimal_manifest_bytes=_pretty_json_bytes(minimal),
        contract_bindings=manifest["contractBindings"],
        runtime_records=records,
        runtime_files=runtime_files,
        behavior_dependencies=dependencies,
    )


def check_no_hook_bundle(
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> tuple[int, int]:
    """Validate tracked static evidence without writing generated output."""
    try:
        root = root.resolve()
        schema, schema_bytes, contract = load_bundle_schema(root / SCHEMA_RELATIVE)
        evidence_bytes = _read_regular_file(
            root / EVIDENCE_RELATIVE,
            EVIDENCE_RELATIVE.as_posix(),
            maximum=MAX_BUNDLE_MANIFEST_BYTES,
        )
        evidence = _load_json_bytes(evidence_bytes, EVIDENCE_RELATIVE.as_posix())
        _exact_object(
            evidence,
            {
                "schemaVersion",
                "kind",
                "profileId",
                "source",
                "candidateRepositoryPolicyRevision",
                "bundleManifest",
                "builds",
                "artifactRetention",
                "evidenceBoundary",
            },
            "no-Hook bundle evidence",
        )
        if evidence["schemaVersion"] != "1" or evidence["kind"] != "axiom-hook-independent-bundle-static-evidence":
            raise BundleContractError("no-Hook bundle evidence identity drifted")
        if evidence["profileId"] != PROFILE_ID:
            raise BundleContractError("no-Hook bundle evidence profileId drifted")
        manifest = validate_bundle_manifest(evidence["bundleManifest"])
        if evidence["source"] != manifest["source"]:
            raise BundleContractError("static evidence source differs from its bundle manifest")
        if evidence["candidateRepositoryPolicyRevision"] != 6:
            raise BundleContractError("static evidence candidate repositoryPolicyRevision must be 6")

        revision_document = _load_json_bytes(
            _read_regular_file(
                root / "evidence/repository-policy-revisions-v1.json",
                "evidence/repository-policy-revisions-v1.json",
                maximum=MAX_BUNDLE_MANIFEST_BYTES,
            ),
            "evidence/repository-policy-revisions-v1.json",
        )
        revisions = revision_document.get("revisions")
        if type(revisions) is not list or not revisions or type(revisions[-1]) is not dict:
            raise BundleContractError("repository policy revision history is unavailable")
        revision = revisions[-1]
        if (
            revision.get("revision") != 6
            or revision.get("baselineCommit") != manifest["source"]["commit"]
            or revision.get("sourceIssue") != 117
        ):
            raise BundleContractError("revision 6 does not bind the frozen Phase 2 source")

        frozen_bindings = contract["contractBindings"]
        for key in PROFILE_ARTIFACT_KEYS:
            binding = frozen_bindings[key]
            data = _read_regular_file(
                root / binding["path"],
                binding["path"],
                maximum=MAX_BUNDLE_MANIFEST_BYTES,
            )
            if _sha256(data) != binding["sha256"]:
                raise BundleContractError(f"tracked {key} bytes drifted from Phase 1")
        benchmark = _load_json_bytes(
            (root / frozen_bindings["benchmark"]["path"]).read_bytes(),
            "no-Hook benchmark",
        )
        golden = (root / frozen_bindings["goldenSet"]["path"]).read_bytes()
        versions = _load_contract_versions(golden)
        actual_host_sets = []
        for case_set in benchmark.get("hostCaseSets", []):
            actual_host_sets.append(
                {
                    "id": case_set.get("id"),
                    "host": case_set.get("host"),
                    "sha256": _host_case_set_sha256(case_set, versions),
                }
            )
        if actual_host_sets != frozen_bindings["hostCaseSets"]:
            raise BundleContractError("tracked host case-set identity drifted from Phase 1")

        inputs = _evidence_inputs(root, evidence, schema, schema_bytes, contract)
        expected_manifest = create_bundle_manifest(inputs)
        if manifest != expected_manifest:
            raise BundleContractError("tracked bundle manifest evidence is not reproducible from current inputs")
        manifest_bytes = _pretty_json_bytes(manifest)
        files = _file_map(inputs, manifest_bytes)
        archive_bytes = build_archive_bytes(files)
        validate_archive_bytes(archive_bytes, files)
        expected_envelope = _create_envelope(inputs, manifest, files, archive_bytes)

        builds = _exact_object(
            evidence["builds"],
            {
                "independentBuildCount",
                "repositoryOutsideDestinations",
                "directoryFileSetsEqual",
                "directoryBytesEqual",
                "profileRuntimeDigest",
                "bundleManifestDigest",
                "archiveSha256",
                "archiveBytesEqual",
                "envelopeSemanticFieldsEqual",
            },
            "no-Hook bundle evidence builds",
        )
        expected_builds = {
            "independentBuildCount": 2,
            "repositoryOutsideDestinations": True,
            "directoryFileSetsEqual": True,
            "directoryBytesEqual": True,
            "profileRuntimeDigest": manifest["profileRuntimeDigest"],
            "bundleManifestDigest": manifest["bundleManifestDigest"],
            "archiveSha256": _sha256(archive_bytes),
            "archiveBytesEqual": True,
            "envelopeSemanticFieldsEqual": True,
        }
        if builds != expected_builds:
            raise BundleContractError("two-build equality evidence drifted")
        if evidence.get("artifactRetention") != {
            "generatedArtifactsTracked": False,
            "generatedArtifactsRetained": False,
            "generatedArtifactsPublished": False,
            "generatedArtifactsInstalled": False,
        }:
            raise BundleContractError("generated artifact retention boundary drifted")
        if evidence.get("evidenceBoundary") != {
            "staticBundleValidation": "pass",
            "codexNoHookObservation": "not-run",
            "chatgptNoHookObservation": "not-run",
            "fullProfileInstalledObservation": "not-run",
            "claudeCodeNoHookProfile": "excluded",
            "installation": "not-run",
            "marketplace": "not-run",
            "portal": "not-run",
            "officialDirectory": "not-run",
            "tagReleaseLatestPublication": "not-run",
            "fullProfileDigestReused": False,
        }:
            raise BundleContractError("static evidence boundary drifted")
        if evidence.get("bundleManifest") != manifest:
            raise BundleContractError("static evidence bundle manifest drifted")
        if evidence.get("source") != expected_envelope["source"] | {
            "repository": SOURCE_REPOSITORY_SLUG,
            "repositoryPolicyRevision": 5,
        }:
            raise BundleContractError("static evidence source provenance drifted")
        return len(inputs.runtime_records), builds["independentBuildCount"]
    except (BundleContractError, OSError, KeyError, TypeError, ValueError) as error:
        failures.append(f"no-Hook bundle validation failed: {error}")
        return 0, 0


__all__ = [
    "BUNDLE_ENVELOPE_NAME",
    "BUNDLE_MANIFEST_NAME",
    "BuildResult",
    "BundleContractError",
    "GitObjectSource",
    "PROFILE_ID",
    "build_archive_bytes",
    "build_bundle",
    "check_no_hook_bundle",
    "create_bundle_manifest",
    "inspect_source",
    "load_bundle_schema",
    "validate_archive_bytes",
    "validate_bundle_manifest",
    "validate_derived_plugin_manifest",
    "validate_envelope",
    "validate_path_set",
    "validate_portable_path",
]
