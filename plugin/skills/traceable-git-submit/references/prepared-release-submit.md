# Prepared Release Submission

Own a combined request to commit already-prepared plugin changes, create one exact release tag, and push that branch and tag. This is ordinary release history, not checkpoint consolidation. Read `git-values.md` and the repository, push-identity, and target sections of `remote-targets.md` first; this file owns preparation and the branch and tag updates instead of that file's existing-commit push.

Freeze the exact repository, branch, prepared path set and tree, commit message, tag name, type, and message, version, signing requirements, ordered push targets, destination branch, and the authority for each action. The user's exact combined request may cover all three actions; do not reconfirm unchanged authority, and leave an absent action unperformed. Do not alter versions, release content, other refs, GitHub Releases, marketplaces, or installation state to make this phase pass. When a repository's protected-tag workflow or publication controller owns tag creation, hand that action to its owner instead of pushing a tag past it.

## Freeze Preparation

1. Resolve the root, object format, symbolic `HEAD`, the branch's direct ref and current `oldHead`, upstream and destination identity, index, worktree, and operation state. A detached or unborn `HEAD` or an active operation stops.
2. Inspect the repository's commit and tag signing requirements and release rules before creating anything; stop rather than create an invalid object when required signing or a required controller is unavailable.
3. Require an empty index or one that already matches the authorized path set exactly, stage only those paths, read the staged set back, require exact equality, and freeze its tree with `git write-tree`. Leave unrelated worktree and index state alone; never stash or broaden staging.
4. Validate the tag ref `refs/tags/<name>` with `git check-ref-format` and freeze the tag type, message, and signature policy. Require the local tag absent before the commit exists; a tag already bound to this recorded attempt enters resume instead.
5. Inventory the targets through `remote-targets.md`. For each, bind its branch `liveBaselineSha` as a locally present ancestor of `oldHead` and prove the tag absent with `git ls-remote <push-url> refs/tags/<name>`. An ambiguous query or an unexpected existing tag stops with zero remote writes. Several targets need the user's exact ordered authorization and the acknowledgement that atomicity holds per target, not across the set.

## Construct Local Objects

Create one ordinary commit from the frozen tree and `oldHead` with `git commit-tree`, the message on standard input, and only explicitly authorized signing; verify its parent, tree, message, and signature, then install it with branch compare-and-swap from `oldHead` to `finalSha` using `git update-ref --no-deref <branch-ref> <final-sha> <old-head>`. If the payload is already committed and the frozen tree equals `oldHead^{tree}`, reuse that verified commit as `finalSha` and report that no new commit was needed; never add an empty commit.

Create the tag object with `git tag` as frozen (annotated or signed), or let a lightweight tag name `finalSha` itself; create the ref with `update-ref --no-deref <tag-ref> <tag-oid> <null-oid>` so that an existing tag makes it fail, and verify the direct object and the peeled commit. Never overwrite an existing tag. On a conflicting or uncertain local write, inspect only: reuse an exact previously recorded object or stop and keep the candidate.

## Atomic Branch And Tag Push

Recheck the envelope, object format, `finalSha`, the tag object, the operation state, and the ordered targets immediately before the first push; every remote branch must still equal its baseline and every remote tag must still be absent, or nothing is pushed. For each target in order, push both refs in one atomic update with repository hooks running:

```bash
git -C <repo> push --atomic --no-follow-tags <push-remote> <branch-ref>:<merge-ref> <tag-ref>:<tag-ref>
```

Add `--no-verify` only when the user explicitly authorized bypassing this repository's pre-push hook for this push. If the receiver lacks atomic support, stop; never silently split the update. Stop at the first rejection or unknown response and do not fetch, force, retry, delete, or move a tag to recover.

## Verify And Resume

Read both refs back from every target. Completion requires the branch to equal `finalSha` and the tag's direct object to equal `tagOid` with its peeled commit `finalSha`; a lightweight tag equals `finalSha` directly. Keep the local commit and tag after a partial or unknown outcome. On resume, rebuild the envelope, local objects, per-target baselines, and attempt history from direct state before any new write; unknown attempts enter verification only. Never recreate the commit or tag or repeat a successful target. A separately authorized retry covers only proven unattempted or terminally rejected targets after fresh branch and tag gates. Report each target's two ref states and any retained local objects without claiming a GitHub Release, marketplace, install, or cleanup effect.
