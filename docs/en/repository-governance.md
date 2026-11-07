# Repository Governance

This reference is for maintainers and auditors reviewing repository controls. It describes the controls in force and where each one is enforced. It does not configure GitHub, grant authority, or replace server-side rulesets, and editing it does not re-verify the live repository: [Manual Re-verification](#manual-re-verification) gives the read-only calls for a new decision. For plugin execution and permissions, use the [Trust Model](trust-model.md).

## Find The Relevant Boundary

| Review task | Section |
| --- | --- |
| Classify a repository change | [Runtime Identity](runtime-identity.md#classify-a-change) |
| Inspect merge, tag, and release-branch restrictions | [Main Branch Policy](#main-branch-policy), [Release Tag Policy](#release-tag-policy), and [Release Branch Policy](#release-branch-policy) |
| Check version syntax | [Production Release Version Policy](#production-release-version-policy) |
| Follow how CI publishes a version | [Release Workflow](#release-workflow) |
| Inspect CI and publication boundaries | [Pull-Request Validation And Release Provenance](#pull-request-validation-and-release-provenance) |
| Understand immutable-release guarantees | [Immutable Release Policy](#immutable-release-policy) |
| Assess ownership and independent review | [Critical-Path Ownership](#critical-path-ownership) and [Human Review Trust Boundary](#human-review-trust-boundary) |
| Verify live settings for a new decision | [Manual Re-verification](#manual-re-verification) and [Limits](#limits) |
| Understand the star-history data branch | [Stats Branch Policy](#stats-branch-policy) |

Release preparation and evidence responsibilities belong to [Release Documentation And Evidence](maintainers/release-documentation.md). The [ruleset REST API](https://docs.github.com/en/rest/repos/rules), [ruleset semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets), and [CODEOWNERS behavior](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) are the external interpretation references.

## Main Branch Policy

The active repository ruleset `require-signed-commits-on-main` (ID `20677005`) targets exactly `refs/heads/main` and has no bypass actor. It contains:

- `pull_request`, with no required approving review, no code-owner review requirement, and squash as the only allowed merge method;
- `non_fast_forward`, which blocks force pushes;
- `required_signatures`, which requires signed commits; and
- `required_status_checks`, with the exact GitHub Actions checks `repository-guards`, `unit-and-integration-tests`, and `hook-runtime-gate` in strict mode.

All three checks must pass before merge, and strict mode requires the pull-request branch to be current with `main` before their final results are accepted. Only the stable hook aggregate is required; the three native platform jobs remain directly visible for diagnosis.

The ruleset contains no `deletion` rule, so this page claims no deletion restriction on the default branch.

## Release Tag Policy

The active repository ruleset `require-github-signed-release-tags` (ID `20724385`) targets exactly `refs/tags/v*` and has no bypass actor. It contains:

- `required_signatures`, so a release tag is either a lightweight tag on a signed commit or an annotated tag signed by its creator;
- `required_status_checks`, with the exact GitHub Actions checks `repository-guards`, `unit-and-integration-tests`, `hook-runtime-gate`, and `Verify signed main history` on the tagged commit;
- `deletion`, which prevents ordinary actors from deleting matching tags; and
- `non_fast_forward`, which blocks the forced update needed to replace an existing Git tag.

It contains no `creation` rule, and no other ruleset restricts tag creation. Pushing a `v*` tag is the release decision, so release authority is write access to this repository. Contributors can still fork the repository, create branches and tags in their forks, and propose pull requests; a tag in a fork releases nothing.

The required status checks are commit-level evidence and may be reusable for the same commit independently of the event that produced them. The [Release workflow](#release-workflow) therefore reads them again on the exact tagged commit, together with its place on `main` and its GitHub-made signature, before its first write.

## Release Branch Policy

The `release` branch holds the installed tree that both marketplace catalogs select: each release adds one commit whose tree is the tagged `plugin/` directory with the version stamped into both plugin manifests, plus `LICENSE`. The active repository ruleset `protect-release-branch` targets exactly `refs/heads/release` and has no bypass actor. It contains:

- `deletion`, which prevents ordinary actors from deleting the branch; and
- `non_fast_forward`, which blocks force pushes, so every published installed tree stays in the branch history.

It contains no `creation` rule: the Release workflow creates the branch with `GITHUB_TOKEN` when it is absent. A new branch starts at `main`'s root commit `fb86eb61e8161642c627bcce84c214730634b570`, whose tree holds only `LICENSE`, because `createCommitOnBranch` always builds on an existing branch head. The branch never carries `.github/workflows/`: `GITHUB_TOKEN` cannot be granted the `workflows` permission, and GitHub refuses a token write that creates, changes, or deletes a workflow file.

Before each write, the Release workflow requires the branch head to descend from that root commit, to hold only `plugin/` and `LICENSE`, and to carry an older version than the tag. A tampered branch therefore fails the next release closed. Because the branch holds no workflow files, a push to it starts no workflow; its commit is checked by `Verify release branch commit`, which the Release workflow dispatches on the release tag. That check fails unless the branch head is GitHub-signed, descends from the root commit, and declares exactly the dispatched tag's version, and that tag's commit is on `main`.

## Production Release Version Policy

Axiom production releases use stable numeric `MAJOR.MINOR.PATCH` versions. Each component is either `0` or a nonzero decimal digit followed by decimal digits. The release tag `v<version>` is the version's only source: the plugin manifests on `main` declare no version, and the Release workflow stamps the tag's version into both manifests of the tree it commits to `release`. Prerelease identifiers, build metadata, leading-zero components, and missing or extra components are rejected.

`.ci/axiom_validation/release_versions.py` owns the canonical parser, derived Bash tag pattern, and shared regression corpus. The Release workflow, the exact JavaScript signed-target guard, the Bash publication gate, the release evidence, and the GitHub Latest comparison must remain equivalent to that policy. The signed-target guard requires the version that the release-branch manifests declare to name a tag on `main`.

Historical tags and Releases remain immutable records and are not rewritten. Prerelease or build-metadata support requires a separately reviewed design for GitHub prerelease state, Latest selection, precedence and duplicate-build semantics, evidence asset names, release recovery, and compatibility claims.

## Pull-Request Validation And Release Provenance

`Distribution and publication guards` produces the `repository-guards` check. It validates a proposed pull-request tree with read-only repository checks. It does not establish release provenance, prevent a Git ref mutation, or authorize publication.

### Repository Guards Canonical Environment

The checked-in workflow contract pins the required `repository-guards` job to the exact `ubuntu-24.04` runner. Full-commit-SHA setup Actions select Python `3.14.7` and Node.js `24.19.0`; the exact `package-manager-cache: false` setting keeps package-manager caching disabled. Checkout credentials remain non-persistent. Before validation, the job reports `/etc/os-release`, `python --version`, `node --version`, and `git --version`. Distribution agreement and publication policy run through one read-only aggregate: `python -B .ci/check.py publication`. The aggregate validates the manifest, marketplace, and README skill inventory alongside the remaining publication invariants.

Fork pull requests use ordinary `pull_request`, receive only `contents: read`, and receive no repository secret. The job ID and stable required-check name remain `repository-guards`; the workflow performs no repository or external mutation.

No moving `ubuntu-latest` compatibility canary is currently defined. This omission is deliberate: without reviewed ownership, cadence, failure triage, and runner-upgrade criteria, a non-required canary would create an unowned signal that could be mistaken for canonical acceptance. Any future canary must define those responsibilities in a separate reviewed contract, remain read-only with a distinct non-required check name, and never be described as release provenance or installed-host evidence.

`Unit and integration tests` produces the exact `unit-and-integration-tests` check. It runs the complete standard-library unittest discovery command in the fixed blocking environment and remains separate from package and publication-policy validation. The active `main` ruleset requires these two checks plus `hook-runtime-gate` and accepts all three only from GitHub Actions.

`Cross-platform hook runtime integration` separately executes the exact checked-in Codex and Claude Code `SessionStart` command strings on `ubuntu-24.04`, `windows-2025`, and `macos-15`. Its three read-only matrix checks are `hook-runtime-ubuntu-24.04`, `hook-runtime-windows-2025`, and `hook-runtime-macos-15`. They use no repository secret, do not persist checkout credentials, and exercise only temporary roots through `cmd.exe` or no-profile Bash, as applicable to the checked-in command.

### Hook Runtime Gate

The same workflow defines one stable aggregate job and check, `hook-runtime-gate`. It uses `if: always()`, depends on the complete `hook-runtime` matrix job, and accepts only the current workflow run's `needs.hook-runtime.result == success`. Failed, cancelled, skipped, neutral, or missing current-run evidence therefore cannot produce a successful aggregate check. Because the dependency is the matrix job ID rather than a list of platform check names, an approved matrix expansion is included without changing the public aggregate name. The aggregate job performs no checkout, receives no secret, and has no repository mutation step.

The workflow also runs at `17 6 * * 1`, a bounded weekly compatibility observation on the default branch. A scheduled failure reports runner-image, shell, runtime, setup-action, or command drift through ordinary Actions state; it does not mutate repository settings and is not installed-host or model-session evidence. Pull requests continue to use ordinary `pull_request`, global `contents: read`, and checkout with credential persistence disabled; `pull_request_target` and repository secrets remain absent.

Main merges and release-tag creation require `hook-runtime-gate`, so a platform-specific hook failure blocks the normal `main` merge path and the release of that commit. The Release workflow requires the same exact checks on the tagged commit: failed, cancelled, skipped, neutral, or wrong-App aggregate evidence fails before any write. This is native process and server-side policy evidence; it does not show how a host's model behaves.

## Release Workflow Boundaries

### Release Workflow

`Release` ([`.github/workflows/release.yml`](../../.github/workflows/release.yml)) runs on `push` of a `v*` tag and on nothing else. It checks out the tagged commit without persisted credentials and runs [`.ci/scripts/release.py`](../../.ci/scripts/release.py) with the Python standard library, Git, and the GitHub API; it runs no AI model or agent, uses no secret, App token, or Actions environment, and its validator rejects any other trigger or Action. Its job has `actions: write` to dispatch the publisher and the signature guard, `checks: read`, and `contents: write` for the release branch and the Draft.

It runs these gates in order and writes nothing until all of them pass:

1. the tag name is strict SemVer `vX.Y.Z`, and an annotated tag carries a verified signature;
2. the tagged commit is `main`'s head or an ancestor of it, and has a valid signature made with GitHub's signing key;
3. `repository-guards`, `unit-and-integration-tests`, `hook-runtime-gate`, `Verify signed main history`, and `Verify created release tag` succeeded on the tagged commit;
4. the version is the immediate patch, minor, or major successor of GitHub Latest, and Latest is the highest published release;
5. the installed-runtime digest of the tagged tree differs from the one recorded in Latest's evidence asset, except for the bootstrap release that runs while `release` holds no release commit yet;
6. no Release uses the tag, and the release branch passes its [shape check](#release-branch-policy) with an older version; and
7. the tagged tree with both manifests stamped passes `python3 -B .ci/check.py --release-version X.Y.Z` in a disposable worktree.

It then fast-forwards `release` by one GitHub-signed `createCommitOnBranch` commit and verifies its tree, parent, and signature. It stages the Draft with the plugin zip and the release-policy asset, dispatches `Publish immutable release` on the tag, and dispatches `Verify release branch commit` and `Observe published immutable release`. It identifies each dispatched run by its new run ID and exact head commit, and requires that run to succeed.

The workflow has no resume path. A failure after the tag exists leaves no Release, and the next attempt uses the next version; the [release procedure](maintainers/release-documentation.md#recovery) describes the cases.

### Evidence Boundaries

The checked-in `Release signature guard` maps each evidence boundary to one stable name: `Verify signed main history` for a push to `main`, `Verify created release tag` for a tag creation, `Verify release branch commit` for a `phase=release-branch` dispatch on a release tag, and `Observe published immutable release` for a published or edited Release and its `phase=published-release` dispatch on a tag. A created tag must be one exact strict SemVer single-creation event whose commit is on `main` and GitHub-signed. A published Release must be final, non-prerelease, immutable, and bound to the tagged commit.

`Publish immutable release` is a separate dispatch-only workflow. It accepts only one strict SemVer release tag, grants only `contents: write`, and has no pull-request, push, release, schedule, secret, or arbitrary repository input. It globally serializes Latest publication and derives the release subject itself from the tag: the tag object, tagged commit and tree, the stamped tree it builds, the release-branch head, which must hold exactly that tree with a GitHub-made signature, the plugin zip it rebuilds, the runtime digest, the previous release, and the notes digest. It verifies the live tag, release branch, `main` history, and REST plus GraphQL signatures, and rejects a different equal-or-newer current stable release version. It then freezes one numeric Release ID, validates the downloaded policy asset and plugin zip byte for byte, and uploads one deterministic evidence asset without replacement. It downloads all three assets again, publishes the same Draft, and requires the final Release to be immutable and GitHub Latest. It can resume a Draft after the exact evidence asset already exists and can perform final-only readback without a second publication mutation.

GitHub does not start another workflow for an ordinary event created by a workflow's `GITHUB_TOKEN`, so neither the release-branch commit nor the published Release starts the signature guard by itself. GitHub does start a run for a `workflow_dispatch` event made with that token, so the Release workflow dispatches the guard on the tag with `phase=release-branch` and with `phase=published-release`, and waits for both to pass; both checks attach to the tagged commit.

## Stats Branch Policy

The `stats` branch holds only the star-history data `stars.csv`, the rendered chart `stars.svg`, and a short README. The rulesets above target `refs/heads/main`, `refs/tags/v*`, and `refs/heads/release`, so `stats` has no required checks, signature requirement, or deletion protection. It is not a release or distribution surface, and nothing under `plugin/**` reads it.

`Record star history` (`.github/workflows/record-star-history.yml`) owns the branch. It runs daily and on manual dispatch, grants only `contents: write` to its job, uses no other secret, and runs the standard-library script `.ci/scripts/record-star-history.py`. The script reads `stargazers_count` and `forks_count` from the repository API, replaces or appends the row for the current UTC date, renders the chart, and commits both files only when the data or the rendered chart differs from the branch. The chart is drawn in a sketched, hand-lettered style: axes, line, and legend pass through one SVG displacement filter, and the text uses a printable-ASCII subset of the Patrick Hand typeface embedded in the SVG from `.ci/scripts/fonts/` (SIL Open Font License 1.1, `PatrickHand-OFL.txt`), so the chart renders the same in every viewer and the output is deterministic for the same data. On the first run it creates the branch from a parentless root commit that holds the branch README through the Git Data API; every data commit uses the GraphQL `createCommitOnBranch` mutation. GitHub signs commits that the workflow token creates through either API and attributes them to `github-actions[bot]`.

Commits made with `GITHUB_TOKEN` start no other workflow run. A manual push to `stats` would start the distribution guards and fail on that tree, so maintainers do not push to `stats` by hand. The README embeds the chart from the raw `stats` URL; a missing or stale chart means the workflow has not run and says nothing about the plugin or a release.

## Immutable Release Policy

Immutable releases are enabled for `wheakerd/axiom`. The setting applies to Releases published after it was enabled.

The checkout cannot prove that this remote setting remains enabled. The release workflow reads it before any mutation, immediately before publication, and after publication. Final acceptance also requires GitHub's Release response itself to report `immutable: true`.

GitHub's documented immutable-release guarantees cover the associated tag and uploaded assets, and GitHub attaches its own release attestation to an immutable Release. They do not document the Release title, body, Latest marker, or Release object as immutable. Axiom's content-addressed evidence asset binds the exact title and release-notes SHA-256, and later verification fails on metadata drift. That is durable detection, not a claim that the platform blocks every metadata edit or Release deletion.

## Critical-Path Ownership

The checked-in [CODEOWNERS file](../../.github/CODEOWNERS) assigns the critical paths to the repository owner `@wheakerd`: the CODEOWNERS file itself, the workflows, both plugin manifests, both marketplace catalogs, the hooks, the startup gate, the scripts, the validators, the tests, the security policy, and this page. The publication aggregate requires that exact owner set.

The validator and tests are covered because the stable scripts delegate policy decisions to those paths. Ownership of only the wrapper script would leave a sibling path able to change the accepted result.

CODEOWNERS declares responsibility and requests review. It does not require an approval by itself. The main ruleset does not require code-owner review, so critical-path code-owner approval is not server-side enforced.

## Human Review Trust Boundary

`wheakerd` is the repository's single maintainer and its ultimate trust root, and the absence of independent human review is a known limitation. Every critical-path CODEOWNERS entry names that account. CODEOWNERS is advisory: it assigns responsibility and requests review, but it does not block an unapproved merge, because the main ruleset requires neither an approving review nor code-owner review.

The preventive controls are the server-side pull-request requirement, required signatures, non-fast-forward protection, strict required checks, squash-only main merges, and the release-tag and release-branch integrity rules. Server-side enforcement of the three required check contexts is preventive, while the repository-owned validator and test content behind those results remains controlled by the same trust root.

The detective controls are the repository validators and tests, GitHub Actions and check output, signed-target and release observations, content-addressed release evidence assets, manual read-only API re-verification, and ruleset-history entries. They can expose drift or preserve provenance, but they do not supply an independent human approval. Hardware-backed authentication and an independently controlled release identity are not claimed as compensating controls.

Emergency or administrative ruleset changes remain auditable through GitHub's ruleset version history. That audit trail is detective evidence; because the governing administrator is the same identity, it is not an independent trust domain.

Independent review must not be enforced until a different trusted GitHub principal has direct write access, is added alongside `@wheakerd` as a code owner for every critical path, and has approved a protected test pull request that changes at least one such path. That test must prove that the approval counts without author self-approval or a ruleset bypass. Only after that proof and a live API read-back should the main ruleset require an approving review, code-owner review, last-push approval, stale-review dismissal, and review-thread resolution.

## Manual Re-verification

Use read-only calls and compare the returned values with this document. Do not copy tokens or full administrative API responses into the repository.

1. List active repository rulesets. For this public repository, GitHub permits an unauthenticated request; a fine-grained token needs only repository metadata read permission.

   ```bash
   gh api -X GET 'repos/wheakerd/axiom/rulesets?includes_parents=true' \
     --jq '.[] | [.id, .name, .target, .enforcement] | @tsv'
   ```

2. For each returned ID, inspect the exact target, ref conditions, rules, and enforcement without writing the ruleset.

   ```bash
   gh api -X GET 'repos/wheakerd/axiom/rulesets/RULESET_ID?includes_parents=true' \
     --jq '{name,target,enforcement,conditions,rules,bypass_actors,current_user_can_bypass}'
   ```

3. Confirm the effective rules on `main`, the default branch, workflow names, and the exact check-run names on the current commit.

   ```bash
   gh api -X GET repos/wheakerd/axiom/rules/branches/main
   gh api -X GET repos/wheakerd/axiom --jq '.default_branch'
   gh api -X GET repos/wheakerd/axiom/actions/workflows \
     --jq '.workflows[] | [.name, .path, .state] | @tsv'
   gh api -X GET repos/wheakerd/axiom/commits/main/check-runs \
     --jq '.check_runs[] | [.name, .app.slug, .status, .conclusion] | @tsv'
   ```

4. With a repository administrator present, repeat the individual ruleset GET, because GitHub omits bypass details from callers without ruleset write visibility. Verify that `require-github-signed-release-tags` has no bypass actor and no `creation` rule and requires exactly the four contexts listed in [Release Tag Policy](#release-tag-policy), that `protect-release-branch` has no bypass actor and exactly the `deletion` and `non_fast_forward` rules, and that no other active ruleset targets `refs/tags/v*` or `refs/heads/release`.

5. With repository administration read access, list direct collaborators and inspect every active ruleset's history. Confirm that a second trusted write-capable principal has not appeared and preserve each history actor as detective evidence rather than independent review.

   ```bash
   gh api --paginate -X GET \
     'repos/wheakerd/axiom/collaborators?affiliation=direct&per_page=100' \
     --jq '.[] | [.login, .permissions.admin, .permissions.maintain, .permissions.push] | @tsv'
   gh api --paginate -X GET \
     'repos/wheakerd/axiom/rulesets/RULESET_ID/history?per_page=100' \
     --jq '.[] | [.version_id, .actor.id, .actor.type, .updated_at] | @tsv'
   ```

6. Review `.github/CODEOWNERS` on the protected base branch, run the repository static checks, and correct this page in the same reviewed change as any changed policy value.

## Limits

- GitHub's legacy `branches/main/protection` endpoint returns `404 Branch not protected`; protection is in repository rulesets and the effective branch-rules endpoint.
- No destructive proof of branch or tag rejection has been attempted. The conclusions above follow from the active rule types and GitHub's documented semantics.
- No scheduled or manually dispatched governance-audit workflow exists. The manual method exposes the relevant public settings, while an automated job could not prove hidden bypass actors without elevated permission. A workflow must never receive ruleset-write permission merely to perform an audit.
- The repository's static checks verify only that CODEOWNERS assigns every critical path to the owner and that each critical pattern matches a file in the repository. They cannot contact GitHub or prove that remote configuration has not drifted; manual re-verification covers that.
