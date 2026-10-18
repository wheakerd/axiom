# Getting Started

This guide owns Axiom installation, first use, and the initial safe comparison
between one routed request and one ordinary control request. Axiom supports
Codex and Claude Code through separate host manifests, marketplaces, and Hooks
over the same checked-in Skills.

## Before Installing

Use a test repository that contains no sensitive material. Review the current
[compatibility boundary](../compatibility.md) and remember that checked-in or
statically validated support is not a fresh observation of your host.

## Install For Codex

Add the Git marketplace and install Axiom from it:

```bash
codex plugin marketplace add wheakerd/axiom --sparse .agents/plugins
codex plugin add axiom@axiom
```

The [marketplace entry](../../.agents/plugins/marketplace.json) selects a
published version through its Git source `ref`. Fetching the marketplace from
the default branch does not install that branch's development plugin files.
See [version selection](managing-installation.md#version-selection) for fixed
sources and existing installations.

The official `--sparse` option limits the marketplace checkout to its catalog
directory. The catalog's Git `url` entry fetches the plugin separately, so the
plugin's Skills and Hook do not need additional marketplace sparse paths.
This CLI option was last verified on 2026-10-13 against the official
[marketplace registration documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli).
If `axiom` is already registered without sparse checkout, follow the
[migration procedure](managing-installation.md#marketplace-clone-timeouts).

Start a new Codex chat or CLI session. An existing session may retain an older
Hook or Skill snapshot.

## Install For Claude Code

Add the marketplace and install Axiom from a terminal:

```bash
claude plugin marketplace add wheakerd/axiom
claude plugin install axiom@axiom
```

Inside a running session, use `/plugin marketplace add wheakerd/axiom` and
`/plugin install axiom@axiom`, then `/reload-plugins`. The Claude Code catalog
in `.claude-plugin/marketplace.json` selects the same published version as the
Codex catalog through a Git source `ref`; development commits on `main` do not
change it.

Start a new Claude Code session or run `/reload-plugins`. A running session
keeps the plugin snapshot loaded at launch. On Windows, Claude Code needs Git
Bash to run the startup Hook.

The Claude Code plugin loads the same skills. `delegate-simple-task`,
`continuous-progress`, and `optimize-codex-usage` depend on Codex-only
features; in Claude Code they report that they are not available instead of
running. Invoke any other skill in plain language or as `/axiom:<skill-name>`.

## Inspect The Hook

Open `/hooks` in the host and compare the installed `SessionStart` definition
with the [Hook Reference](../reference/hooks.md). Verify the matcher, command,
host root variable, and any packaged wrapper before trusting it.

Stop if the installed definition differs. Do not repair the mismatch by
editing installed files, deleting caches, or adding another context-loading
Hook. Reconcile the installed version with the repository through the host's
normal plugin lifecycle.

## Try One Routed Request

Use this read-only request:

> Audit this repository's AGENTS.md instruction system. Report findings only;
> do not modify files.

The expected contract is selection of `agents-architect`, a read-only evidence
report, and no file mutation. A route selection is not permission to change the
repository. With `using-axiom` active, the model and host may explain the
invocation according to your output-verbosity preferences. For example:

`Axiom:agents-architect` Review the repository's instruction structure.

The entire Axiom skill marker is inline code. An external or repository-local
skill, plugin, or MCP capability keeps its own inline-code name and a
brief reason, without an `Axiom:` prefix. The model chooses whether to explain
the invocation and how to arrange the surrounding output.

This optional guidance belongs to `using-axiom`: it applies through the enabled
startup gate or an explicit invocation of that skill. With the gate disabled,
invoking a different Axiom skill alone does not activate notice guidance.

## Try One Control Request

Use this ordinary request:

> Summarize the purpose of this README. Do not modify files.

The expected contract is normal host execution with no additional Axiom route.
Startup and a no-route result receive no notice. A no-route result is not
a safety certification; host permissions and repository instructions remain
in force. See the [notice guidance](../../skills/using-axiom/SKILL.md#invocation-notes)
for activation and naming boundaries.

## Interpret And Report The Result

The expected results above are contracts, not claims that your installation
has already reproduced them. Record the host name and version, operating
system, Axiom version or immutable commit, installation method, lifecycle
source, exact request, selected route, clarification count, and whether any
mutation was attempted.

Keep reports free of credentials, private conversation text, and sensitive
repository content. If a result may expose a vulnerability or unauthorized
action, use the private reporting process in [SECURITY.md](../../SECURITY.md)
before sharing details publicly.

- Use the [compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)
  for a bounded host result.
- Use the [routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)
  for a false positive, false negative, or unexpected clarification.
- Follow [Field Validation](../field-validation.md) for evidence labels and the
  non-destructive observation protocol.

For update, removal, disable, or troubleshooting procedures, continue with
[Managing an Installation](managing-installation.md).
