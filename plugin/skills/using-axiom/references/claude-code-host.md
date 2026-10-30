# Claude Code Host Facts

Verified against Claude Code 2.1.308 on 2026-10-30 from its installed help output and sessions the maintainers observed. Items marked (docs) restate the host documentation as read for that release and need a recheck on a newer version. Run `claude --help` for the current commands and flags; this file never replaces it.

## Instructions And Skills

- At session start Claude Code loads a managed policy file, `~/.claude/CLAUDE.md`, and every `CLAUDE.md` and `CLAUDE.local.md` from the working directory upward; a project may keep its file at `.claude/CLAUDE.md`. Files concatenate root-down, so closer guidance loads later (docs).
- Subdirectory instruction files load on demand when Claude works with a file there; their presence does not prove loading. After compaction it rereads the project-root file, and nested files and path-scoped rules load again on demand (docs).
- From 2.1.277 it reads `AGENTS.md` and `.claude/AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` exists in the working directory or above it; the Project instructions setting can change that. It never reads `AGENTS.override.md`, `AGENTS.local.md`, or files under `.agents/` (docs).
- `@path` imports expand up to four hops from the importing file; `.claude/rules/` files without `paths` frontmatter load at session start; `claudeMdExcludes` skips files; `--add-dir` directories contribute instruction files only when configured (docs).
- `/context` lists the instruction files the session loaded under Memory files; `/memory` also lists locations that do not exist yet (docs).
- Plugin skills appear in the skill list as `axiom:<skill-name>`, and `/axiom:skill-name` invokes one. The plugin's `SessionStart` Hook delivers the gate at session start and again after compaction with `source` set to `compact`; `/reload-plugins` applies plugin changes without rerunning it.

## Permission Modes

- `default` (Manual) prompts natively before a tool call that needs approval; the answer is the grant.
- `auto` runs without routine prompts and has a classifier check each action against the conversation, so present the exact command and target first. A classifier denial is a stop; the user may run the command natively or grant it again.
- `bypassPermissions` is the permission-bypass mode and waives no Axiom boundary. `dontAsk` denies every call that would prompt and is not a grant. `--allowedTools` and `--disallowedTools` bound a run within the user's authority; never widen them to finish.

## Running Claude Code From A Session

- `claude -p` runs one prompt from arguments, a file, or stdin; `--output-format json` or `stream-json` returns the result with its `session_id`, and `--input-format stream-json` continues the same thread.
- `--model` and `--effort` pass the observed settings to a child; `--max-turns` and `--max-budget-usd` bound it, and a cap that stops the run also stops its background subagents.
- `--resume <id>` continues a saved session and `--fork-session` gives the successor a new identity; `--no-session-persistence` saves nothing; `--bare` skips hooks, plugins, and project instructions and binds no inbox. `--plugin-dir` loads a plugin for one invocation, and `--settings` can disable an installed one.
- `claude --bg` starts a background session, which `claude agents`, `attach`, `logs`, `respawn`, and `stop` manage. A `done` state means the last turn ended, not that the assignment succeeded. Exit code 143 after SIGTERM is an unfinished turn; send SIGINT first.
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` turns off auto memory for a run that must leave no trace.

## Scheduling, Messaging, Compaction, And Cancellation

- Session-scoped `CronCreate` tasks and `/loop` fire only while their session runs and is idle, expire after seven days, and do not catch up on missed fires; `/goal` keeps one session working and is not a supervisor (docs).
- An independent wake comes only from a Desktop scheduled task (this machine, app open), a cloud scheduled task (fresh clone, one-hour minimum, no local files), or a GitHub Actions schedule (docs). Without one, no independent wake mechanism exists; never substitute a cron job, service, daemon, or startup hook.
- `ListAgents` discovers live local sessions and `SendMessage` delivers plain text; `notify_when_idle` requests one notice when a session next goes idle. A receiver's `crossSessionInbound` setting may hold or refuse a message, and a held message is not a delivered handoff (docs).
- `PreCompact` and `PostCompact` hooks bracket compaction. Manual `/compact` proves that path only; automatic compaction needs its own observation.
- To cancel, persist control first, stop new dispatch, disable the exact wake mechanism, then stop the active work: `claude stop <id>` for a background session, SIGINT for a foreground run, and the owning tool's cancel for subagents.
