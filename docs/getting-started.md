# Getting Started

This guide takes a new Axiom installation through four observable steps:
install the plugin, load it in a fresh or reloaded session, review its hook, and
compare one routed request with one ordinary control request.

Axiom supports Codex and Claude Code through separate host wrappers over the
same checked-in skills. Choose the section for the host you are using.

## Codex

### 1. Install

Add the Git marketplace, then install Axiom from that marketplace:

```bash
codex plugin marketplace add wheakerd/axiom
codex plugin add axiom@axiom
```

The first `axiom` in `axiom@axiom` is the plugin name; the second is the
configured marketplace name.

### 2. Start a fresh session

Start a new Codex chat or CLI session after installation. An existing session
may retain earlier hook or skill state.

### 3. Review the hook

Open the host hook review UI:

```text
/hooks
```

Compare the installed `SessionStart` handler with the exact POSIX or Windows
command in [README: Inspect The Hooks](../README.md#inspect-the-hooks). Confirm
that it:

- uses the host-provided `PLUGIN_ROOT`;
- reads only `skills/using-axiom/SKILL.md`;
- performs foreground output and a local file read; and
- contains no added program, redirection, write, network access, or background
  launch.

Do not trust or manually run a definition that differs. Reconcile the installed
package with the checked-in hook first.

## Claude Code

### 1. Install and reload

Run these commands inside Claude Code:

```text
/plugin marketplace add wheakerd/axiom
/plugin install axiom@axiom
/reload-plugins
```

The `/reload-plugins` step loads the newly installed plugin before hook review.

### 2. Review both hooks

Open:

```text
/hooks
```

Compare both installed handlers with
[README: Inspect The Hooks](../README.md#inspect-the-hooks):

- `SessionStart` for `startup`, `resume`, `clear`, and `compact`;
- `PreCompact` for `manual` and `auto`.

Both commands should use the host-provided `CLAUDE_PLUGIN_ROOT` and read only
`skills/using-axiom/SKILL.md`. Stop trusting a handler if extra commands or a
different path appear.

## Verify One Routed Request

Use a disposable or reviewable repository when you first test routing. Ask:

```text
Perform a read-only audit of this repository's AGENTS.md instruction system.
Report findings only; do not modify files.
```

The expected route is `agents-architect`. The observable behavior should
inventory the repository and instruction system, then report findings without
changing files. The request does not authorize any file change, commit, or
push.

This is an expected route, not a fabricated execution transcript. Higher
priority instructions and the actual repository state still govern what the
agent may do.

## Verify One Control Request

Ask an ordinary request that does not match an Axiom workflow:

```text
Summarize the purpose of this README. Do not modify files.
```

The expected result is normal host behavior without an Axiom route or any file
change. No-route is intentional; Axiom is not a wrapper around every task.

For more route and control cases, see [Examples](examples.md).

## Interpret The Result

| Observation | Meaning |
| --- | --- |
| The routed request selects `agents-architect` | The routing gate matched a checked-in workflow; it does not prove that edits are authorized or complete |
| The control request continues normally | The gate correctly declined to turn an ordinary task into an Axiom workflow |
| The loading message appears but neither result matches | The hook ran, but route selection needs review against the installed gate and higher-priority instructions |
| No loading message appears | Hook installation, trust, enablement, or session reload should be checked before testing routes |

## Non-Destructive Troubleshooting

Use this sequence without deleting or rewriting state:

1. Open `/hooks` and confirm that the expected Axiom handlers are present,
   enabled, and trusted.
2. Compare every installed command character-for-character with the exact
   checked-in command linked above. If it differs, stop and identify which
   package snapshot is installed.
3. Confirm that the host reports the plugin as installed through its normal
   plugin UI or listing command. Do not edit the installed copy.
4. Start a fresh Codex session, or run `/reload-plugins` in Claude Code and
   start a fresh session.
5. Retry the explicit routed request and the ordinary control request. Record
   the host version, Axiom version or commit, request, expected route, and
   observed behavior.
6. If a host command or validator is unavailable, record it as unavailable.
   Do not install or update tooling merely to turn that absence into a pass.

Do not use `git reset`, `git clean`, cache deletion, plugin-directory edits,
global configuration changes, or an automatic reinstall as troubleshooting
shortcuts. If you intentionally update Axiom, use the exact host-controlled
commands in [README: Updating](../README.md#updating), reload the session, and
review the hook again.

Continue with the [Trust Model](trust-model.md) before authorizing a workflow
that can commit, push, deploy, delete, migrate, or promote persistent state.
