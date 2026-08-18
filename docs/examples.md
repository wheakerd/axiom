# Examples

These examples show route selection, not claimed execution transcripts. For
each request, higher-priority instructions, repository state, and the user's
actual authorization remain decisive.

## `agents-architect`

| Field | Example |
| --- | --- |
| User request | "Audit this repository's `AGENTS.md` discovery, then split oversized guidance into scoped `.agents/` routes." |
| Expected selected route | `agents-architect` |
| Expected safety boundary | Resolve the repository and active instructions through a read-only metadata inventory first; load only the relevant internal route; keep the change limited to the requested instruction system. |
| Not authorized | Editing unrelated source, mutating host-discovered non-`AGENTS.md` instruction files, crossing into protected plugin metadata, committing, or pushing. |

The route should distinguish active instructions from copied, inactive,
historical, or other-repository material. A discovered instruction candidate is
not automatically writable, and an Axiom route in the installed plugin is not
something to copy into the target repository's `AGENTS.md`.

For implementation reconciliation, use
`effective-instructions:reconcile-preview` for a read-only report or
`effective-instructions:reconcile` for an authorized AGENTS-system update.
These modes compare atomized existing claims with the live working tree through
independent instruction, implementation, and provenance audits. Ordinary AGENTS
maintenance, repository drift, rollback, compaction, or a model or agent handoff
does not activate reconciliation without an explicit user request.

## `optimize-codex-usage`

| Field | Example |
| --- | --- |
| User request | "Reduce the Codex credits and context used by this repository's Skills without weakening validation or safety." |
| Expected selected route | `optimize-codex-usage` |
| Expected safety boundary | Inventory metadata and route chains before reading candidate bodies; use host metrics when exposed and label byte/word/call proxies otherwise; compare the same quality scenarios before and after. |
| Not authorized | Lowering the model or reasoning effort, removing required tests or rollback gates, installing a tokenizer, changing user Skills, committing, pushing, or claiming an exact percentage without repeatable evidence. |

If the implementation also changes a target repository's `AGENTS.md` system,
add `agents-architect` only for that authorized instruction surface. A plain
AGENTS audit still selects only `agents-architect`, and ordinary software
performance work does not select this route.

## `review-axiom-task`

| Field | Example |
| --- | --- |
| User request | "Explain the routing, authorization, actions, and evidence for this Axiom-guided task." |
| Expected selected route | `review-axiom-task` |
| Expected safety boundary | Freeze the review window at the request, inspect only scoped host-visible evidence, separate Axiom guidance from host-agent actions, and label material claims as observed, reconstructed, or unavailable. |
| Not authorized | Rerunning the task, opening unrelated tasks or targets, accessing credentials, editing files, committing, pushing, deploying, changing configuration, or creating persistent trace data. |

The report may use current read-only state to verify an outcome when that target
is already in scope. Current state does not prove past authorization, causation,
or which instructions were active. If compaction or host limits hide required
history, the report remains partial rather than inventing a complete trace.

## `traceable-git-submit`

| Field | Example |
| --- | --- |
| User request | "Create local checkpoint commits for `README.md` and `docs/`, preserve every other path, and do not push." |
| Expected selected route | `traceable-git-submit` |
| Expected safety boundary | Resolve one exact Git root, freeze the authorized paths, compare the entire index with that set, and record exact checkpoint provenance before treating commits as workflow-owned. |
| Not authorized | Staging unrelated work, adopting or rewriting unclear commits, pushing, changing another remote target, or deleting recovery metadata. |

Here the user's wording authorizes local checkpoint commits for a bounded path
set and explicitly withholds push authority. The route selection itself grants
neither permission. A later consolidation and a later push are separate
requests; neither can be inferred from the other.

A distinct routed request is: "Consolidate the authorized checkpoint series
into one final local commit, and do not push." It authorizes local
consolidation only. The workflow retains recoverable post-consolidation state
until a later explicit push or recovery request completes remote verification
and cleanup.

"Push the current branch without rewriting history" also selects this route,
but only its direct-submit phase. It resolves and verifies every push target,
does not create Axiom cache or provenance metadata, and does not authorize
checkpoint creation or consolidation.

## `reversible-system-change`

| Field | Example |
| --- | --- |
| User request | "Prepare a read-only migration plan for the staging database, including rollback evidence and promotion gates. Do not download or change anything." |
| Expected selected route | `reversible-system-change` |
| Expected safety boundary | Identify the exact target and intended persistent effects through metadata-only observation; distinguish rollback material that exists from a restore path that is currently validated or safely rehearsed. |
| Not authorized | Reading secret contents, downloading a candidate, creating rollback artifacts, writing local or remote state, restarting a service, migrating data, or promoting a candidate. |

A plan or rehearsal request routes because the proposed operation has persistent
change and rollback risk, but the plan-only contract remains read-only. If the
user later authorizes execution, candidate preparation, promotion, destructive
retention, sensitive asset use, and rollback are still separate boundaries.

## Requests That Should Not Route

| User request | Expected behavior | Why no Axiom route applies |
| --- | --- | --- |
| "Fix the typo in `README.md`." | Continue normally | An ordinary source or documentation edit is not an Axiom workflow |
| "What version of the service is running?" | Continue normally | A pure read-only status query does not plan a persistent change |
| "Explain what a rollback is." | Continue normally | A conceptual explanation has no concrete persistent target |
| "Refactor this parser and run its unit tests." | Continue normally | Ordinary code and repository-local testing are outside Axiom's focused routes |
| "Commit the current changes with a multi-paragraph English message." | Continue normally | An ordinary local commit does not request checkpoint provenance or consolidation |
| "Make this algorithm use less memory." | Continue normally | Software runtime performance is not Codex usage optimization |
| "Summarize what changed in this coding task." | Continue normally | An ordinary task summary is not an explicit review of an Axiom-guided task |

No-route does not certify that a task is risk-free, and it does not relax any
host, repository, or user instruction. It means only that the request does not
clearly match a bundled Axiom workflow.

## Ambiguous Requests

If wording could map to more than one workflow and the choice would change
execution, the routing gate calls for one concise clarification question. It
does not load every possible skill as a precaution. Once the intent is clear,
the smallest matching skill set is selected.

If "submit" or "push" could mean preserving current history or consolidating
an active checkpoint series, ask once which history outcome is intended. Do
not inspect or mutate Git state before that choice is clear.

See [Architecture](architecture.md) for the route sequence and
[Trust Model](trust-model.md) for authority and mutation boundaries.
