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

## Derived profile identity

The Hook-independent compatibility artifact has an independent identity stack;
none of its values replaces or reuses the installed full-profile digest:

- `profileRuntimeDigest` hashes the profile ID, runtime canonicalization
  version, behavior-bearing fields of the derived manifest, and the ordered
  path, kind, mode, size, and SHA-256 records for all 50 canonical Skill files.
  Source commit, repository policy, timestamps, ZIP metadata, and the bundle
  manifest itself are excluded, so identical runtime bytes retain one runtime
  identity across source commits.
- `bundleManifestDigest` hashes the complete canonical bundle manifest except
  only its own digest field. It binds the frozen Phase 1 contracts, ordered
  host case sets, source commit and tree, source and candidate policy revisions,
  derived manifest raw bytes, runtime records, builder dependency closure, and
  transport contract.
- `archiveSha256` hashes the final deterministic ZIP bytes. It is stored only
  in the external completion envelope and tracked static evidence, avoiding a
  self-reference in the archive.

Repository policy revision 6 owns the builder, closed schema, and static
evidence at
[`evidence/profiles/openai-hook-independent-v1/bundle-v1.json`](../evidence/profiles/openai-hook-independent-v1/bundle-v1.json).
Generated directories, ZIPs, and envelopes are temporary caller-owned outputs
outside the repository. Static construction does not establish Codex or
ChatGPT host acceptance and has no installation or publication effect.

Repository policy revision 7 owns the Codex no-Hook observation protocol,
source-bound JSONL taxonomy, guarded runner, deterministic fixture matrix,
prompt envelope, closed result schema, and empty result history. It also makes
the revision 6 bundle evidence valid under later append-only policy revisions:
the evidence finds its immutable owner revision uniquely instead of assuming
that owner is the latest record. Because the validator module is a bound
builder dependency, this maintenance refreshes `bundleManifestDigest` and
`archiveSha256`; revision 6 remains the artifact owner, and the 50-file runtime
payload and `profileRuntimeDigest` do not change. The protocol binds Codex CLI
0.153.0 and its binary identity for a future Linux observation, but the
runner's default validation path cannot make a model call. No credential was
used, no plugin was installed, and the Codex observation remains `NOT-RUN`.

The prompt-envelope and protocol digests use canonical JSON with sorted keys,
UTF-8 encoding, and no insignificant whitespace after excluding exactly their
own digest field. File bindings for the source-closed taxonomy, blinded model
response schema, fixture matrix, normalized result schema, runner entry point,
implementation, and fake process fixture hash their exact tracked bytes. Each
run additionally retains a public 256-bit materialization seed. From that seed,
the canonical ordinal, and the protocol digest, a verifier independently
derives each unretained opaque token and reconstructs the exact materialized
model schema and stdin prompt. Per-case canonical commitments bind those
identities to the canonical case, request, realized fixture, and logical file
set; an ordered commitment root binds all 16 cases. The empty result history
binds the protocol digest and reserves one canonical future result path; it is
not a placeholder observation.

The future Linux runner's registry-backed execution capability binds the exact
protocol, runner/module and Codex binary identities, source commit/tree, model,
reasoning effort, run-root identity, host, nonce, and irreversible 16-call
budget. A sole descriptor-pinned launcher consumes the ordered plan. The local
marketplace receipt must resolve to the already-held source object; the plugin
receipt must identify the exact
`plugins/cache/<marketplace>/<plugin>/<version>` object below the frozen Codex
home. Both are parsed as bounded complete JSON documents using the Codex
0.153.0 source shapes.
Run-root writes, model schemas, isolated homes, workspaces, accepted installed
copies, and cleanup stay anchored to held Linux descriptors and creation-time
object identities. Schema bytes reach the child only through an inherited
`/proc/self/fd` alias; installed-tree snapshots stay on the same held object.
Cleanup quarantines and deletes only ledger-owned objects, preserving unknown
replacements, while normalized output is created through a separately frozen
external parent descriptor. Any name or object substitution forces incomplete
status and manual cleanup rather than host PASS. Descriptor numbers, inodes,
procfs aliases, paths, and temporary names are runtime checks, not portable
evidence. Public JSONL does not expose Hook lifecycle telemetry; no-Hook proof
therefore belongs to package, installed-tree, temporary-config, and wrapper
absence facts rather than an event-count claim. All protocol validation remains
fake-only, and the Codex observation remains `NOT-RUN`.

Revision 7 binds the Linux helper and observer implementing the Combined
Group 1 + Group 2 offline lifecycle contract. Helper, observer, result schema,
and protocol bytes propagate through the runner bindings, result-schema hash,
protocolDigest, and empty result-history reference. Protocol-derived schema,
prompt, opaque bindings, and commitments are recomputed from that digest;
their frozen definition files remain unchanged. Revision 7 retains its revision
6 baseline and Issue 117 ownership; revisions 1 through 6 remain unchanged.
The revision 5 runtime source, revision 6 bundle-artifact owner, frozen bundle
format, and runtime payload remain unchanged. Explicit Git-reader working
directories change the builder dependency identity, bundleManifestDigest, and
archiveSha256; two local frozen-object builds must reproduce the new bytes.

Contract completion, deterministic simulation, and runtime observation are
separate facts. The closed result carries workload and control-resource counts,
a canonical scope prefix with closed component roles and phase records, a fixed
simulation source, and explicit not-verified runtime facts. Both complete and
incomplete counts are recomputed from those records and checked against case
and execution facts. Scope registration failures cannot reset the run or add
an unregistered scope. The 47
maximum workload domains are not the complete control inventory. A separate
supervisor process remains unimplemented and has zero recorded starts.
The existing Linux process-domain code is not a completed Combined backend.
Unified private filesystem and identity lifecycles, descendant coverage, and
runtime teardown still require separate implementation and validation. Earlier
partial process-domain checks do not establish complete Group 2 acceptance.
Default validation performs no capability detection. Actual execution remains
hard-disabled; FCR-001/003/004 are OPEN and FCR-002 is STILL OPEN. No current
host observation, release readiness, revision 8, or publication is created.

Construction binds one caller-supplied absolute Git executable, requires its
`--no-lazy-fetch` capability, and rechecks its physical identity around every
read-only invocation. Git receives a fixed environment allowlist rather than
the ambient process environment: model credentials, auth tokens, credential
helpers, real user homes, and XDG state cannot reach a builder child. Each
invocation uses both `--no-lazy-fetch` and `GIT_NO_LAZY_FETCH=1`, with
`GIT_PROTOCOL_FROM_USER=0`; a missing partial-clone or promisor object therefore
fails locally even if repository configuration allows a protocol-specific
remote helper. Git replacement objects, hooks, generic protocols, filesystem
monitoring, and ambient repository/object redirection are disabled or rejected.

Ordinary bundle output lifecycle version 2 replaces the revision 7 prototype's
creation-ledger deletion and quarantine paths. The v1 package, canonicalization,
manifest schema, frozen runtime source, and transport format are unchanged;
the builder implementation dependency binds this lifecycle change, so the
manifest and archive identities must be rebuilt. Existing v1 package bytes and
historical results are not reinterpreted as evidence of lifecycle 2.

The supported construction environment is Linux with directory-relative file
operations and a filesystem supporting anonymous `O_TMPFILE` creation and
no-overwrite linking of the prepared completion envelope. The caller provides
an existing empty external directory and prevents concurrent writes to that
directory and its descendants for the build. This is a use prerequisite, not
an exclusion mechanism enforced by the builder. The builder does not claim
protection against arbitrary same-identity processes concurrently changing
that namespace. Unsupported anonymous-file creation fails before visible
outputs are created; there is no unsafe pathname publication fallback.

The pathname API delegates to the directory-descriptor core. It constructs the
canonical `plugin/` tree and ZIP directly, without a staging tree. Exclusive
file creation retains the returned descriptor; successful creation attempts
are recorded before fallible binding registration. Directory bindings describe
objects opened under the single-writer prerequisite, not atomic creation proof.
No caller directory or named output is granted automatic deletion authority.
Normal completion closes handles and leaves only the intended products.
Failure preserves visible partial products and the original exception chain,
including creation progress and incomplete registration; it does not claim
that retained or unknown objects were removed. Recovery after failure requires
inspection and a new empty destination, not automatic reuse or deletion.

The completion envelope is fully prepared anonymously. Output validation,
source verification, record export, and necessary handle closure precede its
atomic no-overwrite publication; there is no fallible product validation after
that commit point. An absent envelope means the products are incomplete.
This is an in-process completion contract, not a power-loss durability claim.

Lifecycle 2 output bindings are explicitly refused by the disabled observer's
legacy creation-ownership admission. The internal worker receipt is version 2;
it cannot upgrade ordinary builder records into permission for observer cleanup.
The ordinary CLI does not require an observer supervisor. FCR-004's ordinary
name-based deletion path is removed; its earlier universal ownership claims
are superseded by this versioned support contract, not VERIFIED_FIXED. The
legacy observer's separate cleanup defect remains OPEN.

Git tree enumeration is a bounded pre-read gate rather than a buffered
post-read check. NUL-delimited records are consumed incrementally, with fixed
limits for each partial record, portable path, entry count, per-file declared
size, cumulative declared size, complete stdout, and stderr. The runtime tree
is also required to match its frozen 50-file, 230826-byte inventory before any
runtime blob is requested. A blob is read only after its tree-declared size has
passed the applicable limit: 256 KiB for runtime files and 512 KiB for profile
or support JSON. The reader consumes exactly that declared size and at most one
additional EOF-check byte; overflow terminates and reaps the Git process.

Runtime working-tree state is checked without `git status`. Python
`lstat`/`scandir` snapshots derive expected type and byte count from the bounded
Git entries, enforce per-file, aggregate, file-count, directory, and total-entry
limits, and reject unknown children during streaming enumeration. An opened
file must retain the same identity and size; at most the expected bytes plus one
EOF-check byte are read before its identity, size, exact blob bytes, and path
are rechecked. The snapshots run before and after construction, so
repository-local `core.fsmonitor`, PATH-shadowed `git`, lazy promisor helpers,
dirty or oversized files, and substituted paths cannot enter the runtime
payload. Runtime payload bytes themselves continue to come only from the
frozen commit's blobs.

Static-evidence replay applies the same resource discipline independently of
construction. After the closed manifest and its self-digest pass, its ordered
runtime records become a constrained expected child graph, not trusted input.
The replay validates the 50-file, 230826-byte inventory and the 128-file,
2 MiB safety ceilings before enumerating `skills/`; then it consumes each
`scandir` entry incrementally under explicit directory and total-entry limits.
An unknown child is rejected before its metadata or body is read. Expected
files must match their declared type, size, order, and SHA-256 and are read
through stable descriptors for at most the expected size plus one EOF-check
byte. Schema, evidence, Phase 1 contract, benchmark, Golden Set, response
schema, runtime identity, policy revision, and builder dependency files use
the same descriptor identity checks with an explicit per-input maximum rather
than `Path.read_bytes()`.

The package's logical mode contract is always `100644` for files and `040755`
for directories, including ZIP metadata. On POSIX, generated objects must also
have physical `0644`/`0755` modes. On Windows, the validator instead requires
ordinary files and directories, rejects symlinks and junction/reparse points,
and binds the exact paths and bytes; it does not claim that Windows ACLs or
mode emulation are a POSIX-mode observation. The destination must be an empty,
external directory under exclusive caller ownership for the duration of the
build. Concurrent same-user path substitution is outside this v1 construction
contract; if destination identity becomes uncertain, the caller must retain
the output for manual inspection rather than treat it as accepted evidence.

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

The native Codex observation v2 protocol is a repository-policy implementation,
not an installed-runtime change. It binds its CLI, implementation dependencies,
unchanged Phase 1 inputs, existing bundle identities, new prompt envelope, and
closed result schema. Changing those bytes changes its protocol digest and all
derived prompts, schemas, opaque bindings, and ordered commitments. A later
observation must identify the actual implementation used; an unmerged source
must not be described as a merged implementation.

The [v2 execution contract](field-validation.md#native-codex-no-hook-observation-v2)
replaces the unfinished v1 execution architecture for a bounded native-client
experiment. It binds standard user Skill discovery to the verified installed
package while disabling plugin runtime. The initial permission failure remains
historical; corrected no-model discovery and consumption checks passed. The v2
authentication contract now permits explicitly authorized opaque reuse of a
dedicated test login across separate case homes, with serial refresh handoff.
The protocol and result schema bind this mode; credential bytes are never
identity inputs. Official login status passed in all 16 dedicated homes after
authorized reuse. Implementation `f7a590ad58e2a1200f64009e48556fa7448f2f86`
then launched Case 1 once; its normalized result is INCOMPLETE with
`execution-failed` and no valid terminal response. Cases 2-16 remain NOT-RUN.
The v2 history binds that result to its unchanged execution protocol and inputs;
it does not establish a host PASS or a more specific failure cause. V1 artifacts
and historical failures are not reinterpreted. The
original Golden Set, model-response definition, fixture matrix, profile runtime,
full-profile runtime, bundle format, and ordinary builder lifecycle are unchanged.
The in-flight revision 7 owns this observer work; revision 5 still owns the
profile source and revision 6 still owns the derived bundle. No host claim is
created by maintaining a protocol or empty result history.

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
