# Compatibility

Axiom's compatibility claims are evidence-bounded. Checked-in support,
historical validation, documentation-derived expectations, a current local
observation, and an unverified environment are different states.

## Checked-In Support

The release tree contains two wrappers over one shared skill source:

| Host | Checked-in support surface | Lifecycle surface |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, `hooks/codex-hooks.json`, and `./skills/` | `SessionStart` on `startup`, `resume`, `clear`, and `compact`; POSIX and Windows command variants are present |
| Claude Code | `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, `hooks/claude-hooks.json`, and `./skills/` | `SessionStart` on `startup`, `resume`, `clear`, and `compact`; `PreCompact` on `manual` and `auto` |

Both manifests declare the same `./skills/` directory. Platform-specific
marketplaces, manifests, and hooks remain separate. The distribution drift
guard checks agreement among the skill tree, both manifests, both marketplace
wrappers, and the README shared-skill list.

The shared source includes `optimize-codex-usage` on both hosts; neither host
receives a platform-specific copy. Its byte, word, line, reference, and
scenario measurements are repository-level proxies unless the active host
separately exposes exact usage for the scoped run.

The shared source also includes `review-axiom-task` on both hosts. Its review
contract is identical, but coverage depends on the task history, summaries,
tool results, and task-inspection interfaces each active host exposes.

This is repository support: it proves that the integration files exist and
declare the intended shape. It does not prove execution on every host release,
operating system, shell, installation method, or policy configuration.

## Current Observation

A current observation belongs to one installed host version and one fresh
session. To produce it:

1. Record the host and version plus the Axiom version or commit.
2. Open `/hooks` and compare every installed handler with the exact checked-in
   command in the [README](../README.md#inspect-the-hooks).
3. Start or reload the session.
4. Try the routed request and non-routing control in
   [Getting Started](getting-started.md), plus the explicit usage-optimization
   and task-review requests in [Examples](examples.md) when validating those
   routes.
5. Record pass, fail, not run, and unavailable results separately.

This document does not assert that a current end-to-end host check has run. A
present executable or manifest alone would be too weak to support that claim.

## Historical Validation

Historical results describe the tree and tooling at the time they were
recorded; they are not a current pass.

The Git record for `v0.5.1` reports:

- the distribution and publication guards, JSON and YAML parsing, hook and
  documentation agreement, skill-shape, English-only, size, artifact, and
  whitespace checks passed for the release candidate;
- a compacted task-context regression scenario kept turn coverage separate
  from raw-output coverage, admitted only the controlling user decision,
  rejected superseded candidates, and preserved the current-run versus
  later-run activation boundary;
- all six packaged Skills passed the local Skill Creator quick validator and
  Claude Code strict plugin validation passed;
- a fresh Codex or Claude Code session-level semantic-routing check was not
  run; and
- the bundled local `plugin-creator` validator continued to reject the Codex
  manifest's intentional `hooks` field, so that result remains a recorded
  validator discrepancy rather than a pass.

The Git record for `v0.5.0` reports:

- the distribution and publication guards, JSON and YAML parsing, hook and
  documentation agreement, skill-shape, English-only, size, artifact, and
  whitespace checks passed for the release candidate;
- fifteen static routing-contract scenarios and ten rollback-gate scenarios
  passed without being presented as host-native semantic routing evidence;
- all six packaged Skills passed the local Skill Creator quick validator and
  Claude Code strict plugin validation passed;
- a fresh Codex or Claude Code session-level semantic-routing check was not
  run; and
- the bundled local `plugin-creator` validator continued to reject the Codex
  manifest's intentional `hooks` field, so that result remains a recorded
  validator discrepancy rather than a pass.

The Git record for `v0.4.2` reports:

- the distribution and publication guards, JSON and YAML parsing, hook and
  documentation agreement, skill-shape, English-only, size, artifact, and
  whitespace checks passed for the release candidate;
- a complete real-task-history scenario confirmed that a first durable review
  with eight earlier completed turns and no prior update baseline starts at the
  task's oldest available turn rather than its latest work phase;
- all five packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin validation passed;
- Codex CLI `0.147.0` exposed no plugin-validation command; and
- the bundled local `plugin-creator` validator continued to reject the Codex
  manifest's intentional `hooks` field, so that result remains a recorded
  validator discrepancy rather than a pass.

The Git record for `v0.4.1` reports:

- the distribution and publication guards, JSON and YAML parsing, hook and
  documentation agreement, skill-shape, English-only, size, artifact, and
  whitespace checks passed for the release candidate;
- read-only forward scenarios distinguished a reusable instruction conflict
  from a one-off code defect without treating source-read volume as proof;
- all five packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin validation passed;
- Codex CLI `0.147.0` exposed no plugin-validation command; and
- the bundled local `plugin-creator` validator continued to reject the Codex
  manifest's intentional `hooks` field, so that result remains a recorded
  validator discrepancy rather than a pass.

The Git record for `v0.4.0` reports:

- the distribution and publication guards, JSON and YAML parsing, hook and
  documentation agreement, skill-shape, English-only, size, artifact, and
  whitespace checks passed for the release candidate;
- ten static routing-contract scenarios and ten rollback-gate scenarios
  passed without being presented as host-native semantic routing evidence;
- all five packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin validation passed;
- Codex CLI `0.147.0` exposed no plugin-validation command; and
- the bundled local `plugin-creator` validator continued to reject the Codex
  manifest's intentional `hooks` field, so that result remains a recorded
  validator discrepancy rather than a pass.

The Git record for `v0.3.1` reports:

- the distribution and publication guards, JSON and YAML parsing, hook and
  documentation agreement, skill-shape, English-only, size, artifact, and
  whitespace checks passed for the release candidate;
- Claude Code `2.1.220` strict marketplace and plugin validation passed;
- Codex CLI `0.146.0` exposed no plugin-validation command; and
- the bundled local `plugin-creator` validator rejected the Codex manifest's
  intentional `hooks` field even though its accompanying field guide describes
  that field, so the result remains a recorded validator discrepancy rather
  than a pass.

The earlier Git record for `v0.3.0` reports:

- the distribution drift, JSON, YAML, hook equality and safety, skill-shape,
  English-only, size, and whitespace checks passed for that release work;
- Claude Code 2.1.220 strict plugin validation passed; and
- a legacy local Codex validator reported a hooks-field compatibility conflict,
  while the release record noted that the then-current official schema
  supported the field.

See the durable [v0.5.1 release notes](releases/v0.5.1.md),
[v0.5.0 release notes](releases/v0.5.0.md),
[v0.4.2 release notes](releases/v0.4.2.md),
[v0.4.1 release notes](releases/v0.4.1.md),
[v0.4.0 release notes](releases/v0.4.0.md),
[v0.3.1 release notes](releases/v0.3.1.md), and
[v0.3.0 release notes](releases/v0.3.0.md) for their release narratives. These
historical results should not be generalized to a newer host, a different
platform, or the present working tree without fresh validation.

## Documentation-Derived Expectations

The installation, update, reload, and `/hooks` review commands in the
[README](../README.md) are the repository's checked-in user guidance. The
event names in this document reflect the checked-in hook matchers. The host,
however, owns marketplace behavior, command availability, lifecycle delivery,
trust UI, and plugin execution.

When host behavior changes, compare this guidance with current official host
documentation and an installed-session observation. Documentation consistency
is useful evidence; it is not runtime proof.

## Unverified Or Unavailable

Unless a current validation report says otherwise, treat these as unverified:

- compatibility with every earlier or later Codex or Claude Code version;
- every POSIX shell, Windows configuration, operating system, and host policy;
- successful marketplace fetch or remote release availability;
- end-to-end routing in a session that was not freshly started or reloaded;
- recovery of task history or raw tool output the host no longer exposes after
  compaction;
- semantic equivalence of task-review selection and reports across Codex and
  Claude Code without current observations from both hosts;
- exact tokens, credits, reasoning work, or cache hits not exposed by the
  current host;
- Windows hook execution inferred only from the presence of `commandWindows`;
  and
- any optional host-native validator that is missing or cannot run.

Do not convert an unavailable validator, missing host, command error, or
unobserved downstream behavior into a pass. Record the limitation and narrow
the compatibility claim to what was directly checked.

## Version Interpretation

Use the version in the platform manifests and an immutable version tag when
describing a release. Do not infer the current version from a floating tag or a
marketplace cache. An installed marketplace snapshot may also lag the checkout;
the hook review and explicit version record are therefore part of a current
observation.

Release history is tracked in the [Changelog](../CHANGELOG.md). Contributor
requirements for compatibility claims and optional host-native validation are
in [CONTRIBUTING.md](../CONTRIBUTING.md).
