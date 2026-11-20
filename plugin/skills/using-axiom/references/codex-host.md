# Codex Host Facts

Verified on 2026-11-20 against the installed Codex CLI 0.171.0 help output (`codex --help`, `codex exec --help`, `codex agents --help`) and OpenAI's Codex documentation as read that day; maintainer observations date to Codex CLI 0.166.0 on 2026-10-30. Items marked (docs) restate the host documentation and need a recheck on a newer version. Run `codex --help` and `codex exec --help` for the current commands and flags; this file never replaces them.

## Instructions And Skills

- Codex builds its project instruction chain once per run from the project root down to the working directory. In each directory it checks `AGENTS.override.md`, then `AGENTS.md`, then any configured fallback names, includes at most one file, and skips empty files; closer files govern scoped conflicts (docs).
- It stops adding project guidance at the visible `project_doc_max_bytes` limit, a truncation guard rather than an authoring budget. Ordinary files under `.agents/` are not auto-loaded, and the instruction guide documents no include syntax (docs).
- User instructions outrank persistent repository instructions (docs).
- Bundled skills appear in the skill list, and `$skill-name` names one explicitly. Repo-local `.agents/skills/**/SKILL.md` files may be discovered as skill metadata, which proves neither body loading nor selection (docs).
- The plugin's `SessionStart` Hook delivers the gate only after the user trusts that exact Hook entry in `/hooks`; the `features.hooks` flag must keep its default for Hooks to run. Trust binds to the hash of the declaration and the packaged script, so a changed script needs a new review.
- The hooks documentation (`https://learn.chatgpt.com/docs/hooks`, read 2026-11-20) lists `UserPromptSubmit` among its current events. It receives `prompt` and adds plain stdout as developer context. `PreCompact` and `PostCompact` ignore plain stdout and receive `turn_id` and `trigger` in addition to the common fields (docs).

## Permission And Sandbox

- The `on-request` approval policy lets the model ask before an escalated command; that native request carries the exact command, and the user's answer is the grant. Approval requests route to the user by default; with `approvals_reviewer = "auto_review"` eligible requests go to a reviewer agent instead (docs), and that review is the host's decision, not the user's grant.
- The `never` approval policy asks nobody: a failure, including a sandbox denial, returns to the model. Present the exact command to the user as a stop; do not retry it under another sandbox or policy.
- Sandbox modes such as `read-only` and `workspace-write`, Hook trust, and the approval policy are host settings; a session never changes them to make an action pass.
- Under default `workspace-write`, each writable root's `.git` file or directory is read-only, as is the Git directory a `.git` pointer resolves to. Existing `.agents`, `.codex`, and `.aws` directories there are read-only. Protection is recursive. The documentation read does not say whether a write to such a path prompts or fails (docs).
- Subagents inherit the parent turn's current sandbox and approval settings, including changes from `/permissions` or `--yolo`; a custom agent file cannot replace them. In the interactive CLI a pending approval request can surface from an inactive agent thread: the overlay names the thread, and `o` opens it before the user answers. In non-interactive runs, or whenever a fresh approval cannot be shown, an action that needs one fails and the error returns to the parent (docs).
- `/subagents` opens a picker of agent threads and switches to the selected one. The user asks Codex to steer or stop a running subagent or to close a completed thread. The documentation read does not say how a session treats a message from another agent or session with respect to the user's consent (docs).

## Running Codex From A Session

- `codex exec` runs one prompt non-interactively from arguments, a file, or stdin. `--json` prints JSONL events, `--output-schema <file>` constrains the final response, `--ephemeral` saves no session, `-s` selects the sandbox, `-c key=value` overrides configuration, and `-C <dir>` sets the working directory.
- A `codex exec` run uses a read-only sandbox by default. The documentation read does not describe a fresh `codex exec` run inheriting the launching session's approvals (docs).
- `codex exec resume`, `codex resume`, `codex fork`, and `codex queue` address saved sessions, and `codex agents` browses sessions on the shared local app-server daemon. Do not use `--ephemeral` when a later supervisor must address the session.
- Give a child session the observed model and effort, never a guessed default. Capture the real thread ID, the terminal event, the final receipt, and the artifacts separately.
- Within one session, a subagent without a configured model or reasoning effort inherits the parent's. An explicit spawn value or an `[agents]` default overrides it, and a model chosen that way without an effort uses that model's default effort (docs).
- The app-server interface is experimental: use the schema exported by the installed version, complete `initialize` and `initialized`, and keep the native IDs. It establishes no stable cross-version contract.
- Inspect unexpected startup latency before widening a deadline; marketplace refreshes can take time independently of the task.

## Scheduling, Compaction, And Cancellation

- CLI execution alone supplies no future wake-up. Use the native automation tool when the Desktop app provides one; it needs that application and machine available. Never substitute a cron job, service, hidden daemon, or startup hook.
- Observe the `contextCompaction` item and the turn lifecycle when the host exposes them; the item can complete before the turn ends, so wait for the turn to end or for an idle state before recovery input. On `ActiveTurnNotSteerable`, observe that turn until it ends, then submit once.
- To cancel, persist control first, stop new dispatch, disable the exact schedule, and interrupt the exact active turn. Observe its terminal status and the command handles it started; never kill a process by a PID copied from a sandbox or another host.
