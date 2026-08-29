# Repository Governance

This document is a dated, read-only observation of GitHub repository policy.
It does not configure GitHub, grant authority, or replace server-side rulesets.
A failed workflow is detection evidence, not server-side mutation prevention.

Last verified (UTC): `2026-08-29`

Verification used authenticated GitHub REST queries for the public
`wheakerd/axiom` repository after the separately authorized release-App
migration. The migration added and read back the App bypass while the owner-user
bypass remained active, removed and read back only the owner-user bypass, then
migrated only the integrity check context. At least one server-side creation
restriction remained active throughout. Follow-up verification was read-only
and changed no branch, tag, release, workflow, permission, or collaborator. The
[ruleset REST API](https://docs.github.com/en/rest/repos/rules),
[ruleset semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets),
and [CODEOWNERS behavior](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
are the external interpretation references.

## Main Branch Policy

The active repository ruleset `require-signed-commits-on-main`, ID `20677005`
and updated at `2026-08-26T04:46:04.609Z`, targets exactly
`refs/heads/main`. Its administrator-visible REST response reported
`bypass_actors: []` and `current_user_can_bypass: never`. It contains:

- `pull_request`, with `required_approving_review_count: 0`,
  `dismiss_stale_reviews_on_push: false`, `required_reviewers: []`,
  `require_code_owner_review: false`, `require_last_push_approval: false`,
  `required_review_thread_resolution: false`,
  `require_extra_approval_for_unattributed_changes: true`, and
  `allowed_merge_methods: [squash]`;
- `non_fast_forward`, which blocks force pushes; and
- `required_signatures`, which requires signed commits; and
- `required_status_checks`, with exact GitHub Actions checks
  `repository-guards` and `unit-and-integration-tests`, both bound to
  `integration_id: 15368`, `strict_required_status_checks_policy: true`, and
  `do_not_enforce_on_create: false`.

Required checks on `main`: `repository-guards` and
`unit-and-integration-tests`. Both must pass before merge, and strict mode
requires the pull-request branch to be current with `main` before their final
results are accepted. The two checks remain distinct server-side prerequisites.

The ruleset contains no `deletion` rule. `main` was the repository's default
branch at verification time, but no destructive deletion probe was attempted
and no repository-specific deletion rule was observed. Default-branch deletion
rule: **UNAVAILABLE / NOT-RUN**. This absence must not be rewritten as an
enforced deletion restriction.

## Release Tag Policy

The active repository ruleset `require-github-signed-release-tags` targets
exactly `refs/tags/v*`. The administrator-visible REST response for ruleset
`20724385`, updated at `2026-08-29T01:53:08.312Z`, reported
`bypass_actors: []` and `current_user_can_bypass: never`. It contains:

- `required_signatures`;
- `required_status_checks`, with the exact required GitHub Actions check
  `Verify signed main history`,
  `strict_required_status_checks_policy: false`, and
  `do_not_enforce_on_create: false`;
- `deletion`, which prevents ordinary actors from deleting matching tags; and
- `non_fast_forward`, which blocks the forced update needed to replace an
  existing Git tag.

It contains no `creation` rule. Its empty bypass list applies to every
integrity rule in this ruleset, including the required signature, required
check, deletion, and non-fast-forward controls.

The separate active ruleset `restrict-release-tag-creation` also targets
exactly `refs/tags/v*`. Ruleset `21703772`, updated at
`2026-08-29T01:52:49.941Z`, contains exactly one `creation` rule. Its only
administrator-visible bypass entry is `actor_id: 4756785`,
`actor_type: Integration`, and `bypass_mode: always`, which identifies the
dedicated `axiom-release-tag-controller` GitHub App. The owner-visible response
reported `current_user_can_bypass: never`. Because the App bypass is scoped to
this creation-only ruleset, it does not bypass any rule in
`require-github-signed-release-tags`.

Together, the observed deletion and non-fast-forward rules prevent ordinary
actors from deleting or updating an existing `v*` tag. This conclusion is
derived from the active rule types and GitHub's documented semantics; no tag
mutation was attempted. The empty bypass list means no bypass actor was
observed with the write-visible response used for this verification.

Only the exact bypass actor may create a matching upstream tag. Other
contributors can continue to fork the repository, create branches and tags in
their forks, and propose pull requests; repository write access alone does not
authorize formal release-tag creation.
Release-tag creator allowlist: **GitHub App `axiom-release-tag-controller` only**.

The required status check remains commit-level evidence and may be reusable for
the same commit independently of the event that produced it. Commit-level
required-check evidence is defense in depth, not exact tag-creation
authorization. The authenticated actor on the exact ref-create operation is
the server-side creation authorization boundary.

## Release Tag Controller Migration

The v0.8.20 migration registered GitHub App ID `4756785` with slug
`axiom-release-tag-controller`, installed it only on `wheakerd/axiom`, and
created the `release-tag-creation` Actions environment. The administrator
read-back above confirms that the App is the only `Integration` / `always`
bypass actor in `restrict-release-tag-creation`, the former owner-user bypass
is absent, and `require-github-signed-release-tags` has no bypass actor and
requires only `Verify signed main history`. A break-glass operation remains a
separately authorized, audited ruleset change; no permanent interactive-user
bypass is retained merely for convenience.

The `release-tag-creation` Actions environment owns
`AXIOM_RELEASE_APP_PRIVATE_KEY`, `AXIOM_RELEASE_APP_CLIENT_ID`, and the numeric
`AXIOM_RELEASE_APP_ID`. The workflow runs only when manually dispatched on
`refs/heads/main`. Its ordinary `GITHUB_TOKEN` has only `contents: read` and
`checks: read`. The minted App token is scoped to this repository and requests
only `administration: read` plus `contents: write`; administration write is not
granted. Pull-request code never receives the private key or App token.

Before one exact `POST /git/refs`, the controller binds the requested version
and tag, live protected-main commit and tree, both manifest versions, the two
main ruleset checks, `Verify signed main history`, REST and GraphQL GitHub-made
signature evidence, tag and Release absence, App installation identity and
repository scope, and all three live rulesets. It performs the same complete
read a second time, rejects any difference, creates only the exact absent tag,
and immediately reads the ref back. It has no update or delete operation. An
uncertain response is read back once and reported as a failure without retry;
a rerun rejects the existing ref with zero mutation.

GitHub returns `bypass_actors` only to a caller with ruleset write access. The
controller deliberately retains `administration: read`, so its App-token view
must omit the `bypass_actors` property. It binds ruleset IDs `20677005`, `20724385`,
and `21703772` plus their normalized server update instants to the reviewed
administrator-visible snapshot, then requires the App's effective bypass
states to be `never`, `never`, and `always` for main, tag integrity, and tag
creation respectively. Any actor or rule edit changes the server-owned update
instant and fails before tag mutation; no workflow receives ruleset-write
permission merely to reveal the actor arrays.

The checked-in `Release signature guard` assigns distinct stable check names:
`Verify signed main history`, `Verify release candidate`,
`Verify created release tag`, and `Observe published immutable release`.
`release/v<version>` runs can produce candidate evidence only. The controller
accepts only the exact current `main` SHA and the main-history context, so a
candidate result cannot authorize production tag creation.

The App, environment names, repository scope, ruleset actors, ruleset update
instants, and migrated check context were read back directly before tag
creation. At this dated snapshot `v0.8.20` remained absent after fail-closed
controller refusals; repository code and offline tests alone are not used as
evidence of those external facts.

## Production Release Version Policy

Axiom production releases use stable numeric `MAJOR.MINOR.PATCH` versions.
Each component is either `0` or a nonzero decimal digit followed by decimal
digits. Manifest versions contain no `v` prefix; formal upstream tags and
release-candidate branches use `v<version>` and `release/v<version>`
respectively. Prerelease identifiers, build metadata, leading-zero components,
missing or extra components, and prefixed manifest versions are rejected.

`axiom_validation/release_versions.py` owns the canonical parser, derived Bash
tag pattern, and shared regression corpus. Both manifests, the exact JavaScript
signed-target guard, the Bash publication gate, release evidence, GitHub Latest
comparison, and attestation subjects must remain equivalent to that policy.
The signed-target guard binds the version named by `release/v<version>` to both
manifests before formal tag creation; it later requires the same version from
the exact `v<version>` tag and GitHub Release.

Historical tags and Releases remain immutable records and are not rewritten.
Prerelease or build-metadata support requires a separately reviewed design for
GitHub prerelease state, Latest selection, precedence and duplicate-build
semantics, evidence asset names, release recovery, and compatibility claims.

## Pull-Request Validation And Release Provenance

`Distribution and publication guards` produces the `repository-guards` check.
It validates a proposed pull-request tree with read-only repository checks. It
does not establish release provenance, prevent a Git ref mutation, or authorize
publication.

`Unit and integration tests` produces the exact
`unit-and-integration-tests` check. It runs the complete standard-library
unittest discovery command in the fixed blocking environment and remains
separate from package and publication-policy validation. The active `main`
ruleset requires both checks and accepts them only from GitHub Actions.

`Cross-platform hook runtime integration` separately executes the exact
checked-in Codex and applicable Claude Code `SessionStart` command strings on
`ubuntu-24.04`, `windows-2025`, and `macos-15`. Its three read-only matrix
checks are `hook-runtime-ubuntu-24.04`, `hook-runtime-windows-2025`, and
`hook-runtime-macos-15`. They use no repository secret, do not persist checkout
credentials, and exercise only temporary roots through `cmd.exe` or
no-profile Bash, as applicable to the checked-in command.

These three matrix checks are intentionally not required by the active `main`
ruleset during their initial native-CI observation period. A platform failure
is review evidence, but does not yet block an external contributor's branch or
fork while runner stability is being established. Only `repository-guards`
and `unit-and-integration-tests` are server-side merge requirements in this
dated snapshot; a future ruleset change requires separate live verification.

The checked-in v0.8.20 `Release signature guard` maps each evidence boundary to
one stable name: `Verify signed main history`, `Verify release candidate`,
`Verify created release tag`, and `Observe published immutable release`. A
manual candidate run accepts only `release/v<version>` and requires the stable
numeric branch version to match both manifests. A manual published-release run
accepts only the exact tag and requires the live Release to be final,
non-prerelease, immutable, and commit-bound. These checked-in names do not
rewrite the dated live ruleset observation above; migration remains pending
until a separate authenticated read-back confirms it.

`Create protected release tag` is separate from the read-only signature guard
and from immutable publication. It is manual-only on current `main`, consumes
the dedicated App credential only after validating non-secret inputs, rereads
all drift-sensitive state twice, and owns the sole normal tag-creation attempt.
It has no pull-request, push, release, schedule, update, delete, publication, or
ruleset-write path.

`Publish immutable release` is a separate manually dispatched workflow. It
accepts only one stable numeric production release tag from the current `main`
commit, grants only `contents: write`, and has no pull-request, push, release,
schedule, secret, or arbitrary repository input. It globally serializes Latest
publication, verifies the live immutable setting, main/tag identity, and REST
plus GraphQL GitHub-made signature, and rejects a different equal-or-newer
current stable release version, then uniquely freezes one numeric Release ID.
It validates one
downloaded observation asset, uploads one deterministic attestation without
replacement, downloads both remote assets, publishes the same draft, and
requires the final Release to be immutable and GitHub Latest. It can resume a
draft after the exact attestation already exists and can perform final-only
readback without a second publication mutation.

The release-target guard remains a separate policy owner. GitHub does not
start another workflow for an ordinary event created by a workflow's
`GITHUB_TOKEN`, so the publication workflow fails closed on direct signature
readback and the release operator explicitly dispatches `Release signature
guard` with `phase=published-release` on the exact published tag afterward.

## Immutable Release Policy

On 2026-08-26 UTC, an authenticated repository-owner REST request enabled
immutable releases for `wheakerd/axiom`; the immediate read-back returned
`enabled: true` and `enforced_by_owner: false`. This repository-level setting
applies only to future Releases. Existing Releases, including v0.8.5, remain in
their previously reported mutable state and are not retroactively relabeled.

The checkout cannot prove that this remote setting remains enabled. The release
workflow reads it before any mutation, immediately before publication, and
after publication. Final acceptance also requires GitHub's Release response
itself to report `immutable: true`.

GitHub's documented immutable-release guarantees cover the associated tag and
uploaded assets. They do not document the Release title, body, Latest marker,
or Release object as immutable. Axiom's content-addressed attestation binds the
exact title and release-notes SHA-256, and later verification fails on metadata
drift. That is durable detection, not a claim that the platform blocks every
metadata edit or Release deletion.

## Critical-Path Ownership

The checked-in [CODEOWNERS file](../.github/CODEOWNERS) assigns the following
critical paths to the repository owner `@wheakerd`:

- `/.github/CODEOWNERS`
- `/.github/workflows/`
- `/.codex-plugin/`
- `/.agents/plugins/`
- `/.claude-plugin/`
- `/hooks/`
- `/skills/using-axiom/`
- `/scripts/`
- `/axiom_validation/`
- `/tests/`
- `/SECURITY.md`
- `/docs/repository-governance.md`

The validator and tests are covered because the stable scripts delegate policy
decisions to those paths. Ownership of only the wrapper script would leave a
sibling path able to change the accepted result.

CODEOWNERS declares responsibility and requests review. It does not require an
approval by itself. The current branch ruleset explicitly reports
`require_code_owner_review: false`, so critical-path code-owner approval is not
server-side enforced as of the verification date.

## Human Review Trust Boundary

`Path B: document the single-maintainer trust boundary` is the selected policy
for this snapshot. `wheakerd` is the current ultimate repository trust root,
and the absence of independent human review is a known limitation. The
authenticated collaborator query returned only `wheakerd`, and every
critical-path CODEOWNERS entry names that same account. CODEOWNERS is advisory
under the live rule: it assigns responsibility and requests review, but it does
not block an unapproved merge while `require_code_owner_review: false` and
`required_approving_review_count: 0`.

The current directly observed preventive controls are the server-side
pull-request requirement, required signatures, non-fast-forward protection,
strict required checks, squash-only main merges, and the release-tag creation
and integrity rules. Server-side enforcement of the two required check contexts
is preventive, while the repository-owned validator and test content behind
those results remains controlled by the same ultimate trust root.

The current directly observed detective controls are the repository validators
and tests, GitHub Actions and check output, signed-target and release
observations, content-addressed release attestations, manual read-only API
re-verification, and ruleset-history entries. They can expose drift or preserve
provenance, but they do not supply an independent human approval. Hardware-backed
authentication and an independently controlled release identity were not
verified by the repository or API evidence used for this snapshot and are not
claimed as current compensating controls.

Emergency or administrative ruleset changes remain separately auditable
through GitHub's ruleset version history. Every currently observed history
entry identifies `actor_id: 78034820` and `actor_type: User`, which maps to the
same `wheakerd` identity. That audit trail is detective evidence; because the
governing administrator remains the same identity, it does not constitute an
independent trust domain.

`Path A: enforce independent review` must not be enabled until a different
trusted GitHub principal has direct write access, is added alongside
`@wheakerd` as a code owner for every critical path listed above, and has
approved a protected test pull request that changes at least one such path.
That test must prove that the approval counts without author self-approval or a
ruleset bypass. Only after that proof and a live API read-back should the main
ruleset require an approving review, code-owner review, last-push approval,
stale-review dismissal, and review-thread resolution.

Path B changes no repository ruleset, CODEOWNERS entry, workflow, collaborator
permission, or required check. The external contribution flow and merge gates
therefore remain unchanged: `repository-guards` and
`unit-and-integration-tests` remain the only required checks, and the three
hook-runtime matrix checks remain non-required review evidence.

## Manual Re-verification

Use read-only calls and compare the returned values with this document. Do not
copy tokens or full administrative API responses into the repository.

1. List active repository rulesets. For this public repository, GitHub permits
   an unauthenticated request; a fine-grained token needs only repository
   metadata read permission.

   ```bash
   gh api -X GET 'repos/wheakerd/axiom/rulesets?includes_parents=true' \
     --jq '.[] | [.id, .name, .target, .enforcement] | @tsv'
   ```

2. For each returned ID, inspect the exact target, ref conditions, rules, and
   enforcement without writing the ruleset.

   ```bash
   gh api -X GET 'repos/wheakerd/axiom/rulesets/RULESET_ID?includes_parents=true' \
     --jq '{name,target,enforcement,conditions,rules,bypass_actors,current_user_can_bypass}'
   ```

3. Confirm the effective rules on `main`, the default branch, workflow names,
   and the exact check-run names on the current commit.

   ```bash
   gh api -X GET repos/wheakerd/axiom/rules/branches/main
   gh api -X GET repos/wheakerd/axiom --jq '.default_branch'
   gh api -X GET repos/wheakerd/axiom/actions/workflows \
     --jq '.workflows[] | [.name, .path, .state] | @tsv'
   gh api -X GET repos/wheakerd/axiom/commits/main/check-runs \
     --jq '.check_runs[] | [.name, .app.slug, .status, .conclusion] | @tsv'
   ```

4. With a repository administrator present, repeat the individual ruleset GET
   and verify that `require-github-signed-release-tags` has no bypass actors or
   `creation` rule, while `restrict-release-tag-creation` has exactly one
   `creation` rule and only App ID `4756785` as an `Integration` / `always`
   bypass. The same read-back must show no owner-user bypass, no integrity
   bypass, and only `Verify signed main history` as the integrity required
   context. GitHub omits bypass details from callers without ruleset write
   visibility. The controller therefore binds the administrator-verified IDs
   and update instants while requiring the read-only App's effective bypass
   states to remain `never`, `never`, and `always`; no workflow receives
   administration write.

5. With repository administration read access, list direct collaborators and
   inspect every active ruleset's history. Confirm that a second trusted
   write-capable principal has not appeared and preserve each history actor as
   detective evidence rather than independent review.

   ```bash
   gh api --paginate -X GET \
     'repos/wheakerd/axiom/collaborators?affiliation=direct&per_page=100' \
     --jq '.[] | [.login, .permissions.admin, .permissions.maintain, .permissions.push] | @tsv'
   gh api --paginate -X GET \
     'repos/wheakerd/axiom/rulesets/RULESET_ID/history?per_page=100' \
     --jq '.[] | [.version_id, .actor.id, .actor.type, .updated_at] | @tsv'
   ```

6. Review `.github/CODEOWNERS` on the protected base branch, run the repository
   static checks, record every unavailable field as unavailable, and update the
   verification date only in the same reviewed change as any corrected policy
   value.

## Availability And Limits

- The detailed ruleset APIs succeeded for the authenticated repository owner.
  Anonymous listing also succeeded because the repository is public. A
  lower-permission detailed check of bypass actors was **NOT-RUN**.
- GitHub's legacy `branches/main/protection` endpoint returned `404 Branch not
  protected`; active protection was observed through repository rulesets and
  the effective branch-rules endpoint instead.
- The authenticated direct-collaborator query reported only `wheakerd`. The
  owner-visible creation ruleset reported the same user as its only bypass
  actor. No destructive proof of branch or tag rejection was attempted.
- Repository-plan capability was not inferred from documentation. The three
  named rulesets were directly observed as active; unavailable fields remain
  unavailable if a future plan or API response hides them.
- No scheduled or manually dispatched governance-audit workflow was added.
  The manual method already exposes the relevant public settings, while an
  automated job could not prove hidden bypass actors without elevated
  permission. A workflow must never receive ruleset-write permission merely to
  perform an audit.
- The repository's static validator checks that this dated snapshot retains
  its required facts, migration target, and exact critical-path owner set. It
  cannot contact GitHub or prove that remote configuration has not drifted;
  manual re-verification remains required.
