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

The shared source includes `agent-plugin-architect` on both hosts without a
host-specific Skill copy. Static discovery, route parity, wrapper and hook
shape, and version-bound evidence are checked separately from authenticated
host loading, lifecycle routing, model behavior, and marketplace acceptance.

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
   packaged-plugin architecture, task-review, and external-action requests in
   [Examples](examples.md) when validating those routes.
5. For Claude Code compaction coverage, observe manual and automatic compaction
   separately. Record whether exactly one `SessionStart` event with source
   `compact` loaded the gate, then run the routed request and no-route control
   after compaction in separate reviewed sessions.
6. Record pass, fail, not run, and unavailable results separately.

The machine-readable [release status](../evidence/release-status.json) is the
canonical current-release summary. It binds prior observations to their exact
tag and commit, records current host results separately, and prevents an older
record from being interpreted as current evidence.

For v0.8.2, that status is `STATIC-ONLY`. The checked-in repair tree cannot
embed its future signed merge commit or final post-merge observation. The v0.8.2
release-bound batch remains terminal `FAIL` at Case 1 after unexpected tool
use. One independent corrected-preflight v0.8.2 Case 1 diagnostic passed at
repeat count one with zero tool events, but the different one-sample outcomes
are observed variance rather than a current v0.8.2 host-pass claim. Two later
complete-batch attempts against signed unreleased v0.8.3 candidate commit
`ca9ae1803a806042866b0c4d288791f0f32df8f1` remain separate external terminal
`UNKNOWN` records. A
prior-release Codex observation also exists for immutable v0.7.4: Codex
`0.149.0` loaded the startup front door in one fresh routed session and selected
no Axiom route in a separate fresh control session. Codex compaction remains
`NOT-RUN`; every authenticated Claude Code case remains `UNAVAILABLE`. See the
[version-bound records](../evidence/v0.7.4/) and do not carry their outcomes
forward to v0.8.2.

The standard-library validator checks the complete record matrix and the
release boundary:

```bash
python3 scripts/check-compatibility-evidence.py --self-test
```

A present executable or manifest alone remains too weak to support a host
claim.

## Marketplace Presentation

The Codex manifest declares Axiom's repository website, Issue tracker support
URL, `#111827` light-surface brand color, `#5EEAD4` dark-surface brand color,
one repository-owned SVG for both the logo and composer icon, and exactly three
single-line non-mutating starter prompts. The short description is 28
characters. The asset is square, font-free, and contains no scripts, event
handlers, external references, or embedded active content.

Axiom has Skills and no MCP custom UI, so `interface.screenshots` remains
absent. No marketplace screenshot was synthesized. Codex portal draft,
preview, and submission validation are `NOT-RUN`; the local Codex CLI exposes
no plugin-validation or marketplace-preview command. Claude Code metadata stays
within its supported schema rather than adding Codex-only listing fields, and
Claude Code `2.1.220` strict offline package validation passed in an isolated
configuration directory. Authenticated Claude Code remains
`UNAVAILABLE / NOT-RUN`.

The bundled local `plugin-creator` remains stale against the current documented
Codex presentation contract. It preserves the pre-existing non-pass for
Axiom's intentional `hooks` field and additionally rejects the supported
`brandColorDark` and `supportURL` fields. Those discrepancies are reported
without removing the fields from the release manifest.

## Packaged Agent-Plugin Architecture

Version 0.8.2 retains the route implemented in v0.8.0 from the
[agent-plugin-architect route contract](agent-plugin-architect-route-contract.md)
as one directly packaged Skill with seven root-reachable references. It owns
only explicit Codex or Claude Code plugin architecture across shared Skills,
routes, manifests, marketplace wrappers, hooks, and version-bound evidence.

Publishing an already-prepared artifact alone selects only
`confirm-external-action`; publication alone is not a persistent system
change. A distinct installation, deployment, migration, activation, or
retention change remains eligible for `reversible-system-change`, including
dual routing when it independently carries an external effect.

The current package has seven task routes and eight direct Skills. Repo-local
instruction systems, ordinary plugin code and documentation, Git submission,
installation, publication, deployment, and external actions remain outside the
new route. The shared Skill tree and marketplace wrappers remain single-source,
and both hooks remain byte-identical. Static support does not establish an
installed Codex or authenticated Claude Code host pass.

## Routing Context Budget

The [versioned routing-context record](../evals/context-budget/results/v0.8.2.json)
binds the immutable v0.7.9 `skills/using-axiom/SKILL.md` gate at commit
`4c24ba6c016945038778475ce6b69ac9e9a5ce3b`, tree
`719622eff9654dd1050863213d2bf81d3455d6f6`, and SHA-256
`1380155863715c28b91223823f3eaadb96bcefbe2482b444ef9dc8e8b62fe011`.
The v0.8.2 repair candidate gate is 6,293 bytes with SHA-256
`5e852f5cc1edc3a2fdb19538b2e8bec982d9e959012cb426ae91bb96ccfef866`.

The candidate has 805 whitespace-delimited words, 114 logical lines, and one
unique direct reference. Its 1,574 `ceil(bytes / 4)` value is an estimate only
for comparing the same English Markdown surface. The exact cumulative delta is
394 bytes, 48 words, seven lines, zero references, and 99 estimated tokens.
Both the 256-byte and 5% triggers are reached, so the record marks the change
reviewed and justifies it as the narrow publication-only negative boundary.
It separately preserves candidate-observed F5 usage: 279,939 input tokens,
156,288 cached input tokens, and 350,053 milliseconds. F5 also reported 2,436
output tokens, which schema v1 does not store. These values are candidate
metrics, not final v0.8.2 host or lifecycle evidence.

Seven lifecycle records cover fresh no-route and routed requests, resume with
no route, clear with routing, manual compaction with no route, automatic
compaction with routing, and repeated no-route requests in one unchanged
session. Their expected single injection comes from the checked-in hook
contract, not a host observation. Codex scenarios are `NOT-RUN`; authenticated
Claude Code scenarios are `UNAVAILABLE / NOT-RUN`. Case 17 in F5 was a
fresh-session routing observation, not actual post-compaction lifecycle
evidence. A future observed record can store each injection event, and the
validator derives a duplicate whenever the observed count exceeds the expected
count.

Growth of at least 256 UTF-8 bytes or 5% from the immutable cumulative baseline
requires review and justification, not automatic rejection. Any actual
reduction requires equivalent before/after `PASS` evidence for both routed and
no-route cases over the same fixed 64-case workload. Static validation and host
observation remain separate evidence classes. No model, reasoning, hook,
telemetry, runtime dependency, safety, authorization, or stop rule changed to
obtain the measured result.

## Routing Corpus And Host Benchmarks

The [routing evaluation corpus](../evals/README.md) is a second, narrower
evidence surface for route selection. Its 64 host-independent JSONL records are
reviewable expectations, not observed model behavior. The frozen 47-case v1
corpus and 13-case `codex-core-v1` benchmark remain bound to the historical
six-route contract. The successor v2 contract adds 17 cases for the seventh
route, a prose-free seven-route host-response schema, and the 17-case
`codex-core-v2` benchmark at repeat count one.

The v2 benchmark covers canonical, paraphrased, repo-local, generic-plugin,
cross-route, phase, ambiguity, multilingual, untrusted-data, and compaction
behavior. One immutable v0.8.0 Codex run attempted Case 1 and stopped terminal
`FAIL`; authenticated Claude Code remains unavailable. The corpus itself stays
static contract evidence and neither record establishes a v0.8.2 host pass.

Host result records live under `evals/results/` and identify a stable run ID,
the applied response-schema path and SHA-256, immutable Axiom source, exact host
and model, operating system, lifecycle, repeat count, route evidence,
clarification count, mutation attempts, and explicit status. Static schema and
coverage validation cannot turn `not-run` or `unavailable` into a pass.

The [Codex exec JSONL observer taxonomy](../evals/codex-exec-jsonl-observer-v2.json)
is the public, exact-version discriminator contract for Codex CLI `0.149.1`.
It binds eight top-level events and nine item types to exact official source.
The standard-library classifier resolves each item category before lifecycle
sequencing: a known benign item may occur between `thread.started` and
`turn.started`, while a tool/action or error item in that same position is
counted and terminates. Unknown, malformed, invalid-status, pre-thread benign,
duplicate-phase, post-terminal, and abrupt input fails closed. Its journal
retains only public discriminators, fixed categories and roles, enumerated
statuses, and ordinals; raw or private payload is excluded.

The append-only v2 Codex record
`codex-v0-8-0-linux-codex-core-v2-initial` binds Codex CLI `0.149.0`, model
`gpt-5.4`, Fedora Linux 44 x86_64, response schema V3, and immutable Axiom
v0.8.0 commit `5d02ebaa94f2a4355cb185a5091153c9e4ec497c` with tree
`974c0f5db0f2dab0aba512a6633b0a22b0d80779`. Case 1 returned a valid response
with `agent-plugin-architect`, zero clarification, and no observed mutation.
The observer derived `mutationAttempted=true` after two unexpected tool events,
while also recording clean completion, no failure event, and unchanged
workspace, source, and installed snapshots. The batch stopped `FAIL` after one
call and 17,984 milliseconds. Cases 2-17 are `NOT-RUN`, no retry occurred, and
the tool categories are not inferred. Exact scoped usage was 14,907 input,
1,920 cached input, and 116 output tokens. This is failed Stage 3 evidence, not
route acceptance; GitHub Issue #34 remains open. The paired Claude Code record
is entirely `UNAVAILABLE / NOT-RUN` because no authenticated subscription or
session was available.

The later F4 diagnostic used Codex CLI `0.149.1` with `gpt-5.4` against
immutable v0.8.1. It stopped terminal `FAIL` after eight calls when
`near-miss-confirm-plugin-publish-001` selected both
`confirm-external-action` and `reversible-system-change` instead of only the
external-action route. F4 is preserved separately and is not reclassified.

After the narrow publication-only wording fix, F5 ran 19 planned candidate
calls: three independent Case 1 variance samples followed by the 16 remaining
cases once each. All 19 passed with zero tool events and unchanged workspace,
source, and installed snapshots. Aggregate usage was 279,939 input tokens,
156,288 cached input tokens, 2,436 output tokens, and 350,053 milliseconds.
The subject is truthfully version `0.8.1`, tag null, commit
`298268ac0cfcaac84af22d7117e126f57e72152c`, tree
`ea298f5a81ca59eeecee863743b714f9f97f201d`, and release state
`candidate-unreleased`; the tested base-plus-diff identity maps exactly to that
commit and tree. The three variance samples mean F5 is not materialized as a
17-case schema-v2 observation, and it is not final v0.8.2 evidence.

The later release-bound batch against exact v0.8.2 stopped terminal `FAIL` at
Case 1 after unexpected tool use. It made no retry and left Cases 2-17
`NOT-RUN`; v0.8.2 remains unreleased. A separate corrected-preflight Case 1
diagnostic then passed one fresh call with the expected route, zero
clarification, false model mutation fields, zero tool events or unique calls,
and unchanged protected snapshots. Its `repeatCount` and call count were both
one. These independent outcomes demonstrate observed variance; the passing
diagnostic is not a schema-v2 result, not a retry, and not Stage 3 acceptance.

The checked-in v0.7.7 Codex run
`codex-v0-7-7-linux-codex-core-v1-initial` is `FAIL`: its first and only
attempted case exited nonzero without a bounded response, so route,
clarification, and mutation fields remain null. It binds the schema used for
that attempt at SHA-256
`9294a71523ba3ba8411810a4678b1170ac6400e5af9351da896018a0324f82ab`.
The stop-on-first-failure rule left cases 2-13 `not-run` without retry.
Authenticated Claude Code evaluation is `UNAVAILABLE / NOT-RUN` because no
subscription or authenticated session is available; its schema binding is
null, and an offline validator result is separate static evidence.

The independent recovery record uses the append-only identity
`codex-v0-7-7-linux-codex-core-v1-recovery-1` and binds the V1 schema at
SHA-256
`377ac22919164033b3dcf55f2b6b96086a5e2731c9b1edacabd5797a0b9127b6`.
It is also `FAIL`: Case 1 exited 0 and returned the expected
`agents-architect` route, zero clarification, false mutation fields, no tool
event, and unchanged protected snapshots. The observer nevertheless failed
closed because stderr contained an unexpected line. Cases 2-13 remain
`not-run`; the correct routing output does not turn the terminal run into a
pass or overwrite the initial failure. The initial and recovery-1 batches are
terminal.

A third append-only identity,
`codex-v0-7-7-linux-codex-core-v1-recovery-2`, records the same
immutable subject, fixed 13-case manifest, Codex model and lifecycle, and
V1 response-schema digest. It is terminal `FAIL`: Case 1 exited 0 with the
expected `agents-architect` route, zero clarification, false mutation fields,
no tool event, and unchanged protected snapshots. Stderr-v2 observed two
nonblank unexpected lines in `warning-prefix-unclassified` and
`other-unclassified`, with no count or category overflow. It retained no raw
stderr text or hashes, and the fatal unexpected classification prevented a
pass. Cases 2-13 remain `not-run`. All three Codex batches are terminal, no
case was retried, and no calls remain within those batches.

Recovery-3 is separately recorded as
`codex-v0-7-7-linux-codex-core-v1-recovery-3` against the same immutable
subject, manifest, model, lifecycle, and V1 response schema. It is terminal
`FAIL`: Cases 1-10 passed every process, lifecycle, tool, bounded-response,
routing, clarification, mutation, and protected-snapshot gate. Case 11 selected
`agents-architect` and `optimize-codex-usage` with zero clarification instead of
the frozen empty route set and one clarification, producing the first semantic
failure. Stderr remained diagnostic-only and non-causal. Cases 12-13 were not
run, and no retry or calls remain within the batch. All four v0.7.7 Codex
batches are terminal.

The v0.7.8 candidate now places an explicit ambiguity-precedence rule before
the usage-reduction route rule: mutually exclusive implementation choices with
materially different routes, write surfaces, or authorization and safety
boundaries must receive one clarification before route selection. Ten
post-repair cases passed, but the critical ambiguity behavior remains
unobserved because its bounded response was malformed. The repair does not
reclassify or replace recovery-3.

The independent post-fix batch
`codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-1` was authorized against
unreleased version `0.7.8`, immutable commit
`389495ae314cff2a5e3491df5ace4a8536de25d9`, and tree
`7afb38829e49a049d0376fc49fb07bde57633e67`. Its tag is explicitly null and its
release state is `candidate-unreleased`; no `v0.7.8` tag is claimed. It is
terminal `UNKNOWN` after 11 calls: Cases 1-10 passed, Case 11 produced malformed
bounded output, and Cases 12-13 remain `not-run`. No semantic fields are
inferred for Case 11, its exact malformed-response subtype is unavailable
because the private raw artifact was already destroyed, and no case was
retried. This batch left the critical repair unobserved; Candidate 4 below
observes it passing. Its unreleased subject is not a host pass bound to the
immutable v0.7.8 release commit.

Candidate diagnostics separate model structure from response acceptance. V1
historically included model-authored evidence and corresponding bounded/privacy
gates. V2 contains only the five semantic routing and mutation fields; route
uniqueness remains an independent acceptance gate, while public evidence is
generated deterministically from validated observer facts and labeled
`observer-derived`. Neither protocol retains raw response text, fragments,
response-content hashes, or exception text, and neither can convert an unknown
or failed semantic gate into a pass.

A second independent batch,
`codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-2`, was evaluated against
immutable commit `1087a10e76fd54e1508bee3938cb03a1e17a2f5e` and tree
`6f838581d1dcc99a5b870920c1c20889c1eb2607`, with `tag: null` and the explicit
unreleased-candidate label. It is terminal `UNKNOWN` after nine calls: Cases
1-8 passed, Case 9 was rejected as `schema-evidence` by the legacy combined
observer, and Cases 10-13 remain `not-run`. That category also covered stricter
evidence acceptance, so it does not prove a model-schema violation; the
destroyed response prevents a narrower subtype or semantic inference. No case
was retried. Candidate 1 remains immutable, and neither batch is a host pass.

A third independent batch,
`codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-3`, was evaluated against
immutable commit `449b3c01e0b4e3ef6fd6902efe3991c0b88758cd` and tree
`5e06400c77d9ca0b789710ab134e0d697adfe943`, with `tag: null`. It is terminal
`FAIL` after eight calls: Cases 1-7 passed, while Case 8 preserved the expected
empty route set, zero clarification, and false mutation fields but exceeded the
closed evidence-length acceptance gate. The rejected evidence is not retained;
Cases 9-13 remain `not-run`, no case was retried, and no host pass is claimed.

Candidate 4 uses the independent run ID
`codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-4` and terminal path
`evals/results/v0.7.8/codex/linux-candidate-4.json`. Against immutable
unreleased commit `70e1242ba9f038fe663f924f167108d8940106a8` and tree
`780b7401f7f12af9c9ab310a24c02c9aae84fe62`, all 13 ordered cases passed one
fresh call each without retry. Candidate 3 remains frozen. Its subject differs
from the immutable v0.7.8 release commit, no v0.8.0 host pass is inferred, and
authenticated Claude Code remains `UNAVAILABLE / NOT-RUN`.

The first failure or unknown result stops the remaining fixed batch without a
retry. That case preserves every known and null field; later cases remain
`not-run`, and summary metrics remain null when the partial batch cannot support
complete arithmetic.

The corpus includes post-compaction contracts, but the fixed Codex acceptance
batch uses fresh-start sessions. Neither corpus presence nor a fresh-start run
proves compaction lifecycle behavior.

## Historical Validation

Historical results describe the tree and tooling at the time they were
recorded; they are not a current pass.

The unreleased Git candidate for `v0.8.3` reports:

- synchronized `0.8.3` manifests with no Skill, route, hook, wrapper, corpus,
  benchmark, schema, or authority change;
- the unreleased v0.8.2 release-bound Case 1 `FAIL` preserved separately from
  one independent corrected-preflight Case 1 `PASS` at repeat count one;
- the unchanged 6,293-byte gate and reviewed +394-byte cumulative delta, with
  the diagnostic's 12,278 input tokens, 1,920 cached input tokens, 69 output
  tokens, and 13,139 milliseconds kept separate from release evidence;
- `STATIC-ONLY` current status, actual post-compaction lifecycle `NOT-RUN`, and
  authenticated Claude Code `UNAVAILABLE / NOT-RUN`; and
- two complete-batch attempts against signed commit
  `ca9ae1803a806042866b0c4d288791f0f32df8f1` that stopped at Case 1 as
  separate external terminal `UNKNOWN` records; no tag or Release exists.

See the [v0.8.3 release notes](releases/v0.8.3.md) for the diagnostic boundary
and the unmet release gate.

The Git record for `v0.8.2` reports:

- synchronized `0.8.2` manifests and one 143-byte route-gate clarification:
  publication alone is external action, not a persistent system change;
- the immutable F4 candidate `FAIL` after eight calls and the separate F5
  candidate-only `PASS` across 19 planned calls, without rewriting either;
- a reviewed 6,293-byte routing gate, +394-byte cumulative delta, and F5
  candidate usage kept separate from final release or lifecycle evidence;
- `STATIC-ONLY` checked-in status, actual post-compaction lifecycle
  `NOT-RUN`, and authenticated Claude Code `UNAVAILABLE / NOT-RUN`; and
- an external validation mode for one final, exact 17-call schema-v2 record
  bound to the signed merge commit, tree, and immutable `v0.8.2` tag. The
  content-addressed release asset supplements but never promotes or rewrites
  checked-in status; and
- the exact-version JSONL observer taxonomy, classify-before-sequencing rule,
  and fail-closed tool/error/unknown handling without raw payload retention.

See the [v0.8.2 release notes](releases/v0.8.2.md) for the candidate evidence,
context review, and gated post-merge sequence.

The Git record for `v0.8.1` reports:

- synchronized `0.8.1` manifests with no package, Skill, hook, route, corpus,
  benchmark, or authority change;
- append-only v0.8.0 Codex terminal `FAIL` and Claude Code `UNAVAILABLE`
  records, with all nine v1 observations and every historical contract
  byte-identical;
- unchanged 6,150-byte routing-gate metrics and +251-byte cumulative delta,
  plus exact scoped usage from the failed v0.8.0 Codex attempt;
- 64 routing cases, 30 fixed benchmark memberships, and 11 labeled result
  records passing static validation without converting the failed batch into a
  Stage 3 pass; and
- `STATIC-ONLY` v0.8.1 evidence, `NOT-RUN` Codex lifecycle, unavailable
  authenticated Claude Code, and GitHub Issue #34 left open for separate
  diagnosis and repair.

See the [v0.8.1 release notes](releases/v0.8.1.md) for the evidence boundary,
measurement, and validation status.

The Git record for `v0.8.0` reports:

- one shared `agent-plugin-architect` Skill with seven direct references and
  explicit exclusions for repo-local instructions, generic plugin work, Git,
  installation, publication, deployment, and external actions;
- synchronized `0.8.0` manifests, eight direct public Skills, seven task
  routes, and byte-identical marketplace wrappers and startup hooks;
- an additive seven-route schema, prose-free response schema, 17-case current
  benchmark, and 64-case combined corpus, while all v1 schemas, benchmarks,
  corpus files, nine observations, and earlier context records remain
  byte-identical;
- an exact 6,150-byte gate with a +251-byte cumulative delta that remains below
  both context-growth review triggers; and
- `STATIC-ONLY` current evidence: Codex host, lifecycle, model, marketplace,
  and portal checks are `NOT-RUN`, while authenticated Claude Code is
  `UNAVAILABLE / NOT-RUN`.

See the [v0.8.0 release notes](releases/v0.8.0.md) for the candidate package,
measurement, and validation boundary.

The Git record for `v0.7.12` reports:

- the Stage 1 `agent-plugin-architect` contract is accepted for Stage 2 and is
  not an installed or host-observed route;
- both manifests advance only their synchronized version while the current
  six-route gate, seven direct public Skills, wrappers, hooks, workflows,
  historical evaluation contracts, and runtime surface remain unchanged;
- the immutable v0.7.9 routing gate remains the cumulative baseline, and the
  v0.7.12 candidate retains its exact 5,899-byte content and SHA-256;
- all 60 standard-library tests and the aggregate publication policy passed in
  disposable copies, along with distribution, compatibility, context-budget,
  duplicate-aware JSON, Markdown-link, English-only, package-shape, mode,
  whitespace, documentation, and forbidden-surface checks;
- Claude Code `2.1.220` strict offline package validation passed separately,
  while the stale bundled `plugin-creator` preserved its known three-field
  non-pass; and
- v0.7.12 remains `STATIC-ONLY`: no current Codex host or model call was run,
  and authenticated Claude Code remains unavailable without a subscription or
  session.

The Git record for `v0.7.11` reports:

- Codex marketplace metadata uses the repository-owned Axiom mark, supported
  HTTPS links and brand colors, and exactly three bounded non-mutating prompts;
- standard-library validation fails closed on unowned fields, unsafe asset
  paths or SVG content, unsupported or oversized files, invalid dimensions,
  low-contrast colors, invalid URLs, and prompt contract violations;
- all 60 standard-library tests, 21 manifest schema fixtures, and the aggregate
  publication policy passed in disposable release copies, while Claude Code
  `2.1.220` strict offline package validation passed separately;
- the immutable v0.7.9 routing gate remains the cumulative baseline, and the
  v0.7.11 candidate retains its exact 5,899-byte content and SHA-256;
- no hook, route, workflow, model, reasoning, telemetry, or installed runtime
  dependency changed; and
- v0.7.11 remains `STATIC-ONLY`: Codex portal preview and submission were not
  run, no current Codex host pass is inferred, and authenticated Claude Code
  was unavailable without a subscription or session.

The Git record for `v0.7.10` reports:

- the immutable v0.7.9 routing gate is the cumulative proxy baseline, and the
  v0.7.10 candidate retains its exact 5,899-byte content and SHA-256;
- all seven required lifecycle scenarios distinguish checked-in hook
  expectations from `NOT-RUN` or `UNAVAILABLE / NOT-RUN` host observations;
- meaningful growth triggers review and justification, while any claimed
  reduction requires equivalent before/after routed and no-route passing
  evidence over the same fixed workload;
- 54 standard-library tests and the aggregate's 52 required files, 47 routing
  cases, 13 fixed benchmark cases, nine preserved host result records, and
  seven context scenarios passed in a disposable release copy;
- Claude Code `2.1.220` strict offline package validation passed, Codex CLI
  `0.149.0` exposed no plugin-validation command, and the bundled local
  validator preserved its known conflict with the intentional Codex `hooks`
  field; and
- v0.7.10 remains `STATIC-ONLY`: no Codex host session or model call was run,
  and authenticated Claude Code was unavailable without a subscription or
  session.

The Git record for `v0.7.9` reports:

- a dated, read-only GitHub governance snapshot distinguishes active
  server-side rulesets from repository workflows and documentation;
- exact required checks, pull-request parameters, force-push and deletion
  policies, bypass visibility, unavailable fields, and manual re-verification
  steps remain reviewable in the repository;
- critical workflows, manifests, hooks, routing, validation, scripts, tests,
  security, CODEOWNERS, and governance paths declare `@wheakerd` as owner; and
- v0.7.9 remains `STATIC-ONLY`: no Codex host run was performed, and
  authenticated Claude Code is `UNAVAILABLE / NOT-RUN` without a subscription
  or session.

The Git record for `v0.7.8` reports:

- 47 versioned black-box routing contracts cover every public route plus near
  misses, overlap, ambiguity, multilingual requests, no-route controls,
  untrusted input, and post-compaction expectations;
- a fixed 13-case, repeat-one Codex manifest and strict response schema keep
  route, clarification, mutation-attempt, and failure evidence reviewable;
- static corpus validation and observed host results remain separate, with
  failed, unavailable, and not-run outcomes preserved; and
- v0.7.8 remains `STATIC-ONLY`: Candidate 4 proves the immutable unreleased
  candidate, not the future release tag; authenticated Claude Code remains
  unavailable without a subscription or session.

The Git record for `v0.7.7` reports:

- the stable publication command delegates to independently testable manifest,
  hook, Markdown, YAML, routing, Git, Action-graph, release, and repository
  policy modules;
- production policy code and deterministic fixtures are separated, while the
  aggregate output and exit-code contract remain stable;
- release identity is derived from the synchronized manifests and release-note
  history is discovered from `docs/releases/`; and
- at v0.7.7 publication, no fresh Codex host lifecycle was run; the later
  v0.7.8 evaluation records preserve three independent v0.7.7-bound Case 1
  failures and each run's 12 stopped cases without turning any into a pass;
- every Claude Code case remains `UNAVAILABLE` without an authenticated
  subscription, and immutable v0.7.4 observations remain prior-release
  evidence only.

The Git record for `v0.7.6` reports:

- the pull-request event graph schedules read-only distribution and publication
  validation for same-repository and fork contributions without testing the
  contributor signature or repository origin;
- release provenance remains limited to protected `main`, strict immutable
  `v*` tags, bounded manual release candidates, and GitHub Release targets, with
  negative fixtures for signatures, ancestry, mutation, version drift, and
  mismatched Release refs;
- a real fork pull-request run is `NOT-RUN`, so GitHub scheduling,
  first-time-contributor approval, and live fork runner behavior are not claimed
  by deterministic fixtures; and
- v0.7.6 remains `STATIC-ONLY`: the current Codex cases were not rerun, all
  Claude Code cases remain `UNAVAILABLE` without an authenticated subscription,
  and immutable v0.7.4 observations are retained only as prior-release evidence.

The Git record for `v0.7.5` reports:

- the versioned evidence schema, two immutable v0.7.4 host records, current
  release status, standard-library validator, and negative fixtures passed
  publication integration;
- a privacy-isolated Codex `0.149.0` local-marketplace installation of Axiom
  v0.7.4 matched the checked-in SessionStart command digest, while separate
  fresh sessions observed `agents-architect` for the routed request and no
  route for the arithmetic control;
- Codex manual and automatic compaction route and control cases remain
  `NOT-RUN`, while all Claude Code startup and compaction cases remain
  `UNAVAILABLE` because no authenticated Claude Code session or subscription
  was available; and
- v0.7.5 remains `STATIC-ONLY`: its commit cannot self-embed its final object
  ID, and v0.7.4 evidence is not a current-release pass.

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

See the durable [v0.8.3 release notes](releases/v0.8.3.md),
[v0.8.2 release notes](releases/v0.8.2.md),
[v0.8.1 release notes](releases/v0.8.1.md),
[v0.8.0 release notes](releases/v0.8.0.md),
[v0.7.12 release notes](releases/v0.7.12.md),
[v0.7.11 release notes](releases/v0.7.11.md),
[v0.7.10 release notes](releases/v0.7.10.md),
[v0.7.9 release notes](releases/v0.7.9.md),
[v0.7.8 release notes](releases/v0.7.8.md),
[v0.7.7 release notes](releases/v0.7.7.md),
[v0.7.6 release notes](releases/v0.7.6.md),
[v0.7.5 release notes](releases/v0.7.5.md),
[v0.7.4 release notes](releases/v0.7.4.md),
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
