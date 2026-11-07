# Runtime Identity

Axiom separates installed plugin behavior from repository maintenance. The [machine-readable identity](../.ci/runtime-identity.json) owns the current version, digest schema, digest, and input count. This page renders the current identity and explains how to interpret it.

## Current Identity

<!-- runtime-identity:current:start -->
- `pluginVersion`: `0.27.6`
- `runtimeContractDigest` (schema v4): `sha256:694996fb0892ffdde7842878c568de4900e5f8e0a034316133b50da34f4b8234`
- Digest input manifest: [`.ci/axiom_validation/runtime-contract-inputs-v4.json`](../.ci/axiom_validation/runtime-contract-inputs-v4.json)
<!-- runtime-identity:current:end -->

## Identity Fields

| Field | Meaning | Canonical source |
| --- | --- | --- |
| `pluginVersion` | Installed package version; a candidate label does not prove publication | [Codex manifest](../plugin/.codex-plugin/plugin.json) |
| `runtimeContractDigest` | Digest of classified installed behavior inputs under a named schema | [Runtime identity](../.ci/runtime-identity.json) |

## Current Runtime Contract

The [schema v4 input policy](../.ci/axiom_validation/runtime-contract-inputs-v4.json) classifies the installed `plugin/` subtree for both hosts. It includes every file under `plugin/skills/` and `plugin/hooks/`, the Codex manifest's `name`, `skills`, `hooks`, `interface.capabilities`, and `interface.defaultPrompt` fields, and the Claude Code manifest's `name`, `skills`, and `hooks` fields.

The policy excludes manifest versions, publisher and presentation fields, the license copy, and branding assets used only by excluded presentation fields. Both marketplace catalogs lie outside the installed subtree. These exclusions distinguish distribution and presentation from loaded behavior; they do not exempt those files from package validation.

Future behavior-bearing assets, MCP or app declarations, settings, executables, or component roots must be classified before shipping. If the existing policy cannot represent them without changing its meaning, introduce a successor schema with its own input policy rather than reinterpreting an earlier digest.

### Reproducible Calculation

The standard-library generator rejects missing, duplicate, unordered, escaping, symlinked, non-portable, or unclassified installed inputs. It sorts portable POSIX paths by UTF-8 bytes, reads text as UTF-8, normalizes CRLF and bare CR to LF, hashes each normalized input, and hashes canonical JSON records with SHA-256. Selected manifest fields are JSON values rather than source formatting. The input-policy digest also normalizes line endings before hashing its text.

File mode is not a digest input: current runtime text is read by the host or an explicitly selected interpreter. A future directly executed file whose mode affects behavior needs a successor schema.

## Classify A Change

| Exact final change | Identity and completion path |
| --- | --- |
| Installed Skill, reference, hook, wrapper, or included manifest field | Change the digest and advance `pluginVersion` before release; follow package release verification |
| Repository-only documentation, CI, validator, governance, or evidence policy | Retain plugin version and runtime digest; complete through the signed merge and required checks |
| A mixture of both | Follow the installed-runtime path; repository-only files do not make the whole change policy-only |

A tree whose version already names an immutable tag must retain that version's recorded runtime digest. An already assigned, uncreated candidate remains the working version until completed. Preserve defective immutable tags and fix forward instead of rewriting release history.

### Version Increment

Classification selects the path; the exact final diff selects the increment. Labels, Issue titles, and planned files do not. Reclassify the final candidate tree before assigning a version.

| Exact final installed-runtime change | Increment |
| --- | --- |
| A new Skill, route, mode, trigger, or Hook event; matching widened to requests a route did not select before; a new protocol, storage location, or evidence format; a packaging or layout change that alters the installed path or requires user action; deprecation or removal of a route | Next minor version |
| A fix without new capability: narrowing a wrongly selected route, wording or reference corrections, Hook defect fixes, size or security hardening, routing fixes | Next patch version |
| Repository-only documentation, CI, validators, evidence, governance, README, marketplace catalogs, release scripts, or this standard | No version change |

The major version stays `0` until a separate maintainer decision declares the 1.0 criteria. Before 1.0, a change that breaks a documented invocation advances the minor version and states its migration in the Changelog.

### Bundling

- One release carries one coherent change set of one identity class whose acceptance fits one candidate tree. Items that change the same Skill or depend on each other ship together.
- A fix for a defect in a published release ships as a patch from `main` before an in-progress minor release continues; the minor candidate then rebuilds on that patch.
- A new Skill ships in its own minor release unless it depends on a redesign in the same cycle. Independent new capabilities share one minor release only when each has passed its own acceptance and the routing-gate review covers both.
- Use the immediate next version in SemVer order; never skip or reorder.
- Every release requires the validated candidate tree and the always-loaded context review in [Runtime Changes](maintainers/runtime-changes.md#always-loaded-context) when the routing gate grows.

A release changes the installed files. The Release pipeline's candidate check rejects a pull request that advances the plugin version while its runtime digest equals its base's.

A repository-only change creates no package tag, GitHub Release, Latest change, or marketplace publication. Classification does not authorize those actions. The [release documentation contract](maintainers/release-documentation.md) owns publication evidence; [Repository Governance](repository-governance.md) records the server-side controls.

## What The Identity Does Not Prove

A manifest version or matching digest proves neither installation nor publication; the tag, the GitHub Release, and the marketplace catalogs are the publication state. An unchanged digest identifies unchanged bytes and creates no host observation. See [Compatibility](compatibility.md) for the support boundary and for [reporting a host result](compatibility.md#report-a-compatibility-result).
