"""Offline tests for the deterministic CI release pipeline."""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from typing import Any

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.manifests import catalog_source
from axiom_validation.release_pipeline import (
    CATALOG_REQUIRED_CHECKS,
    CREATED_TAG_CHECK,
    EXPECTED_WORKFLOW,
    PIPELINE_JOB_NAMES,
    PUBLISHED_RELEASE_CHECK,
    REHEARSAL_COMMANDS,
    REQUIRED_MAIN_CHECKS,
    WORKFLOW_PATH,
    Clock,
    PipelineError,
    Reporter,
    apply_catalog_handoff,
    check_release_pipeline_workflow_contract,
    check_release_pipeline_workflow_text,
    immediate_successors,
    rehearse_catalog_handoff,
    run_candidate,
    run_catalog,
    run_publish,
    wait_for_settled_checks,
)
from axiom_validation.release_evidence import MARKETPLACE_CATALOGS
from axiom_validation.release_tag_controller import GITHUB_ACTIONS_APP_ID


REPOSITORY = "wheakerd/axiom"
HANDOFF_FILES = (
    "CHANGELOG.md",
    "docs/runtime-identity.md",
    "evidence/release-status.json",
    "evidence/repository-policy-revisions-v1.json",
    "evidence/runtime-identity.json",
    ".agents/plugins/marketplace.json",
    ".claude-plugin/marketplace.json",
)


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Axiom Test",
            "-c",
            "user.email=axiom-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *arguments,
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def commit_versions(root: Path, versions: tuple[str, ...]) -> list[str]:
    git(root, "init", "-q", "-b", "main")
    manifest = root / "plugin" / ".codex-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    commits = []
    for version in versions:
        manifest.write_text(json.dumps({"name": "axiom", "version": version}) + "\n")
        git(root, "add", "-A")
        git(root, "commit", "-q", "--allow-empty", "-m", f"version {version}")
        commits.append(git(root, "rev-parse", "HEAD").strip())
    return commits


class FakeClock(Clock):
    def __init__(self) -> None:
        self.current = 0.0
        super().__init__(now=lambda: self.current, sleep=self._sleep)

    def _sleep(self, seconds: float) -> None:
        self.current += seconds


def check_run(identifier: int, name: str, commit: str, status: str, conclusion: str | None) -> dict:
    return {
        "id": identifier,
        "name": name,
        "head_sha": commit,
        "status": status,
        "conclusion": conclusion,
        "app": {"id": GITHUB_ACTIONS_APP_ID, "slug": "github-actions"},
    }


def final_release(identifier: int, tag: str, commit: str) -> dict:
    return {
        "id": identifier,
        "tag_name": tag,
        "target_commitish": commit,
        "name": f"Axiom {tag}",
        "draft": False,
        "prerelease": False,
        "immutable": True,
        "assets": [],
        "html_url": f"https://github.com/{REPOSITORY}/releases/tag/{tag}",
        "published_at": "2026-11-02T10:00:00Z",
    }


class FakeGitHub:
    """In-memory repository state for the publication stage."""

    def __init__(self, commit: str, *, previous_commit: str = "9" * 40) -> None:
        self.main = commit
        self.tags: dict[str, str] = {"v0.20.0": previous_commit}
        self.releases: list[dict[str, Any]] = [final_release(1, "v0.20.0", previous_commit)]
        self.latest_id = 1
        self.checks: dict[str, list[dict[str, Any]]] = {}
        self.pending_check_reads = 1
        self.runs: dict[int, dict[str, Any]] = {}
        self.next_id = 100
        self.mutations: list[tuple[str, str]] = []
        self.extra_dispatch_runs = 0
        self.failing_checks: set[str] = set()
        self.catalog_tag = "v0.20.0"
        # Another workflow on the same commit, such as code scanning, that finishes a
        # few check reads after the required checks do.
        self.sibling_checks: dict[str, str] = {"Analyze (python)": "success"}
        self.sibling_pending_reads = 3

    def _path(self, path: str) -> tuple[str, dict[str, str]]:
        parsed = urllib.parse.urlsplit(path)
        return parsed.path.removeprefix(f"/repos/{REPOSITORY}"), dict(urllib.parse.parse_qsl(parsed.query))

    def _release(self, identifier: int) -> dict[str, Any]:
        return next(release for release in self.releases if release["id"] == identifier)

    def main_checks_for(self, commit: str) -> list[dict[str, Any]]:
        if self.pending_check_reads > 0:
            self.pending_check_reads -= 1
            status, conclusion = "in_progress", None
        else:
            status, conclusion = "completed", "success"
        runs = [
            check_run(
                10 + index,
                name,
                commit,
                status,
                "failure" if name in self.failing_checks and status == "completed" else conclusion,
            )
            for index, name in enumerate(REQUIRED_MAIN_CHECKS)
        ]
        # The pipeline's own job never completes while it waits.
        runs.append(check_run(40, "Publish release", commit, "in_progress", None))
        settled = self.sibling_pending_reads == 0
        if not settled:
            self.sibling_pending_reads -= 1
        runs.extend(
            check_run(
                80 + index,
                name,
                commit,
                "completed" if settled else "in_progress",
                sibling_conclusion if settled else None,
            )
            for index, (name, sibling_conclusion) in enumerate(self.sibling_checks.items())
        )
        return runs

    def get(self, path: str, *, allow_not_found: bool = False) -> Any:
        route, query = self._path(path)
        if route == "/releases":
            return [release for release in self.releases] if query.get("page") == "1" else []
        if route.startswith("/git/ref/tags/"):
            tag = urllib.parse.unquote(route.removeprefix("/git/ref/tags/"))
            if tag not in self.tags:
                if allow_not_found:
                    return None
                raise PipelineError("HTTP 404")
            return {"ref": f"refs/tags/{tag}", "object": {"type": "commit", "sha": self.tags[tag]}}
        if route == "/git/ref/heads/main":
            return {"ref": "refs/heads/main", "object": {"type": "commit", "sha": self.main}}
        if route == "/releases/latest":
            return self._release(self.latest_id)
        if route.startswith("/releases/"):
            return self._release(int(route.removeprefix("/releases/")))
        if route.startswith("/commits/") and route.endswith("/check-runs"):
            commit = route.split("/")[2]
            runs = list(self.checks.get(commit, []))
            if commit == self.main and not any(run["name"] in REQUIRED_MAIN_CHECKS for run in runs):
                runs = self.main_checks_for(commit) + runs
            return {"total_count": len(runs), "check_runs": runs}
        if route.startswith("/compare/"):
            base = route.removeprefix("/compare/").split("...")[0]
            return {"status": "identical", "merge_base_commit": {"sha": base}}
        if route.startswith("/actions/workflows/") and route.endswith("/runs"):
            workflow = route.split("/")[3]
            runs = [
                run
                for run in self.runs.values()
                if run["workflow"] == workflow and run["head_sha"] == query["head_sha"]
            ]
            return {"workflow_runs": runs}
        if route.startswith("/actions/runs/"):
            run = self.runs[int(route.removeprefix("/actions/runs/"))]
            if run["status"] != "completed":
                run.update(status="completed", conclusion="success")
                self._complete(run)
            return run
        if route.startswith("/contents/"):
            source = catalog_source(self.catalog_tag, "codex" if ".agents" in route else "claude-code")
            document = {"plugins": [{"name": "axiom", "source": source}]}
            return {
                "encoding": "base64",
                "content": base64.b64encode(json.dumps(document).encode()).decode(),
            }
        raise AssertionError(f"unexpected GET {path}")

    def _complete(self, run: dict[str, Any]) -> None:
        workflow, inputs = run["workflow"], run["inputs"]
        if workflow == "create-protected-release-tag.yml":
            self.tags[inputs["tag"]] = self.main
            self.checks.setdefault(self.main, []).append(
                check_run(50, CREATED_TAG_CHECK, self.main, "completed", "success")
            )
        elif workflow == "publish-immutable-release.yml":
            release = next(item for item in self.releases if item["tag_name"] == inputs["tag"])
            release.update(draft=False, immutable=True)
            self.latest_id = release["id"]
        elif workflow == "release-signature-guard.yml":
            commit = run["head_sha"]
            self.checks.setdefault(commit, []).append(
                check_run(60, PUBLISHED_RELEASE_CHECK, commit, "completed", "success")
            )

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        route, _ = self._path(path)
        self.mutations.append(("POST", route))
        if route.endswith("/dispatches"):
            workflow = route.split("/")[3]
            head = self.main if payload["ref"] == "main" else self.tags[payload["ref"]]
            for _ in range(1 + self.extra_dispatch_runs):
                self.next_id += 1
                self.runs[self.next_id] = {
                    "id": self.next_id,
                    "workflow": workflow,
                    "head_sha": head,
                    "inputs": payload["inputs"],
                    "status": "queued",
                    "conclusion": None,
                }
            return None
        if route == "/releases":
            self.next_id += 1
            release = {
                "id": self.next_id,
                "tag_name": payload["tag_name"],
                "target_commitish": payload["target_commitish"],
                "name": payload["name"],
                "body": payload["body"],
                "draft": True,
                "prerelease": False,
                "immutable": False,
                "assets": [],
            }
            self.releases.append(release)
            return dict(release)
        raise AssertionError(f"unexpected POST {path}")

    def upload(self, url: str, data: bytes, content_type: str) -> Any:
        parsed = urllib.parse.urlsplit(url)
        identifier = int(parsed.path.split("/")[5])
        name = dict(urllib.parse.parse_qsl(parsed.query))["name"]
        self.mutations.append(("UPLOAD", name))
        asset = {"id": 900, "name": name, "size": len(data), "content_type": content_type}
        self._release(identifier)["assets"].append(asset)
        return asset

    def put(self, path: str, payload: dict[str, Any]) -> Any:
        raise AssertionError(f"unexpected PUT {path}")

    def delete(self, path: str) -> Any:
        raise AssertionError(f"unexpected DELETE {path}")

    def graphql(self, query: str, variables: dict[str, Any]) -> Any:
        raise AssertionError("unexpected GraphQL request")


def render_inputs(root: Path, commit: str, version: str, tag: str) -> tuple[str, bytes, str]:
    return "rendered body\n", b'{"policy":true}', f"axiom-v{version}-release-policy-{'a' * 64}.json"


def no_rehearsal(root: Path, commit: str, version: str, tag: str, *, today: str) -> None:
    raise AssertionError(f"no catalog handoff rehearsal was expected for {tag}")


class SettledChecksApi:
    """Serve successive check-run pages; the last page repeats."""

    def __init__(self, *pages: list[dict[str, Any]]) -> None:
        self.pages = list(pages)
        self.reads = 0

    def get(self, path: str, *, allow_not_found: bool = False) -> Any:
        assert path.endswith("/check-runs?filter=latest&per_page=100&page=1"), path
        runs = self.pages.pop(0) if len(self.pages) > 1 else self.pages[0]
        self.reads += 1
        return {"total_count": len(runs), "check_runs": runs}


class ReleasePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "repository"
        self.root.mkdir()
        self.reports = Path(self.directory.name)
        self.reporter = Reporter(self.reports / "summary.md", self.reports / "output.txt")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def outputs(self) -> dict[str, str]:
        lines = (self.reports / "output.txt").read_text().splitlines()
        return dict(line.split("=", 1) for line in lines)

    def test_checked_in_workflow_contract(self):
        failures: list[str] = []
        self.assertIsNotNone(check_release_pipeline_workflow_contract(failures))
        self.assertEqual([], failures)

    def test_pipeline_job_names_match_the_workflow_contract(self):
        self.assertEqual(
            tuple(job["name"] for job in EXPECTED_WORKFLOW["jobs"].values()),
            PIPELINE_JOB_NAMES,
        )

    def test_rehearsal_commands_are_the_contributor_checks(self):
        self.assertEqual(
            (
                ("scripts/check-publication.py",),
                ("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"),
            ),
            REHEARSAL_COMMANDS,
        )

    def test_settled_wait_covers_sibling_checks_but_not_the_pipeline_jobs(self):
        commit = "f" * 40
        own_job = check_run(1, "Publish release", commit, "in_progress", None)
        sibling_running = check_run(2, "Analyze (python)", commit, "in_progress", None)
        sibling_done = check_run(2, "Analyze (python)", commit, "completed", "success")
        skipped = check_run(3, "Release candidate", commit, "completed", "skipped")
        foreign = {**check_run(4, "Other app", commit, "in_progress", None), "app": {"id": 999}}
        api = SettledChecksApi([own_job, sibling_running, skipped, foreign], [own_job, sibling_done, skipped, foreign])
        clock = FakeClock()
        evidence = wait_for_settled_checks(api, REPOSITORY, commit, clock, "main checks")
        self.assertEqual({"Analyze (python)": 2}, evidence)
        self.assertEqual(2, api.reads)
        self.assertGreater(clock.current, 0)

        failed = check_run(2, "Analyze (python)", commit, "completed", "failure")
        with self.assertRaisesRegex(PipelineError, r"'Analyze \(python\)' concluded 'failure'"):
            wait_for_settled_checks(SettledChecksApi([own_job, failed]), REPOSITORY, commit, FakeClock(), "main checks")

        with self.assertRaisesRegex(PipelineError, r"timed out waiting for Analyze \(python\)"):
            wait_for_settled_checks(
                SettledChecksApi([own_job, sibling_running]), REPOSITORY, commit, FakeClock(), "main checks", timeout=30
            )

    def test_workflow_mutations_are_rejected(self):
        original = WORKFLOW_PATH.read_text(encoding="utf-8")
        candidate_step = "      - name: Check the version step and preview the Release body\n"
        mutations = {
            "unreviewed action": original.replace(
                candidate_step,
                "      - name: Summarize the change\n"
                "        uses: example/ai-review-action@" + "b" * 40 + " # v1\n\n"
                + candidate_step,
            ),
            "unfiltered pull requests": original.replace(
                "    paths:\n      - plugin/.codex-plugin/plugin.json\n  push:",
                "  push:",
            ),
            "secret in candidate job": original.replace(
                "          GITHUB_TOKEN: ${{ github.token }}\n          HEAD_SHA",
                "          GITHUB_TOKEN: ${{ secrets.EXTRA_TOKEN }}\n          HEAD_SHA",
            ),
            "base context trigger": original.replace("  pull_request:\n", "  pull_request_target:\n"),
            "wider publish permission": original.replace(
                "      checks: read\n      contents: write\n",
                "      checks: write\n      contents: write\n",
            ),
            "candidate without Node.js for the rehearsal": original.replace(
                "      - name: Set up Node.js\n"
                "        uses: actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38 # v6\n"
                "        with:\n"
                '          node-version: "24.19.0"\n'
                "          package-manager-cache: false\n\n",
                "",
                1,
            ),
        }
        for label, text in mutations.items():
            with self.subTest(label=label):
                self.assertNotEqual(original, text)
                failures: list[str] = []
                check_release_pipeline_workflow_text(text, failures)
                self.assertTrue(failures)

    def test_immediate_successors(self):
        self.assertEqual(("0.20.1", "0.21.0", "1.0.0"), immediate_successors("0.20.0"))
        self.assertEqual(("1.9.10", "1.10.0", "2.0.0"), immediate_successors("1.9.9"))

    def test_candidate_without_version_change_publishes_nothing(self):
        base, head = commit_versions(self.root, ("0.20.0", "0.20.0"))
        api = FakeGitHub(head)
        outcome = run_candidate(
            root=self.root,
            api=api,
            repository=REPOSITORY,
            base_commit=base,
            head_commit=head,
            reporter=self.reporter,
            render_body=lambda *_: self.fail("no body for a non-release"),
            rehearse=no_rehearsal,
        )
        self.assertEqual("not-a-release", outcome)
        self.assertIn("Not a release candidate", (self.reports / "summary.md").read_text())

    def test_candidate_previews_the_next_version_and_rehearses_its_handoff(self):
        base, head = commit_versions(self.root, ("0.20.0", "0.21.0"))
        rehearsals: list[tuple[Path, str, str, str, str]] = []

        def rehearse(root: Path, commit: str, version: str, tag: str, *, today: str) -> None:
            rehearsals.append((root, commit, version, tag, today))

        outcome = run_candidate(
            root=self.root,
            api=FakeGitHub(head),
            repository=REPOSITORY,
            base_commit=base,
            head_commit=head,
            reporter=self.reporter,
            render_body=lambda root, commit, version: f"notes for {version} at {commit}\n",
            rehearse=rehearse,
            today="2026-11-02",
        )
        self.assertEqual("release-candidate", outcome)
        self.assertEqual([(self.root, head, "0.21.0", "v0.21.0", "2026-11-02")], rehearsals)
        summary = (self.reports / "summary.md").read_text()
        self.assertIn("## Release candidate v0.21.0", summary)
        self.assertIn("| Catalog handoff rehearsal | passed on this head |", summary)
        self.assertIn(f"notes for 0.21.0 at {head}", summary)

    def test_candidate_stops_when_its_handoff_rehearsal_fails(self):
        base, head = commit_versions(self.root, ("0.20.0", "0.21.0"))

        def rehearse(root: Path, commit: str, version: str, tag: str, *, today: str) -> None:
            raise PipelineError(f"the rehearsed catalog handoff for {tag} fails `python -B x`")

        with self.assertRaisesRegex(PipelineError, "rehearsed catalog handoff for v0.21.0"):
            run_candidate(
                root=self.root,
                api=FakeGitHub(head),
                repository=REPOSITORY,
                base_commit=base,
                head_commit=head,
                reporter=self.reporter,
                render_body=lambda root, commit, version: "notes\n",
                rehearse=rehearse,
            )
        self.assertFalse((self.reports / "summary.md").exists())

    def test_candidate_rejects_skipped_or_stacked_versions(self):
        base, head = commit_versions(self.root, ("0.20.0", "0.22.0"))
        with self.assertRaisesRegex(PipelineError, "not the next patch, minor, or major"):
            run_candidate(
                root=self.root,
                api=FakeGitHub(head),
                repository=REPOSITORY,
                base_commit=base,
                head_commit=head,
                reporter=self.reporter,
                rehearse=no_rehearsal,
            )
        stacked_root = Path(self.directory.name) / "stacked"
        stacked_root.mkdir()
        base, head = commit_versions(stacked_root, ("0.21.0", "0.21.1"))
        with self.assertRaisesRegex(PipelineError, "v0.21.0 must be a published immutable Release"):
            run_candidate(
                root=stacked_root,
                api=FakeGitHub(head),
                repository=REPOSITORY,
                base_commit=base,
                head_commit=head,
                reporter=self.reporter,
                rehearse=no_rehearsal,
            )

    def test_publish_runs_every_stage_once_in_order(self):
        (commit,) = commit_versions(self.root, ("0.21.0",))
        api = FakeGitHub(commit)

        def rehearse(root: Path, rehearsed_commit: str, version: str, tag: str, *, today: str) -> None:
            # The rehearsal runs after every sibling check settled and before any mutation.
            self.assertEqual(0, api.sibling_pending_reads)
            self.assertEqual((self.root, commit, "0.21.0"), (root, rehearsed_commit, version))
            api.mutations.append(("REHEARSE", tag))

        outputs = run_publish(
            root=self.root,
            api=api,
            repository=REPOSITORY,
            commit=commit,
            reporter=self.reporter,
            clock=FakeClock(),
            render_inputs=render_inputs,
            rehearse=rehearse,
        )
        dispatched = [run["workflow"] for run in sorted(api.runs.values(), key=lambda run: run["id"])]
        self.assertEqual(
            [
                "create-protected-release-tag.yml",
                "publish-immutable-release.yml",
                "release-signature-guard.yml",
            ],
            dispatched,
        )
        self.assertEqual(
            [
                ("REHEARSE", "v0.21.0"),
                ("POST", "/actions/workflows/create-protected-release-tag.yml/dispatches"),
                ("POST", "/releases"),
                ("UPLOAD", f"axiom-v0.21.0-release-policy-{'a' * 64}.json"),
                ("POST", "/actions/workflows/publish-immutable-release.yml/dispatches"),
                ("POST", "/actions/workflows/release-signature-guard.yml/dispatches"),
            ],
            api.mutations,
        )
        self.assertEqual(commit, api.tags["v0.21.0"])
        self.assertEqual("pending", outputs["catalog"])
        self.assertEqual(
            {"version": "0.21.0", "tag": "v0.21.0", "commit": commit, "catalog": "pending"},
            {key: value for key, value in self.outputs().items() if key != "release-id"},
        )
        self.assertIn(
            "| Catalog handoff rehearsal | passed before the first mutation |",
            (self.reports / "summary.md").read_text(),
        )

    def test_publish_rehearses_before_the_publisher_when_the_tag_already_exists(self):
        (commit,) = commit_versions(self.root, ("0.21.0",))
        api = FakeGitHub(commit)
        api.tags["v0.21.0"] = commit
        api.checks[commit] = [check_run(50, CREATED_TAG_CHECK, commit, "completed", "success")]
        api.sibling_pending_reads = 0
        run_publish(
            root=self.root,
            api=api,
            repository=REPOSITORY,
            commit=commit,
            reporter=self.reporter,
            clock=FakeClock(),
            render_inputs=render_inputs,
            rehearse=lambda root, rehearsed, version, tag, *, today: api.mutations.append(("REHEARSE", tag)),
        )
        self.assertEqual(
            [
                ("REHEARSE", "v0.21.0"),
                ("POST", "/releases"),
                ("UPLOAD", f"axiom-v0.21.0-release-policy-{'a' * 64}.json"),
                ("POST", "/actions/workflows/publish-immutable-release.yml/dispatches"),
                ("POST", "/actions/workflows/release-signature-guard.yml/dispatches"),
            ],
            api.mutations,
        )

    def test_publish_stops_when_the_rehearsed_handoff_fails(self):
        (commit,) = commit_versions(self.root, ("0.21.0",))
        api = FakeGitHub(commit)

        def rehearse(root: Path, rehearsed: str, version: str, tag: str, *, today: str) -> None:
            raise PipelineError(f"the rehearsed catalog handoff for {tag} fails `python -B x`")

        with self.assertRaisesRegex(PipelineError, "rehearsed catalog handoff for v0.21.0"):
            run_publish(
                root=self.root,
                api=api,
                repository=REPOSITORY,
                commit=commit,
                reporter=self.reporter,
                clock=FakeClock(),
                render_inputs=render_inputs,
                rehearse=rehearse,
            )
        self.assertEqual([], api.mutations)
        self.assertNotIn("v0.21.0", api.tags)

    def test_publish_stops_on_a_failed_sibling_check(self):
        (commit,) = commit_versions(self.root, ("0.21.0",))
        api = FakeGitHub(commit)
        api.sibling_checks = {"Analyze (python)": "failure"}
        with self.assertRaisesRegex(PipelineError, r"'Analyze \(python\)' concluded 'failure'"):
            run_publish(
                root=self.root,
                api=api,
                repository=REPOSITORY,
                commit=commit,
                reporter=self.reporter,
                clock=FakeClock(),
                render_inputs=render_inputs,
                rehearse=no_rehearsal,
            )
        self.assertEqual([], api.mutations)

    def test_publish_resumes_without_mutation_when_complete(self):
        (commit,) = commit_versions(self.root, ("0.21.0",))
        api = FakeGitHub(commit)
        api.tags["v0.21.0"] = commit
        api.releases.append(final_release(5, "v0.21.0", commit))
        api.latest_id = 5
        api.catalog_tag = "v0.21.0"
        api.checks[commit] = [check_run(60, PUBLISHED_RELEASE_CHECK, commit, "completed", "success")]
        outputs = run_publish(
            root=self.root,
            api=api,
            repository=REPOSITORY,
            commit=commit,
            reporter=self.reporter,
            clock=FakeClock(),
            render_inputs=render_inputs,
            rehearse=no_rehearsal,
        )
        self.assertEqual([], api.mutations)
        self.assertEqual("current", outputs["catalog"])
        self.assertIn(
            "| Catalog handoff rehearsal | not needed: the Release was already final |",
            (self.reports / "summary.md").read_text(),
        )

    def test_publish_stops_before_mutation_when_main_moved(self):
        (commit,) = commit_versions(self.root, ("0.21.0",))
        api = FakeGitHub(commit)
        api.main = "8" * 40
        with self.assertRaisesRegex(PipelineError, "main moved"):
            run_publish(
                root=self.root,
                api=api,
                repository=REPOSITORY,
                commit=commit,
                reporter=self.reporter,
                clock=FakeClock(),
                render_inputs=render_inputs,
                rehearse=no_rehearsal,
            )
        self.assertEqual([], api.mutations)

    def test_publish_stops_on_a_failed_required_check(self):
        (commit,) = commit_versions(self.root, ("0.21.0",))
        api = FakeGitHub(commit)
        api.failing_checks = {"hook-runtime-gate"}
        with self.assertRaisesRegex(PipelineError, "hook-runtime-gate"):
            run_publish(
                root=self.root,
                api=api,
                repository=REPOSITORY,
                commit=commit,
                reporter=self.reporter,
                clock=FakeClock(),
                render_inputs=render_inputs,
                rehearse=no_rehearsal,
            )
        self.assertEqual([], api.mutations)

    def test_publish_refuses_to_guess_between_dispatched_runs(self):
        (commit,) = commit_versions(self.root, ("0.21.0",))
        api = FakeGitHub(commit)
        api.extra_dispatch_runs = 1
        with self.assertRaisesRegex(PipelineError, "more than one new"):
            run_publish(
                root=self.root,
                api=api,
                repository=REPOSITORY,
                commit=commit,
                reporter=self.reporter,
                clock=FakeClock(),
                render_inputs=render_inputs,
                rehearse=lambda *arguments, **options: None,
            )
        self.assertNotIn("v0.21.0", api.tags)


def prepare_handoff_repository(root: Path, version: str, previous_tag: str = "v0.20.0") -> str:
    """Copy the checked-in handoff files and declare an unreleased next version."""
    for relative in HANDOFF_FILES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / relative, target)
    identity_path = root / "evidence" / "runtime-identity.json"
    identity = json.loads(identity_path.read_text())
    identity["pluginVersion"] = version
    identity_path.write_text(json.dumps(identity, indent=2) + "\n")
    # Select an earlier release, so the handoff has catalogs to advance whatever release
    # the checked-in catalogs already select.
    for host, relative in MARKETPLACE_CATALOGS:
        catalog_path = root / relative
        catalog = json.loads(catalog_path.read_text())
        (entry,) = [plugin for plugin in catalog["plugins"] if plugin.get("name") == "axiom"]
        entry["source"] = catalog_source(previous_tag, host)
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n")
    changelog = root / "CHANGELOG.md"
    text = changelog.read_text()
    if f"\n## {version} - unreleased\n" not in text:
        first = text.index("\n## ")
        changelog.write_text(
            text[: first + 1]
            + f"## {version} - unreleased\n\n### Changed\n\n- Fixture change.\n\n"
            + "### Behavioral impact\n\nNone.\n\n### Required action\n\nNone.\n\n"
            + text[first + 1 :]
        )
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture")
    return git(root, "rev-parse", "HEAD").strip()


class FakeCatalogGitHub:
    """In-memory repository state for the catalog handoff stage."""

    def __init__(self, root: Path, main: str, tag: str) -> None:
        self.root = root
        self.main = main
        self.base = main
        self.tag = tag
        self.merge = "d" * 40
        self.commit = "c" * 40
        self.tree: str | None = None
        self.additions: list[str] = []
        self.branch: str | None = None
        self.deleted: list[str] = []

    def get(self, path: str, *, allow_not_found: bool = False) -> Any:
        parsed = urllib.parse.urlsplit(path)
        route = parsed.path.removeprefix(f"/repos/{REPOSITORY}")
        query = dict(urllib.parse.parse_qsl(parsed.query))
        if route == "/releases/latest":
            return final_release(5, self.tag, "e" * 40)
        if route.startswith("/contents/"):
            relative = route.removeprefix("/contents/")
            if query["ref"] == self.merge:
                data = (self.root / relative).read_bytes()
            else:
                data = git(self.root, "show", f"HEAD:{relative}").encode()
            return {"encoding": "base64", "content": base64.b64encode(data).decode()}
        if route == "/git/ref/heads/main":
            return {"ref": "refs/heads/main", "object": {"type": "commit", "sha": self.main}}
        if route.startswith("/git/ref/heads/catalog/"):
            if self.branch is None or self.tree is None:
                return None
            return {"ref": f"refs/heads/{self.branch}", "object": {"type": "commit", "sha": self.commit}}
        if route.startswith("/git/commits/"):
            return {"tree": {"sha": self.tree}, "parents": [{"sha": self.base}]}
        if route.startswith("/commits/") and route.endswith("/check-runs"):
            runs = [
                check_run(70 + index, name, self.commit, "completed", "success")
                for index, name in enumerate(CATALOG_REQUIRED_CHECKS)
            ]
            return {"total_count": len(runs), "check_runs": runs}
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        route = urllib.parse.urlsplit(path).path.removeprefix(f"/repos/{REPOSITORY}")
        if route == "/git/refs":
            self.branch = payload["ref"].removeprefix("refs/heads/")
            self.base = payload["sha"]
            return {"ref": payload["ref"]}
        if route == "/pulls":
            return {"number": 7, "head": {"sha": self.commit}}
        raise AssertionError(f"unexpected POST {path}")

    def graphql(self, query: str, variables: dict[str, Any]) -> Any:
        if "createCommitOnBranch" in query:
            change = variables["input"]
            assert change["expectedHeadOid"] == self.main
            for addition in change["fileChanges"]["additions"]:
                assert base64.b64decode(addition["contents"]) == (self.root / addition["path"]).read_bytes()
                self.additions.append(addition["path"])
            self.tree = git(self.root, "write-tree").strip()
            return {"createCommitOnBranch": {"commit": {"oid": self.commit}}}
        oid = variables["oid"]
        return {
            "repository": {
                "object": {
                    "oid": oid,
                    "signature": {"isValid": True, "state": "VALID", "wasSignedByGitHub": True},
                }
            }
        }

    def put(self, path: str, payload: dict[str, Any]) -> Any:
        assert payload["merge_method"] == "squash" and payload["sha"] == self.commit
        self.main = self.merge
        return {"merged": True, "sha": self.merge}

    def delete(self, path: str) -> Any:
        self.deleted.append(path)
        return None

    def upload(self, url: str, data: bytes, content_type: str) -> Any:
        raise AssertionError("unexpected upload")


class CatalogHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "repository"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.directory.cleanup()

    def worktree_count(self) -> int:
        return len(git(self.root, "worktree", "list", "--porcelain").strip().split("\n\n"))

    def test_rehearsal_applies_the_handoff_in_a_disposable_worktree(self):
        main = prepare_handoff_repository(self.root, "0.21.0")
        probe_output = Path(self.directory.name) / "probe.txt"
        probe = (
            "-c",
            "import json, pathlib, sys; "
            "changelog = pathlib.Path('CHANGELOG.md').read_text(); "
            "assert '## 0.21.0 - 2026-11-03\\n' in changelog, changelog[:200]; "
            "catalog = json.loads(pathlib.Path('.claude-plugin/marketplace.json').read_text()); "
            "assert catalog['plugins'][0]['source']['ref'] == 'v0.21.0', catalog; "
            "pathlib.Path(sys.argv[1]).write_text(str(pathlib.Path.cwd()))",
            str(probe_output),
        )
        rehearse_catalog_handoff(
            self.root, main, "0.21.0", "v0.21.0", today="2026-11-03", commands=(probe,)
        )
        rehearsal_tree = Path(probe_output.read_text())
        self.assertNotEqual(self.root.resolve(), rehearsal_tree.resolve())
        self.assertFalse(rehearsal_tree.exists())
        self.assertEqual("", git(self.root, "status", "--porcelain"))
        self.assertIn("## 0.21.0 - unreleased\n", (self.root / "CHANGELOG.md").read_text())
        self.assertEqual(1, self.worktree_count())

    def test_rehearsal_failure_names_the_command_and_removes_the_worktree(self):
        main = prepare_handoff_repository(self.root, "0.21.0")
        failing = ("-c", "import sys; print('handoff checks failed', file=sys.stderr); sys.exit(3)")
        with self.assertRaisesRegex(
            PipelineError, r"rehearsed catalog handoff for v0\.21\.0 fails `python -B -c"
        ) as raised:
            rehearse_catalog_handoff(
                self.root, main, "0.21.0", "v0.21.0", today="2026-11-03", commands=(failing,)
            )
        self.assertIn("handoff checks failed", str(raised.exception))
        self.assertEqual("", git(self.root, "status", "--porcelain"))
        self.assertEqual(1, self.worktree_count())

    def test_rehearsal_rejects_a_tag_that_does_not_name_the_version(self):
        with self.assertRaisesRegex(PipelineError, "does not name version"):
            rehearse_catalog_handoff(self.root, "1" * 40, "0.21.0", "v0.22.0", today="2026-11-03")

    def test_handoff_rejects_a_superseded_version(self):
        prepare_handoff_repository(self.root, "0.22.0")
        with self.assertRaisesRegex(PipelineError, "no longer applies"):
            apply_catalog_handoff(
                self.root,
                tag="v0.21.0",
                release_date="2026-11-02",
                baseline_commit="1" * 40,
                recorded_on="2026-11-02",
            )

    def test_catalog_handoff_opens_verifies_and_merges_one_signed_pull_request(self):
        main = prepare_handoff_repository(self.root, "0.21.0")
        previous = json.loads((self.root / "evidence" / "runtime-identity.json").read_text())[
            "repositoryPolicyRevision"
        ]
        api = FakeCatalogGitHub(self.root, main, "v0.21.0")
        summary = Path(self.directory.name) / "summary.md"
        outcome = run_catalog(
            root=self.root,
            read_api=api,
            write_api=api,
            repository=REPOSITORY,
            tag="v0.21.0",
            reporter=Reporter(summary, Path(self.directory.name) / "output.txt"),
            clock=FakeClock(),
            today="2026-11-03",
            run_url="https://github.com/wheakerd/axiom/actions/runs/1",
            publication_checks=lambda root: None,
        )
        self.assertEqual("advanced", outcome)
        self.assertEqual(sorted(HANDOFF_FILES), sorted(api.additions))
        self.assertEqual(["/repos/wheakerd/axiom/git/refs/heads/catalog/v0.21.0"], api.deleted)
        for host, relative in (
            ("codex", ".agents/plugins/marketplace.json"),
            ("claude-code", ".claude-plugin/marketplace.json"),
        ):
            catalog = json.loads((self.root / relative).read_text())
            self.assertEqual(catalog_source("v0.21.0", host), catalog["plugins"][0]["source"])
        ledger = json.loads(
            (self.root / "evidence" / "repository-policy-revisions-v1.json").read_text()
        )
        self.assertEqual(
            {
                "revision": previous + 1,
                "recordedOn": "2026-11-03",
                "baselineCommit": main,
                "sourceIssue": None,
            },
            {key: ledger["revisions"][-1][key] for key in ("revision", "recordedOn", "baselineCommit", "sourceIssue")},
        )
        changelog = (self.root / "CHANGELOG.md").read_text()
        self.assertIn("## 0.21.0 - 2026-11-02\n", changelog)
        self.assertNotIn("## 0.21.0 - unreleased", changelog)
        self.assertLess(
            changelog.index(f"## Repository policy revision {previous + 1}\n"),
            changelog.index("## 0.21.0 - 2026-11-02\n"),
        )
        self.assertIn("Merged commit | `" + "d" * 40, summary.read_text())


if __name__ == "__main__":
    unittest.main()
