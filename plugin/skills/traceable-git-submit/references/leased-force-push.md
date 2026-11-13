# Leased Force Push

Replace the remote history of one branch with one push that the remote accepts only while its tip is still the one the user was shown. Load this file only for an explicit request to force-push, or to replace the remote history of, one branch; no other phase of this skill force-pushes. Read `git-values.md` first. This phase creates no checkpoint, baseline, or consolidation metadata.

## Authority

The user's current statement covers the repository, the remote, the one branch, the replacement commit, and that the branch's remote history is to be replaced. General push authority, an earlier force grant, a request to sync or repair the remote, and a permission-bypass mode are not that authority. One grant covers one attempt on one frozen envelope, and selecting this phase grants nothing.

"This branch" can name the current branch, with one exception: the remote's default branch is in scope only when the user's statement contains that branch's own name as the branch whose remote history is replaced. Read the default branch with `git -C <repo> ls-remote --symref <target> HEAD`; when the remote does not report it, say so and apply the exception to the branch at hand. Server-side branch protection stays the remote's decision.

Stop before any write for a tag, a wildcard or deleting refspec, more than one branch, a detached or unborn `HEAD`, an operation in progress, or a replacement commit that is not the branch's current local tip. Stop as well when the remote argument resolves as a remote group (`remotes.<name>`), including a group that shadows a configured remote of the same name (Git then starts a push for each member of the group and may fail to reach a shadowed remote), and on a nonempty effective `push.pushOption` list, `remote.<name>.mirror=true`, or a nonempty inherited `GIT_NAMESPACE`, each of which changes what the remote receives. Deleting a remote branch is not part of this phase.

## Several Push Destinations

List the destinations as `remote-targets.md` describes. One destination proceeds. Several are the user's decision, because they are usually a primary repository and a backup, and only the user knows what the backup is for. When the user has already said how the destinations are to be treated, including whether the backup must receive the push for the work to count as done, follow that statement and do not ask again. Otherwise it is an open decision: say what you observed, name the workable ways with the consequence of each, recommend one, and ask once before any write. The ways are the first destination only, each destination in a stated order, and a stop that leaves the push to the user. A destination that is not rewritten keeps the old history, so later ordinary pushes to it will be rejected. Every destination that is rewritten gets its own live read, backup ref, lease, and read-back, and the first failure stops the sequence.

## Show What Is Replaced

1. Resolve and freeze the repository root, the branch ref, the replacement commit `newSha`, the remote, and `mergeRef`.
2. Read the live tip with one query, `git -C <repo> ls-remote --symref <target> <merge-ref>`, naming `<target>` as `git-values.md` says. Require one object line and record it as `liveSha`. A `ref:` line means the branch is symbolic on the remote and the update would land on another ref: stop. An older protocol prints that line only for `HEAD`, so also stop when a branch that is not the default one has the tip the `HEAD` query printed. No result means there is no remote history to replace: stop, because that is an ordinary push.
3. When `liveSha` is present locally and `git -C <repo> merge-base --is-ancestor <live-sha> <new-sha>` succeeds, stop: an ordinary push suffices and this phase is not needed.
4. When `liveSha` is present locally, show the commits that would be discarded, `git -C <repo> log --format='%h %s' <new-sha>..<live-sha>`, as a count and escaped subjects. When it is not present, say that the content can be neither shown nor backed up without a fetch, and offer the exact refresh below.
5. A backup holds only what is local, and the checks must see the real history. Stop in a shallow repository, where `git -C <repo> rev-parse --is-shallow-repository` prints `true`; in a partial clone, where `git -C <repo> config --get-regexp '^(extensions\.partialclone|remote\..*\.(promisor|partialclonefilter))$'` prints a line; when objects are borrowed, where the file at `git -C <repo> rev-parse --git-path objects/info/alternates` is not empty or `GIT_ALTERNATE_OBJECT_DIRECTORIES` is set; and when a grafts file exists at `git -C <repo> rev-parse --git-path info/grafts`. Then require `git -C <repo> rev-list --quiet --objects <new-sha>..<live-sha>` to succeed; it fails when a discarded object is missing. Run it and the commands of steps 3 and 4 as `git --no-replace-objects`, so that a replace ref cannot hide what is discarded.

## Exact Refresh Of The Live Tip

Only with the user's refresh authority, which push authority never includes, fetch that one ref without moving any configured ref, and require `FETCH_HEAD` to equal `liveSha`:

```bash
git -C <repo> fetch --no-tags --no-recurse-submodules --refmap= <target> <merge-ref>
git -C <repo> rev-parse --verify FETCH_HEAD
```

Name `<target>` as for the query. A matching result returns to step 3, so the ancestry test, the discarded commits, and the completeness check all run before the backup. A different result means the remote moved: return to step 2 and show the user the new tip before going on. Without refresh authority, stop and keep the envelope.

## Backup, Push, And Read-Back

Create the backup before the push with a create-only update, so that an existing ref makes it fail instead of being overwritten:

```bash
git -C <repo> update-ref --no-deref refs/axiom/backups/traceable-git-submit/<unique-id> <live-sha> <null-oid>
```

Immediately before the push, recheck the envelope, the branch ref against `newSha`, the operation state, the destinations, and every stop of the Authority section. Then push once, with repository hooks running, submodule pushes off, the lease bound to the tip the user saw, and the replacement named by its object ID, so that a branch that moves in the meantime cannot change what is sent:

```bash
git -C <repo> push --no-follow-tags --recurse-submodules=no --force-with-lease=<merge-ref>:<live-sha> <target> <new-sha>:<merge-ref>
```

Never use a bare `--force`, a `+` refspec, or a lease without the explicit expected value: a background fetch defeats the lease that reads the tracking ref, and `--force-if-includes` has no effect once the expected value is explicit. Add `--no-verify` only under invariant 2. A lease rejection means the remote moved after the user saw it: stop, and show the new tip only on a new request. A hook failure, a protection rejection, or an uncertain result also ends the attempt. Never retry, fetch and retry, or switch to another form of force.

Read the target back with the same query. Completion requires the result to equal `newSha`. After an uncertain push result, query only and report what the remote holds.

## Report, Recovery, And Cleanup

Report the remote by name, the branch, `liveSha`, `newSha`, the number of discarded commits, the backup ref, and the read-back result. Give the command that would restore the old tip, `git -C <repo> push --no-follow-tags --recurse-submodules=no --force-with-lease=<merge-ref>:<new-sha> <target> <live-sha>:<merge-ref>`, and say that it is itself a force push that needs its own authority.

Keep the backup ref until the read-back equals `newSha` on every destination selected for rewriting; a partial, rejected, or unknown outcome keeps every backup. Deleting it after that needs separate exact authority that names the repository, the ref, and its commit. Delete it with a compare-and-swap, `git -C <repo> update-ref --no-deref -d <backup-ref> <live-sha>`, and verify that it is gone.

After resume or compaction, mutate nothing until the envelope, the user's authority, the backup ref, and the remote's current tip are reconstructed from direct evidence. A push whose result is unknown is verified by a query and never repeated.
