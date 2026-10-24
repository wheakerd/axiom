# Axiom

[![Release](https://img.shields.io/github/v/release/wheakerd/axiom?sort=semver)](https://github.com/wheakerd/axiom/releases/latest)
[![Distribution and publication guards](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml)
[![CodeQL](https://github.com/wheakerd/axiom/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Think before AI thinks.**

**Axiom is a Codex and Claude Code plugin with a collection of focused skills
for turning requests into clear, actionable work.** It helps clarify intent, plan tasks,
maintain repository instructions, research, review decisions, and handle
actions that need explicit authorization or a recovery plan.

Describe what you want in your host, or name a skill directly. Axiom loads the
smallest matching skill set and its relevant references; everyday requests
continue through the host normally. The skills use the host's existing tools
and permissions, with no background service or automatic updater.

**Supported hosts:** Codex and Claude Code. Both share the same skills and
routes.

[Install](#installation) | [Update](#updating) | [Use a skill](#skills) |
[Documentation](docs/README.md)

---

## Installation

Run these commands in a terminal for your host.

**Codex:**

```bash
codex plugin marketplace add wheakerd/axiom --sparse .agents/plugins
codex plugin add axiom@axiom
```

**Claude Code:**

```bash
claude plugin marketplace add wheakerd/axiom
claude plugin install axiom@axiom
```

Each marketplace selects an immutable published version. Development commits
on `main` do not advance that selection.

Compare the installed startup Hook with the
[Hook Reference](docs/reference/hooks.md) before it runs, and stop if the
definitions differ. In Codex, start a new session and review the Hook in
`/hooks`; Codex skips a new or changed Hook until you trust it. Claude Code has
no separate Hook trust step and runs the Hook at the next `SessionStart` after
the plugin loads, so compare the installed `hooks/claude-hooks.json` before
starting a session or running `/reload-plugins`. The
[Getting Started guide](docs/guides/getting-started.md) owns the full
installation and first-use procedure.

## Updating

Refresh the installed marketplace snapshot from a terminal.

**Codex:**

```bash
codex plugin marketplace upgrade axiom
```

**Claude Code:**

```bash
claude plugin marketplace update axiom
claude plugin update axiom@axiom
```

After updating, repeat the Hook comparison above before the updated Hook
runs. Automatic update behavior is controlled by each host and your settings.
See [Managing an Installation](docs/guides/managing-installation.md) for in-app
updates, disabling, removal, and troubleshooting.
For a marketplace clone timeout in either host, follow the guide's
[recovery procedure](docs/guides/managing-installation.md#marketplace-clone-timeouts).

## First Use

Try a read-only request that matches a skill:

```text
Use the agents-architect skill to audit this repository's AGENTS.md
instruction system. Report findings only; do not modify files.
```

Then try an ordinary request:

```text
Summarize the purpose of this README. Do not modify files.
```

The first request should select `agents-architect`; the second should continue
normally without another skill. Any explanation of the routing decision is
optional and follows the
[invocation notes](skills/using-axiom/SKILL.md#invocation-notes); a quiet
response is valid. These are expected behaviors, not a claim that your
installation has already reproduced them.

> [!IMPORTANT]
> A request that matches no Axiom skill still follows your host's permissions
> and repository instructions. No match is not a safety certification.
> Selecting a skill does not grant permission to edit, publish, deploy,
> or delete anything.

---

## Skills

Use natural language, include `$skill-name` in Codex, or type
`/axiom:skill-name` in Claude Code. The examples below are chat prompts, not
terminal commands; they name each skill in plain words, which reads the same in
both hosts. Each linked source describes the skill's full scope and
requirements; [Examples](docs/examples.md) gives more requests and expected
behavior.

### Shared skills

#### using-axiom

**Link:** [Startup routing skill](skills/using-axiom/SKILL.md)

**Description:** Finds the smallest matching skill set and leaves unmatched
work with the host. It loads through the startup hook.

**Usage:**

```text
Use the using-axiom skill to identify the skill that fits this request.
```

#### clarify-intent

**Link:** [Request clarification](skills/clarify-intent/SKILL.md)

**Description:** Resolves materially different interpretations with a focused
question and useful options.

**Usage:**

```text
Use the clarify-intent skill to clarify what "clean up this project" should mean
before making changes.
```

#### delegate-simple-task

**Link:** [Bounded task delegation](skills/delegate-simple-task/SKILL.md)

**Description:** Assesses simple work against your ordered model preferences
while preserving the main model. Requires the active `using-axiom` gate, the
host's verified top reasoning level, and your consent to invoke the skill.

**Usage:**

```text
I authorize the delegate-simple-task skill to assess this typo fix using my
model preferences, only with the using-axiom gate active and my top reasoning
level verified.
```

#### task-planning

**Link:** [Task planning and revision](skills/task-planning/SKILL.md)

**Description:** Turns requirements into steps, dependencies, and acceptance
criteria, or updates an existing plan.

**Usage:**

```text
Use the task-planning skill to plan this settings-page change.
Do not implement it yet.
```

#### continuous-progress

**Link:** [Supervised progress across sessions](skills/continuous-progress/SKILL.md)

**Description:** Explicitly invoked progress through fresh workers and
coordinator handoffs, with a verified native supervisor. Stops after verified
completion or cancellation; local scheduling requires the owning host
application and the machine to remain available.

**Usage:**

```text
Use the continuous-progress skill to finish this task. Create fresh
execution and successor chats as needed, register an independent native
supervisor, and stop its schedule when the task is verified complete or I
cancel.
```

#### local-web-search

**Link:** [Research through a local browser or client](skills/local-web-search/SKILL.md)

**Description:** Limits information disclosed in requests and handles site
challenges through a user handoff.

**Usage:**

```text
Use the local-web-search skill to find official migration guidance
through my local browser.
```

#### agents-architect

**Link:** [Repository instruction architecture](skills/agents-architect/SKILL.md)

**Description:** Audits and maintains `AGENTS.md`, routed `.agents/` guidance,
and repository skills.

**Usage:**

```text
Use the agents-architect skill to audit this repository's instruction system.
Report findings only.
```

#### agent-plugin-architect

**Link:** [Packaged plugin architecture](skills/agent-plugin-architect/SKILL.md)

**Description:** Designs or audits skills, routes, manifests, hooks, and
compatibility evidence for a packaged agent plugin.

**Usage:**

```text
Use the agent-plugin-architect skill to audit this plugin's package architecture
without editing it.
```

#### optimize-agent-usage

**Link:** [Agent usage analysis](skills/optimize-agent-usage/SKILL.md)

**Description:** Finds ways to reduce context, token, and tool overhead while
preserving required quality.

**Usage:**

```text
Use the optimize-agent-usage skill to review this workflow's context overhead
and recommend reductions.
```

#### review-axiom-task

**Link:** [Axiom task review](skills/review-axiom-task/SKILL.md)

**Description:** Reviews observable routing, authorization, actions, and
evidence for an identified task.

**Usage:**

```text
Use the review-axiom-task skill to review why Axiom paused the previous task.
Do not retry it.
```

#### confirm-external-action

**Link:** [Consequential external actions](skills/confirm-external-action/SKILL.md)

**Description:** Checks the actor, destination, exact content, and existing
authorization before execution and verification.

**Usage:**

```text
Use the confirm-external-action skill to prepare this announcement for
publication. Show the exact destination and text; do not publish yet.
```

#### traceable-git-submit

**Link:** [Traceable Git work](skills/traceable-git-submit/SKILL.md)

**Description:** Handles explicit checkpoints, consolidation, recovery, and
submissions that need traceability.

**Usage:**

```text
Use the traceable-git-submit skill to create a checkpoint of the README changes.
Do not push.
```

#### reversible-system-change

**Link:** [Changes with recovery planning](skills/reversible-system-change/SKILL.md)

**Description:** Plans, rehearses, or executes persistent changes with
verified recovery and outcome checks.

**Usage:**

```text
Use the reversible-system-change skill to plan this database migration
and its rollback. Do not execute it.
```

### Renamed and retired skills

`optimize-codex-usage` was renamed `optimize-agent-usage` in
[v0.16.0](docs/releases/v0.16.0.md) and now runs in both hosts. Invoke the new
name; the old name is no longer bundled. A Claude Code installation cached
before v0.11.0 updates through the commands above. The
[Changelog](CHANGELOG.md) records earlier removals and restored host support.

---

## Security and Checks

The release badge follows GitHub Releases. The workflow badges show live
results: **Distribution and publication guards** validate the package,
documentation, and publication rules, and **CodeQL** scans Python and GitHub
Actions workflows ([configuration](.github/workflows/codeql.yml)). A badge
reports a run result, not a guarantee that the project is free of
vulnerabilities. Axiom is a public beta, and its instructions do not
replace host permissions or provide a sandbox. Read the
[Trust Model](docs/trust-model.md) for the security boundaries and
[SECURITY.md](SECURITY.md) to report a vulnerability privately.

## Documentation and Support

- [Documentation index](docs/README.md): guides and references by task.
- [Compatibility](docs/compatibility.md): supported hosts and known limitations,
  backed by the [release-status record](evidence/release-status.json).
- [Architecture](docs/architecture.md): how routing and skills fit together.
- [Changelog](CHANGELOG.md): changes and migration notices.
- [GitHub Discussions](https://github.com/wheakerd/axiom/discussions): questions and early ideas.
- [GitHub Issues](https://github.com/wheakerd/axiom/issues/new/choose): bug reports,
  feature requests, routing cases, and compatibility reports.
- [Code of Conduct](CODE_OF_CONDUCT.md): community expectations and reporting.
- [Contributing](CONTRIBUTING.md): contribution and validation guidance.

## License

[MIT](LICENSE).
