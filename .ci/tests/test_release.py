"""Offline tests for the tag-driven release: stamping, the zip, notes, and the gates."""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.manifests import MANIFEST_FILES
from axiom_validation.release import (
    GITHUB_ACTIONS_APP_ID,
    RELEASE_BRANCH_ROOT,
    Clock,
    ReleaseError,
    Reporter,
    build_plugin_zip,
    build_release,
    check_release_workflow_contract,
    highest_tag_below,
    immediate_successors,
    inspect_release_branch,
    read_release_files,
    release_notes,
    run_release,
    stamp_files,
    stamp_manifest,
    tree_sha,
    validate_tag,
)
from axiom_validation.runtime_identity import INPUT_MANIFEST_RELATIVE


REPOSITORY = "wheakerd/axiom"
TAG_OBJECT = "7" * 40
GIT = ("git", "-c", "user.name=release-test", "-c", "user.email=release-test@invalid", "-c", "commit.gpgsign=false")
SIGNED_MESSAGE = (
    "Fixed the startup gate.\r\n\r\nRequired action: None.\r\n"
    "-----BEGIN PGP SIGNATURE-----\n\niQEzBAABCAAdFiEE\n-----END PGP SIGNATURE-----\n"
)


def git(root: Path, *arguments: str) -> str:
    return subprocess.run([*GIT, "-C", str(root), *arguments], capture_output=True, text=True, check=True).stdout


def fixture_repository(directory: Path) -> tuple[Path, str]:
    """Commit a versionless plugin tree, LICENSE, and the digest input policy."""
    root = directory / "source"
    root.mkdir()
    shutil.copytree(REPOSITORY_ROOT / "plugin", root / "plugin")
    shutil.copy2(REPOSITORY_ROOT / "LICENSE", root / "LICENSE")
    policy = root / INPUT_MANIFEST_RELATIVE
    policy.parent.mkdir(parents=True)
    shutil.copy2(REPOSITORY_ROOT / INPUT_MANIFEST_RELATIVE, policy)
    for relative in MANIFEST_FILES:
        document = json.loads((root / relative).read_text(encoding="utf-8"))
        document.pop("version", None)
        (root / relative).write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "tagged tree")
    return root, git(root, "rev-parse", "HEAD").strip()


class FakeGitHub:
    """An offline GitHub that holds commits as file maps and records every write."""

    def __init__(self, root: Path, commit: str, *, tag: str = "v1.2.3", tags: tuple[str, ...] = ("v1.2.2",),
                 latest_digest: str | None = "sha256:" + "0" * 64, release_head: dict[str, bytes] | None = None,
                 release_head_version: str = "1.2.2") -> None:
        self.root = root
        self.commit = commit
        self.tag = tag
        self.tags = (*tags, tag)
        self.writes: list[tuple[str, str]] = []
        self.lightweight: dict[str, str] = {}
        self.commits: dict[str, dict] = {RELEASE_BRANCH_ROOT: {"files": {"LICENSE": b"old license\n"}, "parents": []}}
        self.trees: dict[str, dict[str, bytes]] = {}
        self.release_ref: str | None = None
        if release_head is not None:
            files = stamp_files(dict(release_head), release_head_version)
            self.release_ref = self._add_commit(files, [RELEASE_BRANCH_ROOT])
        evidence = {"runtimeContract": {"digest": latest_digest}} if latest_digest else {"schemaVersion": "1"}
        self.evidence_bytes = json.dumps(evidence).encode("utf-8")
        evidence_name = f"axiom-v1.2.2-release-evidence-{hashlib.sha256(self.evidence_bytes).hexdigest()}.json"
        self.latest = {
            "id": 600, "tag_name": "v1.2.2", "draft": False, "prerelease": False, "immutable": True,
            "assets": [{"id": 61, "name": evidence_name}],
        }
        self.releases: list[dict] = [self.latest]
        self.runs: dict[str, list[dict]] = {}

    def _add_commit(self, files: dict[str, bytes], parents: list[str]) -> str:
        sha = hashlib.sha1(repr((sorted(files.items()), parents)).encode()).hexdigest()
        self.commits[sha] = {"files": dict(files), "parents": parents}
        self.trees[tree_sha(files)] = dict(files)
        return sha

    def _commit_document(self, sha: str) -> dict:
        files = self.commits[sha]["files"]
        self.trees[tree_sha(files)] = files
        return {"sha": sha, "tree": {"sha": tree_sha(files)}, "parents": [{"sha": p} for p in self.commits[sha]["parents"]]}

    def get(self, path: str, *, allow_not_found: bool = False):
        prefix = f"/repos/{REPOSITORY}"
        assert path.startswith(prefix), path
        path = path[len(prefix):]
        if path == f"/git/ref/tags/{self.tag}":
            return {"ref": f"refs/tags/{self.tag}", "object": {"type": "tag", "sha": TAG_OBJECT}}
        if path.startswith("/git/ref/tags/") and path.rsplit("/", 1)[1] in self.lightweight:
            name = path.rsplit("/", 1)[1]
            return {"ref": f"refs/tags/{name}", "object": {"type": "commit", "sha": self.lightweight[name]}}
        if path == f"/git/commits/{self.commit}":
            return {"sha": self.commit, "message": "Tagged commit message.\n"}
        if path == f"/git/tags/{TAG_OBJECT}":
            return {"tag": self.tag, "object": {"type": "commit", "sha": self.commit},
                    "verification": {"verified": True}, "message": SIGNED_MESSAGE}
        if path == f"/compare/main...{self.commit}":
            return {"status": "behind"}
        if path.startswith(f"/compare/{RELEASE_BRANCH_ROOT}..."):
            return {"merge_base_commit": {"sha": RELEASE_BRANCH_ROOT}, "status": "ahead"}
        if path.startswith(f"/commits/{self.commit}/check-runs"):
            names = ("repository-guards", "unit-and-integration-tests", "hook-runtime-gate",
                     "Verify signed main history", "Verify created release tag", "Observe published immutable release")
            return {"check_runs": [{"id": index + 1, "name": name, "status": "completed", "conclusion": "success",
                                    "app": {"id": GITHUB_ACTIONS_APP_ID}} for index, name in enumerate(names)]}
        if "/check-runs" in path:
            return {"check_runs": []}
        if path == "/releases/latest":
            return max((r for r in self.releases if r.get("draft") is False), key=lambda r: r["id"])
        if path.startswith("/releases?"):
            return self.releases if "page=1" in path else []
        if path.startswith("/releases/"):
            release_id = int(path.rsplit("/", 1)[1])
            return next(r for r in self.releases if r["id"] == release_id)
        if path == "/git/matching-refs/tags/v":
            return [{"ref": f"refs/tags/{name}"} for name in self.tags]
        if path == "/git/ref/heads/release":
            if self.release_ref is None:
                return None
            return {"ref": "refs/heads/release", "object": {"type": "commit", "sha": self.release_ref}}
        if path.startswith("/git/commits/"):
            return self._commit_document(path.rsplit("/", 1)[1])
        if path.startswith("/git/trees/"):
            tree, _, query = path.removeprefix("/git/trees/").partition("?")
            files = self.trees[tree]
            if query == "recursive=1":
                return {"truncated": False, "tree": [
                    {"path": name, "type": "blob", "mode": "100644", "sha": hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()}
                    for name, data in files.items()]}
            top = {name.split("/")[0]: ("tree" if "/" in name else "blob") for name in files}
            return {"tree": [{"path": name, "type": kind} for name, kind in top.items()]}
        if path.startswith("/contents/plugin/.codex-plugin/plugin.json?ref="):
            files = self.commits[path.rsplit("=", 1)[1]]["files"]
            return {"content": base64.b64encode(files["plugin/.codex-plugin/plugin.json"]).decode()}
        if path.startswith("/actions/workflows/"):
            workflow = path.split("/")[3]
            return {"workflow_runs": self.runs.get(workflow, [])}
        raise AssertionError(f"unexpected GET {path}")

    def download(self, path: str) -> bytes:
        assert path == f"/repos/{REPOSITORY}/releases/assets/61", path
        return self.evidence_bytes

    def post(self, path: str, payload: dict):
        self.writes.append(("POST", path))
        path = path.removeprefix(f"/repos/{REPOSITORY}")
        if path == "/git/refs":
            assert payload == {"ref": "refs/heads/release", "sha": RELEASE_BRANCH_ROOT}
            self.release_ref = RELEASE_BRANCH_ROOT
            return {}
        if path == "/releases":
            release = {**payload, "id": 700, "immutable": False, "assets": []}
            self.releases.append(release)
            return release
        if path.endswith("/dispatches"):
            workflow = path.split("/")[3]
            self.runs.setdefault(workflow, []).append({"id": len(self.writes), "status": "completed", "conclusion": "success"})
            if workflow == "publish-immutable-release.yml":
                draft = next(r for r in self.releases if r["id"] == 700)
                draft.update(draft=False, immutable=True)
            return None
        raise AssertionError(f"unexpected POST {path}")

    def upload(self, url: str, data: bytes, content_type: str):
        self.writes.append(("UPLOAD", url))
        name = url.rsplit("name=", 1)[1]
        release = next(r for r in self.releases if r["id"] == 700)
        release["assets"].append({"name": name, "size": len(data)})
        return {"name": name, "size": len(data)}

    def graphql(self, query: str, variables: dict):
        if query.startswith("mutation"):
            self.writes.append(("GRAPHQL", "createCommitOnBranch"))
            change = variables["input"]
            head = change["expectedHeadOid"]
            assert head == self.release_ref
            files = dict(self.commits[head]["files"])
            for deletion in change["fileChanges"]["deletions"]:
                del files[deletion["path"]]
            for addition in change["fileChanges"]["additions"]:
                files[addition["path"]] = base64.b64decode(addition["contents"])
            self.release_ref = self._add_commit(files, [head])
            return {"createCommitOnBranch": {"commit": {"oid": self.release_ref}}}
        return {"repository": {"object": {"oid": variables["oid"], "signature": {
            "isValid": True, "state": "VALID", "wasSignedByGitHub": True}}}}


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("git") is None:
            raise unittest.SkipTest("git is unavailable")
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root, cls.commit = fixture_repository(Path(cls.temporary.name))
        cls.files = read_release_files(cls.root, cls.commit)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def run_release(self, api: FakeGitHub, tag: str = "v1.2.3", checked: list | None = None):
        def check_tree(root: Path, commit: str, version: str) -> None:
            if checked is not None:
                checked.append((commit, version))

        return run_release(root=self.root, api=api, repository=REPOSITORY, tag=tag,
                           reporter=Reporter(Path(self.temporary.name) / "summary.md"),
                           clock=Clock(now=lambda: 0.0, sleep=lambda _: None), check_tree=check_tree)

    def test_checked_in_release_workflow_contract(self):
        failures: list[str] = []
        self.assertIsNotNone(check_release_workflow_contract(failures))
        self.assertEqual([], failures)
        text = (REPOSITORY_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        path = Path(self.temporary.name) / "release.yml"
        path.write_text(text.replace("  push:\n", "  workflow_dispatch:\n  push:\n", 1), encoding="utf-8")
        failures = []
        check_release_workflow_contract(failures, path)
        self.assertTrue(any("'on' differs" in failure for failure in failures), failures)

    def test_tag_grammar_and_successors(self):
        self.assertEqual("1.2.3", validate_tag("v1.2.3"))
        for tag in ("1.2.3", "v1.2", "v01.2.3", "v1.2.3-rc.1", "v1.2.3/extra"):
            with self.subTest(tag=tag), self.assertRaises(ReleaseError):
                validate_tag(tag)
        self.assertEqual(("0.27.8", "0.28.0", "1.0.0"), immediate_successors("0.27.7"))

    def test_stamp_inserts_the_version_after_name_and_only_on_versionless_manifests(self):
        relative = "plugin/.codex-plugin/plugin.json"
        stamped = stamp_manifest(self.files[relative], "1.2.3", relative)
        document = json.loads(stamped)
        self.assertEqual(["name", "version"], list(document)[:2])
        self.assertEqual("1.2.3", document["version"])
        original = json.loads(self.files[relative])
        document.pop("version")
        self.assertEqual(original, document)
        with self.assertRaisesRegex(ReleaseError, "must not declare a version"):
            stamp_manifest(stamped, "1.2.4", relative)
        with self.assertRaisesRegex(ReleaseError, "not byte-stable"):
            stamp_manifest(self.files[relative].replace(b"\n  ", b"\n   ", 1), "1.2.3", relative)

    def test_stamped_tree_changes_only_the_manifests_and_matches_git(self):
        stamped = stamp_files(self.files, "1.2.3")
        self.assertEqual(set(self.files), set(stamped))
        self.assertEqual(set(MANIFEST_FILES), {path for path in stamped if stamped[path] != self.files[path]})
        self.assertEqual({"LICENSE", "plugin"}, {path.split("/")[0] for path in stamped})
        self.assertEqual(git(self.root, "rev-parse", f"{self.commit}:plugin").strip(),
                         tree_sha({path.removeprefix("plugin/"): data for path, data in self.files.items()
                                   if path.startswith("plugin/")}))
        with tempfile.TemporaryDirectory() as scratch:
            copy = Path(scratch)
            for path, data in stamped.items():
                (copy / path).parent.mkdir(parents=True, exist_ok=True)
                (copy / path).write_bytes(data)
            git(copy, "init", "-q", "-b", "release")
            git(copy, "add", "-A")
            git(copy, "commit", "-q", "-m", "stamped")
            self.assertEqual(git(copy, "rev-parse", "HEAD^{tree}").strip(), tree_sha(stamped))

    def test_zip_is_deterministic_and_holds_exactly_the_stamped_plugin_tree(self):
        stamped = stamp_files(self.files, "1.2.3")
        first, second = build_plugin_zip(stamped), build_plugin_zip(dict(reversed(list(stamped.items()))))
        self.assertEqual(first, second)
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "plugin.zip"
            path.write_bytes(first)
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                self.assertEqual(sorted(names), names)
                self.assertEqual(sorted(p.removeprefix("plugin/") for p in stamped if p.startswith("plugin/")), names)
                self.assertIn("hooks/codex-hooks.json", names)
                self.assertEqual("1.2.3", json.loads(archive.read(".codex-plugin/plugin.json"))["version"])
                for info in archive.infolist():
                    self.assertEqual((1980, 1, 1, 0, 0, 0), info.date_time)
                    self.assertEqual(zipfile.ZIP_STORED, info.compress_type)
                    self.assertEqual(0o100644, info.external_attr >> 16)
        self.assertNotEqual(first, build_plugin_zip(stamp_files(self.files, "1.2.4")))

    def test_notes_strip_the_signature_and_append_the_compare_link(self):
        notes = release_notes(SIGNED_MESSAGE, "v1.2.3", "v1.2.2")
        self.assertEqual(
            "Fixed the startup gate.\n\nRequired action: None.\n\n"
            "https://github.com/wheakerd/axiom/compare/v1.2.2...v1.2.3\n",
            notes,
        )
        self.assertEqual("First release.\n", release_notes("First release.\n", "v0.1.0", None))
        with self.assertRaisesRegex(ReleaseError, "is empty"):
            release_notes("-----BEGIN SSH SIGNATURE-----\nabc\n-----END SSH SIGNATURE-----\n", "v1.2.3", None)
        with self.assertRaisesRegex(ReleaseError, "125000-character"):
            release_notes("x" * 125_000, "v1.2.3", "v1.2.2")

    def test_files_outside_regular_mode_are_rejected(self):
        with tempfile.TemporaryDirectory() as scratch:
            root, _ = fixture_repository(Path(scratch))
            script = root / "plugin/hooks/codex-session-start.cmd"
            script.chmod(0o755)
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "executable")
            with self.assertRaisesRegex(ReleaseError, "100755"):
                read_release_files(root, "HEAD")

    def test_build_derives_the_subject_from_the_annotated_tag(self):
        api = FakeGitHub(self.root, self.commit)
        build = build_release(self.root, api, REPOSITORY, "v1.2.3")
        self.assertEqual(self.commit, build.target.commit)
        self.assertEqual("tag", build.target.object_type)
        self.assertEqual("v1.2.2", build.previous_tag)
        self.assertTrue(build.notes.startswith("Fixed the startup gate."))
        self.assertTrue(build.runtime_digest.startswith("sha256:"))
        self.assertEqual(build.release_tree, tree_sha(build.files))
        self.assertEqual([], api.writes)

    def test_full_release_creates_the_branch_commit_draft_and_dispatches(self):
        api = FakeGitHub(self.root, self.commit)
        checked: list = []
        subject = self.run_release(api, checked=checked)
        self.assertEqual([(self.commit, "1.2.3")], checked)
        head = api.commits[api.release_ref]
        self.assertEqual([RELEASE_BRANCH_ROOT], head["parents"])
        self.assertEqual(stamp_files(self.files, "1.2.3"), head["files"])
        self.assertEqual(subject["releaseCommit"], api.release_ref)
        self.assertEqual(subject["releaseTree"], tree_sha(head["files"]))
        draft = next(r for r in api.releases if r["id"] == 700)
        self.assertEqual("axiom-v1.2.3-plugin.zip", draft["assets"][0]["name"])
        self.assertEqual(2, len(draft["assets"]))
        self.assertTrue(draft["assets"][1]["name"].startswith("axiom-v1.2.3-release-policy-"))
        self.assertEqual(
            ["/git/refs", "createCommitOnBranch", "/releases", "UPLOAD", "UPLOAD",
             "publish-immutable-release.yml", "release-signature-guard.yml"],
            [path.removeprefix(f"/repos/{REPOSITORY}").split("/")[3] if path.endswith("/dispatches")
             else ("UPLOAD" if method == "UPLOAD" else path.removeprefix(f"/repos/{REPOSITORY}"))
             for method, path in api.writes],
        )

    def test_next_release_fast_forwards_from_the_previous_release_commit(self):
        api = FakeGitHub(self.root, self.commit, release_head=self.files)
        previous = api.release_ref
        self.run_release(api)
        self.assertEqual([previous], api.commits[api.release_ref]["parents"])
        self.assertNotIn(("POST", f"/repos/{REPOSITORY}/git/refs"), api.writes)

    def test_non_successor_version_fails_before_any_write(self):
        api = FakeGitHub(self.root, self.commit, tag="v1.2.4")
        with self.assertRaisesRegex(ReleaseError, "not the next patch, minor, or major version after v1.2.2"):
            self.run_release(api, tag="v1.2.4")
        self.assertEqual([], api.writes)

    def test_a_failed_attempt_makes_the_next_version_the_successor(self):
        self.assertEqual("v1.2.3", highest_tag_below(FakeGitHub(self.root, self.commit, tag="v1.2.4",
                                                                 tags=("v1.2.2", "v1.2.3", "v2.0.0")),
                                                     REPOSITORY, "1.2.4"))
        api = FakeGitHub(self.root, self.commit, tag="v1.2.4", tags=("v1.2.2", "v1.2.3"))
        subject = self.run_release(api, tag="v1.2.4")
        self.assertEqual("v1.2.2", subject["previousTag"])

    def test_unchanged_runtime_digest_fails_before_any_write(self):
        digest = build_release(self.root, FakeGitHub(self.root, self.commit), REPOSITORY, "v1.2.3").runtime_digest
        api = FakeGitHub(self.root, self.commit, latest_digest=digest)
        with self.assertRaisesRegex(ReleaseError, "changes no installed file"):
            self.run_release(api)
        self.assertEqual([], api.writes)

    def test_latest_evidence_without_a_digest_uses_the_digest_of_latests_tree(self):
        api = FakeGitHub(self.root, self.commit, latest_digest=None)
        # Latest's lightweight tag names the same tree here, so its computed digest is equal.
        api.lightweight["v1.2.2"] = self.commit
        with self.assertRaisesRegex(ReleaseError, "changes no installed file"):
            self.run_release(api)
        self.assertEqual([], api.writes)

    def test_release_branch_must_keep_its_shape(self):
        stamped_head = dict(self.files)
        cases = {
            "extra-path": ({**stamped_head, ".github/workflows/x.yml": b"name: x\n"}, "must hold only LICENSE, plugin"),
            "same-version": (stamped_head, "already holds version 1.2.3"),
        }
        for label, (files, expected) in cases.items():
            with self.subTest(label=label):
                version = "1.2.3" if label == "same-version" else "1.2.2"
                api = FakeGitHub(self.root, self.commit, release_head=files, release_head_version=version)
                with self.assertRaisesRegex(ReleaseError, expected):
                    inspect_release_branch(api, REPOSITORY, "1.2.3")
        api = FakeGitHub(self.root, self.commit, release_head=stamped_head)
        api.get_original = api.get

        def diverged(path: str, *, allow_not_found: bool = False):
            if path.startswith(f"/repos/{REPOSITORY}/compare/{RELEASE_BRANCH_ROOT}..."):
                return {"merge_base_commit": {"sha": "9" * 40}, "status": "diverged"}
            return api.get_original(path, allow_not_found=allow_not_found)

        api.get = diverged
        with self.assertRaisesRegex(ReleaseError, "does not descend from"):
            inspect_release_branch(api, REPOSITORY, "1.2.3")
        self.assertIsNone(inspect_release_branch(FakeGitHub(self.root, self.commit), REPOSITORY, "1.2.3"))


if __name__ == "__main__":
    unittest.main()
