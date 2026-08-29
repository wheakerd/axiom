"""Regression and disposable-repository tests for protected tag creation."""

from __future__ import annotations

import base64
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

from axiom_validation.context import RELEASE_VERSION
from axiom_validation.release_tag_controller import (
    CREATION_RULESET,
    GITHUB_ACTIONS_APP_ID,
    INTEGRITY_RULESET,
    MAIN_REQUIRED_CHECKS,
    MAIN_RULESET,
    SIGNED_MAIN_CHECK,
    ControllerError,
    GitHubRequestError,
    ReleaseTagRequest,
    run_controller,
    validate_request,
)


REPOSITORY = "wheakerd/axiom"
APP_ID = 424242


class FixtureRepository:
    def __init__(self, *, main_sha: str = "1" * 40, tree_sha: str = "2" * 40) -> None:
        self.main_sha = main_sha
        self.tree_sha = tree_sha
        self.version = RELEASE_VERSION
        self.tag_ref: dict[str, Any] | None = None
        self.release: dict[str, Any] | None = None
        self.mutation_attempts = 0
        self.raise_after_creation = False
        self.installation_repositories = [REPOSITORY]
        self.snapshot_reads = 0
        self.before_second_snapshot: Callable[[FixtureRepository], None] | None = None
        self.signature = {
            "isValid": True,
            "state": "VALID",
            "wasSignedByGitHub": True,
        }
        self.check_runs = [
            {
                "id": index + 100,
                "name": name,
                "head_sha": main_sha,
                "status": "completed",
                "conclusion": "success",
                "completed_at": f"2026-08-28T17:0{index}:00Z",
                "app": {"id": GITHUB_ACTIONS_APP_ID, "slug": "github-actions"},
            }
            for index, name in enumerate((*MAIN_REQUIRED_CHECKS, SIGNED_MAIN_CHECK))
        ]
        self.rulesets = self._rulesets()

    def _rulesets(self) -> dict[str, dict[str, Any]]:
        envelope = {
            "source_type": "Repository",
            "source": REPOSITORY,
            "enforcement": "active",
            "updated_at": "2026-08-28T18:00:00Z",
        }
        main = {
            **envelope,
            "id": 1,
            "name": MAIN_RULESET,
            "target": "branch",
            "conditions": {
                "ref_name": {"exclude": [], "include": ["refs/heads/main"]}
            },
            "rules": [
                {
                    "type": "pull_request",
                    "parameters": {
                        "required_approving_review_count": 0,
                        "dismiss_stale_reviews_on_push": False,
                        "required_reviewers": [],
                        "require_code_owner_review": False,
                        "require_last_push_approval": False,
                        "required_review_thread_resolution": False,
                        "require_extra_approval_for_unattributed_changes": True,
                        "allowed_merge_methods": ["squash"],
                    },
                },
                {"type": "non_fast_forward"},
                {"type": "required_signatures"},
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": True,
                        "do_not_enforce_on_create": False,
                        "required_status_checks": [
                            {"context": name, "integration_id": GITHUB_ACTIONS_APP_ID}
                            for name in MAIN_REQUIRED_CHECKS
                        ],
                    },
                },
            ],
            "bypass_actors": [],
            "current_user_can_bypass": "never",
        }
        integrity = {
            **envelope,
            "id": 2,
            "name": INTEGRITY_RULESET,
            "target": "tag",
            "conditions": {
                "ref_name": {"exclude": [], "include": ["refs/tags/v*"]}
            },
            "rules": [
                {"type": "required_signatures"},
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": False,
                        "do_not_enforce_on_create": False,
                        "required_status_checks": [
                            {
                                "context": SIGNED_MAIN_CHECK,
                                "integration_id": GITHUB_ACTIONS_APP_ID,
                            }
                        ],
                    },
                },
                {"type": "deletion"},
                {"type": "non_fast_forward"},
            ],
            "bypass_actors": [],
            "current_user_can_bypass": "never",
        }
        creation = {
            **envelope,
            "id": 3,
            "name": CREATION_RULESET,
            "target": "tag",
            "conditions": {
                "ref_name": {"exclude": [], "include": ["refs/tags/v*"]}
            },
            "rules": [{"type": "creation"}],
            "bypass_actors": [
                {
                    "actor_id": APP_ID,
                    "actor_type": "Integration",
                    "bypass_mode": "always",
                }
            ],
            "current_user_can_bypass": "always",
        }
        return {MAIN_RULESET: main, INTEGRITY_RULESET: integrity, CREATION_RULESET: creation}

    def request(self) -> ReleaseTagRequest:
        return ReleaseTagRequest(
            repository=REPOSITORY,
            version=self.version,
            tag=f"v{self.version}",
            expected_main_sha=self.main_sha,
            expected_app_id=APP_ID,
        )

    def manifest_content(self, _path: str) -> bytes:
        return (json.dumps({"version": self.version}) + "\n").encode("utf-8")

    def read_tag(self, tag: str) -> dict[str, Any] | None:
        del tag
        return copy.deepcopy(self.tag_ref)

    def create_tag(self, tag: str, sha: str) -> dict[str, Any]:
        self.mutation_attempts += 1
        if self.tag_ref is not None:
            raise ControllerError("fixture tag already exists")
        self.tag_ref = {
            "ref": f"refs/tags/{tag}",
            "object": {"type": "commit", "sha": sha},
        }
        return copy.deepcopy(self.tag_ref)


class FixtureApi:
    def __init__(self, repository: FixtureRepository) -> None:
        self.repository = repository

    def get(self, path: str, *, allow_not_found: bool = False) -> Any:
        repo = self.repository
        if path == f"/repos/{REPOSITORY}":
            repo.snapshot_reads += 1
            if repo.snapshot_reads == 2 and repo.before_second_snapshot is not None:
                repo.before_second_snapshot(repo)
            return {"full_name": REPOSITORY, "default_branch": "main"}
        if path == "/installation":
            return {"id": 77, "app_id": APP_ID}
        if path == "/installation/repositories?per_page=100":
            return {
                "total_count": len(repo.installation_repositories),
                "repositories": [
                    {"full_name": name} for name in repo.installation_repositories
                ],
            }
        if path == f"/repos/{REPOSITORY}/git/ref/heads/main":
            return {
                "ref": "refs/heads/main",
                "object": {"type": "commit", "sha": repo.main_sha},
            }
        if path == f"/repos/{REPOSITORY}/git/commits/{repo.main_sha}":
            return {"sha": repo.main_sha, "tree": {"sha": repo.tree_sha}}
        if path.startswith(f"/repos/{REPOSITORY}/contents/"):
            manifest_path = path.split("/contents/", 1)[1].split("?", 1)[0]
            return {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(repo.manifest_content(manifest_path)).decode(),
            }
        if path == f"/repos/{REPOSITORY}/commits/{repo.main_sha}":
            return {
                "sha": repo.main_sha,
                "commit": {"verification": {"verified": True, "reason": "valid"}},
            }
        if path.startswith(f"/repos/{REPOSITORY}/commits/{repo.main_sha}/check-runs?"):
            return {"total_count": len(repo.check_runs), "check_runs": copy.deepcopy(repo.check_runs)}
        if path.startswith(f"/repos/{REPOSITORY}/git/ref/tags/"):
            tag = path.rsplit("/", 1)[1]
            result = repo.read_tag(tag)
            if result is None and not allow_not_found:
                raise ControllerError("fixture tag not found")
            return result
        if path.startswith(f"/repos/{REPOSITORY}/releases/tags/"):
            if repo.release is None and not allow_not_found:
                raise ControllerError("fixture release not found")
            return copy.deepcopy(repo.release)
        if path == f"/repos/{REPOSITORY}/rulesets?includes_parents=true&per_page=100":
            return [
                {"id": ruleset["id"], "name": name}
                for name, ruleset in repo.rulesets.items()
            ]
        for ruleset in repo.rulesets.values():
            if path == (
                f"/repos/{REPOSITORY}/rulesets/{ruleset['id']}?includes_parents=true"
            ):
                return copy.deepcopy(ruleset)
        raise AssertionError(f"unexpected fixture GET {path}")

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        repo = self.repository
        if path == "/graphql":
            return {
                "data": {
                    "repository": {
                        "object": {"oid": repo.main_sha, "signature": copy.deepcopy(repo.signature)}
                    }
                }
            }
        if path == f"/repos/{REPOSITORY}/git/refs":
            created = repo.create_tag(
                payload["ref"].removeprefix("refs/tags/"), payload["sha"]
            )
            if repo.raise_after_creation:
                raise GitHubRequestError("fixture connection ended after mutation")
            return created
        raise AssertionError(f"unexpected fixture POST {path}")


class BareFixtureRepository(FixtureRepository):
    def __init__(self, root: Path) -> None:
        self.worktree = root / "worktree"
        self.bare = root / "remote.git"
        subprocess.run(["git", "init", "-q", str(self.worktree)], check=True)
        subprocess.run(["git", "config", "user.name", "Axiom Test"], cwd=self.worktree, check=True)
        subprocess.run(
            ["git", "config", "user.email", "axiom-test@example.invalid"],
            cwd=self.worktree,
            check=True,
        )
        for relative in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
            path = self.worktree / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"version": RELEASE_VERSION}) + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.worktree, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.worktree, check=True)
        main_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.worktree, text=True, capture_output=True, check=True
        ).stdout.strip()
        tree_sha = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=self.worktree,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        subprocess.run(["git", "branch", "-M", "main"], cwd=self.worktree, check=True)
        subprocess.run(["git", "clone", "-q", "--bare", str(self.worktree), str(self.bare)], check=True)
        super().__init__(main_sha=main_sha, tree_sha=tree_sha)

    def manifest_content(self, path: str) -> bytes:
        return subprocess.run(
            ["git", f"--git-dir={self.bare}", "show", f"{self.main_sha}:{path}"],
            capture_output=True,
            check=True,
        ).stdout

    def read_tag(self, tag: str) -> dict[str, Any] | None:
        result = subprocess.run(
            ["git", f"--git-dir={self.bare}", "rev-parse", "--verify", f"refs/tags/{tag}"],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return {
            "ref": f"refs/tags/{tag}",
            "object": {"type": "commit", "sha": result.stdout.strip()},
        }

    def create_tag(self, tag: str, sha: str) -> dict[str, Any]:
        self.mutation_attempts += 1
        result = subprocess.run(
            [
                "git",
                f"--git-dir={self.bare}",
                "update-ref",
                f"refs/tags/{tag}",
                sha,
                "0" * 40,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ControllerError(f"disposable Git repository rejected tag creation: {result.stderr}")
        ref = self.read_tag(tag)
        if ref is None:
            raise ControllerError("disposable Git repository lost the created tag")
        return ref


class ReleaseTagControllerTests(unittest.TestCase):
    def test_correct_current_main_creates_once_and_rerun_is_read_only(self):
        fixture = FixtureRepository()
        api = FixtureApi(fixture)
        result = run_controller(api, api, fixture.request())
        self.assertEqual("created-and-verified", result["outcome"])
        self.assertEqual(1, result["mutationAttempts"])
        self.assertEqual(1, fixture.mutation_attempts)

        with self.assertRaisesRegex(ControllerError, "already exists; no mutation attempted"):
            run_controller(api, api, fixture.request())
        self.assertEqual(1, fixture.mutation_attempts)

    def test_wrong_requested_tag_is_rejected_before_api_access(self):
        fixture = FixtureRepository()
        request = fixture.request()
        mismatched = ReleaseTagRequest(
            repository=request.repository,
            version=request.version,
            tag=f"v{request.version}.1",
            expected_main_sha=request.expected_main_sha,
            expected_app_id=request.expected_app_id,
        )
        with self.assertRaisesRegex(ControllerError, "must exactly equal"):
            validate_request(mismatched)
        self.assertEqual(0, fixture.snapshot_reads)
        self.assertEqual(0, fixture.mutation_attempts)

    def test_non_main_candidate_is_rejected(self):
        fixture = FixtureRepository()
        request = fixture.request()
        descendant = ReleaseTagRequest(
            repository=request.repository,
            version=request.version,
            tag=request.tag,
            expected_main_sha="3" * 40,
            expected_app_id=request.expected_app_id,
        )
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "live main does not equal"):
            run_controller(api, api, descendant)
        self.assertEqual(0, fixture.mutation_attempts)

    def test_candidate_context_cannot_replace_signed_main_context(self):
        fixture = FixtureRepository()
        for run in fixture.check_runs:
            if run["name"] == SIGNED_MAIN_CHECK:
                run["name"] = "Verify release candidate"
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "Verify signed main history"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_required_check_for_another_sha_is_rejected(self):
        fixture = FixtureRepository()
        fixture.check_runs[0]["head_sha"] = "4" * 40
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "exact main"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_invalid_github_signature_is_rejected(self):
        fixture = FixtureRepository()
        fixture.signature = {
            "isValid": False,
            "state": "INVALID",
            "wasSignedByGitHub": False,
        }
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "signed with GitHub's signing key"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_app_token_with_another_repository_is_rejected(self):
        fixture = FixtureRepository()
        fixture.installation_repositories = [REPOSITORY, "wheakerd/another"]
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "scoped to exactly this repository"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_main_drift_between_reads_is_rejected(self):
        fixture = FixtureRepository()
        fixture.before_second_snapshot = lambda repository: setattr(repository, "main_sha", "5" * 40)
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "live main does not equal"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_preexisting_release_is_rejected(self):
        fixture = FixtureRepository()
        fixture.release = {"id": 99, "tag_name": f"v{RELEASE_VERSION}"}
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "GitHub Release .* already exists"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_manifest_version_mismatch_is_rejected(self):
        fixture = FixtureRepository()
        fixture.version = "9.9.9"
        request = ReleaseTagRequest(
            repository=REPOSITORY,
            version=RELEASE_VERSION,
            tag=f"v{RELEASE_VERSION}",
            expected_main_sha=fixture.main_sha,
            expected_app_id=APP_ID,
        )
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "manifests must equal"):
            run_controller(api, api, request)
        self.assertEqual(0, fixture.mutation_attempts)

    def test_uncertain_creation_reads_back_once_and_rerun_does_not_mutate(self):
        fixture = FixtureRepository()
        fixture.raise_after_creation = True
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "controller will not retry"):
            run_controller(api, api, fixture.request())
        self.assertEqual(1, fixture.mutation_attempts)
        fixture.raise_after_creation = False
        with self.assertRaisesRegex(ControllerError, "already exists; no mutation attempted"):
            run_controller(api, api, fixture.request())
        self.assertEqual(1, fixture.mutation_attempts)

    def test_creation_app_cannot_bypass_integrity_rules(self):
        fixture = FixtureRepository()
        fixture.rulesets[INTEGRITY_RULESET]["bypass_actors"] = [
            {
                "actor_id": APP_ID,
                "actor_type": "Integration",
                "bypass_mode": "always",
            }
        ]
        fixture.rulesets[INTEGRITY_RULESET]["current_user_can_bypass"] = "always"
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "must retain no bypass actor"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_owner_user_bypass_is_rejected(self):
        fixture = FixtureRepository()
        fixture.rulesets[CREATION_RULESET]["bypass_actors"] = [
            {"actor_id": 78034820, "actor_type": "User", "bypass_mode": "always"}
        ]
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "dedicated release GitHub App"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_old_shared_integrity_context_is_rejected(self):
        fixture = FixtureRepository()
        rules = fixture.rulesets[INTEGRITY_RULESET]["rules"]
        checks = next(rule for rule in rules if rule["type"] == "required_status_checks")
        checks["parameters"]["required_status_checks"][0]["context"] = (
            "Verify GitHub-signed release target"
        )
        api = FixtureApi(fixture)
        with self.assertRaisesRegex(ControllerError, "Verify signed main history"):
            run_controller(api, api, fixture.request())
        self.assertEqual(0, fixture.mutation_attempts)

    def test_disposable_bare_repository_integration(self):
        with tempfile.TemporaryDirectory(prefix="axiom-release-tag-") as temporary:
            fixture = BareFixtureRepository(Path(temporary))
            api = FixtureApi(fixture)
            result = run_controller(api, api, fixture.request())
            self.assertEqual("created-and-verified", result["outcome"])
            self.assertEqual(1, fixture.mutation_attempts)
            self.assertEqual(fixture.main_sha, fixture.read_tag(f"v{RELEASE_VERSION}")["object"]["sha"])

            with self.assertRaisesRegex(ControllerError, "already exists; no mutation attempted"):
                run_controller(api, api, fixture.request())
            self.assertEqual(1, fixture.mutation_attempts)


if __name__ == "__main__":
    unittest.main()
