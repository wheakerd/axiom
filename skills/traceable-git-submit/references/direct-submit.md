# Direct Submit

## Purpose

Perform one explicitly invoked, ordinary named-remote, one-branch, non-force
Git push through the repository's normal Git mechanism. Keep this path
host-native and proportional. It owns no checkpoint, provenance, consolidation,
raw-target, multi-target, recovery, force, fetch, or retry workflow.

## Scope

Enter when the user explicitly invokes `$traceable-git-submit` for one
named-remote branch push that preserves history. Also enter for the specialized
live-baseline constraint only when the request jointly states that the local
tracking ref is stale and the verified live remote tip is an ancestor of the
final commit. Mere stale-tracking mention does not select this owner. Freeze the
exact repository, current branch, configured remote name, destination branch,
final commit, payload, and non-force policy. Require one branch and one
configured push destination. A missing or unknown remote, detached or unborn
branch, in-progress Git operation, multiple push destinations, wildcard or
deleting refspec, force, tag widening, or unresolved identity stops before
mutation.

An ordinary commit-and-push request that does not explicitly invoke this Skill
stays in the host's normal workflow. If the combined request has an already
visible material conflict among the requested command, repository guidance,
remote, branch, payload, target count, or force policy, resolve it before
creating the commit. An expected staged set that exactly matches the authorized
payload is normal state, not a conflict; extra or unknown staged paths stop.
Ask one concise question only when user input is required. Do not ask again when
the frozen actor, repository, remote, branch, payload, and force policy are
unchanged.

## Pre-Commit Conflict Gate

For a combined commit-and-push request, finish the preceding conflict check
before the commit. An unresolved predictable conflict leaves `HEAD` unchanged.

## Effective Configuration Before Every Push

Inspect effective configuration immediately before every direct push, including
push-only requests. For a combined request, also inspect it before the commit;
the pre-push inspection checks for drift. Use the same repository and execution
environment as the requested command, including applicable conditional,
worktree, environment, and command-scope configuration. Stop on
`push.followTags=true`, a nonempty effective `push.pushOption` list, or
`remote.<name>.mirror=true`. Evaluate `push.recurseSubmodules` and
`submodule.recurse` jointly in Git's configuration traversal order for the
executing environment. The last entry of either key decides the mode:
`push.recurseSubmodules` supplies its mode; `submodule.recurse=true` supplies
`on-demand`, and `submodule.recurse=false` supplies `no`. Stop when the resulting
mode is `on-demand` or `only`. Modes `no` and `check` are safe only when they
remain the final mode. Respect Git
boolean parsing and ordered multi-value empty-reset semantics; key presence
alone is insufficient. Absent settings use Git defaults. Distinguish absence
from an inspection or parse error; malformed, unreadable, conflicting, or unclassifiable evidence
stops. A conflict is a stop: never add flags, change configuration, import the
heavy transport closure, or silently switch workflows. Preserve the exact
command, normal hooks, signing policy, endpoint privacy, and one-attempt
boundary. Retain only the conflicting key and effect category, never
push-option payloads or endpoint values.

At both inspections, resolve the command's source-only refspec under the
executing Git version's effective mapping rules, including the first matching
`remote.<name>.push` refspec and, where applicable, `push.default=upstream` with
`branch.<name>.remote` and `branch.<name>.merge`. Stop if the effective refspec
is forced (leading `+`) or its destination differs from the frozen destination
branch. Also stop if the named remote argument resolves as a remote group
(`remotes.<name>`), including a group that shadows a configured remote of the
same name; never invoke group members. Unresolved mapping or group status is
unclassifiable evidence and stops.

At both inspections, stop on a nonempty inherited `GIT_NAMESPACE` or when its
propagation to the receiving side is unclassifiable; never clear or override it.
Any other effective setting or inherited environment that would change the
exact command's refs, destinations, remotes, force, tags, submodules, or push
options is also a conflict and stops.

## Preserve The Named-Remote Mechanism

Honor the exact user- or repository-specified named-remote command as a literal
argument vector. For example, a request for `git push origin main` remains that
command. Do not replace the remote name with an endpoint, derive or persist a
target fingerprint, substitute a raw URL, create an execution wrapper or
generated Git runner, or add a different refspec or option.

Keep normal repository pre-push hooks active. Never add `--no-verify`. Treat an
existing hook or repository-owned Git behavior as part of the selected normal
mechanism; if current instructions reveal a material conflict or unauthorized
effect, stop before any commit or push rather than bypassing it.

Re-resolve the exact repository, branch, named remote, destination branch,
operation state, and target count immediately before the push. Resolve the
configured named remote to exactly one destination and compare endpoint
equality only ephemerally to prove that destination is unchanged. This is not
heavy configuration closure: never display, fingerprint, retain, substitute,
or pass the endpoint as the command target, and never create a wrapper. A
changed, missing, extra, or unclassifiable destination stops with zero pushes.

## One Native Push

Push exactly once with the exact named-remote command. Do not automatically fetch, update a
tracking ref separately, set an upstream, force, retry, prune, follow or add
tags, add push options, widen refs or targets, rewrite history, or start another
push after an uncertain result.

A stale local remote-tracking ref is informational and does not block the
attempt. Normal Git negotiates against the live remote and enforces the
non-force fast-forward. A definite non-fast-forward, unknown-target, hook,
authentication, transport, or other Git rejection is terminal for this phase.

## Proportional Completion

Use the normal Git result and any normal tracking update as primary completion
evidence. Make no query when the Git result is conclusive.
If and only if the result is materially ambiguous about whether the remote
accepted the update, make at most one owning-remote query for the exact
destination branch. Accept success only when that one result equals the frozen
final commit. Otherwise report failure or unknown as observed and do not retry.

Retain no endpoint, credential, command output, wrapper, generated runner, or
auxiliary tracking mutation. Report the selected simple phase, repository and
branch identity, named remote, exact push count, Git result, whether the sole
conditional query was needed, and the final evidence classification.

## Stop Conditions

Stop before mutation for an unknown or changed target, multiple destinations,
force or widened refs, unresolved mechanism conflict, or in-progress operation.
Stop after the one attempt for divergence, hook or Git failure, ambiguous
verification, or drift. Fetch, retry, force, multi-target submission,
checkpoint publication, consolidation, and recovery require their separately
selected owners and authority.
