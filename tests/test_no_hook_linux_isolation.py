"""Focused tests for the Linux no-Hook process-domain supervisor."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from axiom_validation import no_hook_linux_isolation as isolation
from axiom_validation.context import REPOSITORY_ROOT


class ProcessDomainContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.executable = Path(sys.executable).resolve(strict=True)
        self.executable_fd = os.open(
            self.executable,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        self.cwd_fd = os.open(
            REPOSITORY_ROOT,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )

    def tearDown(self) -> None:
        os.close(self.cwd_fd)
        os.close(self.executable_fd)

    def launch(
        self,
        supervisor: isolation.DeterministicProcessDomainSupervisor,
        script: str = "pass",
        *,
        arguments: tuple[str, ...] = (),
        pass_fds: tuple[int, ...] = (),
        popen_factory=subprocess.Popen,
    ) -> isolation.DomainProcess:
        return supervisor.launch(
            purpose="model-case",
            executable_fd=self.executable_fd,
            argv=(str(self.executable), "-I", "-B", "-c", script, *arguments),
            cwd_fd=self.cwd_fd,
            env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "NO_COLOR": "1"},
            pass_fds=pass_fds,
            popen_factory=popen_factory,
        )

    @staticmethod
    def close_process(process: isolation.DomainProcess) -> None:
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except (OSError, ValueError):
                pass

    def test_capability_facts_are_closed_and_unavailable_hosts_fail_closed(self) -> None:
        expected = {
            "platformSupported",
            "cgroupV2Available",
            "delegatedSubtreeWritable",
            "cloneIntoCgroupAvailable",
            "clonePidfdAvailable",
            "cgroupKillAvailable",
            "cgroupEventsAvailable",
            "childSubreaperAvailable",
            "pidfdWaitAvailable",
        }
        facts = isolation.detect_process_domain_capabilities().normalized()
        self.assertEqual(expected, set(facts))
        self.assertTrue(all(type(value) is bool for value in facts.values()))
        with mock.patch.object(isolation.platform, "system", return_value="Darwin"):
            unsupported = isolation.detect_process_domain_capabilities()
        self.assertFalse(unsupported.available)
        self.assertFalse(unsupported.platform_supported)
        self.assertNotIn("/", repr(unsupported.normalized()))

    def test_deterministic_prelaunch_failures_have_owned_diagnostics(self) -> None:
        scenarios = {
            "capability-unavailable": "process-domain-capability-unavailable",
            "domain-create": "process-domain-create-failed",
            "preexisting-domain": "process-domain-preexisting",
            "already-populated": "process-domain-already-populated",
            "clone-into-cgroup": "clone-into-cgroup-unavailable",
            "clone-pidfd": "clone-pidfd-unavailable",
            "clone3": "clone3-atomic-enrollment-failed",
            "pidfd": "pidfd-ownership-unavailable",
        }
        for phase, diagnostic in scenarios.items():
            supervisor = isolation.DeterministicProcessDomainSupervisor(
                failure_phase=phase
            )
            with self.subTest(phase=phase), self.assertRaisesRegex(
                isolation.ProcessDomainError, f"^{diagnostic}$"
            ):
                self.launch(supervisor)
            self.assertEqual(1, supervisor.launch_attempts)
            self.assertEqual(0, supervisor.normalized_summary()["domainCount"])
            supervisor.require_advance_barrier()
            supervisor.close()

    def test_atomic_enrollment_precedes_process_factory(self) -> None:
        supervisor = isolation.DeterministicProcessDomainSupervisor()
        observed: list[tuple[str, ...]] = []

        def factory(*args, **kwargs):
            observed.append(tuple(supervisor.events))
            return subprocess.Popen(*args, **kwargs)

        process = self.launch(supervisor, popen_factory=factory)
        try:
            process.stdin.close()
            self.assertEqual(0, process.wait(timeout=5))
            process.complete(terminate=False)
            supervisor.require_advance_barrier()
            supervisor.close()
        finally:
            self.close_process(process)
        self.assertEqual(
            ("domain-create:1:model-case", "atomic-enrollment:1:model-case"),
            observed[0],
        )
        self.assertNotIn("cgroup.procs", " ".join(supervisor.events))

    def test_active_domain_blocks_advance_until_empty_and_removed(self) -> None:
        supervisor = isolation.DeterministicProcessDomainSupervisor()
        process = self.launch(supervisor)
        try:
            with self.assertRaisesRegex(
                isolation.ProcessDomainError,
                "^process-domain-empty-proof-required$",
            ):
                supervisor.require_advance_barrier()
            process.stdin.close()
            self.assertEqual(0, process.wait(timeout=5))
            outcome = process.complete(terminate=False)
            self.assertTrue(outcome.domain_empty_verified)
            self.assertTrue(outcome.descendant_reaping_verified)
            self.assertTrue(outcome.domain_removal_verified)
            supervisor.require_advance_barrier()
            supervisor.close()
        finally:
            self.close_process(process)

    def test_terminal_backend_failures_block_cleanup_and_publication(self) -> None:
        scenarios = {
            "pidfd-wait": "pidfd-wait-failed",
            "events-read": "cgroup-events-read-failed",
            "events-malformed": "cgroup-events-malformed",
            "populated-timeout": "process-domain-populated-timeout",
            "descendant-reap": "process-domain-descendant-reap-failed",
            "ownership-drift": "process-domain-removal-identity-drift",
            "domain-remove": "process-domain-removal-failed",
        }
        for phase, diagnostic in scenarios.items():
            supervisor = isolation.DeterministicProcessDomainSupervisor(
                failure_phase=phase
            )
            process = self.launch(supervisor)
            try:
                process.stdin.close()
                self.assertEqual(0, process.wait(timeout=5))
                with self.subTest(phase=phase), self.assertRaisesRegex(
                    isolation.ProcessDomainError, f"^{diagnostic}$"
                ):
                    process.complete(terminate=False)
                with self.assertRaises(isolation.ProcessDomainError):
                    supervisor.require_advance_barrier()
                summary = supervisor.normalized_summary()
                self.assertTrue(summary["manualCleanupRequired"])
                self.assertEqual(1, summary["residualDomainCount"])
            finally:
                self.close_process(process)

    def test_bootstrap_and_exec_failures_are_cleaned_after_atomic_enrollment(self) -> None:
        for phase, diagnostic in (
            ("bootstrap", "child-bootstrap-failed"),
            ("exec", "child-exec-failed"),
        ):
            supervisor = isolation.DeterministicProcessDomainSupervisor(
                failure_phase=phase
            )
            with self.subTest(phase=phase), self.assertRaisesRegex(
                isolation.ProcessDomainError, f"^{diagnostic}$"
            ):
                self.launch(supervisor)
            self.assertEqual(
                [
                    "domain-create:1:model-case",
                    "atomic-enrollment:1:model-case",
                    "domain-kill:1:model-case",
                    "domain-empty:1:model-case",
                    "descendants-reaped:1:model-case",
                    "domain-removed:1:model-case",
                ],
                supervisor.events,
            )
            summary = supervisor.normalized_summary()
            self.assertEqual(1, summary["domainCount"])
            self.assertEqual(1, summary["completeDomainTerminationVerifiedCount"])
            self.assertEqual(0, summary["residualDomainCount"])
            self.assertFalse(summary["manualCleanupRequired"])
            supervisor.require_advance_barrier()
            supervisor.close()

    def test_descendant_matrix_requires_complete_domain_barrier(self) -> None:
        scenarios = (
            "leader-with-grandchild",
            "leader-exits-before-grandchild",
            "grandchild-setsid",
            "grandchild-changes-process-group",
            "leader-terminated-with-descendant",
            "leader-success-with-descendant",
            "timeout-with-descendant",
            "hard-stop-with-descendant",
            "descendant-ignores-sigterm",
            "descendant-closes-nonessential-fds",
            "descendant-attempts-to-outlive-case",
            "descendant-retains-protected-descriptor",
        )
        for scenario in scenarios:
            supervisor = isolation.DeterministicProcessDomainSupervisor(
                failure_phase="descendant-active"
            )
            process = self.launch(supervisor)
            try:
                process.stdin.close()
                self.assertEqual(0, process.wait(timeout=5))
                with self.subTest(scenario=scenario), self.assertRaisesRegex(
                    isolation.ProcessDomainError,
                    "^process-domain-empty-proof-required$",
                ):
                    supervisor.require_advance_barrier()
                with self.assertRaisesRegex(
                    isolation.ProcessDomainError,
                    "^previous-process-domain-not-empty$",
                ):
                    self.launch(supervisor)
                outcome = process.complete(terminate=False)
                self.assertTrue(outcome.termination_required)
                self.assertTrue(outcome.complete_domain_termination_verified)
                self.assertTrue(outcome.domain_empty_verified)
                self.assertTrue(outcome.descendant_reaping_verified)
                self.assertTrue(outcome.domain_removal_verified)
                self.assertIn("domain-kill:1:model-case", supervisor.events)
                supervisor.require_advance_barrier()
                supervisor.close()
            finally:
                self.close_process(process)

    def test_passed_descriptor_is_explicit_and_nonessential_descriptors_close(self) -> None:
        retained_read, retained_write = os.pipe2(os.O_CLOEXEC)
        supervisor = isolation.DeterministicProcessDomainSupervisor(
            failure_phase="descendant-active"
        )
        process = self.launch(
            supervisor,
            "import os,sys; fd=int(sys.argv[1]); duplicate=os.dup(fd); "
            "os.close(fd); os.fstat(duplicate)",
            arguments=(str(retained_read),),
            pass_fds=(retained_read,),
        )
        try:
            process.stdin.close()
            self.assertEqual(0, process.wait(timeout=5))
            outcome = process.complete(terminate=False)
            self.assertTrue(outcome.complete_domain_termination_verified)
            supervisor.require_advance_barrier()
            supervisor.close()
        finally:
            self.close_process(process)
            os.close(retained_write)
            os.close(retained_read)

    def test_domain_indices_are_fresh_and_previous_removal_precedes_next_launch(self) -> None:
        supervisor = isolation.DeterministicProcessDomainSupervisor()
        processes: list[isolation.DomainProcess] = []
        try:
            for index in range(1, 4):
                process = self.launch(supervisor)
                processes.append(process)
                process.stdin.close()
                self.assertEqual(0, process.wait(timeout=5))
                process.complete(terminate=False)
                supervisor.require_advance_barrier()
                self.assertEqual(
                    f"domain-removed:{index}:model-case",
                    supervisor.events[-1],
                )
            supervisor.close()
        finally:
            for process in processes:
                self.close_process(process)
        creates = [item for item in supervisor.events if item.startswith("domain-create:")]
        self.assertEqual(
            [
                "domain-create:1:model-case",
                "domain-create:2:model-case",
                "domain-create:3:model-case",
            ],
            creates,
        )

    def test_complete_domain_kill_failure_is_fail_closed(self) -> None:
        supervisor = isolation.DeterministicProcessDomainSupervisor(
            failure_phase="kill"
        )
        process = self.launch(supervisor, "import sys; sys.stdin.buffer.read(1)")
        try:
            with self.assertRaisesRegex(
                isolation.ProcessDomainError, "^cgroup-kill-failed$"
            ):
                process.complete(terminate=True)
            self.assertIsNotNone(process.poll())
            with self.assertRaises(isolation.ProcessDomainError):
                supervisor.require_advance_barrier()
        finally:
            self.close_process(process)

    def test_domain_ownership_does_not_use_pid_or_process_group(self) -> None:
        source = Path(isolation.__file__).read_text(encoding="utf-8")
        self.assertIn("CLONE_INTO_CGROUP | CLONE_PIDFD", source)
        self.assertIn("os.P_PIDFD", source)
        self.assertIn('os.write(process.kill_fd, b"1")', source)
        self.assertIn("cgroup.events", source)
        self.assertNotIn("preexec_fn", source)
        self.assertNotIn("start_new_session", source)
        self.assertNotIn("os.killpg", source)
        self.assertNotIn("signal.pidfd_send_signal", source)
        self.assertNotIn("os.write(procs_fd", source)

    def test_complete_one_domain_does_not_affect_unrelated_process(self) -> None:
        unrelated = subprocess.Popen(
            [sys.executable, "-I", "-B", "-c", "import sys;sys.stdin.read(1)"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        supervisor = isolation.DeterministicProcessDomainSupervisor()
        process = self.launch(supervisor)
        try:
            process.stdin.close()
            self.assertEqual(0, process.wait(timeout=5))
            process.complete(terminate=False)
            self.assertIsNone(unrelated.poll())
            supervisor.require_advance_barrier()
            supervisor.close()
        finally:
            self.close_process(process)
            if unrelated.stdin is not None:
                unrelated.stdin.write(b"x")
                unrelated.stdin.close()
            unrelated.wait(timeout=5)

    def test_events_parser_rejects_malformed_or_ambiguous_payloads(self) -> None:
        self.assertFalse(isolation._parse_cgroup_events(b"populated 0\nfrozen 0\n"))
        self.assertTrue(isolation._parse_cgroup_events(b"populated 1\nfrozen 0\n"))
        for payload in (
            b"",
            b"populated\n",
            b"populated 2\n",
            b"populated 0\npopulated 1\n",
            b"populated 0 extra\n",
            b"populated \xff\n",
        ):
            with self.subTest(payload=payload), self.assertRaisesRegex(
                isolation.ProcessDomainError, "^cgroup-events-malformed$"
            ):
                isolation._parse_cgroup_events(payload)

    def test_closed_summary_contains_no_host_identifiers(self) -> None:
        supervisor = isolation.DeterministicProcessDomainSupervisor()
        process = self.launch(supervisor)
        try:
            process.stdin.close()
            process.wait(timeout=5)
            process.complete(terminate=False)
            summary = supervisor.normalized_summary()
            self.assertEqual(
                {
                    "mechanism",
                    "availability",
                    "domainCount",
                    "builderDomainCount",
                    "marketplaceDomainCount",
                    "pluginInstallDomainCount",
                    "modelDomainCount",
                    "atomicEnrollmentVerifiedCount",
                    "directChildPidfdVerifiedCount",
                    "terminationRequiredCount",
                    "completeDomainTerminationVerifiedCount",
                    "domainEmptyVerifiedCount",
                    "descendantReapingVerifiedCount",
                    "domainRemovalVerifiedCount",
                    "residualDomainCount",
                    "manualCleanupRequired",
                },
                set(summary),
            )
            serialized = repr(summary).lower()
            for forbidden in ("pid", "/sys/", "/proc/", "inode", "username"):
                if forbidden == "pid":
                    self.assertNotIn("pidfd", serialized.replace("directchildpidfd", ""))
                else:
                    self.assertNotIn(forbidden, serialized)
            supervisor.close()
        finally:
            self.close_process(process)


@unittest.skipUnless(
    os.environ.get("AXIOM_RUN_CURRENT_HOST_CGROUP_PROBE") == "1",
    "explicit current-host delegated-cgroup probe only",
)
class CurrentHostProcessDomainProbeTests(unittest.TestCase):
    def test_leader_exit_setsid_descendant_is_killed_reaped_and_removed(self) -> None:
        facts = isolation.detect_process_domain_capabilities()
        self.assertTrue(facts.available)
        result = isolation.run_current_host_synthetic_probe(cwd=REPOSITORY_ROOT)
        self.assertEqual(
            {
                "leaderExited": True,
                "setsidDescendantObserved": True,
                "retainedDescriptorDescendantObserved": True,
                "completeDomainTerminationVerified": True,
                "domainEmptyVerified": True,
                "descendantReapingVerified": True,
                "domainRemovalVerified": True,
            },
            result,
        )


if __name__ == "__main__":
    unittest.main()
