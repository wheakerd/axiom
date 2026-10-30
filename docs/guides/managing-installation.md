# Managing an Axiom Installation

This guide owns Axiom's current update, disable, removal, and non-destructive troubleshooting procedures. The host owns the plugin lifecycle; Axiom does not check for, download, install, or announce updates by itself.

## Updating

For Codex, request a marketplace upgrade:

```bash
codex plugin marketplace upgrade axiom
```

In a supported Codex workspace plugin UI, use **Refresh**. Start a new session after the update and trust the changed Hook in `/hooks`; Codex holds it until you do.

For Claude Code, refresh the marketplace and update Axiom:

```bash
claude plugin marketplace update axiom
claude plugin update axiom@axiom
```

Claude Code runs an updated Hook without a separate trust step, at the next `SessionStart` event after the plugin loads. After these commands, start a new session; verifying the installed Hook is optional, as the [Trust Model](../trust-model.md#hook-trust-boundary) describes. Inside a running session, run `/plugin marketplace update axiom`, then select Axiom on the **Installed** tab of `/plugin` and choose **Update now**. Once closing the panel reloads plugins, the updated Hook runs at that session's next `SessionStart` event, such as `/clear`, `/resume`, `/branch`, or an automatic or manual compaction. A new session's `SessionStart` Hook delivers the updated routing gate; `/reload-plugins` does not rerun it. Claude Code may update plugin files in the background when marketplace auto-update is enabled, which is off by default for third-party marketplaces such as `axiom`; with it on, the installed Hook can change between your sessions without a command from you. A running session keeps the version it loaded until `/reload-plugins`.

Whether updates are checked or installed automatically, and their timing, are controlled by your settings and the native client or workspace policy. Axiom provides versioned source metadata and has no update scheduler.

## Version Selection

The [marketplace entry](../../.agents/plugins/marketplace.json) uses Codex's official `git-subdir` source: the repository `url`, the installed plugin root `./plugin` as its `path`, and an immutable release-tag `ref`. The default marketplace remains discoverable from the repository's default branch, while the entry selects the plugin's published source independently. A normal `main` commit leaves that selection unchanged.

The Claude Code catalog in `.claude-plugin/marketplace.json` uses the same repository and release-tag `ref` through its `git-subdir` source with `path` `plugin`. Both catalogs advance together. Catalogs that select a tag before `v0.17.0` use the Git `url` source instead, because those tags keep the plugin at the repository root.

After a stable release becomes GitHub Latest, maintainers publish the matching catalog references through the existing signed PR process. Until that catalog change is merged, clients continue to resolve the preceding selection. A GitHub Release, its Latest marker, and a Git tag literally named `latest` are different objects; the client does not infer one from the others.

For an existing default-branch registration, use the native marketplace upgrade above, then inspect the installed version. In Codex, run:

```bash
codex plugin list --marketplace axiom --json
```

In Claude Code, `claude plugin list` prints each installed plugin's `Version`, `Scope`, and `Status` lines.

Keep deliberate user pins. A catalog pin fixes the **catalog snapshot**; it does not override a plugin entry's own `source.ref`. In Codex, use the marketplace `--ref` option. In Claude Code, add the marketplace with a `#ref` suffix, such as `wheakerd/axiom#<tag>`; a marketplace added with a tag or branch updates only to the latest commit of that ref. To hold a specific plugin version, select an immutable catalog snapshot whose entry resolves to that version, using the client's supported source controls. Inspect the entry before assuming that a catalog tag and the plugin version match. For a workspace-managed installation, the workspace administrator owns the configured repository, path, ref, and native sync policy.

The Codex source format was last verified on 2026-10-25 and the lifecycle semantics on 2026-10-13 against the official [marketplace format](https://developers.openai.com/plugins/build/plugins#marketplace-metadata), [marketplace configuration](https://learn.chatgpt.com/docs/config-file/config-reference), and [workspace sync documentation](https://learn.chatgpt.com/docs/enterprise/plugin-management). Workspace sync timing is not a promise about personal Codex installations. The Claude Code source format was last verified on 2026-10-25 against the official [marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources), and the other Claude Code statements on 2026-10-22 against the official [plugin installation guide](https://code.claude.com/docs/en/discover-plugins) and [plugin commands reference](https://code.claude.com/docs/en/plugins/cli-reference).

## Marketplace Clone Timeouts

In Codex, an error containing `git clone marketplace source timed out after 30s` identifies a failure to download the marketplace catalog. Codex supports `--sparse` for Git marketplaces to reduce the catalog checkout. Axiom's current catalog needs only `.agents/plugins`: its plugin entry uses a separate `git-subdir` source with an immutable release ref. The steps below apply to Codex; [Claude Code](#claude-code-clone-timeouts) has its own.

### Inspect The Registration

Record the marketplace and installed plugin listings before changing the registration:

```bash
codex plugin marketplace list --json
codex plugin list --marketplace axiom --json
```

Also check the original registration settings for an explicit catalog ref, custom source, or additional sparse paths. The migration below applies to a personal `wheakerd/axiom` Git registration following the default branch. For a pinned catalog, retain its original `--ref` when re-adding it. Inspect that snapshot's entries: if they use local plugin paths, include each path with another `--sparse` option. A catalog that points to local plugin files needs those files as well as `.agents/plugins`. Keep custom sources and workspace-managed controls with their existing owner.

### Re-Register With Sparse Checkout

When an existing registration rejects changed source options, remove that marketplace registration and add it again with the supported sparse option:

```bash
codex plugin marketplace remove axiom
codex plugin marketplace add wheakerd/axiom --sparse .agents/plugins
codex plugin marketplace upgrade axiom
```

Stop if a command fails. If re-registration fails after removal, restore the previous source and ref through `codex plugin marketplace add` using the settings recorded above. Do not remove the plugin or delete its cache to change the marketplace registration.

Sparse checkout changes which catalog files are fetched. It preserves the default-branch catalog selection and the entry's independent plugin version selection. It adds no update scheduler and does not override client or user update settings.

### Verify The Result

Run the two listing commands again. Check the registered source, installed version, plugin source ref, and enabled state against the intended catalog entry and your recorded settings. Follow the [update checks](#updating) for a fresh session and Hook inspection.

This registration migration was verified on 2026-10-13 with Codex CLI `0.162.1` on Linux in an isolated Axiom `v0.14.0` installation. The existing plugin cache and enabled setting were preserved, and the complete native upgrade succeeded. This does not establish desktop refresh, Hook trust, or automatic update timing on another installation.

The clone deadline applies to the catalog download. A complete refresh may also download plugin sources and can take longer than 30 seconds. Sparse checkout does not change the client's timeout or guarantee completion on a slow or unavailable network. If the error persists, record the exact failing phase, CLI version, exit status, and sanitized error for the [problem report](#reporting-a-problem).

The supported CLI options and sparse-path requirements were last verified on 2026-10-13 against the official [marketplace CLI documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli) and [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

### Claude Code Clone Timeouts

In Claude Code, `Git clone timed out after 120s` means cloning or re-cloning the marketplace exceeded the default limit. Raise the limit, in milliseconds, in the shell that runs the command, then retry:

```bash
export CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=300000
claude plugin marketplace update axiom
```

In PowerShell, set `$env:CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS = "300000"` instead. For a new registration, `claude plugin marketplace add wheakerd/axiom --sparse .claude-plugin` fetches only the catalog, because its plugin entry uses a separate `git-subdir` source. Removing a marketplace also uninstalls its plugins, so do not re-register an existing installation only to add sparse checkout. These options were last verified on 2026-10-22 against the official [plugin troubleshooting](https://code.claude.com/docs/en/plugins/troubleshooting) and [plugin commands](https://code.claude.com/docs/en/plugins/cli-reference) references.

## Disabling Or Removing

For a trusted project, disable Axiom in that project's `.codex/config.toml`:

```toml
[plugins."axiom@axiom"]
enabled = false
```

Set `enabled = true` to enable it again. The key combines the plugin name and marketplace name. Project configuration is loaded only for trusted projects and remains subject to managed requirements. Disabling leaves the installation in place; marketplace refresh may still update its files. In Codex, installing or enabling a plugin does not automatically trust its hooks; review the current definition in `/hooks` before use.

This project setting applies to local-marketplace installations, not the enabled state of workspace-managed plugins. These configuration semantics were last verified on 2026-09-16 against the official [project plugin settings](https://developers.openai.com/plugins/build/plugins#enable-or-disable-a-plugin-for-a-repo) and [hook trust requirements](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks).

Remove the exact Codex installation from the `axiom` marketplace:

```bash
codex plugin remove axiom@axiom
```

In Claude Code, disable Axiom while retaining it, enable it again, or uninstall it:

```bash
claude plugin disable axiom@axiom
claude plugin enable axiom@axiom
claude plugin uninstall axiom@axiom
```

Without `--scope`, `disable` and `enable` act on the first of the local, project, and user scopes whose settings mention Axiom. That is usually `user`, so disabling turns Axiom off in every project. To turn it off only in the current project, add `--scope local` for yourself or `--scope project` to share the override through the project's settings. Once Axiom is enabled and loads again, at a session start or a plugin reload, its Hook runs at the next `SessionStart` event without a separate trust step. These Claude Code commands were last verified on 2026-10-24 against the official [plugin commands reference](https://code.claude.com/docs/en/plugins/cli-reference).

After a change on either host, start a new session. In Claude Code, `/reload-plugins` unloads the plugin from a running session, but the routing gate already delivered stays in that session's context. Confirm that Axiom is absent or disabled in the host's plugin list and that its Hook is absent from `/hooks` before treating it as inactive. Do not edit installed files or delete host caches as a substitute for the host-managed lifecycle. Disabling or removing Axiom leaves any task state that routes wrote into your repositories' Git metadata in place; the [Trust Model](../trust-model.md#repository-state-written-by-routes) lists those locations and how to remove them.

## Non-Destructive Troubleshooting

If expected Axiom capabilities are unavailable or a request routes incorrectly:

1. Confirm that Axiom is installed and enabled in the host's plugin list.
2. Open `/hooks` and confirm that the `SessionStart` Hook is present and identical to the [checked-in reference](../reference/hooks.md); in Codex, also confirm that it is trusted.
3. Confirm that the installed Axiom version is the version you intended to test.
4. Start a fresh session in either host.
5. Retry one read-only routed request and one no-route control from [Getting Started](getting-started.md).

If routing is missing after compaction or a fork in either host, confirm that `compact` and `fork` remain in the installed `SessionStart` matcher. On Windows, confirm that Git Bash is available for Claude Code; without it Claude Code runs the Hook in PowerShell, which does not support the command.

Do not delete host data, clear caches, edit the installed plugin, change global configuration, install a proprietary validator, or create a second Hook merely to make routing appear. Record unavailable tooling as `UNAVAILABLE`, not passed.

## Reporting A Problem

Before reporting, record the host and exact version, operating system, Axiom version or commit, installation method, lifecycle source, installed Hook definition, request, selected route, clarification count, and whether any mutation was attempted. Do not include credentials, private conversation text, or sensitive repository content.

- Use the [compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml) for an installation or host observation.
- Use the [routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml) for unexpected routing behavior.
- Use the private reporting process in [SECURITY.md](../../SECURITY.md) for a vulnerability.
