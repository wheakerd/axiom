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

For Claude Code, refresh the marketplace and update Axiom:

```bash
claude plugin marketplace update axiom
claude plugin update axiom@axiom
```

Inside a running session, use `/plugin marketplace update axiom` and
`/plugin update axiom@axiom`. Run `/reload-plugins` or start another session,
then compare the installed Hook with the [Hook Reference](../reference/hooks.md).
Claude Code may update plugin files in the background when marketplace
auto-update is enabled; the running session still uses the snapshot loaded at
launch.

Whether updates are checked or installed automatically, and their timing, are
controlled by your settings and the native client or workspace policy. Axiom
provides versioned source metadata and has no update scheduler.

## Version Selection

The [marketplace entry](../../.agents/plugins/marketplace.json) uses Codex's
official Git `url` source with an immutable release-tag `ref`. The default
marketplace remains discoverable from the repository's default branch, while
the entry selects the plugin's published source independently. A normal
`main` commit leaves that selection unchanged.

The Claude Code catalog in `.claude-plugin/marketplace.json` uses the same Git
`url` source and immutable release-tag `ref`. Both catalogs advance together.

After a stable release becomes GitHub Latest, maintainers publish the matching
catalog references through the existing signed PR process. Until that catalog
change is merged, clients continue to resolve the preceding selection. A
GitHub Release, its Latest marker, and a Git tag literally named `latest` are
different objects; the client does not infer one from the others.

For an existing default-branch registration, use the native marketplace
upgrade above, then inspect the installed version with:

```bash
codex plugin list --marketplace axiom --json
```

Keep deliberate user pins. Codex's marketplace `--ref` option fixes the
**catalog snapshot**; it does not override a plugin entry's own `source.ref`.
To hold a specific plugin version, select an immutable catalog snapshot whose
entry resolves to that version, using the client's supported source controls.
Inspect the entry before assuming that a catalog tag and the plugin version
match. For a workspace-managed installation, the workspace administrator owns
the configured repository, path, ref, and native sync policy.

These source and lifecycle semantics were last verified on 2026-10-13 against
the official [marketplace format](https://developers.openai.com/plugins/build/plugins#marketplace-metadata),
[marketplace configuration](https://learn.chatgpt.com/docs/config-file/config-reference),
and [workspace sync documentation](https://learn.chatgpt.com/docs/enterprise/plugin-management).
Workspace sync timing is not a promise about personal Codex installations.

## Marketplace Clone Timeouts

An error containing `git clone marketplace source timed out after 30s`
identifies a failure to download the marketplace catalog. Codex supports
`--sparse` for Git marketplaces to reduce the catalog checkout. Axiom's current
catalog needs only `.agents/plugins`: its plugin entry uses a separate Git
`url` source with an immutable release ref.

### Inspect The Registration

Record the marketplace and installed plugin listings before changing the
registration:

```bash
codex plugin marketplace list --json
codex plugin list --marketplace axiom --json
```

Also check the original registration settings for an explicit catalog ref,
custom source, or additional sparse paths. The migration below applies to a
personal `wheakerd/axiom` Git registration following the default branch.
For a pinned catalog, retain its original `--ref` when re-adding it. Inspect
that snapshot's entries: if they use local plugin paths, include each path
with another `--sparse` option. A catalog that points to local plugin files
needs those files as well as `.agents/plugins`. Keep custom sources and
workspace-managed controls with their existing owner.

### Re-Register With Sparse Checkout

When an existing registration rejects changed source options, remove that
marketplace registration and add it again with the supported sparse option:

```bash
codex plugin marketplace remove axiom
codex plugin marketplace add wheakerd/axiom --sparse .agents/plugins
codex plugin marketplace upgrade axiom
```

Stop if a command fails. If re-registration fails after removal, restore the
previous source and ref through `codex plugin marketplace add` using the
settings recorded above. Do not remove the plugin or delete its cache to
change the marketplace registration.

Sparse checkout changes which catalog files are fetched. It preserves the
default-branch catalog selection and the entry's independent plugin version
selection. It adds no update scheduler and does not override client or user
update settings.

### Verify The Result

Run the two listing commands again. Check the registered source, installed
version, plugin source ref, and enabled state against the intended catalog
entry and your recorded settings. Follow the [update checks](#updating) for a
fresh session and Hook inspection.

This registration migration was verified on 2026-10-13 with Codex CLI
`0.162.1` on Linux in an isolated Axiom `v0.14.0` installation. The existing
plugin cache and enabled setting were preserved, and the complete native upgrade succeeded.
This does not establish desktop refresh, Hook trust, or automatic update
timing on another installation.

The clone deadline applies to the catalog download. A complete refresh may
also download plugin sources and can take longer than 30 seconds. Sparse
checkout does not change the client's timeout or guarantee completion on a
slow or unavailable network. If the error persists, record the exact failing
phase, CLI version, exit status, and sanitized error for the
[problem report](#reporting-a-problem).

The supported CLI options and sparse-path requirements were last verified on
2026-10-13 against the official
[marketplace CLI documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli)
and [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

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

In Claude Code, disable Axiom while retaining it, or uninstall it:

```bash
claude plugin disable axiom@axiom
claude plugin uninstall axiom@axiom
```

After a Codex removal, start a new session. After a Claude Code change, run
`/reload-plugins` or start another session. Confirm that Axiom is absent or
disabled in the host's plugin list and that its Hook is absent from `/hooks`
before treating it as inactive. Do not edit installed files or delete host
caches as a substitute for the host-managed lifecycle.

## Non-Destructive Troubleshooting

If expected Axiom capabilities are unavailable or a request routes incorrectly:

1. Confirm that Axiom is installed and enabled in the host's plugin list.
2. Open `/hooks` and confirm that the `SessionStart` Hook is present, trusted,
   and identical to the [checked-in reference](../reference/hooks.md).
3. Confirm that the installed Axiom version is the version you intended to
   test.
4. Start a fresh Codex session, or run `/reload-plugins` in Claude Code.
5. Retry one read-only routed request and one no-route control from
   [Getting Started](getting-started.md).

If routing is missing after Claude Code compaction, confirm that `compact`
remains in the installed `SessionStart` matcher. On Windows, confirm that Git
Bash is available; without it the Claude Code Hook fails and the session starts
without the routing gate. A Codex-only route reporting that it is not available
in Claude Code is the expected result, not a failure.

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
