# Axiom

[![Release](https://img.shields.io/github/v/release/wheakerd/axiom?sort=semver)](https://github.com/wheakerd/axiom/releases/latest)
[![Hosts: Codex | Claude Code](https://img.shields.io/badge/hosts-Codex%20%7C%20Claude%20Code-blue)](docs/compatibility.md)
[![Unit and integration tests](https://github.com/wheakerd/axiom/actions/workflows/unit-and-integration-tests.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/unit-and-integration-tests.yml)
[![Cross-platform hook runtime](https://github.com/wheakerd/axiom/actions/workflows/hook-runtime-integration.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/hook-runtime-integration.yml)
[![Distribution and publication guards](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml)
[![CodeQL](https://github.com/wheakerd/axiom/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Think before AI thinks.**

**Axiom is a Codex and Claude Code plugin with a collection of focused skills
for turning requests into clear, actionable work.** It helps clarify intent,
plan tasks, maintain repository instructions, research, review decisions, and
handle actions that need explicit authorization or a recovery plan. Both hosts
share the same skills and routes.

Describe what you want in your host, or name a skill directly. Axiom loads the
smallest matching skill set and its relevant references; everyday requests
continue through the host normally. The skills use the host's existing tools
and permissions, with no background service or automatic updater.

[Install](#installation) | [Update](#updating) | [Use](#usage) |
[Skills](docs/reference/skills.md) | [Documentation](docs/README.md)

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

## Usage

Describe the outcome you want, or name a skill: include `$skill-name` in Codex
or type `/axiom:skill-name` in Claude Code. Try a read-only request that
matches a skill:

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
[invocation notes](plugin/skills/using-axiom/SKILL.md#invocation-notes); a quiet
response is valid. These are expected behaviors, not a claim that your
installation has already reproduced them.

> [!IMPORTANT]
> A request that matches no Axiom skill still follows your host's permissions
> and repository instructions. No match is not a safety certification.
> Selecting a skill does not grant permission to edit, publish, deploy,
> or delete anything.

The [Skill Reference](docs/reference/skills.md) lists every bundled skill with a
copyable example and notes renamed skills; [Examples](docs/examples.md) shows
more requests and expected behavior.

## Documentation and Support

- [Documentation index](docs/README.md): guides and references by task.
- [Skill Reference](docs/reference/skills.md): bundled skills and examples.
- [Compatibility](docs/compatibility.md): supported hosts and known limitations,
  backed by the [release-status record](evidence/release-status.json).
- [Trust Model](docs/trust-model.md): security boundaries. Axiom is a public
  beta; its instructions do not replace host permissions or provide a sandbox.
- [Changelog](CHANGELOG.md): changes and migration notices.
- [GitHub Discussions](https://github.com/wheakerd/axiom/discussions): questions and early ideas.
- [GitHub Issues](https://github.com/wheakerd/axiom/issues/new/choose): bug reports,
  feature requests, routing cases, and compatibility reports.
- [SECURITY.md](SECURITY.md): report a vulnerability privately.
- [Contributing](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md):
  contribution guidance and community expectations.

## License

[MIT](LICENSE).
