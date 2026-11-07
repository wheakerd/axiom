# Repository Governance

This reference is for maintainers and auditors reviewing repository controls. It describes the controls in force and where each one is enforced. It does not configure GitHub, grant authority, or replace server-side rulesets, and editing it does not re-verify the live repository: the release-tag controller reads the live rulesets before it creates a tag, and [Manual Re-verification](#manual-re-verification) gives the read-only calls for a new decision. For plugin execution and permissions, use the [Trust Model](trust-model.md).

## Find The Relevant Boundary

| Review task | Section |
| --- | --- |
| Classify a repository change | [Runtime Identity](runtime-identity.md#classify-a-change) |
| Inspect merge and tag restrictions | [Main Branch Policy](#main-branch-policy) and [Release Tag Policy](#release-tag-policy) |
| Understand release-controller permissions | [Release Tag Controller](#release-tag-controller) |
| Check version syntax | [Production Release Version Policy](#production-release-version-policy) |
| Follow how CI publishes a version | [Release Pipeline](#release-pipeline) |
| Inspect CI and publication boundaries | [Pull-Request Validation And Release Provenance](#pull-request-validation-and-release-provenance) |
| Understand immutable-release guarantees | [Immutable Release Policy](#immutable-release-policy) |
| Assess ownership and independent review | [Critical-Path Ownership](#critical-path-ownership) and [Human Review Trust Boundary](#human-review-trust-boundary) |
| Verify live settings for a new decision | [Manual Re-verification](#manual-re-verification) and [Limits](#limits) |
| Understand the star-history data branch | [Stats Branch Policy](#stats-branch-policy) |

Release preparation and evidence responsibilities belong to [Release Documentation And Evidence](maintainers/release-documentation.md). The [ruleset REST API](https://docs.github.com/en/rest/repos/rules), [ruleset semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets), and [CODEOWNERS behavior](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) are the external interpretation references.

## Main Branch Policy

The active repository ruleset `require-signed-commits-on-main` targets exactly `refs/heads/main` and has no bypass actor. It contains:

- `pull_request`, with no required approving review, no code-owner review requirement, and squash as the only allowed merge method;
- `non_fast_forward`, which blocks force pushes;
- `required_signatures`, which requires signed commits; and
- `required_status_checks`, with the exact GitHub Actions checks `repository-guards`, `unit-and-integration-tests`, and `hook-runtime-gate` in strict mode.

All three checks must pass before merge, and strict mode requires the pull-request branch to be current with `main` before their final results are accepted. Only the stable hook aggregate is required; the three native platform jobs remain directly visible for diagnosis.

The ruleset contains no `deletion` rule, so this page claims no deletion restriction on the default branch.

## Release Tag Policy

The active repository ruleset `require-github-signed-release-tags` targets exactly `refs/tags/v*` and has no bypass actor. It contains:

- `required_signatures`;
- `required_status_checks`, with the exact required GitHub Actions check `Verify signed main history`;
- `deletion`, which prevents ordinary actors from deleting matching tags; and
- `non_fast_forward`, which blocks the forced update needed to replace an existing Git tag.

It contains no `creation` rule. Its empty bypass list applies to every integrity rule in this ruleset.

The separate active ruleset `restrict-release-tag-creation` also targets exactly `refs/tags/v*` and contains exactly one `creation` rule. Its only bypass actor is the dedicated `axiom-release-tag-controller` GitHub App. Because the App bypass is scoped to this creation-only ruleset, it does not bypass any rule in `require-github-signed-release-tags`.

Together, the deletion and non-fast-forward rules prevent ordinary actors from deleting or updating an existing `v*` tag, and only the App may create a matching upstream tag. Other contributors can continue to fork the repository, create branches and tags in their forks, and propose pull requests; repository write access alone does not authorize formal release-tag creation.

The required status check remains commit-level evidence and may be reusable for the same commit independently of the event that produced it. Commit-level required-check evidence is defense in depth, not exact tag-creation authorization. The authenticated actor on the exact ref-create operation is the server-side creation authorization boundary.

## Release Tag Controller

The `release-tag-creation` Actions environment owns `AXIOM_RELEASE_APP_PRIVATE_KEY`, `AXIOM_RELEASE_APP_CLIENT_ID`, and the numeric `AXIOM_RELEASE_APP_ID`. The workflow runs only when dispatched on `refs/heads/main`: the Release pipeline dispatches it after a release pull request merges, and a maintainer may dispatch it to recover. Its ordinary `GITHUB_TOKEN` has only `contents: read` and `checks: read`. The minted App token is scoped to this repository and requests only `administration: read` plus `contents: write`; administration write is not granted. Pull-request code never receives the private key or App token.

The Release pipeline's catalog job uses the same environment to mint a separate repository-scoped App token that requests only `contents: write` and `pull_requests: write`. It opens and merges the catalog handoff pull request under the unchanged `main` rules. The App therefore needs the Pull requests read and write permission in addition to its tag-creation permissions. This page does not verify that live installation setting; without it, publication still completes and the catalog job stops before any write.

Before one exact `POST /git/refs`, the controller binds the requested version and tag, live protected-main commit and tree, the Codex manifest version, the three main ruleset checks, `Verify signed main history`, REST and GraphQL GitHub-made signature evidence, tag and Release absence, App installation identity and repository scope, and all three live rulesets. It performs the same complete read a second time, rejects any difference, creates only the exact absent tag, and immediately reads the ref back. After a valid creation response, only a GET returning HTTP 404 may be retried: at most four exact-ref reads, with waits of 1, 2, and 4 seconds. Each read uses the same read-only credential, frozen tag and commit, and existing request timeout. Other HTTP or transport errors, malformed responses, and ref, type, or commit mismatches stop immediately. Exhausted reads leave verification failed; the tag is never recreated.

The controller has no update or delete operation. An uncertain creation response is read back once and reported as a failure without retry; a rerun rejects the existing ref with zero mutation. Bounded visibility reads apply only after the single creation response has passed its exact-ref validation; they do not repeat the creation request, pre-creation gates, or workflow.

GitHub returns `bypass_actors` only to a caller with ruleset write access. The controller deliberately retains `administration: read`, so its App-token view must omit the `bypass_actors` property. It binds the three ruleset IDs plus their normalized server update instants, recorded in [`.ci/axiom_validation/release_tag_controller.py`](../.ci/axiom_validation/release_tag_controller.py), to the reviewed administrator-visible values, then requires the App's effective bypass states to be `never`, `never`, and `always` for main, tag integrity, and tag creation respectively. Any actor or rule edit changes the server-owned update instant and fails before tag mutation; no workflow receives ruleset-write permission merely to reveal the actor arrays.

The checked-in `Release signature guard` assigns distinct stable check names: `Verify signed main history`, `Verify release candidate`, `Verify created release tag`, and `Observe published immutable release`. `release/v<version>` runs can produce candidate evidence only. The controller accepts only the exact current `main` SHA and the main-history context, so a candidate result cannot authorize production tag creation.

A break-glass operation remains a separately authorized, audited ruleset change; no permanent interactive-user bypass is retained merely for convenience.

## Production Release Version Policy

Axiom production releases use stable numeric `MAJOR.MINOR.PATCH` versions. Each component is either `0` or a nonzero decimal digit followed by decimal digits. Manifest versions contain no `v` prefix; formal upstream tags and release-candidate branches use `v<version>` and `release/v<version>` respectively. Prerelease identifiers, build metadata, leading-zero components, missing or extra components, and prefixed manifest versions are rejected.

`.ci/axiom_validation/release_versions.py` owns the canonical parser, derived Bash tag pattern, and shared regression corpus. The Codex manifest, the exact JavaScript signed-target guard, the Bash publication gate, release evidence, GitHub Latest comparison, and attestation subjects must remain equivalent to that policy. The signed-target guard binds the version named by `release/v<version>` to the Codex manifest before formal tag creation; it later requires the same version from the exact `v<version>` tag and GitHub Release.

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

Main merges and protected tag creation require `hook-runtime-gate`, so a platform-specific hook failure blocks the normal `main` merge path. The release-tag controller requires the same three exact main checks: missing, duplicate, failed, cancelled, skipped, neutral, pending, wrong-commit, or wrong-App aggregate evidence fails before tag creation. This is native process and server-side policy evidence; it does not show how a host's model behaves.

## Release Workflow Boundaries

### Release Pipeline

`Release pipeline` (`.github/workflows/release-pipeline.yml`) publishes a version from CI. Its `pull_request` and `push` triggers both filter on `plugin/.codex-plugin/plugin.json`, the only file that declares the plugin version, so a pull request or `main` commit that leaves the manifest untouched never starts it. A manual dispatch on `main` resumes an interrupted release of the version `main` declares. The workflow runs only the Python standard library, Git, and the GitHub API through [`.ci/scripts/release-pipeline.py`](../.ci/scripts/release-pipeline.py); it runs no AI model or agent, and its validator rejects any Action beyond the pinned checkout, Python and Node.js setup, and App-token Actions.

- `Release candidate` runs on a pull request with `contents: read` and no secret. It reports whether the manifest version changed. A changed version must be the next patch, minor, or major version after a base version that is already a published immutable Release, with an absent tag and Release. It previews the exact Release body in the job summary and rehearses the catalog handoff on the pull-request head: it applies the catalog advance to a disposable worktree and runs `python -B .ci/check.py publication` and the unit tests on that tree.
- `Publish release` runs on `main` with `actions: write`, `checks: read`, and `contents: write`. It requires the exact pushed commit to remain `main` before tag creation, waits for `repository-guards`, `unit-and-integration-tests`, `hook-runtime-gate`, and `Verify signed main history` on that commit, then waits for every other GitHub Actions check on that commit to finish without failing, and rehearses the catalog handoff on that commit before any mutation. It then dispatches `Create protected release tag`, waits for `Verify created release tag` and the other tag-triggered checks, stages the exact Draft with its release-policy asset, dispatches `Publish immutable release` on the tag, and dispatches the published-release observation. It identifies each dispatched run by its new run ID and exact head commit, and requires that run to succeed.
- `Advance marketplace catalogs` runs only when the catalogs on `main` do not yet select the verified Latest tag. It validates the rendered handoff with `python -B .ci/check.py publication`, commits it through the GitHub API as a GitHub-signed commit, and opens a pull request. After the required checks pass on that commit, every other check on it has finished without failing, and Latest is rechecked, it squash-merges the pull request and reads back the merged tree, signature, and both catalogs.

Each job reads current GitHub state before acting, so rerunning a failed job resumes the earliest unfinished step. It stops without guessing when `main` moved before tag creation, a required check fails, any other check on the release commit fails, the rehearsed catalog handoff fails a repository check, or more than one new dispatched run appears. It also stops when a Release is published but mutable, an existing Draft or asset differs from the expected one, or a catalog branch from an earlier attempt exists. Merging other pull requests while a release is in progress makes the publisher's exact-main gate fail closed.

### Evidence Boundaries

The checked-in `Release signature guard` maps each evidence boundary to one stable name: `Verify signed main history`, `Verify release candidate`, `Verify created release tag`, and `Observe published immutable release`. A manual candidate run accepts only `release/v<version>` and requires the stable numeric branch version to match the Codex manifest. A manual published-release run accepts only the exact tag and requires the live Release to be final, non-prerelease, immutable, and commit-bound.

`Create protected release tag` is separate from the read-only signature guard and from immutable publication. It is dispatch-only on current `main`, consumes the dedicated App credential only after validating non-secret inputs, rereads all drift-sensitive state twice, and owns the sole normal tag-creation attempt. It has no pull-request, push, release, schedule, update, delete, publication, or ruleset-write path.

`Publish immutable release` is a separate dispatch-only workflow. It accepts only one stable numeric production release tag from the current `main` commit, grants only `contents: write`, and has no pull-request, push, release, schedule, secret, or arbitrary repository input. It globally serializes Latest publication, verifies the live immutable setting, main/tag identity, and REST plus GraphQL GitHub-made signature, and rejects a different equal-or-newer current stable release version, then uniquely freezes one numeric Release ID. It validates one downloaded release-policy asset. It uploads one deterministic attestation without replacement, downloads both remote assets, publishes the same draft, and requires the final Release to be immutable and GitHub Latest. It can resume a draft after the exact attestation already exists and can perform final-only readback without a second publication mutation.

After successful final verification, including final-only recovery, it emits the standard marketplace source that both host catalogs use for the verified Latest version. The summary explicitly leaves both catalogs pending the [signed catalog update](maintainers/release-documentation.md#marketplace-publication). The publisher itself adds no `main` push trigger, branch write, or client update policy; the Release pipeline's catalog job completes the handoff through a pull request.

The release-target guard remains a separate policy owner. GitHub does not start another workflow for an ordinary event created by a workflow's `GITHUB_TOKEN`, so the publication workflow fails closed on direct signature readback. GitHub does start a run for a `workflow_dispatch` event made with that token, so the Release pipeline dispatches `Release signature guard` with `phase=published-release` on the exact published tag and waits for it to pass.

## Stats Branch Policy

The `stats` branch holds only the star-history data `stars.csv`, the rendered chart `stars.svg`, and a short README. The rulesets above target `refs/heads/main` and `refs/tags/v*`, so `stats` has no required checks, signature requirement, or deletion protection. It is not a release or distribution surface, and nothing under `plugin/**` reads it.

`Record star history` (`.github/workflows/record-star-history.yml`) owns the branch. It runs daily and on manual dispatch, grants only `contents: write` to its job, uses no other secret, and runs the standard-library script `.ci/scripts/record-star-history.py`. The script reads `stargazers_count` and `forks_count` from the repository API, replaces or appends the row for the current UTC date, renders the chart, and commits both files only when the data or the rendered chart differs from the branch. The chart is drawn in a sketched, hand-lettered style: axes, line, and legend pass through one SVG displacement filter, and the text uses a printable-ASCII subset of the Patrick Hand typeface embedded in the SVG from `.ci/scripts/fonts/` (SIL Open Font License 1.1, `PatrickHand-OFL.txt`), so the chart renders the same in every viewer and the output is deterministic for the same data. On the first run it creates the branch from a parentless root commit that holds the branch README through the Git Data API; every data commit uses the GraphQL `createCommitOnBranch` mutation. GitHub signs commits that the workflow token creates through either API and attributes them to `github-actions[bot]`.

Commits made with `GITHUB_TOKEN` start no other workflow run. A manual push to `stats` would start the distribution guards and fail on that tree, so maintainers do not push to `stats` by hand. The README embeds the chart from the raw `stats` URL; a missing or stale chart means the workflow has not run and says nothing about the plugin or a release.

## Immutable Release Policy

Immutable releases are enabled for `wheakerd/axiom`. The setting applies to Releases published after it was enabled.

The checkout cannot prove that this remote setting remains enabled. The release workflow reads it before any mutation, immediately before publication, and after publication. Final acceptance also requires GitHub's Release response itself to report `immutable: true`.

GitHub's documented immutable-release guarantees cover the associated tag and uploaded assets. They do not document the Release title, body, Latest marker, or Release object as immutable. Axiom's content-addressed attestation binds the exact title and release-notes SHA-256, and later verification fails on metadata drift. That is durable detection, not a claim that the platform blocks every metadata edit or Release deletion.

## Critical-Path Ownership

The checked-in [CODEOWNERS file](../.github/CODEOWNERS) assigns the critical paths to the repository owner `@wheakerd`: the CODEOWNERS file itself, the workflows, both plugin manifests, both marketplace catalogs, the hooks, the startup gate, the scripts, the validators, the tests, the security policy, and this page. The publication aggregate requires that exact owner set.

The validator and tests are covered because the stable scripts delegate policy decisions to those paths. Ownership of only the wrapper script would leave a sibling path able to change the accepted result.

CODEOWNERS declares responsibility and requests review. It does not require an approval by itself. The main ruleset does not require code-owner review, so critical-path code-owner approval is not server-side enforced.

## Human Review Trust Boundary

`wheakerd` is the repository's single maintainer and its ultimate trust root, and the absence of independent human review is a known limitation. Every critical-path CODEOWNERS entry names that account. CODEOWNERS is advisory: it assigns responsibility and requests review, but it does not block an unapproved merge, because the main ruleset requires neither an approving review nor code-owner review.

The preventive controls are the server-side pull-request requirement, required signatures, non-fast-forward protection, strict required checks, squash-only main merges, and the release-tag creation and integrity rules. Server-side enforcement of the three required check contexts is preventive, while the repository-owned validator and test content behind those results remains controlled by the same trust root.

The detective controls are the repository validators and tests, GitHub Actions and check output, signed-target and release observations, content-addressed release attestations, manual read-only API re-verification, and ruleset-history entries. They can expose drift or preserve provenance, but they do not supply an independent human approval. Hardware-backed authentication and an independently controlled release identity are not claimed as compensating controls.

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

4. With a repository administrator present, repeat the individual ruleset GET and verify that `require-github-signed-release-tags` has no bypass actors or `creation` rule, while `restrict-release-tag-creation` has exactly one `creation` rule and only App ID `4756785` as an `Integration` / `always` bypass. The same read-back must show no owner-user bypass, no integrity bypass, and only `Verify signed main history` as the integrity required context. GitHub omits bypass details from callers without ruleset write visibility. The controller therefore binds the administrator-verified IDs and update instants while requiring the read-only App's effective bypass states to remain `never`, `never`, and `always`; no workflow receives administration write.

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
- The repository's static checks verify only that CODEOWNERS assigns every critical path to the owner. They cannot contact GitHub or prove that remote configuration has not drifted; the release-tag controller's live read and manual re-verification cover that.
