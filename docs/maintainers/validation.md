# Contributor Validation

This guide owns contributor check commands, validation-tool structure, and the
limits of each result. Start with [CONTRIBUTING.md](../../CONTRIBUTING.md) for
scope, change classification, and the pull-request checklist.

Repository checks use Python's standard library. They are contributor tooling,
not dependencies of the installed Axiom plugin. Use a disposable repository
copy for any check that may write files; keep caches, temporary fixtures, and
tool output out of the contribution.

## Required Checks

Run these checks from the repository root and record exact commands and
outcomes:

```bash
python3 -B scripts/check-publication.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Use the host's equivalent Python 3 launcher when it has a different name. The
publication aggregate owns distribution agreement, runtime identity,
compatibility evidence, routing context, documentation, and publication
checks. Use focused scripts to diagnose a failing domain; a passing aggregate
does not require repeating those checks.

Run additional checks required by the changed surface, read the final diff,
confirm that the manifest version matches the release identity, and inspect
`git status --short` for unrelated paths. Classify every changed path under
[Runtime and Repository Identity](../runtime-identity.md#classify-a-change)
before calling the result repository-only.

| Changed surface | Additional acceptance owner |
| --- | --- |
| Skills, routing, or always-loaded context | [Runtime Changes](runtime-changes.md) and [Routing Context Budget](../../evals/context-budget/README.md) |
| Hooks or Hook workflows | [Hook runtime integration](#hook-runtime-integration) |
| Documentation or navigation | [Documentation Policy](documentation-policy.md#validation-expectations) |
| Routing contracts or host observations | [Routing Evaluations](../../evals/README.md) |
| Compatibility evidence | [Field Validation](../field-validation.md) |
| Release documents or provenance | [Release Documentation And Evidence](release-documentation.md) and [Repository Governance](../repository-governance.md) |

## Hook Runtime Integration

Hook or Hook-workflow changes require the dedicated native integration module
on every available target host:

```bash
python3 -B -m unittest tests.hook_runtime_integration -v
```

Run the module from a disposable repository copy. A Linux result proves only
Linux; report unavailable native Windows or macOS execution as `NOT-RUN`.
Static inspection, emulation, and a successful package read cannot replace a
native result.

The native matrix and its stable `hook-runtime-gate` aggregate are described in
[Repository Governance](../repository-governance.md#hook-runtime-promotion-gate).
That owner records required-check status and the dated remote observation.
The weekly scheduled run remains read-only compatibility evidence.

## Validation Tooling

[scripts/check-publication.py](../../scripts/check-publication.py) is the stable
aggregate entrypoint. Thin wrappers in [scripts/](../../scripts/) call
production parsers and policy gates in [axiom_validation/](../../axiom_validation/).
Reusable negative cases and mutation fixtures used by the aggregate live in
[axiom_validation/cases/](../../axiom_validation/cases/); the aggregate must
remain usable without importing the test package.

Focused `unittest` modules under [tests/](../../tests/) own domain-local
assertions. [tests/fixtures/](../../tests/fixtures/) holds test-specific
mutations and synthetic data, not all aggregate fixtures.

Keep fixture names in failure messages, and let the aggregate reporter add the
policy domain. Keep fixture payloads separate from production policy modules,
and do not add a third-party test or runtime dependency. Prefer focused,
standard-library-only validation when adding repository checks.

The aggregate summary's `immutable external action and image pins` total adds
one for each validated full-SHA GitHub Action, digest-pinned `docker://` action,
workflow job or service image, and digest-pinned remote Dockerfile source. Its
parenthetical breakdown reports remote `FROM` sources as `Dockerfile base-image
pins` and digest-pinned `COPY --from` or `RUN --mount=from` sources as `other
Dockerfile input pins`. `FROM scratch`, references to an already validated
local build stage, and validated action-local `COPY` or `ADD` sources are
accepted but do not increase either Dockerfile count.

The compatibility validator uses
[tests/fixtures/compatibility-v3.json](../../tests/fixtures/compatibility-v3.json)
for synthetic schema regression. A fixture is test data, never a host
observation. The [evidence inventory](../field-validation.md#evidence-directory)
owns format versions and runtime-history bindings; the
[experiment archive](../field-validation.md#archived-experiments) owns retired
observations and methods.

## Optional Native Package Inspection

A host-provided package validator or package read is an additional parsing
signal. Its absence does not turn the repository aggregate into a host
observation. Inspect the installed CLI's help before choosing a command; do not
assume that a `codex plugin validate` subcommand exists.

If a native validator is available, run it against a disposable copy when it
may write files. A bounded app-server `plugin/read` can check local package
discovery, but it is not a strict schema validator or an installed-session
test. Report the exact host version and only the components actually returned.
See [Compatibility](../compatibility.md#codex-package-format-and-validation)
for the supported package contract.

The repository aggregate owns Axiom's strict package checks. The retired
`plugin-creator` allowlist validator is not an optional diagnostic or fallback;
the [v0.13.0 migration notice](../releases/v0.13.0.md#retired-validator) records
its replacement. A missing tool is `unavailable`, not `passed`. Do not install,
update, or patch system tooling merely to satisfy a contribution check.

## Host Observations And Publication

Static validation, native parsing, installed-host observations, and independent
reproduction establish different facts. Use
[Field Validation](../field-validation.md#recording-a-result) for compatibility
records and [Routing Evaluations](../../evals/README.md) for bounded routing
runs. Preserve original subjects, outcomes, and unavailable cases; never
relabel earlier evidence as a new host, lifecycle, version, or date.

The checked-in release status remains `STATIC-ONLY`. A later observation is a
separate artifact bound to its immutable subject. Passing contributor checks
does not authorize tag creation or publication; those actions and their
evidence follow [Repository Governance](../repository-governance.md) and
[Release Documentation And Evidence](release-documentation.md).
