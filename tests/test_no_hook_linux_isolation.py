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


class CombinedLifecycleTests(unittest.TestCase):
    """Pure event contracts: no subprocess, detector, or kernel backend."""

    def test_pending_consumer_view_cannot_close_or_resume(self):
        scope = isolation._CombinedLifecycle("installed-case")
        self.ready_scope(scope)
        with self.assertRaises(isolation.ProcessDomainError):
            scope.control_closed("installed-view")
        self.assertEqual("incomplete", scope.phase)
        with self.assertRaises(isolation.ProcessDomainError):
            scope.consume()
        with self.assertRaises(isolation.ProcessDomainError):
            scope.complete()

    def test_scope_construction_failure_irreversibly_stops_run(self):
        run = isolation._CombinedLifecycleRun(simulated=True)
        completed = run.begin("bundle")
        self.complete_scope(completed)
        for name in ("process-controller", "root-session", "owned-root", "source-bundle"):
            run.register_control(name)
        previous = completed.normalized_record()
        with self.assertRaisesRegex(isolation.ProcessDomainError, "combined-scope-writers-invalid"):
            run.begin("installed-case", bundle_writer=True)
        self.assertEqual([completed], run.scopes)
        self.assertEqual("complete", completed.phase)
        self.assertEqual(1, run.normalized_summary()["startedScopeCount"])
        self.assertEqual("incomplete", run.normalized_summary()["runState"])
        self.assertEqual(previous, completed.normalized_record())
        with self.assertRaises(isolation.ProcessDomainError):
            run.begin("installed-case")
        for name in tuple(run._controls):
            run.control_closed(name)
        run.finish()
        self.assertEqual("incomplete", run.normalized_summary()["contractStatus"])
        self.assertEqual(0, run.normalized_summary()["unresolvedCreatedResourceCount"])
        self.assertEqual("complete", self.complete_run().normalized_summary()["contractStatus"])

    def prepare_scope(self, scope):
        # Finite adapter events, independent of the producer's inventory totals.
        scope.prepared()
        if scope.kind != "bundle":
            for role in ("case-root", "workspace", "model-home", "home", "xdg-config", "xdg-cache", "xdg-data"):
                scope.register_control(role, role=role)
        if scope.kind == "installed-case":
            scope.register_control("marketplace-view", role="marketplace-view")
            writers = ("marketplace", "plugin-install")
        elif scope.kind == "bundle" and scope.expected_writers:
            for role in ("destination", "builder-handles"):
                scope.register_control(role, role=role)
            writers = ("bundle-builder",)
        else:
            writers = ()
        for purpose in writers:
            scope.workload_started(purpose, purpose)
            if purpose != "bundle-builder":
                scope.register_control(f"{purpose}-streams", role=f"{purpose}-streams")
            scope.workload_closed(purpose)
            scope.require_writer_closed(purpose)
            if purpose != "bundle-builder":
                scope.control_closed(f"{purpose}-streams")
        if scope.kind == "installed-case":
            scope.register_control("installed-view", role="installed-view", binding=("accepted-object", 1))

    def seal_scope(self, scope):
        self.prepare_scope(scope)
        scope.writers_closed()
        binding = None if scope.kind == "no-plugin-case" else ("accepted-object", 1)
        control = "installed-view" if scope.kind == "installed-case" else "model-home" if scope.kind == "no-plugin-case" else None
        scope.accept_view(binding, binding, control=control)
        scope.seal_view()
        if scope.kind != "bundle":
            scope.register_control("schema", role="schema")
        return binding

    def ready_scope(self, scope):
        binding = self.seal_scope(scope)
        scope.contract_preconditions(
            view_binding=binding, descriptor_policy="exact-required-pass-fds"
        )

    def complete_scope(self, scope):
        self.ready_scope(scope)
        scope.consume()
        if scope.kind != "bundle":
            scope.workload_started("model-case", "consumer")
            scope.register_control("model-streams", role="model-streams")
            scope.workload_closed("consumer")
        scope.consumers_closed()
        for token, closed in tuple(scope._controls.items()):
            if not closed:
                scope.control_closed(token)
        scope.resources_closed()
        scope.complete()

    def complete_run(self, *, builder=False):
        run = isolation._CombinedLifecycleRun(simulated=True)
        bundle = run.begin("bundle", bundle_writer=builder)
        self.complete_scope(bundle)
        for name in ("process-controller", "root-session", "owned-root", "source-bundle"):
            run.register_control(name)
        for index in range(1, 17):
            self.complete_scope(run.begin("no-plugin-case" if index == 11 else "installed-case"))
        for name in tuple(run._controls):
            run.control_closed(name)
        run.finish()
        return run

    def test_supervisor_lifecycle_ordering_and_bounded_control_inventory(self):
        run = self.complete_run(builder=True)
        facts = run.normalized_summary()
        self.assertEqual("complete", facts["contractStatus"])
        self.assertEqual("complete", facts["simulationStatus"])
        self.assertEqual(31, facts["writerClosedCount"])
        self.assertEqual(16, facts["consumerClosedCount"])
        self.assertEqual(210, facts["controlClosedCount"])
        self.assertEqual(0, facts["unresolvedCreatedResourceCount"])
        self.assertEqual(0, facts["supervisorProcess"]["startedCount"])
        self.assertFalse(facts["actualExecutionEligible"])
        self.assertEqual({"not-verified"}, set(facts["runtimeFacts"].values()))

    def test_missing_phase_preconditions_are_irreversible(self):
        transitions = (
            lambda s: s.writers_closed(), lambda s: s.accept_view((1,), (1,)),
            lambda s: s.seal_view(),
            lambda s: s.contract_preconditions(view_binding=(1,), descriptor_policy="exact-required-pass-fds"),
            lambda s: s.consume(), lambda s: s.consumers_closed(),
            lambda s: s.resources_closed(), lambda s: s.complete(),
        )
        for transition in transitions:
            scope = isolation._CombinedLifecycle("installed-case")
            with self.subTest(transition=transition), self.assertRaises(isolation.ProcessDomainError):
                transition(scope)
            with self.assertRaises(isolation.ProcessDomainError):
                scope.prepared()
            self.assertEqual("incomplete", scope.phase)

    def test_writer_closure_precedes_acceptance_sealing_and_cleanup(self):
        for action in (
            lambda s: s.writers_closed(), lambda s: s.accept_view((1,), (1,)),
            lambda s: s.seal_view(), lambda s: s.control_closed("product"),
        ):
            scope = isolation._CombinedLifecycle("installed-case")
            scope.prepared()
            scope.register_control("product", role="marketplace-view")
            for role in ("case-root", "workspace", "model-home", "home", "xdg-config", "xdg-cache", "xdg-data"):
                scope.register_control(role, role=role)
            scope.workload_started("marketplace", "writer")
            with self.assertRaises(isolation.ProcessDomainError):
                action(scope)
            scope.workload_closed("writer")
            self.assertEqual("incomplete", scope.phase)

    def test_installed_view_binding_and_case_eleven_are_independent(self):
        scope = isolation._CombinedLifecycle("bundle")
        scope.prepared(); scope.writers_closed()
        with self.assertRaises(isolation.ProcessDomainError):
            scope.accept_view(("accepted",), ("different",))
        control = isolation._CombinedLifecycle("no-plugin-case")
        control.prepared()
        with self.assertRaises(isolation.ProcessDomainError):
            control.require_launch("plugin-install")
        control = isolation._CombinedLifecycle("no-plugin-case")
        control.prepared(); control.writers_closed()
        with self.assertRaises(isolation.ProcessDomainError):
            control.accept_view(("installed",), ("installed",))

    def test_consumer_closure_precedes_view_release(self):
        scope = isolation._CombinedLifecycle("no-plugin-case")
        self.ready_scope(scope)
        scope.consume()
        scope.workload_started("model-case", "consumer")
        with self.assertRaises(isolation.ProcessDomainError):
            scope.require_control_close("model-home")
        scope.workload_closed("consumer"); scope.control_closed("model-home")
        self.assertEqual("incomplete", scope.phase)

    def test_local_success_unknown_completion_and_uncreated_resources(self):
        run = isolation._CombinedLifecycleRun()
        bundle = run.begin("bundle")
        self.complete_scope(bundle)
        for name in ("process-controller", "root-session", "owned-root", "source-bundle"):
            run.register_control(name)
        run.abort()
        for name in tuple(run._controls):
            run.control_closed(name)
        run.finish()
        self.assertEqual("incomplete", run.normalized_summary()["contractStatus"])
        self.assertEqual(0, run.normalized_summary()["unresolvedCreatedResourceCount"])
        self.assertEqual("not-run", run.normalized_summary()["simulationStatus"])
        with self.assertRaises(isolation.ProcessDomainError):
            run.control_closed("unknown")
        run.finish()
        self.assertEqual("incomplete", run.normalized_summary()["contractStatus"])

    def test_missing_control_inventory_cannot_complete_a_scope(self):
        scope = isolation._CombinedLifecycle("no-plugin-case")
        self.ready_scope(scope)
        scope.consume(); scope.workload_started("model-case", "consumer")
        scope.workload_closed("consumer"); scope.consumers_closed()
        with self.assertRaises(isolation.ProcessDomainError):
            scope.resources_closed()

    def test_contradictory_preconditions_and_duplicate_completions_stay_incomplete(self):
        for binding, policy in ((("wrong",), "exact-required-pass-fds"), (None, "unknown")):
            scope = isolation._CombinedLifecycle("no-plugin-case")
            self.seal_scope(scope)
            with self.assertRaises(isolation.ProcessDomainError):
                scope.contract_preconditions(view_binding=binding, descriptor_policy=policy)
            with self.assertRaises(isolation.ProcessDomainError):
                scope.contract_preconditions(view_binding=None, descriptor_policy="exact-required-pass-fds")
        scope = isolation._CombinedLifecycle("installed-case")
        scope.prepared()
        for role in ("case-root", "workspace", "model-home", "home", "xdg-config", "xdg-cache", "xdg-data", "marketplace-view"):
            scope.register_control(role, role=role)
        scope.workload_started("marketplace", "writer")
        scope.workload_closed("writer")
        with self.assertRaises(isolation.ProcessDomainError):
            scope.workload_closed("writer")
        self.assertEqual("incomplete", scope.phase)

    def test_simulation_has_no_launch_authority_and_enforces_finite_inventory(self):
        scope = isolation._CombinedLifecycle("bundle", bundle_writer=True)
        for role in ("destination", "builder-handles"):
            scope.register_control(role, role=role)
        with self.assertRaises(isolation.ProcessDomainError):
            scope.register_control(object(), role="unowned-extra-control")
        run = isolation._CombinedLifecycleRun(simulated=True)
        with self.assertRaises(isolation.ProcessDomainError):
            run.begin("installed-case")
        self.assertFalse(run.normalized_summary()["actualExecutionEligible"])
        self.assertEqual(0, run.normalized_summary()["supervisorProcess"]["startedCount"])

    def test_view_control_is_checked_at_acceptance_sealing_and_consumption(self):
        for stage in ("accept", "seal", "consume"):
            for inconsistency in ("missing", "closed", "foreign-binding"):
                with self.subTest(stage=stage, inconsistency=inconsistency):
                    scope = isolation._CombinedLifecycle("installed-case")
                    self.prepare_scope(scope)
                    scope.writers_closed()
                    if stage != "accept":
                        scope.accept_view(("accepted-object", 1), ("accepted-object", 1), control="installed-view")
                    if stage == "consume":
                        scope.seal_view()
                        scope.register_control("schema", role="schema")
                        scope.contract_preconditions(view_binding=("accepted-object", 1), descriptor_policy="exact-required-pass-fds")
                    # A contradictory owner record must fail even at a valid phase.
                    if inconsistency == "missing":
                        scope._controls.pop("installed-view")
                    elif inconsistency == "closed":
                        scope._controls["installed-view"] = True
                    else:
                        scope._control_bindings["installed-view"] = ("another-scope",)
                    with self.assertRaisesRegex(isolation.ProcessDomainError, "combined-consumption-control-invalid"):
                        if stage == "accept":
                            scope.accept_view(("accepted-object", 1), ("accepted-object", 1), control="installed-view")
                        elif stage == "seal":
                            scope.seal_view()
                        else:
                            scope.consume()
                    self.assertEqual("incomplete", scope.phase)

    def test_case_eleven_pending_consumer_and_failure_cleanup_are_independent(self):
        run = isolation._CombinedLifecycleRun(simulated=True)
        bundle = run.begin("bundle")
        self.complete_scope(bundle)
        for role in ("process-controller", "root-session", "owned-root", "source-bundle"):
            run.register_control(role)
        for _ in range(10):
            self.complete_scope(run.begin("installed-case"))
        scope = run.begin("no-plugin-case")
        self.ready_scope(scope)
        self.assertEqual("not-started", scope.normalized_record()["consumer"])
        self.assertEqual({"not-required"}, set(scope.normalized_record()["writers"].values()))
        with self.assertRaisesRegex(isolation.ProcessDomainError, "pending"):
            scope.control_closed("model-home")
        run.abort()
        for token, closed in tuple(scope._controls.items()):
            if not closed:
                scope.control_closed(token)
        for role in tuple(run._controls):
            run.control_closed(role)
        with self.assertRaises(isolation.ProcessDomainError):
            scope.consume()
        run.finish()
        facts = run.normalized_summary()
        self.assertEqual((12, 11, 20, 10, 0), tuple(facts[key] for key in (
            "startedScopeCount", "completedScopeCount", "writerStartedCount", "consumerStartedCount", "unresolvedCreatedResourceCount"
        )))
        self.assertEqual("incomplete", facts["contractStatus"])

    def test_normal_consumer_closure_and_consumerless_bundle_scopes_complete(self):
        for kind, builder, controls in (("bundle", False, 0), ("bundle", True, 2),
                                        ("installed-case", False, 13), ("no-plugin-case", False, 9)):
            with self.subTest(kind=kind, builder=builder):
                scope = isolation._CombinedLifecycle(kind, bundle_writer=builder)
                self.complete_scope(scope)
                record = scope.normalized_record()
                self.assertEqual("complete", record["phase"])
                self.assertEqual(controls, len(record["controls"]))
                self.assertTrue(all(item["state"] == "closed" for item in record["controls"]))
                self.assertEqual("not-required" if kind == "bundle" else "closed", record["consumer"])

    def test_scope_registration_failure_preserves_exception_and_completed_records(self):
        class FailedRegistration(list):
            def append(self, value):
                raise failure

        failure = MemoryError("registration unavailable")
        run = isolation._CombinedLifecycleRun(simulated=True)
        completed = run.begin("bundle")
        self.complete_scope(completed)
        for role in ("process-controller", "root-session", "owned-root", "source-bundle"):
            run.register_control(role)
        previous = completed.normalized_record()
        run.scopes = FailedRegistration(run.scopes)
        with self.assertRaises(MemoryError) as caught:
            run.begin("installed-case")
        self.assertIs(failure, caught.exception)
        self.assertEqual([previous], [s.normalized_record() for s in run.scopes])
        self.assertEqual((1, 1, "incomplete"), tuple(run.normalized_summary()[key] for key in (
            "startedScopeCount", "completedScopeCount", "runState"
        )))
        with self.assertRaises(isolation.ProcessDomainError):
            run.begin("installed-case")

    def test_first_scope_construction_failure_creates_no_resources(self):
        run = isolation._CombinedLifecycleRun(simulated=True)
        with self.assertRaisesRegex(isolation.ProcessDomainError, "combined-scope-writers-invalid"):
            run.begin("bundle", bundle_writer="true")
        run.finish()
        facts = run.normalized_summary()
        self.assertEqual("incomplete", facts["runState"])
        self.assertEqual([], facts["scopes"])
        self.assertEqual([], facts["runControls"])
        self.assertEqual(0, facts["unresolvedCreatedResourceCount"])
        with self.assertRaises(isolation.ProcessDomainError):
            run.begin("bundle")


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
