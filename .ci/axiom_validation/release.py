"""Tag-driven release of one Axiom version.

A maintainer pushes a strict SemVer tag ``vX.Y.Z`` on a GitHub-signed ``main``
commit. The Release workflow runs this module on that tag. Every gate reads
GitHub and the tagged tree before the first write:

1. the tag is ``vX.Y.Z``, and an annotated tag carries a verified signature;
2. the tagged commit is on ``main`` history and has a valid signature made
   with GitHub's signing key;
3. the required checks and ``Verify signed main history`` succeeded on it;
4. the version is the immediate patch, minor, or major successor of the
   highest existing release tag below it, which is GitHub Latest's tag unless
   a later attempt failed after its tag was pushed;
5. the installed-runtime digest differs from the one Latest's evidence asset
   records, except for the bootstrap release that creates the release
   branch, which may carry Latest's runtime unchanged;
6. neither a Release nor a ``release``-branch commit exists for this version,
   and the ``release`` branch still descends from its root and holds only
   ``plugin/`` and ``LICENSE``;
7. the tagged tree with both plugin manifests stamped passes the repository
   checks in a disposable worktree.

Only then does it write: one GitHub-signed ``createCommitOnBranch`` commit that
fast-forwards ``release`` to the stamped ``plugin/`` tree and ``LICENSE``, the
Draft with the plugin zip, the immutable publisher run, which adds the one
evidence asset, and the published-release observation. A failure after the tag
exists leaves no Release; the next attempt uses the next version.

The ``release`` branch never carries ``.github/workflows/``: ``GITHUB_TOKEN``
cannot write workflow files. When the branch is absent, it starts at
``main``'s root commit, whose tree holds only ``LICENSE``.

Standard library only; it runs no AI model or agent.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from .context import REPOSITORY_ROOT, display_path
from .manifests import MANIFEST_FILES, RELEASE_BRANCH
from .release_versions import parse_production_release_version
from .runtime_identity import INPUT_MANIFEST_RELATIVE, compute_runtime_contract
from .yaml_subset import (
    CanonicalYamlError,
    CanonicalYamlScalar,
    parse_canonical_yaml_document,
)


API_VERSION = "2026-03-10"
GITHUB_ACTIONS_APP_ID = 15368
REPOSITORY_URL = "https://github.com/wheakerd/axiom"
RELEASE_BRANCH_REF = f"refs/heads/{RELEASE_BRANCH}"
# main's root commit; its tree holds only LICENSE. An absent release branch
# starts here, so the branch never contains .github/workflows/.
RELEASE_BRANCH_ROOT = "fb86eb61e8161642c627bcce84c214730634b570"
CODEX_MANIFEST = MANIFEST_FILES[0]
REQUIRED_CHECKS = (
    "repository-guards",
    "unit-and-integration-tests",
    "hook-runtime-gate",
    "Verify signed main history",
)
CREATED_TAG_CHECK = "Verify created release tag"
RELEASE_BRANCH_CHECK = "Verify release branch commit"
PUBLISHED_RELEASE_CHECK = "Observe published immutable release"
PUBLISHER_WORKFLOW = "publish-immutable-release.yml"
SIGNATURE_GUARD_WORKFLOW = "release-signature-guard.yml"
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "release.yml"
RELEASE_NOTES_MAX_CHARACTERS = 125_000
FILE_MODE = "100644"
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
POLL_SECONDS = 20
CHECK_TIMEOUT_SECONDS = 75 * 60
RUN_DISCOVERY_SECONDS = 5 * 60
RUN_TIMEOUT_SECONDS = 45 * 60
CHECK_OUTPUT_LIMIT = 4000
OID_PATTERN = re.compile(r"[0-9a-f]{40}")
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
RELEASE_TAG_PATTERN = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
SIGNATURE_BLOCK = re.compile(
    r"(?:\A|\n)-----BEGIN (?:PGP|SSH) SIGNATURE-----\n.*\Z", re.DOTALL
)
CREATE_COMMIT_MUTATION = (
    "mutation($input: CreateCommitOnBranchInput!) { "
    "createCommitOnBranch(input: $input) { commit { oid } } }"
)
SIGNATURE_QUERY = (
    "query($owner: String!, $name: String!, $oid: GitObjectID!) { "
    "repository(owner: $owner, name: $name) { object(oid: $oid) { "
    "... on Commit { oid signature { isValid state wasSignedByGitHub } } } } }"
)


class ReleaseError(RuntimeError):
    """A fail-closed release decision."""


class Api(Protocol):
    def get(self, path: str, *, allow_not_found: bool = False) -> Any: ...

    def download(self, path: str) -> bytes: ...

    def post(self, path: str, payload: dict[str, Any]) -> Any: ...

    def upload(self, url: str, data: bytes, content_type: str) -> Any: ...

    def graphql(self, query: str, variables: dict[str, Any]) -> Any: ...


class GitHubClient:
    """No-retry GitHub REST, GraphQL, download, and upload client for one token."""

    def __init__(
        self,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        user_agent: str = "axiom-release",
    ) -> None:
        if not token:
            raise ReleaseError("a GitHub token is required")
        if not api_url.startswith("https://"):
            raise ReleaseError("the GitHub API URL must use HTTPS")
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.user_agent = user_agent

    def _send(
        self,
        method: str,
        url: str,
        data: bytes | None,
        content_type: str,
        *,
        accept: str = "application/vnd.github+json",
        allow_not_found: bool = False,
        raw: bool = False,
    ) -> Any:
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": accept,
                "Authorization": f"Bearer {self.token}",
                "Content-Type": content_type,
                "User-Agent": self.user_agent,
                "X-GitHub-Api-Version": API_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            if allow_not_found and error.code == 404:
                return None
            try:
                detail = json.loads(error.read().decode("utf-8")).get("message")
            except (UnicodeError, json.JSONDecodeError, AttributeError):
                detail = None
            suffix = f": {detail}" if isinstance(detail, str) and detail else ""
            raise ReleaseError(f"GitHub {method} {url} returned HTTP {error.code}{suffix}") from error
        except (OSError, urllib.error.URLError) as error:
            raise ReleaseError(
                f"GitHub {method} {url} did not return a definitive response: {error}"
            ) from error
        if raw:
            return body
        if not body:
            return None
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ReleaseError(f"GitHub {method} {url} returned invalid JSON") from error

    def _path(self, path: str) -> str:
        if not path.startswith("/"):
            raise ReleaseError("GitHub API paths must be absolute")
        return f"{self.api_url}{path}"

    def get(self, path: str, *, allow_not_found: bool = False) -> Any:
        return self._send(
            "GET", self._path(path), None, "application/json", allow_not_found=allow_not_found
        )

    def download(self, path: str) -> bytes:
        return self._send(
            "GET", self._path(path), None, "application/json",
            accept="application/octet-stream", raw=True,
        )

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return self._send("POST", self._path(path), data, "application/json")

    def upload(self, url: str, data: bytes, content_type: str) -> Any:
        if not url.startswith("https://uploads.github.com/"):
            raise ReleaseError("release assets upload only to uploads.github.com")
        return self._send("POST", url, data, content_type)

    def graphql(self, query: str, variables: dict[str, Any]) -> Any:
        response = self.post("/graphql", {"query": query, "variables": variables})
        if not isinstance(response, dict) or response.get("errors"):
            raise ReleaseError(f"GitHub GraphQL request failed: {response!r}")
        return response.get("data")


@dataclass
class Clock:
    """Wall clock and sleep, injectable for offline tests."""

    now: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep


@dataclass
class Reporter:
    """Write the job summary, or print it locally."""

    summary_path: Path | None = None

    def summary(self, text: str) -> None:
        if self.summary_path is None:
            sys.stdout.write(text)
            return
        with self.summary_path.open("a", encoding="utf-8") as stream:
            stream.write(text)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseError(message)


def _quoted(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def validate_repository(repository: str) -> None:
    _require(REPOSITORY_PATTERN.fullmatch(repository) is not None, f"invalid repository {repository!r}")


def validate_tag(tag: str) -> str:
    """Return the version a strict ``vX.Y.Z`` release tag names."""
    _require(
        isinstance(tag, str) and RELEASE_TAG_PATTERN.fullmatch(tag) is not None,
        f"{tag!r} is not a strict SemVer release tag vX.Y.Z",
    )
    return tag[1:]


def immediate_successors(version: str) -> tuple[str, str, str]:
    """Return the next patch, minor, and major versions in SemVer order."""
    _require(parse_production_release_version(version) is not None, f"invalid version {version!r}")
    major, minor, patch = (int(part) for part in version.split("."))
    return (
        f"{major}.{minor}.{patch + 1}",
        f"{major}.{minor + 1}.0",
        f"{major + 1}.0.0",
    )


def git(root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise ReleaseError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


# --- The stamped installed tree -------------------------------------------


def read_release_files(root: Path, commit: str) -> dict[str, bytes]:
    """Return ``plugin/**`` and ``LICENSE`` at a commit, as regular-file bytes."""
    raw = git(root, "ls-tree", "-r", "-z", commit, "--", "LICENSE", "plugin")
    files: dict[str, bytes] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, blob = meta.decode("ascii").split(" ")
        relative = path.decode("utf-8")
        _require(
            kind == "blob" and mode == FILE_MODE,
            f"{relative} at {commit} is {mode} {kind}; the release tree holds only "
            f"regular {FILE_MODE} files",
        )
        files[relative] = git(root, "cat-file", "blob", blob)
    _require("LICENSE" in files, f"LICENSE is missing at {commit}")
    for manifest in MANIFEST_FILES:
        _require(manifest in files, f"{manifest} is missing at {commit}")
    return files


def stamp_manifest(data: bytes, version: str, label: str) -> bytes:
    """Insert ``version`` after ``name`` in one versionless canonical manifest."""
    _require(parse_production_release_version(version) is not None, f"invalid version {version!r}")
    try:
        document = json.loads(data.decode("utf-8"), object_pairs_hook=OrderedDict)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseError(f"{label} is not valid JSON: {error}") from error
    _require(isinstance(document, OrderedDict), f"{label} must be one JSON object")
    _require("version" not in document, f"{label} on main must not declare a version")
    _require(
        (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8") == data,
        f"{label} is not byte-stable in the canonical two-space JSON form",
    )
    stamped: OrderedDict[str, Any] = OrderedDict()
    for key, value in document.items():
        stamped[key] = value
        if key == "name":
            stamped["version"] = version
    _require("version" in stamped, f"{label} has no name field to stamp after")
    return (json.dumps(stamped, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def stamp_files(files: dict[str, bytes], version: str) -> dict[str, bytes]:
    """Return the release tree: the files with both manifests stamped."""
    stamped = dict(files)
    for manifest in MANIFEST_FILES:
        stamped[manifest] = stamp_manifest(files[manifest], version, manifest)
    return stamped


def blob_sha(data: bytes) -> str:
    """Return the Git blob ID of the bytes."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def tree_sha(files: dict[str, bytes]) -> str:
    """Return the Git tree ID of regular files at slash-separated paths."""
    root: dict[str, Any] = {}
    for path, data in files.items():
        parts = path.split("/")
        _require(all(parts), f"invalid tree path {path!r}")
        node = root
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            _require(isinstance(child, dict), f"{path} collides with a file")
            node = child
        _require(parts[-1] not in node, f"duplicate tree path {path!r}")
        node[parts[-1]] = data

    def encode(node: dict[str, Any]) -> str:
        entries = []
        for name, value in node.items():
            if isinstance(value, dict):
                entries.append((name + "/", b"40000 " + name.encode() + b"\0" + bytes.fromhex(encode(value))))
            else:
                entries.append((name, FILE_MODE.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(blob_sha(value))))
        payload = b"".join(entry for _, entry in sorted(entries, key=lambda item: item[0].encode()))
        return hashlib.sha1(b"tree %d\0" % len(payload) + payload).hexdigest()

    return encode(root)


def write_tree(files: dict[str, bytes], directory: Path) -> None:
    for path, data in files.items():
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def zip_name(version: str) -> str:
    return f"axiom-v{version}-plugin.zip"


def build_plugin_zip(files: dict[str, bytes]) -> bytes:
    """Build the deterministic zip of the stamped ``plugin/`` tree.

    Members are relative to the plugin root, sorted, stored without compression,
    with a fixed timestamp and Unix mode 0644, so equal trees give equal bytes.
    """
    members = sorted(
        (path.removeprefix("plugin/"), data)
        for path, data in files.items()
        if path.startswith("plugin/")
    )
    _require(bool(members), "the release tree has no plugin/ files")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for relative, data in members:
            info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (0o100000 | 0o644) << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def runtime_digest(files: dict[str, bytes], input_manifest: dict[str, Any]) -> str:
    """Compute the installed-runtime digest of a release tree."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="axiom-release-digest-") as directory:
        write_tree(files, Path(directory))
        contract = compute_runtime_contract(Path(directory), input_manifest, failures)
    _require(
        contract is not None and not failures,
        "the runtime digest could not be computed: " + "; ".join(failures),
    )
    return contract.digest


def input_manifest_at(root: Path, commit: str) -> dict[str, Any]:
    try:
        document = json.loads(git(root, "show", f"{commit}:{INPUT_MANIFEST_RELATIVE}"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseError(f"{INPUT_MANIFEST_RELATIVE} at {commit} is not valid JSON") from error
    _require(isinstance(document, dict), f"{INPUT_MANIFEST_RELATIVE} at {commit} must be an object")
    return document


def release_notes(message: str, tag: str, previous_tag: str | None) -> str:
    """Render the Release body from a tag or commit message.

    A signature block is removed, line endings become LF, and one final line
    links the comparison with the previous release when there is one.
    """
    validate_tag(tag)
    text = SIGNATURE_BLOCK.sub("", message.replace("\r\n", "\n").replace("\r", "\n")).strip()
    _require(bool(text), f"the {tag} message is empty; the Release needs notes")
    if previous_tag is not None:
        validate_tag(previous_tag)
        text += f"\n\n{REPOSITORY_URL}/compare/{previous_tag}...{tag}"
    body = text + "\n"
    _require(
        len(body) <= RELEASE_NOTES_MAX_CHARACTERS,
        f"the {tag} notes exceed GitHub's {RELEASE_NOTES_MAX_CHARACTERS}-character limit",
    )
    return body


def release_commit_message(tag: str, commit: str) -> dict[str, str]:
    return {"headline": f"release: {tag}", "body": f"Installed tree of {tag}, built from {commit}."}


# --- GitHub state -----------------------------------------------------------


@dataclass(frozen=True)
class TagTarget:
    """One release tag ref, its peeled commit, and the message that becomes the notes."""

    object_type: str
    object_sha: str
    commit: str
    message: str


def resolve_tag(api: Api, repository: str, tag: str) -> TagTarget:
    reference = api.get(f"/repos/{repository}/git/ref/tags/{_quoted(tag)}", allow_not_found=True)
    _require(isinstance(reference, dict), f"tag {tag} does not exist")
    target = reference.get("object") or {}
    sha = target.get("sha")
    _require(
        reference.get("ref") == f"refs/tags/{tag}" and OID_PATTERN.fullmatch(str(sha)) is not None,
        f"refs/tags/{tag} must resolve exactly",
    )
    if target.get("type") == "commit":
        commit = api.get(f"/repos/{repository}/git/commits/{sha}")
        message = commit.get("message") if isinstance(commit, dict) else None
        _require(isinstance(message, str), f"cannot read the message of {sha}")
        return TagTarget("commit", sha, sha, message)
    _require(target.get("type") == "tag", f"{tag} must point at a commit or one annotated tag")
    annotated = api.get(f"/repos/{repository}/git/tags/{sha}")
    _require(isinstance(annotated, dict), f"cannot read the annotated tag {sha}")
    peeled = annotated.get("object") or {}
    verification = annotated.get("verification") or {}
    _require(annotated.get("tag") == tag, f"the annotated tag object {sha} names another tag")
    _require(
        peeled.get("type") == "commit" and OID_PATTERN.fullmatch(str(peeled.get("sha"))) is not None,
        f"the annotated tag {tag} must point directly at a commit",
    )
    _require(
        verification.get("verified") is True,
        f"the annotated tag {tag} must carry a verified signature",
    )
    message = annotated.get("message")
    _require(isinstance(message, str), f"cannot read the message of the annotated tag {tag}")
    return TagTarget("tag", sha, peeled["sha"], message)


def require_on_main_history(api: Api, repository: str, commit: str) -> None:
    """Require the commit to be main's head or one of its ancestors."""
    comparison = api.get(f"/repos/{repository}/compare/main...{commit}")
    _require(
        isinstance(comparison, dict) and comparison.get("status") in {"identical", "behind"},
        f"{commit} is not on the main history",
    )


def require_github_signature(api: Api, repository: str, commit: str) -> None:
    owner, name = repository.split("/", 1)
    data = api.graphql(SIGNATURE_QUERY, {"owner": owner, "name": name, "oid": commit})
    target = (((data or {}).get("repository") or {}).get("object")) or {}
    signature = target.get("signature") or {}
    _require(
        target.get("oid") == commit
        and signature.get("isValid") is True
        and signature.get("state") == "VALID"
        and signature.get("wasSignedByGitHub") is True,
        f"{commit} must have a valid signature made with GitHub's signing key",
    )


def list_check_runs(api: Api, repository: str, commit: str) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    page = 1
    while True:
        response = api.get(
            f"/repos/{repository}/commits/{commit}/check-runs"
            f"?filter=latest&per_page=100&page={page}"
        )
        batch = response.get("check_runs") if isinstance(response, dict) else None
        _require(isinstance(batch, list), "the check-runs response must contain a list")
        runs.extend(run for run in batch if isinstance(run, dict))
        if len(batch) < 100:
            return runs
        page += 1


def _actions_check(runs: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    matches = [
        run
        for run in runs
        if run.get("name") == name and (run.get("app") or {}).get("id") == GITHUB_ACTIONS_APP_ID
    ]
    return max(matches, key=lambda run: run.get("id") or 0) if matches else None


def wait_for_checks(
    api: Api,
    repository: str,
    commit: str,
    names: tuple[str, ...],
    clock: Clock,
    label: str,
    *,
    timeout: float = CHECK_TIMEOUT_SECONDS,
) -> dict[str, int]:
    """Wait until each named GitHub Actions check succeeded on the exact commit."""
    deadline = clock.now() + timeout
    while True:
        runs = list_check_runs(api, repository, commit)
        evidence: dict[str, int] = {}
        pending: list[str] = []
        for name in names:
            run = _actions_check(runs, name)
            if run is None or run.get("status") != "completed":
                pending.append(name)
                continue
            _require(
                run.get("conclusion") == "success",
                f"{label}: required check {name!r} concluded {run.get('conclusion')!r} on {commit}",
            )
            evidence[name] = run.get("id")
        if not pending:
            return evidence
        _require(
            clock.now() < deadline,
            f"{label}: timed out waiting for {', '.join(pending)} on {commit}",
        )
        clock.sleep(POLL_SECONDS)


def check_succeeded(api: Api, repository: str, commit: str, name: str) -> bool:
    run = _actions_check(list_check_runs(api, repository, commit), name)
    return bool(run and run.get("status") == "completed" and run.get("conclusion") == "success")


def is_final_release(release: Any, tag: str | None = None) -> bool:
    return (
        isinstance(release, dict)
        and (tag is None or release.get("tag_name") == tag)
        and release.get("draft") is False
        and release.get("prerelease") is False
        and release.get("immutable") is True
    )


def list_releases(api: Api, repository: str) -> list[dict[str, Any]]:
    releases: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = api.get(f"/repos/{repository}/releases?per_page=100&page={page}")
        _require(isinstance(batch, list), "the Release collection must be a list")
        releases.extend(release for release in batch if isinstance(release, dict))
        if len(batch) < 100:
            return releases
        page += 1


def find_release(api: Api, repository: str, tag: str) -> dict[str, Any] | None:
    """Select zero or one Release for the tag from the complete collection."""
    matches = [release for release in list_releases(api, repository) if release.get("tag_name") == tag]
    _require(len(matches) <= 1, f"more than one Release uses {tag}; inspect them before any retry")
    return matches[0] if matches else None


def previous_release_tag(api: Api, repository: str, version: str) -> str | None:
    """Return the highest published stable Release tag older than the version."""
    target = parse_production_release_version(version)
    candidates = []
    for release in list_releases(api, repository):
        tag = release.get("tag_name")
        if release.get("draft") is not False or release.get("prerelease") is not False:
            continue
        if not isinstance(tag, str) or RELEASE_TAG_PATTERN.fullmatch(tag) is None:
            continue
        precedence = parse_production_release_version(tag[1:])
        if precedence < target:
            candidates.append((precedence, tag))
    return max(candidates)[1] if candidates else None


def highest_tag_below(api: Api, repository: str, version: str) -> str | None:
    """Return the highest strict SemVer release tag older than the version.

    Normally this is GitHub Latest's tag. After a release attempt failed past
    its tag, it is that failed tag, so the next attempt takes the next version.
    """
    target = parse_production_release_version(version)
    references = api.get(f"/repos/{repository}/git/matching-refs/tags/v")
    _require(isinstance(references, list), "the tag listing must be a list")
    candidates = []
    for reference in references:
        name = str((reference or {}).get("ref", "")).removeprefix("refs/tags/")
        if RELEASE_TAG_PATTERN.fullmatch(name) is None:
            continue
        precedence = parse_production_release_version(name[1:])
        if precedence < target:
            candidates.append((precedence, name))
    return max(candidates)[1] if candidates else None


def evidence_asset(release: dict[str, Any]) -> dict[str, Any]:
    tag = release.get("tag_name")
    prefix = f"axiom-{tag}-release-evidence-"
    matches = [
        asset
        for asset in release.get("assets") or []
        if isinstance(asset, dict)
        and str(asset.get("name", "")).startswith(prefix)
        and str(asset.get("name", "")).endswith(".json")
    ]
    _require(len(matches) == 1, f"the {tag} Release must hold exactly one release-evidence asset")
    return matches[0]


def latest_runtime_digest(api: Api, repository: str, latest: dict[str, Any], root: Path) -> str:
    """Return the runtime digest recorded for the Latest release.

    The digest comes from Latest's release-evidence asset. Evidence that records
    no digest gets the digest the generator computes on Latest's tagged tree
    with the input policy at that commit.
    """
    tag = latest["tag_name"]
    asset = evidence_asset(latest)
    data = api.download(f"/repos/{repository}/releases/assets/{asset['id']}")
    _require(
        hashlib.sha256(data).hexdigest() == str(asset["name"]).removesuffix(".json").rsplit("-", 1)[-1],
        f"the {tag} evidence asset bytes do not match its name",
    )
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseError(f"the {tag} evidence asset is not valid JSON") from error
    recorded = (document.get("runtimeContract") or {}).get("digest") if isinstance(document, dict) else None
    if recorded is not None:
        _require(
            isinstance(recorded, str) and DIGEST_PATTERN.fullmatch(recorded) is not None,
            f"the {tag} evidence asset records a malformed runtime digest",
        )
        return recorded
    commit = resolve_tag(api, repository, tag).commit
    return runtime_digest(read_release_files(root, commit), input_manifest_at(root, commit))


def inspect_release_branch(api: Api, repository: str, version: str) -> str | None:
    """Return the release branch head after checking its shape, or None when absent.

    The head must descend from the branch root, hold only ``plugin/`` and
    ``LICENSE`` (the root holds only ``LICENSE``), and carry an older version
    than the one being released.
    """
    reference = api.get(f"/repos/{repository}/git/ref/heads/{RELEASE_BRANCH}", allow_not_found=True)
    if reference is None:
        return None
    target = reference.get("object") if isinstance(reference, dict) else None
    _require(
        isinstance(reference, dict)
        and reference.get("ref") == RELEASE_BRANCH_REF
        and isinstance(target, dict)
        and target.get("type") == "commit"
        and OID_PATTERN.fullmatch(str(target.get("sha"))) is not None,
        f"{RELEASE_BRANCH_REF} must resolve to one commit",
    )
    head = target["sha"]
    comparison = api.get(f"/repos/{repository}/compare/{RELEASE_BRANCH_ROOT}...{head}")
    _require(
        isinstance(comparison, dict)
        and (comparison.get("merge_base_commit") or {}).get("sha") == RELEASE_BRANCH_ROOT
        and comparison.get("status") in {"ahead", "identical"},
        f"{RELEASE_BRANCH_REF} head {head} does not descend from {RELEASE_BRANCH_ROOT}",
    )
    commit = api.get(f"/repos/{repository}/git/commits/{head}")
    tree = ((commit or {}).get("tree") or {}).get("sha") if isinstance(commit, dict) else None
    listing = api.get(f"/repos/{repository}/git/trees/{tree}")
    entries = {
        entry.get("path"): entry.get("type")
        for entry in (listing or {}).get("tree") or []
        if isinstance(entry, dict)
    }
    expected = {"LICENSE": "blob"} if head == RELEASE_BRANCH_ROOT else {"LICENSE": "blob", "plugin": "tree"}
    _require(
        entries == expected,
        f"{RELEASE_BRANCH_REF} head {head} must hold only {', '.join(sorted(expected))}",
    )
    if head == RELEASE_BRANCH_ROOT:
        return head
    content = api.get(
        f"/repos/{repository}/contents/{CODEX_MANIFEST}?ref={head}"
    )
    try:
        manifest = json.loads(base64.b64decode(content["content"]).decode("utf-8"))
        head_version = manifest["version"]
    except (KeyError, TypeError, ValueError) as error:
        raise ReleaseError(f"cannot read the version at {RELEASE_BRANCH_REF} head {head}") from error
    head_precedence = parse_production_release_version(head_version)
    _require(head_precedence is not None, f"{RELEASE_BRANCH_REF} head {head} has no release version")
    _require(
        head_precedence < parse_production_release_version(version),
        f"{RELEASE_BRANCH_REF} already holds version {head_version}; a release commit for "
        f"{version} or later exists",
    )
    return head


def remote_tree_files(api: Api, repository: str, commit: str) -> dict[str, str]:
    """Return path to blob ID for every file in a commit's tree."""
    document = api.get(f"/repos/{repository}/git/commits/{commit}")
    tree = ((document or {}).get("tree") or {}).get("sha") if isinstance(document, dict) else None
    listing = api.get(f"/repos/{repository}/git/trees/{tree}?recursive=1")
    _require(isinstance(listing, dict) and listing.get("truncated") is False, f"cannot list {commit}'s tree")
    files: dict[str, str] = {}
    for entry in listing.get("tree") or []:
        if entry.get("type") == "tree":
            continue
        _require(
            entry.get("type") == "blob" and entry.get("mode") == FILE_MODE,
            f"{entry.get('path')} at {commit} is not a regular file",
        )
        files[entry["path"]] = entry["sha"]
    return files


def release_branch_commit(
    api: Api,
    repository: str,
    *,
    head: str | None,
    files: dict[str, bytes],
    expected_tree: str,
    tag: str,
    commit: str,
) -> str:
    """Fast-forward the release branch by one GitHub-signed commit of the stamped tree."""
    if head is None:
        api.post(
            f"/repos/{repository}/git/refs",
            {"ref": RELEASE_BRANCH_REF, "sha": RELEASE_BRANCH_ROOT},
        )
        head = RELEASE_BRANCH_ROOT
    current = remote_tree_files(api, repository, head)
    additions = [
        {"path": path, "contents": base64.b64encode(data).decode("ascii")}
        for path, data in sorted(files.items())
        if current.get(path) != blob_sha(data)
    ]
    deletions = [{"path": path} for path in sorted(current) if path not in files]
    data = api.graphql(
        CREATE_COMMIT_MUTATION,
        {
            "input": {
                "branch": {"repositoryNameWithOwner": repository, "branchName": RELEASE_BRANCH},
                "expectedHeadOid": head,
                "message": release_commit_message(tag, commit),
                "fileChanges": {"additions": additions, "deletions": deletions},
            }
        },
    )
    created = ((((data or {}).get("createCommitOnBranch") or {}).get("commit")) or {}).get("oid")
    _require(isinstance(created, str) and OID_PATTERN.fullmatch(created) is not None, "no release commit")
    document = api.get(f"/repos/{repository}/git/commits/{created}")
    _require(
        isinstance(document, dict)
        and (document.get("tree") or {}).get("sha") == expected_tree
        and [parent.get("sha") for parent in document.get("parents") or []] == [head],
        f"release commit {created} does not hold exactly the stamped tree {expected_tree} on {head}",
    )
    require_github_signature(api, repository, created)
    reference = api.get(f"/repos/{repository}/git/ref/heads/{RELEASE_BRANCH}")
    _require(
        ((reference or {}).get("object") or {}).get("sha") == created,
        f"{RELEASE_BRANCH_REF} does not hold {created}",
    )
    return created


# --- The release subject ----------------------------------------------------


@dataclass(frozen=True)
class ReleaseBuild:
    """Everything derived from one tag before the release branch moves."""

    tag: str
    version: str
    target: TagTarget
    tree: str
    files: dict[str, bytes]
    release_tree: str
    zip_bytes: bytes
    runtime_digest: str
    previous_tag: str | None
    notes: str

    def subject(self, release_commit: str, bootstrap: bool) -> dict[str, Any]:
        return {
            "bootstrap": bootstrap,
            "version": self.version,
            "tag": self.tag,
            "tagObject": {"type": self.target.object_type, "sha": self.target.object_sha},
            "commit": self.target.commit,
            "tree": self.tree,
            "releaseCommit": release_commit,
            "releaseTree": self.release_tree,
            "zip": {
                "name": zip_name(self.version),
                "sha256": hashlib.sha256(self.zip_bytes).hexdigest(),
                "size": len(self.zip_bytes),
            },
            "runtimeDigest": self.runtime_digest,
            "previousTag": self.previous_tag,
            "notesSha256": hashlib.sha256(self.notes.encode("utf-8")).hexdigest(),
        }


def require_runtime_change(
    digest: str, latest_digest: str, *, tag: str, latest_tag: str, bootstrap: bool
) -> None:
    """Require a changed runtime digest, except for the bootstrap release.

    The bootstrap release creates the release branch; until it exists, hosts
    have no installed tree to resolve, so it may carry Latest's runtime.
    """
    _require(
        bootstrap or digest != latest_digest,
        f"{tag} changes no installed file: its runtime digest equals {latest_tag}'s "
        f"({latest_digest}); a repository-only change publishes no release",
    )


def is_bootstrap(head: str | None) -> bool:
    """Return whether the release branch holds no release commit yet."""
    return head is None or head == RELEASE_BRANCH_ROOT


def build_release(root: Path, api: Api, repository: str, tag: str) -> ReleaseBuild:
    """Derive the stamped tree, zip, digest, and notes of one tag."""
    validate_repository(repository)
    version = validate_tag(tag)
    target = resolve_tag(api, repository, tag)
    tree = git(root, "rev-parse", f"{target.commit}^{{tree}}").decode("ascii").strip()
    files = stamp_files(read_release_files(root, target.commit), version)
    zip_bytes = build_plugin_zip(files)
    previous = previous_release_tag(api, repository, version)
    return ReleaseBuild(
        tag=tag,
        version=version,
        target=target,
        tree=tree,
        files=files,
        release_tree=tree_sha(files),
        zip_bytes=zip_bytes,
        runtime_digest=runtime_digest(files, input_manifest_at(root, target.commit)),
        previous_tag=previous,
        notes=release_notes(target.message, tag, previous),
    )


def canonical_json(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


# --- Checks on the stamped tree ----------------------------------------------


def check_stamped_tree(root: Path, commit: str, version: str) -> None:
    """Run the repository checks on the tagged tree with both manifests stamped."""
    with tempfile.TemporaryDirectory(prefix="axiom-release-check-") as directory:
        tree = Path(directory) / "tree"
        git(root, "worktree", "add", "--detach", str(tree), commit)
        try:
            for manifest in MANIFEST_FILES:
                path = tree / manifest
                path.write_bytes(stamp_manifest(path.read_bytes(), version, manifest))
            result = subprocess.run(
                [sys.executable, "-B", ".ci/check.py", "--release-version", version],
                cwd=tree,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                output = (result.stderr + result.stdout).strip()[-CHECK_OUTPUT_LIMIT:]
                raise ReleaseError(
                    f"the stamped v{version} tree fails `python3 -B .ci/check.py "
                    f"--release-version {version}`:\n{output}"
                )
        finally:
            git(root, "worktree", "remove", "--force", str(tree))


# --- Draft, publisher, observation -------------------------------------------


def dispatch_and_wait(
    api: Api,
    repository: str,
    workflow: str,
    ref: str,
    inputs: dict[str, str],
    expected_commit: str,
    clock: Clock,
    label: str,
) -> dict[str, Any]:
    """Dispatch one workflow run, identify exactly that run, and require success."""
    runs_path = (
        f"/repos/{repository}/actions/workflows/{workflow}/runs"
        f"?event=workflow_dispatch&head_sha={expected_commit}&per_page=100"
    )

    def current_runs() -> list[dict[str, Any]]:
        response = api.get(runs_path)
        runs = response.get("workflow_runs") if isinstance(response, dict) else None
        _require(isinstance(runs, list), f"{label}: the workflow-runs response must contain a list")
        return [run for run in runs if isinstance(run, dict)]

    before = {run.get("id") for run in current_runs()}
    api.post(
        f"/repos/{repository}/actions/workflows/{workflow}/dispatches",
        {"ref": ref, "inputs": inputs},
    )
    deadline = clock.now() + RUN_DISCOVERY_SECONDS
    while True:
        clock.sleep(POLL_SECONDS)
        new_runs = [run for run in current_runs() if run.get("id") not in before]
        _require(
            len(new_runs) <= 1,
            f"{label}: more than one new {workflow} run appeared; inspect them before any retry",
        )
        if new_runs:
            run = new_runs[0]
            break
        _require(clock.now() < deadline, f"{label}: no dispatched {workflow} run appeared")
    run_id = run.get("id")
    _require(type(run_id) is int and run_id > 0, f"{label}: the dispatched run has no ID")
    deadline = clock.now() + RUN_TIMEOUT_SECONDS
    while run.get("status") != "completed":
        _require(clock.now() < deadline, f"{label}: run {run_id} did not complete in time")
        clock.sleep(POLL_SECONDS)
        run = api.get(f"/repos/{repository}/actions/runs/{run_id}")
        _require(isinstance(run, dict), f"{label}: run {run_id} could not be read")
    _require(
        run.get("conclusion") == "success",
        f"{label}: run {run_id} concluded {run.get('conclusion')!r}; inspect it and the "
        f"release state ({run.get('html_url')})",
    )
    return run


def _upload_asset(
    api: Api, repository: str, release_id: int, name: str, data: bytes, content_type: str
) -> None:
    uploaded = api.upload(
        f"https://uploads.github.com/repos/{repository}/releases/{release_id}/assets?name={_quoted(name)}",
        data,
        content_type,
    )
    _require(
        isinstance(uploaded, dict) and uploaded.get("name") == name and uploaded.get("size") == len(data),
        f"the uploaded asset does not match {name}",
    )


def stage_draft(
    api: Api,
    repository: str,
    *,
    tag: str,
    commit: str,
    body: str,
    assets: tuple[tuple[str, bytes, str], ...],
) -> dict[str, Any]:
    """Create the one exact Draft the immutable publisher requires."""
    release = api.post(
        f"/repos/{repository}/releases",
        {
            "tag_name": tag,
            "target_commitish": commit,
            "name": tag,
            "body": body,
            "draft": True,
            "prerelease": False,
        },
    )
    release_id = release.get("id") if isinstance(release, dict) else None
    _require(type(release_id) is int and release_id > 0, "Draft creation returned no Release")
    _require(
        release.get("draft") is True
        and release.get("tag_name") == tag
        and release.get("name") == tag
        and release.get("body") == body,
        f"Release {release_id} is not the exact Draft for {tag}",
    )
    for name, data, content_type in assets:
        _upload_asset(api, repository, release_id, name, data, content_type)
    staged = api.get(f"/repos/{repository}/releases/{release_id}")
    _require(
        isinstance(staged, dict)
        and staged.get("draft") is True
        and sorted((asset.get("name"), asset.get("size")) for asset in staged.get("assets") or [])
        == sorted((name, len(data)) for name, data, _ in assets),
        f"Draft {release_id} does not hold exactly the release assets",
    )
    return staged


# --- The release run ---------------------------------------------------------


def run_release(
    *,
    root: Path,
    api: Api,
    repository: str,
    tag: str,
    reporter: Reporter,
    clock: Clock,
    check_tree: Callable[[Path, str, str], None] = check_stamped_tree,
) -> dict[str, Any]:
    """Gate, then build the release branch commit, the Draft, and the immutable Release."""
    validate_repository(repository)
    version = validate_tag(tag)
    build = build_release(root, api, repository, tag)
    commit = build.target.commit

    require_on_main_history(api, repository, commit)
    require_github_signature(api, repository, commit)
    wait_for_checks(api, repository, commit, REQUIRED_CHECKS, clock, "tagged commit")
    wait_for_checks(api, repository, commit, (CREATED_TAG_CHECK,), clock, "created tag")
    head = inspect_release_branch(api, repository, version)
    bootstrap = is_bootstrap(head)

    latest = api.get(f"/repos/{repository}/releases/latest", allow_not_found=True)
    if latest is not None:
        latest_tag = latest.get("tag_name") if isinstance(latest, dict) else None
        _require(is_final_release(latest), f"GitHub Latest {latest_tag} must be final and immutable")
        validate_tag(str(latest_tag))
        _require(
            build.previous_tag == latest_tag,
            f"GitHub Latest {latest_tag} is not the highest published release before {tag}",
        )
        require_runtime_change(
            build.runtime_digest,
            latest_runtime_digest(api, repository, latest, root),
            tag=tag,
            latest_tag=str(latest_tag),
            bootstrap=bootstrap,
        )
    base_tag = highest_tag_below(api, repository, version)
    if base_tag is not None:
        _require(
            version in immediate_successors(base_tag[1:]),
            f"{version} is not the next patch, minor, or major version after {base_tag}, "
            "the highest release tag below it",
        )
    _require(find_release(api, repository, tag) is None, f"a Release already uses {tag}")
    check_tree(root, commit, version)

    release_commit = release_branch_commit(
        api,
        repository,
        head=head,
        files=build.files,
        expected_tree=build.release_tree,
        tag=tag,
        commit=commit,
    )
    subject = build.subject(release_commit, bootstrap)
    release = stage_draft(
        api,
        repository,
        tag=tag,
        commit=commit,
        body=build.notes,
        assets=((subject["zip"]["name"], build.zip_bytes, "application/zip"),),
    )
    dispatch_and_wait(
        api, repository, PUBLISHER_WORKFLOW, tag, {"tag": tag}, commit, clock, "immutable publisher"
    )
    release = api.get(f"/repos/{repository}/releases/{release['id']}")
    _require(is_final_release(release, tag), f"the {tag} Release is not final and immutable")
    latest = api.get(f"/repos/{repository}/releases/latest")
    _require(
        isinstance(latest, dict) and latest.get("id") == release.get("id"),
        f"GitHub Latest does not identify the {tag} Release",
    )
    # The release branch holds no workflow files, so both observations run on
    # the tag and attach to the tagged commit.
    for phase, check in (
        ("release-branch", RELEASE_BRANCH_CHECK),
        ("published-release", PUBLISHED_RELEASE_CHECK),
    ):
        if not check_succeeded(api, repository, commit, check):
            dispatch_and_wait(
                api, repository, SIGNATURE_GUARD_WORKFLOW, tag, {"phase": phase}, commit, clock, check
            )
    reporter.summary(
        f"## Published {tag}\n\n"
        "| Field | Value |\n| --- | --- |\n"
        f"| Release | [{release['id']}]({release.get('html_url', '')}) |\n"
        f"| Tagged commit | `{commit}` |\n"
        f"| `{RELEASE_BRANCH}` commit | `{release_commit}` |\n"
        f"| Installed tree | `{build.release_tree}` |\n"
        f"| Plugin zip sha256 | `{subject['zip']['sha256']}` |\n"
        f"| Runtime digest | `{build.runtime_digest}` |\n"
        f"| Bootstrap release | `{str(bootstrap).lower()}` |\n"
        "| Immutable | `true` |\n"
        "| GitHub Latest | `true` |\n"
    )
    return subject


def subject_for_publisher(
    root: Path, api: Api, repository: str, tag: str, output: Path
) -> dict[str, Any]:
    """Independently derive the subject the publisher verifies a Draft against.

    The release branch head must be the GitHub-signed commit whose tree is the
    stamped tree this tag derives.
    """
    build = build_release(root, api, repository, tag)
    reference = api.get(f"/repos/{repository}/git/ref/heads/{RELEASE_BRANCH}")
    head = ((reference or {}).get("object") or {}).get("sha") if isinstance(reference, dict) else None
    _require(OID_PATTERN.fullmatch(str(head)) is not None, f"{RELEASE_BRANCH_REF} does not exist")
    document = api.get(f"/repos/{repository}/git/commits/{head}")
    _require(
        isinstance(document, dict) and (document.get("tree") or {}).get("sha") == build.release_tree,
        f"{RELEASE_BRANCH_REF} head {head} does not hold the stamped {tag} tree {build.release_tree}",
    )
    require_github_signature(api, repository, head)
    parents = [parent.get("sha") for parent in document.get("parents") or []]
    subject = build.subject(head, parents == [RELEASE_BRANCH_ROOT])
    output.mkdir(parents=True, exist_ok=True)
    (output / "subject.json").write_bytes(canonical_json(subject))
    (output / subject["zip"]["name"]).write_bytes(build.zip_bytes)
    return subject


# --- Workflow contract -------------------------------------------------------


def _plain(value: Any) -> Any:
    if isinstance(value, CanonicalYamlScalar):
        return value.value
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


CHECKOUT_ACTION = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON_ACTION = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
SETUP_NODE_ACTION = "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38"
EXPECTED_WORKFLOW = {
    "name": "Release",
    "on": {"push": {"tags": ["v*"]}},
    "permissions": {"contents": "read"},
    "concurrency": {"group": "release", "cancel-in-progress": "false"},
    "jobs": {
        "release": {
            "name": "Release",
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": "120",
            "permissions": {"actions": "write", "checks": "read", "contents": "write"},
            "steps": [
                {
                    "name": "Check out the tagged commit",
                    "uses": CHECKOUT_ACTION,
                    "with": {
                        "ref": "${{ github.sha }}",
                        "persist-credentials": "false",
                        "fetch-depth": "0",
                    },
                },
                {
                    "name": "Set up Python",
                    "uses": SETUP_PYTHON_ACTION,
                    "with": {"python-version": "3.14.7"},
                },
                # The repository checks on the stamped tree execute the
                # JavaScript release guard with Node.js.
                {
                    "name": "Set up Node.js",
                    "uses": SETUP_NODE_ACTION,
                    "with": {"node-version": "24.19.0", "package-manager-cache": "false"},
                },
                {
                    "name": "Gate, build, and publish the release",
                    "env": {
                        "GITHUB_TOKEN": "${{ github.token }}",
                        "RELEASE_TAG": "${{ github.ref_name }}",
                    },
                    "run": ">-",
                },
            ],
        },
    },
}
REQUIRED_COMMAND_ANCHOR = (
    "python3 -B .ci/scripts/release.py run\n"
    '          --repository "$GITHUB_REPOSITORY"\n'
    '          --tag "$RELEASE_TAG"\n'
)
FORBIDDEN_WORKFLOW_TEXT = (
    "pull_request",
    "workflow_run",
    "workflow_dispatch",
    "schedule:",
    "secrets.",
    "git push",
    "--force",
    "persist-credentials: true",
    "environment:",
)


def check_release_workflow_text(
    text: str, failures: list[str], *, label: str = ".github/workflows/release.yml"
) -> dict[str, Any] | None:
    """Validate the exact Release workflow trigger, job, permissions, and actions."""
    domain_failures: list[str] = []
    try:
        document = _plain(parse_canonical_yaml_document(text, label))
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None
    for key in sorted(set(document) | set(EXPECTED_WORKFLOW)):
        if document.get(key) != EXPECTED_WORKFLOW.get(key):
            domain_failures.append(f"{label} {key!r} differs from the reviewed Release workflow contract")
    if text.count(REQUIRED_COMMAND_ANCHOR) != 1:
        domain_failures.append(f"{label} must run exactly one `.ci/scripts/release.py run` command")
    for forbidden in FORBIDDEN_WORKFLOW_TEXT:
        if forbidden in text:
            domain_failures.append(f"{label} exposes forbidden surface {forbidden!r}")
    failures.extend(domain_failures)
    return document if not domain_failures else None


def check_release_workflow_contract(
    failures: list[str], workflow_path: Path = WORKFLOW_PATH
) -> dict[str, Any] | None:
    """Validate the checked-in Release workflow."""
    try:
        text = workflow_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read {display_path(workflow_path)}: {error}")
        return None
    return check_release_workflow_text(text, failures, label=display_path(workflow_path))


__all__ = (
    "Clock",
    "EXPECTED_WORKFLOW",
    "GitHubClient",
    "MANIFEST_FILES",
    "PUBLISHED_RELEASE_CHECK",
    "RELEASE_BRANCH",
    "RELEASE_BRANCH_CHECK",
    "RELEASE_BRANCH_ROOT",
    "REQUIRED_CHECKS",
    "ReleaseBuild",
    "ReleaseError",
    "Reporter",
    "blob_sha",
    "build_plugin_zip",
    "build_release",
    "check_release_workflow_contract",
    "check_release_workflow_text",
    "immediate_successors",
    "highest_tag_below",
    "inspect_release_branch",
    "is_bootstrap",
    "require_runtime_change",
    "latest_runtime_digest",
    "release_branch_commit",
    "release_notes",
    "resolve_tag",
    "run_release",
    "stamp_files",
    "stamp_manifest",
    "subject_for_publisher",
    "tree_sha",
    "validate_tag",
    "zip_name",
)
