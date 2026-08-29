# Runtime And Repository Identity

Axiom gives three different subjects three different identities:

| Identity | Subject | Changes when |
| --- | --- | --- |
| `pluginVersion` | The package users install | Released Skills, hooks, wrappers, host component paths, route contracts, action authority, or another included runtime surface changes |
| `repositoryPolicyRevision` | Repository governance and validation state | CI, validators, release automation, governance documentation, or evidence policy changes without changing the installed runtime |
| `runtimeContractDigest` | The exact installed behavior contract under one input schema | Any included runtime input or the input schema version changes |

The current machine-readable identities are in
[`evidence/runtime-identity.json`](../evidence/runtime-identity.json). Repository
policy revisions are append-only in
[`evidence/repository-policy-revisions-v1.json`](../evidence/repository-policy-revisions-v1.json).

## Runtime Contract V1

[`runtime-contract-inputs-v1.json`](../axiom_validation/runtime-contract-inputs-v1.json)
is the complete v1 classification of installed package surfaces. It includes:

- every file below `skills/`;
- every hook declaration and command wrapper below `hooks/`;
- `name`, `skills`, and `hooks` from both host manifests; and
- Codex capability and starter-prompt fields that affect the installed host
  contract.

It explicitly excludes:

- both manifest `version` fields, so `pluginVersion` is an identity bound to the
  digest rather than an input that changes it;
- publisher, discovery, and presentation fields;
- marketplace wrappers, whose policy belongs to distribution and installation;
  and
- the current branding assets, because they are referenced only by excluded
  presentation fields.

Any future behavior-bearing asset, MCP declaration, app mapping, default
setting, agent directory, command directory, executable, or other installed
surface must be classified before it can ship. If its canonicalization cannot
be expressed without changing v1 semantics, create a successor input schema;
do not reinterpret v1.

The standard-library generator rejects missing, duplicated, unordered,
escaping, symlinked, non-portable, or unclassified installed inputs. It sorts
portable POSIX paths by their UTF-8 bytes, decodes text as UTF-8, normalizes
CRLF and bare CR to LF, hashes each normalized input, and hashes one canonical
JSON record set with SHA-256. JSON manifest fields are canonical values rather
than source formatting. This makes the identity reproducible across supported
operating systems without treating checkout line-ending policy as behavior.
The input-manifest SHA-256 binding likewise normalizes checkout line endings
before hashing the otherwise exact UTF-8 policy document.

File mode is not a v1 input because the current runtime surfaces are text read
by a host or an explicitly selected command interpreter. Adding a directly
executed file whose mode is semantic requires a successor schema.

## Version Policy

An installed-runtime change must change `runtimeContractDigest` and advance
`pluginVersion` before release. A current tree whose version still names an
immutable tag must have that tag's exact digest. Advancing `pluginVersion`
without changing the digest is rejected for new candidates; use a new
`repositoryPolicyRevision` instead.

A repository-policy-only change appends the next contiguous policy revision,
retains `pluginVersion`, and must leave the runtime digest unchanged. Its signed
merge commit and required checks are the durable repository record. It does not
create a GitHub Release by default. GitHub Releases remain installed-package
releases and therefore follow `pluginVersion`.

A release-infrastructure security fix follows the same rule: unchanged runtime
inputs mean a policy revision, while any fix users must receive in an installed
Skill, hook, wrapper, route, or behavior-relevant manifest field requires a new
plugin version.

The existing release workflows, tag grammar, release-evidence validator, and
publication scripts remain the stable publication entrypoints. This identity
model narrows when they are used; it does not replace their signing,
attestation, immutable-tag, Latest, or recovery contracts.

## Marketplace And Host Constraint

This policy was checked against the official host documentation on
2026-08-29:

- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
  defines `version` as plugin identity, distinguishes component pointers from
  publisher and install-surface metadata, and treats repo/personal marketplaces
  as separate authoring and distribution sources. It does not require a plugin
  release for a repository-only governance commit.
- [Claude Code marketplace version management](https://code.claude.com/docs/en/plugin-marketplaces#version-resolution-and-release-channels)
  states that an explicit manifest version controls the cache and update
  signal. Keeping it unchanged intentionally prevents users from receiving a
  new installed copy when only repository policy changed.

No public marketplace publication is performed for a policy-only revision.
Before a future marketplace or host changes this constraint, verify the then-
current official behavior in that publication phase. Do not convert an
undocumented portal assumption into a version bump or a compatibility claim.

## Historical Derivation

[`runtime-contract-history-v1.json`](../evidence/runtime-contract-history-v1.json)
applies the v1 schema to immutable tag trees without rewriting those tags,
Releases, notes, host records, or prior failures. The history proves that the
installed Windows hook change from v0.8.14 to v0.8.15 changes the digest, while
the repository-only v0.8.16 and v0.8.17 changes do not. Later recorded
repository-policy releases through v0.8.20 retain that same digest.

A successor digest schema receives a new manifest and history file. Historical
digests are derived again under the new schema and labeled with that schema;
the v1 history remains append-only evidence of the v1 calculation.

## Host Evidence

New host observations use `evidence/schema-v2.json` and bind:

- `pluginVersion` and `runtimeContractDigest`;
- exact host identity and version;
- lifecycle source for each observed case;
- the observation subject; and
- the original observation timestamp.

An identical digest may make a prior observation applicable to the same
runtime contract, but it never changes that observation's host, version, date,
or lifecycle. Reuse is a reference to prior evidence, not a new run. The
machine-readable release status keeps `NOT-RUN` and `UNAVAILABLE` current-host
states separate from any prior record.
