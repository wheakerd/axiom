# Changelog

This file records notable changes to Axiom. Historical entries are based on
the repository's version tags and the commits they identify.

## Unreleased

The active tree is the v0.8.11 sequential candidate for Issue #61. It preserves
the immutable v0.8.10 release and every historical observation without claiming
a checked-in current host pass.

## 0.8.11 - unreleased candidate

### Performance

- Reduced the always-loaded `using-axiom` gate from 7,739 to 6,673 UTF-8 bytes,
  increasing 8,192-byte headroom from 5.53% to 18.54% while retaining every
  public route, exact effective-instructions mode, near-miss exclusion,
  cross-route ownership rule, authorization boundary, and lifecycle stop.
- Removed duplicated ordinary Git staging and conflict mechanics from the
  startup surface; their directly reachable owner remains
  `traceable-git-submit/references/direct-submit.md`.
- Documented a minimum 15% engineering headroom target and a roughly 6-6.5 KiB
  preferred range, subordinate to equivalent routing and safety acceptance.

### Evidence Boundary

- Bound reduction experiments to the immediate predecessor candidate while
  retaining immutable v0.7.9 as the cumulative growth baseline.
- Recorded equivalent `PASS` results for the unchanged 67-case workload before
  and after the reduction: 47 routed cases and 20 no-route controls.
- The complete 110-test suite, focused 44-test routing run, publication guard,
  distribution drift guard, compatibility self-test, context-budget and
  canonical-facts checks, JSON parsing, English-only scan, instruction-size
  check, skill quick validation, and Claude Code strict offline validation pass
  in a disposable copy.
- The checked-in release status remains `STATIC-ONLY`. Codex host and lifecycle
  evidence is `NOT-RUN`; authenticated Claude Code host and lifecycle
  validation is `UNAVAILABLE / NOT-RUN`. Pull-request checks, signed merge,
  tag, immutable Release, GitHub Latest, and Issue closure remain future
  external gates.

See [the v0.8.11 release notes](docs/releases/v0.8.11.md).

## 0.8.10 - unreleased candidate

### Fixed

- Reworked `split_yaml_comment()` as an explicit index-driven scanner that
  consumes doubled single quotes together and keeps the single-quoted state
  active across the escaped literal quote.
- Prevented an internal `#` in a valid single-quoted scalar from becoming an
  inline comment delimiter while preserving the existing whitespace boundary
  for the first unquoted comment marker.
- Tightened single-quoted scalar validation so unterminated, odd-quoted, and
  unexpected-tail forms fail closed without adding a YAML dependency or
  expanding the accepted subset.
- Added focused valid and adversarial coverage for quoted hashes, adjacent and
  doubled quotes, escaped double-quoted content, empty scalars, comment
  boundaries, line endings, tabs, trailing spaces, and document markers.

### Evidence Boundary

- Corrected the current release-bound Codex observer contract so model-process
  stderr is bounded, privacy-safe, diagnostic-only, and non-causal. Process
  exit, JSONL lifecycle and unknown-event handling, structured response,
  semantic routing, mutation, protected-snapshot, and cleanup gates remain
  fail closed.
- Preserved the pre-correction full-batch Case 1 failure and the separately
  authorized diagnostic Case 1 failure as distinct terminal evidence. Neither
  result is retried or reclassified; the corrected signed merge requires a new
  complete 17-case batch.
- The complete 109-test suite, focused 6-test parser run, focused 17-test
  action and release-contract run, publication guard, distribution drift guard,
  compatibility self-test, context-budget and canonical-facts checks, JSON
  parsing, English-only scan, and whitespace checks pass locally on the
  candidate tree.
- Existing canonical workflows, action metadata, installed Skills, hooks,
  route selection, benchmark membership, models, reasoning settings,
  workflows, and action authority are unchanged.
- The checked-in release status remains `STATIC-ONLY`. Codex host and
  release-bound lifecycle evidence for this corrected tree is `NOT-RUN`;
  authenticated Claude Code host
  and lifecycle validation is `UNAVAILABLE / NOT-RUN`. Pull-request checks,
  signed merge, tag, immutable Release, GitHub Latest, and Issue closure remain
  future external gates.

See [the v0.8.10 release notes](docs/releases/v0.8.10.md).

## 0.8.9 - unreleased candidate

### Security

- Changed `all_evidence()` to require the exact singleton `True` for every
  owned field, rejecting integers, strings, collections, nulls, and every other
  non-boolean value without coercion.
- Routed both external-action and rollback evidence through the shared strict
  helper while preserving their required field sets and ignoring unknown fields
  unless an owned field is missing.
- Added exhaustive per-field type-confusion, true-missing-field, and
  unknown-field-substitution fixtures for external actions, rollback, and
  cleanup authority.

### Evidence Boundary

- The complete 104-test suite, focused 16-test safety run, publication guard,
  distribution drift guard, context-budget and canonical-facts checks, JSON
  parsing, English-only scan, and whitespace checks pass locally on the
  candidate tree.
- The aggregate reports 155 external-action, 127 rollback, and 238 traceable-Git
  contract fixtures, including the strict cleanup-authority matrix.
- Installed Skills, hooks, route selection, benchmark membership, models,
  reasoning settings, workflows, and action authority are unchanged.
- The checked-in release status remains `STATIC-ONLY`. Current Codex host and
  release-bound lifecycle evidence is `NOT-RUN`; authenticated Claude Code host
  and lifecycle validation is `UNAVAILABLE / NOT-RUN`. Pull-request checks,
  signed merge, tag, immutable Release, GitHub Latest, and Issue closure remain
  future external gates.

See [the v0.8.9 release notes](docs/releases/v0.8.9.md).

## 0.8.8 - unreleased candidate

### Fixed

- Corrected the final v0.8.4 routing-context measurements in the README and
  release notes from the versioned machine-readable record.
- Added a version-aware, standard-library release-facts renderer and read-only
  drift check. README follows the current manifest version, current release
  notes are always managed, and marker-managed historical notes remain bound
  to their own records.
- Added one human-reviewable structured Git route catalog that validates the
  `using-axiom` front door, renders the README and v0.8.4 route boundary, and
  directly supplies ten offline route fixtures.
- Rejected the superseded over-broad submit/publish/push claim, changed public
  measurements, and historical candidate values that lack both an explicit
  label and immutable commit or content identity.

### Evidence Boundary

- The complete 104-test suite, publication guard, distribution drift guard,
  canonical-facts check, JSON parsing, English-only scan, and Claude Code strict
  plugin validation pass on the candidate tree.
- The always-loaded `using-axiom` gate remains byte-identical at 7,739 UTF-8
  bytes with SHA-256
  `7da583bb99880157a7fbca539ebb0426f49cd79d2748be51e5ef5fe85eaa3996`.
  Installed Skills, hooks, route selection, benchmark membership, models,
  reasoning settings, and action authority are unchanged.
- The checked-in release status remains `STATIC-ONLY`. Current Codex host and
  lifecycle evidence is `NOT-RUN`; authenticated Claude Code host and lifecycle
  evidence remains `UNAVAILABLE / NOT-RUN`. A fresh release-bound Codex
  observation remains external to the Git tree.

See [the v0.8.8 release notes](docs/releases/v0.8.8.md).

## 0.8.7 - unreleased candidate

### Fixed

- Removed the repository Administration-only immutable-release settings read
  from the `GITHUB_TOKEN` publication workflow. The release operator performs
  that owner-side read-only preflight immediately before dispatch, while the
  workflow proves `immutable=true` from the exact final Release.
- Replaced ambiguous tag-shaped commit lookup with fully qualified local and
  remote Git tag refs. Live `main` and `v0.8.7` must both be lightweight refs to
  the exact signed dispatch commit before any Release mutation.
- Added bounded compensation and restart handling for an exact published but
  mutable Release. Only the frozen Release ID is deleted; a fresh authenticated
  listing must prove both its ID and tag absent, and the protected Git tag is
  never deleted.
- Allowed an explicit manual `Release signature guard` dispatch on one strict
  SemVer tag ref, matching the documented post-publication provenance gate.

### Evidence Boundary

- Added no-model regression coverage for the inaccessible endpoint, exact ref
  identities, published-mutable recovery, immutable classification, bounded
  cleanup identity, and exact-tag manual dispatch.
- Versioned the unchanged routing-context record and `STATIC-ONLY` evidence for
  v0.8.7. Installed behavior, the 67-case routing workload, the 17-case release
  acceptance contract, models, and reasoning settings remain unchanged.
- Kept the signed v0.8.6 tag as an unpublished audit record. The failed v0.8.6
  draft Release was removed; v0.8.5 remains GitHub Latest until v0.8.7 passes
  every release gate.

See [the v0.8.7 release notes](docs/releases/v0.8.7.md).

## 0.8.6 - signed tag, not released

The signed `v0.8.6` tag records the original Issue #57 candidate. Its immutable
publication workflow stopped before mutation when `GITHUB_TOKEN` received HTTP
403 from the repository Administration-only settings endpoint. No v0.8.6
GitHub Release exists; v0.8.7 carries the publication repair.

### Security

- Added a manual, main-only `Publish immutable release` workflow that accepts
  only one strict SemVer tag, checks out the exact dispatch commit without
  persisted credentials, serializes all repository-wide Latest publication,
  and rejects a different equal-or-newer current Latest SemVer.
- Added a standard-library release-evidence validator that uniquely selects a
  draft or already-immutable Release, freezes its numeric ID and evidence
  assets, downloads the exact GitHub bytes, requires the filename SHA-256,
  size, asset ID, and exposed API digest, then applies the existing 17-case
  external observation validator.
- Added a deterministic content-addressed attestation that binds the Release,
  version, tag, commit, tree, asset identity, digest, size, and validator result.
  The workflow uploads it to the frozen Release ID without replacement,
  downloads both remote assets, resumes safely after an earlier upload or
  publication, and verifies `immutable=true` plus GitHub Latest.
- Added fail-closed live preflights for the immutable-release setting, `main`
  and tag targets, and REST plus GraphQL GitHub-made signature evidence before
  mutation, immediately before publication, and after publication.
- Enabled immutable releases for `wheakerd/axiom`. GitHub directly reported
  `enabled: true` and `enforced_by_owner: false`; the setting applies to future
  releases and does not rewrite the mutable state of earlier Releases.
- Kept `Verify GitHub-signed release target` unchanged and separate: it still
  owns signed tag/history provenance, while the new stable check owns exact
  evidence-asset validity and publication immutability. The operator explicitly
  dispatches the unchanged guard after publication because `GITHUB_TOKEN`
  mutations do not trigger an ordinary `release: published` workflow run.

### Evidence Boundary

- Missing, duplicated, malformed, replaced, or digest-mismatched assets fail
  closed. Incomplete, non-pass, retrying, mutating, wrong-order, or wrong-subject
  observations also fail through the existing repository-owned validator.
- GitHub immutable Releases protect the tag and assets. The attestation also
  binds the exact title and release-notes digest so later metadata drift is
  detectable; this does not claim that GitHub blocks every metadata edit or
  Release deletion.
- The checked-in release status remains `STATIC-ONLY`. A fresh v0.8.6 Codex
  result must remain external until it is bound to the final tag, commit, tree,
  immutable Release, and attestation. Prior terminal results are unchanged.
- Installed Skills, hooks, route selection, corpus membership, benchmarks,
  models, reasoning settings, and action authority are unchanged. Authenticated
  Claude Code host evidence remains `UNAVAILABLE / NOT-RUN`.

See [the v0.8.6 release notes](docs/releases/v0.8.6.md).

## 0.8.5 - unreleased candidate

### Security

- Added a dedicated `unit-and-integration-tests` GitHub Actions check for pull
  requests and pushes to `main`. It uses `ubuntu-24.04`, exact Python `3.14.7`
  and Node.js `24.19.0`, prints the Ubuntu, Python, Node.js, and Git versions,
  and executes the complete verbose standard-library `unittest` suite.
- Kept the workflow read-only for same-repository and fork pull requests: it
  grants only `contents: read`, persists no checkout credential, references no
  secret or token expression, and pins every external Action to a full commit.
- Preserved `repository-guards` as the separate publication-policy signal and
  kept release provenance under the unchanged `Release signature guard`.
- Extended the checked-in action-graph contract and pull-request event fixtures
  to fail closed on workflow, permission, trigger, toolchain, command, or check
  name drift.

### Evidence Boundary

- The checked-in release status remains `STATIC-ONLY`. Local validation can
  prove the workflow and test contracts, while final-candidate GitHub Actions,
  pending or failing merge rejection, and a real fork run remain external
  gates.
- Updated and directly re-read the active main ruleset on 2026-08-26 UTC. It
  requires both `repository-guards` and `unit-and-integration-tests` from
  GitHub Actions with strict branch synchronization while preserving the
  signed-commit, squash-only, non-fast-forward, zero-bypass, and release-tag
  protections.
- Installed Skills, hooks, routing contracts, corpus membership, benchmarks,
  models, reasoning settings, and action authority are unchanged. Current
  Codex host and lifecycle evidence is `NOT-RUN`; authenticated Claude Code is
  `UNAVAILABLE / NOT-RUN`.

See [the v0.8.5 release notes](docs/releases/v0.8.5.md).

## 0.8.4 - unreleased candidate

### Changed

- Kept ordinary named-remote non-force commit and push requests host-native, so
  `git push origin main` does not load an Axiom Git Skill. A no-match result is
  neither denial nor authorization, and an exact expected staged payload does
  not manufacture a repository-state conflict.
- Added one parent-owned lightweight direct-submit reference for an explicit
  `$traceable-git-submit` simple push. It preserves the named remote, hooks, one
  push, normal Git result, and normal tracking update, with at most one query
  only when the result is materially ambiguous.
- Kept raw-target, fingerprint, compare-and-swap, backup, consolidation,
  recovery, force, and multi-target controls in their existing heavyweight
  phases. Predictable material push conflicts stop before a combined commit.
- Added deterministic hook, stale-tracking A/B/C, divergence, drift, force,
  multi-target, retry, fetch-separation, and pre-commit conflict coverage.
- Added two schema-v2 cases outside the frozen benchmarks, advanced both
  manifests to `0.8.4`, and updated the static workload to 67 cases while
  preserving all 30 benchmark memberships.

### Evidence Boundary

- The checked-in release status remains `STATIC-ONLY`. No v0.8.4 host or
  lifecycle observation binds the revised candidate, and it performs no remote
  action. Phase 3A's route-only passes and terminal behavior observation, and
  Phase 3B's terminal behavior observation, bind the prior patch only and remain
  separate external evidence.
- Authenticated Claude Code remains `UNAVAILABLE / NOT-RUN`; actual
  post-compaction lifecycle observation remains `NOT-RUN`.

See [the v0.8.4 release notes](docs/releases/v0.8.4.md).

## 0.8.3 - unreleased candidate

### Changed

- Changed direct non-force push validation so the immediately queried live
  remote tip owns the baseline while a local tracking ref remains
  informational. A verified live commit must be an ancestor of the final local
  commit, and identity, operation state, target, and live tip are rechecked
  immediately before one push.
- Preserved conservative stops for missing or non-local live objects,
  divergence, force, multiple targets, drift, failed push, and ambiguous
  verification. The route neither fetches nor updates a tracking ref merely
  because it is stale.
- Added one schema-v2 routing case outside both frozen benchmarks and a
  deterministic bare-remote behavioral test for the stale-tracking
  fast-forward case.
- Advanced both manifests together to `0.8.3`, updated the 65-case routing
  workload identity, and left both 13-case and 17-case benchmarks unchanged.

### Evidence Boundary

- The earlier signed v0.8.3 candidate and its two external terminal `UNKNOWN`
  records remain immutable unreleased history; neither is relabeled or used as
  current evidence.
- The stale-tracking route case is static contract evidence only. A separate
  single-case Codex diagnostic and a fresh complete release-bound observation
  remain required before release.
- Authenticated Claude Code remained `UNAVAILABLE / NOT-RUN`, and actual
  post-compaction behavior remained `NOT-RUN`.

See [the v0.8.3 release notes](docs/releases/v0.8.3.md) for the diagnostic
boundary and release gate.

## 0.8.2 - 2026-08-24

### Changed

- Clarified that publishing an already-prepared artifact selects only
  `confirm-external-action`. A separate persistent installation, deployment,
  migration, activation, or retention change still selects
  `reversible-system-change` as well when it has an external effect.
- Advanced both manifests together to `0.8.2` without changing route names,
  hooks, marketplace wrappers, corpus records, benchmarks, or authorization.
- Added a reviewed v0.8.2 routing-context record and an explicit validator mode
  for a content-addressed, external post-merge `codex-core-v2` observation.
- Added the exact Codex CLI 0.149.1 public JSONL discriminator taxonomy under
  the existing routing-evaluation validator. Items are classified before
  lifecycle sequencing; tool/action, error, unknown, malformed, invalid-status,
  and post-terminal events fail closed without retaining private payload.
- Replaced the warning-producing hook-trust bypass in the documented
  release-bound setup with a native zero-model `hooks/list` and
  `config/batchWrite` trust handshake after installed-hook byte verification.
  The disposable `CODEX_HOME` must now use an owner-only runtime root outside
  the system temporary directory.

### Evidence Boundary

- Preserved the F4 terminal `FAIL` after eight calls: the publication-only case
  incorrectly selected both routes. A later candidate-only F5 batch passed all
  19 planned calls, including three Case 1 variance samples, with zero tool
  events and unchanged protected snapshots.
- F5 is bound to the unreleased 0.8.1 candidate commit
  `298268ac0cfcaac84af22d7117e126f57e72152c`; it is not final v0.8.2 evidence.
  Actual post-compaction lifecycle remains `NOT-RUN`, and authenticated Claude
  Code remains `UNAVAILABLE / NOT-RUN`.
- The signed v0.8.2 release-bound batch remains terminal `FAIL` at Case 1 after
  unexpected tool use. A separate corrected-preflight Case 1 diagnostic passed
  once with zero tool events, but it is variance evidence rather than Stage 3
  acceptance. The signed v0.8.3 candidate and both external terminal `UNKNOWN`
  attempts remain distinct unreleased history.
- A later complete-batch attempt against signed v0.8.2 repair commit
  `9dbc2592dc2e544d3f62aafb2788af7efc503840` also stopped at Case 1 without
  retry. Its route, V3 response, mutation fields, zero-tool observation, and
  protected snapshots were valid, but the old hook-trust bypass necessarily
  emitted a startup `ConfigWarning`; the fail-closed JSONL observer correctly
  treated the resulting error item as terminal. Cases 2-17 remain `NOT-RUN`.
- The final signed repair merge received a complete 17-call Codex pass. The
  immutable `v0.8.2` tag, GitHub Release, and content-addressed observation
  asset bind that result to the released commit and tree; Issue #34 closed only
  after those checks succeeded.

See [the v0.8.2 release notes](docs/releases/v0.8.2.md) for the preserved
candidate evidence, context review, and completed acceptance sequence.

## 0.8.1 - 2026-08-23

### Added

- Added append-only `codex-core-v2` records for immutable Axiom v0.8.0:
  Codex stopped at Case 1 with terminal `FAIL`, while authenticated Claude Code
  remains `UNAVAILABLE / NOT-RUN` because no subscription or session exists.
- Added a v0.8.1 routing-context record. The always-loaded gate and cumulative
  delta are unchanged, while exact scoped Codex usage records 14,907 input
  tokens, 1,920 cached input tokens, and 17,984 milliseconds. The host reported
  116 output tokens, which the existing context schema does not store.

### Changed

- Extended the existing routing validator to select v1 or v2 benchmark order,
  route bounds, diagnostics, observer provenance, call limits, and immutable
  response-schema bindings without changing either route contract.
- Advanced both manifests together to `0.8.1` and kept the package, hooks,
  Skills, routing gate, corpus, benchmarks, and historical evidence unchanged.

### Evidence Boundary

- The sole v0.8.0 Codex attempt returned a valid V3 response with
  `agent-plugin-architect`, zero clarification, and no observed mutation, but
  the observer recorded a mutation attempt after two unexpected tool events.
  Stop-on-first-failure left Cases 2-17 `NOT-RUN`; no case was retried and the
  unexpected tool categories are not inferred.
- Version 0.8.1 records that failed Stage 3 attempt; it does not fix the route,
  claim Stage 3 acceptance, or close GitHub Issue #34. Codex lifecycle,
  v0.8.1 host behavior, authenticated Claude Code, marketplace, portal,
  publication, and active-user installation remain unverified or not run.

## 0.8.0 - 2026-08-23

### Added

- Added the direct `agent-plugin-architect` Skill and seven root-reachable
  references for package inventory, route and trigger contracts, packaged
  Skill architecture, hook trust, cross-host packaging, evaluation evidence,
  and validation reporting.
- Added additive seven-route corpus, host-response, and benchmark contracts
  with 17 focused packaged-plugin cases. The frozen six-route schemas,
  benchmark, and nine historical observations remain byte-identical.
- Added v0.8.0 context-budget and release-status records that preserve Codex
  host behavior as `NOT-RUN` and authenticated Claude Code as `UNAVAILABLE /
  NOT-RUN`.

### Changed

- Advanced both plugin manifests to `0.8.0` and exposed the same shared
  eight-Skill tree to Codex and Claude Code without changing either marketplace
  wrapper or startup hook.
- Extended `using-axiom` only for explicit packaged Codex or Claude Code plugin
  architecture. Repo-local instruction systems, generic plugin work, Git,
  installation, publication, deployment, and external effects retain their
  existing owners and phase boundaries.
- Measured the always-loaded gate at 6,150 bytes, 788 words, 111 lines, one
  direct reference, and an estimated 1,538 tokens. The 251-byte cumulative
  increase from v0.7.9 is below both review triggers.

See [the v0.8.0 release notes](docs/releases/v0.8.0.md) for package shape,
validation evidence, context metrics, and unavailable host checks.

## 0.7.12 - 2026-08-23

### Added

- Accepted the `agent-plugin-architect` route contract for Stage 2, including
  its canonical description, ownership boundaries, routing cases, two-route
  limit, evidence requirements, successor evaluation rules, and stop
  conditions.
- Added a versioned v0.7.12 routing-context record that preserves the exact
  immutable v0.7.9 gate metrics and keeps every current lifecycle and usage
  observation explicitly unrun or unavailable.

### Changed

- Advanced both plugin manifests to `0.7.12` for design and release bookkeeping
  only. The accepted route is not implemented in this release; Stage 2 is
  intended for v0.8.0.
- Kept the current six-route gate, all seven direct public Skills, hooks,
  marketplace wrappers, historical schemas and benchmarks, workflows, model,
  reasoning, telemetry, authorization boundaries, and runtime dependencies
  unchanged.

See [the v0.7.12 release notes](docs/releases/v0.7.12.md) for the accepted
design boundary, static validation evidence, and unavailable host checks.

## 0.7.11 - 2026-08-23

### Added

- Added a font-free, repository-owned Axiom mark for both the Codex marketplace
  logo and composer icon, plus light- and dark-surface brand colors, website and
  support links, a concise listing description, and three non-mutating starter
  prompts.
- Added standard-library validation and negative controls for the supported
  Codex listing fields, HTTPS links, color contrast, prompt limits, safe
  in-package assets, SVG safety, image dimensions, file formats, and file size.

### Changed

- Advanced both plugin manifests to `0.7.11` while leaving the shared Skills,
  hook definitions, route behavior, authorization boundaries, model settings,
  reasoning settings, and runtime dependency surface unchanged.
- Kept `interface.screenshots` absent because Axiom is a skills-only plugin
  without MCP custom UI; no synthetic marketplace result or host success is
  claimed.

See [the v0.7.11 release notes](docs/releases/v0.7.11.md) for the listing
contract, static validation evidence, and unavailable host and portal checks.

## 0.7.10 - 2026-08-23

### Added

- Added a versioned, standard-library routing-context budget for the
  always-loaded `using-axiom` gate, with reproducible UTF-8 byte, word, line,
  direct-reference, and explicitly estimated `ceil(bytes / 4)` measurements.
- Represented fresh, resume, clear, manual-compaction, automatic-compaction,
  and unchanged-session duplicate-injection scenarios while preserving Codex
  host observation as `NOT-RUN` and authenticated Claude Code as
  `UNAVAILABLE / NOT-RUN`.
- Added focused policy and negative controls that derive duplicate injection
  from observed event counts and reject any claimed reduction without
  equivalent before/after routed and no-route passing evidence.

### Changed

- Established immutable v0.7.9 as the cumulative always-loaded baseline and
  documented a 256-byte-or-5% growth threshold that triggers review and
  justification rather than automatic rejection.
- Kept `skills/using-axiom/SKILL.md`, route selection, lifecycle hooks, safety
  rules, authorization boundaries, stop conditions, model settings, and
  reasoning settings unchanged; no size reduction was manufactured for this
  release.

See [the v0.7.10 release notes](docs/releases/v0.7.10.md) for metric
classification, scenario status, threshold semantics, validation evidence, and
known host-observation gaps.

## 0.7.9 - 2026-08-23

### Security

- Added a dated repository-governance record that distinguishes active GitHub
  branch and tag rulesets from checked-in validation and documents every
  observed control, unavailable field, exact required check, and manual
  minimum-permission re-verification step.
- Declared the repository owner for critical workflows, manifests, hooks,
  routing entry point, validation code, scripts, tests, security policy, and
  governance files in `.github/CODEOWNERS` without claiming an approval rule
  that GitHub does not currently enforce.

### Changed

- Added standard-library publication checks and a focused negative test that
  fail when the governance snapshot loses a required fact or a sibling
  critical path loses its exact owner.
- Kept governance auditing manual and read-only. No scheduled or dispatch
  workflow was added, and no workflow received repository-administration
  permission merely to inspect rulesets.

See [the v0.7.9 release notes](docs/releases/v0.7.9.md) for the observed policy,
security boundary, validation evidence, and explicitly unavailable controls.

## 0.7.8 - 2026-08-21

### Added

- Added a versioned, host-independent JSONL routing corpus with 47 reviewed
  cases covering every public route, near misses, overlap, ambiguity,
  multilingual requests, lifecycle states, and untrusted input.
- Added a fixed 13-case Codex acceptance and safety manifest, a strict host
  response schema, and separately labeled Codex and Claude Code observation
  records bound to immutable Axiom source identities.
- Added standard-library publication policy and focused negative fixtures for
  corpus coverage, stable IDs, result arithmetic, privacy, lifecycle, route,
  clarification, mutation-attempt, and status fields.

### Changed

- Documented the isolated, read-only black-box method derived from OpenAI's
  official plugin evaluation repository without adding an installed runtime
  dependency or uploading private conversations.
- Recorded the initial authorized Codex run as `FAIL` after a nonzero exit
  without a bounded response, preserved its unknown fields as null, and left
  cases 2-13 `not-run` under the no-retry stop policy.
- Recorded the independent Codex recovery run separately as `FAIL`: Case 1
  returned the expected routing, clarification, and mutation fields, but the
  observer failed closed on unexpected stderr and left cases 2-13 `not-run`.
- Reduced the model-facing response schema to OpenAI's documented Structured
  Outputs subset while retaining exact-field, uniqueness, length, privacy, and
  semantic constraints in standard-library offline validation.
- Made host observations append-only by stable run ID and exact response-schema
  path plus SHA-256, preserving all failed Codex runs without turning correct
  partial routing output into a batch pass.
- Recorded recovery-2 as a separate terminal `FAIL`: Case 1 returned the exact
  expected routing, clarification, and mutation fields, but stderr-v2 found two
  unexpected categorized lines, stopped without retry, and retained no raw
  stderr text or hashes.
- Recorded recovery-3 as a terminal `FAIL`: Cases 1-10 passed, then the
  ambiguity case selected two routes with zero clarification instead of no
  route and one clarification. Stderr remained diagnostic-only and non-causal;
  Cases 12-13 were not run and no retry occurred.
- Made ambiguity precedence explicit before usage optimization: a delegated
  choice among materially different implementations now selects no route and
  asks one clarification. Candidate 1 did not observe the repaired case because
  malformed output stopped that batch; Candidate 4 later observed it passing.
- Recorded the append-only unreleased-candidate batch as terminal `UNKNOWN`:
  Cases 1-10 passed, Case 11 returned malformed bounded output, and Cases 12-13
  remained `not-run` under the no-retry stop policy. Its tag stays explicitly
  null, and no current-release host pass is inferred.
- Separated exact model-schema diagnostics from privacy-safe response
  acceptance. Route uniqueness, evidence non-emptiness, length, uniqueness,
  and privacy remain fail-closed publication gates without being mislabeled as
  unsupported model-schema constraints.
- Recorded the second immutable unreleased-candidate batch as terminal
  `UNKNOWN`: Cases 1-8 passed, Case 9 hit the legacy combined evidence
  classifier, and Cases 10-13 remained `not-run`. The destroyed response is not
  reclassified, no case was retried, and no current host pass is inferred.
- Recorded the third independent unreleased-candidate batch as terminal
  `FAIL`: Cases 1-7 passed, Case 8 matched its route, clarification, and mutation
  contract but exceeded the bounded evidence-length acceptance gate, and Cases
  9-13 remained `not-run`. The batch stopped without retry, retained no rejected
  response text, and does not establish a host pass.
- Added a byte-distinct V2 host-response schema containing only the five
  routing and mutation fields needed for evaluation. Candidate 4 publishes
  fixed observer-derived evidence rather than model-authored prose; route
  uniqueness and all lifecycle, tool, mutation, privacy, and snapshot gates
  remain fail closed. Its immutable unreleased-candidate batch passed all 13
  fixed cases once without retry, with zero routing, clarification, or mutation
  regressions. Candidate 3 and every earlier terminal outcome remain frozen.
- Kept authenticated Claude Code host and lifecycle evaluation explicitly
  `UNAVAILABLE / NOT-RUN` because no subscription or authenticated session was
  available; no Claude Code host pass is inferred.

See [the v0.7.8 release notes](docs/releases/v0.7.8.md) for the corpus contract,
bounded host method, validation evidence, and known host-observation limits.

## 0.7.7 - 2026-08-21

### Changed

- Split the publication validator into standard-library policy modules for
  manifests, hooks, Markdown, strict YAML, routing, traceable Git, GitHub
  Actions, release provenance, and repository layout.
- Moved deterministic event and mutation fixtures into `tests/fixtures/` and
  added focused `unittest` coverage for each major policy domain.
- Kept `python3 scripts/check-publication.py` as the stable aggregate command,
  added domain ownership to failure output, derived the release version from
  the synchronized manifests, and discovered release notes from
  `docs/releases/`.

### Validation

- Preserved the valid-tree aggregate output and exit behavior, including all
  existing mutation-policy reasons, without adding an installed or third-party
  runtime dependency.
- Kept the aggregate runtime at the measured 0.26-second baseline before the
  version-document update; the final candidate runtime is recorded in the
  release notes.

See [the v0.7.7 release notes](docs/releases/v0.7.7.md) for module ownership,
focused test coverage, runtime evidence, and known host-validation limits.

## 0.7.6 - 2026-08-21

### Fixed

- Separated read-only pull-request tree validation from release provenance so
  unsigned same-repository and fork contributions can run the distribution and
  publication validators without a repository-origin gate.
- Kept provenance enforcement on protected `main`, strict immutable `v*` tags,
  bounded release-candidate dispatches, and published or edited GitHub Releases.
- Added deterministic event-graph and release-provenance fixtures for the eight
  Issue #26 scenarios, including invalid trees, unsigned `main`, ancestry drift,
  tag mutation, manifest-version mismatch, and mismatched Release targets.

### Security

- Restricted the pull-request workflow to `contents: read`, an immutable
  checkout with `persist-credentials: false`, and exact local validators with no
  secret or write-token path.
- Preserved GitHub-signature, approved-history, strict-tag, and manifest-version
  checks for merged and published release targets.

See [the v0.7.6 release notes](docs/releases/v0.7.6.md) for the workflow trust
boundary, validation evidence, and live-fork acceptance gap.

## 0.7.5 - 2026-08-21

### Added

- Added a versioned, privacy-safe compatibility evidence schema with immutable
  tag and commit binding, explicit routed and no-route cases, and preserved
  `pass`, `fail`, `not-run`, and `unavailable` outcomes.
- Added a standard-library evidence validator with negative fixtures and a
  post-tag record mode for release-asset validation.
- Recorded fresh Codex `0.149.0` startup routing and no-route observations for
  immutable `v0.7.4`, while preserving unobserved Codex compaction and all
  unavailable Claude Code cases without inferring a pass.

### Changed

- Made publication validation execute the evidence validator and require the
  schema, release status, immutable prior-release records, and v0.7.5 release
  documentation.
- Marked the checked-in v0.7.5 host status `STATIC-ONLY`; prior-release evidence
  cannot be promoted to the current release, whose final commit cannot be
  self-embedded in the commit that creates it.

See [the v0.7.5 release notes](docs/releases/v0.7.5.md) for the evidence
boundary, validation results, and post-tag asset option.

## 0.7.4 - 2026-08-21

### Fixed

- Removed the ineffective Claude Code `PreCompact` context loader because
  ordinary successful stdout from that event is not injected into model
  context.
- Kept `SessionStart` with the `compact` matcher as the single Axiom routing
  injection after both manual and automatic compaction, and synchronized the
  public lifecycle and troubleshooting guidance.
- Added publication fixtures that reject a restored `PreCompact` context
  loader or a Claude Code `SessionStart` matcher that omits `compact`.

See [the v0.7.4 release notes](docs/releases/v0.7.4.md) for validation evidence
and known limits.

## 0.7.3 - 2026-08-20

### Fixed

- Bound checkpoint commits to the frozen staged tree and installed them with
  compare-and-swap ref updates, preserving concurrently staged paths instead
  of committing them outside the authorized path set.
- Resolved the effective Git push destination independently from the fetch
  upstream, added a one-time later-push target binding, and rejected hostile
  commit metadata before it can reach a terminal or public commit message.
- Extended Action-pin validation through local composite actions and reusable
  workflows, and restricted protected manifests to their exact owned schemas.
- Required strict, version-matched, creation-only release tags and made the
  publication guard execute the exact workflow gate against positive,
  negative, and mutation-bypass fixtures.

## 0.7.2 - 2026-08-20

### Fixed

- Separated remote refresh from push authority, replaced broad configured
  fetch and pruning with one source-ref fetch plus a compare-and-swap tracking
  ref update, and closed push against tags, submodules, signing, push options,
  and unapproved hooks.
- Added SHA-256 Git object support and create-only backup-ref transactions so
  valid repositories no longer stop at 40-character OIDs and concurrent
  recovery refs cannot be overwritten.
- Required current explicit edit authority regardless of Axiom provenance,
  selected both external-action and reversible-change gates for persistent
  external effects, and failed closed across resume or compaction gaps.
- Replaced regex-only metadata and Action-pin inspection with strict bounded
  parsers and negative fixtures, derived current release documentation from the
  release version, and verified release targets by ancestry and GitHub
  signature across main, tag, and GitHub Release events.

## 0.7.1 - 2026-08-20

### Fixed

- Required a frozen non-executable Git process boundary before every
  `traceable-git-submit` command so target-controlled configuration, helpers,
  hooks, filters, transport commands, and ambient Git state cannot silently run.
- Distinguished read-only workflow rehearsal from an authorized isolated
  restore rehearsal, and kept that write separate from candidate preparation,
  promotion, complete execution, and cleanup.

## 0.7.0 - 2026-08-20

### Added

- Added `confirm-external-action` to bind consequential app actions to an exact
  actor, target, payload, disclosure, cost, count, and retry envelope before
  one execution and authoritative verification.

### Fixed

- Required literal argument vectors, validated refs and transports, opaque
  remote capture, and no-follow Git-metadata containment throughout
  `traceable-git-submit`.
- Made post-consolidation cleanup independently authorized and recoverable via
  a persisted `cleanupReady` state.
- Pinned every third-party GitHub Action to an immutable commit and added a
  publication guard against moving action references.

See [the v0.7.0 release notes](docs/releases/v0.7.0.md) for validation evidence
and known limits.

## 0.6.1 - 2026-08-18

### Fixed

- Limited Codex starter prompts to the three entries the host displays and
  made the AGENTS audit starter explicitly read-only.
- Anchored routing validation to the packaged front door and Skill
  descriptions, including every canonical `effective-instructions` mode.
- Repaired the agents-architect validation route to its sibling instruction
  document contract.
- Qualified host-controlled auto-update behavior and documented safe disable
  and removal workflows.

See [the v0.6.1 release notes](docs/releases/v0.6.1.md) for validation evidence
and known limits.

## 0.6.0 - 2026-08-18

### Added

- Added the explicitly user-triggered `effective-instructions:reconcile` and
  `effective-instructions:reconcile-preview` modes for comparing existing
  AGENTS guidance with current implementation.
- Added an atomized evidence ledger that separates claim kind, observed
  status, disposition, and write action before any rule is corrected, moved,
  or removed.

### Changed

- Made the live filesystem working tree the default reconciliation baseline,
  with staged divergence, unstaged, untracked, and material ignored content
  recorded separately from `HEAD`, named refs, and history.
- Required one coordinator, three independent read-only auditors, and one
  isolated non-coordinator writer after ledger freeze; incomplete role
  coverage now stops writes and is reported as `NOT-RUN`.
- Kept rollback, interrupted execution, compaction, and model or agent handoff
  as post-activation evidence rather than autonomous reconciliation triggers.
- Added focused routing and evidence scenarios for preview/apply boundaries,
  partial rollback, normative constraints, worker conflict, and active-chain
  authority.

See [the v0.6.0 release notes](docs/releases/v0.6.0.md) for validation evidence
and known limits.

## 0.5.1 - 2026-08-17

### Fixed

- Separated task-turn coverage, raw-output coverage, and unread required
  history so a compacted review cannot imply that unavailable tool output was
  recovered.
- Prevented superseded or narrowed proposals from being revived after
  compaction unless the user explicitly reauthorizes them.

### Changed

- Made current-run versus later-run activation explicit for durable
  `AGENTS.md` updates and required fresh-session loading claims to be marked
  verified, not run, or unavailable.
- Consolidated review-window and candidate-disposition ownership in the
  context-evidence reference instead of repeating it across update paths.
- Added a focused compaction regression scenario for task-context maintenance.

See [the v0.5.1 release notes](docs/releases/v0.5.1.md) for validation evidence
and known limits.

## 0.5.0 - 2026-08-15

### Added

- Added `review-axiom-task`, an explicitly triggered read-only retrospective
  for Axiom route choice, scope, authorization, actions, evidence, stops, and
  outcomes across host-visible task history.

### Changed

- Extended the shared router, public documentation, Codex interface metadata,
  and offline routing scenarios for task reviews without adding telemetry,
  persistent logs, background work, or new mutation authority.

See [the v0.5.0 release notes](docs/releases/v0.5.0.md) for validation evidence
and known limits.

## 0.4.2 - 2026-08-12

### Fixed

- Made a first `effective-instructions` or preview review cover the current
  task from its oldest available turn through the trigger instead of starting
  at the latest work phase or Skill activation point.
- Limited incremental review baselines to prior completed reviews that record
  their start, reviewed-through point, and candidate dispositions; ordinary
  AGENTS reads, narrow edits, and task completion no longer imply a baseline.
- Required task-history inspection to reach the established review-window
  boundary while keeping raw tool replay proportional to candidate decisions.
- Prevented newest-phase-only extraction from being reported as a complete task
  review and separated review coverage from the number of accepted updates.

See [the v0.4.2 release notes](docs/releases/v0.4.2.md) for validation evidence
and known limits.

## 0.4.1 - 2026-08-12

### Changed

- Extended AGENTS Architect task evidence to treat repeated source reads,
  history recovery, user corrections, and missing-route scans as signals for
  an instruction-maintenance review rather than automatic proof of a gap.
- Added explicit `instruction-gap`, `routing-gap`, `validation-gap`,
  `expected-live-verification`, and `one-off-code-defect` dispositions so
  durable guidance remains scoped and implementation defects stay in source
  or regression tests under separate authorization.
- Applied the retrieval-friction review to both `effective-instructions` and
  `effective-instructions:preview`, including required reporting of source
  checks that remain necessary.

See [the v0.4.1 release notes](docs/releases/v0.4.1.md) for validation evidence
and known limits.

## 0.4.0 - 2026-08-10

### Added

- Added `optimize-codex-usage`, an explicitly triggered workflow for reducing
  or diagnosing Codex credit, token, context, Skill/AGENTS/MCP-loading, tool,
  validation, and reporting overhead without weakening quality or safety.

### Changed

- Reduced the always-loaded `using-axiom` gate and moved explicit marketplace
  refresh detail to an on-demand reference.
- Replaced AGENTS Architect's forwarding indexes with direct one-hop reference
  routes and made inventory, scenarios, validation, and reporting proportional
  to the changed surface.
- Split direct history-preserving Git submission from checkpoint metadata and
  consolidation so publish/push requests load only their active phase.
- Shortened the reversible-change parent while retaining rollback,
  authorization, sensitive-data, and layered completion gates before mutation.
- Updated shared documentation, UI metadata, both platform wrappers, and
  publication validation for the five-skill source without changing the
  hook behavior.

See [the v0.4.0 release notes](docs/releases/v0.4.0.md) for validation evidence
and known limits.

## 0.3.1 - 2026-07-31

### Added

- Expanded public onboarding, architecture, examples, trust, compatibility,
  and release documentation.
- Added contributor guidance plus focused bug, feature, and pull-request
  intake templates.
- Added an offline publication validator for durable documentation, repository
  metadata, hook declarations, and packaged-skill shape.

### Changed

- Reorganized the public project introduction around installation, first-use
  verification, observable routing, and explicit non-goals.
- Extended the read-only repository guard workflow to run both distribution
  drift and publication checks without persisting checkout credentials.
- Synchronized the Codex and Claude Code manifests at version `0.3.1`.

See [the v0.3.1 release notes](docs/releases/v0.3.1.md) for validation evidence
and known limits.

## 0.3.0 - 2026-07-29

### Added

- Added the Claude Code plugin manifest, marketplace wrapper, and isolated
  `SessionStart` and `PreCompact` hooks.
- Added a standard-library distribution drift guard and a read-only GitHub
  Actions job that compares the checked-in skill tree with both platform
  wrappers and the README shared-skill list.

### Changed

- Kept Codex and Claude Code on one shared `skills/` source while separating
  their manifests, marketplaces, and hook definitions.
- Moved the Codex hook definition to `hooks/codex-hooks.json` and declared the
  Claude Code hook separately at `hooks/claude-hooks.json`.
- Synchronized both plugin manifests at version `0.3.0`.

See [the v0.3.0 release notes](docs/releases/v0.3.0.md) for evidence and known
limits.

## 0.2.1 - 2026-07-29

### Fixed

- Hardened `reversible-system-change` so rollback claims require current
  restore evidence, complete coverage, and freshness.
- Made the Codex session-start hook independently reviewable and codified
  foreground-only, explicitly requested updates.

### Changed

- Preserved the exact four-skill release shape and added a concrete routed
  workflow example to the README.

## 0.2.0 - 2026-07-29

### Added

- Added `reversible-system-change` with rollback and layered postcondition
  requirements.

### Changed

- Strengthened `agents-architect` with explicit instruction ownership,
  `AGENTS.md` write boundaries, and current Codex discovery semantics.
- Split `traceable-git-submit` into phase-specific references covering
  provenance, multi-target verification, consolidation, and recovery.
- Aligned routing, plugin metadata, and documentation with the four direct
  public skills.

## 0.1.1 - 2026-07-20

### Changed

- Reorganized `agents-architect` internals into on-demand references.
- Added checkpoint-provenance safeguards to `traceable-git-submit`.
- Documented host-controlled marketplace refreshes and explicit update
  behavior.

## 0.1.0 - 2026-07-20

### Added

- Created the initial Codex plugin distribution with its manifest, local
  marketplace entry, session-start routing hook, and public README.
- Added the initial `using-axiom`, `agents-architect`, and
  `traceable-git-submit` packaged skills.
