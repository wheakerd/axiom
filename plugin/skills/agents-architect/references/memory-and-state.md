# Memory And State

## Purpose

Decide where instruction memory and task state live, keep a grown instruction
memory navigable, and address every durable owner in at most two hops. This
reference supplies options, signals, and trade-offs; the model chooses the
shape that fits the repository and records the choice and its reason.

## Apply When

- Creating, moving, or deleting task state such as a runtime capsule or a
  generated inventory.
- An instruction system shows growth signals, or the user asks how much
  durable guidance is too much.
- Designing or simplifying how root reaches its owners.

## Do Not Apply When

- Only writing one rule into an already selected owner.
- The task is strictly read-only and creates no state.

## Memory Tiers

| Tier | Holds | Lives in | Lifetime |
| --- | --- | --- | --- |
| Durable rules | Constraints and routed guidance the team shares | Root `AGENTS.md` and routed `.agents/**` owners, tracked by Git | Until superseded through the admission gate |
| Decision ledger | Dated project decisions with status | `.agents/decisions.md`, tracked, append-only | Permanent; entries change status, never disappear |
| Task state | Capsules, inventories, migration tables, scratch | Git metadata resolved below; never under `.agents/` | One task; deleted or marked obsolete at completion |

Durable rules answer "what always applies here". The ledger answers "why" and
"since when". Task state answers "where was I"; it is never a rule and never
promoted without the admission gate.

## Task State Location

Resolve the state directory from the target repository's Git metadata, never by
hand:

```bash
git -C <repo> rev-parse --path-format=absolute --git-path axiom/agents-architect/
```

Write capsules as `session-<unique-id>.md` and generated material under that
directory. The path stays outside the working tree, so IDE indexers, code
search, and `git status` never see it, `.gitignore` is not involved, and a
linked worktree whose `.git` is a file resolves correctly. Require an absolute
canonical path, reject a symbolic link or junction at any component, and never
place state under the installed plugin root or under `.agents/`, `.claude/`, or
`.codex/` inside the repository.

Earlier Axiom versions wrote `.agents/.runtime/` and `.agents/.generated/`.
Treat leftovers as migration candidates: delete obsolete capsules, move
anything still needed to the resolved directory, and report both.

For a target without Git metadata, use the host's session scratch directory
when the host provides one; otherwise ask the user for a directory outside the
indexed tree. Record the chosen location in the report.

Personal durable rules stay in `.agents/local/`, listed in `.git/info/exclude`.
They are user-authored Markdown, not task state.

## Capsule Contract

Create a capsule only for a mutating, long-running AGENTS task that risks
losing critical state, never for a read-only task. Target under 2 KiB and keep
under 4 KiB. Contents: current goal, confirmed scope, active instruction files,
critical constraints, modified files, completed and failed validation with a
brief reason, open decisions, next action. Exclude transcripts, long logs,
large code, whole-document summaries, guesses, secrets, and personal data.
Delete or mark the capsule obsolete when the task completes; a later session
reads a capsule only when the user or the task record points at it.

## Growth Signals

Treat these as signals to decide, not as faults:

- The registry lists more owners than one screen or about twenty entries.
- Two owners match the same applies-when signals.
- `last_verified` dates are older than the current implementation they govern.
- Task history shows repeated sibling scans, misloads, or rediscovery of a rule.
- A rule contradicts current implementation or another rule.
- Root approaches its byte boundary.
- Capsules outlive their task.

## Decision Table

| Signal | Options | Choose when | Record |
| --- | --- | --- | --- |
| Two owners share signals | Consolidate into one owner; or sharpen both applies-when lines | Consolidate when the rules always co-apply; sharpen when tasks differ | Merged or sharpened owners and the retired slug |
| An owner holds long detail | Demote detail into a parent-owned reference | The detail is needed only after the owner is selected | Owner, new reference, bytes moved |
| A rule no longer applies | Archive: mark the ledger entry `retired` and delete the rule | Implementation or policy changed and the user confirms | Ledger entry, removed path |
| One owner serves unrelated tasks | Split by signal, not by symmetry | Normal tasks load siblings they do not need | New owners and their signals |
| Task state accumulates | Expire: delete obsolete capsules and generated files | The owning task is complete or abandoned | Deleted paths |
| Root grows | Re-route: move scoped rules to owners; keep root global | A rule applies only to some tasks | Moved rules and their owners |

Prefer the smallest option that removes the signal. Never delete durable
content to satisfy a count; move it to its owner or the ledger.

## Addressing

- Keep one flat registry at `.agents/index.md`: one line per owner with a
  stable slug, its applies-when signals, and its path, sorted by slug.
- Reach every owner in at most two hops: root to a unique high-signal owner
  directly, or root to the registry to the owner.
- Add a group index only when the registry's growth signals make one-hop
  selection unreliable; record why.
- Never reuse a slug. A retired slug keeps its ledger entry with status.
- Each registry line names the ledger entry its rule derives from when one
  exists.

## Decision Ledger

`.agents/decisions.md` holds one line per decision: date, slug, decision,
status (`accepted`, `superseded`, or `retired`), and the slug it supersedes.
Append only; change status instead of rewriting history. Create the ledger when
the first decision needs a durable "why"; do not create it for symmetry.

## Report

For every state or memory action, report the resolved state directory, created
or deleted task-state files, the signals observed, the option chosen with its
reason, and the departures from the default shapes in the sibling references.

## Prohibited Actions

- Do not write task state under `.agents/`, `.claude/`, `.codex/`, or the
  installed plugin root.
- Do not promote capsule or generated content to durable rules without the
  admission gate.
- Do not create registries, ledgers, or group indexes for symmetry.
- Do not hand-build `.git/axiom/...`; resolve the path through Git.
