# Managing an Axiom Installation

This guide owns Axiom's current update, disable, removal, and non-destructive
troubleshooting procedures. The host owns the plugin lifecycle; Axiom does not
check for, download, install, or announce updates by itself.

## Updating

For Codex, request a marketplace upgrade:

```bash
codex plugin marketplace upgrade axiom
```

In a supported Codex workspace plugin UI, use **Refresh**. Start a new session
after the update, then inspect `/hooks` again before trusting the changed
snapshot.

For Claude Code, refresh the marketplace, update Axiom, and reload plugins:

```text
/plugin marketplace update axiom
/plugin update axiom@axiom
/reload-plugins
```

Claude Code may update installed plugin files in the background when
marketplace auto-update is enabled. The running session still uses the snapshot
loaded at launch. Reload plugins after a notification or start another session,
then compare the installed Hook with the [Hook Reference](../reference/hooks.md).
The absence of a manual refresh does not prove that files on disk are
unchanged.

## Disabling Or Removing

Remove the exact Codex installation from the `axiom` marketplace:

```bash
codex plugin remove axiom@axiom
```

In Claude Code, disable Axiom while retaining it or uninstall it:

```text
/plugin disable axiom@axiom
/plugin uninstall axiom@axiom
```

After a Codex removal, start a new session. After a Claude Code change, run
`/reload-plugins` or start another session. Confirm that Axiom is absent or
disabled in the host's plugin list and that its Hook is absent from `/hooks`
before treating it as inactive. Do not edit installed files or delete host
caches as a substitute for the host-managed lifecycle.

## Non-Destructive Troubleshooting

If the loading message or expected route is missing:

1. Confirm that Axiom is installed and enabled in the host's plugin list.
2. Open `/hooks` and confirm that the `SessionStart` Hook is present, trusted,
   and identical to the [checked-in reference](../reference/hooks.md).
3. Confirm that the installed Axiom version is the version you intended to
   test.
4. Start a fresh Codex session or run `/reload-plugins` in Claude Code.
5. Retry one read-only routed request and one no-route control from
   [Getting Started](getting-started.md).

If routing is missing after Claude Code compaction, confirm that `compact`
remains in the installed `SessionStart` matcher and that exactly one matching
loading event occurred. Do not add or trust a `PreCompact` context-loading
command as a workaround; ordinary successful stdout from that event does not
enter Claude Code's context.

Do not delete host data, clear caches, edit the installed plugin, change global
configuration, install a proprietary validator, or create a second Hook merely
to make routing appear. Record unavailable tooling as `UNAVAILABLE`, not
passed.

## Reporting A Problem

Before reporting, record the host and exact version, operating system, Axiom
version or commit, installation method, lifecycle source, installed Hook
definition, request, selected route, clarification count, and whether any
mutation was attempted. Do not include credentials, private conversation text,
or sensitive repository content.

- Use the [compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)
  for an installation or host observation.
- Use the [routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)
  for unexpected routing behavior.
- Use the private reporting process in [SECURITY.md](../../SECURITY.md) for a
  vulnerability.
