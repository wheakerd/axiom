# Hook Reference

Plugin Hooks execute commands inside the host session. Compare the installed
definition with the checked-in source before it runs, and stop if it differs.
Codex skips a new or changed Hook until you review and trust it in `/hooks`.
Claude Code has no separate Hook trust step: once the plugin loads at a session
start, an in-session install, or a plugin reload, its Hook runs at the next
`SessionStart` event, such as a new session, `/clear`, `/resume`, a fork, or
compaction. Compare the installed copy before the plugin loads. In either host,
`/hooks` shows the loaded definition.

The canonical sources are
[`hooks/codex-hooks.json`](../../hooks/codex-hooks.json), the packaged
[`hooks/codex-session-start.cmd`](../../hooks/codex-session-start.cmd) wrapper,
and [`hooks/claude-hooks.json`](../../hooks/claude-hooks.json).
This page is a human-readable rendering. The publication validator compares
every command block below with those sources.

## Codex SessionStart

The matcher is `startup|resume|clear|compact|fork`; `fork` covers a forked thread. On
Linux and macOS, the exact checked-in command is:

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

The matcher is `startup|resume|clear|compact|fork`; `fork` covers a session forked from an existing one,
such as with `/fork`, `/branch`, or `--fork-session`. The exact checked-in
command is:

```bash
printf '%s\n\n' 'You have Axiom in Claude Code. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

The preamble names the host before the session reads the same routing gate.
The handler has a five-second timeout. Claude Code passes the command to
`sh -c` on macOS and Linux and to Git Bash on Windows. Without Git Bash,
Claude Code uses PowerShell, which does not support this command; that path is
unsupported and untested. Install Git for Windows, or set
`CLAUDE_CODE_GIT_BASH_PATH` if Claude Code does not find an installed Git Bash.

## Bounded Behavior

The checked-in handlers print a loading message and read
`skills/using-axiom/SKILL.md` from the installed plugin root. They do not write
files, access credentials, start background work, or contact a network service.
The Hook loads the routing gate; the gate decides whether a route matches. It
does not authorize an action.

If the installed matcher, command, root variable, wrapper, timeout, or event
differs on either host, keep that Hook from running: leave it untrusted in
Codex, or disable Axiom in Claude Code, until the installation and checked-in
package are reconciled through the host-managed lifecycle in
[Managing an Installation](../guides/managing-installation.md).
