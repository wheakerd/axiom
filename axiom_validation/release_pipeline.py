"""Deterministic CI release pipeline for one merged plugin version.

A pull request that changes the Codex manifest version is a release candidate;
every other pull request leaves the pipeline idle. On the candidate pull
request the pipeline checks the version step, previews the Release body, and
rehearses the catalog handoff on the pull-request head. After the merge it
waits for the required checks and every other check on the exact main commit,
rehearses the catalog handoff again in a disposable worktree of that commit so
the post-publication step is proven before the first irreversible one,
dispatches the protected tag controller, stages the exact Draft, dispatches the
immutable publisher and the published-release observation, and then proposes
and merges the marketplace catalog handoff for the verified Latest release.
Each step reads the current GitHub state first, so a rerun resumes the earliest
unfinished step. The pipeline uses only the Python standard library, Git, and
the GitHub API; it runs no AI model or agent.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Protocol

from .context import REPOSITORY_ROOT, display_path
from .manifests import catalog_source
from .release_evidence import MARKETPLACE_CATALOGS
from .release_tag_controller import (
    API_VERSION,
    GITHUB_ACTIONS_APP_ID,
    MAIN_REQUIRED_CHECKS,
    SIGNED_MAIN_CHECK,
)
from .release_versions import parse_production_release_version
from .runtime_identity import replace_runtime_identity_block
from .yaml_subset import (
    CanonicalYamlError,
    CanonicalYamlScalar,
    parse_canonical_yaml_document,
)


CODEX_MANIFEST = "plugin/.codex-plugin/plugin.json"
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "release-pipeline.yml"
TAG_CONTROLLER_WORKFLOW = "create-protected-release-tag.yml"
PUBLISHER_WORKFLOW = "publish-immutable-release.yml"
SIGNATURE_GUARD_WORKFLOW = "release-signature-guard.yml"
REQUIRED_MAIN_CHECKS = (*MAIN_REQUIRED_CHECKS, SIGNED_MAIN_CHECK)
CATALOG_REQUIRED_CHECKS = MAIN_REQUIRED_CHECKS
CREATED_TAG_CHECK = "Verify created release tag"
PUBLISHED_RELEASE_CHECK = "Observe published immutable release"
CATALOG_BRANCH_PREFIX = "catalog/"
# The pipeline's own jobs stay in progress while it waits, so the settled-check
# gate below never waits for them.
PIPELINE_JOB_NAMES = ("Release candidate", "Publish release", "Advance marketplace catalogs")
SETTLED_CONCLUSIONS = frozenset({"success", "skipped", "neutral"})
# The contributor checks that the rehearsed catalog handoff must pass, each run
# as ``python -B <command>`` from the rehearsal tree.
REHEARSAL_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("scripts/check-publication.py",),
    ("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"),
)
REHEARSAL_OUTPUT_LIMIT = 4000
CHANGELOG_RELATIVE = "CHANGELOG.md"
LEDGER_RELATIVE = "evidence/repository-policy-revisions-v1.json"
IDENTITY_RELATIVE = "evidence/runtime-identity.json"
STATUS_RELATIVE = "evidence/release-status.json"
IDENTITY_DOCUMENT_RELATIVE = "docs/runtime-identity.md"
POLL_SECONDS = 20
CHECK_TIMEOUT_SECONDS = 75 * 60
RUN_DISCOVERY_SECONDS = 5 * 60
RUN_TIMEOUT_SECONDS = 45 * 60
OID_PATTERN = re.compile(r"[0-9a-f]{40}")
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
RELEASE_TAG_PATTERN = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
CREATE_COMMIT_MUTATION = (
    "mutation($input: CreateCommitOnBranchInput!) { "
    "createCommitOnBranch(input: $input) { commit { oid } } }"
)
SIGNATURE_QUERY = (
    "query($owner: String!, $name: String!, $oid: GitObjectID!) { "
    "repository(owner: $owner, name: $name) { object(oid: $oid) { "
    "... on Commit { oid signature { isValid state wasSignedByGitHub } } } } }"
)


class PipelineError(RuntimeError):
    """A fail-closed release pipeline decision."""


class Api(Protocol):
    def get(self, path: str, *, allow_not_found: bool = False) -> Any: ...

    def post(self, path: str, payload: dict[str, Any]) -> Any: ...

    def put(self, path: str, payload: dict[str, Any]) -> Any: ...

    def delete(self, path: str) -> Any: ...

    def upload(self, url: str, data: bytes, content_type: str) -> Any: ...

    def graphql(self, query: str, variables: dict[str, Any]) -> Any: ...


class GitHubClient:
    """No-retry GitHub REST, GraphQL, and upload client for one token."""

    def __init__(
        self,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        user_agent: str = "axiom-release-pipeline",
    ) -> None:
        if not token:
            raise PipelineError("a GitHub token is required")
        if not api_url.startswith("https://"):
            raise PipelineError("the GitHub API URL must use HTTPS")
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
        allow_not_found: bool = False,
    ) -> Any:
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": content_type,
                "User-Agent": self.user_agent,
                "X-GitHub-Api-Version": API_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            if allow_not_found and error.code == 404:
                return None
            try:
                detail = json.loads(error.read().decode("utf-8")).get("message")
            except (UnicodeError, json.JSONDecodeError, AttributeError):
                detail = None
            suffix = f": {detail}" if isinstance(detail, str) and detail else ""
            raise PipelineError(f"GitHub {method} {url} returned HTTP {error.code}{suffix}") from error
        except (OSError, urllib.error.URLError) as error:
            raise PipelineError(
                f"GitHub {method} {url} did not return a definitive response: {error}"
            ) from error
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise PipelineError(f"GitHub {method} {url} returned invalid JSON") from error

    def _json(self, method: str, path: str, payload: dict[str, Any] | None, **options: Any) -> Any:
        if not path.startswith("/"):
            raise PipelineError("GitHub API paths must be absolute")
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return self._send(method, f"{self.api_url}{path}", data, "application/json", **options)

    def get(self, path: str, *, allow_not_found: bool = False) -> Any:
        return self._json("GET", path, None, allow_not_found=allow_not_found)

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        return self._json("POST", path, payload)

    def put(self, path: str, payload: dict[str, Any]) -> Any:
        return self._json("PUT", path, payload)

    def delete(self, path: str) -> Any:
        return self._json("DELETE", path, None)

    def upload(self, url: str, data: bytes, content_type: str) -> Any:
        if not url.startswith("https://uploads.github.com/"):
            raise PipelineError("release assets upload only to uploads.github.com")
        return self._send("POST", url, data, content_type)

    def graphql(self, query: str, variables: dict[str, Any]) -> Any:
        response = self.post("/graphql", {"query": query, "variables": variables})
        if not isinstance(response, dict) or response.get("errors"):
            raise PipelineError(f"GitHub GraphQL request failed: {response!r}")
        return response.get("data")


@dataclass
class Clock:
    """Wall clock and sleep, injectable for offline tests."""

    now: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep


@dataclass
class Reporter:
    """Write job summaries and step outputs, or print them locally."""

    summary_path: Path | None = None
    output_path: Path | None = None

    def summary(self, text: str) -> None:
        if self.summary_path is None:
            sys.stdout.write(text)
            return
        with self.summary_path.open("a", encoding="utf-8") as stream:
            stream.write(text)

    def output(self, name: str, value: str) -> None:
        if "\n" in value or "\r" in value:
            raise PipelineError(f"step output {name!r} must be one line")
        if self.output_path is None:
            sys.stdout.write(f"{name}={value}\n")
            return
        with self.output_path.open("a", encoding="utf-8") as stream:
            stream.write(f"{name}={value}\n")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PipelineError(message)


def _quoted(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def validate_repository(repository: str) -> None:
    _require(REPOSITORY_PATTERN.fullmatch(repository) is not None, f"invalid repository {repository!r}")


def validate_commit(commit: str, label: str) -> None:
    _require(OID_PATTERN.fullmatch(commit) is not None, f"{label} must be a lowercase 40-character Git SHA")


def validate_tag(tag: str) -> str:
    _require(RELEASE_TAG_PATTERN.fullmatch(tag) is not None, f"invalid production release tag {tag!r}")
    return tag[1:]


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PipelineError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout


def manifest_version_at(root: Path, commit: str) -> str:
    """Return the stable production version the Codex manifest declares at a commit."""
    try:
        document = json.loads(git(root, "show", f"{commit}:{CODEX_MANIFEST}"))
    except json.JSONDecodeError as error:
        raise PipelineError(f"{CODEX_MANIFEST} at {commit} is not valid JSON") from error
    version = document.get("version") if isinstance(document, dict) else None
    _require(
        parse_production_release_version(version) is not None,
        f"{CODEX_MANIFEST} at {commit} must declare one stable production version",
    )
    return version


def immediate_successors(version: str) -> tuple[str, str, str]:
    """Return the next patch, minor, and major versions in SemVer order."""
    _require(parse_production_release_version(version) is not None, f"invalid version {version!r}")
    major, minor, patch = (int(part) for part in version.split("."))
    return (
        f"{major}.{minor}.{patch + 1}",
        f"{major}.{minor + 1}.0",
        f"{major + 1}.0.0",
    )


def _is_final_release(release: Any, tag: str) -> bool:
    return (
        isinstance(release, dict)
        and release.get("tag_name") == tag
        and release.get("draft") is False
        and release.get("prerelease") is False
        and release.get("immutable") is True
    )


def find_release(api: Api, repository: str, tag: str) -> dict[str, Any] | None:
    """Select zero or one Release for the tag from the complete collection."""
    matches: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = api.get(f"/repos/{repository}/releases?per_page=100&page={page}")
        _require(isinstance(batch, list), "the Release collection must be a list")
        matches.extend(
            release for release in batch if isinstance(release, dict) and release.get("tag_name") == tag
        )
        if len(batch) < 100:
            break
        page += 1
    _require(len(matches) <= 1, f"more than one Release uses {tag}; inspect them before any retry")
    return matches[0] if matches else None


def read_tag_commit(api: Api, repository: str, tag: str) -> str | None:
    reference = api.get(f"/repos/{repository}/git/ref/tags/{_quoted(tag)}", allow_not_found=True)
    if reference is None:
        return None
    target = reference.get("object") if isinstance(reference, dict) else None
    _require(
        isinstance(reference, dict)
        and reference.get("ref") == f"refs/tags/{tag}"
        and isinstance(target, dict)
        and target.get("type") == "commit"
        and OID_PATTERN.fullmatch(str(target.get("sha"))) is not None,
        f"{tag} must be one lightweight tag that targets a commit",
    )
    return target["sha"]


def read_main_commit(api: Api, repository: str) -> str:
    reference = api.get(f"/repos/{repository}/git/ref/heads/main")
    target = reference.get("object") if isinstance(reference, dict) else None
    _require(
        isinstance(target, dict)
        and target.get("type") == "commit"
        and OID_PATTERN.fullmatch(str(target.get("sha"))) is not None,
        "main must resolve to one commit",
    )
    return target["sha"]


def require_on_main_history(api: Api, repository: str, commit: str) -> None:
    main = read_main_commit(api, repository)
    comparison = api.get(f"/repos/{repository}/compare/{commit}...{main}")
    _require(
        isinstance(comparison, dict)
        and (comparison.get("merge_base_commit") or {}).get("sha") == commit
        and comparison.get("status") in {"ahead", "identical"},
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
    """Wait until each named GitHub Actions check succeeds on the exact commit."""
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
                f"{label}: required check {name!r} concluded "
                f"{run.get('conclusion')!r} on {commit}",
            )
            evidence[name] = run.get("id")
        if not pending:
            return evidence
        _require(
            clock.now() < deadline,
            f"{label}: timed out waiting for {', '.join(pending)} on {commit}",
        )
        clock.sleep(POLL_SECONDS)


def wait_for_settled_checks(
    api: Api,
    repository: str,
    commit: str,
    clock: Clock,
    label: str,
    *,
    timeout: float = CHECK_TIMEOUT_SECONDS,
) -> dict[str, int]:
    """Wait until every other GitHub Actions check on the commit finished without failing.

    The required checks gate the release by name; this gate adds every other check
    that GitHub started for the same commit, such as code scanning, so the pipeline
    creates no tag and publishes no Release while a check on that commit is still
    running or has failed. The pipeline's own jobs are excluded because they stay in
    progress while it waits.
    """
    deadline = clock.now() + timeout
    while True:
        evidence: dict[str, int] = {}
        pending: list[str] = []
        for run in list_check_runs(api, repository, commit):
            name = run.get("name")
            if (run.get("app") or {}).get("id") != GITHUB_ACTIONS_APP_ID or name in PIPELINE_JOB_NAMES:
                continue
            if run.get("status") != "completed":
                pending.append(str(name))
                continue
            _require(
                run.get("conclusion") in SETTLED_CONCLUSIONS,
                f"{label}: check {name!r} concluded {run.get('conclusion')!r} on {commit}; "
                "the pipeline publishes nothing while a check on the release commit has failed",
            )
            evidence[str(name)] = run.get("id")
        if not pending:
            return evidence
        _require(
            clock.now() < deadline,
            f"{label}: timed out waiting for {', '.join(sorted(set(pending)))} on {commit}",
        )
        clock.sleep(POLL_SECONDS)


def check_succeeded(api: Api, repository: str, commit: str, name: str) -> bool:
    run = _actions_check(list_check_runs(api, repository, commit), name)
    return bool(run and run.get("status") == "completed" and run.get("conclusion") == "success")


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
        _require(
            clock.now() < deadline,
            f"{label}: no dispatched {workflow} run appeared; inspect before any retry",
        )
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
        f"release state before any retry ({run.get('html_url')})",
    )
    return run


@contextlib.contextmanager
def tree_at(root: Path, commit: str) -> Iterator[Path]:
    """Yield a checkout of the exact commit, reusing a clean checkout at it."""
    head = git(root, "rev-parse", "HEAD").strip()
    if head == commit and not git(root, "status", "--porcelain", "--untracked-files=no").strip():
        yield root
        return
    with tempfile.TemporaryDirectory(prefix="axiom-release-tree-") as directory:
        checkout = Path(directory) / "tree"
        git(root, "worktree", "add", "--detach", str(checkout), commit)
        try:
            yield checkout
        finally:
            git(root, "worktree", "remove", "--force", str(checkout))


def _evidence_script(tree: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        [sys.executable, "-B", str(tree / "scripts" / "check-release-evidence.py"), *arguments],
        cwd=tree,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise PipelineError(
            f"check-release-evidence.py {arguments[0]} failed: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def render_release_body_at(root: Path, commit: str, version: str) -> str:
    """Render the exact future Release body from the Changelog at a commit."""
    with tree_at(root, commit) as checkout:
        body = _evidence_script(checkout, "render-body", "--expected-version", version)
    return body.decode("utf-8")


def render_release_inputs(
    root: Path, commit: str, version: str, tag: str
) -> tuple[str, bytes, str]:
    """Render the exact Release body, policy asset bytes, and asset name at a commit."""
    tree = git(root, "rev-parse", f"{commit}^{{tree}}").strip()
    with tree_at(root, commit) as checkout:
        body = _evidence_script(checkout, "render-body", "--expected-version", version).decode("utf-8")
        policy = _evidence_script(
            checkout,
            "render-policy",
            "--expected-version",
            version,
            "--expected-tag",
            tag,
            "--expected-commit",
            commit,
            "--expected-tree",
            tree,
        )
    name = f"axiom-v{version}-release-policy-{hashlib.sha256(policy).hexdigest()}.json"
    return body, policy, name


def _upload_policy_asset(
    api: Api, repository: str, release_id: int, policy: bytes, name: str
) -> None:
    uploaded = api.upload(
        f"https://uploads.github.com/repos/{repository}/releases/{release_id}/assets"
        f"?name={_quoted(name)}",
        policy,
        "application/json",
    )
    _require(
        isinstance(uploaded, dict) and uploaded.get("name") == name and uploaded.get("size") == len(policy),
        f"the uploaded policy asset does not match {name}",
    )


def stage_draft(
    api: Api,
    repository: str,
    release: dict[str, Any] | None,
    *,
    tag: str,
    commit: str,
    body: str,
    policy: bytes,
    asset_name: str,
) -> dict[str, Any]:
    """Create or resume the one exact Draft the immutable publisher requires."""
    if release is None:
        release = api.post(
            f"/repos/{repository}/releases",
            {
                "tag_name": tag,
                "target_commitish": commit,
                "name": f"Axiom {tag}",
                "body": body,
                "draft": True,
                "prerelease": False,
            },
        )
        _require(isinstance(release, dict), "Draft creation returned no Release")
    release_id = release.get("id")
    _require(type(release_id) is int and release_id > 0, "the Draft has no numeric Release ID")
    _require(
        release.get("draft") is True
        and release.get("prerelease") is False
        and release.get("tag_name") == tag
        and release.get("target_commitish") == commit
        and release.get("name") == f"Axiom {tag}"
        and release.get("body") == body,
        f"Release {release_id} is not the exact Draft for {tag}; inspect it before any retry",
    )
    assets = release.get("assets") or []
    if not assets:
        _upload_policy_asset(api, repository, release_id, policy, asset_name)
    else:
        _require(
            [asset.get("name") for asset in assets if isinstance(asset, dict)] == [asset_name],
            f"Draft {release_id} holds unexpected assets; inspect it before any retry",
        )
    staged = api.get(f"/repos/{repository}/releases/{release_id}")
    _require(
        isinstance(staged, dict)
        and staged.get("draft") is True
        and [asset.get("name") for asset in staged.get("assets") or []] == [asset_name]
        and (staged.get("assets") or [{}])[0].get("size") == len(policy),
        f"Draft {release_id} does not hold exactly the policy asset {asset_name}",
    )
    return staged


def catalog_status(api: Api, repository: str, tag: str, ref: str = "main") -> str:
    """Report whether both marketplace catalogs at the ref select the tag."""
    for host, relative in MARKETPLACE_CATALOGS:
        content = api.get(f"/repos/{repository}/contents/{relative}?ref={_quoted(ref)}")
        _require(
            isinstance(content, dict) and content.get("encoding") == "base64",
            f"cannot read {relative} at {ref}",
        )
        document = json.loads(base64.b64decode(content["content"]).decode("utf-8"))
        entries = [plugin for plugin in document.get("plugins", []) if plugin.get("name") == "axiom"]
        _require(len(entries) == 1, f"{relative} must contain exactly one axiom plugin")
        if entries[0].get("source") != catalog_source(tag, host):
            return "pending"
    return "current"


def rehearse_catalog_handoff(
    root: Path,
    commit: str,
    version: str,
    tag: str,
    *,
    today: str,
    commands: tuple[tuple[str, ...], ...] = REHEARSAL_COMMANDS,
) -> None:
    """Prove the post-publication catalog handoff before any tag or Release exists.

    The handoff is applied to a disposable worktree of the exact commit, with the
    rehearsal date standing in for the publication date, and the contributor checks
    run on that tree. A failure here stops the pipeline before its first irreversible
    step instead of after the immutable Release, and leaves the checkout untouched.
    """
    validate_commit(commit, "rehearsal commit")
    _require(validate_tag(tag) == version, f"tag {tag} does not name version {version}")
    with tempfile.TemporaryDirectory(prefix="axiom-release-rehearsal-") as directory:
        tree = Path(directory) / "tree"
        git(root, "worktree", "add", "--detach", str(tree), commit)
        try:
            apply_catalog_handoff(
                tree, tag=tag, release_date=today, baseline_commit=commit, recorded_on=today
            )
            for command in commands:
                result = subprocess.run(
                    [sys.executable, "-B", *command],
                    cwd=tree,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    output = (result.stderr or result.stdout).strip()[-REHEARSAL_OUTPUT_LIMIT:]
                    raise PipelineError(
                        f"the rehearsed catalog handoff for {tag} fails "
                        f"`python -B {' '.join(command)}`; fix the candidate before any "
                        f"tag or Release exists:\n{output}"
                    )
        finally:
            git(root, "worktree", "remove", "--force", str(tree))


def run_candidate(
    *,
    root: Path,
    api: Api,
    repository: str,
    base_commit: str,
    head_commit: str,
    reporter: Reporter,
    render_body: Callable[[Path, str, str], str] = render_release_body_at,
    rehearse: Callable[..., None] = rehearse_catalog_handoff,
    today: str | None = None,
) -> str:
    """Classify a pull request, preview its Release, and rehearse its catalog handoff."""
    validate_repository(repository)
    validate_commit(base_commit, "base commit")
    validate_commit(head_commit, "head commit")
    base_version = manifest_version_at(root, base_commit)
    head_version = manifest_version_at(root, head_commit)
    if head_version == base_version:
        reporter.summary(
            "## Release candidate\n\n"
            f"Not a release candidate: the plugin version stays `{head_version}`, "
            "so merging this pull request publishes nothing.\n"
        )
        return "not-a-release"
    _require(
        head_version in immediate_successors(base_version),
        f"version {head_version} is not the next patch, minor, or major version after "
        f"{base_version}",
    )
    base_tag, head_tag = f"v{base_version}", f"v{head_version}"
    _require(
        _is_final_release(find_release(api, repository, base_tag), base_tag),
        f"{base_tag} must be a published immutable Release before the next version",
    )
    _require(read_tag_commit(api, repository, head_tag) is None, f"tag {head_tag} already exists")
    _require(find_release(api, repository, head_tag) is None, f"a Release already uses {head_tag}")
    body = render_body(root, head_commit, head_version)
    rehearse(root, head_commit, head_version, head_tag, today=today or utc_today())
    reporter.summary(
        f"## Release candidate {head_tag}\n\n"
        "| Field | Value |\n| --- | --- |\n"
        f"| Version | `{base_version}` to `{head_version}` |\n"
        f"| Tag | `{head_tag}` |\n"
        f"| Head commit | `{head_commit}` |\n"
        "| Catalog handoff rehearsal | passed on this head |\n\n"
        f"Merging this pull request publishes `{head_tag}` through the Release "
        "pipeline after every check passes on the merged main commit and the catalog "
        "handoff is rehearsed again on that commit.\n\n"
        "### Release body preview\n\n"
        f"{body}\n"
    )
    return "release-candidate"


def run_publish(
    *,
    root: Path,
    api: Api,
    repository: str,
    commit: str,
    reporter: Reporter,
    clock: Clock,
    render_inputs: Callable[
        [Path, str, str, str], tuple[str, bytes, str]
    ] = render_release_inputs,
    rehearse: Callable[..., None] = rehearse_catalog_handoff,
) -> dict[str, str]:
    """Create the tag, publish the immutable Latest release, and observe it.

    Nothing irreversible happens while a check on the release commit is still
    running or has failed, or while the rehearsed catalog handoff fails a repository
    check: the rehearsal runs before the tag, or before the publisher when the tag
    already exists from an earlier attempt.
    """
    validate_repository(repository)
    validate_commit(commit, "pipeline commit")
    version = manifest_version_at(root, commit)
    tag = f"v{version}"
    release = find_release(api, repository, tag)
    tag_commit = read_tag_commit(api, repository, tag)
    rehearsed = False

    if not _is_final_release(release, tag):
        _require(
            release is None or release.get("draft") is True,
            f"the {tag} Release is published but not immutable; inspect it before any retry",
        )
        if tag_commit is None:
            _require(release is None, f"a Release uses {tag} before its tag exists; inspect it")
            main = read_main_commit(api, repository)
            _require(
                main == commit,
                f"main moved from {commit} to {main} before {tag} was created; dispatch the "
                "Release pipeline on main to release the current main commit",
            )
            latest = api.get(f"/repos/{repository}/releases/latest", allow_not_found=True)
            if isinstance(latest, dict):
                latest_version = str(latest.get("tag_name", ""))[1:]
                _require(
                    parse_production_release_version(latest_version) is not None
                    and parse_production_release_version(version)
                    > parse_production_release_version(latest_version),
                    f"{tag} must be newer than the current Latest {latest.get('tag_name')}",
                )
            wait_for_checks(api, repository, commit, REQUIRED_MAIN_CHECKS, clock, "main checks")
            wait_for_settled_checks(api, repository, commit, clock, "main checks")
            rehearse(root, commit, version, tag, today=utc_today())
            rehearsed = True
            dispatch_and_wait(
                api,
                repository,
                TAG_CONTROLLER_WORKFLOW,
                "main",
                {"version": version, "tag": tag},
                commit,
                clock,
                "tag controller",
            )
            tag_commit = read_tag_commit(api, repository, tag)
            _require(tag_commit == commit, f"{tag} must target {commit} after the controller run")
        require_on_main_history(api, repository, tag_commit)
        wait_for_checks(api, repository, tag_commit, (CREATED_TAG_CHECK,), clock, "created tag")
        wait_for_settled_checks(api, repository, tag_commit, clock, "created tag")
        if not rehearsed:
            rehearse(root, tag_commit, version, tag, today=utc_today())
            rehearsed = True
        body, policy, asset_name = render_inputs(root, tag_commit, version, tag)
        release = stage_draft(
            api,
            repository,
            release,
            tag=tag,
            commit=tag_commit,
            body=body,
            policy=policy,
            asset_name=asset_name,
        )
        dispatch_and_wait(
            api,
            repository,
            PUBLISHER_WORKFLOW,
            tag,
            {"tag": tag},
            tag_commit,
            clock,
            "immutable publisher",
        )
        release = api.get(f"/repos/{repository}/releases/{release['id']}")
        _require(_is_final_release(release, tag), f"the {tag} Release is not final and immutable")

    _require(tag_commit is not None, f"the final {tag} Release has no tag")
    _require(release.get("target_commitish") == tag_commit, f"the {tag} Release targets another commit")
    latest = api.get(f"/repos/{repository}/releases/latest")
    _require(
        isinstance(latest, dict) and latest.get("id") == release.get("id"),
        f"GitHub Latest does not identify the {tag} Release",
    )
    if not check_succeeded(api, repository, tag_commit, PUBLISHED_RELEASE_CHECK):
        dispatch_and_wait(
            api,
            repository,
            SIGNATURE_GUARD_WORKFLOW,
            tag,
            {"phase": "published-release"},
            tag_commit,
            clock,
            "published-release observation",
        )
    status = catalog_status(api, repository, tag)
    outputs = {
        "version": version,
        "tag": tag,
        "commit": tag_commit,
        "release-id": str(release["id"]),
        "catalog": status,
    }
    for name, value in outputs.items():
        reporter.output(name, value)
    reporter.summary(
        f"## Published {tag}\n\n"
        "| Field | Value |\n| --- | --- |\n"
        f"| Release | [{release['id']}]({release.get('html_url', '')}) |\n"
        f"| Tag commit | `{tag_commit}` |\n"
        "| Immutable | `true` |\n"
        "| GitHub Latest | `true` |\n"
        f"| `{PUBLISHED_RELEASE_CHECK}` | passed |\n"
        "| Catalog handoff rehearsal | "
        f"{'passed before the first mutation' if rehearsed else 'not needed: the Release was already final'} |\n"
        f"| Marketplace catalogs | {status} |\n"
    )
    return outputs


def _write_json(path: Path, document: Any) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def _read_round_trip_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    document = json.loads(text)
    _require(
        json.dumps(document, indent=2) + "\n" == text,
        f"{path.name} does not round-trip; refusing to reformat it",
    )
    return document


def catalog_changelog_section(revision: int, tag: str, version: str) -> str:
    return (
        f"## Repository policy revision {revision}\n\n"
        "### Changed\n\n"
        f"- Advance the Codex marketplace plugin source to the verified immutable Latest release `{tag}`.\n"
        f"- Advance the Claude Code marketplace plugin source to the same immutable release `{tag}`.\n\n"
        "### Behavioral impact\n\n"
        f"Codex and Claude Code marketplace refresh now select release `{tag}`. This catalog "
        f"handoff preserves plugin version `{version}` and its installed runtime digest.\n\n"
        "### Required action\n\n"
        "None. Existing Codex and Claude Code clients follow each host's native marketplace "
        "refresh and update controls.\n\n"
    )


def apply_catalog_handoff(
    root: Path,
    *,
    tag: str,
    release_date: str,
    baseline_commit: str,
    recorded_on: str,
) -> tuple[str, ...]:
    """Advance both catalogs to the tag and record the next policy revision."""
    version = validate_tag(tag)
    validate_commit(baseline_commit, "handoff baseline")
    for value, label in ((release_date, "release date"), (recorded_on, "record date")):
        _require(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None, f"invalid {label} {value!r}")

    identity_path = root / IDENTITY_RELATIVE
    identity = _read_round_trip_json(identity_path)
    _require(
        identity.get("pluginVersion") == version,
        f"main declares plugin version {identity.get('pluginVersion')}, not {version}; "
        "the catalog handoff no longer applies",
    )
    previous = identity.get("repositoryPolicyRevision")
    _require(type(previous) is int and previous > 0, "the runtime identity has no policy revision")
    revision = previous + 1
    digest = identity["runtimeContract"]["digest"]

    ledger_path = root / LEDGER_RELATIVE
    ledger = _read_round_trip_json(ledger_path)
    _require(
        ledger["revisions"][-1]["revision"] == previous,
        "the policy ledger and runtime identity disagree on the current revision",
    )
    ledger["revisions"].append(
        {
            "revision": revision,
            "recordedOn": recorded_on,
            "baselineCommit": baseline_commit,
            "sourceIssue": None,
            "summary": (
                "Advance the Codex and Claude Code marketplace sources to verified "
                f"immutable Latest {tag}."
            ),
            "runtimeContractDigest": digest,
        }
    )
    _write_json(ledger_path, ledger)

    identity["repositoryPolicyRevision"] = revision
    _write_json(identity_path, identity)
    status_path = root / STATUS_RELATIVE
    status = _read_round_trip_json(status_path)
    _require(
        status["runtimeIdentity"]["repositoryPolicyRevision"] == previous,
        "the release status and runtime identity disagree on the current revision",
    )
    status["runtimeIdentity"]["repositoryPolicyRevision"] = revision
    _write_json(status_path, status)
    identity_document = root / IDENTITY_DOCUMENT_RELATIVE
    identity_document.write_text(
        replace_runtime_identity_block(identity_document.read_text(encoding="utf-8"), identity),
        encoding="utf-8",
    )

    for host, relative in MARKETPLACE_CATALOGS:
        path = root / relative
        catalog = _read_round_trip_json(path)
        entries = [plugin for plugin in catalog.get("plugins", []) if plugin.get("name") == "axiom"]
        _require(len(entries) == 1, f"{relative} must contain exactly one axiom plugin")
        entries[0]["source"] = catalog_source(tag, host)
        _write_json(path, catalog)

    changelog_path = root / CHANGELOG_RELATIVE
    changelog = changelog_path.read_text(encoding="utf-8")
    unreleased = f"\n## {version} - unreleased\n"
    _require(
        changelog.count(unreleased) == 1,
        f"{CHANGELOG_RELATIVE} must contain exactly one `## {version} - unreleased` heading",
    )
    changelog = changelog.replace(unreleased, f"\n## {version} - {release_date}\n")
    first_entry = changelog.find("\n## ")
    _require(first_entry >= 0, f"{CHANGELOG_RELATIVE} has no entries")
    changelog = (
        changelog[: first_entry + 1]
        + catalog_changelog_section(revision, tag, version)
        + changelog[first_entry + 1 :]
    )
    changelog_path.write_text(changelog, encoding="utf-8")
    return (
        CHANGELOG_RELATIVE,
        IDENTITY_DOCUMENT_RELATIVE,
        STATUS_RELATIVE,
        LEDGER_RELATIVE,
        IDENTITY_RELATIVE,
        *(relative for _, relative in MARKETPLACE_CATALOGS),
    )


def _run_publication_checks(root: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-B", str(root / "scripts" / "check-publication.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PipelineError(
            "the rendered catalog handoff fails the publication checks:\n"
            + (result.stderr or result.stdout).strip()
        )


HANDOFF_REQUIRED_PATHS = (
    CHANGELOG_RELATIVE,
    IDENTITY_DOCUMENT_RELATIVE,
    STATUS_RELATIVE,
    LEDGER_RELATIVE,
    IDENTITY_RELATIVE,
)


def _stage_handoff(root: Path, paths: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    git(root, "add", "--", *paths)
    staged = tuple(git(root, "diff", "--cached", "--name-only").split())
    _require(
        set(HANDOFF_REQUIRED_PATHS) <= set(staged) <= set(paths),
        f"the catalog handoff changed an unexpected path set: {', '.join(staged)}",
    )
    return git(root, "write-tree").strip(), staged


def _await_main(api: Api, repository: str, expected: str, clock: Clock) -> None:
    for _ in range(5):
        if read_main_commit(api, repository) == expected:
            return
        clock.sleep(2)
    raise PipelineError(f"main does not hold {expected} after the merge")


def run_catalog(
    *,
    root: Path,
    read_api: Api,
    write_api: Api,
    repository: str,
    tag: str,
    reporter: Reporter,
    clock: Clock,
    today: str,
    run_url: str,
    publication_checks: Callable[[Path], None] = _run_publication_checks,
) -> str:
    """Open, verify, and merge the signed catalog handoff for the verified Latest."""
    validate_repository(repository)
    version = validate_tag(tag)
    latest = read_api.get(f"/repos/{repository}/releases/latest")
    _require(_is_final_release(latest, tag), f"GitHub Latest must be the immutable {tag} Release")
    release_date = str(latest.get("published_at", ""))[:10]
    if catalog_status(read_api, repository, tag) == "current":
        reporter.summary(f"## Marketplace catalogs\n\nBoth catalogs already select `{tag}`.\n")
        return "current"

    main = read_main_commit(read_api, repository)
    _require(
        git(root, "rev-parse", "HEAD").strip() == main
        and not git(root, "status", "--porcelain").strip(),
        f"the checkout must be a clean copy of main {main}; rerun this job",
    )
    branch = f"{CATALOG_BRANCH_PREFIX}{tag}"
    _require(
        read_api.get(f"/repos/{repository}/git/ref/heads/{branch}", allow_not_found=True) is None,
        f"branch {branch} already exists from an earlier attempt; inspect, then delete it "
        "before rerunning this job",
    )
    paths = apply_catalog_handoff(
        root,
        tag=tag,
        release_date=release_date,
        baseline_commit=main,
        recorded_on=today,
    )
    publication_checks(root)
    expected_tree, staged = _stage_handoff(root, paths)
    headline = f"chore: advance the marketplace catalogs to the immutable release {tag}"
    body = (
        f"Advance both marketplace catalogs to the verified immutable Latest release {tag}, "
        "date its Changelog heading, and record the next repository policy revision.\n\n"
        f"Prepared by the Release pipeline run {run_url} from main {main}."
    )
    write_api.post(
        f"/repos/{repository}/git/refs",
        {"ref": f"refs/heads/{branch}", "sha": main},
    )
    data = write_api.graphql(
        CREATE_COMMIT_MUTATION,
        {
            "input": {
                "branch": {"repositoryNameWithOwner": repository, "branchName": branch},
                "expectedHeadOid": main,
                "message": {"headline": headline, "body": body},
                "fileChanges": {
                    "additions": [
                        {
                            "path": path,
                            "contents": base64.b64encode((root / path).read_bytes()).decode("ascii"),
                        }
                        for path in staged
                    ]
                },
            }
        },
    )
    commit = ((((data or {}).get("createCommitOnBranch") or {}).get("commit")) or {}).get("oid")
    _require(isinstance(commit, str) and OID_PATTERN.fullmatch(commit) is not None, "no handoff commit")
    created = read_api.get(f"/repos/{repository}/git/commits/{commit}")
    _require(
        (created.get("tree") or {}).get("sha") == expected_tree
        and [parent.get("sha") for parent in created.get("parents") or []] == [main],
        f"handoff commit {commit} does not hold exactly the validated tree on {main}",
    )
    require_github_signature(read_api, repository, commit)
    pull = write_api.post(
        f"/repos/{repository}/pulls",
        {"title": headline, "head": branch, "base": "main", "body": body},
    )
    number = pull.get("number") if isinstance(pull, dict) else None
    _require(type(number) is int and number > 0, "the catalog pull request was not created")
    _require((pull.get("head") or {}).get("sha") == commit, "the catalog pull request head drifted")
    wait_for_checks(read_api, repository, commit, CATALOG_REQUIRED_CHECKS, clock, "catalog checks")
    wait_for_settled_checks(read_api, repository, commit, clock, "catalog checks")
    latest = read_api.get(f"/repos/{repository}/releases/latest")
    _require(_is_final_release(latest, tag), f"GitHub Latest changed away from {tag}; not merging")
    _require(read_main_commit(read_api, repository) == main, "main moved; rerun after inspection")
    merged = write_api.put(
        f"/repos/{repository}/pulls/{number}/merge",
        {"merge_method": "squash", "sha": commit, "commit_title": headline, "commit_message": body},
    )
    merge_commit = merged.get("sha") if isinstance(merged, dict) else None
    _require(
        isinstance(merged, dict) and merged.get("merged") is True and isinstance(merge_commit, str),
        f"catalog pull request #{number} did not merge",
    )
    _await_main(read_api, repository, merge_commit, clock)
    merged_commit = read_api.get(f"/repos/{repository}/git/commits/{merge_commit}")
    _require(
        (merged_commit.get("tree") or {}).get("sha") == expected_tree,
        "the merged catalog commit does not hold the validated tree",
    )
    require_github_signature(read_api, repository, merge_commit)
    _require(
        catalog_status(read_api, repository, tag, merge_commit) == "current",
        f"the merged catalogs do not select {tag}",
    )
    reference = read_api.get(f"/repos/{repository}/git/ref/heads/{branch}", allow_not_found=True)
    if reference is not None and (reference.get("object") or {}).get("sha") == commit:
        write_api.delete(f"/repos/{repository}/git/refs/heads/{branch}")
    reporter.summary(
        f"## Marketplace catalogs advanced to {tag}\n\n"
        "| Field | Value |\n| --- | --- |\n"
        f"| Pull request | #{number} |\n"
        f"| Merged commit | `{merge_commit}` |\n"
        f"| Plugin version | `{version}` |\n"
        f"| Changelog date | `{release_date}` |\n"
    )
    return "advanced"


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
APP_TOKEN_ACTION = "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1"
SETUP_NODE_ACTION = "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38"
SETUP_PYTHON_STEP = {
    "name": "Set up Python",
    "uses": SETUP_PYTHON_ACTION,
    "with": {"python-version": "3.14.7"},
}
# The publication aggregate validates the JavaScript release guard with Node.js, so
# every job that rehearses or validates the catalog handoff sets it up.
SETUP_NODE_STEP = {
    "name": "Set up Node.js",
    "uses": SETUP_NODE_ACTION,
    "with": {"node-version": "24.19.0", "package-manager-cache": "false"},
}
EXPECTED_WORKFLOW = {
    "name": "Release pipeline",
    "on": {
        "pull_request": {"branches": ["main"], "paths": [CODEX_MANIFEST]},
        "push": {"branches": ["main"], "paths": [CODEX_MANIFEST]},
        "workflow_dispatch": "",
    },
    "permissions": {"contents": "read"},
    "jobs": {
        "release-candidate": {
            "name": "Release candidate",
            "if": "github.event_name == 'pull_request'",
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": "10",
            "concurrency": {
                "group": "release-candidate-${{ github.event.pull_request.number }}",
                "cancel-in-progress": "true",
            },
            "permissions": {"contents": "read"},
            "steps": [
                {
                    "name": "Check out the pull request head",
                    "uses": CHECKOUT_ACTION,
                    "with": {
                        "ref": "${{ github.event.pull_request.head.sha }}",
                        "persist-credentials": "false",
                        "fetch-depth": "0",
                    },
                },
                SETUP_PYTHON_STEP,
                SETUP_NODE_STEP,
                {
                    "name": "Check the version step and preview the Release body",
                    "env": {
                        "BASE_SHA": "${{ github.event.pull_request.base.sha }}",
                        "GITHUB_TOKEN": "${{ github.token }}",
                        "HEAD_SHA": "${{ github.event.pull_request.head.sha }}",
                    },
                    "run": ">-",
                },
            ],
        },
        "publish-release": {
            "name": "Publish release",
            "if": "github.event_name != 'pull_request' && github.ref == 'refs/heads/main'",
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": "150",
            "concurrency": {"group": "release-pipeline", "cancel-in-progress": "false"},
            "permissions": {"actions": "write", "checks": "read", "contents": "write"},
            "outputs": {
                "tag": "${{ steps.publish.outputs.tag }}",
                "catalog": "${{ steps.publish.outputs.catalog }}",
            },
            "steps": [
                {
                    "name": "Check out the main commit",
                    "uses": CHECKOUT_ACTION,
                    "with": {
                        "ref": "${{ github.sha }}",
                        "persist-credentials": "false",
                        "fetch-depth": "0",
                    },
                },
                SETUP_PYTHON_STEP,
                SETUP_NODE_STEP,
                {
                    "name": "Tag, publish, and observe the release",
                    "id": "publish",
                    "env": {"GITHUB_TOKEN": "${{ github.token }}"},
                    "run": ">-",
                },
            ],
        },
        "advance-catalogs": {
            "name": "Advance marketplace catalogs",
            "needs": "publish-release",
            "if": "needs.publish-release.outputs.catalog == 'pending'",
            "environment": "release-tag-creation",
            "runs-on": "ubuntu-24.04",
            "timeout-minutes": "120",
            "concurrency": {"group": "release-catalog", "cancel-in-progress": "false"},
            "permissions": {"checks": "read", "contents": "read"},
            "steps": [
                {
                    "name": "Check out current main",
                    "uses": CHECKOUT_ACTION,
                    "with": {
                        "ref": "main",
                        "persist-credentials": "false",
                        "fetch-depth": "0",
                    },
                },
                SETUP_PYTHON_STEP,
                SETUP_NODE_STEP,
                {
                    "name": "Mint the catalog handoff App token",
                    "id": "catalog-app-token",
                    "uses": APP_TOKEN_ACTION,
                    "with": {
                        "client-id": "${{ vars.AXIOM_RELEASE_APP_CLIENT_ID }}",
                        "private-key": "${{ secrets.AXIOM_RELEASE_APP_PRIVATE_KEY }}",
                        "owner": "${{ github.repository_owner }}",
                        "repositories": "${{ github.event.repository.name }}",
                        "permission-contents": "write",
                        "permission-pull-requests": "write",
                    },
                },
                {
                    "name": "Open, verify, and merge the catalog handoff",
                    "env": {
                        "AXIOM_RELEASE_APP_TOKEN": "${{ steps.catalog-app-token.outputs.token }}",
                        "GITHUB_TOKEN": "${{ github.token }}",
                        "RELEASE_TAG": "${{ needs.publish-release.outputs.tag }}",
                    },
                    "run": ">-",
                },
            ],
        },
    },
}
REQUIRED_COMMAND_ANCHORS = (
    "python3 -B scripts/release-pipeline.py candidate\n"
    '          --repository "$GITHUB_REPOSITORY"\n'
    '          --base-sha "$BASE_SHA"\n'
    '          --head-sha "$HEAD_SHA"\n',
    "python3 -B scripts/release-pipeline.py publish\n"
    '          --repository "$GITHUB_REPOSITORY"\n'
    '          --commit "$GITHUB_SHA"\n',
    "python3 -B scripts/release-pipeline.py catalog\n"
    '          --repository "$GITHUB_REPOSITORY"\n'
    '          --tag "$RELEASE_TAG"\n',
)
FORBIDDEN_WORKFLOW_TEXT = (
    "pull_request_target",
    "workflow_run",
    "schedule:",
    "secrets: inherit",
    "git push",
    "--force",
    "persist-credentials: true",
    "permission-administration",
)


def check_release_pipeline_workflow_text(
    text: str, failures: list[str], *, label: str = ".github/workflows/release-pipeline.yml"
) -> dict[str, Any] | None:
    """Validate the exact release pipeline triggers, jobs, permissions, and actions."""
    try:
        document = _plain(parse_canonical_yaml_document(text, label))
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None
    if document != EXPECTED_WORKFLOW:
        for key in sorted(set(document) | set(EXPECTED_WORKFLOW)):
            if document.get(key) != EXPECTED_WORKFLOW.get(key):
                failures.append(f"{label} {key!r} differs from the reviewed release pipeline contract")
    for anchor in REQUIRED_COMMAND_ANCHORS:
        if text.count(anchor) != 1:
            failures.append(f"{label} must run exactly one {anchor.splitlines()[0]!r} command")
    for forbidden in FORBIDDEN_WORKFLOW_TEXT:
        if forbidden in text:
            failures.append(f"{label} exposes forbidden surface {forbidden!r}")
    if text.count("${{ secrets.") != 1:
        failures.append(f"{label} must read exactly one secret, in the catalog token step")
    return document if not failures else None


def check_release_pipeline_workflow_contract(
    failures: list[str], workflow_path: Path = WORKFLOW_PATH
) -> dict[str, Any] | None:
    """Validate the checked-in release pipeline workflow."""
    try:
        text = workflow_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read {display_path(workflow_path)}: {error}")
        return None
    domain_failures: list[str] = []
    document = check_release_pipeline_workflow_text(
        text, domain_failures, label=display_path(workflow_path)
    )
    failures.extend(domain_failures)
    return document


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


__all__ = (
    "CATALOG_REQUIRED_CHECKS",
    "CREATED_TAG_CHECK",
    "Clock",
    "EXPECTED_WORKFLOW",
    "GitHubClient",
    "PIPELINE_JOB_NAMES",
    "PUBLISHED_RELEASE_CHECK",
    "PipelineError",
    "REHEARSAL_COMMANDS",
    "REQUIRED_MAIN_CHECKS",
    "Reporter",
    "WORKFLOW_PATH",
    "apply_catalog_handoff",
    "catalog_status",
    "check_release_pipeline_workflow_contract",
    "check_release_pipeline_workflow_text",
    "dispatch_and_wait",
    "immediate_successors",
    "manifest_version_at",
    "rehearse_catalog_handoff",
    "run_candidate",
    "run_catalog",
    "run_publish",
    "stage_draft",
    "utc_today",
    "wait_for_checks",
    "wait_for_settled_checks",
)
