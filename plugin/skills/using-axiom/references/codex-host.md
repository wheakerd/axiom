# Codex Host Facts

Verified against Codex CLI 0.166.0 on 2026-10-30 from its installed help output and sessions the maintainers observed. Items marked (docs) restate the host documentation as read for that release and need a recheck on a newer version. Run `codex --help` and `codex exec --help` for the current commands and flags; this file never replaces them.

## Instructions And Skills

- Codex builds its project instruction chain once per run from the `AGENTS.md` files between the project root and the working directory; closer files govern scoped conflicts (docs).
- It stops adding project guidance at the visible `project_doc_max_bytes` limit, a truncation guard rather than an authoring budget. Ordinary files under `.agents/` are not auto-loaded, and there is no include syntax (docs).
- User instructions outrank persistent repository instructions (docs).
- Bundled skills appear in the skill list, and `$skill-name` names one explicitly. Repo-local `.agents/skills/**/SKILL.md` files may be discovered as skill metadata, which proves neither body loading nor selection (docs).
- The plugin's `session_start` Hook delivers the gate only after the user trusts that exact Hook entry in `/hooks`; the `features.hooks` flag must keep its default for Hooks to run.

## Permission And Sandbox

- The `on-request` approval policy lets the model ask before an escalated command; that native request carries the exact command, and the user's answer is the grant.
- The `never` approval policy asks nobody: a failure, including a sandbox denial, returns to the model. Present the exact command to the user as a stop; do not retry it under another sandbox or policy.
- Sandbox modes such as `read-only` and `workspace-write`, Hook trust, and the approval policy are host settings; a session never changes them to make an action pass.

## Running Codex From A Session

- `codex exec` runs one prompt non-interactively from arguments, a file, or stdin. `--json` prints JSONL events, `--output-schema <file>` constrains the final response, `--ephemeral` saves no session, `-s` selects the sandbox, `-c key=value` overrides configuration, and `-C <dir>` sets the working directory.
- `codex exec resume`, `codex resume`, `codex fork`, and `codex queue` address saved sessions, and `codex agents` browses sessions on the shared local app-server daemon. Do not use `--ephemeral` when a later supervisor must address the session.
- A child session inherits the observed model and effort, never a guessed default. Capture the real thread ID, the terminal event, the final receipt, and the artifacts separately.
- The app-server interface is experimental: use the schema exported by the installed version, complete `initialize` and `initialized`, and keep the native IDs. It establishes no stable cross-version contract.
- Inspect unexpected startup latency before widening a deadline; marketplace refreshes can take time independently of the task.

## Scheduling, Compaction, And Cancellation

- CLI execution alone supplies no future wake-up. Use the native automation tool when the Desktop app provides one; it needs that application and machine available. Never substitute a cron job, service, hidden daemon, or startup hook.
- Observe the `contextCompaction` item and the turn lifecycle when the host exposes them; the item can complete before the turn ends, so wait for the turn to end or for an idle state before recovery input. On `ActiveTurnNotSteerable`, observe that turn until it ends, then submit once.
- To cancel, persist control first, stop new dispatch, disable the exact schedule, and interrupt the exact active turn. Observe its terminal status and the command handles it started; never kill a process by a PID copied from a sandbox or another host.
