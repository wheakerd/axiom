# Compatibility

Axiom's compatibility claims are evidence-bounded. Checked-in support,
historical validation, documentation-derived expectations, a current local
observation, and an unverified environment are different states.

## Checked-In Support

The release tree contains two wrappers over one shared skill source:

| Host | Checked-in support surface | Lifecycle surface |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, `hooks/codex-hooks.json`, and `./skills/` | `SessionStart` on `startup`, `resume`, `clear`, and `compact`; POSIX and Windows command variants are present |
| Claude Code | `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, `hooks/claude-hooks.json`, and `./skills/` | `SessionStart` on `startup`, `resume`, `clear`, and `compact`; the `compact` source follows manual or automatic compaction, and no Axiom `PreCompact` handler is declared |

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

The shared source includes `confirm-external-action` on both hosts. Its action
envelope and retry boundary are identical, while available confirmation UI,
idempotency support, and authoritative verification depend on the connected
service and host tool.

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
   [Getting Started](getting-started.md), plus the explicit usage-optimization,
   task-review, and external-action requests in [Examples](examples.md) when
   validating those routes.
5. For Claude Code compaction coverage, observe manual and automatic compaction
   separately. Record whether exactly one `SessionStart` event with source
   `compact` loaded the gate, then run the routed request and no-route control
   after compaction in separate reviewed sessions.
6. Record pass, fail, not run, and unavailable results separately.

This document does not assert that a current end-to-end host check has run. A
present executable or manifest alone would be too weak to support that claim.

## Historical Validation

Historical results describe the tree and tooling at the time they were
recorded; they are not a current pass.

The Git record for `v0.7.4` reports:

- the distribution and publication guards, JSON parsing, hook and documentation
  agreement, packaged Skill shape, protected schemas, English-only, size, link,
  artifact, and whitespace checks passed for the release candidate;
- three hook-lifecycle fixtures accepted the checked-in `SessionStart(compact)`
  control and rejected both an Axiom `PreCompact` context loader and a Claude
  Code `SessionStart` matcher without `compact`;
- the unchanged seven-Skill package shape passed the distribution and
  publication guards, while Claude Code `2.1.220` strict plugin and marketplace
  validation passed; and
- fresh manual and automatic compaction, exactly-one-injection, and
  post-compaction routed and no-route observations are `NOT-RUN` /
  `UNAVAILABLE`: the available environment had no Claude Code subscription or
  authenticated session, and no pass is implied.

The Git record for `v0.7.3` reports:

- the distribution and publication guards, JSON and strict YAML parsing, hook
  and documentation agreement, packaged Skill shape, transitive immutable
  Action pins, exact manifest schemas, English-only, size, link, artifact, and
  whitespace checks passed for the release candidate;
- thirty routing-contract fixtures, fifty-six traceable-Git contract fixtures,
  twelve external-action gate fixtures, ten rollback gate fixtures, four
  source-linked cross-route and resume contracts, and seventeen parser fixtures
  passed without being presented as fresh host semantic-routing evidence;
- focused disposable Git probes confirmed frozen-tree checkpoint construction,
  compare-and-swap branch installation, effective push-target precedence,
  one-time later-push target binding, and hostile commit-metadata rejection;
- the exact release-workflow JavaScript passed fifteen signed-target, strict
  tag, immutable-creation, version-binding, and event fixtures, while a mutated
  bypass copy was rejected by the publication guard;
- all seven packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin and marketplace validation passed; and
- the bundled local `plugin-creator` validator still rejected the intentional
  Codex `hooks` field, while a fresh installation, fresh-session route test,
  Codex Security Deep Scan, real external app action, and real persistent
  system change were not run.

The Git record for `v0.7.2` reports:

- the distribution and publication guards, JSON and strict YAML parsing, hook
  and documentation agreement, packaged Skill shape, immutable action pins,
  English-only, size, link, artifact, and whitespace checks passed for the
  release candidate;
- thirty routing-contract fixtures, fifty-six traceable-Git contract fixtures,
  twelve external-action gate fixtures, ten rollback gate fixtures, four
  source-linked cross-route and resume contracts, and sixteen parser fixtures
  passed without being presented as fresh host semantic-routing evidence;
- disposable Git `2.55.0` probes confirmed exact no-prune refresh, one-ref push,
  no followed tag, bypass of an unapproved pre-push hook, SHA-256 OIDs, and
  create-only backup-ref collision handling;
- all seven packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin and marketplace validation passed;
- malformed Skill frontmatter, malformed agent metadata, alternate moving
  Action syntax, and missing version-derived release notes were rejected; and
- the bundled local `plugin-creator` validator still rejected the intentional
  Codex `hooks` field, while a fresh installation, fresh-session route test,
  Codex Security Deep Scan, real external app action, and real persistent
  system change were not run.

The Git record for `v0.7.1` reports:

- the distribution and publication guards, JSON parsing, hook and
  documentation agreement, packaged Skill shape, immutable action pins,
  English-only, size, link, artifact, and whitespace checks passed for the
  release candidate;
- twenty-eight routing scenarios, thirty-seven traceable-Git security
  scenarios, twelve external-action scenarios, and ten rollback scenarios
  passed without being presented as fresh host semantic-routing evidence;
- focused Linux and Git `2.55.0` probes reproduced target-controlled
  `core.fsmonitor` and `core.sshCommand` execution, then confirmed the frozen
  non-executable process envelope blocked both paths while benign status still
  worked;
- all seven packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin and marketplace validation passed;
- a complete security review covered seventy-one artifacts across ten attack
  surfaces with no remaining reportable finding, while the rehearsal routing
  regressions selected read-only, clarification, and exact isolated-write
  outcomes as intended;
- the bundled local `plugin-creator` validator still rejected the intentional
  Codex `hooks` field, while Codex CLI `0.148.0` exposed no native
  plugin-validation command; and
- a fresh installation, fresh-session route-selection test, real external app
  action, and real persistent system change were not run.

The Git record for `v0.7.0` reports:

- the distribution and publication guards, JSON parsing, hook and
  documentation agreement, packaged Skill shape, immutable action pins,
  English-only, size, link, artifact, and whitespace checks passed for the
  release candidate;
- twenty-four routing scenarios, twenty-seven traceable-Git security
  scenarios, twelve external-action scenarios, and ten rollback scenarios
  passed without being presented as fresh host semantic-routing evidence;
- all seven packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin and marketplace validation passed;
- focused negative checks rejected a moving GitHub Action reference, an
  incomplete external-action contract, an unsafe Git transport, missing exact
  cleanup authority, and the absence of the current release document;
- the bundled local `plugin-creator` validator rejected the intentional Codex
  `hooks` field on both the candidate and clean `v0.6.1` baseline, while Codex
  CLI `0.148.0` exposed no native plugin-validation command; and
- a fresh installation, fresh-session route-selection test, and real external
  action were not run.

The Git record for `v0.6.1` reports:

- the distribution and publication guards, JSON parsing, hook and
  documentation agreement, skill shape, English-only, size, link, and
  whitespace checks passed for the release candidate;
- all six packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin and marketplace validation passed;
- negative checks rejected a fourth Codex starter prompt, a missing canonical
  route token, the prior broken relative link, and non-strict SemVer; and
- fresh install, disable, removal, and session-level semantic-routing checks
  were not run.

The Git record for `v0.6.0` reports:

- the distribution and publication guards, JSON and YAML parsing, hook and
  documentation agreement, skill-shape, English-only, size, artifact, and
  whitespace checks passed for the release candidate;
- focused reconciliation scenarios covered explicit preview and apply,
  non-English normalization, no-trigger controls, live-tree divergence,
  partial rollback, normative constraints, worker conflict, active-chain
  authority, and single-writer isolation;
- all six packaged Skills passed the local Skill Creator quick validator and
  Claude Code `2.1.220` strict plugin validation passed;
- a fresh Codex or Claude Code session-level semantic-routing check was not
  run; and
- the bundled local `plugin-creator` validator continued to reject the Codex
  manifest's intentional `hooks` field on both the release candidate and its
  clean baseline, so that result remains a validator discrepancy rather than
  a pass.

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

See the durable [v0.7.4 release notes](releases/v0.7.4.md),
[v0.7.3 release notes](releases/v0.7.3.md),
[v0.7.2 release notes](releases/v0.7.2.md),
[v0.7.1 release notes](releases/v0.7.1.md),
[v0.7.0 release notes](releases/v0.7.0.md),
[v0.6.1 release notes](releases/v0.6.1.md),
[v0.6.0 release notes](releases/v0.6.0.md),
[v0.5.1 release notes](releases/v0.5.1.md),
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

Claude Code's official lifecycle documentation identifies `SessionStart` with
the `compact` matcher as the post-compaction context-loading path for both
manual and automatic compaction. It does not make ordinary successful
`PreCompact` stdout available as model context. The checked-in wrapper follows
that distinction; a host observation is still required before claiming that a
particular installed version delivered it exactly once.

When host behavior changes, compare this guidance with current official host
documentation and an installed-session observation. Documentation consistency
is useful evidence; it is not runtime proof.

## Unverified Or Unavailable

Unless a current validation report says otherwise, treat these as unverified:

- compatibility with every earlier or later Codex or Claude Code version;
- every POSIX shell, Windows configuration, operating system, and host policy;
- successful marketplace fetch or remote release availability;
- end-to-end routing in a session that was not freshly started or reloaded;
- manual or automatic Claude Code compaction reinjection without a current
  observation of the `SessionStart` `compact` delivery and post-compaction
  routed and control requests;
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
