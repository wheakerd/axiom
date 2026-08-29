"""Closed pre-creation policy for one protected production release tag."""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from .context import REPOSITORY_ROOT, display_path
from .release_versions import parse_production_release_version
from .yaml_subset import CanonicalYamlError, CanonicalYamlScalar, parse_canonical_yaml_document


API_VERSION = "2026-03-10"
GITHUB_ACTIONS_APP_ID = 15368
MAIN_RULESET = "require-signed-commits-on-main"
INTEGRITY_RULESET = "require-github-signed-release-tags"
CREATION_RULESET = "restrict-release-tag-creation"
MAIN_REQUIRED_CHECKS = ("repository-guards", "unit-and-integration-tests")
SIGNED_MAIN_CHECK = "Verify signed main history"
OID_PATTERN = re.compile(r"[0-9a-f]{40}")
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
APP_SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class ControllerError(RuntimeError):
    """A fail-closed release-tag controller decision."""


class GitHubRequestError(ControllerError):
    """One GitHub request failed without an automatic retry."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class ApiClient(Protocol):
    def get(self, path: str, *, allow_not_found: bool = False) -> Any: ...

    def post(self, path: str, payload: dict[str, Any]) -> Any: ...


class GitHubApi:
    """Small no-retry GitHub JSON client used by the protected workflow."""

    def __init__(self, api_url: str, token: str) -> None:
        if not api_url.startswith("https://"):
            raise ControllerError("GitHub API URL must use HTTPS")
        if not token:
            raise ControllerError("GitHub API token must be non-empty")
        self.api_url = api_url.rstrip("/")
        self.token = token

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        *,
        allow_not_found: bool = False,
    ) -> Any:
        if not path.startswith("/"):
            raise ControllerError("GitHub API paths must be absolute")
        body = None
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_url}{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "axiom-release-tag-controller",
                "X-GitHub-Api-Version": API_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            if allow_not_found and error.code == 404:
                return None
            try:
                detail = json.loads(error.read().decode("utf-8")).get("message")
            except (UnicodeError, json.JSONDecodeError, AttributeError):
                detail = None
            suffix = f": {detail}" if isinstance(detail, str) and detail else ""
            raise GitHubRequestError(
                f"GitHub {method} {path} returned HTTP {error.code}{suffix}",
                status=error.code,
            ) from error
        except (OSError, urllib.error.URLError) as error:
            raise GitHubRequestError(
                f"GitHub {method} {path} did not return a definitive response: {error}"
            ) from error
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise GitHubRequestError(
                f"GitHub {method} {path} returned invalid JSON"
            ) from error

    def get(self, path: str, *, allow_not_found: bool = False) -> Any:
        return self._request("GET", path, None, allow_not_found=allow_not_found)

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request("POST", path, payload)


@dataclass(frozen=True)
class ReleaseTagRequest:
    repository: str
    version: str
    tag: str
    expected_main_sha: str
    expected_app_id: int


@dataclass(frozen=True)
class ReleaseAppTokenIdentity:
    app_slug: str
    installation_id: int


def validate_request(request: ReleaseTagRequest) -> None:
    if REPOSITORY_PATTERN.fullmatch(request.repository) is None:
        raise ControllerError("repository must be one exact owner/name pair")
    if parse_production_release_version(request.version) is None:
        raise ControllerError(
            "requested version must be one stable numeric production release version"
        )
    if request.tag != f"v{request.version}":
        raise ControllerError("requested tag must exactly equal v<requested version>")
    if OID_PATTERN.fullmatch(request.expected_main_sha) is None:
        raise ControllerError("expected main SHA must be one lowercase 40-character Git SHA")
    if type(request.expected_app_id) is not int or request.expected_app_id <= 0:
        raise ControllerError("expected release App ID must be a positive integer")


def validate_app_token_identity(identity: ReleaseAppTokenIdentity) -> None:
    if (
        type(identity.app_slug) is not str
        or APP_SLUG_PATTERN.fullmatch(identity.app_slug) is None
    ):
        raise ControllerError("release App slug must be one lowercase GitHub App slug")
    if type(identity.installation_id) is not int or identity.installation_id <= 0:
        raise ControllerError("release App installation must have a positive ID")


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ControllerError(f"{label} must be one JSON object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if type(value) is not list:
        raise ControllerError(f"{label} must be one JSON array")
    return value


def _require_oid(value: Any, label: str) -> str:
    if type(value) is not str or OID_PATTERN.fullmatch(value) is None:
        raise ControllerError(f"{label} must be one lowercase 40-character Git SHA")
    return value


def _quoted(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _decode_manifest_version(document: Any, path: str) -> str:
    content = _require_object(document, path)
    if (
        content.get("type") != "file"
        or content.get("encoding") != "base64"
        or type(content.get("content")) is not str
    ):
        raise ControllerError(f"{path} must resolve to one base64 GitHub content file")
    try:
        raw = base64.b64decode(
            content["content"].replace("\n", ""), validate=True
        ).decode("utf-8")
        manifest = json.loads(raw)
    except (ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise ControllerError(f"{path} does not contain valid UTF-8 JSON") from error
    manifest = _require_object(manifest, path)
    version = manifest.get("version")
    if type(version) is not str:
        raise ControllerError(f"{path}.version must be a string")
    return version


def _rule_map(ruleset: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    rules = _require_list(ruleset.get("rules"), f"{label}.rules")
    mapped: dict[str, dict[str, Any]] = {}
    for index, raw_rule in enumerate(rules):
        rule = _require_object(raw_rule, f"{label}.rules[{index}]")
        rule_type = rule.get("type")
        if type(rule_type) is not str or not rule_type:
            raise ControllerError(f"{label}.rules[{index}].type must be non-empty")
        if rule_type in mapped:
            raise ControllerError(f"{label} repeats rule type {rule_type!r}")
        mapped[rule_type] = rule
    return mapped


def _validate_ruleset_envelope(
    ruleset: dict[str, Any],
    request: ReleaseTagRequest,
    expected_name: str,
    target: str,
) -> None:
    expected = {
        "name": expected_name,
        "target": target,
        "source_type": "Repository",
        "source": request.repository,
        "enforcement": "active",
    }
    for field, value in expected.items():
        if ruleset.get(field) != value:
            raise ControllerError(f"{expected_name}.{field} must equal {value!r}")
    conditions = _require_object(ruleset.get("conditions"), f"{expected_name}.conditions")
    ref_name = _require_object(conditions.get("ref_name"), f"{expected_name}.conditions.ref_name")
    expected_ref = "refs/heads/main" if target == "branch" else "refs/tags/v*"
    if conditions != {
        "ref_name": {"exclude": [], "include": [expected_ref]}
    } or ref_name != {"exclude": [], "include": [expected_ref]}:
        raise ControllerError(f"{expected_name} must target only {expected_ref}")


def _require_rule_shape(
    rule: dict[str, Any],
    label: str,
    *,
    parameterized: bool,
) -> None:
    expected = {"type", "parameters"} if parameterized else {"type"}
    if set(rule) != expected:
        raise ControllerError(f"{label} rule fields drifted")


def _validate_main_ruleset(ruleset: dict[str, Any], request: ReleaseTagRequest) -> None:
    _validate_ruleset_envelope(ruleset, request, MAIN_RULESET, "branch")
    rules = _rule_map(ruleset, MAIN_RULESET)
    if set(rules) != {
        "pull_request",
        "non_fast_forward",
        "required_signatures",
        "required_status_checks",
    }:
        raise ControllerError(f"{MAIN_RULESET} rule set drifted")
    _require_rule_shape(rules["pull_request"], "main pull-request", parameterized=True)
    _require_rule_shape(
        rules["required_status_checks"], "main required-status-check", parameterized=True
    )
    _require_rule_shape(rules["non_fast_forward"], "main non-fast-forward", parameterized=False)
    _require_rule_shape(rules["required_signatures"], "main signature", parameterized=False)
    pull = _require_object(rules["pull_request"].get("parameters"), "main pull-request parameters")
    expected_pull = {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": False,
        "required_reviewers": [],
        "require_code_owner_review": False,
        "require_last_push_approval": False,
        "required_review_thread_resolution": False,
        "require_extra_approval_for_unattributed_changes": True,
        "allowed_merge_methods": ["squash"],
    }
    if pull != expected_pull:
        raise ControllerError(f"{MAIN_RULESET} pull-request policy drifted")
    checks = _require_object(
        rules["required_status_checks"].get("parameters"),
        "main required-status-check parameters",
    )
    expected_checks = [
        {"context": name, "integration_id": GITHUB_ACTIONS_APP_ID}
        for name in MAIN_REQUIRED_CHECKS
    ]
    if checks != {
        "strict_required_status_checks_policy": True,
        "do_not_enforce_on_create": False,
        "required_status_checks": expected_checks,
    }:
        raise ControllerError(f"{MAIN_RULESET} required checks drifted")
    if ruleset.get("bypass_actors") != [] or ruleset.get("current_user_can_bypass") != "never":
        raise ControllerError(f"{MAIN_RULESET} must have no bypass actor")


def _validate_integrity_ruleset(ruleset: dict[str, Any], request: ReleaseTagRequest) -> None:
    _validate_ruleset_envelope(ruleset, request, INTEGRITY_RULESET, "tag")
    rules = _rule_map(ruleset, INTEGRITY_RULESET)
    if set(rules) != {
        "required_signatures",
        "required_status_checks",
        "deletion",
        "non_fast_forward",
    }:
        raise ControllerError(f"{INTEGRITY_RULESET} rule set drifted")
    _require_rule_shape(
        rules["required_status_checks"], "tag required-status-check", parameterized=True
    )
    for rule_type in ("required_signatures", "deletion", "non_fast_forward"):
        _require_rule_shape(rules[rule_type], f"tag {rule_type}", parameterized=False)
    checks = _require_object(
        rules["required_status_checks"].get("parameters"),
        "tag required-status-check parameters",
    )
    if checks != {
        "strict_required_status_checks_policy": False,
        "do_not_enforce_on_create": False,
        "required_status_checks": [
            {"context": SIGNED_MAIN_CHECK, "integration_id": GITHUB_ACTIONS_APP_ID}
        ],
    }:
        raise ControllerError(
            f"{INTEGRITY_RULESET} must require only {SIGNED_MAIN_CHECK!r}"
        )
    if ruleset.get("bypass_actors") != [] or ruleset.get("current_user_can_bypass") != "never":
        raise ControllerError(f"{INTEGRITY_RULESET} must retain no bypass actor")


def _validate_creation_ruleset(ruleset: dict[str, Any], request: ReleaseTagRequest) -> None:
    _validate_ruleset_envelope(ruleset, request, CREATION_RULESET, "tag")
    rules = _rule_map(ruleset, CREATION_RULESET)
    if set(rules) != {"creation"}:
        raise ControllerError(f"{CREATION_RULESET} must contain only the creation rule")
    _require_rule_shape(rules["creation"], "tag creation", parameterized=False)
    expected_actor = [{
        "actor_id": request.expected_app_id,
        "actor_type": "Integration",
        "bypass_mode": "always",
    }]
    if ruleset.get("bypass_actors") != expected_actor:
        raise ControllerError(
            f"{CREATION_RULESET} must bypass only the dedicated release GitHub App"
        )
    if ruleset.get("current_user_can_bypass") != "always":
        raise ControllerError(
            f"the dedicated release GitHub App cannot bypass {CREATION_RULESET}"
        )


def _normalize_ruleset(ruleset: dict[str, Any]) -> dict[str, Any]:
    return {
        key: ruleset.get(key)
        for key in (
            "id",
            "name",
            "target",
            "source_type",
            "source",
            "enforcement",
            "conditions",
            "rules",
            "bypass_actors",
            "current_user_can_bypass",
            "updated_at",
        )
    }


def _load_named_rulesets(
    admin: ApiClient,
    request: ReleaseTagRequest,
) -> dict[str, dict[str, Any]]:
    index = _require_list(
        admin.get(f"/repos/{request.repository}/rulesets?includes_parents=true&per_page=100"),
        "ruleset index",
    )
    expected_names = {MAIN_RULESET, INTEGRITY_RULESET, CREATION_RULESET}
    ids: dict[str, int] = {}
    for item in index:
        summary = _require_object(item, "ruleset summary")
        name = summary.get("name")
        if name not in expected_names:
            continue
        identifier = summary.get("id")
        if type(identifier) is not int or identifier <= 0:
            raise ControllerError(f"ruleset {name!r} has no positive ID")
        if name in ids:
            raise ControllerError(f"ruleset index repeats {name!r}")
        ids[name] = identifier
    if set(ids) != expected_names:
        missing = ", ".join(sorted(expected_names - set(ids)))
        raise ControllerError(f"live ruleset index is missing: {missing}")
    detailed: dict[str, dict[str, Any]] = {}
    for name, identifier in ids.items():
        ruleset = _require_object(
            admin.get(
                f"/repos/{request.repository}/rulesets/{identifier}?includes_parents=true"
            ),
            f"ruleset {name}",
        )
        if ruleset.get("id") != identifier:
            raise ControllerError(f"ruleset {name!r} changed identity during read-back")
        detailed[name] = ruleset
    return detailed


def _validate_app_identity(
    admin: ApiClient,
    request: ReleaseTagRequest,
    token_identity: ReleaseAppTokenIdentity,
) -> dict[str, Any]:
    validate_app_token_identity(token_identity)
    repositories = _require_object(
        admin.get("/installation/repositories?per_page=100"),
        "App installation repositories",
    )
    entries = _require_list(repositories.get("repositories"), "App installation repositories")
    names = [
        _require_object(item, "App installation repository").get("full_name")
        for item in entries
    ]
    if repositories.get("total_count") != 1 or names != [request.repository]:
        raise ControllerError("release App token must be scoped to exactly this repository")
    return {
        "appId": request.expected_app_id,
        "appSlug": token_identity.app_slug,
        "installationId": token_identity.installation_id,
        "repositories": names,
    }


def _check_run_evidence(document: Any, request: ReleaseTagRequest) -> list[dict[str, Any]]:
    payload = _require_object(document, "check-runs response")
    runs = _require_list(payload.get("check_runs"), "check-runs response.check_runs")
    if payload.get("total_count") != len(runs):
        raise ControllerError("check-runs response must fit in one complete latest-results page")
    required_names = (*MAIN_REQUIRED_CHECKS, SIGNED_MAIN_CHECK)
    evidence: list[dict[str, Any]] = []
    for name in required_names:
        matches = [run for run in runs if type(run) is dict and run.get("name") == name]
        if len(matches) != 1:
            raise ControllerError(f"exactly one latest check run named {name!r} is required")
        run = matches[0]
        app = _require_object(run.get("app"), f"check run {name!r}.app")
        run_id = run.get("id")
        completed_at = run.get("completed_at")
        if (
            type(run_id) is not int
            or run_id <= 0
            or type(completed_at) is not str
            or not completed_at
            or run.get("head_sha") != request.expected_main_sha
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
            or app.get("id") != GITHUB_ACTIONS_APP_ID
            or app.get("slug") != "github-actions"
        ):
            raise ControllerError(
                f"check run {name!r} must be a successful GitHub Actions result for exact main"
            )
        evidence.append(
            {
                "id": run_id,
                "name": name,
                "headSha": request.expected_main_sha,
                "status": "completed",
                "conclusion": "success",
                "appId": GITHUB_ACTIONS_APP_ID,
                "completedAt": completed_at,
            }
        )
    return evidence


def collect_state(
    read: ApiClient,
    admin: ApiClient,
    request: ReleaseTagRequest,
    app_identity: dict[str, Any],
) -> dict[str, Any]:
    repository = _require_object(read.get(f"/repos/{request.repository}"), "repository")
    if repository.get("full_name") != request.repository or repository.get("default_branch") != "main":
        raise ControllerError("release repository identity or default branch drifted")

    main_ref = _require_object(
        read.get(f"/repos/{request.repository}/git/ref/heads/main"),
        "main ref",
    )
    main_object = _require_object(main_ref.get("object"), "main ref object")
    if main_ref.get("ref") != "refs/heads/main" or main_object.get("type") != "commit":
        raise ControllerError("main must resolve directly to one commit")
    main_sha = _require_oid(main_object.get("sha"), "main ref SHA")
    if main_sha != request.expected_main_sha:
        raise ControllerError("live main does not equal the workflow's authorized commit")

    commit = _require_object(
        read.get(f"/repos/{request.repository}/git/commits/{main_sha}"),
        "main Git commit",
    )
    tree = _require_object(commit.get("tree"), "main Git tree")
    if _require_oid(commit.get("sha"), "main Git commit SHA") != main_sha:
        raise ControllerError("Git commit response changed identity")
    tree_sha = _require_oid(tree.get("sha"), "main Git tree SHA")

    manifest_versions: dict[str, str] = {}
    for path in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
        content = read.get(
            f"/repos/{request.repository}/contents/{path}?ref={main_sha}"
        )
        manifest_versions[path] = _decode_manifest_version(content, path)
    if set(manifest_versions.values()) != {request.version}:
        raise ControllerError("both exact-main manifests must equal the requested version")

    rest_commit = _require_object(
        read.get(f"/repos/{request.repository}/commits/{main_sha}"),
        "REST commit",
    )
    verification = _require_object(rest_commit.get("commit"), "REST commit envelope").get(
        "verification"
    )
    verification = _require_object(verification, "REST commit verification")
    if (
        rest_commit.get("sha") != main_sha
        or verification.get("verified") is not True
        or verification.get("reason") != "valid"
    ):
        raise ControllerError("exact main commit must have valid REST signature evidence")

    graphql = _require_object(
        read.post(
            "/graphql",
            {
                "query": (
                    "query($owner: String!, $name: String!, $oid: GitObjectID!) { "
                    "repository(owner: $owner, name: $name) { object(oid: $oid) { "
                    "... on Commit { oid signature { isValid state wasSignedByGitHub } } } } }"
                ),
                "variables": {
                    "owner": request.repository.split("/", 1)[0],
                    "name": request.repository.split("/", 1)[1],
                    "oid": main_sha,
                },
            },
        ),
        "GraphQL response",
    )
    data = _require_object(graphql.get("data"), "GraphQL data")
    graph_repository = _require_object(data.get("repository"), "GraphQL repository")
    graph_commit = _require_object(graph_repository.get("object"), "GraphQL commit")
    signature = _require_object(graph_commit.get("signature"), "GraphQL signature")
    if (
        graph_commit.get("oid") != main_sha
        or signature.get("isValid") is not True
        or signature.get("state") != "VALID"
        or signature.get("wasSignedByGitHub") is not True
    ):
        raise ControllerError("exact main commit must be signed with GitHub's signing key")

    checks = _check_run_evidence(
        read.get(
            f"/repos/{request.repository}/commits/{main_sha}/check-runs?filter=latest&per_page=100"
        ),
        request,
    )
    tag_ref = read.get(
        f"/repos/{request.repository}/git/ref/tags/{_quoted(request.tag)}",
        allow_not_found=True,
    )
    if tag_ref is not None:
        raise ControllerError(f"release tag {request.tag} already exists; no mutation attempted")
    release = read.get(
        f"/repos/{request.repository}/releases/tags/{_quoted(request.tag)}",
        allow_not_found=True,
    )
    if release is not None:
        raise ControllerError(f"GitHub Release {request.tag} already exists; no mutation attempted")

    rulesets = _load_named_rulesets(admin, request)
    _validate_main_ruleset(rulesets[MAIN_RULESET], request)
    _validate_integrity_ruleset(rulesets[INTEGRITY_RULESET], request)
    _validate_creation_ruleset(rulesets[CREATION_RULESET], request)

    return {
        "schemaVersion": "1",
        "repository": request.repository,
        "requestedVersion": request.version,
        "requestedTag": request.tag,
        "mainSha": main_sha,
        "mainTree": tree_sha,
        "manifestVersions": manifest_versions,
        "checks": checks,
        "restVerification": {
            "verified": True,
            "reason": "valid",
        },
        "graphqlSignature": {
            "oid": main_sha,
            "isValid": True,
            "state": "VALID",
            "wasSignedByGitHub": True,
        },
        "tagAbsent": True,
        "releaseAbsent": True,
        "appIdentity": app_identity,
        "rulesets": {
            name: _normalize_ruleset(rulesets[name])
            for name in (MAIN_RULESET, INTEGRITY_RULESET, CREATION_RULESET)
        },
    }


def _validate_created_ref(document: Any, request: ReleaseTagRequest) -> dict[str, str]:
    reference = _require_object(document, "created tag ref")
    obj = _require_object(reference.get("object"), "created tag ref object")
    expected_ref = f"refs/tags/{request.tag}"
    if (
        reference.get("ref") != expected_ref
        or obj.get("type") != "commit"
        or obj.get("sha") != request.expected_main_sha
    ):
        raise ControllerError("created tag read-back does not match the authorized ref and commit")
    return {"ref": expected_ref, "sha": request.expected_main_sha}


def run_controller(
    read: ApiClient,
    admin_and_mutation: ApiClient,
    request: ReleaseTagRequest,
    token_identity: ReleaseAppTokenIdentity,
) -> dict[str, Any]:
    """Validate twice, attempt one ref creation, and immediately read it back."""
    validate_request(request)
    validate_app_token_identity(token_identity)
    initial_identity = _validate_app_identity(
        admin_and_mutation, request, token_identity
    )
    initial = collect_state(read, admin_and_mutation, request, initial_identity)
    final_identity = _validate_app_identity(
        admin_and_mutation, request, token_identity
    )
    final = collect_state(read, admin_and_mutation, request, final_identity)
    if initial != final:
        raise ControllerError("release state changed during the final live-state gate")

    path = f"/repos/{request.repository}/git/refs"
    payload = {
        "ref": f"refs/tags/{request.tag}",
        "sha": request.expected_main_sha,
    }
    try:
        created = admin_and_mutation.post(path, payload)
    except GitHubRequestError as error:
        readback = read.get(
            f"/repos/{request.repository}/git/ref/tags/{_quoted(request.tag)}",
            allow_not_found=True,
        )
        detail = "absent"
        if readback is not None:
            try:
                exact = _validate_created_ref(readback, request)
            except ControllerError as readback_error:
                detail = str(readback_error)
            else:
                detail = f"present at {exact['sha']}"
        raise ControllerError(
            "the single tag-creation attempt did not return a definitive success; "
            f"read-back is {detail}; the controller will not retry"
        ) from error

    created_ref = _validate_created_ref(created, request)
    readback = read.get(
        f"/repos/{request.repository}/git/ref/tags/{_quoted(request.tag)}"
    )
    verified_ref = _validate_created_ref(readback, request)
    if created_ref != verified_ref:
        raise ControllerError("created tag response and immediate read-back disagree")
    return {
        "outcome": "created-and-verified",
        "version": request.version,
        "tag": request.tag,
        "commit": request.expected_main_sha,
        "tree": final["mainTree"],
        "appId": request.expected_app_id,
        "appSlug": final_identity["appSlug"],
        "installationId": final_identity["installationId"],
        "mutationAttempts": 1,
    }


def canonical_result(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def check_controller_workflow_contract(failures: list[str]) -> None:
    """Validate the secret boundary and exact controller workflow shape."""
    path = REPOSITORY_ROOT / ".github" / "workflows" / "create-protected-release-tag.yml"
    label = display_path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {label}: {error}")
        return
    try:
        document = parse_canonical_yaml_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        return

    def scalar(value: Any) -> str | None:
        return value.value if isinstance(value, CanonicalYamlScalar) else None

    if set(document) != {"name", "on", "permissions", "concurrency", "jobs"}:
        failures.append(f"{label} must contain only its canonical controller fields")
    if scalar(document.get("name")) != "Create protected release tag":
        failures.append(f"{label} must keep its exact public workflow name")

    triggers = document.get("on")
    dispatch = triggers.get("workflow_dispatch") if isinstance(triggers, dict) else None
    inputs = dispatch.get("inputs") if isinstance(dispatch, dict) else None
    if (
        not isinstance(triggers, dict)
        or set(triggers) != {"workflow_dispatch"}
        or not isinstance(dispatch, dict)
        or set(dispatch) != {"inputs"}
        or not isinstance(inputs, dict)
        or set(inputs) != {"version", "tag"}
    ):
        failures.append(f"{label} must be manual-only with exact version and tag inputs")
    else:
        for name in ("version", "tag"):
            field = inputs.get(name)
            if (
                not isinstance(field, dict)
                or set(field) != {"description", "required", "type"}
                or scalar(field.get("required")) != "true"
                or scalar(field.get("type")) != "string"
            ):
                failures.append(f"{label} input {name!r} must be one required string")

    permissions = document.get("permissions")
    if not isinstance(permissions, dict) or {
        key: scalar(value) for key, value in permissions.items()
    } != {"contents": "read", "checks": "read"}:
        failures.append(f"{label} GITHUB_TOKEN must grant only contents/read and checks/read")

    concurrency = document.get("concurrency")
    if (
        not isinstance(concurrency, dict)
        or set(concurrency) != {"group", "cancel-in-progress"}
        or scalar(concurrency.get("group")) != "create-protected-release-tag"
        or scalar(concurrency.get("cancel-in-progress")) != "false"
    ):
        failures.append(f"{label} must serialize every repository release-tag creation")

    jobs = document.get("jobs")
    job = jobs.get("create-protected-release-tag") if isinstance(jobs, dict) else None
    if not isinstance(jobs, dict) or set(jobs) != {"create-protected-release-tag"}:
        failures.append(f"{label} must declare one controller job")
        return
    expected_job_fields = {
        "name",
        "if",
        "environment",
        "runs-on",
        "timeout-minutes",
        "steps",
    }
    if not isinstance(job, dict) or set(job) != expected_job_fields:
        failures.append(f"{label} controller job shape drifted")
        return
    expected_scalars = {
        "name": "Create protected release tag",
        "if": "github.ref == 'refs/heads/main'",
        "environment": "release-tag-creation",
        "runs-on": "ubuntu-24.04",
        "timeout-minutes": "10",
    }
    for field, expected in expected_scalars.items():
        if scalar(job.get(field)) != expected:
            failures.append(f"{label} jobs.create-protected-release-tag.{field} drifted")

    steps = job.get("steps")
    if not isinstance(steps, list) or len(steps) != 5 or any(
        not isinstance(step, dict) for step in steps
    ):
        failures.append(f"{label} must contain five exact controller steps")
        return
    checkout, python, validate, token, create = steps
    checkout_with = checkout.get("with")
    if (
        scalar(checkout.get("uses"))
        != "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
        or not isinstance(checkout_with, dict)
        or {key: scalar(value) for key, value in checkout_with.items()}
        != {"ref": "${{ github.sha }}", "persist-credentials": "false"}
    ):
        failures.append(f"{label} checkout must bind github.sha without credentials")
    python_with = python.get("with")
    if (
        scalar(python.get("uses"))
        != "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
        or not isinstance(python_with, dict)
        or {key: scalar(value) for key, value in python_with.items()}
        != {"python-version": "3.14.7"}
    ):
        failures.append(f"{label} must pin the exact Python environment")

    token_with = token.get("with")
    expected_token_with = {
        "client-id": "${{ vars.AXIOM_RELEASE_APP_CLIENT_ID }}",
        "private-key": "${{ secrets.AXIOM_RELEASE_APP_PRIVATE_KEY }}",
        "owner": "${{ github.repository_owner }}",
        "repositories": "${{ github.event.repository.name }}",
        "permission-administration": "read",
        "permission-contents": "write",
    }
    if (
        scalar(token.get("id")) != "release-app-token"
        or scalar(token.get("uses"))
        != "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1"
        or not isinstance(token_with, dict)
        or {key: scalar(value) for key, value in token_with.items()}
        != expected_token_with
    ):
        failures.append(
            f"{label} must mint one repository-scoped App token with administration/read "
            "and contents/write only"
        )

    create_env = create.get("env")
    expected_create_env = {
        "AXIOM_RELEASE_APP_ID": "${{ vars.AXIOM_RELEASE_APP_ID }}",
        "AXIOM_RELEASE_APP_SLUG": "${{ steps.release-app-token.outputs.app-slug }}",
        "AXIOM_RELEASE_APP_TOKEN": "${{ steps.release-app-token.outputs.token }}",
        "AXIOM_RELEASE_INSTALLATION_ID": (
            "${{ steps.release-app-token.outputs.installation-id }}"
        ),
        "GITHUB_TOKEN": "${{ github.token }}",
        "RELEASE_TAG": "${{ inputs.tag }}",
        "RELEASE_VERSION": "${{ inputs.version }}",
    }
    if (
        not isinstance(create_env, dict)
        or {key: scalar(value) for key, value in create_env.items()}
        != expected_create_env
    ):
        failures.append(
            f"{label} must bind the exact App-token identity outputs into the controller"
        )

    if "python3 scripts/create-release-tag.py validate-request" not in text:
        failures.append(f"{label} must validate the request before minting a secret token")
    if "python3 scripts/create-release-tag.py create" not in text:
        failures.append(f"{label} must execute the closed creation controller")
    request_offset = text.find("python3 scripts/create-release-tag.py validate-request")
    token_offset = text.find("actions/create-github-app-token@")
    create_offset = text.find("python3 scripts/create-release-tag.py create")
    if not (0 <= request_offset < token_offset < create_offset):
        failures.append(f"{label} controller steps must preserve request, token, create order")
    if text.count("${{ secrets.AXIOM_RELEASE_APP_PRIVATE_KEY }}") != 1:
        failures.append(f"{label} must consume the private key in exactly one token step")
    if text.count("${{ steps.release-app-token.outputs.token }}") != 1:
        failures.append(f"{label} must pass one minted token to one controller step")
    if text.count("${{ steps.release-app-token.outputs.app-slug }}") != 1:
        failures.append(f"{label} must pass one App slug to one controller step")
    if text.count("${{ steps.release-app-token.outputs.installation-id }}") != 1:
        failures.append(f"{label} must pass one installation ID to one controller step")
    if '--app-slug "$AXIOM_RELEASE_APP_SLUG"' not in text:
        failures.append(f"{label} must bind the App slug CLI input")
    if '--installation-id "$AXIOM_RELEASE_INSTALLATION_ID"' not in text:
        failures.append(f"{label} must bind the installation ID CLI input")
    for forbidden in (
        "pull_request_target",
        "\n  pull_request:",
        "\n  push:",
        "\n  release:",
        "\n  schedule:",
        "permission-administration: write",
        "persist-credentials: true",
        "git push",
        "git tag",
    ):
        if forbidden in text:
            failures.append(f"{label} exposes forbidden mutation surface {forbidden!r}")
