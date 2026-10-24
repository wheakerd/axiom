# Compatibility

Axiom's compatibility claims are evidence-bounded. Checked-in integration,
static validation, an observed host session, and an independent reproduction
are different levels. A prior observation remains attached to its original
host, version, lifecycle, commit, and date; it is never silently promoted to
the current release.

## Support Levels

| Level | Meaning |
| --- | --- |
| `CHECKED-IN` | The repository contains the named manifest, Hook, wrapper, Skill, or contract. |
| `STATICALLY-VALIDATED` | Deterministic repository checks passed for an identified tree. This is not host execution. |
| `HOST-OBSERVED` | Behavior was observed in a named host/version and lifecycle against an immutable subject. |
| `EXTERNALLY-REPRODUCED` | An independent user supplied a reviewable result for the named subject. |
| `NOT-VERIFIED` | The claim has not been checked at the level it requires. |
| `NOT-RUN` | The case was intentionally or procedurally not executed. |
| `UNAVAILABLE` | A required host, interface, permission, authenticated session, or evidence source was unavailable. |

These labels are not interchangeable. A passing static validator cannot turn a
`NOT-RUN` or `UNAVAILABLE` host case into a pass. See
[Field Validation](field-validation.md) for the reporting protocol.

## Supported Hosts

The release tree provides one integration per host over the same Skills:

| Host | Checked-in integration | Lifecycle contract |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json`, `plugin/.codex-plugin/plugin.json`, `plugin/hooks/codex-hooks.json`, `plugin/hooks/codex-session-start.cmd`, and `plugin/skills/` | `SessionStart` on `startup`, `resume`, `clear`, `compact`, and `fork`; POSIX and Windows command variants are declared |
| Claude Code | `.claude-plugin/marketplace.json`, `plugin/.claude-plugin/plugin.json`, `plugin/hooks/claude-hooks.json`, and `plugin/skills/` | `SessionStart` on `startup`, `resume`, `clear`, `compact`, and `fork`; one POSIX shell command, which needs Git Bash on Windows |

Both manifests point to `./skills/` inside the installed plugin root `plugin/`.
A catalog that selects `v0.17.0` or later installs only that subtree through a
`git-subdir` source; earlier tags hold the plugin at the repository root. Codex and Claude Code are supported
installation and runtime hosts from `0.15.0`; Claude Code records from
`0.10.x` and earlier remain historical. From `0.16.0`, both hosts receive
every bundled route. `continuous-progress` keeps each host's operations detail
in its own `references/`, and `delegate-simple-task` leaves the judgment of
host settings to the host model. This is repository support, not proof of
execution on every host release, operating system, shell, installation method,
or policy configuration.

Compare the installed Hook with the exact commands in the
[Hook Reference](reference/hooks.md) before it runs: in Codex, before you trust
it in `/hooks`; in Claude Code, before the plugin loads.

## Claude Code Package Format And Validation

`claude plugin validate --strict` accepted the Claude Code manifest and every
shared Skill with Claude Code `2.1.308` on 2026-10-22. That check validates
schema and Skill metadata; it does not prove installation or
execution. The manifest declares only fields that strict validation accepts.

## Codex Package Format And Validation

Official documentation last verified: 2026-09-16.

OpenAI still supports `.codex-plugin/plugin.json` as a compatibility manifest.
Its newer portable format uses root `plugin.json` and `extensions.com.openai`.
An inline OpenAI extension replaces the compatibility overlay rather than
merging with it. Axiom keeps its supported Codex layout and explicit hook path;
adding a second manifest is not required for compatibility. See the official
[packaging specification](https://developers.openai.com/plugins/build/plugins#plugin-structure).

The `hooks` declaration is supported in this layout. The listing schema also
supports `interface.brandColorDark` and `interface.supportURL`; their value,
contrast, and HTTPS requirements still apply. See the official
[hook specification](https://learn.chatgpt.com/docs/hooks#plugin-bundled-hooks)
and [interface requirements](https://developers.openai.com/plugins/deploy/submission-errors#listing-and-interface-errors).

Current package checks use the repository's publication aggregate. A native
package read is a separate parsing check; it does not prove strict schema
validation, installation, hook trust, or execution. The response may omit
listing fields, so it cannot establish whether those fields render in the UI.
Contributor check ownership is in
[CONTRIBUTING.md](../CONTRIBUTING.md#required-local-checks).

## Current Bounded Status

The machine-readable [release status](../evidence/release-status.json) is the
canonical current summary. It binds the current plugin and runtime identity,
keeps current host states separate from prior evidence, and requires an
immutable subject before a host pass can be claimed.

The table summarizes that record. Read its `targetRelease` and
`runtimeIdentity` fields for the candidate version, immutable binding, and
installed-runtime contract schema.

| Host | Repository support | Current installed-host evidence | Current claim |
| --- | --- | --- | --- |
| Codex | `CHECKED-IN`; deterministic package and contract checks are available | `NOT-RUN` | `STATIC-ONLY` |
| Claude Code | `CHECKED-IN`; deterministic package and contract checks and strict `claude plugin validate` are available | `NOT-RUN` | `STATIC-ONLY` |

A source candidate cannot establish a future signed merge, immutable tag,
final workflow result, or post-publication host observation. See
[Routing Context Budget](../evals/context-budget/README.md) for the current
startup-document measurement and its separate static evidence boundary.

An identical runtime digest may make older evidence relevant to the same bytes,
but it does not create a new observation or change the older record's host,
version, date, lifecycle, or status.

## Known Limitations

Unless a current immutable result states otherwise, do not assume:

- compatibility with every earlier or later Codex or Claude Code version;
- execution across every POSIX shell, Windows configuration, operating system,
  installation method, or host policy;
- successful marketplace fetch, update, cache refresh, or remote release
  availability from repository presence alone;
- end-to-end routing in a session that was not freshly started;
- recovery of task history or tool output that the host no longer exposes;
- exact tokens, credits, reasoning work, cache hits, or latency that the host
  does not expose for the scoped run; or
- a missing optional native validator, command error, or unavailable host is a
  pass.

Static workflow execution on native runners is useful process-boundary evidence
for the exact checked-in commands, but it is not an installed-plugin or model-
session observation.

## Report A Compatibility Result

Follow [Recording A Result](field-validation.md#recording-a-result) for the
read-only test, required host and subject details, sanitized reporting fields,
and offline evidence-validation command. It owns the reporting procedure for
both compatibility and routing-case reports. Preserve each observed outcome
and leave unexecuted lifecycle cases `NOT-RUN`.

## Evidence Paths

Current sources:

- [current release status](../evidence/release-status.json);
- [runtime identity](../evidence/runtime-identity.json) and its
  [policy](runtime-identity.md);
- [routing-context measurement and record selection](../evals/context-budget/README.md); and
- [current route corpus](../evals/README.md).

Historical sources:

- [archived version-bound host records and no-Hook experiments](field-validation.md#archived-experiments);
- [routing observation records](../evals/results/);
- [routing-context history](../evals/context-budget/results/); and
- [version notes](releases/).

These collections retain their original identities and terminal `FAIL`,
`UNKNOWN`, `NOT-RUN`, and `UNAVAILABLE` states. Read the records directly for
case-level, observer, commit/tree, token, timing, and investigation detail;
those historical streams are intentionally not reproduced in this current
user reference.

## Version Interpretation

Use the synchronized manifests to identify the source package version and an
immutable version tag when describing a published release. A working-tree
checkout, floating tag, or marketplace cache does not establish publication or
the installed version. An installed marketplace snapshot may lag the source,
so compare its behavior with documentation and Hook declarations from the same
release or commit. Current observations include an explicit version and Hook
review.

User-visible release history belongs in the [Changelog](../CHANGELOG.md).
Contributor requirements for compatibility claims and optional native
validation are in [CONTRIBUTING.md](../CONTRIBUTING.md).
