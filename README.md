<div align="center">

# Axiom

**Think before AI thinks.**

<!-- readme:badges:start -->
[![Latest release](https://img.shields.io/github/v/release/wheakerd/axiom?sort=semver&style=for-the-badge&label=release&color=0f766e)](https://github.com/wheakerd/axiom/releases/latest) [![Skills: 14](https://img.shields.io/badge/skills-14-0369a1?style=for-the-badge)](docs/reference/skills.md) [![Hosts: Codex and Claude Code](https://img.shields.io/badge/hosts-Codex%20%7C%20Claude%20Code-6d28d9?style=for-the-badge)](docs/compatibility.md) [![License: MIT](https://img.shields.io/badge/license-MIT-b45309?style=for-the-badge)](LICENSE)
<!-- readme:badges:end -->

[![Unit and integration tests](https://github.com/wheakerd/axiom/actions/workflows/unit-and-integration-tests.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/unit-and-integration-tests.yml) [![Cross-platform hook runtime](https://github.com/wheakerd/axiom/actions/workflows/hook-runtime-integration.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/hook-runtime-integration.yml) [![Distribution and publication guards](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/distribution-drift.yml) [![CodeQL](https://github.com/wheakerd/axiom/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/wheakerd/axiom/actions/workflows/codeql.yml)

Focused workflow skills for Codex and Claude Code that turn requests into clear, actionable work.

[Install](#installation) | [Update](#updating) | [Use](#usage) | [Skills](#skills) | [Documentation](docs/README.md) | [Changelog](CHANGELOG.md)

![Axiom: workflow guardrails for Codex and Claude Code. Scope, authority, evidence, rollback.](docs/assets/social-preview.png)

If Axiom helps your agent work, consider starring the repository. Stars help other Codex and Claude Code users find it.

[![Star Axiom on GitHub](https://img.shields.io/github/stars/wheakerd/axiom?style=for-the-badge&logo=github&label=star&color=f59e0b)](https://github.com/wheakerd/axiom/stargazers)

</div>

---

## Skills

Describe the outcome you want, or name a skill. Axiom selects a bundled skill from your host's skill list by its description; a request that matches none continues through the host as usual. Skills use the host's existing tools and permissions, with no background service or automatic updater.

<!-- readme:skill-index:start -->
| Skill | What it does |
| --- | --- |
| [`using-axiom`](docs/reference/skills.md#using-axiom) | Route installed Axiom skills from a session bootstrap |
| [`clarify-intent`](docs/reference/skills.md#clarify-intent) | Resolve unclear requests with options or a custom answer |
| [`delegate-simple-task`](docs/reference/skills.md#delegate-simple-task) | Assess delegation with top reasoning, the gate, and consent |
| [`task-planning`](docs/reference/skills.md#task-planning) | Create and revise plans around current requirements |
| [`continuous-progress`](docs/reference/skills.md#continuous-progress) | Supervised progress across fresh sessions |
| [`local-web-search`](docs/reference/skills.md#local-web-search) | Constrain local searches and stop at site challenges |
| [`agents-architect`](docs/reference/skills.md#agents-architect) | Initialize, maintain, and validate scoped AGENTS.md systems |
| [`agent-plugin-architect`](docs/reference/skills.md#agent-plugin-architect) | Design and audit packaged plugin architecture |
| [`optimize-agent-usage`](docs/reference/skills.md#optimize-agent-usage) | Reduce agent context and workflow overhead |
| [`review-axiom-task`](docs/reference/skills.md#review-axiom-task) | Audit Axiom decisions from observable evidence |
| [`verify-completion`](docs/reference/skills.md#verify-completion) | Check completion claims against current evidence |
| [`confirm-external-action`](docs/reference/skills.md#confirm-external-action) | Bind and verify consequential external actions |
| [`traceable-git-submit`](docs/reference/skills.md#traceable-git-submit) | Trace checkpoints and explicit Git submissions |
| [`reversible-system-change`](docs/reference/skills.md#reversible-system-change) | Plan and verify reversible system changes |
<!-- readme:skill-index:end -->

The [Skill Reference](docs/reference/skills.md) gives each skill's full description, a copyable example, and rename notices.

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

Each marketplace selects an immutable published version. A new version reaches both marketplaces only after its release is published and verified; development commits on `main` do not advance that selection.

Compare the installed startup Hook with the [Hook Reference](docs/reference/hooks.md) before it runs, and stop if the definitions differ. In Codex, start a new session and review the Hook in `/hooks`; Codex skips a new or changed Hook until you trust it. Claude Code has no separate Hook trust step and runs the Hook at the next `SessionStart` after the plugin loads, so compare the installed `hooks/claude-hooks.json` before starting a session or running `/reload-plugins`. The [Getting Started guide](docs/guides/getting-started.md) owns the full installation and first-use procedure.

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

After updating, repeat the Hook comparison above before the updated Hook runs. Automatic update behavior is controlled by each host and your settings. See [Managing an Installation](docs/guides/managing-installation.md) for in-app updates, disabling, removal, and troubleshooting. For a marketplace clone timeout in either host, follow the guide's [recovery procedure](docs/guides/managing-installation.md#marketplace-clone-timeouts).

## Usage

To name a skill, include `$skill-name` in Codex or type `/axiom:skill-name` in Claude Code. Try a read-only request that matches a skill:

```text
Use the agents-architect skill to audit this repository's AGENTS.md
instruction system. Report findings only; do not modify files.
```

Then try an ordinary request:

```text
Summarize the purpose of this README. Do not modify files.
```

The first request should select `agents-architect`; the second should continue normally without another skill. Any explanation of the routing decision is optional and follows the [invocation notes](plugin/skills/using-axiom/SKILL.md#invocation-notes); a quiet response is valid. These are expected behaviors, not a claim that your installation has already reproduced them.

> [!IMPORTANT]
> A request that matches no Axiom skill still follows your host's permissions and repository instructions. No match is not a safety certification. Selecting a skill does not grant permission to edit, publish, deploy, or delete anything.

[Examples](docs/examples.md) shows more requests and their expected behavior.

## Star History

![Star history of wheakerd/axiom](https://raw.githubusercontent.com/wheakerd/axiom/stats/stars.svg)

The [Record star history workflow](.github/workflows/record-star-history.yml) re-renders the chart daily from [`stars.csv` on the `stats` branch](https://github.com/wheakerd/axiom/blob/stats/stars.csv); see the [stats branch policy](docs/repository-governance.md#stats-branch-policy).

## Documentation and Support

- [Documentation index](docs/README.md): guides and references by task.
- [Skill Reference](docs/reference/skills.md): bundled skills and examples.
- [Latest release](https://github.com/wheakerd/axiom/releases/latest) and [Changelog](CHANGELOG.md): what changed in each version and any required action.
- [Compatibility](docs/compatibility.md): supported hosts and known limitations, backed by the [release-status record](evidence/release-status.json).
- [Trust Model](docs/trust-model.md): security boundaries. Axiom is a public beta; its instructions do not replace host permissions or provide a sandbox.
- [GitHub Discussions](https://github.com/wheakerd/axiom/discussions): questions and early ideas.
- [GitHub Issues](https://github.com/wheakerd/axiom/issues/new/choose): bug reports, feature requests, routing cases, and compatibility reports.
- [SECURITY.md](SECURITY.md): report a vulnerability privately.
- [Contributing](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md): contribution guidance and community expectations.

## License

[MIT](LICENSE).
