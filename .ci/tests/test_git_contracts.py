"""Fixture tests that run the Git procedures and configuration rules the traceable-Git skill documents."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class GitContractTests(unittest.TestCase):
    @staticmethod
    def fixture_environment(environment=None):
        inherited_namespace = os.environ.get("GIT_NAMESPACE")
        if (inherited_namespace and environment is not None and "GIT_NAMESPACE" in environment
                and environment["GIT_NAMESPACE"] != inherited_namespace):
            raise ValueError("cannot clear or replace an inherited namespace")
        return {
            **{key: os.environ[key] for key in ("SystemRoot", "WINDIR", "TEMP", "TMP", "GIT_NAMESPACE")
               if key in os.environ},
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_NO_LAZY_FETCH": "1",
            **(environment or {}),
        }

    def fixture_git(self, repository: Path, *arguments: str, check: bool = True, environment=None):
        return subprocess.run(
            ("git", "-C", str(repository), *arguments),
            env=self.fixture_environment(environment),
            check=check, capture_output=True, text=True, timeout=10,
        )

    def initialize_fixture(self, repository: Path) -> None:
        repository.mkdir()
        self.fixture_git(repository, "init", "--quiet", "--initial-branch=main")
        self.fixture_git(repository, "config", "user.name", "fixture")
        self.fixture_git(repository, "config", "user.email", "fixture@example.invalid")

    def fixture_commit(self, repository: Path, subject: str) -> str:
        self.fixture_git(repository, "commit", "--quiet", "--allow-empty", "-m", subject)
        return self.fixture_git(repository, "rev-parse", "HEAD").stdout.strip()

    def fixture_configuration_safe(self, repository, *git_options, environment=None):
        """Resolve only isolated fixture facts; this is not an installed runner."""
        def read(key, *, boolean=False, multiple=False):
            result = self.fixture_git(
                repository, *git_options, "config", "--null",
                *(("--type=bool",) if boolean else ()),
                "--get-all", key,
                check=False, environment=environment,
            )
            if result.returncode == 1 and not result.stdout and not result.stderr:
                return None
            if result.returncode != 0 or not result.stdout.endswith("\0"):
                raise ValueError("unreadable or malformed configuration")
            values = result.stdout[:-1].split("\0")
            if boolean and any(value not in ("true", "false") for value in values):
                raise ValueError("unclassifiable configuration")
            if multiple:
                return values
            return values[-1]

        try:
            namespace = self.fixture_environment(environment).get("GIT_NAMESPACE", "")
            if type(namespace) is not str or namespace:
                return False
            if read("remotes.origin", multiple=True) is not None:
                return False
            # This fixture models fully qualified exact and single-wildcard
            # mappings for the fixed command `git push origin main` only.
            # Unsupported evidence stops; no installed parser is supplied.
            mappings = []
            for value in read("remote.origin.push", multiple=True) or []:
                forced = value.startswith("+")
                refspec = value[1:] if forced else value
                if refspec.count(":") != 1:
                    raise ValueError("unsupported fixture refspec")
                source, destination = refspec.split(":")
                if source.count("*") != destination.count("*"):
                    raise ValueError("unclassifiable fixture refspec")
                for ref in (source, destination):
                    if self.fixture_git(repository, "check-ref-format", "--refspec-pattern", ref,
                                        check=False, environment=environment).returncode != 0:
                        raise ValueError("unsupported fixture refspec")
                mappings.append((source, destination, forced))
            frozen = "refs/heads/main"
            mapped = None
            for source, destination, forced in mappings:
                if "*" in source:
                    prefix, suffix = source.split("*")
                    if (not frozen.startswith(prefix) or not frozen.endswith(suffix)
                            or len(frozen) < len(prefix) + len(suffix)):
                        continue
                    matched = frozen[len(prefix):len(frozen) - len(suffix) if suffix else None]
                    destination = destination.replace("*", matched)
                elif source != frozen:
                    continue
                mapped = destination, forced
                break  # Git uses the first matching remote push refspec.
            default = read("push.default")
            if default not in (None, "nothing", "current", "upstream", "tracking", "simple", "matching"):
                raise ValueError("unclassifiable push default")
            if mapped is None and default in ("upstream", "tracking"):
                if read("branch.main.remote") != "origin":
                    raise ValueError("unresolved fixture upstream remote")
                merge = read("branch.main.merge", multiple=True)
                if merge is None or len(merge) != 1:
                    raise ValueError("unresolved fixture upstream destination")
                mapped = merge[0], False
            if mapped is not None and mapped != (frozen, False):
                return False
            follow_tags = read("push.followTags", boolean=True)
            mirror = read("remote.origin.mirror", boolean=True)
            inherited_recursion = read("submodule.recurse", boolean=True, multiple=True) or []
            ordered_recursion = self.fixture_git(
                repository, *git_options, "config", "--null", "--get-regexp",
                r"^(push\.recursesubmodules|submodule\.recurse)$",
                check=False, environment=environment,
            )
            if (ordered_recursion.returncode == 1 and not ordered_recursion.stdout
                    and not ordered_recursion.stderr):
                records = []
            elif ordered_recursion.returncode == 0 and ordered_recursion.stdout.endswith("\0"):
                records = ordered_recursion.stdout[:-1].split("\0")
            else:
                raise ValueError("unreadable recursion traversal")
            recursion, inherited_index = "no", 0
            # Git feeds both keys into one variable in configuration traversal
            # order. Native boolean parsing above also covers valueless keys.
            for record in records:
                key, separator, value = record.partition("\n")
                if key == "submodule.recurse" and inherited_index < len(inherited_recursion):
                    recursion = "on-demand" if inherited_recursion[inherited_index] == "true" else "no"
                    inherited_index += 1
                elif (key == "push.recursesubmodules" and separator
                      and value in ("no", "check", "on-demand", "only")):
                    recursion = value
                else:
                    raise ValueError("malformed recursion traversal")
            if inherited_index != len(inherited_recursion):
                raise ValueError("inconsistent recursion traversal")
            options = []
            for value in read("push.pushOption", multiple=True) or []:
                if value == "":
                    options.clear()
                else:
                    options.append(value)
        except ValueError:
            return False
        return (
            follow_tags != "true" and mirror != "true" and not options
            and recursion in ("no", "check")
        )

    def test_direct_configuration_uses_git_boolean_parsing_and_defaults(self):
        with tempfile.TemporaryDirectory(prefix="axiom-direct-config-") as temporary:
            repository = Path(temporary) / "repository"
            self.initialize_fixture(repository)
            self.assertTrue(self.fixture_configuration_safe(repository))
            for key in ("push.followTags", "remote.origin.mirror", "submodule.recurse"):
                for value, expected in (("false", True), ("no", True), ("off", True),
                                        ("0", True), ("", True), ("true", False),
                                        ("yes", False), ("on", False), ("2", False),
                                        ("invalid", False)):
                    with self.subTest(key=key, value=value):
                        self.assertEqual(expected, self.fixture_configuration_safe(
                            repository, "-c", f"{key}={value}"))
            config = repository / ".git" / "config"
            config.write_text(config.read_text() + "\n[push]\nfollowTags\n")
            self.assertFalse(self.fixture_configuration_safe(repository))

    def test_direct_configuration_resolves_inheritance_scopes_and_overrides(self):
        with tempfile.TemporaryDirectory(prefix="axiom-direct-config-") as temporary:
            root = Path(temporary)
            repository = root / "repository"
            self.initialize_fixture(repository)
            inherited = root / "inherited.config"
            inherited.write_text("[push]\nfollowTags = true\n")
            self.fixture_git(repository, "config", f"includeIf.gitdir:{repository}/.git.path", str(inherited))
            self.assertFalse(self.fixture_configuration_safe(repository))
            self.fixture_git(repository, "config", "push.followTags", "false")
            self.assertTrue(self.fixture_configuration_safe(repository))
            self.fixture_git(repository, "config", "extensions.worktreeConfig", "true")
            self.fixture_git(repository, "config", "--worktree", "push.followTags", "true")
            self.assertFalse(self.fixture_configuration_safe(repository))
            environment = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "push.followTags",
                           "GIT_CONFIG_VALUE_0": "false"}
            self.assertTrue(self.fixture_configuration_safe(repository, environment=environment))
            self.assertFalse(self.fixture_configuration_safe(
                repository, "-c", "push.followTags=true", environment=environment))
            self.assertFalse(self.fixture_configuration_safe(
                repository, "-c", "push.followTags=invalid", "-c", "push.followTags=false"))

    def test_direct_configuration_push_option_ordered_empty_resets(self):
        with tempfile.TemporaryDirectory(prefix="axiom-direct-config-") as temporary:
            repository = Path(temporary) / "repository"
            self.initialize_fixture(repository)
            for values, expected in (((), True), (("",), True), (("one",), False),
                                     (("one", ""), True), (("", "one"), False),
                                     (("one", "two", "", ""), True),
                                     (("one", "", "two"), False)):
                with self.subTest(values=values):
                    options = tuple(part for value in values for part in ("-c", f"push.pushOption={value}"))
                    self.assertEqual(expected, self.fixture_configuration_safe(repository, *options))
            inherited = Path(temporary) / "global.config"
            inherited.write_text("[push]\npushOption = inherited\n")
            environment = {"GIT_CONFIG_GLOBAL": str(inherited)}
            self.assertFalse(self.fixture_configuration_safe(repository, environment=environment))
            self.assertTrue(self.fixture_configuration_safe(
                repository, "-c", "push.pushOption=", environment=environment))

    def test_direct_configuration_recursion_explicit_and_inherited_modes(self):
        with tempfile.TemporaryDirectory(prefix="axiom-direct-config-") as temporary:
            repository = Path(temporary) / "repository"
            self.initialize_fixture(repository)
            for mode, expected in (("no", True), ("check", True), ("on-demand", False),
                                   ("only", False), ("unknown", False), ("", False)):
                for inherited in ("true", "false"):
                    with self.subTest(mode=mode, inherited=inherited):
                        self.assertEqual(expected, self.fixture_configuration_safe(
                            repository, "-c", f"submodule.recurse={inherited}",
                            "-c", f"push.recurseSubmodules={mode}"))
                        # Reversing traversal order lets the final boolean
                        # select on-demand or no; malformed values still stop.
                        self.assertEqual(inherited == "false" and mode not in ("unknown", ""),
                                         self.fixture_configuration_safe(
                                             repository, "-c", f"push.recurseSubmodules={mode}",
                                             "-c", f"submodule.recurse={inherited}"))
            inherited_file = Path(temporary) / "global.config"
            inherited_file.write_text("[push]\nrecurseSubmodules = no\n")
            self.fixture_git(repository, "config", "submodule.recurse", "true")
            environment = {"GIT_CONFIG_GLOBAL": str(inherited_file)}
            self.assertFalse(self.fixture_configuration_safe(repository, environment=environment))
            environment.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "push.recurseSubmodules",
                                "GIT_CONFIG_VALUE_0": "no"})
            self.assertTrue(self.fixture_configuration_safe(repository, environment=environment))
            self.assertFalse(self.fixture_configuration_safe(
                repository, "-c", "submodule.recurse=true", environment=environment))

    def test_native_joint_recursion_last_boolean_controls_submodule_push(self):
        cases = (
            ("on-demand", "false", False),
            ("only", "false", False),
            ("no", "true", True),
            ("check", "true", True),
        )
        for earlier_mode, later_boolean, pushes_child in cases:
            with self.subTest(earlier_mode=earlier_mode, later_boolean=later_boolean), tempfile.TemporaryDirectory(
                    prefix="axiom-direct-recursion-") as temporary:
                root = Path(temporary)
                child_source = root / "child-source"
                self.initialize_fixture(child_source)
                child_base = self.fixture_commit(child_source, "child base")
                child_remote = root / "child.git"
                self.fixture_git(child_source, "clone", "--bare", "--quiet", str(child_source), str(child_remote))

                repository = root / "repository"
                self.initialize_fixture(repository)
                self.fixture_git(repository, "-c", "protocol.file.allow=always", "submodule", "add",
                                 "--quiet", str(child_remote), "module")
                self.fixture_commit(repository, "parent base")
                remote = root / "remote.git"
                self.fixture_git(repository, "clone", "--bare", "--quiet", str(repository), str(remote))
                self.fixture_git(repository, "remote", "add", "origin", str(remote))

                child = repository / "module"
                self.fixture_git(child, "config", "user.name", "fixture")
                self.fixture_git(child, "config", "user.email", "fixture@example.invalid")
                child_tip = self.fixture_commit(child, "unpublished child")
                self.fixture_git(repository, "add", "--", "module")
                parent_tip = self.fixture_commit(repository, "reference unpublished child")
                self.fixture_git(repository, "config", "--add", "push.recurseSubmodules", earlier_mode)
                self.fixture_git(repository, "config", "--add", "submodule.recurse", later_boolean)

                self.assertEqual(not pushes_child, self.fixture_configuration_safe(repository))
                # Exercise Git itself against disposable local remotes: a final
                # false resets even only/on-demand to no, while true selects
                # on-demand even after no/check. Never infer this from the
                # fixture configuration classifier alone.
                self.fixture_git(repository, "push", "origin", "main")
                self.assertEqual(parent_tip, self.fixture_git(
                    remote, "rev-parse", "refs/heads/main").stdout.strip())
                self.assertEqual(child_tip if pushes_child else child_base, self.fixture_git(
                    child_remote, "rev-parse", "refs/heads/main").stdout.strip())

    def test_direct_configuration_read_and_parse_errors_stop(self):
        with tempfile.TemporaryDirectory(prefix="axiom-direct-config-") as temporary:
            repository = Path(temporary) / "repository"
            self.initialize_fixture(repository)
            for namespace in ("fixture-namespace", None, 1):
                with self.subTest(namespace=namespace):
                    self.assertFalse(self.fixture_configuration_safe(
                        repository, environment={"GIT_NAMESPACE": namespace}))
            with patch.dict(os.environ, {"GIT_NAMESPACE": "fixture-namespace"}):
                self.assertEqual("fixture-namespace", self.fixture_environment()["GIT_NAMESPACE"])
                self.assertFalse(self.fixture_configuration_safe(repository))
                self.assertFalse(self.fixture_configuration_safe(repository, environment={"GIT_NAMESPACE": ""}))
                self.assertEqual("fixture-namespace", os.environ["GIT_NAMESPACE"])
            self.assertFalse(self.fixture_configuration_safe(
                repository, environment={"GIT_CONFIG_GLOBAL": str(repository)}))
            (repository / ".git" / "config").write_text("[malformed\n")
            self.assertFalse(self.fixture_configuration_safe(repository))

    def test_prepared_release_atomic_push_does_not_leave_a_branch_without_its_tag(self):
        with tempfile.TemporaryDirectory(prefix="axiom-prepared-release-") as temporary:
            root = Path(temporary)
            repository = root / "client"
            remote = root / "remote.git"
            self.initialize_fixture(repository)
            remote.mkdir()
            self.fixture_git(remote, "init", "--bare", "--quiet")
            baseline = self.fixture_commit(repository, "base")
            self.fixture_git(repository, "push", "--quiet", str(remote), "refs/heads/main:refs/heads/main")
            final = self.fixture_commit(repository, "prepared release")
            tag_ref = "refs/tags/v1.2.3"
            self.fixture_git(repository, "update-ref", "--no-deref", tag_ref, final, "0" * 40)
            self.fixture_git(remote, "update-ref", "--no-deref", tag_ref, baseline, "0" * 40)
            refspecs = ("refs/heads/main:refs/heads/main", f"{tag_ref}:{tag_ref}")
            rejected = self.fixture_git(repository, "push", "--atomic", str(remote), *refspecs, check=False)
            self.assertNotEqual(0, rejected.returncode)
            self.assertEqual(baseline, self.fixture_git(remote, "rev-parse", "refs/heads/main").stdout.strip())
            self.assertEqual(baseline, self.fixture_git(remote, "rev-parse", tag_ref).stdout.strip())
            # Restore this disposable receiver's test precondition; production
            # recovery must retain a conflicting immutable tag and stop.
            self.fixture_git(remote, "update-ref", "--no-deref", "-d", tag_ref, baseline)
            self.fixture_git(repository, "push", "--atomic", str(remote), *refspecs)
            self.assertEqual(final, self.fixture_git(remote, "rev-parse", "refs/heads/main").stdout.strip())
            self.assertEqual(final, self.fixture_git(remote, "rev-parse", tag_ref).stdout.strip())

    def run_git(self, repository: Path, *arguments: str, stdin: str | None = None, check: bool = True):
        return subprocess.run(
            ("git", "-C", str(repository), *arguments),
            env=self.fixture_environment(), input=stdin,
            check=check, capture_output=True, text=True, timeout=10,
        )

    def write_hook(self, repository: Path, name: str, body: str) -> None:
        hooks = repository / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / name
        hook.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        hook.chmod(0o755)

    def test_commit_procedures_match_the_skill_text(self):
        """Execute the traceable-git-submit commit, consolidation, tag, and URL-push procedures against a fixture."""
        commit = ("commit", "--quiet", "--no-status", "-F", "-")
        with tempfile.TemporaryDirectory(prefix="axiom-commit-procedures-") as temporary:
            root = Path(temporary)
            repository = root / "repo"
            self.initialize_fixture(repository)
            base = self.fixture_commit(repository, "base")
            log = root / "hooks.log"
            self.write_hook(repository, "pre-commit", f"echo pre-commit >> '{log}'\n")
            self.write_hook(repository, "commit-msg", f"echo commit-msg >> '{log}'\n")

            # 1 and 2: ordinary git commit from the verified index runs both hooks and
            # carries the recorded tree and parent.
            (repository / "a.txt").write_text("one\n", encoding="utf-8")
            self.run_git(repository, "add", "--", "a.txt")
            staged = self.run_git(repository, "write-tree").stdout.strip()
            self.run_git(repository, *commit, stdin="feat: one\n\nScope:\none\n")
            first = self.run_git(repository, "rev-parse", "HEAD").stdout.strip()
            self.assertEqual(["pre-commit", "commit-msg"], log.read_text(encoding="utf-8").split())
            self.assertEqual(base, self.run_git(repository, "rev-parse", "HEAD^").stdout.strip())
            self.assertEqual(staged, self.run_git(repository, "rev-parse", "HEAD^{tree}").stdout.strip())

            # 9: Git's default message cleanup is not byte-preserving.
            self.assertNotEqual("feat: one  \n\n\nScope:\none\n",
                                self.run_git(repository, "log", "-1", "--format=%B").stdout)

            # A failing pre-commit hook leaves HEAD unchanged.
            self.write_hook(repository, "pre-commit", "exit 1\n")
            (repository / "a.txt").write_text("two\n", encoding="utf-8")
            self.run_git(repository, "add", "--", "a.txt")
            refused = self.run_git(repository, *commit, stdin="feat: two\n", check=False)
            self.assertNotEqual(0, refused.returncode)
            self.assertEqual(first, self.run_git(repository, "rev-parse", "HEAD").stdout.strip())

            # 3: a hook that rewrites the index makes the tree proof fail; compare-and-swap restores the branch.
            self.write_hook(repository, "pre-commit", "printf 'rewritten\\n' > a.txt && git add -- a.txt\n")
            staged = self.run_git(repository, "write-tree").stdout.strip()
            self.run_git(repository, *commit, stdin="feat: two\n")
            rejected = self.run_git(repository, "rev-parse", "HEAD").stdout.strip()
            self.assertNotEqual(staged, self.run_git(repository, "rev-parse", "HEAD^{tree}").stdout.strip())
            self.run_git(repository, "update-ref", "--no-deref", "refs/heads/main", first, rejected)
            self.assertEqual(first, self.run_git(repository, "rev-parse", "HEAD").stdout.strip())
            self.write_hook(repository, "pre-commit", "exit 0\n")
            self.run_git(repository, "read-tree", first)

            # 4: an empty checkpoint needs --allow-empty.
            self.assertNotEqual(0, self.run_git(repository, *commit, stdin="chore: empty\n", check=False).returncode)
            self.assertEqual(first, self.run_git(repository, "rev-parse", "HEAD").stdout.strip())
            self.run_git(repository, *commit, "--allow-empty", stdin="chore: empty\n")
            self.assertEqual(first, self.run_git(repository, "rev-parse", "HEAD^").stdout.strip())

            # 5: consolidation moves the branch to the upstream by compare-and-swap and commits the index.
            old_head = self.run_git(repository, "rev-parse", "HEAD").stdout.strip()
            final_tree = self.run_git(repository, "rev-parse", "HEAD^{tree}").stdout.strip()
            self.run_git(repository, "update-ref", "--no-deref", "refs/heads/main", base, old_head)
            self.assertEqual(final_tree, self.run_git(repository, "write-tree").stdout.strip())
            self.run_git(repository, *commit, stdin="feat: consolidated\n")
            new_commit = self.run_git(repository, "rev-parse", "HEAD").stdout.strip()
            self.assertEqual(base, self.run_git(repository, "rev-parse", "HEAD^").stdout.strip())
            self.assertEqual(final_tree, self.run_git(repository, "rev-parse", "HEAD^{tree}").stdout.strip())

            # 6: when the consolidation commit does not complete, the branch sits at the upstream and is restorable.
            self.run_git(repository, "update-ref", "--no-deref", "refs/heads/main", old_head, new_commit)
            self.write_hook(repository, "pre-commit", "exit 1\n")
            self.run_git(repository, "update-ref", "--no-deref", "refs/heads/main", base, old_head)
            self.assertNotEqual(0, self.run_git(repository, *commit, stdin="feat: consolidated\n", check=False).returncode)
            self.assertEqual(base, self.run_git(repository, "rev-parse", "HEAD").stdout.strip())
            self.run_git(repository, "update-ref", "--no-deref", "refs/heads/main", old_head, base)
            self.assertEqual(old_head, self.run_git(repository, "rev-parse", "HEAD").stdout.strip())
            self.write_hook(repository, "pre-commit", "exit 0\n")

            # 7: git tag refuses an existing name in lightweight and annotated mode.
            self.run_git(repository, "tag", "v1.0.0")
            self.assertNotEqual(0, self.run_git(repository, "tag", "v1.0.0", check=False).returncode)
            self.assertNotEqual(0, self.run_git(repository, "tag", "-a", "-m", "again", "v1.0.0", check=False).returncode)
            self.run_git(repository, "tag", "-a", "-m", "annotated", "v1.1.0")
            self.assertNotEqual(0, self.run_git(repository, "tag", "v1.1.0", check=False).returncode)
            self.assertEqual(old_head, self.run_git(repository, "rev-parse", "v1.1.0^{}").stdout.strip())

            # 8: a push named by a configured URL resolves to that remote, updates its tracking ref, and hands pre-push the URL.
            remote = root / "remote.git"
            remote.mkdir()
            self.run_git(remote, "init", "--bare", "--quiet")
            self.run_git(repository, "remote", "add", "origin", str(remote))
            seen = root / "pre-push.log"
            self.write_hook(repository, "pre-push", f"printf '%s\\n' \"$1\" >> '{seen}'\n")
            self.run_git(repository, "push", "--quiet", "--no-follow-tags", str(remote), "refs/heads/main:refs/heads/main")
            self.assertEqual(old_head, self.run_git(remote, "rev-parse", "refs/heads/main").stdout.strip())
            self.assertEqual(old_head, self.run_git(repository, "rev-parse", "--verify", "refs/remotes/origin/main").stdout.strip())
            self.assertEqual(str(remote), seen.read_text(encoding="utf-8").strip())


if __name__ == "__main__":
    unittest.main()
