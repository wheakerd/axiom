# Skill Reference

Axiom bundles the skills below for both Codex and Claude Code. Describe what you want in natural language, include `$skill-name` in Codex, or type `/axiom:skill-name` in Claude Code. The examples are chat prompts, not terminal commands; they name each skill in plain words, which reads the same in both hosts. Each linked source describes the skill's full scope and requirements; [Examples](../examples.md) shows more requests and expected behavior.

## Shared skills

### using-axiom

**Link:** [Startup routing skill](../../plugin/skills/using-axiom/SKILL.md)

**Description:** Finds the smallest matching skill set and leaves unmatched work with the host. It selects bundled skills by the descriptions in the host's skill list, keeps a more specific skill or tool you chose, and loads through the startup hook. When you explicitly delegate a choice and every alternative is reversible and already authorized, the model picks the one that fits your environment and goal and says which and why before acting; otherwise the gate asks first.

**Usage:**

```text
Use the using-axiom skill to identify the skill that fits this request.
```

### clarify-intent

**Link:** [Request clarification](../../plugin/skills/clarify-intent/SKILL.md)

**Description:** Resolves materially different interpretations with one focused question per open decision, useful options, and room for your own answer. It asks only for decisions that the request, context, and your environment leave open, never for reassurance; a choice between alternatives with different authority stays yours unless you delegate it and every alternative is reversible and already authorized.

**Usage:**

```text
Use the clarify-intent skill to clarify what "clean up this project" should mean
before making changes.
```

### delegate-simple-task

**Link:** [Bounded task delegation](../../plugin/skills/delegate-simple-task/SKILL.md)

**Description:** Delegates clear, simple, bounded work to a model from your ordered candidate list while the main session keeps responsibility for the outcome. An explicit invocation selects the skill. It requires the active `using-axiom` gate and states the unmet condition instead of silently declining. Before delegating it shows the exact model and brief and asks once, unless an explicit invocation or standing delegation policy already gave consent within a permission-bypass mode; that one answer covers both consent and the assignment. The host's reasoning level is not a condition: the main session judges whether it can state the work completely and check the result.

**Usage:**

```text
Use the delegate-simple-task skill to assess this typo fix for my ordered
model candidates, and show me the exact model and brief before delegating.
```

### task-planning

**Link:** [Task planning and revision](../../plugin/skills/task-planning/SKILL.md)

**Description:** Turns requirements into steps, dependencies, and acceptance criteria, or updates an existing plan.

**Usage:**

```text
Use the task-planning skill to plan this settings-page change.
Do not implement it yet.
```

### continuous-progress

**Link:** [Supervised progress across sessions](../../plugin/skills/continuous-progress/SKILL.md)

**Description:** Explicitly invoked progress through fresh workers and coordinator handoffs, with a verified native supervisor. Stops after verified completion or cancellation; local scheduling requires the owning host application and the machine to remain available.

**Usage:**

```text
Use the continuous-progress skill to finish this task. Create fresh
execution and successor chats as needed, register an independent native
supervisor, and stop its schedule when the task is verified complete or I
cancel.
```

### local-web-search

**Link:** [Research through a local browser or client](../../plugin/skills/local-web-search/SKILL.md)

**Description:** Limits information disclosed in requests and handles site challenges through a user handoff.

**Usage:**

```text
Use the local-web-search skill to find official migration guidance
through my local browser.
```

### agents-architect

**Link:** [Repository instruction architecture](../../plugin/skills/agents-architect/SKILL.md)

**Description:** Audits and maintains `AGENTS.md`, routed `.agents/` guidance, and repository skills; places task state in Git metadata and keeps a grown instruction memory navigable.

**Usage:**

```text
Use the agents-architect skill to audit this repository's instruction system.
Report findings only.
```

### agent-plugin-architect

**Link:** [Packaged plugin architecture](../../plugin/skills/agent-plugin-architect/SKILL.md)

**Description:** Designs or audits skills, routes, manifests, hooks, and compatibility evidence for a packaged agent plugin.

**Usage:**

```text
Use the agent-plugin-architect skill to audit this plugin's package architecture
without editing it.
```

### optimize-agent-usage

**Link:** [Agent usage analysis](../../plugin/skills/optimize-agent-usage/SKILL.md)

**Description:** Finds ways to reduce context, token, and tool overhead while preserving required quality.

**Usage:**

```text
Use the optimize-agent-usage skill to review this workflow's context overhead
and recommend reductions.
```

### review-axiom-task

**Link:** [Axiom task review](../../plugin/skills/review-axiom-task/SKILL.md)

**Description:** Reviews observable routing, authorization, actions, and evidence for an identified task. A prior refusal governs neither a review nor a narrower request.

**Usage:**

```text
Use the review-axiom-task skill to review why Axiom paused the previous task.
Do not retry it.
```

### verify-completion

**Link:** [Completion verification](../../plugin/skills/verify-completion/SKILL.md)

**Description:** Verifies completion, progress, or success claims against current direct evidence, especially after compaction or resume, and advises before complying when evidence conflicts.

**Usage:**

```text
Use the verify-completion skill to check whether this task is actually
complete. List each criterion with what you observed now, not what you recall.
```

### confirm-external-action

**Link:** [Consequential external actions](../../plugin/skills/confirm-external-action/SKILL.md)

**Description:** Checks the actor, destination, exact content, and existing authorization before execution and verification.

**Usage:**

```text
Use the confirm-external-action skill to prepare this announcement for
publication. Show the exact destination and text; do not publish yet.
```

### traceable-git-submit

**Link:** [Traceable Git work](../../plugin/skills/traceable-git-submit/SKILL.md)

**Description:** Handles explicit checkpoints, consolidation, recovery, and submissions that need traceability. Ordinary named-remote non-force Git stays with the host.

**Usage:**

```text
Use the traceable-git-submit skill to create a checkpoint of the README changes.
Do not push.
```

### reversible-system-change

**Link:** [Changes with recovery planning](../../plugin/skills/reversible-system-change/SKILL.md)

**Description:** Plans, rehearses, or executes persistent changes with verified recovery and outcome checks. When you explicitly delegate the choice of target or environment and every alternative is reversible and already authorized, it chooses by your environment and goal and says which and why first. If recovery cannot be verified, it stops before candidate or active-state mutation; if you then knowingly choose to proceed without it, that informed waiver lifts the rollback requirement only for the effects you were told about, every other effect, rule, and check still applies, and the change is never called reversible.

**Usage:**

```text
Use the reversible-system-change skill to plan this database migration
and its rollback. Do not execute it.
```

## Renamed and retired skills

`optimize-codex-usage` was renamed `optimize-agent-usage` in [v0.16.0](../releases/v0.16.0.md) and now runs in both hosts. Invoke the new name; the old name is no longer bundled. A Claude Code installation cached before v0.11.0 updates through the [README update commands](../../README.md#updating). The [Changelog](../../CHANGELOG.md) records earlier removals and restored host support.
