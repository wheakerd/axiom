# Axiom

[![Release](https://img.shields.io/github/v/release/wheakerd/axiom?sort=semver)](https://github.com/wheakerd/axiom/releases/latest)
[![Distribution and publication guards](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml)
[![CodeQL](https://github.com/wheakerd/axiom/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Think before AI thinks.**

**Axiom is a Codex plugin with a collection of focused skills for turning
requests into clear, actionable work.** It helps clarify intent, plan tasks,
maintain repository instructions, research, review decisions, and handle
actions that need explicit authorization or a recovery plan.

Describe what you want in Codex, or name a skill directly. Axiom loads the
smallest matching skill set and its relevant references; everyday requests
continue through Codex normally. The skills use Codex's existing tools and
permissions, with no background service or automatic updater.

**Supported host:** Codex. ~~Claude Code~~ support has been retired; see
[Deprecated Skills and Support](#deprecated-skills-and-support).

[Install](#installation) | [Update](#updating) | [Use a skill](#skills) |
[Documentation](docs/README.md)

---

## Installation

Run these commands in a terminal to add the marketplace and install Axiom:

```bash
codex plugin marketplace add wheakerd/axiom
codex plugin add axiom@axiom
```

Start a new Codex chat or CLI session. Open `/hooks` and compare the installed
entry with the [Hook Reference](docs/reference/hooks.md) before trusting it.
Stop if the definitions differ. The [Getting Started guide](docs/guides/getting-started.md)
owns the full installation and first-use procedure.

## Updating

Refresh the installed marketplace snapshot from a terminal:

```bash
codex plugin marketplace upgrade axiom
```

In a supported Codex workspace plugin UI, use **Refresh**. After updating,
start a new session and inspect `/hooks` again. Axiom does not check for or
install updates automatically. See [Managing an Installation](docs/guides/managing-installation.md)
for disabling, removal, and troubleshooting.

## First Use

In Codex, try a read-only request that matches a skill:

```text
Use $agents-architect to audit this repository's AGENTS.md instruction system.
Report findings only; do not modify files.
```

Then try an ordinary request:

```text
Summarize the purpose of this README. Do not modify files.
```

The first should select `agents-architect`; the second should continue normally
without an Axiom skill. These are expected behaviors, not a claim that your
installation has already reproduced them.

> [!IMPORTANT]
> A request that matches no Axiom skill still follows Codex permissions
> and repository instructions. No match is not a safety certification.
> Selecting a skill does not grant permission to edit, publish, deploy,
> or delete anything.

---

## Skills

Use natural language or include `$skill-name` in a Codex message. The examples
below are chat prompts, not terminal commands. Each linked source describes
the skill's full scope and requirements; [Examples](docs/examples.md) gives
more requests and expected behavior.

### Shared skills

#### using-axiom

**Link:** [Startup routing skill](skills/using-axiom/SKILL.md)

**Description:** Finds the smallest matching skill set and leaves unmatched
work with Codex. It loads through the startup hook.

**Usage:**

```text
Use $using-axiom to identify the skill that fits this request.
```

#### clarify-intent

**Link:** [Request clarification](skills/clarify-intent/SKILL.md)

**Description:** Resolves materially different interpretations with a focused
question and useful options.

**Usage:**

```text
Use $clarify-intent to clarify what "clean up this project" should mean
before making changes.
```

#### delegate-simple-task

**Link:** [Bounded task delegation](skills/delegate-simple-task/SKILL.md)

**Description:** Assesses simple work against your ordered model preferences
while preserving the main model.

**Usage:**

```text
Use $delegate-simple-task to assess whether this typo fix can be delegated
using my model preferences.
```

#### task-planning

**Link:** [Task planning and revision](skills/task-planning/SKILL.md)

**Description:** Turns requirements into steps, dependencies, and acceptance
criteria, or updates an existing plan.

**Usage:**

```text
Use $task-planning to plan this settings-page change.
Do not implement it yet.
```

#### local-web-search

**Link:** [Research through a local browser or client](skills/local-web-search/SKILL.md)

**Description:** Limits information disclosed in requests and handles site
challenges through a user handoff.

**Usage:**

```text
Use $local-web-search to find official migration guidance
through my local browser.
```

#### agents-architect

**Link:** [Repository instruction architecture](skills/agents-architect/SKILL.md)

**Description:** Audits and maintains `AGENTS.md`, routed `.agents/` guidance,
and repository skills.

**Usage:**

```text
Use $agents-architect to audit this repository's instruction system.
Report findings only.
```

#### agent-plugin-architect

**Link:** [Packaged plugin architecture](skills/agent-plugin-architect/SKILL.md)

**Description:** Designs or audits skills, routes, manifests, hooks, and
compatibility evidence for a packaged agent plugin.

**Usage:**

```text
Use $agent-plugin-architect to audit this Codex plugin's package architecture
without editing it.
```

#### optimize-codex-usage

**Link:** [Codex usage analysis](skills/optimize-codex-usage/SKILL.md)

**Description:** Finds ways to reduce context, token, and tool overhead while
preserving required quality.

**Usage:**

```text
Use $optimize-codex-usage to review this workflow's context overhead
and recommend reductions.
```

#### review-axiom-task

**Link:** [Axiom task review](skills/review-axiom-task/SKILL.md)

**Description:** Reviews observable routing, authorization, actions, and
evidence for an identified task.

**Usage:**

```text
Use $review-axiom-task to review why Axiom paused the previous task.
Do not retry it.
```

#### confirm-external-action

**Link:** [Consequential external actions](skills/confirm-external-action/SKILL.md)

**Description:** Checks the actor, destination, exact content, and existing
authorization before execution and verification.

**Usage:**

```text
Use $confirm-external-action to prepare this announcement for publication.
Show the exact destination and text; do not publish yet.
```

#### traceable-git-submit

**Link:** [Traceable Git work](skills/traceable-git-submit/SKILL.md)

**Description:** Handles explicit checkpoints, consolidation, recovery, and
submissions that need traceability.

**Usage:**

```text
Use $traceable-git-submit to create a checkpoint of the README changes.
Do not push.
```

#### reversible-system-change

**Link:** [Changes with recovery planning](skills/reversible-system-change/SKILL.md)

**Description:** Plans, rehearses, or executes persistent changes with
verified recovery and outcome checks.

**Usage:**

```text
Use $reversible-system-change to plan this database migration and its rollback.
Do not execute it.
```

### Deprecated Skills and Support

No current top-level bundled skill is marked deprecated. Earlier nested
AGENTS Architect topics are now supporting references within
[`agents-architect`](skills/agents-architect/SKILL.md), not separate skills to
install or invoke.

~~Claude Code installation and runtime support~~ was removed in
[v0.11.0](docs/releases/v0.11.0.md). Existing users should disable or uninstall
their old Axiom installation in that host and use the Codex installation above.
Updating the repository does not remove cached installations.

`agent-plugin-architect` can still help design Claude Code plugins for other
projects. That skill does not make Claude Code a supported host for Axiom.

---

## Security and Checks

The release badge follows GitHub Releases automatically. The other status
badges link to the repository's live workflow results:

- **Distribution and publication guards** validate the package, documentation,
  and repository publication rules.
- **CodeQL** scans Python and GitHub Actions workflows for potential
  vulnerabilities. Its configuration is in [the security workflow](.github/workflows/codeql.yml).
- **MIT** identifies the project's license.

A workflow badge reports a run result, not a guarantee that the project is
free of vulnerabilities. Axiom is a public beta, and its instructions do not
replace Codex permissions or provide a sandbox. Read the
[Trust Model](docs/trust-model.md) for the security boundaries and
[SECURITY.md](SECURITY.md) to report a vulnerability privately.

## Documentation and Support

- [Documentation index](docs/README.md): guides and references by task.
- [Compatibility](docs/compatibility.md): supported hosts and known limitations,
  backed by the [release-status record](evidence/release-status.json).
- [Architecture](docs/architecture.md): how routing and skills fit together.
- [Changelog](CHANGELOG.md): changes and migration notices.
- [GitHub Issues](https://github.com/wheakerd/axiom/issues): help and bug reports.
- [Contributing](CONTRIBUTING.md): contribution and validation guidance.

## License

[MIT](LICENSE).
