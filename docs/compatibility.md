# Compatibility

Axiom's compatibility claims are bounded by what the repository checks. It checks structure: for each release, the manifests, marketplace catalogs, Hooks, wrappers, Skills, and documentation parse and agree with each other. It does not measure how a host's model behaves with the plugin installed, for this release or any other. An earlier observation stays attached to its original host, version, lifecycle, commit, and date; it is never promoted to the current release.

## Support Levels

| Level | Meaning |
| --- | --- |
| Checked in | The repository contains the named manifest, Hook, wrapper, Skill, or contract. |
| Statically validated | Deterministic repository checks passed for an identified tree. This is not host execution. |
| Observed | Someone observed the behavior in a named host version and lifecycle against an immutable release and reported it. |

A passing static check is not an observation. See [Field Validation](field-validation.md) for how to report one.

## Supported Hosts

The release tree provides one integration per host over the same Skills:

| Host | Checked-in integration | Lifecycle contract |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json`, `plugin/.codex-plugin/plugin.json`, `plugin/hooks/codex-hooks.json`, `plugin/hooks/codex-session-start.cmd`, and `plugin/skills/` | `SessionStart` on `startup`, `resume`, `clear`, `compact`, and `fork`; POSIX and Windows command variants are declared |
| Claude Code | `.claude-plugin/marketplace.json`, `plugin/.claude-plugin/plugin.json`, `plugin/hooks/claude-hooks.json`, and `plugin/skills/` | `SessionStart` on `startup`, `resume`, `clear`, `compact`, and `fork`; one POSIX shell command, which needs Git Bash on Windows |

Both manifests point to `./skills/` inside the installed plugin root `plugin/`. A catalog that selects `v0.17.0` or later installs only that subtree through a `git-subdir` source; earlier tags hold the plugin at the repository root. Codex and Claude Code are supported installation and runtime hosts from `0.15.0`; Claude Code records from `0.10.x` and earlier remain historical. From `0.16.0`, both hosts receive every bundled route, with one host-specific boundary: `agents-architect` writes only `AGENTS.md`, and a Claude Code project that has a `CLAUDE.md` does not load `AGENTS.md`, so there the skill stops and says so. `continuous-progress` keeps each host's operations detail in its own `references/`, and `delegate-simple-task` leaves the judgment of host settings to the host model. This is repository support, not proof of execution on every host release, operating system, shell, installation method, or policy configuration.

Codex holds a new or changed Hook until you trust it in `/hooks`; Claude Code runs it at the next `SessionStart` once the plugin loads. The [Hook Reference](reference/hooks.md) renders the exact checked-in commands for an optional comparison with an installed copy.

## Claude Code Package Format And Validation

`claude plugin validate --strict` accepted the Claude Code manifest and every shared Skill with Claude Code `2.1.308` on 2026-10-22. That check validates schema and Skill metadata; it does not prove installation or execution. The manifest declares only fields that strict validation accepts.

## Codex Package Format And Validation

Official documentation last verified: 2026-09-16.

OpenAI still supports `.codex-plugin/plugin.json` as a compatibility manifest. Its newer portable format uses root `plugin.json` and `extensions.com.openai`. An inline OpenAI extension replaces the compatibility overlay rather than merging with it. Axiom keeps its supported Codex layout and explicit hook path; adding a second manifest is not required for compatibility. See the official [packaging specification](https://developers.openai.com/plugins/build/plugins#plugin-structure).

The `hooks` declaration is supported in this layout. The listing schema also supports `interface.brandColorDark` and `interface.supportURL`; their value, contrast, and HTTPS requirements still apply. See the official [hook specification](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks) and [interface requirements](https://developers.openai.com/plugins/deploy/submission-errors#listing-and-interface-errors).

Current package checks use the repository's publication aggregate. A native package read is a separate parsing check; it does not prove strict schema validation, installation, hook trust, or execution. The response may omit listing fields, so it cannot establish whether those fields render in the UI. Contributor check ownership is in [CONTRIBUTING.md](../CONTRIBUTING.md#required-local-checks).

## Current Bounded Status

The machine-readable [release status](../evidence/release-status.json) binds the checked-in tree to its plugin version and runtime identity. It never records publication; the tag, the GitHub Release, and the marketplace catalogs are the publication state. Read its `targetRelease` and `runtimeIdentity` fields for the candidate version, immutable binding, and installed-runtime contract schema.

| Host | What the repository checks for each release |
| --- | --- |
| Codex | The package and Hook are checked in and pass the deterministic package and contract checks. |
| Claude Code | The package and Hook are checked in and pass the deterministic package and contract checks; strict `claude plugin validate` is available as a native check. |

The repository records no observation of an installed host for the current release. The cross-platform CI job runs the checked-in Hook commands on a Windows runner, the Codex wrapper under `cmd.exe` and the Claude Code command under Git Bash; Claude Code without Git Bash falls back to PowerShell, which does not run the command.

A source candidate cannot establish a future signed merge, immutable tag, final workflow result, or post-publication host observation.

An identical runtime digest may make older evidence relevant to the same bytes, but it does not create a new observation or change the older record's host, version, date, lifecycle, or status. From repository policy revision 118 until revision 138, a release candidate that changed a bundled route also carried checked-in fresh-session routing observation records for both hosts; the 0.22.0 and 0.22.1 releases predate that requirement. From revision 138 no release requires a record, and revision 141 archived the records with the routing evaluations, as [Field Validation](field-validation.md#archived-experiments) records.

On 2026-11-03 the maintainer found that the 0.26.0 fresh-session records were collected in case workspaces inside the maintainer's own repository, so each host also loaded that repository's root instruction file; earlier versions' harnesses were not retained and their workspace location is unknown. The records keep their lifecycle and outcome, the deviation is recorded in the [v0.26.0 note](releases/v0.26.0.md#host-evidence) and Issue #251, and from repository policy revision 130 every case workspace lies outside any instruction chain, as the archived [Host Observation Boundaries](https://github.com/wheakerd/axiom/blob/v0.27.2/evals/README.md#host-observation-boundaries) required.

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

Follow [Recording A Result](field-validation.md#recording-a-result) for the read-only test, required host and subject details, and sanitized reporting fields. It owns the reporting procedure for both compatibility and routing-case reports. Report what you observed and say which cases you did not run.

## Evidence Paths

Current sources:

- [current release status](../evidence/release-status.json); and
- [runtime identity](../evidence/runtime-identity.json) and its [policy](runtime-identity.md).

Historical sources:

- [v0.19.0 Codex host observation record](https://github.com/wheakerd/axiom/blob/v0.27.2/evidence/v0.19.0/codex/linux.json) (prior-release evidence, schema v4);
- [v0.19.0 Claude Code host observation record](https://github.com/wheakerd/axiom/blob/v0.27.2/evidence/v0.19.0/claude-code/linux.json) (prior-release evidence, schema v4);
- [archived version-bound host records, no-Hook experiments, and routing evaluations](field-validation.md#archived-experiments);
- [routing observation records](https://github.com/wheakerd/axiom/tree/v0.27.2/evals/results);
- [routing-context history](https://github.com/wheakerd/axiom/tree/v0.27.2/evals/context-budget/results); and
- [version notes](releases/).

These collections retain their original identities and outcomes, including failed, unknown, and unexecuted cases. Read the records directly for case-level, observer, commit/tree, token, timing, and investigation detail; those historical streams are intentionally not reproduced in this current user reference.

## Version Interpretation

Use the synchronized manifests to identify the source package version and an immutable version tag when describing a published release. A working-tree checkout, floating tag, or marketplace cache does not establish publication or the installed version. An installed marketplace snapshot may lag the source, so compare its behavior with documentation and Hook declarations from the same release or commit. Current observations include an explicit version and Hook review.

User-visible release history belongs in the [Changelog](../CHANGELOG.md). Contributor requirements for compatibility claims and optional native validation are in [CONTRIBUTING.md](../CONTRIBUTING.md).
