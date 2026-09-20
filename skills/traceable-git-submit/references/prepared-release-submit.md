# Prepared Release Submission

## Scope And Authority

Own a combined request to commit already-prepared plugin changes, create one
exact release tag, and push that branch and tag. This is ordinary release
history, not checkpoint consolidation. Read `safe-git-values-and-metadata.md`,
`network-transport.md`, and the repository, effective push identity, and
ordered-target sections of `repository-and-remote-targets.md` before acting.
This file owns preparation and branch/tag updates instead of that file's
existing-commit-only preflight and one-ref push procedure.

Freeze the exact repository, branch, prepared path set and tree, commit
message, tag name/type/message, version, signing requirements, ordered push
targets, destination branch, and authority for each action. The user's exact
combined request may cover all three; do not reconfirm unchanged authority.
An absent action remains unperformed. Do not alter versions, release content,
other refs, GitHub Releases, marketplaces, or installation state to make this
phase pass. A repository's required publication controller or protected-tag
workflow remains authoritative: if it owns tag creation, hand that action to
its separately authorized owner instead of bypassing it with a direct push.

## Freeze Preparation

1. Resolve the exact root, object format, symbolic HEAD, direct branch ref and
   current `oldHead`, upstream and destination identity, index tree, worktree state,
   and operation state. Detached/unborn state or an active operation stops.
2. Inspect current commit/tag signing, hooks, and release rules before creating
   anything. Apply the non-executable boundary; use a signer or hook only with
   its exact program identity and action authorized. Missing required signing
   or controller support stops preparation rather than creating invalid objects.
3. Freeze the intended NUL-safe path set. An existing index must be empty or
   match that authorized set exactly. Stage only those paths under current
   commit authority, require exact index equality, and freeze its tree. Retain
   unrelated working-tree and index state; never stash or broaden staging.
4. Validate all message/tagger fields as hostile metadata. Require an exact
   full `refs/tags/<name>` passing `git check-ref-format`, with no option-shaped
   component; do not derive authority from a version string alone. Freeze the
   intended tag type and its required signature policy. Require the local tag
   absent before commit creation; an unexpected existing tag stops preparation.
   A tag already bound to this exact recorded attempt enters resume instead.
5. Inventory and authorize all endpoints through the shared target owner. For
   each, bind its own branch `liveBaselineSha`, require a locally available
   commit ancestral to `oldHead`, and prove the exact remote tag absent. An
   ambiguous query or existing unexpected tag stops with zero remote writes.
   Multiple endpoints need the exact ordered authorization and acknowledgement
   that atomicity is per endpoint, not across the whole set.

## Construct Local Objects

Create one ordinary commit from the frozen tree and `oldHead` parent using
`commit-tree`, with the frozen message on standard input and only explicitly
authorized signing. Verify the full resulting commit OID, exact parent, tree,
message and required signature. Install it only through branch compare-and-swap
from `oldHead` to `finalSha`. Verify the branch, index and preserved worktree
state. Never create Axiom checkpoint, baseline or consolidation metadata here.
If the release payload is already committed and the frozen tree equals
`oldHead^{tree}`, reuse that verified commit as `finalSha` under current
authority and report that no new commit was needed; never add an empty commit.

Construct the exact authorized tag object through a literal native argument
API. An annotated tag must name `finalSha`, match its frozen type/message/tagger
and required signature; a lightweight tag's object is `finalSha` itself. Call
the verified full object OID `tagOid`. Create the local tag ref with a create-only
`update-ref --no-deref <tag-ref> <tag-oid> <null-oid>` and verify its direct object
and peeled commit. Never overwrite an existing tag. On a conflict or uncertain
local write, inspect only: reuse an exact previously recorded object under
unchanged authority, or stop and retain the candidate without recreating it.

## Atomic Branch And Tag Push

Immediately before the first push, recheck the full envelope, object format,
source branch `finalSha`, tag object `tagOid` and peeled commit, operation state,
and ordered endpoints. Every remote branch must still equal its own baseline
and every tag must still be absent. One failed gate means zero pushes.

For each frozen endpoint in order, issue one atomic push with exactly the two
validated full-ref refspecs below and the shared network closure. The command
block shows literal argument order, never shell interpolation:

```bash
git -C <repo> push --atomic --no-verify --no-follow-tags --recurse-submodules=no --no-signed --no-push-option --no-set-upstream --no-prune --no-force --no-force-with-lease --no-force-if-includes <push-target> <branch-ref>:<merge-ref> <tag-ref>:<tag-ref>
```

Use `--no-verify` unless the exact frozen pre-push hook was authorized. Apply
the network owner's command-scoped configuration overrides as well as these
options. Tag-object signing is independent of the disabled push certificate.
If the receiver lacks atomic support, stop; never silently split the update.
Stop later endpoints on the first rejection or unknown response. Do not fetch,
force, retry, delete, or move a tag to recover a failed push.

## Verify And Resume

Query both exact refs on every authorized endpoint. Completion requires the
branch to equal `finalSha`, the tag's direct object to equal `tagOid`, and its
peeled commit to equal `finalSha` for an annotated tag. A lightweight tag has no
peeled record and must directly equal `finalSha`. An unexpected extra result,
partial success, or unavailable observation is not completion.

Keep the local commit and tag after partial or unknown outcomes. On resume,
reconstruct the frozen envelope, local objects, per-target baselines and
attempt history from direct state and host task context before any new write.
Unknown attempts enter verification only. Never recreate the commit/tag or
repeat a successful endpoint. A separately authorized retry must cover only
proven unattempted or terminally rejected endpoints, after fresh branch/tag
gates; unresolved acceptance never permits retry. Report each endpoint's two
ref states and retained local objects without claiming any external Release,
marketplace, install or cleanup effect.
