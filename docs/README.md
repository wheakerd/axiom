# Axiom Documentation

English | [Simplified Chinese (zh-CN)](README.zh-CN.md)

Use this index to find the document that owns the task or fact you need. The locations below are the current canonical public structure.

Current guidance describes the same source snapshot as the document. See [Source And Version Scope](maintainers/documentation-policy.md#source-and-version-scope) when comparing the source tree, a published release, and an installed package.

## Start By Task

| I want to | Start here | Audience |
| --- | --- | --- |
| Install Axiom and try one routed request | [Getting Started](guides/getting-started.md) | Users |
| Update, disable, remove, or troubleshoot Axiom | [Managing an Installation](guides/managing-installation.md) | Users |
| Inspect exact Hook commands | [Hook Reference](reference/hooks.md) | Users and auditors |
| Find a skill and copy an example | [Skill Reference](reference/skills.md) | Users |
| Understand what Axiom does | [Architecture](architecture.md) | Users and reviewers |
| Review permissions and trust boundaries | [Trust Model](trust-model.md) | Users and security reviewers |
| Check current host support | [Compatibility](compatibility.md) | Users and auditors |
| See route examples | [Examples](examples.md) | Users and reviewers |
| Resolve an unclear request | [Clarify Intent example](examples.md#clarify-intent) | Users |
| Delegate simple work without changing the main model | [Delegate Simple Task example](examples.md#delegate-simple-task) | Users |
| Create or revise a task plan | [Task Planning example](examples.md#task-planning) | Users |
| Explicitly continue a task across sessions | [Continuous Progress](../plugin/skills/continuous-progress/SKILL.md) | Users |
| Research through a local browser or client | [Local Web Search example](examples.md#local-web-search) | Users |
| Report a host result | [Report A Compatibility Result](compatibility.md#report-a-compatibility-result) | Testers and auditors |
| Understand package identity | [Runtime Identity](runtime-identity.md) | Maintainers and auditors |
| Decide the version increment or bundling for a change | [Version Increment](runtime-identity.md#version-increment) | Maintainers |
| Review repository controls | [Repository Governance](repository-governance.md) | Maintainers |
| Contribute documentation | [Documentation Policy](maintainers/documentation-policy.md) | Contributors |
| Prepare release documentation and evidence | [Release Documentation And Evidence](maintainers/release-documentation.md) | Maintainers and auditors |
| Decide where Axiom is listed and record a submission | [Distribution Channels](maintainers/distribution-channels.md) | Maintainers |
| Review plugin-architecture audit rules | [Agent Plugin Architect Route Contract](agent-plugin-architect-route-contract.md) | Maintainers |
| Make a contribution | [Contributing](../CONTRIBUTING.md) | Contributors |
| Change a Skill, route, or Hook | [Runtime Changes](maintainers/runtime-changes.md) | Contributors |
| Run repository checks and interpret results | [Contributor Validation](maintainers/validation.md) | Contributors |

Ask questions in [GitHub Discussions](https://github.com/wheakerd/axiom/discussions) and file actionable reports through the [GitHub Issues](https://github.com/wheakerd/axiom/issues/new/choose) forms. Report security concerns through the process in [SECURITY.md](../SECURITY.md), and see the [Code of Conduct](../CODE_OF_CONDUCT.md) for community expectations.

## Release History

Consult the [published Releases](https://github.com/wheakerd/axiom/releases) for publication facts. Publication alone does not establish installed-host behavior.

- [Changelog](../CHANGELOG.md) records user-visible changes and required action for every version.
- [Runtime identity](../evidence/runtime-identity.json) records the current version and installed-file digest.
- [Earlier Records](compatibility.md#earlier-records) names the release tag that keeps version notes, routing evaluations, and host observation records.

## Current Structure

| Location | Responsibility |
| --- | --- |
| `plugin/` | Installed plugin root for both hosts; the rest of the repository supports development, validation, and release |
| Root `README.md` | Product introduction, installation and update quick start, and first use |
| Root `CONTRIBUTING.md` | Contribution intake, repository map, and review checklist |
| Root `SECURITY.md` | Supported security scope and private vulnerability reporting |
| Root `CODE_OF_CONDUCT.md` | Community conduct expectations and enforcement contact |
| Root `CHANGELOG.md` | User-visible changes, impact, and required action |
| `docs/guides/` | First use and host-managed installation lifecycle |
| Topical documents in `docs/` | Architecture, examples, trust, compatibility, identity, and repository governance |
| `docs/reference/` | Exact public technical references: the Skill Reference and the checked Hook rendering |
| `docs/maintainers/` | Runtime authoring, validation, documentation, and release procedures |
| `evidence/` | Machine-readable runtime identity |
| `<name>.zh-CN.md` beside an English document | Simplified Chinese translation of that document; English is canonical, and the translation changes in the same change as its source |

See [Contributing](../CONTRIBUTING.md#repository-layout) for the full repository map.

See the [Documentation Policy](maintainers/documentation-policy.md) for the document classes, canonical owners, migration rules, and validation expectations.
