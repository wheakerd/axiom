# Consolidated Commit Construction

## Purpose

Construct and install one final commit from the authorized checkpoint tree
while preserving a recovery ref. Apply the hostile commit metadata boundary in
`safe-git-values-and-metadata.md` before reading subjects or constructing the
message.

## Record State

Before creating the final commit, record:

- `branchRef`, `oldHead`, `upstreamSha`, and `finalTree`.
- The exact ordered authorized SHA list.
- Provenance path and workflow id.
- Current status, unstaged diff, and staged diff summaries.
- `pushTargetState.state == unbound`; consolidation does not resolve endpoints.
- A unique backup ref such as
  `refs/axiom/backups/traceable-git-submit/<unique-id>`.

Capture path-bearing summaries in NUL-safe form and render paths only with
JSON-string, Git C-style, or equivalent reversible escaping.
Apply `safe-git-values-and-metadata.md` to every operand below. The command
blocks show argument order, never a shell interpolation template.

Before backup creation, validate every checkpoint subject and final-message
line through that hostile metadata boundary.

Generate each candidate id from a UTC timestamp plus a short `oldHead` prefix.
Validate its namespace and syntax, but do not probe for absence before create;
only a create-only ref transaction decides whether the candidate is free.

## Create And Verify Backup

Recheck the frozen object format, derive its all-zero `nullOid`, and atomically
create the backup before changing the branch:

```bash
git -C <repo> update-ref --no-deref <backup-ref> <old-head> <null-oid>
git -C <repo> rev-parse --verify <backup-ref>
```

`--no-deref` binds the transaction to the candidate ref itself. The null old
value makes it create-only: it must fail if any ref appeared concurrently. On
a conclusively classified existing-ref compare-and-swap
conflict, generate and validate a fresh candidate and retry; on any other or
uncertain failure, stop. Never fall back to an unconditional `update-ref`.
Require the backup to equal `oldHead`. Keep it through local-only consolidation
and until every later bound target is verified and cleanup proof is persisted.

## Create Final Commit

Reuse the exact tree from `oldHead` and use `upstreamSha` as the only parent:

```bash
git -C <repo> commit-tree <final-tree> -p <upstream-sha>
```

Provide the message through standard input or a permission-restricted native
temporary file. Remove any temporary message file after `commit-tree` completes
or fails. Do not escape unsafe metadata into public history. Assemble only
validated scalar lines with workflow-owned LF separators, hash the exact
bytes, and include `Remote baseline`, `Scope`, `Checkpoints`, and `Validation`.
Do not carry
`Axiom-checkpoint: true` into the final public commit unless explicitly asked.

```text
<type>: <concise final summary>

Remote baseline: <upstream> @ <sha>

Scope:
<consolidated outcome>

Checkpoints:
<ordered checkpoint SHA and subject list>

Validation:
<commands run and outcomes>
```

Never put raw remote URLs, credentials, usernames, private endpoints, or
push-target fingerprints in the public commit message.

## Verify Before Branch Update

```bash
git -C <repo> rev-parse <new-commit>^
git -C <repo> rev-parse <new-commit>^{tree}
git -C <repo> diff --quiet <old-head>^{tree} <new-commit>^{tree}
git -C <repo> rev-parse --verify <branch-ref>
```

Require:

- `newCommit^ == upstreamSha`.
- `newCommit^{tree} == finalTree`.
- The trees of `oldHead` and `newCommit` are identical.
- The exact parsed message bytes and digest equal the frozen input, with the
  required sections and no unsafe metadata or sensitive endpoint data.
- `branchRef` still equals `oldHead`.

Capture and parse the candidate commit object invisibly for the parent, tree,
and message checks; never render its raw body during verification.

Stop and keep the backup on any failure.

## Atomically Update And Verify Branch

```bash
git -C <repo> update-ref --no-deref <branch-ref> <new-commit> <old-head>
```

If `oldHead` changed, the compare-and-swap must fail. After success, verify:

```bash
git -C <repo> rev-parse --verify HEAD
git -C <repo> rev-parse HEAD^
git -C <repo> rev-parse HEAD^{tree}
git -C <repo> diff --quiet <old-head>^{tree} HEAD^{tree}
git -C <repo> status --porcelain=v1 -z --untracked-files=all
git -C <repo> rev-parse --verify <backup-ref>
```

Require `HEAD == newCommit`, `HEAD^ == upstreamSha`, the exact final tree, no
new working-tree or index changes, and `backupRef == oldHead`.

If verification fails before push, restore with compare-and-swap:

```bash
git -C <repo> update-ref --no-deref <branch-ref> <old-head> <new-commit>
```

Keep the backup and report restoration failure with a manual recovery command.

After successful verification, atomically add `oldHead`, `finalTree`,
`backupRef`, and `newCommit` while retaining the exact unbound target state.
If that write fails, do not push or update the cache; follow the
atomic-persistence failure path in `checkpoint-provenance.md`.
