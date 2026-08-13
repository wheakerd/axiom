# Maintenance Application

## Purpose

Apply approved durable AGENTS updates to the smallest correct surface.

## Apply when

- Evidence has produced candidate durable AGENTS updates.
- Authorization is satisfied or the task is read-only preview.
- Existing `AGENTS.md` or `.agents` content must be patched, split, or
  validated within this terminal owner's scope.

## Do not apply when

- Candidate updates still need context extraction.
- Non-Axiom or unclear-provenance `AGENTS.md` edits are not authorized.
- The only target is a repo-local skill; use `repo-local-skills.md` first.

## Durable update gate

Write only candidates with:

- Persistent future reuse.
- Clear path, task, domain, risk, workflow, or skill scope.
- Concrete agent action, prohibition, routing condition, or validation step.
- Verifiable evidence from code, config, tests, commands, authoritative docs, or repeated task history.
- Target-project specificity rather than restating Axiom packaged skill protocol.
- One canonical home.
- Verified AGENTS ownership: the nearest owning index, rule leaf, closer
  `AGENTS.md`, and likely adjacent owner have been checked first, and they do
  not already contain an equivalent rule unless the update amends that owner.
- Correct abstraction level.
- Positive context value after active-set size cost.
- Demonstrable retrieval value when proposed from task friction: a concise
  instruction, route, source-of-truth pointer, or validation step would
  materially reduce avoidable rediscovery in future matching work without
  replacing direct inspection of mutable source.
- No secrets, credentials, personal data, raw transcripts, or transient logs.

Reject or report temporary, speculative, duplicated, too broad, unsupported, or human-doc-only candidates.

Before applying a task-context update, confirm that context evidence reached
the established review-window boundary or reported the exact unavailable
history. Do not present a newest-phase-only extraction as a complete task
review. A complete broad review may still produce one small update or no file
change; review coverage and accepted-rule count are independent.

## Retrieval-friction disposition

When task evidence flags retrieval friction:

- For `instruction-gap`, add or repair only the durable rule in its canonical
  owner.
- For `routing-gap`, repair the smallest next hop needed to reach the existing
  owner; do not copy the owner into the route.
- For `validation-gap`, add the focused acceptance step that would prevent the
  same contract from being reconstructed from history.
- For `expected-live-verification`, report the read as still required and
  reject an AGENTS update.
- For `one-off-code-defect`, reject an AGENTS update and report source or
  regression-test repair as separately authorized work unless other evidence
  establishes a reusable project rule.

Do not optimize for zero source reads. Optimize for correct routing, stable
project constraints, and removal of avoidable rediscovery.

## Canonical homes

- Root `AGENTS.md`: true global constraints, priority, routing entry points, and minimum verification.
- `.agents/**`: routed group indexes, direct domain entries, rule leaves,
  cross-cutting safety or risk rule leaves, parent-owned references, and
  temporary runtime capsules.
- `.agents/skills/<skill-name>/SKILL.md`: repo-local skills for repeatable repository workflows only when explicitly requested or already part of the target repository design.
- Project docs: human source-of-truth facts that are not agent-executable guidance.
- Installed Axiom plugin: Axiom workflow triggers, packaged skill rules, internal routes, validation protocols, and reporting formats.

## Existing AGENTS reorganization

- For small approved updates, patch the smallest canonical file.
- Sink each approved update to the closest owning route. Root receives only true
  global constraints; group indexes receive only next-hop routing; direct
  domain entries and rule leaves receive scoped executable rules; risk-rule
  leaves receive explicit cross-cutting constraints; parent-owned references
  receive long supporting material.
- When initial inventory shows inherited, duplicated, oversized, or
  mixed-responsibility content, the parent route table must select
  `../migration-policy.md` as the primary owner instead of this terminal. If
  discovered here, safe-stop and return to the parent route; do not scan it as
  a maintenance sibling.
- Use `../routing-architecture.md` when the approved outcome needs a new or materially changed routed `.agents` tree.
- Use `../project-initialization.md` only as a target-shape reference after authorization when reorganizing an existing non-Axiom system. Do not treat it as fresh initialization.

## Validation and report

- Run static checks for route reachability, links, duplicate rules, protected metadata boundaries, secrets, and size model.
- Run routing scenarios when AGENTS routing changed.
- Run skill validation for changed repo-local skills when applicable.
- Report authorization basis, inspected task scope and review-window baseline,
  added/modified/rejected candidates, affected files, Git tracking state, byte
  changes, and validation results.

## Prohibited actions

- Do not update non-Axiom AGENTS systems without authorization.
- Do not rewrite protected plugin or skill metadata as ordinary AGENTS routing content.
- Do not copy Axiom packaged skill rules, trigger phrases, load policies,
  internal routes, validation protocols, or reporting formats into target
  `AGENTS.md` files.
- Do not create or update repo-local skills as local copies of Axiom packaged skills.
- Do not persist one-off task discoveries.
