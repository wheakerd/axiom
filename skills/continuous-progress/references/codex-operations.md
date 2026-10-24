# Codex Operations

Use this reference only when binding a run to actual Codex host capabilities.
Inspect the installed CLI help, exported app-server schema, and available app
tools before selecting operations. Preserve authentication, permissions, model,
effort, project instructions, and applicable execution rules.

## Fresh Execution

Use `codex exec` or the supported native session API. Supply prompts through
literal files, stdin, or structured inputs. Capture the real thread ID, native
terminal event, final receipt, and actual artifacts separately. Do not use
`--ephemeral` when a later supervisor must address the saved session.

A child inherits the observed model and effort, not a guessed default. Verify
the effective configuration on the selected host. CLI and Desktop addressability
must be tested: a locally saved CLI ID is not proof that Desktop can resume it.

Inspect unexpected startup latency before widening deadlines. Host marketplace
refreshes can consume time independently of the task. An invocation-scoped
`--disable plugins` is suitable only for a deliberately bounded worker that
does not need plugin capabilities and receives its full assignment and required
protocol. Do not use it for a supervisor that needs app tools, as an implicit
production default, or to remove applicable instructions. Never change global
configuration, hook trust, approval policy, or authentication to make a test pass.

For app-server clients, use the schema exported by the installed version.
Complete `initialize` and `initialized`, retain native IDs, and consume the
event stream without losing buffered messages. Treat transport or observer
failures separately from failures of the task. An experimental app-server
interface does not establish a stable cross-version runtime contract.

## Independent Supervisor

Use the native automation tool when available. Register a heartbeat against an
independently addressable supervisor, not the rotating coordinator. Keep its
target fixed; the durable record identifies the current coordinator. Verify the
registration, exact target, active state, and an actual scheduled wake before
depending on recovery. No manual message can stand in for a scheduled wake.

The saved prompt must state the run-record location, original scope, model and
effort, control check, reconciliation rules, exclusive ownership mechanism, and
exact shutdown operation. Every wake rereads that record and current host state.
Stay quiet unless recovery, completion, failure, or required user action changes
the situation. The heartbeat must not recursively create another supervisor.

Inspect an existing matching schedule before creating one. Use the returned
automation ID for all later operations. When updating, preserve the complete
existing fields unless the run requires a change. Use native view plus readable
stored state or an equivalent supported read to verify shutdown; a rendered
card or the model's statement alone is not a terminal-state observation.

Local scheduling requires its owning application and machine to be available.
Do not substitute a cron job, service, hidden daemon, or startup hook when native
scheduling is unavailable. CLI execution by itself supplies no future wakeup.

## Compaction And Cancellation

Observe `contextCompaction` and the associated native turn lifecycle when the
host exposes them. The item can complete before the compaction turn. Wait for
the turn to end or verify an idle host state before recovery input. If input is
rejected with `ActiveTurnNotSteerable`, observe the same turn until it ends, then
submit once. Then reread
the original durable request and constraints, reconcile work, and transfer to a
fresh coordinator. Manual compaction proves that path only; automatic context
pressure, a numerical reserve, and another host need their own observations.

For user cancellation, persist control first, stop new dispatch, disable the
exact schedule, and interrupt the exact active native turn. Observe both the
turn's terminal status and the command handles it started. Cooperatively
cancel task-owned workers where supported and verify their effects have stopped.
Do not kill a process by a PID copied from a sandbox or another host. If native
handles cannot drain, identify the unresolved operation and retain cleanup
pending without restarting the task.

## Acceptance Evidence

Record the host version and distinguish: scheduled wake after coordinator exit;
recovery of a failed handoff; native worker and successor completion; actual
compaction and durable reread; cancellation of active work; and observed schedule
shutdown after both completion and cancellation. Keep failed observations and
measurement corrections. Never convert a correct artifact into proof that the
supervisor finished, or a stopped schedule into proof that all work stopped.
