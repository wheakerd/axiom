# Hook Reference

Plugin Hooks execute commands inside the host session. This page renders the checked-in definitions; comparing an installed copy with them is an optional reviewer check described in the [Trust Model](../trust-model.md#hook-trust-boundary). Codex skips a new or changed Hook until you review and trust it in `/hooks`, and a change to a packaged script needs a new review even when the declaration is unchanged. Claude Code has no separate Hook trust step: once the plugin loads at a session start, an in-session install, or a plugin reload, its Hooks run at their next events. In either host, `/hooks` shows the loaded definitions.

Axiom declares three Hook events on each host, all documented by the host as current events: `SessionStart` loads the routing gate; `UserPromptSubmit` prints one static statement before the model acts on a prompt; `Stop` prints one static statement once, before the turn ends, about what completion rests on. Every handler prints Axiom's own static text and reads nothing else into the session. Each hook places a statement; the host model decides.

The canonical sources are [`plugin/hooks/codex-hooks.json`](../../../plugin/hooks/codex-hooks.json), [`plugin/hooks/claude-hooks.json`](../../../plugin/hooks/claude-hooks.json), the shared [`plugin/hooks/stop-check.sh`](../../../plugin/hooks/stop-check.sh) script, and the packaged Windows wrappers [`plugin/hooks/codex-session-start.cmd`](../../../plugin/hooks/codex-session-start.cmd), [`plugin/hooks/codex-prompt-submit.cmd`](../../../plugin/hooks/codex-prompt-submit.cmd), and [`plugin/hooks/codex-stop-check.cmd`](../../../plugin/hooks/codex-stop-check.cmd). This page is a human-readable rendering. The publication validator compares every command and script block below with those sources byte for byte.

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
printf '%s\n' 'Axiom: material ambiguity that context cannot resolve is clarified before acting.'
```

On Windows, the exact checked-in command invokes the packaged wrapper:

```cmd
"%PLUGIN_ROOT%\hooks\codex-prompt-submit.cmd"
```

The wrapper contains only command-shell built-ins:

```bat
@echo off
setlocal DisableDelayedExpansion
echo Axiom: material ambiguity that context cannot resolve is clarified before acting.
```

## Codex Stop

No matcher; the handler runs when the turn is about to end. Codex passes the Stop event as JSON on standard input and requires JSON on standard output. The checked-in script prints a `decision: block` continuation carrying Axiom's statement while `stop_hook_active` is false, and an empty object once the turn has already been continued, so the statement is delivered at most once per turn. On Linux and macOS, the exact checked-in command is:

```bash
sh "${PLUGIN_ROOT}/hooks/stop-check.sh" codex
```

The shared script, used by both hosts, contains only shell built-ins and `cat`:

```sh
#!/bin/sh
# Axiom Stop check. Argument: claude or codex. Reads the host's Stop event JSON on stdin and prints JSON only.
# When the host reports stop_hook_active true, this turn was already continued once: print an empty object and let it end.
input=$(cat)
case "$input" in
  *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) printf '{}\n'; exit 0 ;;
esac
text='Axiom: completion rests on evidence observed in this session, names what remains unresolved, and replies in the language of the request.'
case "$1" in
  claude) printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' "$text" ;;
  codex) printf '{"decision":"block","reason":"%s"}\n' "$text" ;;
  *) printf '{}\n' ;;
esac
```

On Windows, the exact checked-in command invokes the packaged wrapper:

```cmd
"%PLUGIN_ROOT%\hooks\codex-stop-check.cmd"
```

The wrapper reads standard input with `findstr.exe` from the system directory by absolute path, the one program these wrappers resolve, and otherwise uses command-shell built-ins:

```bat
@echo off
setlocal DisableDelayedExpansion
"%SystemRoot%\System32\findstr.exe" /R "stop_hook_active.:true stop_hook_active.:.true" >nul
if not errorlevel 1 goto allow
echo {"decision":"block","reason":"Axiom: completion rests on evidence observed in this session, names what remains unresolved, and replies in the language of the request."}
exit /b 0
:allow
echo {}
exit /b 0
```

## Claude Code SessionStart

The matcher is `startup|resume|clear|compact|fork`; `fork` covers a session forked from an existing one, such as with `/fork`, `/branch`, or `--fork-session`. The exact checked-in command is:

```bash
printf '%s\n\n' 'You have Axiom in Claude Code. Load this startup front door before deciding whether any Axiom skill applies:'; cat "${CLAUDE_PLUGIN_ROOT}/skills/using-axiom/SKILL.md"
```

The preamble names the host before the session reads the same routing gate.

## Claude Code UserPromptSubmit

No matcher; the handler runs for every prompt, including a scheduled task firing, a background subagent reporting back, or a message from another session. The exact checked-in command is the same static sentence:

```bash
printf '%s\n' 'Axiom: material ambiguity that context cannot resolve is clarified before acting.'
```

## Claude Code Stop

No matcher; the handler runs when the main agent is about to finish responding. Claude Code passes the Stop event as JSON on standard input. The exact checked-in command runs the shared script above with the `claude` argument, which returns Axiom's statement as `additionalContext` while `stop_hook_active` is false and an empty object afterwards, so the turn continues at most once and the transcript shows the statement as hook feedback rather than a hook error:

```bash
sh "${CLAUDE_PLUGIN_ROOT}/hooks/stop-check.sh" claude
```

## Bounded Behavior

Every handler has a five-second timeout. The Windows wrapper paths are plugin-relative and do not resolve a program from the session working directory or `PATH`; the Stop wrapper names `findstr.exe` by its absolute system path. Claude Code passes each POSIX command to `sh -c` on macOS and Linux and to Git Bash on Windows. Without Git Bash, Claude Code uses PowerShell, which does not support these commands; that path is unsupported and untested. Install Git for Windows, or set `CLAUDE_CODE_GIT_BASH_PATH` if Claude Code does not find an installed Git Bash.

The checked-in handlers print a loading message and read `skills/using-axiom/SKILL.md` from the installed plugin root, print one static sentence, or print one static JSON object. They do not write files, access credentials, start background work, or contact a network service. The `SessionStart` Hook loads the routing gate and the gate decides whether a route matches; the `UserPromptSubmit` and `Stop` Hooks print one statement each. None of them selects a route by itself or authorizes an action.

If an installed matcher, command, root variable, script, timeout, or event differs on either host, keep that Hook from running: leave it untrusted in Codex, or disable Axiom in Claude Code, until the installation and checked-in package are reconciled through the host-managed lifecycle in [Managing an Installation](../guides/managing-installation.md).
