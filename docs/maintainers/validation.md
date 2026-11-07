# Contributor Validation

This guide owns contributor check commands, validation-tool structure, and the limits of each result. Start with [CONTRIBUTING.md](../../CONTRIBUTING.md) for scope, change classification, and the pull-request checklist.

Repository checks use Python's standard library. They are contributor tooling, not dependencies of the installed Axiom plugin. Use a disposable repository copy for any check that may write files; keep caches, temporary fixtures, and tool output out of the contribution.

## Required Checks

Provide Python 3, Node.js available as `node` on `PATH`, and Git. The [canonical CI environment](../repository-governance.md#repository-guards-canonical-environment) owns their current selections. The publication aggregate invokes Node.js to validate the exact JavaScript release-workflow guard.

A disposable Git copy must preserve the candidate's tracked-file inventory in its index; a filesystem-only copy may not.

Run these checks from the repository root and record exact commands and outcomes:

```bash
python3 -B scripts/check-publication.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Use the host's equivalent Python 3 launcher when it has a different name. The publication aggregate owns distribution agreement, runtime identity, the routing gate's byte ceiling, documentation, and publication checks. Use focused scripts to diagnose a failing domain; a passing aggregate does not require repeating those checks. The [Release pipeline](release-documentation.md#release-pipeline) runs the first two commands on the rehearsed catalog handoff before it creates a tag.

Run additional checks required by the changed surface, read the final diff, confirm that the manifest version matches the release identity, and inspect `git status --short` for unrelated paths. Classify every changed path under [Runtime Identity](../runtime-identity.md#classify-a-change) before calling the result repository-only.

| Changed surface | Additional acceptance owner |
| --- | --- |
| Skills, routing, or always-loaded context | [Runtime Changes](runtime-changes.md) |
| Hooks or Hook workflows | [Hook runtime integration](#hook-runtime-integration) |
| Documentation or navigation | [Documentation Policy](documentation-policy.md#validation-expectations) |
| Compatibility observations | [Compatibility](../compatibility.md#report-a-compatibility-result) |
| Release documents or provenance | [Release Documentation And Evidence](release-documentation.md) and [Repository Governance](../repository-governance.md) |

## Code Security Scanning

The [CodeQL workflow](../../.github/workflows/codeql.yml) analyzes Python and GitHub Actions with the `security-extended` query suite on pull requests to `main`, pushes to `main`, and manual dispatch. Actions use full commit pins; checkout credentials are not persisted. The analysis job can read source and upload security findings, but cannot push repository content.

Review findings in the repository's [code scanning results](https://github.com/wheakerd/axiom/security/code-scanning). A successful analysis run does not mean there are no findings. The README badge reports workflow status; code-scanning alerts and repository rules own any merge-blocking decision. This workflow does not scan Markdown instructions for prompt injection or establish installed-host behavior.

Configuration was checked against GitHub's [CodeQL workflow reference](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options) (`last_verified: 2026-10-11`). Remote execution and alert results require an actual GitHub Actions run; local publication checks validate the workflow's repository policy, not the CodeQL analysis itself.

## Hook Runtime Integration

Hook or Hook-workflow changes require the dedicated native integration module on at least one supported operating system:

```bash
python3 -B -m unittest tests.hook_runtime_integration -v
```

Run the module from a disposable repository copy. One local operating system is sufficient: the host tool owns hook triggering, and the required CI matrix runs the same module on Linux, Windows, and macOS, which covers each system's command variant. Static inspection, emulation, and a successful package read cannot replace a native result.

The native matrix and its stable `hook-runtime-gate` aggregate are described in [Repository Governance](../repository-governance.md#hook-runtime-gate). That page describes the gate's workflow conditions and the weekly scheduled run, which only reports drift.

## Validation Tooling

[scripts/check-publication.py](../../scripts/check-publication.py) is the stable aggregate entrypoint. Thin wrappers in [scripts/](../../scripts/) call production parsers and policy gates in [axiom_validation/](../../axiom_validation/). Reusable negative cases and mutation fixtures used by the aggregate live in [axiom_validation/cases/](../../axiom_validation/cases/); the aggregate must remain usable without importing the test package.

Focused `unittest` modules under [tests/](../../tests/) own domain-local assertions.

Tests pin fixture totals and invariants, not release facts. A total that grows with every release, such as the required public files, the Markdown files, or the installed-runtime inputs, comes from the same production owner the aggregate reports. A release that changes no validator behavior therefore needs no test edit; a lost fixture still fails.

The validators check structure, not wording: a skill's frontmatter, its references, its size, the manifests, the hooks, and the documentation links. They pin no sentence of a skill or a document and model no routing or gate decision, because each host's model decides how to act within the binding rules a skill states. The fixture tests in [tests/test_git_contracts.py](../../tests/test_git_contracts.py) run the Git procedures and configuration rules that `traceable-git-submit` documents against disposable repositories, so a documented command that stops working fails a test.

Keep fixture names in failure messages, and let the aggregate reporter add the policy domain. Keep fixture payloads separate from production policy modules, and do not add a third-party test or runtime dependency. Prefer focused validation using Python's standard library, without third-party Python packages; the host executable prerequisites above still apply.

The aggregate summary's `immutable external action and image pins` total adds one for each validated full-SHA GitHub Action, digest-pinned `docker://` action, workflow job or service image, and digest-pinned remote Dockerfile source. Its parenthetical breakdown reports remote `FROM` sources as `Dockerfile base-image pins` and digest-pinned `COPY --from` or `RUN --mount=from` sources as `other Dockerfile input pins`. `FROM scratch`, references to an already validated local build stage, and validated action-local `COPY` or `ADD` sources are accepted but do not increase either Dockerfile count.

A fixture is test data, never a host observation.

## Optional Native Package Inspection

A host-provided package validator or package read is an additional parsing signal. Its absence does not turn the repository aggregate into a host observation. Inspect the installed CLI's help before choosing a command; do not assume that a `codex plugin validate` subcommand exists.

If a native validator is available, run it against a disposable copy when it may write files. A bounded app-server `plugin/read` can check local package discovery, but it is not a strict schema validator or an installed-session test. Report the exact host version and only the components actually returned. See [Compatibility](../compatibility.md#codex-package-format-and-validation) for the supported package contract.

When Claude Code is installed, run its strict validator from a disposable copy:

```bash
claude plugin validate --strict .
```

It checks the Claude Code manifest and shared Skill metadata against the installed Claude Code version; record that version with the result. It does not install the plugin or run its Hook. See [Compatibility](../compatibility.md#claude-code-package-format-and-validation).

The repository aggregate owns Axiom's strict package checks. A missing tool is `unavailable`, not `passed`. Do not install, update, or patch system tooling merely to satisfy a contribution check.

## Host Observations And Publication

Static validation and native parsing check structure; they do not establish how a host's model behaves, and the repository measures no host model behavior for a release. Use [Report A Compatibility Result](../compatibility.md#report-a-compatibility-result) to report an observation of an installed host. Never relabel earlier evidence as a new host, lifecycle, version, or date.

The checked-in runtime identity binds the tree to its version and installed-file digest and never records publication or an observation. The Release pipeline requires no observation record for any release candidate. Passing contributor checks does not authorize tag creation or publication; only a merged release pull request starts the Release pipeline, and its actions and evidence follow [Repository Governance](../repository-governance.md) and [Release Documentation And Evidence](release-documentation.md).
