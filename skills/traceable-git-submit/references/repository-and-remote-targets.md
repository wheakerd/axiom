# Repository And Remote Targets

## Purpose

Resolve one exact Git root and independently freeze the upstream baseline,
effective push remote, and every endpoint it can update without leaking
secrets. Simple named-remote submission belongs to `direct-submit.md`, not this
heavy owner.

## Exact Repository Root

Resolve the user's explicit path or scoped files before the session directory:

```bash
git -C <candidate> rev-parse --show-toplevel
git -C <candidate> rev-parse --path-format=absolute --git-common-dir
```

Canonicalize both results and resolve every intended path's owning Git root.
Stop if a path is outside the root, paths span repositories/worktrees, a
parent or nested repository is ambiguous, or an explicit path conflicts with
the session directory. Report the root and common directory with reversible
escaping; a linked worktree is valid when Git resolves both identities.

## Hardened Direct Submit Preflight

For a history-preserving submit, freeze object format, symbolic branch,
upstream display/full tracking ref, `upstreamRemote`, `mergeRef`, `HEAD`,
upstream OID, local divergence, and operation-state paths. Resolve `pushRemote`
under the next section. Use current Git facts, not Axiom cache or provenance,
and recheck object format before network access. Record the tracking OID and
local divergence as informational state for this phase; neither owns the live
network baseline.

Stop on detached/unborn `HEAD`, missing upstream or push identity, a local-only
push remote, or an in-progress operation. Do not stop solely because the local
tracking ref is stale, missing an object already identified by the live target,
or reports behind/diverged state. Set `finalSha` to current `HEAD`; bind
`liveBaselineSha` only from the verified live target under the next gates.
Uncommitted work is excluded: never stage, stash, clean, commit, or require a
clean worktree merely to push existing commits. Never force-push on this route.

## Effective Push Identity

`upstreamRemote` comes only from `branch.<branch>.remote` and owns `@{u}` and
refresh. Resolve effective `pushRemote` independently in this order:

1. a configured remote explicitly named in the current request;
2. `branch.<branch>.pushRemote` when present;
3. `remote.pushDefault` when present;
4. current `upstreamRemote`.

Capture configuration invisibly through `safe-git-values-and-metadata.md`.
Only an absent key falls through. An empty, duplicate, malformed,
option-shaped, `.` or non-enumerated selected value stops. A raw URL is not a
configured remote name and must not be reinterpreted or persisted.

Freeze `pushRemote`, resolution source, `mergeRef`, branch, and upstream
identity separately; re-resolve them before inventory and before push. A
changed remote or ref is drift. Refresh still uses `upstreamRemote`. If a
configuration fallback selects `pushRemote != upstreamRemote` and the user did
not name it, report only validated remote names and target fingerprints and
obtain exact destination confirmation before push or provenance binding.

## Network Semantic And Transport Closure

First apply the generic semantic closure in `safe-git-values-and-metadata.md`.
For an authorized refresh or push, also close the network-specific effects
below; stop if any cannot be disabled or separately authorized.

Refresh uses one exact source-only refspec and empty `--refmap`, never
`remote.<name>.fetch`; fetch objects before compare-and-swap update of the sole
tracking ref. Keep tags, prune/tag-prune, submodules, `FETCH_HEAD`, maintenance,
and commit-graph writes off. Broad prune needs separate authority. Reject
`fetch.bundleURI` and other implicit endpoints.

Push uses one frozen raw target and exact full-ref refspec. Neutralize
`push.followTags`, recurse, signing, push options, negotiation, upstream setup,
prune, and force. Bypass pre-push hooks unless their exact frozen identity and
action are separately authorized.

Classify endpoints without display. Allow authenticated `https://`, `ssh://`,
`git+ssh://`, and standard SCP-like SSH. Reject plaintext `http://`/`git://`,
network `file://` or local paths, controls, `<helper>::<address>`, and `ext::`.
At command scope set `protocol.allow=never`, enable only the classified HTTPS
or SSH protocol, and keep `protocol.ext.allow` disabled. Contain enumeration,
hashing, queries, errors, and debugging; emit only fingerprints, validated
refs/OIDs, and sanitized status.

## Target Inventory And Authorization

Apply only to push or post-consolidation recovery. Checkpoint-only work may use
local `upstreamRemote == .` and never loads target inventory.

```bash
git -C <repo> remote get-url --push --all <push-remote>
```

Run this endpoint-producing command only inside a non-visible literal-argument
capture. Validate transports, collapse byte-identical values in first-seen
order, and derive for each target an ordinal, full-value cryptographic
fingerprint, `mergeRef`, and expected baseline/final OIDs. Keep raw values only
in memory or a protected temporary file, then remove them. Never persist them.

- Zero targets stops with zero pushes.
- One target may proceed under an explicit submit, publish, or push request.
- Multiple targets require authorization of the exact ordered fingerprints and
  acknowledgement that sequential pushes can leave partial remote state.
- Any identity, order, count, fingerprint, or ref change invalidates authority.

Direct push identity remains in memory. A consolidated record binds only under
`post-consolidation-recovery.md`; never select a subset from a multi-target
remote.

For a direct push, query the sole target's exact `mergeRef` after inventory.
Require exactly one full OID, require that object to exist locally as a commit,
and require `git merge-base --is-ancestor <live-baseline-sha> <final-sha>` to
succeed. Bind that OID as `liveBaselineSha`. Missing, unreadable, non-local,
non-commit, or non-ancestor live state stops without fetch, tracking-ref
mutation, push, or retry. The local tracking OID remains informational and is
never compared with `liveBaselineSha` as a permission gate.

## Immediate Drift Gate

Immediately before the first push, re-resolve push identity, re-enumerate
targets, and require exact equality with frozen or bound fields. Recheck
operation state and the direct branch ref. Query every target's `mergeRef`;
require exactly one result equal to the bound `liveBaselineSha` from each before
issuing any push. Missing, unreadable, changed, moved, non-local, non-commit, or
non-ancestor state means zero pushes. Report only ordinal/fingerprint, escaped
ref, and expected/observed OID.

## Push And Verification

Push each raw frozen target separately in authorized order with one exact ref
update:

```bash
git -C <repo> -c push.followTags=false -c push.recurseSubmodules=no -c push.gpgSign=false -c push.pushOption= -c push.negotiate=false -c push.autoSetupRemote=false push --no-verify --no-follow-tags --recurse-submodules=no --no-signed --no-push-option --no-set-upstream --no-prune --no-force --no-force-with-lease --no-force-if-includes <push-target> <branch-ref>:<merge-ref>
```

`--no-verify` is mandatory unless the exact frozen pre-push hook identity and
action are separately authorized. Stop later pushes on first failure, then
query every authorized target. Completion requires every `mergeRef` to equal
`finalSha` or post-consolidation `newCommit`; one push exit status, fetch, or
tracking-ref update is insufficient.

On disagreement, retain backup/provenance state, do not update baseline, and
do not retry automatically. Push authority never grants fetch; report `@{u}`
unrefreshed unless separately refreshed. A direct push neither requires nor
separately mutates its tracking ref and creates no Axiom metadata.

## Sensitive Reporting

Never expose raw URLs, credentials, usernames, private hosts/IPs, filesystem
endpoints, or internal paths. Reports use the canonical root, validated remote
name, target ordinal/fingerprint, escaped ref, and expected/observed OIDs. If
sanitization cannot be guaranteed, report only target verification failure.

## References

- `safe-git-values-and-metadata.md`
- `post-consolidation-recovery.md`
