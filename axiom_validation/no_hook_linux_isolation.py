"""Offline Combined lifecycle contract and retained Linux process-domain code.

The Combined runtime backend is unfinished. Import and repository validation
perform no capability detection; contract/simulation facts never prove host
support, identity isolation, descendant coverage, or runtime cleanup.

The real backend is deliberately narrow: Linux/x86_64, delegated cgroup v2,
``clone3(CLONE_INTO_CGROUP | CLONE_PIDFD)``, pidfd-bound direct-child waits,
and an authoritative ``cgroup.events`` empty proof.  There is no process-group
or post-spawn ``cgroup.procs`` fallback.

The deterministic backend exists only for fake validation and unit tests.  It
shares the same ordering and closed-result contract, but it never represents a
host process-domain claim.  The real bootstrap is implemented directly after
``clone3``; no subprocess callback runs between enrollment and ``execve``.
"""

from __future__ import annotations

import ctypes
import errno
import json
import os
import platform
import secrets
import select
import signal
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Callable, Mapping, Sequence


REAL_MECHANISM = "linux-cgroup-v2-clone3-pidfd-v1"
TEST_MECHANISM = "deterministic-process-domain-test-backend-v1"
PROCESS_PURPOSES = frozenset(
    {
        "bundle-builder",
        "marketplace",
        "plugin-install",
        "model-case",
        "synthetic-probe",
    }
)

SYS_CLONE3_X86_64 = 435
SYS_CLOSE_RANGE_X86_64 = 436
CLONE_PIDFD = 0x00001000
CLONE_INTO_CGROUP = 0x200000000
CLOSE_RANGE_CLOEXEC = 1 << 2
PR_SET_CHILD_SUBREAPER = 36
PR_GET_CHILD_SUBREAPER = 37
DOMAIN_EMPTY_TIMEOUT_SECONDS = 5.0
BOOTSTRAP_TIMEOUT_SECONDS = 5.0
MAX_BUNDLE_WORKER_RESULT_BYTES = 512 * 1024


class ProcessDomainError(RuntimeError):
    """Closed process-domain failure with no retained host identifier."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


_COMBINED_PHASES = (
    "prepare", "writing", "writers-closed", "view-sealed",
    "contract-preconditions-complete", "consuming", "consumers-closed",
    "resources-closed", "complete",
)
_COMBINED_RUNTIME_FACTS = (
    "kernelSupport", "preExecutionIsolation", "lifetimeMembership",
    "descendantCoverage", "privateViewConsumption", "runtimeTeardown",
    "fixedIdentityTransition", "descriptorInheritance", "capabilityReduction",
    "writerDomainClosure", "controlResourceTeardown",
)
_COMBINED_WRITERS = ("bundle-builder", "marketplace", "plugin-install")
_COMBINED_RUN_CONTROLS = ("process-controller", "root-session", "owned-root", "source-bundle")
_COMBINED_DIRECTORIES = (
    "case-root", "workspace", "model-home", "home", "xdg-config", "xdg-cache", "xdg-data",
)
_COMBINED_CASE_CONTROLS = (*_COMBINED_DIRECTORIES, "schema", "model-streams")
_COMBINED_INSTALL_CONTROLS = ("marketplace-view", "installed-view", "marketplace-streams", "plugin-install-streams")
_COMBINED_BUNDLE_CONTROLS = ("destination", "builder-handles")
_COMBINED_CONTROLS = (*_COMBINED_CASE_CONTROLS, *_COMBINED_INSTALL_CONTROLS, *_COMBINED_BUNDLE_CONTROLS)


def _combined_lifecycle_contract() -> dict[str, object]:
    """The offline contract has no capability detector or execution authority."""
    return {
        "implementation": "offline-contract-only",
        "scope": "one-bundle-and-sixteen-case-scopes",
        "phases": list(_COMBINED_PHASES),
        "failureState": "incomplete-irreversible",
        "owners": {
            "prepare": "observer-object-owner",
            "writing": "workload-writer",
            "writers-closed": "process-domain-owner",
            "view-sealed": "observer-object-owner",
            "contract-preconditions-complete": "lifecycle-contract-owner",
            "consuming": "separately-authorized-launcher",
            "consumers-closed": "process-domain-owner",
            "resources-closed": "resource-owner",
            "complete": "observer-result-owner",
        },
        "requiredFacts": {
            "prepare": "owned-scope-and-canonical-position",
            "writing": "canonical-writer-order-with-separate-launch-authority",
            "writers-closed": "every-registered-writer-closed",
            "view-sealed": "closed-writers-and-matching-accepted-object",
            "contract-preconditions-complete": "sealed-logical-view-and-exact-descriptor-policy",
            "consuming": "contract-preconditions-and-separate-model-authority",
            "consumers-closed": "every-registered-consumer-closed",
            "resources-closed": "consumers-closed-and-no-unresolved-owned-control",
            "complete": "all-scopes-complete-and-run-controls-closed",
        },
        "inventoryBounds": {
            "scopes": 17, "writerWorkloads": 31,
            "consumerWorkloads": 16, "controlResources": 256,
        },
        "controlInventory": {
            "run": ["process-controller", "root-session", "owned-root", "source-bundle"],
            "bundle": "destination-and-worker-handles-if-builder-started",
            "installedCase": "seven-directories-two-product-views-schema-three-stream-worker-sets",
            "noPluginCase": "seven-directories-schema-one-stream-worker-set",
            "streamWorkerSet": "stdin-stdout-stderr-handles-and-joined-workers",
        },
        "simulationSource": "deterministic-contract-backend-v1",
        "runtimeBackend": "not-implemented",
        "runtimeFacts": {key: "not-verified" for key in _COMBINED_RUNTIME_FACTS},
        "actualExecutionEligible": False,
        "supervisorProcess": "not-implemented-zero-started",
        "viewBinding": "live-scope-control-and-accepted-logical-binding-required",
        "scopeAccounting": "successful-registration-only-canonical-prefix",
        "componentAccounting": "closed-role-records-before-aggregate-counts-for-every-status",
        "failureCleanup": "irreversible-incomplete-with-no-active-workloads",
        "writerHandoff": "closed-writer-before-product-acceptance",
        "publication": "all-scopes-and-owned-controls-closed-for-selected-mode",
        "unknownObjects": "preserve-incomplete-no-invented-residual",
        "modelCallAuthority": "external-unchanged-sixteen-call-capability",
    }


def _combined_lifecycle_result_schema() -> dict[str, object]:
    """Closed normalized contract facts, with no retained object identifiers."""
    def closed(properties: dict[str, object]) -> dict[str, object]:
        return {"type": "object", "additionalProperties": False,
                "required": list(properties), "properties": properties}

    properties: dict[str, object] = {
        "source": {"enum": ["contract-only", "deterministic-contract-backend-v1"]},
        "contractStatus": {"enum": ["complete", "incomplete"]},
        "simulationStatus": {"enum": ["complete", "incomplete", "not-run"]},
        "runtimeBackend": {"const": "not-implemented"},
        "runtimeFacts": closed({key: {"const": "not-verified"}
                                for key in _COMBINED_RUNTIME_FACTS}),
        "actualExecutionEligible": {"const": False},
    }
    for name, maximum in (
        ("startedScopeCount", 17), ("completedScopeCount", 17),
        ("writerStartedCount", 31), ("writerClosedCount", 31),
        ("consumerStartedCount", 16), ("consumerClosedCount", 16),
        ("controlRegisteredCount", 256), ("controlClosedCount", 256),
        ("unresolvedCreatedResourceCount", 303),
    ):
        properties[name] = {"type": "integer", "minimum": 0, "maximum": maximum}
    properties["supervisorProcess"] = closed({
        "implementation": {"const": "not-implemented"},
        "startedCount": {"const": 0}, "closedCount": {"const": 0},
    })
    properties["runState"] = {"enum": ["active", "incomplete", "complete"]}
    properties["runControls"] = {
        "type": "array", "maxItems": 4,
        "items": closed({"role": {"enum": list(_COMBINED_RUN_CONTROLS)},
                         "state": {"enum": ["open", "closed"]}}),
    }
    properties["scopes"] = {
        "type": "array", "maxItems": 17,
        "items": closed({
            "kind": {"enum": ["bundle", "installed-case", "no-plugin-case"]},
            "phase": {"enum": [*_COMBINED_PHASES, "incomplete"]},
            "progress": {"enum": list(_COMBINED_PHASES)},
            "viewState": {"enum": ["not-accepted", "accepted", "sealed"]},
            "writers": closed({purpose: {"enum": ["not-required", "not-started", "active", "closed"]}
                               for purpose in _COMBINED_WRITERS}),
            "consumer": {"enum": ["not-required", "not-started", "active", "closed"]},
            "controls": {"type": "array", "maxItems": 13,
                         "items": closed({"role": {"enum": list(_COMBINED_CONTROLS)},
                                          "state": {"enum": ["open", "closed"]}})},
        }),
    }
    return closed(properties)


class _CombinedLifecycle:
    """One in-memory scope. Completion proves contract order, never isolation.

    Tokens identify components/resources registered by their owning adapter.
    There is deliberately no boolean API for asserting runtime success. Known
    resources may still be closed after failure, but failure cannot be undone.
    """

    def __init__(self, kind: str, *, bundle_writer: bool = False) -> None:
        if type(kind) is not str or kind not in {"bundle", "installed-case", "no-plugin-case"}:
            raise ProcessDomainError("combined-scope-kind-invalid")
        if type(bundle_writer) is not bool or (bundle_writer and kind != "bundle"):
            raise ProcessDomainError("combined-scope-writers-invalid")
        self.kind = kind
        self.phase = "prepare"
        self._failure_phase = "prepare"
        self.expected_writers = (
            ("bundle-builder",) if bundle_writer else
            ("marketplace", "plugin-install") if kind == "installed-case" else ()
        )
        self.expected_consumers = 0 if kind == "bundle" else 1
        self._writers: dict[object, tuple[str, bool]] = {}
        self._consumers: dict[object, bool] = {}
        self._controls: dict[object, bool] = {}
        self._control_roles: dict[object, str] = {}
        self._control_bindings: dict[object, tuple[object, ...] | None] = {}
        self._accepted = False
        self._sealed = False
        self._binding: tuple[object, ...] | None = None
        self._view_control: object | None = None

    def abort(self) -> None:
        if self.phase != "incomplete":
            self._failure_phase = self.phase
        self.phase = "incomplete"

    @property
    def expected_controls(self) -> tuple[str, ...]:
        if self.kind == "bundle":
            return _COMBINED_BUNDLE_CONTROLS if self.expected_writers else ()
        return (*_COMBINED_CASE_CONTROLS,
                *(_COMBINED_INSTALL_CONTROLS if self.kind == "installed-case" else ()))

    @property
    def view_role(self) -> str | None:
        return ("installed-view" if self.kind == "installed-case" else
                "model-home" if self.kind == "no-plugin-case" else None)

    def _require_live_view(self) -> None:
        if self.expected_consumers and (
            self._controls.get(self._view_control) is not False
            or self._control_roles.get(self._view_control) != self.view_role
            or self._control_bindings.get(self._view_control) != self._binding
        ):
            self._reject("combined-consumption-control-invalid")

    def _reject(self, code: str) -> None:
        self.abort()
        raise ProcessDomainError(code)

    def _require(self, phase: str) -> None:
        if self.phase != phase:
            self._reject("combined-phase-order-invalid")

    def prepared(self) -> None:
        self._require("prepare")
        self.phase = "writing"

    def _require_controls_open(self, roles: set[str]) -> None:
        live = {self._control_roles[token] for token, closed in self._controls.items() if not closed}
        if not roles <= live:
            self._reject("combined-launch-controls-incomplete")

    def require_launch(self, purpose: str) -> None:
        if purpose == "model-case":
            self._require("consuming")
            self._require_live_view()
            if len(self._consumers) >= self.expected_consumers:
                self._reject("combined-consumer-count-invalid")
        else:
            self._require("writing")
            if self.kind == "installed-case":
                self._require_controls_open(set(_COMBINED_DIRECTORIES) | {"marketplace-view"})
            index = len(self._writers)
            if (index >= len(self.expected_writers)
                    or self.expected_writers[index] != purpose
                    or any(not closed for _, closed in self._writers.values())):
                self._reject("combined-writer-order-invalid")

    def workload_started(self, purpose: str, token: object) -> None:
        self.require_launch(purpose)
        if purpose == "bundle-builder":
            self._require_controls_open(set(_COMBINED_BUNDLE_CONTROLS))
        if token in self._writers or token in self._consumers:
            self._reject("combined-workload-identity-invalid")
        if purpose == "model-case":
            self._consumers[token] = False
        else:
            self._writers[token] = (purpose, False)

    def workload_closed(self, token: object) -> None:
        if token in self._writers and self._writers[token][1] is False:
            self._writers[token] = (self._writers[token][0], True)
        elif token in self._consumers and self._consumers[token] is False:
            self._consumers[token] = True
        else:
            self._reject("combined-workload-completion-invalid")

    def require_writer_closed(self, purpose: str) -> None:
        self._require("writing")
        if (purpose, True) not in self._writers.values():
            self._reject("combined-writer-handoff-incomplete")

    def writers_closed(self) -> None:
        self._require("writing")
        if (len(self._writers) != len(self.expected_writers)
                or any(not closed for _, closed in self._writers.values())):
            self._reject("combined-writer-closure-incomplete")
        self.phase = "writers-closed"

    def accept_view(
        self, expected: tuple[object, ...] | None, observed: tuple[object, ...] | None,
        *, control: object | None = None,
    ) -> None:
        self._require("writers-closed")
        absent = self.kind == "no-plugin-case"
        if (self._accepted or expected != observed
                or (absent and expected is not None)
                or (not absent and (type(expected) is not tuple or not expected))):
            self._reject("combined-consumption-binding-invalid")
        self._binding = expected
        self._view_control = control
        self._require_live_view()
        self._accepted = True

    def seal_view(self) -> None:
        self._require("writers-closed")
        if not self._accepted:
            self._reject("combined-view-acceptance-missing")
        self._require_live_view()
        self._sealed = True
        self.phase = "view-sealed"

    def contract_preconditions(
        self, *, view_binding: tuple[object, ...] | None, descriptor_policy: str
    ) -> None:
        self._require("view-sealed")
        self._require_live_view()
        if (view_binding != self._binding
                or descriptor_policy != "exact-required-pass-fds"
                or not set(self.expected_controls) - {"model-streams"} <= set(self._control_roles.values())):
            self._reject("combined-contract-preconditions-incomplete")
        self.phase = "contract-preconditions-complete"

    def consume(self) -> None:
        self._require("contract-preconditions-complete")
        self._require_live_view()
        self.phase = "consuming"

    def consumers_closed(self) -> None:
        self._require("consuming")
        if (len(self._consumers) != self.expected_consumers
                or not all(self._consumers.values())):
            self._reject("combined-consumer-closure-incomplete")
        self.phase = "consumers-closed"

    def register_control(
        self, token: object, *, role: str, binding: tuple[object, ...] | None = None
    ) -> None:
        if (self.phase in {"incomplete", "resources-closed", "complete"}
                or token in self._controls or role not in self.expected_controls
                or role in self._control_roles.values()):
            self._reject("combined-control-registration-invalid")
        if (role == "schema" and self.phase != "view-sealed"
                or role == "installed-view" and ("plugin-install", True) not in self._writers.values()
                or role == "model-streams" and not self._consumers
                or role in {"marketplace-streams", "plugin-install-streams"}
                and not any(purpose == role.removesuffix("-streams") for purpose, _ in self._writers.values())):
            self._reject("combined-control-phase-invalid")
        self._controls[token] = False
        self._control_roles[token] = role
        self._control_bindings[token] = binding

    def require_control_close(self, token: object) -> None:
        if token not in self._controls or self._controls[token]:
            self._reject("combined-control-completion-invalid")
        # Closing a view while a consumer is live is never a valid transition.
        if not self.workloads_closed:
            self._reject("combined-view-consumer-still-active")
        if (self.phase != "incomplete" and self.expected_consumers
                and not self._control_roles[token].endswith("-streams")
                and len(self._consumers) != self.expected_consumers):
            self._reject("combined-view-consumer-still-pending")

    def control_closed(self, token: object) -> None:
        self.require_control_close(token)
        self._controls[token] = True

    @property
    def workloads_closed(self) -> bool:
        return (all(self._consumers.values())
                and all(closed for _, closed in self._writers.values()))

    @property
    def unresolved_resources(self) -> int:
        return (sum(not closed for _, closed in self._writers.values())
                + sum(not closed for closed in self._consumers.values())
                + sum(not closed for closed in self._controls.values()))

    def resources_closed(self) -> None:
        self._require("consumers-closed")
        if (self.unresolved_resources
                or set(self._control_roles.values()) != set(self.expected_controls)):
            self._reject("combined-resource-closure-incomplete")
        self.phase = "resources-closed"

    def complete(self) -> None:
        self._require("resources-closed")
        self.phase = "complete"

    def normalized_record(self) -> dict[str, object]:
        writers = {purpose: "not-started" if purpose in self.expected_writers else "not-required"
                   for purpose in _COMBINED_WRITERS}
        for purpose, closed in self._writers.values():
            writers[purpose] = "closed" if closed else "active"
        return {
            "kind": self.kind, "phase": self.phase,
            "progress": self._failure_phase if self.phase == "incomplete" else self.phase,
            "viewState": "sealed" if self._sealed else "accepted" if self._accepted else "not-accepted",
            "writers": writers,
            "consumer": ("not-required" if not self.expected_consumers else
                         "not-started" if not self._consumers else
                         "closed" if all(self._consumers.values()) else "active"),
            "controls": [{"role": self._control_roles[token], "state": "closed" if closed else "open"}
                         for token, closed in self._controls.items()],
        }


class _CombinedLifecycleRun:
    """Bounded contract/simulation accounting, separate from model authority."""

    def __init__(self, *, simulated: bool = False) -> None:
        if type(simulated) is not bool:
            raise ProcessDomainError("combined-source-invalid")
        self.simulated = simulated
        self.scopes: list[_CombinedLifecycle] = []
        self._controls: dict[object, bool] = {}
        self._failed = False
        self._finished = False

    def begin(self, kind: str, *, bundle_writer: bool = False) -> _CombinedLifecycle:
        try:
            ordinal = len(self.scopes)
            expected = "bundle" if ordinal == 0 else "no-plugin-case" if ordinal == 11 else "installed-case"
            if (self._failed or self._finished or ordinal >= 17 or kind != expected
                    or (ordinal and any(self._controls.get(name) is not False for name in _COMBINED_RUN_CONTROLS))
                    or (self.scopes and self.scopes[-1].phase != "complete")):
                raise ProcessDomainError("combined-scope-order-invalid")
            scope = _CombinedLifecycle(kind, bundle_writer=bundle_writer)
            # The count advances only after successful construction and append.
            self.scopes.append(scope)
        except (ProcessDomainError, MemoryError):
            self.abort()
            raise
        return scope

    def abort(self) -> None:
        self._failed = True
        if self.scopes and self.scopes[-1].phase != "complete":
            self.scopes[-1].abort()

    def register_control(self, token: object) -> None:
        if (self._failed or self._finished or not self.scopes or token in self._controls
                or token not in _COMBINED_RUN_CONTROLS):
            self.abort()
            raise ProcessDomainError("combined-run-control-invalid")
        if token == "source-bundle" and (
            self.scopes[0].phase == "prepare"
            or len(self.scopes[0]._writers) != len(self.scopes[0].expected_writers)
            or not self.scopes[0].workloads_closed
        ):
            self.abort()
            raise ProcessDomainError("combined-run-source-writer-incomplete")
        self._controls[token] = False

    def control_closed(self, token: object) -> None:
        if (token not in self._controls or self._controls[token]
                or any(not scope.workloads_closed for scope in self.scopes)
                or (not self._failed and (len(self.scopes) != 17
                    or any(scope.phase != "complete" for scope in self.scopes)))):
            self.abort()
            raise ProcessDomainError("combined-run-control-completion-invalid")
        self._controls[token] = True

    @property
    def safe_for_cleanup(self) -> bool:
        # Run-level filesystem/session handles remain open until cleanup.
        return all(scope.unresolved_resources == 0 for scope in self.scopes)

    def finish(self) -> None:
        if (len(self.scopes) != 17
                or any(scope.phase != "complete" for scope in self.scopes)
                or len(self._controls) != 4
                or not all(self._controls.values())):
            self.abort()
        self._finished = True

    def normalized_summary(self) -> dict[str, object]:
        writers = [closed for scope in self.scopes for _, closed in scope._writers.values()]
        consumers = [closed for scope in self.scopes for closed in scope._consumers.values()]
        controls = [*self._controls.values(), *(closed for scope in self.scopes for closed in scope._controls.values())]
        complete = (self._finished and not self._failed
                    and len(self.scopes) == 17
                    and all(scope.phase == "complete" for scope in self.scopes)
                    and all(controls))
        return {
            "source": "deterministic-contract-backend-v1" if self.simulated else "contract-only",
            "contractStatus": "complete" if complete else "incomplete",
            "simulationStatus": ("complete" if complete else "incomplete") if self.simulated else "not-run",
            "runtimeBackend": "not-implemented",
            "runtimeFacts": {key: "not-verified" for key in _COMBINED_RUNTIME_FACTS},
            "actualExecutionEligible": False,
            "runState": ("incomplete" if self._failed or any(scope.phase == "incomplete" for scope in self.scopes)
                         else "complete" if complete else "active"),
            "runControls": [{"role": token, "state": "closed" if closed else "open"}
                            for token, closed in self._controls.items()],
            "scopes": [scope.normalized_record() for scope in self.scopes],
            "startedScopeCount": len(self.scopes),
            "completedScopeCount": sum(scope.phase == "complete" for scope in self.scopes),
            "writerStartedCount": len(writers), "writerClosedCount": sum(writers),
            "consumerStartedCount": len(consumers), "consumerClosedCount": sum(consumers),
            "controlRegisteredCount": len(controls), "controlClosedCount": sum(controls),
            "unresolvedCreatedResourceCount": sum(not closed for closed in (*writers, *consumers, *controls)),
            "supervisorProcess": {"implementation": "not-implemented", "startedCount": 0, "closedCount": 0},
        }


@dataclass(frozen=True)
class ProcessDomainCapabilities:
    """Path-free capability facts suitable for normalized reporting."""

    platform_supported: bool
    cgroup_v2_available: bool
    delegated_subtree_writable: bool
    clone_into_cgroup_available: bool
    clone_pidfd_available: bool
    cgroup_kill_available: bool
    cgroup_events_available: bool
    child_subreaper_available: bool
    pidfd_wait_available: bool

    @property
    def available(self) -> bool:
        return all(
            (
                self.platform_supported,
                self.cgroup_v2_available,
                self.delegated_subtree_writable,
                self.clone_into_cgroup_available,
                self.clone_pidfd_available,
                self.cgroup_kill_available,
                self.cgroup_events_available,
                self.child_subreaper_available,
                self.pidfd_wait_available,
            )
        )

    def normalized(self) -> dict[str, bool]:
        return {
            "platformSupported": self.platform_supported,
            "cgroupV2Available": self.cgroup_v2_available,
            "delegatedSubtreeWritable": self.delegated_subtree_writable,
            "cloneIntoCgroupAvailable": self.clone_into_cgroup_available,
            "clonePidfdAvailable": self.clone_pidfd_available,
            "cgroupKillAvailable": self.cgroup_kill_available,
            "cgroupEventsAvailable": self.cgroup_events_available,
            "childSubreaperAvailable": self.child_subreaper_available,
            "pidfdWaitAvailable": self.pidfd_wait_available,
        }


@dataclass(frozen=True)
class ProcessDomainOutcome:
    """One path-free terminal process-domain record."""

    purpose: str
    atomic_enrollment_verified: bool
    direct_child_pidfd_verified: bool
    termination_required: bool
    complete_domain_termination_verified: bool
    domain_empty_verified: bool
    descendant_reaping_verified: bool
    domain_removal_verified: bool


class _CloneArgs(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_uint64),
        ("pidfd", ctypes.c_uint64),
        ("child_tid", ctypes.c_uint64),
        ("parent_tid", ctypes.c_uint64),
        ("exit_signal", ctypes.c_uint64),
        ("stack", ctypes.c_uint64),
        ("stack_size", ctypes.c_uint64),
        ("tls", ctypes.c_uint64),
        ("set_tid", ctypes.c_uint64),
        ("set_tid_size", ctypes.c_uint64),
        ("cgroup", ctypes.c_uint64),
    ]


def _libc() -> ctypes.CDLL:
    """Load libc only on an explicitly entered legacy runtime path."""
    return ctypes.CDLL(None, use_errno=True)


_REAL_SUPERVISOR_LOCK = threading.Lock()


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )


def _parse_current_cgroup() -> str | None:
    try:
        with open("/proc/self/cgroup", "r", encoding="ascii") as stream:
            matches = [
                line.rstrip("\n").split("::", 1)[1]
                for line in stream
                if line.startswith("0::") and "::" in line
            ]
    except (OSError, UnicodeError):
        return None
    if len(matches) != 1:
        return None
    parts = matches[0].split("/")
    if any(part in {".", ".."} for part in parts):
        return None
    return matches[0]


def detect_process_domain_capabilities() -> ProcessDomainCapabilities:
    """Perform a read-only, normalized availability inspection.

    The actual clone flags and control-file writes are verified again by the
    launch path.  A read-only detection result never authorizes a process.
    """

    supported = platform.system() == "Linux" and platform.machine() == "x86_64"
    cgroup_v2 = False
    delegated = False
    kill_available = False
    events_available = False
    subreaper = False
    if supported:
        try:
            with open("/proc/self/mountinfo", "r", encoding="utf-8") as stream:
                cgroup_v2 = any(" - cgroup2 " in line for line in stream)
        except (OSError, UnicodeError):
            cgroup_v2 = False
    relative = _parse_current_cgroup() if cgroup_v2 else None
    if relative is not None:
        path = Path("/sys/fs/cgroup") / relative.lstrip("/")
        descriptor: int | None = None
        try:
            descriptor = os.open(path, _directory_flags())
            metadata = os.fstat(descriptor)
            delegated = (
                stat.S_ISDIR(metadata.st_mode)
                and metadata.st_uid == os.geteuid()
                and os.access(path, os.W_OK)
            )
            kill_available = stat.S_ISREG(
                os.stat("cgroup.kill", dir_fd=descriptor, follow_symlinks=False).st_mode
            )
            events_available = stat.S_ISREG(
                os.stat("cgroup.events", dir_fd=descriptor, follow_symlinks=False).st_mode
            )
        except OSError:
            delegated = False
            kill_available = False
            events_available = False
        finally:
            if descriptor is not None:
                os.close(descriptor)
        current = ctypes.c_int()
        subreaper = (
            _libc().prctl(PR_GET_CHILD_SUBREAPER, ctypes.byref(current), 0, 0, 0) == 0
        )
    return ProcessDomainCapabilities(
        platform_supported=supported,
        cgroup_v2_available=cgroup_v2,
        delegated_subtree_writable=delegated,
        clone_into_cgroup_available=supported and hasattr(os, "P_PIDFD"),
        clone_pidfd_available=supported and hasattr(os, "P_PIDFD"),
        cgroup_kill_available=kill_available,
        cgroup_events_available=events_available,
        child_subreaper_available=subreaper,
        pidfd_wait_available=hasattr(os, "P_PIDFD") and hasattr(os, "waitid"),
    )


def _parse_cgroup_events(data: bytes) -> bool:
    try:
        text = data.decode("ascii")
    except UnicodeError as error:
        raise ProcessDomainError("cgroup-events-malformed") from error
    values: dict[str, str] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[0] in values:
            raise ProcessDomainError("cgroup-events-malformed")
        values[fields[0]] = fields[1]
    if values.get("populated") not in {"0", "1"}:
        raise ProcessDomainError("cgroup-events-malformed")
    return values["populated"] == "1"


def _wait_status_returncode(status: os.waitid_result) -> int:
    if status.si_code == os.CLD_EXITED:
        return int(status.si_status)
    if status.si_code in {os.CLD_KILLED, os.CLD_DUMPED}:
        return -int(status.si_status)
    raise ProcessDomainError("direct-child-status-invalid")


class DomainProcess:
    """Popen-shaped process whose lifecycle is owned by one process domain."""

    def __init__(
        self,
        *,
        supervisor: "BaseProcessDomainSupervisor",
        purpose: str,
        stdin: BinaryIO,
        stdout: BinaryIO,
        stderr: BinaryIO,
    ) -> None:
        self.supervisor = supervisor
        self.purpose = purpose
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.returncode: int | None = None
        self._completed = False

    def poll(self) -> int | None:
        raise NotImplementedError

    def wait(self, timeout: float | None = None) -> int:
        raise NotImplementedError

    def complete(self, *, terminate: bool) -> ProcessDomainOutcome:
        if self._completed:
            raise ProcessDomainError("process-domain-already-completed")
        outcome = self.supervisor._complete(self, terminate=terminate)
        self._completed = True
        return outcome


class _RealDomainProcess(DomainProcess):
    def __init__(
        self,
        *,
        supervisor: "LinuxProcessDomainSupervisor",
        purpose: str,
        stdin: BinaryIO,
        stdout: BinaryIO,
        stderr: BinaryIO,
        pidfd: int,
        group_fd: int,
        events_fd: int,
        kill_fd: int,
        group_name: str,
        group_device: int,
        group_inode: int,
    ) -> None:
        super().__init__(
            supervisor=supervisor,
            purpose=purpose,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        self.pidfd = pidfd
        self.group_fd = group_fd
        self.events_fd = events_fd
        self.kill_fd = kill_fd
        self.group_name = group_name
        self.group_device = group_device
        self.group_inode = group_inode
        self.direct_reaped = False

    def poll(self) -> int | None:
        if self.returncode is not None:
            return self.returncode
        status = os.waitid(
            os.P_PIDFD,
            self.pidfd,
            os.WEXITED | os.WNOHANG | os.WNOWAIT,
        )
        if status is None:
            return None
        self.returncode = _wait_status_returncode(status)
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        if self.direct_reaped:
            if self.returncode is None:
                raise ProcessDomainError("direct-child-status-missing")
            return self.returncode
        poller = select.poll()
        poller.register(self.pidfd, select.POLLIN)
        milliseconds = -1 if timeout is None else max(0, int(timeout * 1000))
        if not poller.poll(milliseconds):
            raise TimeoutError("direct-child-wait-timeout")
        status = os.waitid(os.P_PIDFD, self.pidfd, os.WEXITED)
        if status is None:
            raise ProcessDomainError("direct-child-status-missing")
        self.returncode = _wait_status_returncode(status)
        self.direct_reaped = True
        return self.returncode


class _DeterministicDomainProcess(DomainProcess):
    def __init__(
        self,
        *,
        supervisor: "DeterministicProcessDomainSupervisor",
        purpose: str,
        process: subprocess.Popen[bytes],
        domain_index: int,
    ) -> None:
        if process.stdin is None or process.stdout is None or process.stderr is None:
            raise ProcessDomainError("child-pipes-unavailable")
        super().__init__(
            supervisor=supervisor,
            purpose=purpose,
            stdin=process.stdin,
            stdout=process.stdout,
            stderr=process.stderr,
        )
        self.process = process
        self.domain_index = domain_index

    def poll(self) -> int | None:
        self.returncode = self.process.poll()
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = self.process.wait(timeout=timeout)
        return self.returncode


class BaseProcessDomainSupervisor:
    """Shared ordering and normalized-result owner for process domains."""

    mechanism: str
    availability: str
    test_only: bool

    def __init__(self) -> None:
        self._active: DomainProcess | None = None
        self._outcomes: list[ProcessDomainOutcome] = []
        self._unsafe = False
        self._closed = False

    def _before_launch(self, purpose: str) -> None:
        if self._closed:
            raise ProcessDomainError("process-domain-supervisor-closed")
        if purpose not in PROCESS_PURPOSES:
            raise ProcessDomainError("process-domain-purpose-invalid")
        if self._active is not None:
            raise ProcessDomainError("previous-process-domain-not-empty")
        if self._unsafe:
            raise ProcessDomainError("process-domain-manual-cleanup-required")

    def launch(
        self,
        *,
        purpose: str,
        executable_fd: int,
        argv: Sequence[str],
        cwd_fd: int,
        env: Mapping[str, str],
        pass_fds: Sequence[int],
        popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    ) -> DomainProcess:
        raise NotImplementedError

    def _complete(
        self, process: DomainProcess, *, terminate: bool
    ) -> ProcessDomainOutcome:
        raise NotImplementedError

    def _record(self, process: DomainProcess, outcome: ProcessDomainOutcome) -> None:
        if self._active is not process:
            self._unsafe = True
            raise ProcessDomainError("process-domain-ownership-drift")
        self._outcomes.append(outcome)
        self._active = None

    @property
    def safe_for_filesystem_cleanup(self) -> bool:
        return self._active is None and not self._unsafe and all(
            outcome.atomic_enrollment_verified
            and outcome.direct_child_pidfd_verified
            and (
                not outcome.termination_required
                or outcome.complete_domain_termination_verified
            )
            and outcome.domain_empty_verified
            and outcome.descendant_reaping_verified
            and outcome.domain_removal_verified
            for outcome in self._outcomes
        )

    def require_advance_barrier(self) -> None:
        if not self.safe_for_filesystem_cleanup:
            raise ProcessDomainError("process-domain-empty-proof-required")

    def normalized_summary(self) -> dict[str, object]:
        counts = {
            purpose: sum(outcome.purpose == purpose for outcome in self._outcomes)
            for purpose in ("bundle-builder", "marketplace", "plugin-install", "model-case")
        }
        total = len(self._outcomes)
        return {
            "mechanism": self.mechanism,
            "availability": self.availability,
            "domainCount": total,
            "builderDomainCount": counts["bundle-builder"],
            "marketplaceDomainCount": counts["marketplace"],
            "pluginInstallDomainCount": counts["plugin-install"],
            "modelDomainCount": counts["model-case"],
            "atomicEnrollmentVerifiedCount": sum(
                item.atomic_enrollment_verified for item in self._outcomes
            ),
            "directChildPidfdVerifiedCount": sum(
                item.direct_child_pidfd_verified for item in self._outcomes
            ),
            "terminationRequiredCount": sum(
                item.termination_required for item in self._outcomes
            ),
            "completeDomainTerminationVerifiedCount": sum(
                item.termination_required
                and item.complete_domain_termination_verified
                for item in self._outcomes
            ),
            "domainEmptyVerifiedCount": sum(
                item.domain_empty_verified for item in self._outcomes
            ),
            "descendantReapingVerifiedCount": sum(
                item.descendant_reaping_verified for item in self._outcomes
            ),
            "domainRemovalVerifiedCount": sum(
                item.domain_removal_verified for item in self._outcomes
            ),
            "residualDomainCount": (
                int(self._active is not None)
                + sum(not item.domain_removal_verified for item in self._outcomes)
            ),
            "manualCleanupRequired": self._unsafe or self._active is not None,
        }

    def close(self) -> None:
        if self._closed:
            return
        if not self.safe_for_filesystem_cleanup:
            self._unsafe = True
            raise ProcessDomainError("process-domain-close-before-empty")
        self._closed = True


class LinuxProcessDomainSupervisor(BaseProcessDomainSupervisor):
    """Real delegated-cgroup supervisor using atomic clone3 enrollment."""

    mechanism = REAL_MECHANISM
    availability = "available"
    test_only = False

    def __init__(
        self,
        *,
        parent_fd: int,
        parent_device: int,
        parent_inode: int,
        old_subreaper: int,
    ) -> None:
        super().__init__()
        self.parent_fd = parent_fd
        self.parent_device = parent_device
        self.parent_inode = parent_inode
        self.old_subreaper = old_subreaper
        self._counter = 0
        self._lock_held = True

    @classmethod
    def open(cls) -> "LinuxProcessDomainSupervisor":
        facts = detect_process_domain_capabilities()
        if not facts.available:
            raise ProcessDomainError("process-domain-capability-unavailable")
        if not _REAL_SUPERVISOR_LOCK.acquire(blocking=False):
            raise ProcessDomainError("process-domain-supervisor-already-active")
        parent_fd: int | None = None
        old = ctypes.c_int()
        try:
            relative = _parse_current_cgroup()
            if relative is None:
                raise ProcessDomainError("process-domain-membership-unavailable")
            parent_fd = os.open(
                Path("/sys/fs/cgroup") / relative.lstrip("/"),
                _directory_flags(),
            )
            metadata = os.fstat(parent_fd)
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.geteuid()
            ):
                raise ProcessDomainError("process-domain-delegation-invalid")
            if _libc().prctl(PR_GET_CHILD_SUBREAPER, ctypes.byref(old), 0, 0, 0) != 0:
                raise ProcessDomainError("child-subreaper-unavailable")
            if _libc().prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
                raise ProcessDomainError("child-subreaper-unavailable")
            result = cls(
                parent_fd=parent_fd,
                parent_device=metadata.st_dev,
                parent_inode=metadata.st_ino,
                old_subreaper=int(old.value),
            )
            parent_fd = None
            return result
        except BaseException:
            if parent_fd is not None:
                os.close(parent_fd)
            _libc().prctl(PR_SET_CHILD_SUBREAPER, int(old.value), 0, 0, 0)
            _REAL_SUPERVISOR_LOCK.release()
            raise

    def _verify_parent(self) -> None:
        current = os.fstat(self.parent_fd)
        if (
            not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino)
            != (self.parent_device, self.parent_inode)
        ):
            self._unsafe = True
            raise ProcessDomainError("process-domain-parent-identity-drift")

    @staticmethod
    def _read_populated(process: _RealDomainProcess) -> bool:
        try:
            data = os.pread(process.events_fd, 4096, 0)
        except OSError as error:
            raise ProcessDomainError("cgroup-events-read-failed") from error
        return _parse_cgroup_events(data)

    @staticmethod
    def _write_kill(process: _RealDomainProcess) -> None:
        try:
            written = os.write(process.kill_fd, b"1")
        except OSError as error:
            raise ProcessDomainError("cgroup-kill-failed") from error
        if written != 1:
            raise ProcessDomainError("cgroup-kill-failed")

    @staticmethod
    def _close_range_cloexec() -> None:
        result = _libc().syscall(
            SYS_CLOSE_RANGE_X86_64,
            ctypes.c_uint(3),
            ctypes.c_uint(0xFFFFFFFF),
            ctypes.c_uint(CLOSE_RANGE_CLOEXEC),
        )
        if result != 0 and ctypes.get_errno() not in {errno.ENOSYS, errno.EINVAL}:
            raise OSError(ctypes.get_errno(), "close_range")
        if result != 0:
            # Python-created descriptors are non-inheritable by default.  A
            # kernel without close_range is nevertheless rejected on the real
            # path rather than widening the inherited descriptor surface.
            raise ProcessDomainError("close-range-cloexec-unavailable")

    @staticmethod
    def _child_exec(
        *,
        executable_fd: int,
        argv: tuple[str, ...],
        cwd_fd: int,
        env: dict[str, str],
        pass_fds: tuple[int, ...],
        stdin_fd: int,
        stdout_fd: int,
        stderr_fd: int,
        status_fd: int,
    ) -> None:
        try:
            signal.pthread_sigmask(signal.SIG_SETMASK, [])
            for observed in (
                signal.SIGPIPE,
                signal.SIGINT,
                signal.SIGTERM,
                signal.SIGHUP,
            ):
                signal.signal(observed, signal.SIG_DFL)
            os.dup2(stdin_fd, 0, inheritable=True)
            os.dup2(stdout_fd, 1, inheritable=True)
            os.dup2(stderr_fd, 2, inheritable=True)
            LinuxProcessDomainSupervisor._close_range_cloexec()
            for descriptor in sorted({executable_fd, *pass_fds}):
                os.set_inheritable(descriptor, True)
            os.fchdir(cwd_fd)
            os.execve(f"/proc/self/fd/{executable_fd}", list(argv), env)
        except BaseException:
            try:
                os.write(status_fd, b"E")
            except OSError:
                pass
            os._exit(127)

    def _create_domain(self) -> tuple[str, int, int, int, int, int]:
        self._verify_parent()
        self._counter += 1
        name = f"axiom-no-hook-{self._counter:03d}-{secrets.token_hex(12)}"
        try:
            os.mkdir(name, 0o700, dir_fd=self.parent_fd)
        except FileExistsError as error:
            raise ProcessDomainError("process-domain-preexisting") from error
        except OSError as error:
            raise ProcessDomainError("process-domain-create-failed") from error
        group_fd: int | None = None
        events_fd: int | None = None
        kill_fd: int | None = None
        procs_fd: int | None = None
        try:
            group_fd = os.open(name, _directory_flags(), dir_fd=self.parent_fd)
            metadata = os.fstat(group_fd)
            if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.geteuid():
                raise ProcessDomainError("process-domain-ownership-drift")
            events_fd = os.open("cgroup.events", os.O_RDONLY | os.O_CLOEXEC, dir_fd=group_fd)
            kill_fd = os.open("cgroup.kill", os.O_WRONLY | os.O_CLOEXEC, dir_fd=group_fd)
            procs_fd = os.open("cgroup.procs", os.O_WRONLY | os.O_CLOEXEC, dir_fd=group_fd)
            if _parse_cgroup_events(os.pread(events_fd, 4096, 0)):
                raise ProcessDomainError("process-domain-already-populated")
            os.close(procs_fd)
            procs_fd = None
            return (
                name,
                group_fd,
                events_fd,
                kill_fd,
                metadata.st_dev,
                metadata.st_ino,
            )
        except BaseException:
            for descriptor in (procs_fd, kill_fd, events_fd, group_fd):
                if descriptor is not None:
                    os.close(descriptor)
            try:
                os.rmdir(name, dir_fd=self.parent_fd)
            except OSError:
                self._unsafe = True
            raise

    def launch(
        self,
        *,
        purpose: str,
        executable_fd: int,
        argv: Sequence[str],
        cwd_fd: int,
        env: Mapping[str, str],
        pass_fds: Sequence[int],
        popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    ) -> DomainProcess:
        self._before_launch(purpose)
        if popen_factory is not subprocess.Popen:
            raise ProcessDomainError("real-process-launcher-substitution-forbidden")
        if threading.current_thread() is not threading.main_thread():
            raise ProcessDomainError("process-domain-launch-must-use-main-thread")
        if threading.active_count() != 1:
            raise ProcessDomainError("process-domain-launch-requires-single-threaded-supervisor")
        if (
            type(executable_fd) is not int
            or type(cwd_fd) is not int
            or executable_fd < 0
            or cwd_fd < 0
            or type(argv) not in {tuple, list}
            or not argv
            or any(type(value) is not str or "\x00" in value for value in argv)
            or type(env) is not dict
            or any(type(key) is not str or type(value) is not str for key, value in env.items())
        ):
            raise ProcessDomainError("process-domain-launch-spec-invalid")
        try:
            executable_metadata = os.fstat(executable_fd)
            cwd_metadata = os.fstat(cwd_fd)
        except OSError as error:
            raise ProcessDomainError("process-domain-launch-descriptor-invalid") from error
        if (
            not stat.S_ISREG(executable_metadata.st_mode)
            or not executable_metadata.st_mode & 0o111
            or not stat.S_ISDIR(cwd_metadata.st_mode)
        ):
            raise ProcessDomainError("process-domain-launch-descriptor-invalid")
        inherited = tuple(sorted(set(pass_fds)))
        if any(type(descriptor) is not int or descriptor < 3 for descriptor in inherited):
            raise ProcessDomainError("process-domain-pass-fds-invalid")
        name, group_fd, events_fd, kill_fd, device, inode = self._create_domain()
        stdin_read = stdin_write = stdout_read = stdout_write = None
        stderr_read = stderr_write = status_read = status_write = None
        pidfd = None
        child_created = False
        try:
            stdin_read, stdin_write = os.pipe2(os.O_CLOEXEC)
            stdout_read, stdout_write = os.pipe2(os.O_CLOEXEC)
            stderr_read, stderr_write = os.pipe2(os.O_CLOEXEC)
            status_read, status_write = os.pipe2(os.O_CLOEXEC)
            pidfd_out = ctypes.c_int(-1)
            arguments = _CloneArgs()
            arguments.flags = CLONE_INTO_CGROUP | CLONE_PIDFD
            arguments.pidfd = ctypes.addressof(pidfd_out)
            arguments.exit_signal = signal.SIGCHLD
            arguments.cgroup = group_fd
            result = _libc().syscall(
                SYS_CLONE3_X86_64,
                ctypes.byref(arguments),
                ctypes.sizeof(arguments),
            )
            if result == -1:
                raise ProcessDomainError("clone3-atomic-enrollment-failed")
            if result == 0:
                for descriptor in (stdin_write, stdout_read, stderr_read, status_read):
                    os.close(descriptor)
                self._child_exec(
                    executable_fd=executable_fd,
                    argv=tuple(argv),
                    cwd_fd=cwd_fd,
                    env=dict(env),
                    pass_fds=inherited,
                    stdin_fd=stdin_read,
                    stdout_fd=stdout_write,
                    stderr_fd=stderr_write,
                    status_fd=status_write,
                )
                os._exit(127)
            child_created = True
            pidfd = int(pidfd_out.value)
            if pidfd < 0:
                raise ProcessDomainError("clone-pidfd-unavailable")
            for descriptor_name in (
                "stdin_read",
                "stdout_write",
                "stderr_write",
                "status_write",
            ):
                descriptor = locals()[descriptor_name]
                os.close(descriptor)
                if descriptor_name == "stdin_read":
                    stdin_read = None
                elif descriptor_name == "stdout_write":
                    stdout_write = None
                elif descriptor_name == "stderr_write":
                    stderr_write = None
                else:
                    status_write = None
            poller = select.poll()
            poller.register(status_read, select.POLLIN | select.POLLHUP)
            if not poller.poll(int(BOOTSTRAP_TIMEOUT_SECONDS * 1000)):
                raise ProcessDomainError("child-bootstrap-timeout")
            marker = os.read(status_read, 1)
            os.close(status_read)
            status_read = None
            if marker:
                raise ProcessDomainError("child-bootstrap-failed")
            process = _RealDomainProcess(
                supervisor=self,
                purpose=purpose,
                stdin=os.fdopen(stdin_write, "wb", buffering=0),
                stdout=os.fdopen(stdout_read, "rb", buffering=0),
                stderr=os.fdopen(stderr_read, "rb", buffering=0),
                pidfd=pidfd,
                group_fd=group_fd,
                events_fd=events_fd,
                kill_fd=kill_fd,
                group_name=name,
                group_device=device,
                group_inode=inode,
            )
            stdin_write = stdout_read = stderr_read = pidfd = None
            group_fd = events_fd = kill_fd = None
            self._active = process
            return process
        except BaseException as error:
            for descriptor in (
                stdin_read,
                stdin_write,
                stdout_read,
                stdout_write,
                stderr_read,
                stderr_write,
                status_read,
                status_write,
            ):
                if descriptor is not None:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass
            self._unsafe = True
            cleanup_verified = False
            try:
                if child_created:
                    if kill_fd is None or events_fd is None:
                        raise ProcessDomainError(
                            "process-domain-launch-cleanup-unavailable"
                        )
                    if os.write(kill_fd, b"1") != 1:
                        raise ProcessDomainError("cgroup-kill-failed")
                    if pidfd is None or pidfd < 0:
                        raise ProcessDomainError("pidfd-ownership-unavailable")
                    poller = select.poll()
                    poller.register(pidfd, select.POLLIN)
                    if not poller.poll(int(DOMAIN_EMPTY_TIMEOUT_SECONDS * 1000)):
                        raise ProcessDomainError("direct-child-wait-timeout")
                    try:
                        os.waitid(os.P_PIDFD, pidfd, os.WEXITED)
                    except ChildProcessError:
                        pass
                    deadline = time.monotonic() + DOMAIN_EMPTY_TIMEOUT_SECONDS
                    while _parse_cgroup_events(os.pread(events_fd, 4096, 0)):
                        if time.monotonic() >= deadline:
                            raise ProcessDomainError(
                                "process-domain-populated-timeout"
                            )
                        time.sleep(0.005)
                    self._reap_adopted_descendants()
                elif events_fd is not None and _parse_cgroup_events(
                    os.pread(events_fd, 4096, 0)
                ):
                    raise ProcessDomainError(
                        "process-domain-unexpected-population"
                    )
                current = os.stat(
                    name,
                    dir_fd=self.parent_fd,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISDIR(current.st_mode)
                    or (current.st_dev, current.st_ino) != (device, inode)
                ):
                    raise ProcessDomainError(
                        "process-domain-removal-identity-drift"
                    )
                for descriptor in (kill_fd, events_fd, group_fd):
                    if descriptor is not None:
                        os.close(descriptor)
                kill_fd = events_fd = group_fd = None
                os.rmdir(name, dir_fd=self.parent_fd)
                try:
                    os.stat(
                        name,
                        dir_fd=self.parent_fd,
                        follow_symlinks=False,
                    )
                except FileNotFoundError:
                    cleanup_verified = True
            except (OSError, ProcessDomainError):
                cleanup_verified = False
            finally:
                if pidfd is not None:
                    try:
                        os.close(pidfd)
                    except OSError:
                        pass
                for descriptor in (kill_fd, events_fd, group_fd):
                    if descriptor is not None:
                        try:
                            os.close(descriptor)
                        except OSError:
                            pass
            if cleanup_verified:
                if child_created:
                    self._outcomes.append(
                        ProcessDomainOutcome(
                            purpose=purpose,
                            atomic_enrollment_verified=True,
                            direct_child_pidfd_verified=True,
                            termination_required=True,
                            complete_domain_termination_verified=True,
                            domain_empty_verified=True,
                            descendant_reaping_verified=True,
                            domain_removal_verified=True,
                        )
                    )
                self._unsafe = False
            if isinstance(error, ProcessDomainError):
                raise
            raise ProcessDomainError("process-domain-launch-failed") from error

    def _wait_empty(self, process: _RealDomainProcess) -> None:
        deadline = time.monotonic() + DOMAIN_EMPTY_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if not self._read_populated(process):
                return
            time.sleep(0.005)
        raise ProcessDomainError("process-domain-populated-timeout")

    @staticmethod
    def _reap_adopted_descendants() -> None:
        """Reap until the dedicated supervisor has no child of any kind.

        A single nonblocking miss is not a proof: an exiting descendant can
        have left the cgroup before it becomes waitable.  The real observer is
        deliberately single-threaded and is the sole child-process owner while
        this supervisor is active, so ``ECHILD`` is the closed reap proof.
        """

        deadline = time.monotonic() + DOMAIN_EMPTY_TIMEOUT_SECONDS
        while True:
            try:
                status = os.waitid(os.P_ALL, 0, os.WEXITED | os.WNOHANG)
            except ChildProcessError:
                return
            if status is not None:
                continue
            if time.monotonic() >= deadline:
                raise ProcessDomainError("process-domain-descendant-reap-timeout")
            time.sleep(0.005)

    def _remove_domain(self, process: _RealDomainProcess) -> None:
        self._verify_parent()
        try:
            current = os.stat(
                process.group_name,
                dir_fd=self.parent_fd,
                follow_symlinks=False,
            )
        except OSError as error:
            raise ProcessDomainError("process-domain-removal-identity-missing") from error
        if (
            not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino)
            != (process.group_device, process.group_inode)
        ):
            raise ProcessDomainError("process-domain-removal-identity-drift")
        for descriptor in (process.kill_fd, process.events_fd, process.group_fd):
            os.close(descriptor)
        process.kill_fd = process.events_fd = process.group_fd = -1
        try:
            os.rmdir(process.group_name, dir_fd=self.parent_fd)
        except OSError as error:
            raise ProcessDomainError("process-domain-removal-failed") from error
        try:
            os.stat(process.group_name, dir_fd=self.parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        raise ProcessDomainError("process-domain-removal-unverified")

    def _complete(
        self, process: DomainProcess, *, terminate: bool
    ) -> ProcessDomainOutcome:
        if type(process) is not _RealDomainProcess or self._active is not process:
            self._unsafe = True
            raise ProcessDomainError("process-domain-ownership-drift")
        termination_required = terminate
        termination_verified = False
        try:
            if terminate:
                self._write_kill(process)
                termination_verified = True
            if process.poll() is None and not terminate:
                raise ProcessDomainError("process-domain-completion-before-leader-exit")
            if not process.direct_reaped:
                process.wait(timeout=DOMAIN_EMPTY_TIMEOUT_SECONDS)
            if self._read_populated(process):
                termination_required = True
                self._write_kill(process)
                termination_verified = True
            self._wait_empty(process)
            self._reap_adopted_descendants()
            self._remove_domain(process)
            os.close(process.pidfd)
            process.pidfd = -1
            outcome = ProcessDomainOutcome(
                purpose=process.purpose,
                atomic_enrollment_verified=True,
                direct_child_pidfd_verified=True,
                termination_required=termination_required,
                complete_domain_termination_verified=(
                    not termination_required or termination_verified
                ),
                domain_empty_verified=True,
                descendant_reaping_verified=True,
                domain_removal_verified=True,
            )
            self._record(process, outcome)
            return outcome
        except BaseException:
            self._unsafe = True
            raise

    def close(self) -> None:
        if self._closed:
            return
        if self._active is not None:
            try:
                self._active.complete(terminate=True)
            except BaseException:
                self._unsafe = True
        if not self.safe_for_filesystem_cleanup:
            self._unsafe = True
            raise ProcessDomainError("process-domain-close-before-empty")
        if _libc().prctl(
            PR_SET_CHILD_SUBREAPER, self.old_subreaper, 0, 0, 0
        ) != 0:
            self._unsafe = True
            raise ProcessDomainError("child-subreaper-restore-failed")
        try:
            os.close(self.parent_fd)
        except OSError as error:
            self._unsafe = True
            raise ProcessDomainError("process-domain-parent-close-failed") from error
        self.parent_fd = -1
        if self._lock_held:
            self._lock_held = False
            _REAL_SUPERVISOR_LOCK.release()
        self._closed = True


class DeterministicProcessDomainSupervisor(BaseProcessDomainSupervisor):
    """Fail-closed fake backend with deterministic phase injection."""

    mechanism = TEST_MECHANISM
    availability = "simulated-fake-validation"
    test_only = True

    def __init__(self, *, failure_phase: str | None = None) -> None:
        super().__init__()
        self.failure_phase = failure_phase
        self.launch_attempts = 0
        self.events: list[str] = []

    def _fail(self, phase: str, code: str) -> None:
        if self.failure_phase == phase:
            if phase not in {
                "capability-unavailable",
                "domain-create",
                "preexisting-domain",
                "already-populated",
                "clone-into-cgroup",
                "clone-pidfd",
                "clone3",
                "pidfd",
            }:
                self._unsafe = True
            raise ProcessDomainError(code)

    def launch(
        self,
        *,
        purpose: str,
        executable_fd: int,
        argv: Sequence[str],
        cwd_fd: int,
        env: Mapping[str, str],
        pass_fds: Sequence[int],
        popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    ) -> DomainProcess:
        self._before_launch(purpose)
        self.launch_attempts += 1
        domain = self.launch_attempts
        self.events.append(f"domain-create:{domain}:{purpose}")
        for phase, code in (
            ("capability-unavailable", "process-domain-capability-unavailable"),
            ("domain-create", "process-domain-create-failed"),
            ("preexisting-domain", "process-domain-preexisting"),
            ("already-populated", "process-domain-already-populated"),
            ("clone-into-cgroup", "clone-into-cgroup-unavailable"),
            ("clone-pidfd", "clone-pidfd-unavailable"),
            ("clone3", "clone3-atomic-enrollment-failed"),
            ("pidfd", "pidfd-ownership-unavailable"),
        ):
            self._fail(phase, code)
        # The deterministic backend exposes the same ordering contract as the
        # kernel path: enrollment is complete before any caller-supplied
        # process factory can run executable code.
        self.events.append(f"atomic-enrollment:{domain}:{purpose}")
        for phase, code in (
            ("bootstrap", "child-bootstrap-failed"),
            ("exec", "child-exec-failed"),
        ):
            if self.failure_phase == phase:
                self.events.extend(
                    (
                        f"domain-kill:{domain}:{purpose}",
                        f"domain-empty:{domain}:{purpose}",
                        f"descendants-reaped:{domain}:{purpose}",
                        f"domain-removed:{domain}:{purpose}",
                    )
                )
                self._outcomes.append(
                    ProcessDomainOutcome(
                        purpose=purpose,
                        atomic_enrollment_verified=True,
                        direct_child_pidfd_verified=True,
                        termination_required=True,
                        complete_domain_termination_verified=True,
                        domain_empty_verified=True,
                        descendant_reaping_verified=True,
                        domain_removal_verified=True,
                    )
                )
                raise ProcessDomainError(code)
        child_env = dict(env)
        child_env["AXIOM_FAKE_PROCESS_DOMAIN"] = "deterministic-enrolled"
        try:
            process = popen_factory(
                list(argv),
                executable=f"/proc/self/fd/{executable_fd}",
                pass_fds=tuple(sorted({executable_fd, *pass_fds})),
                cwd=f"/proc/self/fd/{cwd_fd}",
                env=child_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except BaseException as error:
            self._unsafe = True
            raise ProcessDomainError("test-process-launch-failed") from error
        wrapped = _DeterministicDomainProcess(
            supervisor=self,
            purpose=purpose,
            process=process,
            domain_index=domain,
        )
        self._active = wrapped
        return wrapped

    def _complete(
        self, process: DomainProcess, *, terminate: bool
    ) -> ProcessDomainOutcome:
        if type(process) is not _DeterministicDomainProcess or self._active is not process:
            self._unsafe = True
            raise ProcessDomainError("process-domain-ownership-drift")
        termination_required = terminate or self.failure_phase == "descendant-active"
        domain = process.domain_index
        try:
            if terminate and process.poll() is None:
                self._fail("kill", "cgroup-kill-failed")
                self.events.append(f"domain-kill:{domain}:{process.purpose}")
                process.process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.process.kill()
                    process.wait()
            elif process.poll() is None:
                raise ProcessDomainError("process-domain-completion-before-leader-exit")
            if self.failure_phase == "descendant-active":
                self.events.append(f"domain-kill:{domain}:{process.purpose}")
            self._fail("pidfd-wait", "pidfd-wait-failed")
            self._fail("events-read", "cgroup-events-read-failed")
            self._fail("events-malformed", "cgroup-events-malformed")
            self._fail("populated-timeout", "process-domain-populated-timeout")
            self._fail("descendant-reap", "process-domain-descendant-reap-failed")
            self._fail("ownership-drift", "process-domain-removal-identity-drift")
            self._fail("domain-remove", "process-domain-removal-failed")
            outcome = ProcessDomainOutcome(
                purpose=process.purpose,
                atomic_enrollment_verified=True,
                direct_child_pidfd_verified=True,
                termination_required=termination_required,
                complete_domain_termination_verified=True,
                domain_empty_verified=True,
                descendant_reaping_verified=True,
                domain_removal_verified=True,
            )
            self.events.extend(
                (
                    f"domain-empty:{domain}:{process.purpose}",
                    f"descendants-reaped:{domain}:{process.purpose}",
                    f"domain-removed:{domain}:{process.purpose}",
                )
            )
            self._record(process, outcome)
            return outcome
        except BaseException:
            self._unsafe = True
            if process.poll() is None:
                try:
                    process.process.kill()
                    process.wait(timeout=1)
                except (OSError, subprocess.SubprocessError, TimeoutError):
                    pass
            raise


def run_current_host_synthetic_probe(
    *, cwd: Path, executable: Path = Path(sys.executable)
) -> dict[str, bool]:
    """Exercise the real backend with a leader-exit + setsid descendant.

    Only closed capability facts are returned.  PID values, cgroup names,
    paths, raw events, and child output are never part of the result.
    """

    executable_fd: int | None = None
    cwd_fd: int | None = None
    retained_fd: int | None = None
    supervisor: LinuxProcessDomainSupervisor | None = None
    process: DomainProcess | None = None
    try:
        executable = executable.resolve(strict=True)
        executable_fd = os.open(
            executable,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        metadata = os.fstat(executable_fd)
        if not stat.S_ISREG(metadata.st_mode) or not metadata.st_mode & 0o111:
            raise ProcessDomainError("synthetic-probe-executable-invalid")
        cwd_fd = os.open(cwd, _directory_flags())
        retained_fd = os.memfd_create(
            "axiom-process-domain-probe",
            getattr(os, "MFD_CLOEXEC", 0x0001),
        )
        supervisor = LinuxProcessDomainSupervisor.open()
        script = (
            "import os,signal,sys\n"
            "held=int(sys.argv[1])\n"
            "ready_read,ready_write=os.pipe()\n"
            "child=os.fork()\n"
            "if child==0:\n"
            " os.close(ready_read)\n"
            " os.setsid()\n"
            " duplicate=os.dup(held)\n"
            " os.close(held)\n"
            " os.write(ready_write,b'R')\n"
            " os.close(ready_write)\n"
            " while True: signal.pause()\n"
            "os.close(ready_write)\n"
            "marker=os.read(ready_read,1)\n"
            "os.close(ready_read)\n"
            "if marker!=b'R': os._exit(2)\n"
            "os.write(1,b'R')\n"
            "os._exit(0)\n"
        )
        process = supervisor.launch(
            purpose="synthetic-probe",
            executable_fd=executable_fd,
            argv=(str(executable), "-I", "-B", "-c", script, str(retained_fd)),
            cwd_fd=cwd_fd,
            env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "NO_COLOR": "1"},
            pass_fds=(retained_fd,),
        )
        process.stdin.close()
        leader_exited = process.wait(timeout=DOMAIN_EMPTY_TIMEOUT_SECONDS) == 0
        descendant_ready = os.read(process.stdout.fileno(), 1) == b"R"
        if type(process) is not _RealDomainProcess:
            raise ProcessDomainError("synthetic-probe-backend-invalid")
        descendant_observed = supervisor._read_populated(process)
        if not descendant_ready or not descendant_observed:
            raise ProcessDomainError("synthetic-descendant-not-observed")
        outcome = process.complete(terminate=False)
        supervisor.require_advance_barrier()
        result = {
            "leaderExited": leader_exited,
            "setsidDescendantObserved": descendant_observed,
            "retainedDescriptorDescendantObserved": descendant_ready,
            "completeDomainTerminationVerified": (
                outcome.complete_domain_termination_verified
            ),
            "domainEmptyVerified": outcome.domain_empty_verified,
            "descendantReapingVerified": outcome.descendant_reaping_verified,
            "domainRemovalVerified": outcome.domain_removal_verified,
        }
        supervisor.close()
        supervisor = None
        return result
    finally:
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass
        cleanup_error: ProcessDomainError | None = None
        if supervisor is not None:
            try:
                supervisor.close()
            except ProcessDomainError as error:
                cleanup_error = error
        for descriptor in (retained_fd, cwd_fd, executable_fd):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        if cleanup_error is not None:
            raise cleanup_error


def _write_all_descriptor(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    offset = 0
    while offset < len(view):
        written = os.write(descriptor, view[offset:])
        if type(written) is not int or written <= 0 or written > len(view) - offset:
            raise ProcessDomainError("bundle-worker-write-failed")
        offset += written


def _bundle_worker_main(arguments: Sequence[str]) -> int:
    """Fixed bundle-builder worker entered only after process-domain exec."""

    if len(arguments) != 8 or arguments[0] != "__bundle_worker_v1__":
        return 2
    try:
        repository_fd = int(arguments[1])
        destination_fd = int(arguments[2])
        source_repository = Path(arguments[3])
        source_commit = arguments[4]
        source_tree = arguments[5]
        git_executable = Path(arguments[6])
        failure_relative = None if arguments[7] == "-" else arguments[7]
        for descriptor in (repository_fd, destination_fd):
            metadata = os.fstat(descriptor)
            if not stat.S_ISDIR(metadata.st_mode):
                raise ProcessDomainError("bundle-worker-directory-fd-invalid")
        if failure_relative not in {None, ".axiom-no-hook-bundle-staging"}:
            raise ProcessDomainError("bundle-worker-test-failure-invalid")
        repository_alias = f"/proc/self/fd/{repository_fd}"
        if repository_alias not in sys.path:
            sys.path.insert(0, repository_alias)
        from axiom_validation.no_hook_bundle import build_bundle_to_directory_fd

        def test_hook(phase: str, facts: dict[str, object]) -> None:
            if (
                failure_relative is not None
                and phase == "builder-after-create-before-ledger"
                and facts.get("relativePath") == failure_relative
            ):
                raise OSError("closed-test-builder-failure")

        result = build_bundle_to_directory_fd(
            source_repository,
            source_commit,
            source_tree,
            destination_fd,
            git_executable=git_executable,
            schema_path=Path(repository_alias)
            / "evals/no-hook/bundle-manifest-schema-v1.json",
            entrypoint_path=Path(repository_alias) / "scripts/build-no-hook-bundle.py",
            module_path=Path(repository_alias)
            / "axiom_validation/no_hook_bundle.py",
            expected_destination_identity=(
                os.fstat(destination_fd).st_dev,
                os.fstat(destination_fd).st_ino,
            ),
            _test_hook=test_hook if failure_relative is not None else None,
        )
        document = {
            "schemaVersion": "1",
            "profileRuntimeDigest": result.profile_runtime_digest,
            "bundleManifestDigest": result.bundle_manifest_digest,
            "archiveSha256": result.archive_sha256,
            "creationRecords": [
                {
                    "relativePath": item.relative_path,
                    "parentRelativePath": item.parent_relative_path,
                    "basename": item.basename,
                    "kind": item.kind,
                    "device": item.device,
                    "inode": item.inode,
                    "mode": item.mode,
                    "creationPhase": item.creation_phase,
                }
                for item in result.creation_records
            ],
        }
        payload = json.dumps(
            document,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii") + b"\n"
        if len(payload) > MAX_BUNDLE_WORKER_RESULT_BYTES:
            raise ProcessDomainError("bundle-worker-result-too-large")
        _write_all_descriptor(1, payload)
        return 0
    except BaseException:
        return 1


if __name__ == "__main__":
    raise SystemExit(_bundle_worker_main(tuple(sys.argv[1:])))


def check_no_hook_linux_isolation(failures: list[str]) -> int:
    """Validate only the closed offline contract; never inspect host support."""

    try:
        contract = _combined_lifecycle_contract()
        if (set(contract["owners"]) != set(_COMBINED_PHASES)
                or set(contract["requiredFacts"]) != set(_COMBINED_PHASES)
                or contract["actualExecutionEligible"] is not False
                or set(contract["runtimeFacts"].values()) != {"not-verified"}):
            raise ProcessDomainError("combined-static-contract-invalid")
    except ProcessDomainError as error:
        failures.append(f"no-Hook Linux isolation validation failed: {error}")
        return 0
    return 1


__all__ = [
    "BaseProcessDomainSupervisor",
    "DeterministicProcessDomainSupervisor",
    "DomainProcess",
    "LinuxProcessDomainSupervisor",
    "ProcessDomainCapabilities",
    "ProcessDomainError",
    "ProcessDomainOutcome",
    "REAL_MECHANISM",
    "TEST_MECHANISM",
    "check_no_hook_linux_isolation",
    "detect_process_domain_capabilities",
    "run_current_host_synthetic_probe",
]
