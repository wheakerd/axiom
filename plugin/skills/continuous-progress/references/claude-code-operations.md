# Claude Code Operations

Use this reference only when binding a run to actual Claude Code host
capabilities. Inspect `claude --version`, the installed CLI help, and the
tools available in this session before selecting operations. Preserve
authentication, permission mode, model, effort, project instructions, and
applicable execution rules. Several facilities below are research previews;
confirm each one on the installed version before depending on it.

## Fresh Execution

Start a worker with `claude -p` and a prompt supplied through a literal file,
stdin, or structured input. Use `--output-format json` or `stream-json` and
record the returned `session_id`; pass `--session-id` only with a fresh UUID.
Do not use `--no-session-persistence` when a later coordinator or supervisor
must address the saved session. Use `--bare` only for a deliberately bounded
worker that needs no plugin, hook, or project instruction and receives its
full assignment and protocol in the prompt.

A child inherits the observed model and effort through `--model` and
`--effort`, not a guessed default. Bound a worker with `--max-turns` and
`--max-budget-usd` where the assignment allows; a cap that stops the run also
stops its background subagents. `--permission-mode` and `--allowedTools` must
stay within the human's existing authority; never widen them to make a worker
finish.

A background session started with `claude --bg`, or converted with `/bg`,
runs under the local supervisor process. `claude agents --json --all` lists
its short ID, full session ID, and `working`, `blocked`, `done`, `failed`, or
`stopped` state; `claude logs`, `claude attach`, `claude respawn`, and
`claude stop` operate on that ID. A `done` state means the last turn ended,
not that the assignment succeeded. Reboot or shutdown stops these sessions;
their conversations stay resumable.

Treat exit code `143` after SIGTERM as an unfinished turn with no recorded
result. Send SIGINT first when the turn should end cleanly.

## Independent Supervisor

Session-scoped scheduling is not independent. `CronCreate` tasks and `/loop`
fire only while their session runs and is idle, expire after seven days, do
not catch up on missed fires, and a self-paced loop is not restored on
resume. A session-scoped task may pace a coordinator's own waits, but it
cannot recover a run after that coordinator ends.

Select the independent wake mechanism from what the host actually provides:

- A Desktop scheduled task runs on this machine with local file access while
  the Desktop app is open and the computer is awake. It keeps one stable task
  folder, runs at most one catch-up for a missed window, and can adjust its
  own schedule through `update_scheduled_task`.
- A cloud scheduled task runs without this machine on a fresh repository
  clone with a one-hour minimum interval. It cannot read local run records or
  files; use it only when the run record and work live in the repository or
  another reachable service.
- A GitHub Actions schedule is an alternative for repository-resident work.

When none of these mechanisms is available, no independent wake mechanism
exists. Retain the task as waiting for that capability and say so; do not substitute a cron job,
service, daemon, or startup hook. `/goal` keeps one session working toward a
condition and is restored on resume, but it is not a supervisor and runs no
turn while its session is closed.

Register the chosen mechanism against the run record, not the rotating
coordinator. Verify its identifier, schedule, enabled state, and an actual
wake before depending on recovery. A `SendMessage` turn or other manual
message cannot stand in for a scheduled wake.

The task's saved prompt must state the run-record location, original scope,
model and effort, control check, reconciliation rules, exclusive ownership
mechanism, and exact shutdown operation. Every run rereads that record and
current host state. A scheduled run must not create another supervisor or
wake mechanism, and it changes its own schedule or prompt through
`update_scheduled_task` only when the run record calls for that change.

Check for an existing task for this run before creating one, and address that
same task in every later operation. When editing it, keep every existing
setting unless the run requires a change. Verify shutdown through the owning
surface: `CronDelete` for a session task, the Desktop task page or
`update_scheduled_task` for a Desktop task, or `/schedule update` and the web
task page for a cloud task. The model's statement alone is not a
terminal-state observation.

## Coordinator Addressing

Use cross-session messaging to reach a live coordinator or worker on this
machine: `ListAgents` discovers sessions and `SendMessage` delivers plain
text. An idle receiving session starts a new turn; a busy one reads the message
between tool calls. `notify_when_idle` requests one notice when a watched local
session next goes idle. The receiver's `crossSessionInbound` setting and
permission-mode class may hold or refuse a message; a held message is not a
delivered handoff. A `--bare` session binds no inbox and cannot be reached.

Resume an ended coordinator with `claude --resume <session-id>`; use
`--fork-session` when the successor needs a new identity. A saved ID proves a
transcript exists, not that a process is alive.

## Compaction And Cancellation

`PreCompact` and `PostCompact` hooks bracket compaction, and `SessionStart`
runs again with `source` set to `compact`. On `resume`, hook input may carry
`context_tokens`. After an observed compaction, reread the durable request and
run record before recovery input. Manual `/compact` proves that path only;
automatic compaction needs its own observation.

For user cancellation, persist control first, stop new dispatch, disable the
exact wake mechanism, then stop the active work: `claude stop <id>` for a
background session, SIGINT for a foreground `claude -p` run, and the owning
tool's cancel for subagents. Observe the terminal state and any command
handles the session started. If a handle cannot be stopped or observed,
retain cleanup pending and name it.

## Acceptance Evidence

Record the Claude Code version and distinguish: a scheduled wake after the
coordinator exited; recovery of a failed handoff; worker and successor
completion with session IDs; actual compaction and durable reread;
cancellation of active work; and observed scheduler shutdown after both
completion and cancellation. A UI status, a green run indicator, or the
model's own statement is not a terminal-state observation.
