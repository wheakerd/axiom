# Compatibility

Axiom's compatibility claims are bounded by what the repository checks. It checks structure: for each release, the manifests, marketplace catalogs, Hooks, wrappers, Skills, and documentation parse and agree with each other. It does not measure how a host's model behaves with the plugin installed.

## Support Levels

| Level | Meaning |
| --- | --- |
| Checked in | The repository contains the named manifest, Hook, wrapper, Skill, or contract. |
| Statically validated | Deterministic repository checks passed for an identified tree. This is not host execution. |
| Observed | Someone observed the behavior in a named host version and lifecycle against an immutable release and reported it. |

A passing static check is not an observation. See [Report A Compatibility Result](#report-a-compatibility-result) for how to report one.

## Supported Hosts

The release tree provides one integration per host over the same Skills:

| Host | Checked-in integration | Lifecycle contract |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json`, `plugin/.codex-plugin/plugin.json`, `plugin/hooks/codex-hooks.json`, `plugin/hooks/codex-session-start.cmd`, and `plugin/skills/` | `SessionStart` on `startup`, `resume`, `clear`, `compact`, and `fork`; POSIX and Windows command variants are declared |
| Claude Code | `.claude-plugin/marketplace.json`, `plugin/.claude-plugin/plugin.json`, `plugin/hooks/claude-hooks.json`, and `plugin/skills/` | `SessionStart` on `startup`, `resume`, `clear`, `compact`, and `fork`; one POSIX shell command, which needs Git Bash on Windows |

Both manifests point to `./skills/` inside the installed plugin root `plugin/`, and each catalog installs only that subtree through a `git-subdir` source. Codex and Claude Code are supported installation and runtime hosts, and both receive every bundled route, with one host-specific boundary: `agents-architect` writes only `AGENTS.md`, and a Claude Code project that has a `CLAUDE.md` does not load `AGENTS.md`, so there the skill stops and says so. `continuous-progress` keeps each host's operations detail in its own `references/`, and `delegate-simple-task` leaves the judgment of host settings to the host model. This is repository support, not proof of execution on every host release, operating system, shell, installation method, or policy configuration.

Codex holds a new or changed Hook until you trust it in `/hooks`; Claude Code runs it at the next `SessionStart` once the plugin loads. The [Hook Reference](reference/hooks.md) renders the exact checked-in commands for an optional comparison with an installed copy.

## Claude Code Package Format And Validation

`claude plugin validate --strict` validates the Claude Code manifest and each Skill's metadata; it does not prove installation or execution. The manifest declares only fields that strict validation accepts.

## Codex Package Format And Validation

OpenAI still supports `.codex-plugin/plugin.json` as a compatibility manifest. Its newer portable format uses root `plugin.json` and `extensions.com.openai`. An inline OpenAI extension replaces the compatibility overlay rather than merging with it. Axiom keeps its supported Codex layout and explicit hook path; adding a second manifest is not required for compatibility. See the official [packaging specification](https://developers.openai.com/plugins/build/plugins#plugin-structure).

The `hooks` declaration is supported in this layout. The listing schema also supports `interface.brandColorDark` and `interface.supportURL`; their value, contrast, and HTTPS requirements still apply. See the official [hook specification](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks) and [interface requirements](https://developers.openai.com/plugins/deploy/submission-errors#listing-and-interface-errors).

Current package checks use the repository's publication aggregate. A native package read is a separate parsing check; it does not prove strict schema validation, installation, hook trust, or execution. The response may omit listing fields, so it cannot establish whether those fields render in the UI. Contributor check ownership is in [CONTRIBUTING.md](../CONTRIBUTING.md#required-local-checks).

## Current Bounded Status

The machine-readable [runtime identity](../evidence/runtime-identity.json) binds the checked-in tree to its plugin version and installed-file digest, as [Runtime Identity](runtime-identity.md) describes. It never records publication; the tag, the GitHub Release, and the marketplace catalogs are the publication state.

| Host | What the repository checks for each release |
| --- | --- |
| Codex | The package and Hook are checked in and pass the deterministic package and contract checks. |
| Claude Code | The package and Hook are checked in and pass the deterministic package and contract checks; strict `claude plugin validate` is available as a native check. |

The repository records no observation of an installed host for the current release. The cross-platform CI job runs the checked-in Hook commands on a Windows runner, the Codex wrapper under `cmd.exe` and the Claude Code command under Git Bash; Claude Code without Git Bash falls back to PowerShell, which does not run the command.

A source candidate cannot establish a future signed merge, immutable tag, final workflow result, or post-publication host observation.

## Known Limitations

Unless a current immutable result states otherwise, do not assume:

- compatibility with every earlier or later Codex or Claude Code version;
- execution across every POSIX shell, Windows configuration, operating system, installation method, or host policy;
- successful marketplace fetch, update, cache refresh, or remote release availability from repository presence alone;
- end-to-end routing in a session that was not freshly started;
- recovery of task history or tool output that the host no longer exposes;
- exact tokens, credits, reasoning work, cache hits, or latency that the host does not expose for the scoped run; or
- a missing optional native validator, command error, or unavailable host is a pass.

Static workflow execution on native runners is useful process-boundary evidence for the exact checked-in commands, but it is not an installed-plugin or model- session observation.

## Report A Compatibility Result

Report what you observed in a host session. Report a pass, a failure, an unknown result, and a case you did not run as different outcomes.

1. Use a disposable, non-sensitive workspace and a read-only request. Place the workspace in a directory with no `AGENTS.md` or `CLAUDE.md` in itself or in any ancestor and no enclosing Git repository, so the host loads no project instruction file beside Axiom.
2. Record the exact host version, operating system, immutable Axiom tag and commit, installation method, and lifecycle source.
3. Compare the installed Hook with the [Hook Reference](reference/hooks.md).
4. Follow the routed example and no-route control in [Getting Started](guides/getting-started.md). A fresh session does not prove manual or automatic compaction behavior; say which cases you did not observe.
5. Retain only minimal sanitized facts. Never include credentials, private paths, raw transcripts, session identifiers, or external-service content.
6. Use the [compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml) or the [routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml).

A report lives in its issue; the repository checks in no observation records.

## Earlier Records

Version notes, routing evaluations, host observation records, runtime digest histories, and the index of earlier experiment archives are not part of the current tree. They remain in the tree at tag [`v0.27.2`](https://github.com/wheakerd/axiom/tree/v0.27.2), under `docs/releases/`, `evals/`, `evidence/`, and `docs/field-validation.md`. Each record keeps its original host, version, date, and outcome and says nothing about the current release.

## Version Interpretation

Use the synchronized manifests to identify the source package version and an immutable version tag when describing a published release. A working-tree checkout, floating tag, or marketplace cache does not establish publication or the installed version. An installed marketplace snapshot may lag the source, so compare its behavior with documentation and Hook declarations from the same release or commit. Current observations include an explicit version and Hook review.

User-visible release history belongs in the [Changelog](../CHANGELOG.md). Contributor requirements for compatibility claims and optional native validation are in [CONTRIBUTING.md](../CONTRIBUTING.md).
