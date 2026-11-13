# Hook Reference

Plugin Hooks execute commands inside the host session. This page renders the checked-in definitions; comparing an installed copy with them is an optional reviewer check described in the [Trust Model](../trust-model.md#hook-trust-boundary). Codex skips a new or changed Hook until you review and trust it in `/hooks`, and a change to a packaged script needs a new review even when the declaration is unchanged. Claude Code has no separate Hook trust step: once the plugin loads at a session start, an in-session install, or a plugin reload, its Hooks run at their next events. In either host, `/hooks` shows the loaded definitions.

Axiom declares two Hook events on each host, both documented by the host as current events: `SessionStart` loads the routing gate; `UserPromptSubmit` prints one static statement before the model acts on a prompt, covering material ambiguity and what completion rests on. Every handler prints Axiom's own static text and reads nothing else into the session. No handler reads the host's event input, returns a decision, or continues a turn. Each hook places a statement; the host model decides.

The canonical sources are [`plugin/hooks/codex-hooks.json`](../../../plugin/hooks/codex-hooks.json), [`plugin/hooks/claude-hooks.json`](../../../plugin/hooks/claude-hooks.json), and the packaged Windows wrappers [`plugin/hooks/codex-session-start.cmd`](../../../plugin/hooks/codex-session-start.cmd) and [`plugin/hooks/codex-prompt-submit.cmd`](../../../plugin/hooks/codex-prompt-submit.cmd). This page is a human-readable rendering. The publication validator compares every command and script block below with those sources byte for byte.

## Codex SessionStart

The matcher is `startup|resume|clear|compact|fork`; `fork` covers a forked thread. On Linux and macOS, the exact checked-in command is:

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

## Codex UserPromptSubmit

No matcher; the handler runs for every prompt. On Linux and macOS, the exact checked-in command is:

```bash
printf '%s\n' 'Axiom: material ambiguity that context cannot resolve is clarified before acting; completion rests on evidence observed in this session and names what remains unresolved; replies use the language of the request.'
```

On Windows, the exact checked-in command invokes the packaged wrapper:

```cmd
"%PLUGIN_ROOT%\hooks\codex-prompt-submit.cmd"
```

The wrapper contains only command-shell built-ins:

```bat
@echo off
setlocal DisableDelayedExpansion
echo Axiom: material ambiguity that context cannot resolve is clarified before acting; completion rests on evidence observed in this session and names what remains unresolved; replies use the language of the request.
```

## Claude Code SessionStart

The matcher is `startup|resume|clear|compact|fork`; `fork` covers a session forked from an existing one, such as with `/fork`, `/branch`, or `--fork-session`. The exact checked-in command is:

```bash
printf '%s\n\n' 'You have Axiom in Claude Code. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

The preamble names the host before the session reads the same routing gate.

## Claude Code UserPromptSubmit

No matcher; the handler runs for every prompt, including a scheduled task firing, a background subagent reporting back, or a message from another session. The exact checked-in command prints the same static statement:

```bash
printf '%s\n' 'Axiom: material ambiguity that context cannot resolve is clarified before acting; completion rests on evidence observed in this session and names what remains unresolved; replies use the language of the request.'
```

## Bounded Behavior

Every handler has a five-second timeout. The Windows wrapper paths are plugin-relative and do not resolve a program from the session working directory or `PATH`. Claude Code passes each POSIX command to `sh -c` on macOS and Linux and to Git Bash on Windows. Without Git Bash, Claude Code uses PowerShell, which does not support these commands; that path is unsupported and untested. Install Git for Windows, or set `CLAUDE_CODE_GIT_BASH_PATH` if Claude Code does not find an installed Git Bash.

The checked-in handlers print a loading message and read `skills/using-axiom/SKILL.md` from the installed plugin root, or print one static statement. They do not write files, access credentials, start background work, or contact a network service. The `SessionStart` Hook loads the routing gate and the gate decides whether a route matches; the `UserPromptSubmit` Hook prints one statement. Neither selects a route by itself or authorizes an action.

If an installed matcher, command, root variable, script, timeout, or event differs on either host, keep that Hook from running: leave it untrusted in Codex, or disable Axiom in Claude Code, until the installation and checked-in package are reconciled through the host-managed lifecycle in [Managing an Installation](../guides/managing-installation.md).
