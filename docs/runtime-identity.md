# Runtime And Repository Identity

Axiom separates installed plugin behavior from repository maintenance. The
[machine-readable identity](../evidence/runtime-identity.json) owns the current
version, policy revision, digest schema, digest, and input count. The README
renders those values; this page explains how to interpret them.

## Identity Fields

| Field | Meaning | Canonical source |
| --- | --- | --- |
| `pluginVersion` | Installed package version; a candidate label does not prove publication | [Codex manifest](../.codex-plugin/plugin.json) |
| `repositoryPolicyRevision` | Contiguous, append-only repository policy history | [Policy ledger](../evidence/repository-policy-revisions-v1.json) |
| `runtimeContractDigest` | Digest of classified installed behavior inputs under a named schema | [Runtime identity](../evidence/runtime-identity.json) |
| Release and host status | Immutable binding and observed compatibility, independently of version labels | [Release status](../evidence/release-status.json) |

A policy entry's `baselineCommit` identifies its observed starting point. It
does not claim that the baseline contains the later changes. Record a
`sourceIssue` only when an Issue actually owns the change; direct maintenance
requests may use `null`.

## Current Runtime Contract

The [schema v2 input policy](../axiom_validation/runtime-contract-inputs-v2.json)
classifies the current Codex package. It includes every file under `skills/`
and `hooks/`, plus the Codex manifest's `name`, `skills`, `hooks`,
`interface.capabilities`, and `interface.defaultPrompt` fields.

The policy excludes the manifest version, publisher and presentation fields,
the marketplace wrapper, and branding assets used only by excluded presentation
fields. These exclusions distinguish distribution and presentation from loaded
behavior; they do not exempt those files from package validation.

Future behavior-bearing assets, MCP or app declarations, settings, executables,
or component roots must be classified before shipping. If the existing policy
cannot represent them without changing its meaning, introduce a successor
schema rather than reinterpreting a historical digest.

### Reproducible Calculation

The standard-library generator rejects missing, duplicate, unordered, escaping,
symlinked, non-portable, or unclassified installed inputs. It sorts portable
POSIX paths by UTF-8 bytes, reads text as UTF-8, normalizes CRLF and bare CR to
LF, hashes each normalized input, and hashes canonical JSON records with
SHA-256. Selected manifest fields are JSON values rather than source formatting.
The input-policy digest also normalizes line endings before hashing its text.

File mode is not a digest input: current runtime text is read by the host or
an explicitly selected interpreter.
A future directly executed file whose mode affects behavior needs a successor
schema.

## Classify A Change

| Exact final change | Identity and completion path |
| --- | --- |
| Installed Skill, reference, hook, wrapper, or included manifest field | Change the digest and advance `pluginVersion` before release; follow package release verification |
| Repository-only documentation, CI, validator, governance, or evidence policy | Retain plugin version and runtime digest; append the next policy revision; complete through the signed merge and required checks |
| A mixture of both | Follow the installed-runtime path; repository-only files do not make the whole change policy-only |

A tree whose version already names an immutable tag must retain that version's
recorded runtime digest. New public capabilities use the next minor version;
compatible fixes use the next patch. An already assigned, uncreated candidate
remains the working version until completed. Preserve defective immutable tags
and fix forward instead of rewriting release history.

Advancing a version without changing the digest is normally rejected. The
explicit [v0.13.1 repository-tooling exception](releases/v0.13.1.md) is bound by
the validator to its exact predecessor, baseline, policy revision, and digest.
It creates no reusable exception for later versions and waives no verification.

A policy revision alone creates no package tag, GitHub Release, Latest change,
or marketplace publication. Classification does not authorize those actions.
The [release documentation contract](maintainers/release-documentation.md)
owns publication evidence; [Repository Governance](repository-governance.md)
records the dated server-side controls.

## Current Candidate And Host Evidence

Read [release status](../evidence/release-status.json) and
[Compatibility](compatibility.md) for the candidate and observation boundary.
A manifest version or matching digest proves neither installation nor
publication. An unchanged digest can identify unchanged bytes, but cannot
create a new observation or change a prior record's lifecycle or outcome.

An empty checked-in historical evidence list does not imply a pass or erase
archived failures. New observations bind their own immutable subject and follow
[Field Validation](field-validation.md).

## Historical Identities

- The [v2 history](../evidence/runtime-contract-history-v2.json) records
  immutable subjects under the current schema, beginning with the v0.10.1
  derivation used for the Codex-only transition.
- The [v1 policy](../axiom_validation/runtime-contract-inputs-v1.json) and
  [v1 history](../evidence/runtime-contract-history-v1.json) retain their
  original cross-host classification and bindings. Schema v2 retains their
  canonicalization, removes the retired Claude manifest input, and uses its
  own digest namespace.
- The [policy ledger](../evidence/repository-policy-revisions-v1.json) and
  [version notes](releases/) own revision-specific changes and migrations.
- Retired host snapshots and no-Hook experiments remain at the verified sources
  indexed by the [experiment archive](field-validation.md#archived-experiments).

A successor schema gets its own input policy and labeled history. Deriving
older immutable trees under it does not rewrite their earlier digests, release
notes, observations, or failures.
