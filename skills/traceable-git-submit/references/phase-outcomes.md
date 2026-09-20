# Phase Outcomes

Read only the outcome paragraph for the selected phase; it grants no new
action authority or permission to load other phase protocols.

For a simple direct push, follow `direct-submit.md` for the exact
named-remote command, normal hooks, one attempt and proportional verification.

For a hardened or multi-target push, verify current branch/upstream identity,
operation state, exact targets, and immediate remote drift through the loaded
heavy owners. Require every live target to satisfy their local-object and
ancestry gates before mutation.

For a checkpoint, require clean staged state, exact adoption of any existing
unpublished commits, current baseline identity, a frozen write set, exact index
equality, a tree-bound verified candidate, branch compare-and-swap, and atomic
provenance append. Preserve concurrent index state. Do not update the cache.

For consolidation, require every unpublished commit to match active provenance,
construct one commit with the exact final tree, update the branch with
compare-and-swap, and persist recoverable state. Without push authority, retain
the backup and active record with push targets `unbound`, and stop locally.

For combined consolidation submission or its recovery, recheck every remote before
push, bind once or require exact existing binding, verify every target and
refreshed upstream, then persist `cleanupReady`. Cleanup requires separate exact
authority. Drift, partial state, or uncertainty retains recovery state.

For a prepared-release submission, use `prepared-release-submit.md`: every
requested branch and tag must match the frozen commit and tag object on each
authorized target. Partial or unknown state retains the local candidate;
never infer a GitHub Release, marketplace publication, or cleanup outcome.
