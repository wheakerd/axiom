---
name: traceable-git-submit
description: Keep Git work traceable with local checkpoint commits and publish one clean consolidated commit. Use when the user asks to enable or run a traceable Git workflow, create local checkpoint commits, cache the last remote-push baseline in Git metadata, compare unpublished commits against upstream, consolidate authorized checkpoint commits, submit/publish/push through a one-final-commit workflow, or recover/audit a working tree before that workflow pushes.
---

# Traceable Git Submit

Use this skill to keep local work reviewable through checkpoint commits while
publishing a single clean commit when the user explicitly asks to submit,
publish, or push.

## Safety Rules

- Do not commit unless the user asks for a commit or authorizes the traceable
  checkpoint workflow for the current task or session.
- Do not push unless the user explicitly asks to submit, publish, or push.
- Do not use `git reset --hard`.
- Do not stage unrelated user changes.
- Do not stage or commit baseline cache files. The current cache lives in Git
  metadata, and the legacy `.agents/.cache/traceable-git-submit-baseline.json`
  path is local workflow state, not a project artifact.
- Do not treat `Axiom-checkpoint: true` as sufficient proof that a commit
  belongs to the current authorized workflow. Require the active checkpoint
  provenance record described below.
- Do not rewrite, squash, or drop unclear, non-workflow, already-pushed, or
  user-authored commits without explicit confirmation.
- If repository instructions specify a different cache location or Git policy,
  follow the higher-priority repository instructions and report the difference.

## Baseline Cache

Resolve the baseline cache path from the target Git repository's metadata, not
from the working tree and not from the installed plugin directory:

```bash
git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-baseline.json
```

Use the resolved path as the only current baseline cache location. It must live
under Git metadata, must not appear in `git status`, must not depend on the
target repository's `.gitignore`, and must work when `.git` is a file in a
linked worktree. Do not hand-build `.git/axiom/...`, and do not use
`PLUGIN_ROOT` as target repository runtime state.

The cache is advisory local workflow state. The upstream remote-tracking ref
from `@{u}` remains authoritative.

Cache schema:

```json
{
  "repo": "<repository-name>",
  "branch": "<current-branch>",
  "upstream": "<remote>/<branch>",
  "remote": "<branch-remote>",
  "mergeRef": "<branch-merge-ref>",
  "lastRemotePushSha": "<upstream-sha>",
  "updatedAt": "<utc-iso8601>"
}
```

Legacy cache migration:

- Legacy path:
  `.agents/.cache/traceable-git-submit-baseline.json` under the target working
  tree.
- If the new Git metadata cache exists, use it and leave any legacy file
  untouched.
- If only the legacy file exists, read it as JSON and validate `repo`, `branch`,
  `upstream`, and `lastRemotePushSha` against the current repository name,
  branch short name, upstream ref, and `@{u}` SHA.
- Migrate legacy state to the new Git metadata cache only when all four fields
  match. Add `remote` and `mergeRef` from the current Git preflight facts when
  writing the new schema.
- If the legacy file is invalid JSON or any required field mismatches, ignore
  it, report the legacy path and mismatch, and do not copy its state into the
  new cache.
- Never stage, commit, delete, or rewrite the legacy cache automatically.

Do not require a bundled programming-language helper for cache operations.
Perform the workflow directly with Git plus the operating system's native shell
or structured file tools for the current environment. If a script is ever
needed, prefer OS-native interpreters for the target environment: POSIX shell on
macOS/Linux and PowerShell on Windows.

Use `init` semantics when a checkpoint, submit, or push workflow starts and the
cache may not exist. Use `check` semantics before checkpoint consolidation or
push. Use `update` semantics only after a push workflow completes successfully
and the new remote HEAD has been verified.

## Active Checkpoint Provenance

For every authorized checkpoint workflow, read and follow
`references/checkpoint-provenance.md` before creating checkpoints or
consolidating them. It records the exact SHA list created by the current
authorized workflow in target Git metadata. A commit message marker remains a
required secondary check, but never proves current authorization by itself.

Use these Git facts for all cache operations and workflow preflight:

```bash
git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-baseline.json
git -C <repo> symbolic-ref --quiet HEAD
git -C <repo> branch --show-current
git -C <repo> rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git -C <repo> config --get "branch.<branch>.remote"
git -C <repo> config --get "branch.<branch>.merge"
git -C <repo> rev-parse --verify HEAD
git -C <repo> rev-parse --verify '@{u}'
git -C <repo> rev-list --left-right --count HEAD...'@{u}'
git -C <repo> rev-parse --path-format=absolute --git-path MERGE_HEAD
git -C <repo> rev-parse --path-format=absolute --git-path CHERRY_PICK_HEAD
git -C <repo> rev-parse --path-format=absolute --git-path REVERT_HEAD
git -C <repo> rev-parse --path-format=absolute --git-path REBASE_HEAD
git -C <repo> rev-parse --path-format=absolute --git-path rebase-merge
git -C <repo> rev-parse --path-format=absolute --git-path rebase-apply
```

On macOS/Linux, create the resolved cache directory with `mkdir -p
"$(dirname "$cache_path")"` and write JSON with a shell heredoc or another
available structured JSON writer. On Windows, create the resolved cache
directory with PowerShell `New-Item -ItemType Directory -Force (Split-Path
$cachePath)` and write JSON with `ConvertTo-Json` plus `Set-Content -Encoding
utf8`. Use the equivalent native command only after resolving `<repo>`, cache
path, branch ref, branch short name, upstream ref, branch remote, merge ref,
upstream SHA, HEAD SHA, ahead/behind state, and UTC update time in the current
environment.

If cached `branch`, `upstream`, `remote`, `mergeRef`, or `lastRemotePushSha`
differs from the current branch short name, upstream ref, branch remote, branch
merge ref, or `@{u}` SHA before a normal checkpoint submit or push, stop and
report that the branch changed, the cache is stale, the remote configuration
changed, or the remote baseline moved. Do not consolidate checkpoints or push
until the user confirms the intended baseline. For a post-consolidation recovery
record, defer the baseline decision to its recovery gate: the remote may already
equal the recorded final commit while the cache correctly still records the old
baseline.

## Git Preflight

Run this preflight at the start of every checkpoint, submit, or push workflow.
Treat `@{u}` as the authoritative remote-tracking baseline. Do not infer the
remote by splitting the upstream ref string; resolve it from
`branch.<branch>.remote`.

Resolve and report:

- Current branch full ref from `git -C <repo> symbolic-ref --quiet HEAD`.
- Current branch short name from `git -C <repo> branch --show-current`.
- Upstream ref from
  `git -C <repo> rev-parse --abbrev-ref --symbolic-full-name '@{u}'`.
- Branch remote from `git -C <repo> config --get "branch.<branch>.remote"`.
- Branch merge ref from `git -C <repo> config --get "branch.<branch>.merge"`.
- Upstream SHA from `git -C <repo> rev-parse --verify '@{u}'`.
- Current HEAD SHA from `git -C <repo> rev-parse --verify HEAD`.
- Ahead/behind state from
  `git -C <repo> rev-list --left-right --count HEAD...'@{u}'`.

When the branch remote is not `.`, confirm the named remote exists before a
network fetch or push by reading `git -C <repo> config --get
"remote.<remote>.url"`. A branch remote of `.` is a local upstream and is not a
network push target.

Before changing state, resolve each Git-provided operation path and test whether
it exists. `git rev-parse --git-path` only prints a path; a zero exit status from
that command does not prove that the operation is active.

```bash
for git_state in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD REBASE_HEAD rebase-merge rebase-apply; do
  git_state_path="$(git -C <repo> rev-parse --path-format=absolute --git-path "$git_state")"
  if [ -e "$git_state_path" ]; then
    printf 'Git operation in progress: %s (%s)\n' "$git_state" "$git_state_path" >&2
    exit 1
  fi
done
```

PowerShell equivalent:

```powershell
$gitStates = @('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'REBASE_HEAD', 'rebase-merge', 'rebase-apply')
foreach ($gitState in $gitStates) {
  $gitStatePath = git -C <repo> rev-parse --path-format=absolute --git-path $gitState
  if (Test-Path -LiteralPath $gitStatePath) {
    throw "Git operation in progress: $gitState ($gitStatePath)"
  }
}
```

Stop before checkpoint, submit, or push when:

- `symbolic-ref --quiet HEAD` fails because HEAD is detached.
- `rev-parse --verify HEAD` fails because the branch is unborn.
- `@{u}` cannot be resolved because the branch has no upstream.
- `branch.<branch>.remote` is empty.
- The named remote does not exist in Git config.
- `branch.<branch>.remote` is `.` and the current flow requires a network push.
- Merge, rebase, cherry-pick, or revert state is present.
- The upstream SHA has advanced from the cached baseline before submit or push.
- Ahead/behind shows divergence instead of only local ahead commits.
- Cached branch, upstream ref, or baseline SHA differs from the current
  preflight facts, unless the active record is a post-consolidation recovery
  record and its recovery gate permits the remote state.
- Before submit or push, there are uncommitted intentional changes: staged,
  unstaged, or untracked files that belong to the work being submitted. During
  checkpoint work, report those files first and stage only intentional paths.

## Checkpoint Flow

At the start of an authorized traceable workflow:

1. Resolve the target Git root.
2. Run Git preflight and record branch ref, branch short name, upstream ref,
   remote name, merge ref, upstream SHA, HEAD SHA, and ahead/behind state.
3. Initialize or read the baseline cache and the active checkpoint provenance
   record. Create a new active record only after the user has authorized this
   checkpoint workflow.
4. Stop on detached HEAD, unborn branch, missing upstream, missing remote
   configuration, in-progress Git operation, cache mismatch, or divergence.
5. Report any existing unstaged, staged, or untracked files before changing
   state.

After each completed feature, maintenance slice, or instruction-rule update:

1. Run validation appropriate to the changed surface.
2. Inspect:

```bash
git -C <repo> status --short --branch --untracked-files=all
git -C <repo> diff --stat
git -C <repo> diff --cached --stat
```

3. Stage only intentional files.
4. Create one local checkpoint commit. Include an explicit marker so submit flow
   can perform its secondary marker check:

```text
<type>: <concise checkpoint summary>

Axiom-checkpoint: true
Remote baseline: <upstream> @ <sha>

Scope:
<what changed and why>

Validation:
<commands run and outcomes>
```

5. Verify that `HEAD` is the new checkpoint SHA, then append that exact SHA to
   the active checkpoint provenance record. Stop if the record is missing,
   stale, or cannot be updated.

Do not update the baseline cache after local checkpoints. The cache tracks the
last remote push point, not local progress.

## Submit Flow

When the user asks to submit, publish, or push:

1. Run Git preflight. Stop on detached HEAD, unborn branch, missing upstream,
   empty `branch.<branch>.remote`, missing remote configuration, in-progress
   Git operation, divergence, or uncommitted intentional changes. Defer any
   cache-baseline decision until the active checkpoint record selects normal or
   post-consolidation recovery handling.
2. Resolve the metadata cache path, migrate a matching legacy cache only when
   allowed by the migration rules, then read or initialize the cache. Compare
   cached `branch`, `upstream`, `remote`, `mergeRef`, and `lastRemotePushSha`
   with the current branch short name, upstream ref, branch remote, merge ref,
   and upstream SHA from `@{u}`, but defer rejection until step 5 determines
   whether this is normal or post-consolidation recovery handling.
3. Read the active checkpoint provenance record and select exactly one path:
   - A record without `newCommit` is a normal checkpoint record. Do not adopt
     marker-bearing commits automatically: its recorded ordered SHA list must
     exactly equal the current unpublished commit list before consolidation.
   - A record with `newCommit` is a post-consolidation recovery record. Do not
     create or append checkpoints, apply the normal checkpoint-list equality
     gate, or run consolidation again. Use the recovery path in
     `references/checkpoint-provenance.md`.
4. Fetch when network access is available and the resolved branch remote is not
   `.`:

```bash
git -C <repo> fetch --prune <remote>
```

The `<remote>` value must come from `branch.<branch>.remote`, not from parsing
the upstream ref. If the resolved branch remote is `.`, stop when the current
flow requires a network push.

5. After fetch, select the matching path again:
   - For a normal checkpoint record, rerun the upstream checks: read `@{u}`
     SHA again, recalculate ahead/behind, and recheck cached branch, upstream
     ref, and baseline SHA against the current facts. Stop if upstream
     advanced, the branch diverged, or the cache no longer matches.
   - For a post-consolidation recovery record, validate the remote merge ref
     against its recorded `baselineSha` and `newCommit`. The remote may still
     equal `baselineSha` (retry is permitted) or already equal `newCommit`
     (skip a second push and proceed to verified cleanup); any other value
     stops the flow. Do not reject the latter case merely because the baseline
     cache still records the old remote SHA.
6. For a normal checkpoint record, recheck active checkpoint provenance against
   the refreshed facts and ordered unpublished SHA list. Stop on any mismatch.
7. For a post-consolidation recovery record, validate `HEAD`, parent, tree,
   backup ref, and remote state as required by the reference. If the remote
   still equals `baselineSha`, retry only the recorded `newCommit`; if it
   equals `newCommit`, perform only remote-verification cleanup. Never create a
   second final commit or re-consolidate the checkpoint series.
8. For a normal checkpoint record, run the checkpoint consolidation algorithm
   below. This is the only supported consolidation path.
9. Validate again before push or recovery cleanup.
10. Push only after validation passes and the user explicitly requested it.

## Checkpoint Consolidation

Use Git plumbing so the working tree contents do not change. The only
consolidation path is `commit-tree` plus `update-ref`. Do not use
`git reset --hard`, interactive rebase, checkout-based worktree replacement, or
any alternate history-rewrite flow.

### Preconditions

Before creating any new commit or updating a ref, verify:

- Current `HEAD` is on a normal branch and `branch_ref` is a full ref such as
  `refs/heads/main`.
- `@{u}` exists and resolves to `upstream_sha`.
- `git -C <repo> merge-base --is-ancestor <upstream_sha> HEAD` succeeds.
- Ahead/behind shows only local ahead commits: ahead is greater than zero and
  behind is zero.
- `git -C <repo> rev-list --merges '@{u}'..HEAD` returns no commits.
- `git -C <repo> rev-list --reverse '@{u}'..HEAD` returns the checkpoint commit
  SHA list to consolidate.
- Every unpublished commit in that list belongs to the current authorized
  checkpoint workflow according to the active checkpoint provenance record.
- Every checkpoint commit body contains `Axiom-checkpoint: true`.
- Any old checkpoint, user-created commit, unknown-provenance commit, missing
  checkpoint marker, missing/stale provenance record, or mixed commit stops the
  flow.
- No merge, rebase, cherry-pick, or revert operation is in progress.
- Status has been reported with:

```bash
git -C <repo> status --short --branch --untracked-files=all
git -C <repo> diff --stat
git -C <repo> diff --cached --stat
```

- There are no staged, unstaged, or untracked intentional changes that belong
  to the work being submitted.

Use these checks for the unpublished commits:

```bash
git -C <repo> merge-base --is-ancestor <upstream_sha> HEAD
git -C <repo> rev-list --merges '@{u}'..HEAD
git -C <repo> rev-list --reverse '@{u}'..HEAD
git -C <repo> log --reverse --format='%h %s' '@{u}'..HEAD
git -C <repo> diff --stat '@{u}'..HEAD
git -C <repo> diff --name-status '@{u}'..HEAD
```

### Record State

Before creating the final commit, record:

- `branch_ref`, for example `refs/heads/main`.
- `old_head` from `git -C <repo> rev-parse --verify HEAD`.
- `upstream_sha` from `git -C <repo> rev-parse --verify '@{u}'`.
- `final_tree` from `git -C <repo> rev-parse <old_head>^{tree}`.
- The ordered checkpoint commit SHA list from
  `git -C <repo> rev-list --reverse '@{u}'..HEAD`.
- The active checkpoint provenance record path and workflow id. Its recorded
  ordered checkpoint SHA list must exactly equal the list above.
- Current status summary from `git status --short --branch --untracked-files=all`,
  `git diff --stat`, and `git diff --cached --stat`.
- A unique backup ref such as
  `refs/axiom/backups/traceable-git-submit/<unique-id>`.

Generate `<unique-id>` from the current UTC timestamp plus a short `old_head`
prefix, then verify the ref does not already exist with:

```bash
git -C <repo> show-ref --verify --quiet <backup-ref>
```

If the backup ref already exists, choose a new unique id and check again. The
candidate backup ref is usable only when this command exits nonzero because the
ref is absent.

### Create Backup Ref

Create the backup ref before changing the current branch:

```bash
git -C <repo> update-ref <backup-ref> <old-head>
git -C <repo> rev-parse --verify <backup-ref>
```

The resolved backup ref SHA must equal `old_head`. Stop if backup creation or
verification fails. Do not delete the backup ref before push succeeds and remote
verification confirms the remote ref equals the new final commit.

### Create Final Commit

The final commit must reuse the exact tree from `old_head` and use
`upstream_sha` as its only parent:

```bash
git -C <repo> commit-tree <final-tree> -p <upstream-sha>
```

Provide the commit message on standard input or from a temporary message file.
Use the operating system's native file-writing tool; do not require an extra
repository script.

POSIX example:

```bash
message_file="$(mktemp)"
cat >"$message_file" <<'EOF'
<type>: <final summary>

Remote baseline: <upstream-ref> @ <upstream-sha>

Scope:
<final scope summary>

Validation:
<validation commands and outcomes>

Checkpoint commits:
- <sha> <subject>
EOF
new_commit="$(git -C <repo> commit-tree <final-tree> -p <upstream-sha> <"$message_file")"
```

PowerShell example:

```powershell
$messageFile = New-TemporaryFile
Set-Content -Path $messageFile -Encoding utf8 -Value @'
<type>: <final summary>

Remote baseline: <upstream-ref> @ <upstream-sha>

Scope:
<final scope summary>

Validation:
<validation commands and outcomes>

Checkpoint commits:
- <sha> <subject>
'@
$newCommit = Get-Content -Raw $messageFile | git -C <repo> commit-tree <final-tree> -p <upstream-sha>
```

The final message must be clean and must include `Remote baseline`, `Scope`, and
`Validation`. It should summarize the authorized checkpoint series and should
not carry the `Axiom-checkpoint: true` marker into the final public commit
unless the user explicitly asks for that marker.

### Verify Before Branch Update

Before updating the current branch, verify:

```bash
git -C <repo> rev-parse <new-commit>^
git -C <repo> rev-parse <new-commit>^{tree}
git -C <repo> diff --quiet <old-head>^{tree} <new-commit>^{tree}
git -C <repo> log -1 --format=%B <new-commit>
git -C <repo> rev-parse --verify <branch-ref>
```

Required results:

- `new_commit^` equals `upstream_sha`.
- `new_commit^{tree}` equals `final_tree`.
- The tree diff between `old_head` and `new_commit` is empty.
- The final commit message contains `Remote baseline`, `Scope`, and
  `Validation`.
- `branch_ref` still resolves to `old_head`; the new commit has not already
  moved the current branch.

Stop and keep `backup_ref` if any check fails.

### Atomically Update Current Branch

Update the branch with compare-and-swap semantics:

```bash
git -C <repo> update-ref <branch-ref> <new-commit> <old-head>
```

If `old_head` changed, `update-ref` must fail. Stop, keep `backup_ref`, and do
not overwrite the new branch state.

### Verify After Branch Update

After the branch update, verify:

```bash
git -C <repo> rev-parse --verify HEAD
git -C <repo> rev-parse HEAD^
git -C <repo> rev-parse HEAD^{tree}
git -C <repo> diff --quiet <old-head>^{tree} HEAD^{tree}
git -C <repo> status --short --branch --untracked-files=all
git -C <repo> rev-parse --verify <backup-ref>
```

Required results:

- `HEAD` equals `new_commit`.
- `HEAD^` equals `upstream_sha`.
- `HEAD^{tree}` equals `final_tree`.
- The tree diff between `old_head` and `HEAD` is empty.
- The working tree and index did not gain unexpected changes.
- `backup_ref` still resolves to `old_head`, so the original checkpoint history
  is recoverable.

If post-update verification fails and push has not run, restore the old branch
with compare-and-swap semantics:

```bash
git -C <repo> update-ref <branch-ref> <old-head> <new-commit>
```

Keep `backup_ref` and report the failed verification and restoration result. If
the restore command fails, keep `backup_ref` and report the manual recovery
command.

After post-update verification succeeds, update the active checkpoint provenance
record with `old_head`, `final_tree`, `backup_ref`, and `new_commit`. If a later
push retry resumes after interruption, use that record to validate the existing
consolidated commit and backup ref; do not run a second consolidation.

Write those post-consolidation fields through a temporary sibling file and an
atomic replacement. If that write or replacement fails after `update-ref`
succeeds, treat the state as unsafe: do not push or update the baseline cache.
Immediately attempt to restore the old branch with compare-and-swap semantics:

```bash
git -C <repo> update-ref <branch-ref> <old-head> <new-commit>
git -C <repo> rev-parse --verify <branch-ref>
git -C <repo> rev-parse --verify <backup-ref>
```

The branch and backup ref must both resolve to `old_head`. Keep the backup ref
and the active record regardless of the write outcome, report their paths and
the restoration result, and stop. Do not retry, push, or re-consolidate until a
new explicit recovery assessment resolves the record state.

### Push And Remote Verification

Push only when the user explicitly asked to submit, publish, or push. Use the
resolved branch remote and merge ref from Git preflight:

```bash
git -C <repo> push <remote> <branch-ref>:<merge-ref>
```

After push, verify the remote ref equals `new_commit`. Prefer checking the
remote ref directly, or fetch the resolved remote and re-read `@{u}`:

```bash
git -C <repo> ls-remote <remote> <merge-ref>
git -C <repo> fetch --prune <remote>
git -C <repo> rev-parse --verify '@{u}'
```

Only after remote verification confirms the remote SHA equals `new_commit`:

1. Update the Git metadata baseline cache to the verified new remote SHA.
2. Delete the backup ref with an old-value check:

```bash
git -C <repo> update-ref -d <backup-ref> <old-head>
```

3. Delete the active checkpoint provenance record only after the baseline update
   and backup-ref deletion both succeed. If either step fails, retain the record
   and report its path for recovery or retry.

If push fails, do not report success, do not delete `backup_ref`, and do not
update the baseline cache. Leave the local consolidated commit in place, report
that the original checkpoint history is still available through `backup_ref`,
and report both recovery options:

```bash
git -C <repo> update-ref <branch-ref> <old-head> <new-commit>
git -C <repo> push <remote> <branch-ref>:<merge-ref>
```

If remote verification fails after push, do not delete `backup_ref` or update
the baseline cache. Report the observed remote SHA, the expected `new_commit`,
and the retry or recovery commands.

## Reporting

Report the repository, branch ref, branch short name, upstream ref, remote name,
merge ref, fetched remote when fetch runs, `old_head`, `upstream_sha`,
`final_tree`, ordered checkpoint SHAs, `backup_ref`, `new_commit`, cached
`lastRemotePushSha`, current upstream SHA, current HEAD SHA, ahead/behind state,
active checkpoint provenance path and workflow id, changed files, validation
commands and results, push result, remote verification result, backup ref and
provenance-record deletion or retention, final consolidated commit hash, and
pushed branch when those actions occur. If a step stops, report the exact stop
condition and leave the working tree visible.
