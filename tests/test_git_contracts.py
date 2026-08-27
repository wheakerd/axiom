"""Focused tests for traceable-Git safety gates and fixtures."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from axiom_validation.git_contracts import (
    direct_push_fast_forward_gate,
    lightweight_direct_submit_gate,
    lightweight_push_arguments,
    lightweight_push_outcome,
    ordinary_combined_commit_push_gate,
    safe_git_oid,
    safe_git_operand,
)
from tests.fixtures.git_contracts import check_traceable_security_contracts


class GitContractTests(unittest.TestCase):
    def test_all_traceable_git_fixtures(self):
        failures = []
        count = check_traceable_security_contracts(failures)
        self.assertEqual(238, count)
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
