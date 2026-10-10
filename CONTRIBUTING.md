# Contributing to Axiom

Keep contributions focused, evidence-based, and easy to review. Axiom's public
repository contains the installed Codex plugin, its documentation, and the
tooling used to validate a proposed change.

Use [GitHub Issues](https://github.com/wheakerd/axiom/issues) for ordinary bug
reports and feature requests. Follow [SECURITY.md](SECURITY.md) for potentially
sensitive findings; do not disclose vulnerability details in a public report.

## Repository layout

| Path | Ownership |
| --- | --- |
| [skills/](skills/) | Skill source installed by Codex, with supporting resources loaded on demand |
| [.codex-plugin/plugin.json](.codex-plugin/plugin.json) | Codex plugin manifest |
| [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json) | Codex marketplace wrapper |
| [hooks/](hooks/) | Codex startup Hook declaration and packaged wrappers |
| [README.md](README.md) | Product landing page and safe-start entry point |
| [docs/](docs/README.md) | Task navigation, user guides, concepts, references, and maintainer policy |
| [evidence/](evidence/) | Current identity and status, policy ledger, compatibility schemas, and runtime digest histories |
| [evals/](evals/README.md) | Versioned routing contracts, context budgets, and separately labeled host observations |
| [axiom_validation/](axiom_validation/) | Standard-library publication policy and installed-runtime input classification |
| [tests/](tests/) | Focused unit tests and isolated policy fixtures |
| [scripts/](scripts/) and [.github/workflows/](.github/workflows/) | Stable validation entrypoints and CI wiring |

Top-level Skills include the `using-axiom` startup gate and the workflows it
selects. A Skill's supporting references and agent resources are not separate
public routes. Repository validators, tests, and CI are contributor tooling;
they are not installed plugin dependencies or proof of host behavior.

## Before making a change

1. Inspect the worktree and preserve edits you did not create. Do not reset,
   stash, clean, stage, or rewrite unrelated work to make your change appear
   clean.
2. Identify the intended outcome and the owning surface: installed Skills and
   Hooks, the Codex package, documentation, or repository tooling.
3. Classify the change against
   [Runtime and Repository Identity](docs/runtime-identity.md#classify-a-change).
   An included runtime change must alter the digest and advance
   `pluginVersion`; a repository-only change appends
   `repositoryPolicyRevision` and must retain the digest.
4. Separate route selection from action authorization. Loading a Skill never
   grants permission to commit, push, deploy, delete, promote, read a secret,
   or mutate a remote system.
5. Keep the change within its stated scope and identify any routing or
   authorization impact before implementation.

## Choose the owning guidance

| Change | Read before editing |
| --- | --- |
| Skills, routing, always-loaded context, or Hooks | [Runtime Changes](docs/maintainers/runtime-changes.md) |
| Documentation, navigation, or public claims | [Documentation Policy](docs/maintainers/documentation-policy.md) |
| Repository validators, tests, or validation results | [Contributor Validation](docs/maintainers/validation.md) |
| Routing cases, benchmarks, or host evaluation records | [Routing Evaluations](evals/README.md) |
| Compatibility observations or evidence formats | [Field Validation](docs/field-validation.md) |
| Repository controls or release provenance | [Repository Governance](docs/repository-governance.md) |
| Changelog entries, version notes, or release evidence | [Release Documentation And Evidence](docs/maintainers/release-documentation.md) |

Keep public prose, examples, and trigger definitions in English. Use `Axiom`
for the brand and `axiom` for plugin, marketplace, route, path, and command
identifiers. Link to the canonical owner of a fact instead of maintaining a
second copy. The [documentation index](docs/README.md) provides task-oriented
navigation across these references.

Write current guides and references for the implementation in the same source
snapshot, and update them with the code or contract they explain. Put change
narratives in the Changelog or version notes. Preserve exact versions for
schemas, compatibility requirements, and historical evidence; source support
alone does not establish a published release or host observation. Follow the
[source and version rules](docs/maintainers/documentation-policy.md#source-and-version-scope)
when deciding whether a version belongs in current guidance.

## Routing evaluation contracts

[Routing Evaluations](evals/README.md) owns case versioning, benchmark
membership, bounded host runs, and append-only observation records. Follow
that contract before changing a case or collecting a result.

## Required local checks

Run the publication aggregate, full unit suite, and whitespace check listed in
[Contributor Validation](docs/maintainers/validation.md#required-checks), plus
any checks required for the changed surface. Record exact commands and
outcomes, review the final diff, and inspect the worktree for unrelated paths.
A missing tool or unobserved host result is unavailable or `NOT-RUN`, not a
passing result. Static checks do not establish installed-session behavior.

## Pull requests

Use the [pull-request template](.github/pull_request_template.md) and include:

- the intended outcome and exact affected files;
- which files are shared and which are Codex-specific;
- route-selection and action-authorization impact, including an explicit
  `none` when there is no impact, and any changed stop conditions;
- documentation changes or a reason none are needed;
- every validation command and its exact result, including unavailable
  optional host checks;
- a Codex behavior review when Skills or packaging changes; and
- confirmation that unrelated work was not reset, hidden, staged, or rewritten.

Do not mix opportunistic cleanup with the requested change. Do not commit
generated caches, disposable validation copies, local maintenance notes, or
tool output.

## Pull-request validation and release provenance

Contributor checks validate the proposed merge tree. They do not require a
GitHub-signed contributor commit or a same-repository head, establish release
provenance, or authorize publication. Review the separate
[pull-request and release trust boundaries](docs/repository-governance.md#pull-request-validation-and-release-provenance)
when a change affects CI or release controls.
