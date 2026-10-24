# Host And Run Contract

## Activation

Start only from an explicit human invocation for an executable task. Discussion,
review, testing, or editing of this skill does not activate its workflow. State
the exact model, reasoning effort, execution surface, supervision mechanism,
and the circumstances in which it can run. Reuse settled user decisions.

Establish a verifiable completion condition and preserve the original request.
Clarify only unresolved choices that materially affect the outcome or authority.
Do not start an unrelated workstream merely to keep the run busy.

Confirm that existing human authority covers the host-required creation,
messaging, scheduling, and execution actions. Ask only for missing authority;
do not invent it from a worker or supervisor's instruction. No activation
authorizes publication, deployment, destructive cleanup, or unrelated changes.

## Required Host Capabilities

Confirm all of the following for this run's selected environment:

1. A durable task record readable by the coordinator, workers, and supervisor.
2. Fresh execution contexts with addressable session IDs, known working roots,
   explicit model and effort settings, and accessible result evidence.
   Verify that the chosen dispatcher can start them under its existing host
   permissions. A nested CLI also needs its normal session-store access; a
   worker sandbox may correctly prevent that. Use an already-authorized native
   dispatch facility or retain a capability wait instead of broadening access.
3. Supported creation and addressing of successor coordinators. A CLI session
   is not automatically a desktop sidebar chat. A saved ID does not prove a
   callback can reach that chat.
4. An independently owned wake mechanism that can inspect and recover the run
   after the coordinator's turn or session ends. Register it and verify its
   state before the coordinator depends on it. Record its identifier, owner,
   cadence or event source, host dependencies, and shutdown operation.
5. A way to determine session liveness and distinguish waiting, failure, and
   completion. Prefer supported host APIs; transcript formats may change.
6. A way to perform coordinator ownership changes without two active owners.
   If the host cannot enforce exclusive ownership, report that limitation.

Use the host's native scheduling and session tools where available. A heartbeat
attached only to an old coordinator is insufficient unless its survival and
retargeting behavior have been verified. Give the task one independently
addressable supervision owner. Do not install a daemon, add a startup launcher,
edit global hooks, or change host permissions as an implicit fallback.

For local scheduled work, document the actual application and machine
availability requirements. An application-owned schedule does not prove
execution after that application exits. Offline periods retain a pending task;
continuation requires the selected host to become available again.

When a required capability is unavailable, retain the task as waiting for that
capability and report exactly what could not start. If no independent wake
mechanism was registered, say that automatic recovery is unavailable. Do not
claim a supervisor is running or promise a later wakeup.

## Durable Record

Store task-owned state outside publishable output and separately from transient
chat summaries. Respect the target project's ownership and storage conventions.
Use [the run record template](../assets/run-record.json) as an output starting
point, filling observed values rather than treating nulls as established facts.

Keep at least:

- Original request, completion criteria, constraints, and authorization source.
- Status, current phase, coordinator generation and session ID, and supervisor
  owner plus scheduler ID. Keep the run ID stable across all sessions.
- Exact execution root, relevant artifacts, worker assignments and attempt IDs,
  current process or session handles, result receipts, and unresolved effects.
- Requested and observed model and effort, plus any allowed fallback.
- Evidence pointers, accepted decisions, remaining work, and the next action.
- User pause or cancellation, applicable cumulative budget accounting, waiting
  conditions, and the last successful observation of the owning host.

Write assignment intent before dispatch, then add the returned session ID and
acknowledgment. Retain completion evidence before transferring coordination.
Each worker writes its own result receipt; the active coordinator owns task
progress, while the supervisor owns coordinator transfer and scheduler state.

Use the storage mechanism's atomic update or locking facility for competing
ownership transitions. A prose instruction or an unlocked JSON file alone is
not an enforcement mechanism. An expired lease is a recovery signal; first
reconcile the prior owner and outstanding actions before assigning a successor.

Keep secrets and credentials out of run records and handoff prompts. Preserve
only references needed to use existing authorized host access.

## Model And Context Signals

Observe the current model and reasoning configuration before inheriting it.
If the exact configuration is unavailable or cannot be selected on the child
host, retain the limitation and use only a fallback the human has allowed.

Document whether the host exposes compaction events, current context usage,
and its relevant limits. Cumulative billing tokens are not current context
occupancy. A numerical handoff threshold requires a documented occupancy
signal and allowance for the next bounded step plus the handoff itself.
Without those signals, proactive rotation is best effort; do not claim precise
pre-compaction protection.
