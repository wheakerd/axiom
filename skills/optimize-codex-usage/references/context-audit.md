# Codex Context Audit

Use this reference for a scoped consumption audit or implementation. It is a
measurement method, not a claim that Axiom can inspect hidden host accounting.

## Contents

- [Baseline](#baseline)
- [Route chains](#route-chains)
- [Candidate analysis](#candidate-analysis)
- [Implementation](#implementation)
- [Scenario validation](#scenario-validation)

## Baseline

Resolve the target repository and preserve its current worktree before edits.
Start with metadata rather than recursive document reads:

- Public Skill names, descriptions, paths, bytes, words, and lines.
- Always-loaded hooks or routing gates and applicable `AGENTS.md` files.
- Direct reference edges, broken links, cycles, and references not directly
  discoverable from their owning `SKILL.md`.
- MCP server and tool-description counts without contacting servers or reading
  credentials.
- Available host-reported usage plus conversation, file, history, tool-result,
  and output sizes when exposed.

Use a documented proxy when no tokenizer or host counter is available. A
simple `ceil(UTF-8 bytes / 4)` estimate is suitable only for comparing the same
English Markdown surface before and after; also retain bytes, words, and lines
so the estimate is reproducible. Do not compare proxy values with billed or
host-reported tokens as if they were equivalent.

Classify context by when it is paid:

| Layer | Examples |
| --- | --- |
| Always loaded | Skill names/descriptions, startup gate, applicable repository instructions, enabled MCP/tool schemas |
| Selected route | Full `SKILL.md`, active-phase references, scoped source files |
| Growing session | User/assistant history, repeated instructions, intermediate updates, tool inputs and results, compaction summaries |
| Output and model work | Final response and any usage or reasoning metrics actually exposed by the host |

## Route Chains

Choose representative requests before changing content. For every public
route record:

- no-match or control request;
- minimum route that needs only the main Skill;
- common active phase;
- worst valid phase chain;
- required references, expected tool-call categories, and default report
  fields;
- authorization that is present, absent, or still needs clarification.

Sum only files the route requires. Do not count sibling references as loaded
merely because they are installed. Separate the startup gate from host-managed
Skill metadata so both costs remain visible.

## Candidate Analysis

Search metadata, headings, reference edges, repeated normalized rules, command
blocks, and report sections first. Read full text only for candidates with one
of these signals:

- broad or overlapping trigger descriptions;
- startup content duplicated by task Skills or public documentation;
- an index or reference that only forwards to another reference;
- safety rules owned by several files instead of one always-loaded owner;
- a phase that loads remote, mutation, recovery, or validation guidance before
  that phase is authorized;
- repeated state probes whose results cannot change the next decision;
- validation loops without a changed-surface or stopping condition;
- reports that require fields unrelated to the outcome or a recovery decision.

Prefer deleting forwarding layers, making every remaining reference directly
discoverable from its parent Skill, and retaining safety-critical preconditions
in the file loaded before mutation. Do not move an authorization or rollback
gate behind a reference that the dangerous phase might skip.

## Implementation

Optimize in this order:

1. Shrink startup and no-match context.
2. Narrow metadata descriptions without losing real user trigger phrases.
3. Remove duplicate owners and forwarding-only route layers.
4. Split active phases so planning does not load execution and local work does
   not load remote or cleanup instructions.
5. Batch independent read-only probes and reduce large tool output before it
   enters the conversation.
6. Make validation proportional to changed surfaces and stop after a
   conclusive current result.
7. Require final reports to retain the outcome, material evidence, caveats,
   recovery state, and next action while omitting repetition.

Scripts are justified only for repeated deterministic work that materially
reduces model context or error risk. Do not add a script solely to enforce
agent prose when a small instruction or existing validator is sufficient.

## Scenario Validation

Re-run the same representative requests after the change. At minimum cover:

1. Ordinary documentation and source edits that remain no-match.
2. Every public route's minimum and common phase.
3. A dangerous or remote phase with authorization deliberately absent.
4. A valid non-English request with an unambiguous canonical route.
5. One request that could match two routes and needs at most one material
   clarification.
6. The explicit Codex-usage request that selects this Skill without making it
   a general coding orchestrator.

For each scenario compare selected routes, loaded files, authorized actions,
required evidence, and stop behavior. Static route-contract checks do not prove
that a fresh host model selected the same route; label host-native routing as
not run or unavailable unless it was directly observed.
