# Execution And Handoff

## Coordinate One Step

1. Read the original goal, the current run record, and the authoritative state
   of outstanding work. Confirm this session still owns the recorded generation.
2. Check whether the whole request is already satisfied. Reuse still-current
   conclusive evidence; repeat checks only after relevant changes or failure.
3. Select one bounded next assignment and define its expected output and
   verification. Record the assignment and attempt ID before sending it.
4. Start a fresh worker using the supported host facility and authorized model
   configuration. Supply the scope, working root, relevant evidence, constraints,
   and exact return destination. Feed prompts through structured arguments or
   literal files; never interpolate retrieved text into shell source.
   Bound the worker's turns and budget where the host allows it, and never
   widen its permissions or tools to make it finish; a cap that stops the run
   also stops its background subagents.
5. Record the actual session ID. Observe completion through host events or a
   bounded wait. A successful launch, zero exit code, or fluent response is
   insufficient evidence that the requested work succeeded.
   A timeout or nonzero exit also does not erase a persisted result. Reconcile
   receipts, actual artifacts, and outstanding operations before deciding to
   retry or classify the run as waiting.
   Keep the native command or turn handle while work is active. Do not stack
   short wall-clock wrappers around nested model calls: startup, tools, and
   model latency belong in the observed wait budget. A real deadline triggers
   native interruption and reconciliation, not an assumed rollback.
6. Inspect the result and relevant artifacts against the assignment. Record
   verified work and remaining uncertainty. If the overall outcome remains
   unfinished, choose the next fresh worker or transfer coordination as needed.

Apply the specialized workflow owners for each assignment before its actions.
The progress protocol does not replace their authorization or verification.
Keep each worker's authority inside its assignment. Workers return partial
results and blockers rather than creating more coordinators or supervisors.
Use separate worktrees when the target project requires them. Do not allow
concurrent workers to modify the same files without an explicit integration
owner and conflict strategy.

## Prepare A Coordinator Transfer

Trigger a transfer at a supported context threshold, an observed compaction
event, a planned stage boundary, or supervisor recovery of an ended coordinator.
On a context warning, enter handoff promptly and finish the transfer at the
next safe boundary. Record in-flight operations before doing anything else.

Prepare a compact handoff packet containing:

- Run ID, predecessor ID, generation, transfer ID, and role of the successor.
- Original outcome, constraints, completion criteria, and human authority.
- Durable record location, actual execution root, and current worker handles.
- Verified results with evidence pointers, unresolved operations, and next step.
- Model and effort, remaining applicable budgets, and pause or cancel state.

Start the successor with a fresh context and these references. Forking an entire
history may retain the context pressure that prompted the transfer; use a fork
only for a separately justified need to preserve that history.

## Transfer Ownership

The supervisor serializes coordinator changes for this run:

1. Record a pending transfer and the predecessor's current generation.
2. Reconcile any earlier creation attempt using returned IDs and host state.
   A lost acknowledgment does not establish that creation failed.
3. Create at most one successor for the transfer, record its ID, and wait for
   an acknowledgment that it read the durable record and accepted the role.
4. Activate the successor by an exclusive ownership transition. The successor
   must verify its generation immediately before dispatching or mutating work.
5. Retire the predecessor's dispatch authority and update the supervisor's
   current target. Retain old evidence; do not delete other chats or worktrees.

If the predecessor has already ended, the supervisor reconstructs the packet
from the durable record and current host state. If acknowledgment is missing,
inspect the known successor before retrying. If status cannot be reconciled,
retain an unresolved transfer and wait for the missing evidence rather than
starting competing writers.

## Compaction

Save progress at meaningful boundaries throughout execution. Do not depend on
receiving one final chance to summarize before compaction.

When the host exposes a pre-compaction event, promptly record the transfer
intent and outstanding work through the authorized runtime mechanism. Do not
modify global or startup hooks merely to manufacture this capability.

After an observed compaction, re-read the original request, run record,
applicable instructions, current coordinator ownership, and referenced evidence.
Reconcile in-flight operations, then initiate the fresh-coordinator transfer.
Only recovery and handoff work continues in the compacted predecessor; normal
dispatch belongs to the verified owner. A summary alone cannot reestablish
permissions, successful side effects, or completion.

Wait for the host's compaction turn to finish before submitting recovery input.
A compaction event can complete before its turn ends. If the host rejects input
while a turn is still active, preserve the pending recovery, observe the same
turn until it ends, then submit once. Do not create a second coordinator or
treat the rejected input as an accepted handoff. The current host's facts in
the startup gate's references name its compaction and turn signals.

If a compaction signal is missing, record that observation limit. Neither
static schema support nor a manually triggered CLI compaction proves automatic
desktop compaction handling.
