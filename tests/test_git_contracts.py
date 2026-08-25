"""Focused tests for traceable-Git safety gates and fixtures."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from axiom_validation.git_contracts import (
    direct_push_fast_forward_gate,
    safe_git_oid,
    safe_git_operand,
)
from tests.fixtures.git_contracts import check_traceable_security_contracts


class GitContractTests(unittest.TestCase):
    def test_all_traceable_git_fixtures(self):
        failures = []
        count = check_traceable_security_contracts(failures)
        self.assertEqual(65, count)
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
            live_query = run(
                "ls-remote", "--refs", "origin", "refs/heads/main", cwd=client
            ).stdout.splitlines()
            self.assertEqual(1, len(live_query))
            queried_b, queried_ref = live_query[0].split("\t", 1)

            self.assertNotEqual(tracking_a, live_b)
            self.assertEqual(live_b, queried_b)
            self.assertEqual("refs/heads/main", queried_ref)
            self.assertEqual(
                tracking_a,
                run("rev-parse", "refs/remotes/origin/main", cwd=client).stdout.strip(),
            )
            run("merge-base", "--is-ancestor", queried_b, final_c, cwd=client)
            self.assertTrue(
                direct_push_fast_forward_gate(
                    queried_b,
                    final_c,
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
            immediate_query = run(
                "ls-remote", "--refs", "origin", "refs/heads/main", cwd=client
            ).stdout.splitlines()
            self.assertEqual(live_query, immediate_query)

            run(
                "push",
                "--quiet",
                "--no-force",
                "origin",
                "refs/heads/main:refs/heads/main",
                cwd=client,
            )
            self.assertEqual(
                final_c,
                run("--git-dir", str(remote), "rev-parse", "refs/heads/main").stdout.strip(),
            )


if __name__ == "__main__":
    unittest.main()
