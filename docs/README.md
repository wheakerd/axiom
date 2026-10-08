# Axiom Documentation

Use this index to find the document that owns the task or fact you need. The
locations below are the current canonical public structure; historical
evidence remains distinct from current user guidance.

## Start By Task

| I want to | Start here | Audience |
| --- | --- | --- |
| Install Axiom and try one routed request | [Getting Started](guides/getting-started.md) | Users |
| Update, disable, remove, or troubleshoot Axiom | [Managing an Installation](guides/managing-installation.md) | Users |
| Inspect exact Hook commands | [Hook Reference](reference/hooks.md) | Users and auditors |
| Understand what Axiom does | [Architecture](architecture.md) | Users and reviewers |
| Review permissions and trust boundaries | [Trust Model](trust-model.md) | Users and security reviewers |
| Check current host support | [Compatibility](compatibility.md) | Users and auditors |
| See route examples | [Examples](examples.md) | Users and reviewers |
| Resolve an unclear request | [Clarify Intent example](examples.md#clarify-intent) | Users |
| Delegate simple work without changing the main model | [Delegate Simple Task example](examples.md#delegate-simple-task) | Users |
| Create or revise a task plan | [Task Planning example](examples.md#task-planning) | Users |
| Research through a local browser or client | [Local Web Search example](examples.md#local-web-search) | Users |
| Interpret evidence files or report a host result | [Field Validation](field-validation.md) | Testers and auditors |
| Understand package identity | [Runtime and Repository Identity](runtime-identity.md) | Maintainers and auditors |
| Review repository controls | [Repository Governance](repository-governance.md) | Maintainers |
| Contribute documentation | [Documentation Policy](maintainers/documentation-policy.md) | Contributors |
| Prepare release documentation and evidence | [Release Documentation And Evidence](maintainers/release-documentation.md) | Maintainers and auditors |
| Review plugin-architecture audit rules | [Agent Plugin Architect Route Contract](agent-plugin-architect-route-contract.md) | Maintainers |

For help, use [GitHub Issues](https://github.com/wheakerd/axiom/issues). Report
security concerns through the process in [SECURITY.md](../SECURITY.md).

## Candidate And Historical Records

The [current release status](../evidence/release-status.json) owns the candidate
binding and host-observation status. The [v0.13.3 candidate notes](releases/v0.13.3.md)
explain the current changes; a candidate is not a published or observed release.

- [Changelog](../CHANGELOG.md) records user-visible changes and required action.
- [Version notes](releases/) preserve version-specific migrations, architecture,
  compatibility, security, and evidence. Earlier candidate wording describes
  its original source state, not the current publication state.
- [Evidence](../evidence/) and [evaluation results](../evals/) contain machine
  facts and observations with their own version, subject, and date.
- [Archived experiments](field-validation.md#archived-experiments) link the
  retired host snapshots and no-Hook work at verified immutable sources.

Use the task references above for current guidance. Historical records neither
establish current host support nor impose retired procedures on current work.

## Current Structure

The repository separates current guidance from historical evidence:

- `README.md` is the bounded product landing page;
- `docs/guides/` owns first use and the host-managed installation lifecycle;
- `docs/reference/hooks.md` renders the canonical Hook declarations and
  wrapper, while `docs/getting-started.md` remains only as a compatibility
  entry for historical links;
- `docs/compatibility.md` owns the concise current support contract and links
  to preserved current and historical evidence; retired host snapshots and
  experiments are indexed in [Field Validation](field-validation.md#archived-experiments);
- `docs/maintainers/release-documentation.md` defines the fix-forward boundary
  among the Changelog, version notes, Release body, and evidence.

See the [Documentation Policy](maintainers/documentation-policy.md) for the
document classes, lifecycle vocabulary, canonical owners, migration rules, and
validation expectations.
