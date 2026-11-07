# Runtime Identity

Axiom separates installed plugin behavior from repository maintenance. A release's identity is its tag `v<version>` and the runtime digest of its installed tree. The Release workflow computes that digest from the tagged tree and records it in the Release's evidence asset; this page explains the method and how to classify a change.

## Identity Fields

| Field | Meaning | Where it is recorded |
| --- | --- | --- |
| Version | Installed package version, named by the release tag and stamped into both plugin manifests on the `release` branch | The tag `v<version>` and the `release` branch manifests |
| `runtimeContract.digest` | Digest of the classified installed behavior inputs under a named schema | The `axiom-v<version>-release-evidence-<sha256>.json` asset of each [GitHub Release](https://github.com/wheakerd/axiom/releases) |

Derive the digest of any tree with `python3 -B .ci/scripts/check-runtime-identity.py --digest-root <tree>`, for example a checkout of `main` or of a release tag. `--check` requires the input policy to classify every installed file of the current tree.

## Current Runtime Contract

The [schema v4 input policy](../../.ci/axiom_validation/runtime-contract-inputs-v4.json) classifies the installed `plugin/` subtree for both hosts. It includes every file under `plugin/skills/` and `plugin/hooks/`, the Codex manifest's `name`, `skills`, `hooks`, `interface.capabilities`, and `interface.defaultPrompt` fields, and the Claude Code manifest's `name`, `skills`, and `hooks` fields.

The policy excludes manifest versions, publisher and presentation fields, the license copy, and branding assets used only by excluded presentation fields. Both marketplace catalogs lie outside the installed subtree. These exclusions distinguish distribution and presentation from loaded behavior; they do not exempt those files from package validation.

Future behavior-bearing assets, MCP or app declarations, settings, executables, or component roots must be classified before shipping. If the existing policy cannot represent them without changing its meaning, introduce a successor schema with its own input policy rather than reinterpreting an earlier digest.

### Reproducible Calculation

The standard-library generator rejects missing, duplicate, unordered, escaping, symlinked, non-portable, or unclassified installed inputs. It sorts portable POSIX paths by UTF-8 bytes, reads text as UTF-8, normalizes CRLF and bare CR to LF, hashes each normalized input, and hashes canonical JSON records with SHA-256. Selected manifest fields are JSON values rather than source formatting. The input-policy digest also normalizes line endings before hashing its text.

File mode is not a digest input: current runtime text is read by the host or an explicitly selected interpreter. A future directly executed file whose mode affects behavior needs a successor schema.

## Classify A Change

| Exact final change | Identity and completion path |
| --- | --- |
| Installed Skill, reference, hook, wrapper, or included manifest field | Changes the digest; release it by tagging the next version after the merge |
| Repository-only documentation, CI, validator, governance, or evidence policy | Keeps the digest; complete through the signed merge and required checks, with no tag |
| A mixture of both | Follow the installed-runtime path; repository-only files do not make the whole change policy-only |

A published tag's digest is fixed in its evidence asset. Preserve defective immutable tags and fix forward with the next version instead of rewriting release history.

### Version Increment

Classification selects the path; the exact diff since the previous release selects the increment. Labels, Issue titles, and planned files do not. Classify the tagged tree before choosing the version.

| Exact final installed-runtime change | Increment |
| --- | --- |
| A new Skill, route, mode, trigger, or Hook event; matching widened to requests a route did not select before; a new protocol, storage location, or evidence format; a packaging or layout change that alters the installed path or requires user action; deprecation or removal of a route | Next minor version |
| A fix without new capability: narrowing a wrongly selected route, wording or reference corrections, Hook defect fixes, size or security hardening, routing fixes | Next patch version |
| Repository-only documentation, CI, validators, evidence, governance, README, marketplace catalogs, release scripts, or this standard | No version change |

The major version stays `0` until a separate maintainer decision declares the 1.0 criteria. Before 1.0, a change that breaks a documented invocation advances the minor version and states its migration in the release notes.

### Bundling

- One release carries one coherent change set of one identity class whose acceptance fits one tagged tree. Items that change the same Skill or depend on each other ship together.
- A fix for a defect in a published release ships as a patch from `main` before an in-progress minor release is tagged; the minor release then builds on that patch.
- A new Skill ships in its own minor release unless it depends on a redesign in the same cycle. Independent new capabilities share one minor release only when each has passed its own acceptance and the routing-gate review covers both.
- Use the immediate next version in SemVer order; never skip or reorder.
- Every release requires the validated tagged tree and the always-loaded context review in [Runtime Changes](maintainers/runtime-changes.md#always-loaded-context) when the routing gate grows.

A release changes the installed files. The Release workflow rejects a tag whose runtime digest equals the one recorded in the Latest release's evidence asset, except for the [bootstrap release](maintainers/release-documentation.md#what-ci-does) that first creates the `release` branch. When Latest's evidence asset records no digest, the workflow computes Latest's digest with the same generator on Latest's tagged tree.

A repository-only change creates no package tag, GitHub Release, Latest change, or marketplace publication. Classification does not authorize those actions. The [release documentation contract](maintainers/release-documentation.md) owns publication evidence; [Repository Governance](repository-governance.md) records the server-side controls.

## What The Identity Does Not Prove

A version or matching digest proves neither installation nor publication; the tag, the GitHub Release, and the `release` branch are the publication state. An unchanged digest identifies unchanged bytes and creates no host observation. See [Compatibility](compatibility.md) for the support boundary and for [reporting a host result](compatibility.md#report-a-compatibility-result).
