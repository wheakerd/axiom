# Axiom Documentation

Use this index to find the document that owns the task or fact you need. The
documentation architecture is being migrated in reviewable phases under
[Issue #110](https://github.com/wheakerd/axiom/issues/110); the locations below
describe the repository as it exists now, not the completed target layout.

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
| Report a host result | [Field Validation](field-validation.md) | Testers and auditors |
| Understand package identity | [Runtime and Repository Identity](runtime-identity.md) | Maintainers and auditors |
| Review repository controls | [Repository Governance](repository-governance.md) | Maintainers |
| Contribute documentation | [Documentation Policy](maintainers/documentation-policy.md) | Contributors |
| Prepare release documentation and evidence | [Release Documentation And Evidence](maintainers/release-documentation.md) | Maintainers and auditors |
| Review plugin-architecture audit rules | [Agent Plugin Architect Route Contract](agent-plugin-architect-route-contract.md) | Maintainers |

For help, use [GitHub Issues](https://github.com/wheakerd/axiom/issues). Report
security concerns through the process in [SECURITY.md](../SECURITY.md).

## Current Collections

- [Version notes](releases/) retain version-specific migration, architecture,
  compatibility, security, and evidence detail. They are neither the current
  installation guide nor the final GitHub Release body.
- [Evidence](../evidence/) and [evaluation results](../evals/) retain
  machine-readable facts and historical observations. A historical record is
  not a statement about the current host.

Project-operation material is intentionally outside this current user
documentation tree under `project/`; it is not current product guidance.

## Current Structure And Migration

The current repository still has transitional overlap:

- `README.md` is the bounded product landing page;
- `docs/guides/` owns first use and the host-managed installation lifecycle;
- `docs/reference/hooks.md` renders the canonical Hook declarations and
  wrapper, while `docs/getting-started.md` remains only as a compatibility
  entry for historical links;
- `docs/compatibility.md` owns the concise current support contract and links
  to preserved current and historical evidence;
- `docs/maintainers/release-documentation.md` defines the fix-forward boundary
  among the Changelog, version notes, Release body, and evidence;
- `project/` separately owns marketing, distribution, channel-status, launch,
  and editorial plans.

The accepted target separates current user guides, concepts, references,
maintainer policy, historical evidence, and project operations. Each migration
phase must preserve working links and historical records. Until a phase moves
content, the existing file remains the truthful public location.

See the [Documentation Policy](maintainers/documentation-policy.md) for the
document classes, lifecycle vocabulary, canonical owners, migration rules, and
validation expectations.
