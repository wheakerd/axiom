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

## Disabling Or Removing

For a trusted project, disable Axiom in that project's `.codex/config.toml`:

```toml
[plugins."axiom@axiom"]
enabled = false
```

Set `enabled = true` to enable it again. The key combines the plugin name and
marketplace name. Project configuration is loaded only for trusted projects
and remains subject to managed requirements. Disabling leaves the installation
in place; marketplace refresh may still update its files. Installing or
enabling a plugin does not automatically trust its hooks. Review the current
definition in `/hooks` before use.

This project setting applies to local-marketplace installations, not the
enabled state of workspace-managed plugins. These configuration semantics were
last verified on 2026-09-16 against the official
[project plugin settings](https://developers.openai.com/plugins/build/plugins#enable-or-disable-a-plugin-for-a-repo)
and [hook trust requirements](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks).

Remove the exact Codex installation from the `axiom` marketplace:

```bash
codex plugin remove axiom@axiom
```

After removal, start a new Codex session. Confirm that Axiom is absent from
the plugin list and `/hooks` before treating it as inactive. Do not edit installed files or delete
host caches as a substitute for the host-managed lifecycle.

## Non-Destructive Troubleshooting

If the loading message or expected route is missing:

1. Confirm that Axiom is installed and enabled in the host's plugin list.
2. Open `/hooks` and confirm that the `SessionStart` Hook is present, trusted,
   and identical to the [checked-in reference](../reference/hooks.md).
3. Confirm that the installed Axiom version is the version you intended to
   test.
4. Start a fresh Codex session.
5. Retry one read-only routed request and one no-route control from
   [Getting Started](getting-started.md).

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
