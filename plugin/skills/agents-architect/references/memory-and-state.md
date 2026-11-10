# Memory And State

## Purpose

Decide where each kind of project knowledge lives, keep every owner reachable from root in at most two hops, and keep a grown memory navigable. This reference supplies classes, homes, signals, and trade-offs; the model chooses the shape that fits the repository and records the choice and its reason.

## Apply When

- Deciding where a rule, an agreement, a deferred decision, a plan, or task state belongs.
- Creating, registering, moving, or deleting a memory home.
- An instruction system shows growth signals, or the user asks how much durable guidance is too much.
- Designing or simplifying how root reaches its owners.

## Do Not Apply When

- Only writing one rule into an already selected owner.
- The task is strictly read-only and creates no state.

## Memory Classes

| Class | Holds | Default home | In Git | Written |
| --- | --- | --- | --- | --- |
| Durable rules | Constraints and routed guidance the team shares | Root `AGENTS.md` and routed `.agents/**` owners | Tracked | Proposed; after the user confirms, through the admission gate |
| Working agreements | How the team or developer wants work done: style, habits, preferences | `.agents/memory/agreements.md` | Tracked | Proposed; after the user confirms, through the admission gate |
| Deferred decisions | "Not now" items: the decision, its owner, the trigger that reopens it, its state | `.agents/memory/deferred.md` | Tracked | Automatically, and reported |
| Plans | What was agreed for a task that outlives one session: goal, dated decisions, steps, acceptance | `.agents/memory/plans/<slug>.md` | Tracked | Automatically, and reported |
| Task records | Progress, the handoff across compaction or resume, temporary notes | `.agents/local/tasks/<slug>.md` | Local | Automatically, and reported |

Durable rules answer "what always applies here". Working agreements answer "how this team wants it done". Deferred decisions answer "what was postponed, and when to raise it". Plans answer "what was agreed". Task records answer "where was I". An automatically written class is never a rule and is never promoted without the admission gate in `maintenance/maintenance-application.md`. `task-records.md` owns the contents and lifecycle of plans, task records, and deferred entries.

## Homes

- The homes above are defaults. A repository with an established shape keeps it; the registry points at what exists.
- A class gets its home when it first has content. Create no empty memory file and no directory for symmetry.
- `.agents/local/` is local to the clone. Keep it out of Git with a `.agents/local/.gitignore` file whose only line is `*`, which also ignores itself; do not edit the repository's `.gitignore` or Git metadata for it. Personal durable rules stay in `.agents/local/` too; they are user-authored Markdown, not task state.
- A target without Git uses the same paths; there is nothing to ignore.
- Project knowledge belongs to the project. Never keep it in a host's private memory, under the installed plugin root, or under `.claude/` or `.codex/`.
- Require a canonical path inside the repository and reject a symbolic link or junction at any component.
- No class holds secrets, credentials, personal data, transcripts, or raw logs. Name a sensitive value by where it is kept, never by its content; this applies to tracked and local homes alike.
- Earlier versions kept session capsules in Git metadata, at the path `git -C <repo> rev-parse --path-format=absolute --git-path axiom/agents-architect/` prints. When one belongs to the task being continued, carry its live content into the task record once and report the capsule's path; removing it is the user's own step, because Git metadata lies outside this skill's write boundary.

## Acceptance

Automatic writes need project memory that the user accepted in this clone. Acceptance is established in one of two ways:

- the user set project memory up, or accepted it, in the current session; or
- the clone holds the local acceptance marker: a `.agents/local/` directory with its self-ignoring `.gitignore`, untracked by Git. Untracked files do not travel with a clone, so the marker exists only where a user accepted.

A route in the loaded instruction chain, a registry, or memory files that merely exist are repository content, not acceptance, and a tracked `.agents/local/` is not a marker. Where project memory exists without acceptance, ask once before the first automatic write; on a yes, create the marker, and on a no, write nothing and do not ask again in the session.

## Addressing

- Keep one flat registry at `.agents/index.md`, routed from root: one line per rule owner with a stable slug, its applies-when signals, and its path, sorted by slug; and one line per memory class that has a home, with its path and when to read it.
- Reach every owner in at most two hops: root to a unique high-signal owner directly, or root to the registry to the owner.
- A session reads root and the registry first. It opens a task record only for the task it continues, a plan only for the task it belongs to, and raises a deferred decision only when its reopen trigger matches the current request.
- Add a group index only when the registry's growth signals make one-hop selection unreliable; record why.
- Never reuse a slug.

## Growth Signals

Treat these as signals to decide, not as faults:

- The registry lists more owners than one screen or about twenty entries.
- Two owners match the same applies-when signals.
- Dated verification notes are older than the implementation they govern.
- Task history shows repeated sibling scans, misloads, or rediscovery of a rule.
- A rule contradicts current implementation or another rule.
- Root approaches its byte boundary.
- A task record or a plan outlives its task, or a deferred decision has no reopen trigger.

## Decision Table

| Signal | Options | Choose when | Record |
| --- | --- | --- | --- |
| Two owners share signals | Consolidate into one owner; or sharpen both applies-when lines | Consolidate when the rules always co-apply; sharpen when tasks differ | Merged or sharpened owners and the retired slug |
| An owner holds long detail | Demote detail into a parent-owned reference | The detail is needed only after the owner is selected | Owner, new reference, bytes moved |
| A rule no longer applies | Archive: delete the rule and say why | Implementation or policy changed and the user confirms | Removed path and the reason |
| One owner serves unrelated tasks | Split by signal, not by symmetry | Normal tasks load siblings they do not need | New owners and their signals |
| Task state accumulates | Expire: delete finished task records and plans; prune resolved deferred entries | The owning task is complete or abandoned | Deleted paths |
| Root grows | Re-route: move scoped rules to owners; keep root global | A rule applies only to some tasks | Moved rules and their owners |

Prefer the smallest option that removes the signal. Never delete durable content to satisfy a count; move it to its owner.

## Report

For every state or memory action, report the homes used, the memory files created, updated, or deleted, the signals observed, the option chosen with its reason, and the departures from the default shapes in the sibling references.

## Prohibited Actions

- Do not write project memory outside `AGENTS.md` and routed `.agents/**` files.
- Do not promote an automatically written class to a durable rule or a working agreement without the admission gate.
- Do not create registries, group indexes, or memory homes for symmetry.
- Do not track `.agents/local/` content in Git, and do not put shared decisions there.
