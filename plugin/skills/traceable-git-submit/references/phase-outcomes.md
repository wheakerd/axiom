# Phase Outcomes

Read only the outcome paragraph for the selected phase; it grants no new action authority or permission to load other phase references.

For a simple direct push, follow `direct-submit.md`: the exact named-remote command, normal hooks, one attempt, and proportional verification.

For a hardened or multi-target push, verify the current branch and upstream identity, the operation state, the exact targets, and immediate remote drift through `remote-targets.md`. Every live target must satisfy its local-object and ancestry gates before mutation, and every target is read back afterwards.

For a checkpoint, require a clean index, exact adoption of any existing unpublished commits, current baseline identity, a frozen write set, exact index equality, a tree-bound verified candidate, branch compare-and-swap, and an atomic record append. Preserve concurrent index state. Do not update the cache.

For consolidation, require every unpublished commit to match the active record, a backup ref created before the branch moves, one commit with the exact final tree, a branch update by compare-and-swap, and persisted recovery state. Without push authority, retain the backup and the record with `pushRemote` unset and stop locally.

For combined consolidation submission or its recovery, recheck every target before the push, bind the push remote once, verify every target and the refreshed upstream, then persist `cleanupReady`. Cleanup requires separate exact authority. Drift, partial state, or uncertainty retains the recovery state.

For a prepared-release submission, use `prepared-release-submit.md`: every requested branch and tag must match the frozen commit and tag object on each authorized target. Partial or unknown state retains the local candidate; never infer a GitHub Release, marketplace publication, or cleanup outcome.
