# Getting Started

This guide owns Axiom installation, first use, and the initial safe comparison
between one routed request and one ordinary control request. Axiom supports
Codex and Claude Code through separate host wrappers over the same checked-in
Skills.

## Before Installing

Use a test repository that contains no sensitive material. Review the current
[compatibility boundary](../compatibility.md) and remember that checked-in or
statically validated support is not a fresh observation of your host.

## Install For Codex

Add the Git marketplace and install Axiom from it:

```bash
codex plugin marketplace add wheakerd/axiom
codex plugin add axiom@axiom
```

Start a new Codex chat or CLI session. An existing session may retain an older
Hook or Skill snapshot.

## Install For Claude Code

Add the marketplace, install Axiom, and reload plugins:

```text
/plugin marketplace add wheakerd/axiom
/plugin install axiom@axiom
/reload-plugins
```

The running session keeps the plugin snapshot loaded at launch until you
reload plugins or start another session.

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
repository.

## Try One Control Request

Use this ordinary request:

> Summarize the purpose of this README. Do not modify files.

The expected contract is no Axiom route and normal host execution. A no-route
result is not a safety certification; host permissions and repository
instructions remain in force.

## Interpret And Report The Result

The expected results above are contracts, not claims that your installation
has already reproduced them. Record the host name and version, operating
system, Axiom version or immutable commit, installation method, lifecycle
source, exact request, selected route, clarification count, and whether any
mutation was attempted.

- Use the [compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)
  for a bounded host result.
- Use the [routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)
  for a false positive, false negative, or unexpected clarification.
- Follow [Field Validation](../field-validation.md) for evidence labels and the
  non-destructive observation protocol.

For update, removal, disable, or troubleshooting procedures, continue with
[Managing an Installation](managing-installation.md).
