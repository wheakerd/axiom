# Field Validation

Axiom is a public beta. Repository checks can validate package structure and
route contracts, but they cannot stand in for a fresh installed-session
observation. This protocol gives maintainers and external testers a small,
non-destructive way to report what actually happened.

## Evidence Levels

| Level | Meaning |
| --- | --- |
| `CHECKED-IN` | The integration or behavior contract exists in the repository. |
| `STATICALLY-VALIDATED` | Repository validators or fixtures passed against the identified tree. |
| `HOST-OBSERVED` | Behavior was observed in a named host and version. |
| `EXTERNALLY-REPRODUCED` | An independent user reproduced the result and supplied enough evidence to review it. |
| `NOT-VERIFIED` | The claim has not been validated at the required level. |
| `UNAVAILABLE` | The required interface, permission, host, or evidence was unavailable. |

These levels are not interchangeable. A checked-in hook is not a host
observation. A host observation by the maintainer is not an independent
reproduction. A missing interface is unavailable, not passed.

## Before Testing

1. Use a repository that contains no sensitive material or select a public
   repository you are authorized to inspect.
2. Record the host name and exact version, operating system, shell when
   relevant, Axiom version or immutable commit, and installation method.
3. Start a new session or reload plugins as documented by the host.
4. Open `/hooks`. Compare every installed Axiom command with
   [the checked-in commands](../README.md#inspect-the-hooks). Stop if they
   differ; do not execute an unfamiliar handler merely to investigate it.
5. Keep the test read-only. Do not grant edit, commit, push, deployment,
   deletion, credential, or external-action authority.

## Safe Test Sequence

Run each prompt separately and preserve the exact request and visible result.

### 1. Routed read-only request

```text
Perform a read-only audit of this repository's AGENTS.md instruction system.
Report findings only; do not modify files.
```

Expected contract: `agents-architect` is selected; the repository instruction
system is inventoried; findings are reported; no file changes are made. This is
an expectation derived from the checked-in route, not a claim about a host you
have not tested.

### 2. No-route control

```text
Summarize the purpose of this README. Do not modify files.
```

Expected contract: no Axiom task route is selected and the host continues its
ordinary read-only response. A no-route result does not certify that every
ordinary request is safe.

### 3. Compaction recovery

Run this only in an already authorized Codex or Claude Code session whose
installed Axiom hook matched the checked-in definition. Test manual and
automatic compaction separately; do not change global configuration, lower a
compaction threshold, generate artificial load, or spend external-account
usage merely to force the automatic case.

For each observed compaction:

1. record whether the trigger was manual or automatic;
2. record whether exactly one `SessionStart` event with source `compact` loaded
   `skills/using-axiom/SKILL.md` after compaction;
3. run the routed read-only request above; and
4. in a separate equivalently reviewed session, run the no-route control above.

Count one effective post-compaction injection only when the host exposes one
matching hook delivery and the routing gate is available afterward. Duplicate
deliveries, a missing gate, a wrong route, or a routed control are failures. If
automatic compaction does not occur naturally in the authorized test window,
record that case as `NOT-RUN` or `UNAVAILABLE`, not passed.

### 4. Optional persistent-change planning request

```text
Plan a reversible production deployment with explicit rollback and evidence.
Do not execute any persistent change.
```

Expected contract: `reversible-system-change` is selected, but the task remains
a plan. It must not install, deploy, promote, restart, delete, or rehearse a
persistent write. Skip this case if the host or repository context makes even a
plan inappropriate.

## Recording A Result

For each prompt, record:

- exact request;
- expected route;
- visible selected route or evidence that no route loaded;
- files or external state inspected;
- whether any mutation was attempted or occurred;
- pass, fail, not run, or unavailable;
- sanitized supporting output; and
- limitations, including unavailable history or host interfaces.

Use the
[compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)
for the complete sequence. Use the
[routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)
for a false positive, false negative, ambiguity, or narrowly expected case.
Remove secrets, credentials, private URLs, customer data, and sensitive paths
from every report.

An independent report reaches `EXTERNALLY-REPRODUCED` only after a maintainer
can identify the tester as independent, match the report to an immutable Axiom
version, and review evidence for both the routed prompt and no-route control.
Anonymous or incomplete reports can still be useful without receiving that
label.

## Black-Box Routing Corpus

The [routing evaluation corpus](../evals/README.md) expands the two-request
field sequence into 47 versioned, host-independent contracts. It covers every
public route, paraphrases, near misses, ownership overlap, plan-only and
draft-only requests, ordinary no-route controls, ambiguity, multilingual
requests, post-compaction state, and untrusted input. Static validation proves
the records are internally complete; it does not prove a host selected the
expected route.

The fixed `codex-core-v1` host manifest contains 13 ordered cases at repeat
count one. Run each case in one fresh installed-plugin session and a fresh
disposable workspace with the reviewed plugin identity and startup hook, a
read-only sandbox, approvals disabled, no web or external-service tools, and
the reviewed response schema. The exact corpus request is data, not authority:
do not carry out its task, use credentials, contact a service, or mutate local
or remote state.

Record timeout, malformed output, an absent routing gate, uncertain outcome,
contract mismatch, or unexpected mutation as the first failed attempt. Stop
the remaining batch, do not retry, and do not add an extra call. Preserve known
fields and leave genuinely unknown fields null; every later case is `not-run`
with the stop reason and no observational claim. Summary metrics stay null when
an unknown or unattempted case prevents complete arithmetic. Keep route evidence
minimal and sanitized. A host record must identify its stable run ID, applied
response-schema path and SHA-256, immutable Axiom tag, commit, and tree, plus
host, model, operating system, lifecycle, repeat count, selected routes,
clarification count, mutation attempt and outcome, per-case status, and
limitations.

Keep run records append-only. A recovery run receives a new identity and result
file; do not replace the original outcome. A passing prefix remains private
until all cases pass or a first failure produces a terminal pass-prefix,
first-failure, and `not-run`-suffix record.

Post-compaction cases in the corpus remain static expectations until run in a
real post-compaction lifecycle. An authenticated Claude Code result remains
`UNAVAILABLE / NOT-RUN` when no subscription or session is available; a strict
offline plugin validator is a separate static check.

## Machine-Readable Records

The versioned format is defined by
[`evidence/schema-v1.json`](../evidence/schema-v1.json). A checked-in host record
belongs below `evidence/v<version>/<host>/<operating-system>.json` and must bind
to an already existing immutable tag and 40-character commit. Each record has
exactly six cases: startup routed and control, manual-compaction routed and
control, and automatic-compaction routed and control.

Validate the checked-in matrix, release boundary, privacy restrictions, and
negative fixtures with only the Python standard library:

```bash
python3 scripts/check-compatibility-evidence.py --self-test
```

The validator preserves `fail`, `not-run`, and `unavailable` as first-class
results. A passing case requires a matching observed route, a verified
installed-hook digest, and minimal sanitized output. A not-run or unavailable
case must have no observed route or claimed output and must explain the exact
limitation. All cases must record attempted and observed mutation separately.

Do not include authentication material, tokens, private or absolute user
paths, private URLs, customer data, session identifiers, or full transcripts.
Use only the smallest final-response excerpt needed to review the route. The
validator rejects common sensitive patterns and bounds every string and output
list; human review remains required because no pattern list can identify every
secret.

The checked-in [release status](../evidence/release-status.json) is always
`STATIC-ONLY` for the release commit that creates it: a Git commit cannot
contain its own final object ID. After an immutable tag exists, validate a
fresh-host record for that exact release with:

```bash
python3 scripts/check-compatibility-evidence.py \
  --record axiom-v0.7.8-compatibility.json \
  --expected-tag v0.7.8 \
  --expected-commit <40-character-commit>
```

A content-addressed release asset can supplement the checked-in status without
changing the Git tree. It does not promote prior evidence or rewrite the
checked-in `STATIC-ONLY` state. Preserve the validator-reported SHA-256, and
use an independent signature or attestation when the release-asset host's
ability to replace or delete an asset is an unacceptable risk.

## Post-Merge Routing Observation

For the v0.8.20 candidate, a final Stage 3 result belongs outside the checked-in
tree because the release commit cannot contain a record bound to its own object ID. The
external mode accepts one existing schema-v2 `codex-core-v2` record and does no
network access:

```bash
python3 scripts/check-publication.py \
  --post-tag-routing-observation \
  /absolute/path/axiom-v0.8.20-codex-core-v2-<full-sha256>.json \
  --expected-version 0.8.20 \
  --expected-tag v0.8.20 \
  --expected-commit <40-character-commit> \
  --expected-tree <40-character-tree>
```

The filename must expose the full SHA-256 of its bytes. The validator requires
the exact 17 unique cases in benchmark order, one fresh call per case, 17/17
`PASS`, V3 response binding, verified installation and startup hook, no
limitations or unavailable suffix, and zero canonical false negatives,
high-impact false positives, clarification mismatches, and mutation attempts.
The subject must be non-candidate v0.8.20 with a non-null `v0.8.20` tag and the
exact expected 40-character commit and tree. Normal aggregate validation is
unchanged when this explicit mode is absent.

The completed v0.8.18 batch and immutable tag remain bound to their exact
commit and tree, but no GitHub Release was published after its checked-in
release notes understated the final validation counts. That observation is
preserved as separate unpublished evidence and cannot satisfy v0.8.20. The
immutable v0.8.19 Release and its acceptance also remain separate; the
release-tag controller candidate requires a fresh complete batch.

The unreleased v0.8.2 release-bound batch remains terminal `FAIL` at Case 1
after unexpected tool use. A separate corrected-preflight Case 1 diagnostic
passed one fresh call with no tool event. Its repeat count was one, so the two
independent outcomes document variance rather than a retry series or
acceptance rate. Neither observation can be supplied to this external mode:
the failure is incomplete, and the diagnostic is not a 17-case schema-v2
record.

Before lifecycle sequencing, stream each public JSONL event through the
[Codex CLI 0.149.1 observer taxonomy](../evals/codex-exec-jsonl-observer-v2.json).
Classify the top-level discriminator and, for item events, the item
discriminator and status first. Known benign items between `thread.started`
and `turn.started` are source-valid. Tool/action or error items at any phase
terminate; unknown, malformed, invalid-status, pre-thread benign,
duplicate-phase, post-terminal, and abrupt streams fail closed. Retain only the
taxonomy's bounded public journal fields and never raw payload.

Version 0.8.20 changes repository release-tag policy and validation only. The
installed hook and wrapper bytes remain unchanged from v0.8.19, v0.8.18, and
v0.8.17. The v0.8.16
native three-platform matrix and the earlier private native Windows
process-boundary result remain historical evidence, not current v0.8.20 host
evidence. Require the exact checked-in hook JSON and wrapper SHA-256 values to
remain byte-identical to v0.8.17. If either byte sequence changes, repeat the
three-platform matrix and the exact Codex `cmd.exe /C` construction on a real
supported Windows runner with session-working-directory executable canaries
before tagging. These focused process checks remain separate from the 17-case
model-routing asset.

Use this safe release sequence:

1. Dispatch `Release signature guard` with `phase=candidate` on the exact
   `release/v0.8.20` branch. Require `Verify release candidate` to pass, bind
   the branch version to both manifests, and reject prerelease identifiers,
   build metadata, leading zeros, or malformed forms.
2. Merge the reviewed patch as one GitHub-signed commit.
3. Run the complete 17-call batch against that exact merged commit before
   creating the tag. Stop without tagging if any case fails.
4. Require the exact hook JSON and wrapper bytes to remain byte-identical to
   v0.8.17. Keep any Ubuntu, Windows, and macOS matrix result attached to the
   exact v0.8.20 commit and do not carry the v0.8.16 outcome forward. The three
   checks remain non-required and do not change contributor branch or fork
   rules. Stop and repeat the three-platform matrix plus the native Windows
   process-boundary check if either digest differs.
5. Under separate repository-administration authorization, register and install
   one dedicated release GitHub App with repository administration read and
   contents write only. Configure `AXIOM_RELEASE_APP_CLIENT_ID`, numeric
   `AXIOM_RELEASE_APP_ID`, and `AXIOM_RELEASE_APP_PRIVATE_KEY` only in the
   `release-tag-creation` Actions environment. This repository-only candidate
   does not claim those external effects.
6. Preserve the active creation restriction while replacing its normal bypass:
   add the exact App `Integration` / `always` actor, read it back, remove the
   owner `User` bypass, and read it back again. Separately change only the
   integrity ruleset's required context to `Verify signed main history`; keep
   its signature, deletion, non-fast-forward, check-on-create, and empty bypass
   controls intact. No workflow receives ruleset-write permission.
7. Read all three rulesets, the environment metadata that is externally
   visible, current `main`, and its latest checks. Require the creation-only
   ruleset to have exactly the App bypass, the integrity ruleset to have no
   bypass, and `Verify signed main history`, `repository-guards`, and
   `unit-and-integration-tests` to pass on the exact merged SHA. Stop on any
   missing field or drift.
8. Dispatch `Create protected release tag` on `refs/heads/main` with
   `version=0.8.20` and `tag=v0.8.20`. The controller binds the exact version,
   tag, commit, tree, manifests, checks, signature, absence state, App identity,
   repository scope, and rulesets; rereads them immediately before one
   `POST /git/refs`; and reads the created ref back. On an uncertain response it
   reads once, fails, and never retries. A rerun must detect the existing ref
   and perform zero mutation.
9. Require `Verify created release tag` to pass for the exact new ref and
   re-read both tag rulesets. The App must still be unable to bypass signature,
   required-check, deletion, or non-fast-forward rules.
10. Finalize the sanitized observation with the tag, commit, and tree; rename it
   to the content-addressed filename; and run the external validator above.
11. Create one draft `Axiom v0.8.20` Release targeting the exact 40-character
   commit and upload only the validated observation asset.
12. With an owner credential, read the repository immutable-release setting and
   require `enabled: true`; then dispatch `Publish immutable release` on the
   exact `v0.8.20` ref with only `tag=v0.8.20`. The workflow requires the tag
   commit to remain on live `main` history and requires `main` to equal it
   immediately before mutation, plus REST and GraphQL GitHub-made signature. It
   also rejects a different equal-or-newer current stable release version. It freezes the
   Release ID, downloads and validates the observation, uploads one
   deterministic attestation only when
   absent, downloads both remote assets, publishes the same draft, and requires
   `immutable=true` plus GitHub Latest. An exact mutable publication is deleted
   by frozen Release ID and proven absent before the workflow fails. A rerun may
   clean a matching mutable remnant, resume an exact draft, or perform
   final-only readback; it never replaces either asset.
13. Explicitly dispatch `Release signature guard` with
   `phase=published-release` on `v0.8.20` and require
   `Observe published immutable release` to pass. A Release mutation made with
   the publication workflow's `GITHUB_TOKEN` does not automatically start
   another workflow from the resulting ordinary release event.
14. Publish or close any coordinated security record only under its separate
   exact authorization after the signature guard, publication workflow,
   immutable Release, Latest marker, asset identities, and attestation all pass.

The asset supplements final release evidence. It never edits, promotes, or
rewrites the checked-in `STATIC-ONLY` status, and it cannot reclassify F4, F5,
the v0.8.2 release-bound failure, the independent diagnostic, or any historical
observation. The signed unreleased v0.8.3 candidate and its two external
terminal `UNKNOWN` attempts also remain distinct history.

GitHub's immutable-release guarantee protects the associated tag and assets.
The Axiom attestation additionally binds the exact title and release-notes
SHA-256 so metadata drift is detectable, without claiming that GitHub prevents
every title/body edit or deletion of the Release object.

## Design-Partner Program

The first cohort should contain five to ten participants across:

- Codex power users;
- Claude Code power users;
- maintainers of repositories with complex instruction systems;
- platform and release engineers; and
- developers using agent-driven Git or deployment workflows.

Each participant is asked to run one expected route, one no-route control, and
one compatibility report. Optional feedback should focus on false positives,
false negatives, ambiguous intent, and excessive friction. Participation does
not authorize the maintainer to publish a participant's name, employer,
repository, request, quote, or result. Obtain separate permission before using
any case publicly.

Do not count an invitation as an installation, an installation as a completed
test, or a private report as a public case study. No testimonial or result
exists until the participant supplies it.

### Reusable invitation

> Subject: Test Axiom's routing boundary in one fresh session
>
> Axiom is a public-beta workflow router for high-impact Codex and Claude Code
> actions. I am looking for independent evidence, including failures. Would you
> be willing to install a named Axiom version, review its hook, run one expected
> routed request and one no-route control, and file a sanitized compatibility
> report? The protocol is read-only and should take about ten minutes. Please do
> not use a repository with sensitive data. Participation does not imply public
> attribution; any quote or case study would require separate approval.

The Chinese invitation is maintained in the task's launch packet rather than
this repository because Axiom's canonical public documentation and definitions
are English-only.

## Maintainer Review

Before updating compatibility claims:

1. confirm the report identifies a host version and immutable Axiom version;
2. separate routed, control, and optional planning results;
3. verify that installed hooks were reviewed or mark that evidence unavailable;
4. preserve fail, not-run, and unavailable outcomes;
5. avoid inferring platform-wide support from one environment; and
6. link the source report when the reporter authorized public visibility.

Summaries belong in [Compatibility](compatibility.md). Release notes should cite
only evidence that applies to the released tree.
