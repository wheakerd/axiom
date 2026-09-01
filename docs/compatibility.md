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

The release tree provides separate host wrappers over one shared Skill source:

| Host | Checked-in integration | Lifecycle contract |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, `hooks/codex-hooks.json`, `hooks/codex-session-start.cmd`, and `skills/` | `SessionStart` on `startup`, `resume`, `clear`, and `compact`; POSIX and Windows command variants are declared |
| Claude Code | `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, `hooks/claude-hooks.json`, and `skills/` | `SessionStart` on `startup`, `resume`, `clear`, and `compact`; no Axiom `PreCompact` handler is declared |

Both manifests point to `./skills/`. The wrappers and Hooks remain
platform-specific; the public Skills do not have host-specific copies. This is
repository support, not proof of execution on every host release, operating
system, shell, installation method, or policy configuration.

Inspect the exact commands in the [Hook Reference](reference/hooks.md) before
trusting an installation.

## Current Bounded Status

The machine-readable [release status](../evidence/release-status.json) is the
canonical current summary. It binds the current plugin and runtime identity,
keeps current host states separate from prior evidence, and requires an
immutable subject before a host pass can be claimed.

The Git record for `v0.10.0` reports:

- target binding: `pending-immutable-tag`;
- checked-in status: `STATIC-ONLY`;
- installed-runtime identity: plugin `0.10.0`, runtime-contract schema v1;
- current Codex installed-host observation: `NOT-RUN`;
- current authenticated Claude Code observation: `UNAVAILABLE / NOT-RUN`.

See the [v0.10.0 version notes](releases/v0.10.0.md) for candidate-specific
architecture and validation detail. The candidate cannot bind itself to a
future signed merge, immutable tag, final workflow result, or post-publication
host observation.

### Current Matrix

| Host | Repository support | Current installed-host evidence | Current claim |
| --- | --- | --- | --- |
| Codex | `CHECKED-IN`; deterministic package and contract checks are available | `NOT-RUN` for v0.10.0 | Static support only |
| Claude Code | `CHECKED-IN`; deterministic package and contract checks are available | `UNAVAILABLE / NOT-RUN` for v0.10.0 | Static support only |

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
- end-to-end routing in a session that was not freshly started or reloaded;
- exactly-once Claude Code post-compaction loading without a current
  `SessionStart` observation for both routed and control requests;
- semantic parity between hosts when one host observation is unavailable;
- recovery of task history or tool output that the host no longer exposes;
- exact tokens, credits, reasoning work, cache hits, or latency that the host
  does not expose for the scoped run; or
- a missing optional native validator, command error, or unavailable host is a
  pass.

Static workflow execution on native runners is useful process-boundary evidence
for the exact checked-in commands, but it is not an installed-plugin or model-
session observation.

## Report A Compatibility Result

Use a disposable, non-sensitive repository and keep the test read-only:

1. Record the host and exact version, operating system, Axiom version or
   immutable commit, installation method, and lifecycle source.
2. Compare the installed Hook with the [checked-in reference](reference/hooks.md).
3. Start a new session or reload plugins.
4. Run the routed and control requests in
   [Getting Started](guides/getting-started.md).
5. Preserve `PASS`, `FAIL`, `NOT-RUN`, and `UNAVAILABLE` separately and record
   whether any mutation or tool event occurred.

Submit the bounded result with the
[compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml).
Use the [routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)
for a false positive, false negative, or unexpected clarification. Do not
include credentials, private conversations, or sensitive repository content.

The standard-library evidence validator is:

```bash
python3 scripts/check-compatibility-evidence.py --self-test
```

It validates checked-in records and negative fixtures; it does not execute a
host or create an observation.

## Evidence Paths

Current sources:

- [current release status](../evidence/release-status.json);
- [runtime identity](../evidence/runtime-identity.json) and its
  [policy](runtime-identity.md);
- [current routing-context record](../evals/context-budget/results/v0.10.0.json);
- [current route corpus](../evals/README.md); and
- [v0.10.0 version notes](releases/v0.10.0.md).

Historical sources:

- [version-bound host records](../evidence/);
- [routing observation records](../evals/results/);
- [routing-context history](../evals/context-budget/results/); and
- [version notes](releases/).

These collections retain their original identities and terminal `FAIL`,
`UNKNOWN`, `NOT-RUN`, and `UNAVAILABLE` states. Read the records directly for
case-level, observer, commit/tree, token, timing, and investigation detail;
those historical streams are intentionally not reproduced in this current
user reference.

## Version Interpretation

Use the synchronized manifest version and an immutable version tag when
describing a release. Do not infer the current version from a floating tag,
marketplace cache, or working-tree checkout. An installed marketplace snapshot
may lag the repository, so current observations include an explicit version and
Hook review.

User-visible release history belongs in the [Changelog](../CHANGELOG.md).
Contributor requirements for compatibility claims and optional native
validation are in [CONTRIBUTING.md](../CONTRIBUTING.md).
