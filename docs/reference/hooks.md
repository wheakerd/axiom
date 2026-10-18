# Hook Reference

Plugin Hooks execute commands inside the host session. Inspect the installed
definition in `/hooks` before trusting it and stop if it differs from the
checked-in source.

The canonical sources are
[`hooks/codex-hooks.json`](../../hooks/codex-hooks.json), the packaged
[`hooks/codex-session-start.cmd`](../../hooks/codex-session-start.cmd) wrapper,
and [`hooks/claude-hooks.json`](../../hooks/claude-hooks.json).
This page is a human-readable rendering. The publication validator compares
every command block below with those sources.

## Codex SessionStart

The matcher is `startup|resume|clear|compact`. On Linux and macOS, the exact
checked-in command is:

```bash
printf '%s\n\n' 'You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

On Windows, the exact checked-in command invokes the packaged wrapper:

```cmd
"%PLUGIN_ROOT%\hooks\codex-session-start.cmd"
```

The wrapper contains only command-shell built-ins:

```bat
@echo off
setlocal DisableDelayedExpansion
echo You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:
echo(
type "%~dp0..\skills\using-axiom\SKILL.md"
```

The handler has a five-second timeout. The Windows path is plugin-relative and
does not resolve a program from the session working directory or `PATH`.

## Claude Code SessionStart

The matcher is `startup|resume|clear|compact`. The exact checked-in command is:

```bash
printf '%s\n\n' 'You have Axiom in Claude Code. Load this startup front door before deciding whether any Axiom skill applies. The Codex-only routes delegate-simple-task, optimize-codex-usage, and continuous-progress are not available in Claude Code; say so instead of simulating them:'; cat "${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

The preamble tells the session that the Codex-only routes are not available in
Claude Code before it reads the same routing gate. The handler has a
five-second timeout. Claude Code runs command Hooks in Bash, including Git Bash
on Windows. Without Git Bash on Windows, the Hook fails and the session starts
without the routing gate.

## Bounded Behavior

The checked-in handlers print a loading message and read
`skills/using-axiom/SKILL.md` from the installed plugin root. They do not write
files, access credentials, start background work, or contact a network service.
The Hook loads the routing gate; the gate decides whether a route matches. It
does not authorize an action.

If the installed matcher, command, root variable, wrapper, timeout, or event
differs on either host, stop trusting that Hook until the installation and
checked-in package are reconciled through the host-managed lifecycle in
[Managing an Installation](../guides/managing-installation.md).
