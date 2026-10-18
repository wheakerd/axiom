"""Focused tests for traceable-Git safety gates and fixtures."""

import copy
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from axiom_validation.git_contracts import (
    CLEANUP_AUTHORITY_FIELDS,
    backup_cleanup_transition,
    backup_ref_gate,
    direct_push_fast_forward_gate,
    lightweight_direct_submit_gate,
    lightweight_push_arguments,
    lightweight_push_outcome,
    ordinary_combined_commit_push_gate,
    ordered_push_baselines_gate,
    safe_git_oid,
    safe_git_operand,
)
from axiom_validation.cases.git_contracts import check_traceable_security_contracts


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

    @staticmethod
    def fixture_direct_gate(configuration_safe, *, rechecked=True):
        return lightweight_direct_submit_gate(
            target_count=1, configured_named_remote=True, exact_branch=True,
            force_requested=False, widened_refspec=False, fetch_requested=False,
            retry_requested=False, identity_rechecked=True, operation_state_clear=True,
            target_unchanged=True, mechanism_conflict=False,
            effective_configuration_safe=configuration_safe,
            configuration_rechecked=rechecked,
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

    def test_direct_configuration_precommit_conflict_and_prepush_drift_stop(self):
        with tempfile.TemporaryDirectory(prefix="axiom-direct-config-") as temporary:
            repository = Path(temporary) / "repository"
            self.initialize_fixture(repository)
            before = self.fixture_commit(repository, "base")
            self.fixture_git(repository, "config", "push.followTags", "true")
            mutations = []
            if self.fixture_direct_gate(self.fixture_configuration_safe(repository)):
                mutations.append(self.fixture_commit(repository, "unauthorized"))
            self.assertEqual([], mutations)
            self.assertEqual(before, self.fixture_git(repository, "rev-parse", "HEAD").stdout.strip())
            self.fixture_git(repository, "config", "push.followTags", "false")
            self.assertTrue(self.fixture_direct_gate(self.fixture_configuration_safe(repository)))
            final = self.fixture_commit(repository, "candidate")
            self.fixture_git(repository, "config", "push.pushOption", "drift")
            self.assertFalse(self.fixture_direct_gate(self.fixture_configuration_safe(repository)))
            self.assertFalse(self.fixture_direct_gate(True, rechecked=False))
            self.assertEqual(final, self.fixture_git(repository, "rev-parse", "HEAD").stdout.strip())

    def test_direct_push_only_checks_configuration_without_a_commit_step(self):
        with tempfile.TemporaryDirectory(prefix="axiom-direct-push-only-") as temporary:
            root = Path(temporary)
            repository = root / "repository"
            self.initialize_fixture(repository)
            # The requested submission starts with an already committed HEAD.
            before = self.fixture_commit(repository, "existing candidate")
            remote = root / "remote.git"
            remote.mkdir()
            self.fixture_git(remote, "init", "--bare", "--quiet", "--initial-branch=main")
            self.fixture_git(repository, "remote", "add", "origin", str(remote))
            pushes = []

            def submit_existing_commit():
                if not self.fixture_direct_gate(self.fixture_configuration_safe(repository)):
                    return None
                arguments = ("git", "push", "origin", "main")
                self.assertTrue(lightweight_push_arguments(arguments, "origin", "main"))
                pushes.append(arguments)
                return self.fixture_git(repository, *arguments[1:])

            self.fixture_git(repository, "config", "push.followTags", "true")
            self.assertIsNone(submit_existing_commit())
            self.assertEqual([], pushes)
            self.assertNotEqual(0, self.fixture_git(
                remote, "rev-parse", "--verify", "refs/heads/main", check=False).returncode)
            self.assertEqual(before, self.fixture_git(repository, "rev-parse", "HEAD").stdout.strip())

            self.fixture_git(repository, "config", "push.followTags", "false")
            self.assertEqual(0, submit_existing_commit().returncode)
            self.assertEqual([("git", "push", "origin", "main")], pushes)
            self.assertEqual(before, self.fixture_git(remote, "rev-parse", "refs/heads/main").stdout.strip())
            self.assertEqual(before, self.fixture_git(repository, "rev-parse", "HEAD").stdout.strip())

    def test_direct_mapping_and_groups_stop_before_commit_or_push(self):
        conflicts = (
            ("T1-force", (("remote.origin.push", "+refs/heads/main:refs/heads/main"),)),
            ("T2-destination", (("remote.origin.push", "refs/heads/main:refs/heads/other"),)),
            ("T4-upstream", (("push.default", "upstream"), ("branch.main.remote", "origin"),
                             ("branch.main.merge", "refs/heads/other2"))),
            ("T3-group", (("remotes.origin", "b2 b3"),)),
            ("R1-recursion-order", (("push.recurseSubmodules", "no"), ("submodule.recurse", "true"))),
            ("N1-namespace", ()),
        )
        for name, configuration in conflicts:
            for phase in ("push-only", "pre-commit", "pre-push-drift"):
                with self.subTest(conflict=name, phase=phase), tempfile.TemporaryDirectory(
                        prefix="axiom-direct-mapping-") as temporary, patch.dict(os.environ):
                    root = Path(temporary)
                    repository = root / "repository"
                    self.initialize_fixture(repository)
                    base = self.fixture_commit(repository, "base")
                    remote_tip = self.fixture_commit(repository, "remote advance")
                    remotes = []
                    for remote_name in (("origin", "b2", "b3") if name == "T3-group" else ("origin",)):
                        remote = root / f"{remote_name}.git"
                        self.fixture_git(repository, "clone", "--bare", "--quiet", str(repository), str(remote))
                        self.fixture_git(repository, "remote", "add", remote_name, str(remote))
                        remotes.append(remote)
                    # A forced mapping would overwrite a divergent remote tip.
                    self.fixture_git(repository, "update-ref", "refs/heads/main", base, remote_tip)
                    before = self.fixture_commit(repository, "existing candidate")

                    def remote_refs():
                        return [self.fixture_git(remote, "for-each-ref", "--format=%(refname) %(objectname)").stdout
                                for remote in remotes]

                    def install_conflict():
                        for key, value in configuration:
                            self.fixture_git(repository, "config", "--add", key, value)
                        if name == "N1-namespace":
                            os.environ["GIT_NAMESPACE"] = "fixture-namespace"
                            self.assertEqual("fixture-namespace", self.fixture_environment()["GIT_NAMESPACE"])

                    # origin remains a configured remote with one URL even
                    # when the group of the same name shadows it.
                    self.assertEqual([str(remotes[0])], self.fixture_git(
                        repository, "remote", "get-url", "--push", "--all", "origin").stdout.splitlines())
                    refs_before = remote_refs()
                    commits, pushes = [], []
                    if phase != "pre-push-drift":
                        install_conflict()
                    if phase != "push-only" and self.fixture_direct_gate(self.fixture_configuration_safe(repository)):
                        commits.append(self.fixture_commit(repository, "combined candidate"))
                        if phase == "pre-push-drift":
                            install_conflict()
                    if self.fixture_direct_gate(self.fixture_configuration_safe(repository)):
                        arguments = ("git", "push", "origin", "main")
                        pushes.append(arguments)
                        self.fixture_git(repository, *arguments[1:], check=False)
                    self.assertEqual(1 if phase == "pre-push-drift" else 0, len(commits))
                    self.assertEqual([], pushes)
                    if name == "N1-namespace":
                        self.assertEqual("fixture-namespace", os.environ["GIT_NAMESPACE"])
                    self.assertEqual(refs_before, remote_refs())
                    self.assertEqual(commits[-1] if commits else before,
                                     self.fixture_git(repository, "rev-parse", "HEAD").stdout.strip())

    def test_direct_mapping_first_match_and_clean_exact_command(self):
        clean = (
            (),
            # R2: the final push.recurseSubmodules value wins in this order.
            (("submodule.recurse", "true"), ("push.recurseSubmodules", "no")),
            (("submodule.recurse", "true"), ("push.recurseSubmodules", "check")),
            (("remote.origin.push", "refs/heads/main:refs/heads/main"),),
            (("remote.origin.push", "refs/heads/*:refs/heads/*"),),
            (("remote.origin.push", "refs/heads/other:refs/heads/elsewhere"),
             ("remote.origin.push", "refs/heads/main:refs/heads/main"),
             ("remote.origin.push", "+refs/heads/main:refs/heads/other")),
            (("remote.origin.push", "refs/heads/*:refs/heads/*"),
             ("remote.origin.push", "+refs/heads/main:refs/heads/other")),
            (("push.default", "upstream"), ("branch.main.remote", "origin"),
             ("branch.main.merge", "refs/heads/main")),
            (("remote.origin.push", "refs/heads/topic:refs/heads/unused"),
             ("push.default", "upstream"), ("branch.main.remote", "origin"),
             ("branch.main.merge", "refs/heads/main")),
            (("remote.origin.push", "refs/heads/main:refs/heads/main"),
             ("push.default", "upstream"), ("branch.main.remote", "origin"),
             ("branch.main.merge", "refs/heads/other2")),
        )
        for configuration in clean:
            for combined in (False, True):
                with self.subTest(configuration=configuration, combined=combined), tempfile.TemporaryDirectory(
                        prefix="axiom-direct-clean-mapping-") as temporary:
                    root = Path(temporary)
                    repository = root / "repository"
                    self.initialize_fixture(repository)
                    self.fixture_commit(repository, "base")
                    remote = root / "remote.git"
                    self.fixture_git(repository, "clone", "--bare", "--quiet", str(repository), str(remote))
                    self.fixture_git(repository, "remote", "add", "origin", str(remote))
                    before = self.fixture_commit(repository, "existing candidate")
                    for key, value in configuration:
                        self.fixture_git(repository, "config", "--add", key, value)
                    if combined:
                        self.assertTrue(self.fixture_direct_gate(self.fixture_configuration_safe(repository)))
                        before = self.fixture_commit(repository, "combined candidate")
                    self.assertTrue(self.fixture_direct_gate(self.fixture_configuration_safe(repository)))
                    arguments = ("git", "push", "origin", "main")
                    self.assertTrue(lightweight_push_arguments(arguments, "origin", "main"))
                    self.assertEqual(0, self.fixture_git(repository, *arguments[1:]).returncode)
                    self.assertEqual(f"refs/heads/main {before}\n", self.fixture_git(
                        remote, "for-each-ref", "--format=%(refname) %(objectname)").stdout)
                    self.assertEqual(before, self.fixture_git(repository, "rev-parse", "HEAD").stdout.strip())

    def test_direct_mapping_first_conflict_and_unresolved_evidence_stop(self):
        with tempfile.TemporaryDirectory(prefix="axiom-direct-mapping-") as temporary:
            repository = Path(temporary) / "repository"
            self.initialize_fixture(repository)
            self.fixture_commit(repository, "base")
            conflicts = (
                (("remote.origin.push", "+refs/heads/main:refs/heads/main"),
                 ("remote.origin.push", "refs/heads/main:refs/heads/main")),
                (("remote.origin.push", "refs/heads/*:refs/heads/other/*"),
                 ("remote.origin.push", "refs/heads/main:refs/heads/main")),
                (("remote.origin.push", "refs/heads/topic:refs/heads/unused"),
                 ("remote.origin.push", "refs/heads/main:refs/heads/other")),
                (("remote.origin.push", "refs/heads/main:refs/heads/main"),
                 ("remote.origin.push", "unclassifiable")),
                (("push.default", "upstream"),),
                (("push.default", "upstream"), ("branch.main.remote", "other"),
                 ("branch.main.merge", "refs/heads/main")),
                (("push.default", "upstream"), ("branch.main.remote", "origin"),
                 ("branch.main.merge", "refs/heads/main"), ("branch.main.merge", "refs/heads/other")),
                (("remote.origin.push", "refs/heads/topic:refs/heads/unused"),
                 ("push.default", "upstream"), ("branch.main.remote", "origin"),
                 ("branch.main.merge", "refs/heads/other2")),
                (("push.default", "invalid"),),
                (("remotes.origin", ""),),
            )
            for configuration in conflicts:
                with self.subTest(configuration=configuration):
                    options = tuple(part for key, value in configuration for part in ("-c", f"{key}={value}"))
                    self.assertFalse(self.fixture_direct_gate(self.fixture_configuration_safe(repository, *options)))

    def test_backup_cleanup_recovers_the_delete_before_record_update_window(self):
        with tempfile.TemporaryDirectory(prefix="axiom-backup-cleanup-") as temporary:
            repository = Path(temporary) / "repository"
            self.initialize_fixture(repository)
            old_head = self.fixture_commit(repository, "original history")
            final_head = self.fixture_commit(repository, "consolidated history")
            backup_ref = "refs/axiom/backups/workflow-1"
            self.fixture_git(repository, "update-ref", "--no-deref", backup_ref, old_head, "0" * 40)
            self.assertNotEqual(old_head, final_head)
            self.assertFalse(safe_git_oid(backup_ref, "sha1"))
            self.assertTrue(backup_ref_gate(backup_ref, old_head, "sha1", "non-symbolic", old_head))

            authority = dict.fromkeys(CLEANUP_AUTHORITY_FIELDS, True)
            readiness = {"backupRefDeleted": False}

            def next_step(record):
                symbolic = self.fixture_git(repository, "symbolic-ref", "--quiet", backup_ref, check=False)
                resolved = self.fixture_git(repository, "rev-parse", "--verify", "--quiet", backup_ref, check=False)
                kind = "symbolic" if symbolic.returncode == 0 else (
                    "non-symbolic" if resolved.returncode == 0 else "absent"
                )
                return backup_cleanup_transition(
                    record, authority, backup_ref=backup_ref, old_head=old_head,
                    object_format="sha1", observed_kind=kind,
                    observed_oid=resolved.stdout.strip() if resolved.returncode == 0 else None,
                )

            self.assertEqual("persist-intent", next_step(readiness))
            readiness["backupDeletion"] = {
                "state": "pending", "backupRef": backup_ref, "expectedOid": old_head,
            }
            self.assertEqual("delete-backup", next_step(readiness))
            self.fixture_git(repository, "update-ref", "--no-deref", "-d", backup_ref, old_head)
            # The process ended after ref deletion and before the metadata update.
            self.assertEqual("record-complete", next_step(readiness))
            self.assertEqual("blocked", next_step({"backupRefDeleted": False}))
            wrong_intent = copy.deepcopy(readiness)
            wrong_intent["backupDeletion"]["expectedOid"] = final_head
            self.assertEqual("blocked", next_step(wrong_intent))
            authority["verification_current"] = False
            self.assertEqual("blocked", next_step(readiness))
            authority["verification_current"] = True
            readiness["backupRefDeleted"] = True
            readiness["backupDeletion"]["state"] = "complete"
            self.assertEqual("delete-record", next_step(readiness))
            self.assertEqual(final_head, self.fixture_git(repository, "rev-parse", "HEAD").stdout.strip())

    def test_backup_ref_rejects_symbolic_wrong_namespace_and_changed_oid(self):
        backup_ref = "refs/axiom/backups/workflow-1"
        old_head = "a" * 40
        authority = dict.fromkeys(CLEANUP_AUTHORITY_FIELDS, True)
        readiness = {
            "backupRefDeleted": False,
            "backupDeletion": {"state": "pending", "backupRef": backup_ref, "expectedOid": old_head},
        }
        for ref, kind, oid in (
            (backup_ref, "symbolic", old_head),
            (backup_ref, "uncertain", old_head),
            (backup_ref, "non-symbolic", "b" * 40),
            ("refs/heads/main", "non-symbolic", old_head),
            (old_head, "non-symbolic", old_head),
        ):
            with self.subTest(ref=ref, kind=kind, oid=oid):
                self.assertFalse(backup_ref_gate(ref, old_head, "sha1", kind, oid))
                self.assertEqual("blocked", backup_cleanup_transition(
                    readiness, authority, backup_ref=ref, old_head=old_head,
                    object_format="sha1", observed_kind=kind, observed_oid=oid,
                ))

    def test_each_ordered_target_uses_its_own_live_ancestor_before_any_push(self):
        with tempfile.TemporaryDirectory(prefix="axiom-ordered-baselines-") as temporary:
            root = Path(temporary)
            repository = root / "client"
            self.initialize_fixture(repository)
            first = self.fixture_commit(repository, "A")
            second = self.fixture_commit(repository, "B")
            final = self.fixture_commit(repository, "C")
            remotes = (root / "first.git", root / "second.git")
            for remote, baseline in zip(remotes, (first, second)):
                remote.mkdir()
                self.fixture_git(remote, "init", "--bare", "--quiet")
                self.fixture_git(repository, "push", "--quiet", str(remote), f"{baseline}:refs/heads/main")
            frozen = [
                {"ordinal": ordinal, "fingerprint": f"fixture-{ordinal}",
                 "mergeRef": "refs/heads/main", "liveBaselineSha": baseline}
                for ordinal, baseline in enumerate((first, second), 1)
            ]

            def observations():
                result = []
                for target, remote in zip(frozen, remotes):
                    oid = self.fixture_git(remote, "rev-parse", "refs/heads/main").stdout.strip()
                    result.append({
                        "ordinal": target["ordinal"], "fingerprint": target["fingerprint"],
                        "mergeRef": target["mergeRef"], "oid": oid,
                        "objectType": self.fixture_git(repository, "cat-file", "-t", oid).stdout.strip(),
                        "isAncestor": self.fixture_git(repository, "merge-base", "--is-ancestor", oid, final, check=False).returncode == 0,
                    })
                return result

            def accepted(targets, observed):
                return ordered_push_baselines_gate(
                    targets, observed, final, "sha1",
                    authorization_current=True, operation_state_clear=True,
                )

            self.assertTrue(accepted(frozen, observations()))
            borrowed = copy.deepcopy(frozen)
            borrowed[1]["liveBaselineSha"] = first
            self.assertFalse(accepted(borrowed, observations()))
            self.assertFalse(accepted(frozen, list(reversed(observations()))))
            # An endpoint changed after inventory. The all-target gate prevents
            # even the still-valid first endpoint from being pushed.
            self.fixture_git(repository, "push", "--quiet", str(remotes[1]), f"{final}:refs/heads/main")
            if accepted(frozen, observations()):
                self.fail("target drift must stop before the first push")
            self.assertEqual(first, self.fixture_git(remotes[0], "rev-parse", "refs/heads/main").stdout.strip())
            self.fixture_git(remotes[1], "update-ref", "refs/heads/main", second, final)
            self.assertTrue(accepted(frozen, observations()))
            for remote in remotes:
                self.fixture_git(repository, "push", "--quiet", str(remote), "refs/heads/main:refs/heads/main")
            for remote in remotes:
                self.assertEqual(final, self.fixture_git(remote, "rev-parse", "refs/heads/main").stdout.strip())

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

    def test_all_traceable_git_fixtures(self):
        failures = []
        count = check_traceable_security_contracts(failures)
        self.assertEqual(241, count)
        self.assertEqual([], failures)

    def test_oid_and_literal_operand_gates(self):
        self.assertTrue(safe_git_oid("a" * 40, "sha1"))
        self.assertFalse(safe_git_oid("0" * 40, "sha1"))
        self.assertTrue(safe_git_operand("ref", "refs/heads/main", True))
        self.assertFalse(safe_git_operand("remote", "--upload-pack=evil", True))

    def test_live_fast_forward_gate_ignores_stale_tracking_state(self):
        self.assertTrue(
            direct_push_fast_forward_gate(
                "b" * 40,
                "c" * 40,
                "sha1",
                target_count=1,
                configured_target=True,
                exact_ref=True,
                force_requested=False,
                live_object_type="commit",
                live_is_ancestor=True,
                identity_rechecked=True,
                operation_state_clear=True,
                target_unchanged=True,
                live_oid_unchanged=True,
            )
        )

    def test_live_fast_forward_gate_fails_closed(self):
        accepted = {
            "target_count": 1,
            "configured_target": True,
            "exact_ref": True,
            "force_requested": False,
            "live_object_type": "commit",
            "live_is_ancestor": True,
            "identity_rechecked": True,
            "operation_state_clear": True,
            "target_unchanged": True,
            "live_oid_unchanged": True,
        }
        rejected = (
            ("target_count", 2),
            ("target_count", True),
            ("configured_target", False),
            ("exact_ref", False),
            ("force_requested", True),
            ("live_object_type", "tree"),
            ("live_is_ancestor", False),
            ("identity_rechecked", False),
            ("operation_state_clear", False),
            ("target_unchanged", False),
            ("live_oid_unchanged", False),
        )
        for field, value in rejected:
            with self.subTest(field=field, value=value):
                scenario = dict(accepted)
                scenario[field] = value
                self.assertFalse(
                    direct_push_fast_forward_gate(
                        "b" * 40,
                        "c" * 40,
                        "sha1",
                        **scenario,
                    )
                )
        self.assertFalse(
            direct_push_fast_forward_gate(
                "missing",
                "c" * 40,
                "sha1",
                **accepted,
            )
        )

    def test_lightweight_submit_gates_are_proportional_and_fail_closed(self):
        accepted = {
            "target_count": 1,
            "configured_named_remote": True,
            "exact_branch": True,
            "force_requested": False,
            "widened_refspec": False,
            "fetch_requested": False,
            "retry_requested": False,
            "identity_rechecked": True,
            "operation_state_clear": True,
            "target_unchanged": True,
            "mechanism_conflict": False,
            "effective_configuration_safe": True,
            "configuration_rechecked": True,
        }
        self.assertTrue(lightweight_direct_submit_gate(**accepted))
        for field, value in (
            ("target_count", 2),
            ("target_count", True),
            ("configured_named_remote", False),
            ("exact_branch", False),
            ("force_requested", True),
            ("widened_refspec", True),
            ("fetch_requested", True),
            ("retry_requested", True),
            ("identity_rechecked", False),
            ("operation_state_clear", False),
            ("target_unchanged", False),
            ("mechanism_conflict", True),
            ("effective_configuration_safe", False),
            ("effective_configuration_safe", None),
            ("configuration_rechecked", False),
        ):
            with self.subTest(field=field):
                rejected = dict(accepted)
                rejected[field] = value
                self.assertFalse(lightweight_direct_submit_gate(**rejected))

        self.assertTrue(
            lightweight_push_arguments(
                ("git", "push", "origin", "feature/topic"),
                "origin",
                "feature/topic",
            )
        )
        self.assertFalse(
            lightweight_push_arguments(
                ("git", "push", "--no-verify", "origin", "main"),
                "origin",
                "main",
            )
        )
        self.assertEqual(
            "pass",
            lightweight_push_outcome(
                "success",
                owning_remote_query_count=0,
                queried_tip_matches_final=None,
            ),
        )
        self.assertEqual(
            "pass",
            lightweight_push_outcome(
                "ambiguous",
                owning_remote_query_count=1,
                queried_tip_matches_final=True,
            ),
        )
        self.assertEqual(
            "unknown",
            lightweight_push_outcome(
                "ambiguous",
                owning_remote_query_count=2,
                queried_tip_matches_final=True,
            ),
        )

    def test_expected_staged_payload_is_not_a_manufactured_conflict(self):
        accepted = {
            "authorization_current": True,
            "actor_unchanged": True,
            "repository_unchanged": True,
            "branch_unchanged": True,
            "configured_named_remote": True,
            "target_unchanged": True,
            "command_unchanged": True,
            "staged_payload_matches": True,
            "extra_or_unknown_staged_paths": False,
            "operation_state_clear": True,
            "non_force_policy_unchanged": True,
            "force_requested": False,
            "widened_refspec": False,
            "target_count": 1,
            "instruction_conflict": False,
            "known_divergence": False,
        }
        self.assertTrue(ordinary_combined_commit_push_gate(**accepted))
        for field, value in (
            ("authorization_current", False),
            ("actor_unchanged", False),
            ("repository_unchanged", False),
            ("branch_unchanged", False),
            ("configured_named_remote", False),
            ("target_unchanged", False),
            ("command_unchanged", False),
            ("staged_payload_matches", False),
            ("extra_or_unknown_staged_paths", True),
            ("operation_state_clear", False),
            ("non_force_policy_unchanged", False),
            ("force_requested", True),
            ("widened_refspec", True),
            ("target_count", 2),
            ("target_count", True),
            ("instruction_conflict", True),
            ("known_divergence", True),
        ):
            with self.subTest(field=field):
                rejected = dict(accepted)
                rejected[field] = value
                self.assertFalse(ordinary_combined_commit_push_gate(**rejected))

    def test_precommit_mechanism_conflict_leaves_head_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="axiom-precommit-conflict-") as directory:
            repository = Path(directory) / "repo"
            subprocess.run(
                ("git", "init", "--quiet", "--initial-branch=main", str(repository)),
                check=True,
                timeout=10,
            )
            subprocess.run(("git", "config", "user.name", "fixture"), cwd=repository, check=True)
            subprocess.run(
                ("git", "config", "user.email", "fixture@example.invalid"),
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ("git", "commit", "--quiet", "--allow-empty", "-m", "base"),
                cwd=repository,
                check=True,
            )
            before = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertFalse(
                lightweight_direct_submit_gate(
                    target_count=1,
                    configured_named_remote=True,
                    exact_branch=True,
                    force_requested=False,
                    widened_refspec=False,
                    fetch_requested=False,
                    retry_requested=False,
                    identity_rechecked=True,
                    operation_state_clear=True,
                    target_unchanged=True,
                    mechanism_conflict=True,
                    effective_configuration_safe=True,
                    configuration_rechecked=True,
                )
            )
            after = subprocess.run(
                ("git", "rev-parse", "HEAD"),
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(before, after)

    def test_stale_tracking_ref_does_not_block_native_non_force_push(self):
        environment = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
        }

        def run(*arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ("git", *arguments),
                cwd=cwd,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

        with tempfile.TemporaryDirectory(prefix="axiom-stale-tracking-") as directory:
            root = Path(directory)
            remote = root / "remote.git"
            client = root / "client"
            run("init", "--bare", "--quiet", str(remote))
            run("init", "--quiet", "--initial-branch=main", str(client))
            run("config", "user.name", "fixture", cwd=client)
            run("config", "user.email", "fixture@example.invalid", cwd=client)
            run("remote", "add", "origin", str(remote), cwd=client)
            run("config", "branch.main.remote", "origin", cwd=client)
            run("config", "branch.main.merge", "refs/heads/main", cwd=client)

            hook_marker = root / "pre-push-ran"
            hook = client / ".git" / "hooks" / "pre-push"
            hook.write_text(
                f"#!/bin/sh\n: > {hook_marker}\n",
                encoding="ascii",
            )
            hook.chmod(0o755)

            run("commit", "--quiet", "--allow-empty", "-m", "A", cwd=client)
            tracking_a = run("rev-parse", "HEAD", cwd=client).stdout.strip()
            run("commit", "--quiet", "--allow-empty", "-m", "B", cwd=client)
            live_b = run("rev-parse", "HEAD", cwd=client).stdout.strip()
            run("push", "--quiet", "origin", f"{live_b}:refs/heads/main", cwd=client)
            run(
                "update-ref",
                "--no-deref",
                "refs/remotes/origin/main",
                tracking_a,
                cwd=client,
            )
            run("commit", "--quiet", "--allow-empty", "-m", "C", cwd=client)
            final_c = run("rev-parse", "HEAD", cwd=client).stdout.strip()

            self.assertNotEqual(tracking_a, live_b)
            self.assertEqual(
                tracking_a,
                run("rev-parse", "refs/remotes/origin/main", cwd=client).stdout.strip(),
            )
            final_push = ("push", "origin", "main")
            hook_marker.unlink()
            self.assertTrue(self.fixture_direct_gate(self.fixture_configuration_safe(client)))
            self.assertTrue(
                lightweight_push_arguments(
                    ("git", *final_push), "origin", "main"
                )
            )
            run(*final_push, cwd=client)
            self.assertEqual(
                final_c,
                run("--git-dir", str(remote), "rev-parse", "refs/heads/main").stdout.strip(),
            )
            self.assertEqual(
                final_c,
                run("rev-parse", "refs/remotes/origin/main", cwd=client).stdout.strip(),
            )
            self.assertTrue(hook_marker.is_file())
            self.assertEqual(
                "pass",
                lightweight_push_outcome(
                    "success",
                    owning_remote_query_count=0,
                    queried_tip_matches_final=None,
                ),
            )

    def test_native_non_force_divergence_is_rejected_without_head_change(self):
        environment = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }

        def run(*arguments: str, cwd: Path | None = None, check: bool = True):
            return subprocess.run(
                ("git", *arguments),
                cwd=cwd,
                env=environment,
                check=check,
                capture_output=True,
                text=True,
                timeout=10,
            )

        with tempfile.TemporaryDirectory(prefix="axiom-divergent-push-") as directory:
            root = Path(directory)
            remote = root / "remote.git"
            client = root / "client"
            peer = root / "peer"
            run("init", "--bare", "--quiet", str(remote))
            run("init", "--quiet", "--initial-branch=main", str(client))
            for repository in (client,):
                run("config", "user.name", "fixture", cwd=repository)
                run("config", "user.email", "fixture@example.invalid", cwd=repository)
            run("remote", "add", "origin", str(remote), cwd=client)
            run("commit", "--quiet", "--allow-empty", "-m", "A", cwd=client)
            run("push", "--quiet", "-u", "origin", "main", cwd=client)
            run(
                "--git-dir",
                str(remote),
                "symbolic-ref",
                "HEAD",
                "refs/heads/main",
            )
            run("clone", "--quiet", str(remote), str(peer))
            run("config", "user.name", "fixture", cwd=peer)
            run("config", "user.email", "fixture@example.invalid", cwd=peer)
            run("commit", "--quiet", "--allow-empty", "-m", "remote-B", cwd=peer)
            run("push", "--quiet", "origin", "main", cwd=peer)
            run("commit", "--quiet", "--allow-empty", "-m", "local-C", cwd=client)
            before = run("rev-parse", "HEAD", cwd=client).stdout.strip()
            rejected = run("push", "origin", "main", cwd=client, check=False)
            self.assertNotEqual(0, rejected.returncode)
            self.assertEqual(before, run("rev-parse", "HEAD", cwd=client).stdout.strip())
            self.assertEqual(
                "fail",
                lightweight_push_outcome(
                    "rejected",
                    owning_remote_query_count=0,
                    queried_tip_matches_final=None,
                ),
            )


if __name__ == "__main__":
    unittest.main()
