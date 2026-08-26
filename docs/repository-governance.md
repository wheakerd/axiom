# Repository Governance

This document is a dated, read-only observation of GitHub repository policy.
It does not configure GitHub, grant authority, or replace server-side rulesets.
A failed workflow is detection evidence, not server-side mutation prevention.

Last verified (UTC): `2026-08-26`

Verification used authenticated read-only GitHub REST and GraphQL queries for
the public `wheakerd/axiom` repository after the separately authorized main
ruleset update. The verification queries changed no ruleset, branch, tag,
release, workflow, permission, collaborator, or repository setting. The
[ruleset REST API](https://docs.github.com/en/rest/repos/rules),
[ruleset semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets),
and [CODEOWNERS behavior](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
are the external interpretation references.

## Main Branch Policy

The active repository ruleset `require-signed-commits-on-main` targets exactly
`refs/heads/main`. Its REST response reported `bypass_actors: []` and
`current_user_can_bypass: never`. It contains:

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
exactly `refs/tags/v*`. Its REST response reported `bypass_actors: []` and
`current_user_can_bypass: never`. It contains:

- `required_signatures`;
- `required_status_checks`, with the exact required GitHub Actions check
  `Verify GitHub-signed release target`,
  `strict_required_status_checks_policy: false`, and
  `do_not_enforce_on_create: false`;
- `deletion`, which prevents ordinary actors from deleting matching tags; and
- `non_fast_forward`, which blocks the forced update needed to replace an
  existing Git tag.

Together, the observed deletion and non-fast-forward rules prevent ordinary
actors from deleting or updating an existing `v*` tag. This conclusion is
derived from the active rule types and GitHub's documented semantics; no tag
mutation was attempted. The empty bypass list means no bypass actor was
observed with the write-visible response used for this verification.

The ruleset has no `creation` restriction and exposes no creator allowlist.
Actors with Git write permission may create a matching tag only when the
signature and required-check rules are satisfied. The REST ruleset does not
enumerate the complete effective actor roster. Release-tag creator allowlist:
**UNAVAILABLE**.

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

`Release signature guard` produces the exact
`Verify GitHub-signed release target` check. The tag ruleset requires that check
for `v*`; the workflow also verifies signed `main` history and observes later
tag or GitHub Release events. Its event-time detection remains distinct from
the active tag ruleset's pre-mutation deletion and force-push restrictions.

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
   and verify `bypass_actors`. GitHub may omit that property from a response to
   a caller without ruleset write visibility. This remains a manual read-only
   verification; do not grant a workflow administrative permission.

5. Review `.github/CODEOWNERS` on the protected base branch, run the repository
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
- Exact collaborator membership, the effective release-tag creator roster,
  and a destructive proof of branch or tag rejection were not collected.
- Repository-plan capability was not inferred from documentation. The two
  named rulesets were directly observed as active; unavailable fields remain
  unavailable if a future plan or API response hides them.
- No scheduled or manually dispatched governance-audit workflow was added.
  The manual method already exposes the relevant public settings, while an
  automated job could not prove hidden bypass actors without elevated
  permission. A workflow must never receive ruleset-write permission merely to
  perform an audit.
- The repository's static validator checks that this dated snapshot retains
  its required facts and exact critical-path owner set. It cannot contact
  GitHub or prove that remote configuration has not drifted; manual
  re-verification remains required.
