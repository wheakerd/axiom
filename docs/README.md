# Axiom Documentation

English | [Simplified Chinese (zh-CN)](README.zh-CN.md)

Use this index to find the document that owns the task or fact you need. The locations below are the current canonical public structure; historical evidence remains distinct from current user guidance.

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
| Interpret evidence files or report a host result | [Field Validation](field-validation.md) | Testers and auditors |
| Understand package identity | [Runtime and Repository Identity](runtime-identity.md) | Maintainers and auditors |
| Decide the version increment or bundling for a change | [Version Increment](runtime-identity.md#version-increment) | Maintainers |
| Review repository controls | [Repository Governance](repository-governance.md) | Maintainers |
| Trace a repository policy revision | [Repository Policy Revisions](repository-policy-revisions.md) | Maintainers and auditors |
| Contribute documentation | [Documentation Policy](maintainers/documentation-policy.md) | Contributors |
| Prepare release documentation and evidence | [Release Documentation And Evidence](maintainers/release-documentation.md) | Maintainers and auditors |
| Decide where Axiom is listed and record a submission | [Distribution Channels](maintainers/distribution-channels.md) | Maintainers |
| Review plugin-architecture audit rules | [Agent Plugin Architect Route Contract](agent-plugin-architect-route-contract.md) | Maintainers |
| Make a contribution | [Contributing](../CONTRIBUTING.md) | Contributors |
| Change a Skill, route, or Hook | [Runtime Changes](maintainers/runtime-changes.md) | Contributors |
| Run repository checks and interpret results | [Contributor Validation](maintainers/validation.md) | Contributors |

Ask questions in [GitHub Discussions](https://github.com/wheakerd/axiom/discussions) and file actionable reports through the [GitHub Issues](https://github.com/wheakerd/axiom/issues/new/choose) forms. Report security concerns through the process in [SECURITY.md](../SECURITY.md), and see the [Code of Conduct](../CODE_OF_CONDUCT.md) for community expectations.

## Candidate And Historical Records

The [checked-in release status](../evidence/release-status.json) owns the source candidate's version and binding. Candidate wording is preserved at its original source state; consult the [published Releases](https://github.com/wheakerd/axiom/releases) for publication facts. Publication alone does not establish installed-host behavior.

- [Changelog](../CHANGELOG.md) records user-visible changes and required action.
- [Version notes](releases/) preserve version-specific migrations, architecture, compatibility, security, and evidence. Earlier candidate wording describes its original source state, not the current publication state.
- [Evidence](../evidence/) contains machine facts with their own version, subject, and date.
- [Archived experiments](field-validation.md#archived-experiments) link the retired host snapshots, the no-Hook work, and the routing evaluations with their observation records at verified immutable sources.

Use the task references above for current guidance. Historical records neither establish current host support nor impose retired procedures on current work.

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
| `docs/releases/` | Preserved version-specific notes and candidate evidence |
| `evidence/` | Machine-readable identity, status, policy revisions, and runtime histories |
| `<name>.zh-CN.md` beside an English document | Simplified Chinese translation of that document; English is canonical, and the translation changes in the same change as its source |

`docs/getting-started.md` remains a compatibility entry for historical links. Use [Getting Started](guides/getting-started.md) for the maintained guide and [Contributing](../CONTRIBUTING.md#repository-layout) for the full repository map.

See the [Documentation Policy](maintainers/documentation-policy.md) for the document classes, lifecycle vocabulary, canonical owners, migration rules, and validation expectations.
