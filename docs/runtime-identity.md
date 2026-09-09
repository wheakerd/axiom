# Runtime And Repository Identity

## Native diagnostic revision 6

Current protocol revision 6 records closed parser assertion codes/ordinals and
requires the last emitted response candidate to agree with the official private
final-output artifact before strict acceptance. Commentary is not itself a JSON
result. Temporary final output is removed after bounded extraction; no raw
message or diagnostic is added to public result fields.

The fifth user-provided fail-closed notice and frozen model catalog establish a
separate limitation: `gpt-5.6-sol` requests `CodeModeOnly`, which cannot use the
ordinary `CodeMode` Direct fallback when its host is disabled. Feature flags do
not override explicit model metadata. No permitted Direct path was established;
no host, model, sandbox, authentication or catalog setting was changed.
See the [source distinctions and parser migration](field-validation.md#native-tool-mode-diagnosis-and-final-response-correction).

All five historical INCOMPLETE results and their original identities remain
unchanged. Current history points to the new protocol while the fifth retained
result is accepted by its immutable historical hash and original binding only.
No new observation, preparation state or attempt exists. Canonical attempts and
CLI launches remain 5, all Case 1; internal model-request count is unknown and
Cases 2-16 are NOT-RUN. This revision's behavior has only no-model regression
evidence. The fifth exact parser assertion and stderr content remain unknown.

## Historical native response transport correction

Native diagnostic revision 5 preserves four immutable historical attempts and
allows one linked schema-correction followup (Case 1 at most five times; 20
cumulative attempts). Its outgoing schema is a typed Structured Outputs
representation; the frozen source definition remains the strict local result
validator, including route uniqueness. All 16 final derived files are checked.
See the [transport migration and user-provided fourth-error evidence](field-validation.md#historical-native-response-transport-correction).
This local preflight is not server acceptance or a completed host observation.


### Fifth actual attempt after the transport correction

Signed implementation `c3ce63d789394f60e93687ec34db05be199fbc19` (tree
`be21ad749edb25e4fb832bce7debe9e0fa75175b`) generated and checked all 16 actual
schema files before launching Case 1 once, its fifth attempt. The configured
client remained Codex 0.153.0, `gpt-5.6-sol / medium`, with fresh context and
standard user-Skill discovery from the bound package. The plugin runtime stayed
disabled. No model probe, fallback model, re-login or further case was started.

The client exited 0 and the receiver observed `turn.completed`, but the
normalized result is **INCOMPLETE**. First cause is `unknown-stderr` (94 bytes);
one pre-turn error item remained unclassified. Input delivery was complete,
with no timeout, observer termination or cleanup failure. Complete stream
validation failed, so no structured response or read-command facts were
accepted. The receiver's observed terminal event is distinct from the
`terminal=not-observed` field of the unsuccessful closed-stream parse.
Post-execution package, fixture, configuration and discovery checks passed.
These facts do not establish route acceptance or identify the new diagnostic
message, and are not relabeled as another `invalid_json_schema` failure.

Operator-only capture saved 197 bytes without truncation. Its original content
was not read, searched, hashed or uploaded by the executor. It remains available
only to the human operator in the dedicated continuation state. No stderr was
retained in that file. The four historical results retain their exact bytes and
original implementation/protocol bindings; the user-provided fourth diagnosis
is not applied to earlier or later attempts.

Result SHA-256:
`7edd7ab7068f85525074b10f874b325c066a35de183048b037f78f5a9286b018`.
Protocol digest:
`sha256:59170c119dca1de340c286c5502d2176c222deb0c34784b5c19d30cc091d4b6d`.
Cumulative attempts and canonical CLI launches are **5**, all Case 1;
Cases 2-16 remain **NOT-RUN**. Observable internal model-request count remains
unknown. No sixth Case 1 attempt is authorized. PR remains Draft and Issue #117
open; this result is not complete host acceptance or Combined validation.

## Historical operator-only diagnostic continuation

Native diagnostic revision 4 preserves all three historical Case 1 INCOMPLETE
results and their original implementation/protocol bindings. The separately
authorized `operator-diagnostic-continuation` ledger verifies those results,
markers and prepared inputs before deriving new inputs. It permits Case 1
attempt four, then Cases 2-16 once only after a complete valid first result and
reliable execution: at most 19 cumulative attempts, no automatic retry.
`--prepare-operator-diagnostics` starts no client; `--run --operator-diagnostics
--authorize-model-calls --reuse-test-auth` uses the same frozen model, package,
permissions and separate fresh case state. Preparation alone is not observation.

The human operator explicitly authorized local retention of only
`error.message`, `turn.failed.error.message`, and completed error-item messages.
These original strings are captured before classification in exclusive 0600
JSON-string files under the new ledger's 0700 `operator-only-diagnostics`
directory. The batch limit is 16 KiB including JSON framing: item notices use
at most 4 KiB, with 6 KiB reserved for each of top-level errors and turn failures.
Truncation and write failure are reported; capture cannot change a failure or
unknown diagnostic into PASS. Public results contain only closed capture status,
byte count and truncation metadata, never the original strings or private paths.

Only the human operator may read the actual files. Neither executing agent nor
subagent may read, search, hash, encode, upload or attach them. The files remain
outside model-readable sandbox roots, Git, validation copies, archives and CI.
Mode 0600 is not claimed to isolate another same-UID process; the executor's
no-read rule is an explicit operational boundary. No stderr, reasoning, agent
message, tool output, request body or authentication file is captured. This
narrow exception does not reinterpret the earlier discarded diagnostics.

### Fourth attempt as originally recorded

Implementation `23d2d9d3a2e98bc67e74cbcf865cb53a929202eb` (tree
`b7ba3d8383f0c25e1af0b76d52a0756bb1acc14b`) produced one new Case 1
**INCOMPLETE**: exit 1, top-level error and turn.failed, with complete input
delivery, a valid event stream and valid post-execution input checks. There was
no validated structured response, timeout, observer termination or cleanup
failure. Three pre-turn diagnostic items and unknown stderr were recorded only
as closed public facts. Their meaning is not inferred from earlier attempts.

The explicitly authorized human-only message file was saved: 1606 bytes,
not truncated, mode 0600 inside its private 0700 directory. The executor checked
only metadata and did not read, hash, attach or publish the original messages.
The file is retained for the human operator; its contents are not host PASS
or a diagnosis available to the executor. Cases 2-16 remain NOT-RUN.
Cumulative attempts and canonical CLI launches are four, all Case 1; internal
model request count is unknown. The three previous INCOMPLETE results and
bindings remain unchanged. This historical record did not authorize a fifth attempt.

## Historical native continuation after two attempts

Native v2 diagnostic revision 3 retains both historical Case 1 INCOMPLETE
results unchanged. An explicitly authorized `diagnostic-continuation` ledger
checks both result hashes, both attempt markers and both preparations before
rebinding derived inputs. It permits one further Case 1 attempt and each of
Cases 2-16 once: at most 18 cumulative attempts, including the two historical
attempts. It does not reset attempts or reuse an earlier conversation.
`--prepare-diagnostic-continuation` performs no client launch;
`--run --diagnostic-continuation --authorize-model-calls --reuse-test-auth
--private-diagnostics` uses the registered installations and serial test-auth
handoff. It never copies authentication into validation or evidence artifacts.

The optional private diagnostic summaries have a 16 KiB batch limit and 0600
files in a 0700 directory inside that ledger. They contain only frozen template
summaries and predeclared public fields; uncertain dynamic content is omitted.
They are not raw logs, public evidence or a claim that arbitrary text can be
made safe by regex. Unknown or condition-changing diagnostics remain INCOMPLETE.
Closed-stream, response-schema and post-execution input checks are recorded
separately so an incomplete attempt can retain independently validated partial
facts. Unperformed checks and unavailable model-request counts remain unknown.
These facts do not establish host PASS or validate the retired Combined path.

Earlier budget and retention descriptions below retain their historical scope.
The continuation executed implementation `07e92135a85523c774cc3cb32499be6d98eee31f`
(tree `82d09603eaa18acd415e8972729b5e429255781e`). Case 1 attempt three is
INCOMPLETE: the client reported `turn.failed` and exited 1 after receiving the
complete input. Stream validation and post-execution input checks passed; no
structured response was available. The observer neither timed out nor terminated
the client. Three pre-turn diagnostics and an upstream error were observed,
but the private finite-template summary could not safely classify their meaning.
The underlying host cause remains unknown; this is not a claim of unavailable
authentication, model service or an administrator restriction. Case 2-16 remained
NOT-RUN. The task has consumed three attempts and three CLI launches; observable
internal model-request count remains unknown. No fourth Case 1 attempt is allowed.

The normalized result SHA-256 is
`bfdd8b8569750d5797caf3e19c1e1acb55e190043b8dbdfdd2f48f47bd93fc79`.
Both earlier INCOMPLETE results keep their original bytes and implementation
bindings. This result does not validate the plugin runtime subsystem, the old
Combined backend or successful Skill discovery. The raw diagnostic content was
not retained, and no later inference is backfilled into it.

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
The v2 history preserves that exact result under `historicalResults`, with its
original execution protocol, implementation commit and result commit. Diagnostic
revision 1 adds safe capture facts and a separately authorized follow-up ledger;
new protocol inputs derive new schemas, prompts and commitments. Historical
bytes are checked against their frozen content identity rather than interpreted
under the new result schema. They do not establish a host PASS or a narrower
failure cause. The follow-up explicitly includes the earlier consumed attempt
in its cumulative budget; its result is separate evidence. The actual follow-up
against `039faf3cc46bebae6823dd21c01bf023d1e2d0e0` recorded a second Case 1
INCOMPLETE: an `error` item was rejected by observer policy. Its closed facts
retain the first cause and successful input delivery without raw messages.
Cumulative starts are two, Cases 2-16 remain NOT-RUN, and Case 1 has no remaining
authorized attempt. Both records keep their distinct implementation bindings. V1 artifacts
and historical failures are not reinterpreted. Diagnostic revision 2 preserves
both actual results as immutable historical bindings and has an empty current
history. Its error-item receiver, structural parser and result validator share
the frozen diagnostic shapes; finite classes are observer inferences, not
upstream codes. Implementation/schema changes update the protocol digest and
all derived input commitments, without changing attempt limits or rewriting
historical input identities. No new actual session validates revision 2. The
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
