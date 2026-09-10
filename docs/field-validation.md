# Field Validation

## Current assessment and historical boundaries

The unpublished 0.10.1 runtime candidate retains its original input view:
eight PASS, one FAIL, two INCOMPLETE and five NOT-RUN cases. The new material-input
segment separately observed Cases 10-16: three PASS and four semantic FAIL;
Cases 1-9 are NOT-RUN under these new inputs. Lifetime attempts and canonical CLI
launches are now 38. The seven authorized new attempts are consumed; there is
no further start or retry authority. Host acceptance remains incomplete and no
historical segment is regraded or combined into a sixteen-case PASS.

See [Canonical assessment candidate 0.10.1](#canonical-assessment-candidate-0101),
[Actual assessment batch and remaining evidence](#actual-assessment-batch-and-remaining-evidence),
[Material-location delivery correction](#material-location-delivery-correction),
[Actual material-input segment evidence](#actual-material-input-segment-evidence),
and [Assessment field clarification](#assessment-field-clarification-revision-3-not-observed).
Older sections retain their original identities, counts and outcomes. Their
use of "current" describes the execution at that time, not the new input
revision. No historical failure is reclassified. Assessment revision 3 clarifies the
measurement fields only; it has no host observations and its execution window
is closed.

## Historical reviewed continuation outcome (0.10.0)

Execution `04c7de8e972d64e1d15d4d40eb0a7081dca23407`, tree
`0a9ce3fba5914684abf6cfe9e7dad3c851a143ad`, used protocol
`sha256:1938bd1e4335e35a9f0d46bf113777e8eb542c7219338d7683a6d0507854c70c`.
The current normalized result is `e6c19c4324da9a40c074f2c0503a4b58a08fd6df6e58f747c7e41ba59248e64d`.
Only Cases 7-13 started under this implementation. Original Cases 1-5 remain
bound to `7c4c2c8a`; Case 6 remains bound to `92e8e435`. Their exact partial
results and the two source-bound, operator-supplied catalog reviews remain
separate records. No old INCOMPLETE status was changed to PASS.

| Cases | Recorded outcome | Evidence and limit |
| --- | --- | --- |
| 1-4 | PASS | Fixed response/routing acceptance; original execution |
| 5-6 | INCOMPLETE | Original unknown stderr retained; separate same-attempt reviews permit continuation only |
| 7 | FAIL | Valid response, semantic mismatch; no retry |
| 8-10 | PASS | Fixed response/routing acceptance; current execution |
| 11 | FAIL | Zero Axiom installation/discovery control, but response selected Axiom routes |
| 12 | FAIL | Valid response, semantic mismatch; no retry |
| 13 | INCOMPLETE | First rejection `read-target-unbound`, event ordinal 7; observer terminated the process |
| 14-16 | NOT-RUN | Batch stopped after Case 13; no further model launch |

There are seven PASS, three FAIL, three INCOMPLETE and three NOT-RUN records
in the preserved 16-case view. Lifetime attempts and CLI launches are 20:
seven historical Case 1 attempts plus thirteen in this batch. Case 1 has used
all eight lifetime starts; Cases 2-13 each started once. Internal model request
counts remain unknown. No retries, probes, model changes or budget refunds occurred.

Case 13 retained complete input delivery and valid non-sensitive postchecks.
The first unbound-target rejection was preserved at event 7, followed by
observer termination (exit -9, signal 9); timeout and cleanup failure were false.
No terminal or validated final response was obtained. The target and original
command are not retained, so no specific alias or command defect is inferred
and no unbound object was read to diagnose it. Its default zero read count is
not proof that no read occurred. This policy rejection is ineligible for the
unknown-stderr-only supplemental review path.

Case 8's complete stream contains one contract-verified read command. The
normalized count does not identify whether it read a Skill or a fixture;
Skill body consumption is therefore not established. Other complete streams
contain no command item. Model-reported routes and permission fields are not
observer proof of body consumption or all invisible actions. Verified package
and standard user-Skill discovery bindings remain separate facts. Case 11 had
no Axiom installation/discovery path. The plugin runtime stayed disabled.

The exact frozen catalog-timeout stderr template was classified only in new
execution; additional or different stderr remains unknown. All input, terminal,
response, fixed-model, final-output and postcheck requirements still apply.
Original Case 5/6 diagnostics are unchanged. Operator-only raw files remain
private and were not read by the executor or included in public evidence.

The overall result remains INCOMPLETE with `hostClaim=false`. Seven historical
failures remain immutable. FCR-001/003/004 remain OPEN; FCR-002 remains STILL_OPEN.
No full host acceptance, descendant closure or legacy Combined completion is
claimed. The PR remains Draft and the Issue open. Builder, bundle, runtime,
Phase 1 inputs and the 266-character reason are unchanged; no bundle was rebuilt.

## Reviewed remainder execution

Execution `92e8e435d3c39041ff2c86a0fa8c039c4996a121` used protocol
`sha256:795610bb36b81bed4d52aa887b055de94de964b9167c7ee7437982ed2544e551`.
Only Case 6 started, once; it is INCOMPLETE because of new unknown stderr.
It retained full input, a valid closed stream and strict response, official
final-output agreement and a valid postcheck, with no policy rejection,
termination, timeout or cleanup failure. Its validated route response selects
`traceable-git-submit`; that response alone is not body-consumption evidence.
No command item appeared in the closed stream. No later case started.

The result preserves original Cases 1-5 and references their earlier execution
separately. Cases 1-4 remain PASS; Case 5 remains INCOMPLETE with a separate
same-attempt catalog review. At capture Case 6 required its own human stderr explanation; equal byte length
did not identify its message. The operator subsequently supplied the same exact
catalog-timeout explanation. A separate Case 6 supplement now permits only
Cases 7-16, preserving both original INCOMPLETE records and both executions. Its operator file is private,
158 bytes per case, UTF-8 and untruncated; inherited stderr use is 316 bytes. The executor has not read its contents.
Cumulative attempts and CLI launches are 13: seven historical plus six in this
batch. Internal model-request count is unknown; Cases 7-16 remain NOT-RUN.
Host claim remains false. No repeated case, model probe or retry occurred.


## Same-attempt catalog diagnostic supplement

The operator supplied the Case 5 stderr message: the frozen client reported a
model-catalog refresh timeout. The [specific review](../evals/no-hook-observation/case-05-catalog-review-v2.json)
binds that report to the immutable partial result. Frozen source maps the
five-second asynchronous catalog timeout to a generic error whose display
mentions a child process; the message alone does not establish a residual child.
Case 5 retained a valid response and postcheck, with gpt-5.5 / medium and Direct
before and after. Its original INCOMPLETE record is unchanged; the supplement
permits only the unstarted Cases 6-16, without claiming Skill body consumption.

The same ledger now requires a separate exclusive remainder marker and
preparation. Original Cases 1-5 keep their original implementation, protocol and
input bindings. New cases use the new implementation and derived inputs; the
result identifies both segments. Prior stderr storage counts against the same
16 KiB budget, without reading operator-only content. No consumed attempt is
refunded. Seven historical failures and the partial result remain immutable.


## Seven-history batch outcome (diagnostic revision 10)

Execution `7c4c2c8aa01cde728976d1047e8801852a7e2485`, tree
`fcd7e72c576321b77742ba5d341f66ef817682f7`, used protocol
`sha256:5ce454ebaf368fd11884f3e91c50bd7ecbcc2d755b21ce0554fe786db94e3a97`.
The [unaltered normalized result](../evals/no-hook-observation/results/codex-native-ccf99c208c1131e6fb9c31d65077138602dd7abc5f803bd50c0bdcaea783dd4b.json)
is INCOMPLETE. Cases 1-4 passed the fixed routing/response acceptance; Case 5
is INCOMPLETE with `unknown-stderr`; Cases 6-16 were not started.

This batch made five attempts and five CLI launches. Lifetime totals are 12,
including all seven historical INCOMPLETE attempts. Case 1 used its eighth and
final allowance; Cases 2-5 used their sole allowance. Internal model request
counts remain unknown. No retry, probe or fallback was used.

For Cases 1-5, input delivery, strict stream, official final output agreement,
and non-sensitive input/configuration postchecks were valid. All exited 0 with
`turn.completed`, no policy rejection, timeout, observer termination or cleanup
failure. Case 5 alone produced 143 bytes of unclassified stderr; its 158-byte
UTF-8 JSON capture was saved privately without truncation (0600 file, 0700
directory). Only the human operator may read it. No JSONL error diagnostic was
emitted. This meets the recorded same-attempt review eligibility conditions,
but is not approval of the unseen diagnostic or authority to restart a case.
The existing batch and attempt markers remain consumed; any permitted later
continuation must preserve this original result and append its review source.

No command-execution item was observed in these five complete streams. Their
zero verified read counts do not establish Skill-body consumption, nor prove
absence of invisible actions. The package/discovery configuration and input
postchecks establish the installed source; route names and model-reported
permission fields are separate evidence. The plugin runtime was disabled and
normal user Skill discovery was used. Case 11's zero-installation/discovery
precheck remains intact, but its actual observation is NOT-RUN.

Seven historical files and their original protocols are unchanged, including
the seventh unknown read predicate. FCR-001/003/004 remain OPEN and FCR-002
STILL_OPEN. Complete host acceptance, descendant closure and the legacy
Combined implementation remain unproven. The Draft PR and open Issue are not
ready for merge or completion. Builder, bundle, runtime, frozen cases and the
266-character release-status reason are unchanged; no bundle was rebuilt.

## Seven-history continuation (diagnostic revision 10)

One explicitly authorized continuation preserves all seven original results and
attempt markers. It permits Case 1 once more (eight lifetime starts) and each
unstarted Case 2-16 once, for at most 23 lifetime attempts. The exclusive
`read-contract-continuation` ledger binds the current implementation and all
16 regenerated inputs before any client starts; consumed attempts are not
refunded. Codex 0.153.0, gpt-5.5 / medium, Direct tools, the installed package,
Case 11's absent discovery, and the revision 9 read predicates are unchanged.

The same-attempt human review applies only to this continuation when unknown
stderr is the sole failure and every recorded eligibility condition passes.
It cannot supply missing Skill-body consumption or invisible permission facts.
The seventh policy rejection is ineligible and its exact predicate remains
unknown. Operator-only raw diagnostic and stderr files remain private to the
human operator; they are excluded from executor/model reads, Git and CI.

## Read rejection preservation (diagnostic revision 9)

The shared production reader now reports the actual rejecting predicate through
`inspect_native_event`, the streaming receiver, strict JSONL parsing, and the
normalized result validator. `streamAssertion` and `streamEventOrdinal` retain
the first code and its one-based event location. `event-shape` means malformed
fields or types; unsupported events/items and content lifecycle have separate
codes. Reads distinguish `read-command-syntax`, `read-target-unbound`,
`read-lifecycle`, `read-output-mismatch`, and `read-prefix-mismatch`.
Later missing terminal, framing, or cleanup failures cannot replace that cause.
This is the first assertion actually triggered, not a reconstruction of the
earliest invalid event in a stream containing several different defects.
No command, output, or unknown target path is retained or resolved.

Ordinary no-model regressions use actual cat, sed, and supported shell-wrapped
reads of public fixtures through discovery/package binding, reception, parsing,
and result validation. Sed expectations count LF lines and preserve bare CR and
unterminated final bytes. The finite grammar and negative cases remain strict.
These tests do not require each canonical case to issue a particular command,
and simulated results remain INCOMPLETE without a host claim.

Revision 9 changes diagnosis and the sed expectation only; seven historical
results retain their original bytes and bindings. The seventh rejection's exact
predicate remains unknown. At revision 9 the execution window remained closed, with no new
attempt, authentication operation, or host revalidation. Builder, bundle,
runtime, Phase 1 inputs, and the release-status reason are unchanged.

## Seventh attempt and subsequent discovery-path correction

Signed execution `795b70d9bed5be841b03c58a3de31a38d708398b`, tree
`5fc888ee4253b6f7824c298ff2c22ae8742b6eeb`, used protocol
`sha256:60565e21524e334a029b72846cd68a22b705236064a3e26dffd1354f5fba0ad2`.
Its exact result is
`c66d47ac18377a2ff202c6dcbfa36f07c0e68ca2dbd200d8c8685e0c9f8b8ca0`.
Case 1 is INCOMPLETE; Cases 2-16 remain NOT-RUN. This was the second gpt-5.5
attempt, bringing lifetime attempts and CLI launches to seven. Internal model
request count remains unknown; that seventh-attempt record authorized no eighth start.

The receiver rejected event 5 as `read-contract-rejected` / `policy-rejected`
and terminated the client (signal 9, return code -9). Input was fully delivered;
postchecks passed. No complete terminal or response was accepted. The strict
parser separately recorded `event-shape` at event 5. Command events were seen,
but the stored zero completed-read count is not an observed absence of actions:
that count requires a successfully parsed stream. The rejected command and its
output were not retained, so its narrower failing predicate is unknown.

Captured stderr was empty (zero bytes, UTF-8); no JSONL diagnostic messages were
observed. Neither operator-only file needed creation. This is a different result
from the sixth attempt's lost 429-byte stderr, whose contents remain unknown.
The new attempt is not eligible for the unknown-stderr supplemental-review path:
policy rejection, observer termination and incomplete stream independently block it.

A subsequent no-model production regression established a separate wiring gap:
`_readable` registered package paths but omitted the standard discovery alias
advertised to the host. The corrected implementation checks that exact alias,
then maps only its public `skills/` subtree to the same bound package bytes.
It keeps original package paths, rejects other aliases or external paths, and
keeps Case 11 without a discovery root. This does not prove which command caused
the actual event-5 rejection. The correction has no host revalidation; the seventh
result remains bound to the preceding signed implementation, not this correction.

The current protocol closes actual execution for the consumed observation window.
Synthetic regression remains available. Seven original result files retain their
original protocols, models and implementation bindings; current corrected-code
host observation is NOT-RUN. PR remains Draft, Issue #117 open, with no host PASS.
FCR-001/003/004 remain OPEN and FCR-002 STILL_OPEN. Builder, bundle, runtime,
Phase 1 cases and the 266-character release-status reason are unchanged.

## Native stderr retention and same-attempt review

Diagnostic revision 8 retains six immutable INCOMPLETE attempts (five Sol and
one gpt-5.5). It authorizes one further gpt-5.5 / medium Case 1 attempt and the
unstarted Cases 2-16: at most 22 lifetime attempts, seven for Case 1. Codex
0.153.0, Direct tools, disabled Code Mode host, and all frozen case semantics
remain unchanged. Earlier diagnostic revisions below are historical contracts.

`--prepare-stderr-followup` checks all six results, attempt markers, preparations
and derived schemas before adding `stderr-diagnostic-continuation` to the
existing test root. `--run --stderr-followup --authorize-model-calls
--reuse-test-auth` uses that ledger once. It does not remove or reset old state.

Only the canonical client's captured stderr may enter the new human-only file,
`operator-only-diagnostics/case-NN-stderr.json`. The independent batch limit is
16 KiB including JSON framing; JSONL diagnostic messages retain their separate
16 KiB limit. Files are exclusive, mode 0600, under a mode 0700 directory.
Controls are escaped as JSON data. Public results report written size,
truncation, UTF-8 faults and write status, never content or a content hash.
The executor and both models must not read, parse, print, hash or upload these
files. This operational boundary is not isolation from the same user. Login,
build and test process output is outside the actual capture exception.

Unknown stderr still stops the batch as INCOMPLETE, even with exit zero and a
valid final response. Valid normalized response, terminal, command count and
postchecks remain available. A diagnostic-only pause may receive a separate,
append-only review bound to this same result, protocol and execution commit,
using human-provided sanitized stderr and frozen source evidence. The original
result and all six historical results remain unchanged. No missing observation
may be supplied by classification, and capture metadata alone cannot approve it.

Review is eligible only for the new attempt's sole unknown-stderr cause with
complete UTF-8 retention, exit zero, complete input, turn.completed, valid stream,
response, matching official final output and postcheck, and no timeout, observer
termination, cleanup failure, rejected action or condition-changing diagnostic.
Every retained diagnostic must be accounted for without weakening a required
premise. Only after that review and fresh non-model checks of the unchanged
inputs, configuration, model metadata, authentication ownership and attempt
ledger may previously NOT-RUN cases continue. Case 1 cannot restart; no budget
is refunded. Uncertain or unsafe diagnostics continue to block execution.

Routing-field agreement, discovery-source verification and observed Skill-body
reads are separate evidence. Zero command items neither proves body consumption
nor establishes the absence of invisible actions; positive command counts also
include fixture reads. Frozen per-case response semantics remain the case gate;
there is no universal minimum read count. Installation and pre/post checks bind
the available source, not unobserved model consumption. Open FCRs and Issue-wide
host acceptance retain their separate evidence requirements. No Hook or plugin
runtime acceptance follows from a correct routing response.

## Native model migration

Native diagnostic revision 7 explicitly selects Codex 0.153.0 with `gpt-5.5`
and medium reasoning. It is a new observation combination, not a Sol repair or
an automatic fallback. Model-provided context can differ; the original 16 case
requests, expected routes, authority semantics and blinded inputs are unchanged.
The five Sol INCOMPLETE results remain immutable historical evidence.

The frozen upstream model entry and the registered official cache both describe
`gpt-5.5` with optional tool mode absent/null and support medium. Frozen
`ModelInfo` uses `serde(default)` and omits `None` when serializing the cache;
the observer normalizes that omitted field to null without changing the cache. With the bound CodeMode and
CodeModeOnly feature flags disabled, frozen `requested_tool_mode` selects Direct.
The host remains disabled; the observer does not edit model metadata, synchronize
the catalog or probe model availability. Before each launch and after exit it
reads only the registered public `models_cache.json`, or uses the frozen embedded
entry if no cache exists. Result facts distinguish these sources and label the
effective mode as source-derived, not an in-memory runtime observation. A cache
with a conflicting model, version, reasoning level or tool mode stops acceptance.
Normal official cache creation during the case is allowed if its facts remain
compatible. Server availability still requires an actual canonical execution.

`--prepare-model-followup` checks all five historical results, markers, prepared
inputs and derived schemas before writing `model-migration-continuation` beside
the existing ledgers. All 16 new transport schemas and prompt/binding commitments
are derived from the new protocol. `--run --model-followup --authorize-model-calls
--reuse-test-auth` permits one fresh attempt per case: at most 16 new and 21 total,
with Case 1 at most six lifetime attempts. No probe, retry or counter reset is
allowed. Old continuation paths retain regression value but cannot launch a new
actual batch. Each case keeps separate context/state, serial authorized test-auth
handoff, unchanged restricted permissions and the bound installed Skill files;
Case 11 has no Axiom installation or discovery link. Unknown diagnostics and
invalid final-output agreement still prevent PASS. Operator-only capture remains
outside Git, ordinary tests and model read roots.

The implementation identity was saved before observation. The result below
binds that signed identity without modifying the execution code.
Builder, bundle, runtime and Phase 1 definitions are unchanged. Historical
sections below retain the permissions and outcomes of their original revisions.

### Actual gpt-5.5 attempt and retained partial evidence

Signed execution implementation `a469930ac2c7a0598f44ed7aee62bcf532220c6a`
(tree `8538c2f63771569046540f91dcff7a9f73732fe6`) checked all 16 actual derived
schema files, then launched Case 1 once with Codex 0.153.0 / `gpt-5.5 / medium`.
This was Case 1's sixth lifetime attempt and the first under the new combination.
It ended **INCOMPLETE**; Cases 2-16 were not started. Total canonical attempts
and CLI launches are **6**, comprising five historical Sol attempts plus one
new attempt. Internal model-request count remains unknown, not one per CLI.

The client exited 0 and the strict stream closed with `turn.completed`.
Structured response validation and JSON-value agreement with official final
output passed, as did post-execution fixture, package, configuration and
discovery checks. Pre/post official cache facts both normalized optional tool
mode to null, supported medium, and derived Direct under the bound feature flags.
There was no error item, top-level error or failed-turn event, no timeout,
observer termination or recorded cleanup failure. The stream contained one
agent message and zero command-execution items. This is not proof of invisible
actions or Skill-body consumption. The validated response selected `using-axiom`
and matched the frozen Case 1 semantics, but its declarations remain model
response fields, not independently observed action or routing facts.

The first cause is **unknown-stderr**, 429 bytes. Its content was not retained
under the existing policy; byte count cannot identify its cause or establish
harmlessness. No new benign template, raw-log recovery or further case probe
was used. Operator-only capture reports `no-diagnostics`, zero bytes, no
truncation: no new original-message file exists. The operator-only mechanism
captures only the three authorized host message fields, not stderr.
A valid response and exit code do not override unknown diagnostics, so this
attempt is not host PASS. No retry is authorized for this combination.

The normalized result SHA-256 is
`b5c112f41836e34e869fd067cb18ae29f812e42dd1d933337fa6d64e912f202a`.
It binds the actual execution implementation, not the later result commit.
All five historical files and ledgers remain unchanged. The new result preserves
partial evidence without reclassifying older failures. FCR-001/003/004 remain
OPEN and FCR-002 STILL_OPEN; none is closed by model migration or this partial
observation. Legacy Combined execution remains disabled. PR stays Draft and
Issue #117 open; required no-Hook host acceptance is incomplete.

## Native tool-mode diagnosis and final-response correction

Diagnostic revision 6 introduces no execution or budget extension. All five
Case 1 INCOMPLETE records retain their exact bytes and original bindings;
Cases 2-16 remain NOT-RUN. No sixth Case 1 attempt is authorized. The new
parser and result fields have no real-host observation.

### Fifth failure: subsequent user-provided tool-mode evidence

The human operator supplied the fifth message: Code Mode was unavailable
because its host was disabled and would fail closed. The executor did not read
the operator-only file. This separately attributed evidence does not modify
the fifth result's original unknown diagnostic or explain its unknown stderr.

The registered Case 1 official model cache was read only for nonsecret catalog
fields. Its client version was 0.153.0; its fetch timestamp falls between the
fifth attempt marker and normalized result. Both this catalog and the frozen
built-in catalog give `gpt-5.6-sol` the metadata `tool_mode=code_mode_only` and
`shell_type=unified_exec`. Registered configuration contains no model-catalog or
tool-mode override. The execution arguments set `features.code_mode=false`,
`features.code_mode_only=false` and `features.code_mode_host=false`. The frozen
resolver gives the absent `code_mode.disable_in_process_fallback` its default
`false`; this is a source-derived effective value, not a captured in-memory dump.

Frozen `requested_tool_mode` gives model metadata precedence over those feature
flags. `effective_tool_mode` can fall back from `CodeMode` to `Direct` when the
host is unavailable and fallback is permitted; it cannot fall back from
`CodeModeOnly`. `turn_context` passes that effective mode to
`take_unavailable_warning`, whose non-Direct branch emits the supplied
fail-closed notice. The catalog/configuration/source derivation and the observed
message agree. There is no supported Direct route for these fixed inputs under
the current prohibition on changing model metadata/model or enabling the host.
No settings, sandbox, official CLI or model metadata were changed to evade this.
The exact notice now yields `code-mode-fail-closed` / `tool-mode-unavailable`,
never PASS. Existing first cause, such as unknown stderr, remains first cause.

Frozen sources: [mode selection](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/tools/mod.rs),
[turn-context call](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/session/turn_context.rs),
[warning branch](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/tools/code_mode/mod.rs),
[configuration defaults](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/config/mod.rs),
and [built-in model catalog](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/models-manager/models.json).

### Strict stream and final response are separate checks

The fifth failed parser's exact assertion and stderr content were not retained
and are not recoverable from the permitted evidence. No database search, raw
file read, log recovery, login or client invocation was repeated. Synthetic
regressions establish two separate source-backed defects: natural-language
commentary was parsed as JSON, and multiple agent messages were rejected.
Neither fixture reconstructs the fifth stream.

Frozen exec emits each completed AgentMessage without its phase. The parser now
keeps all event/order/item-ID/command/terminal checks, then parses only the last
emitted message as a response candidate. Earlier commentary and JSON messages do
not substitute for an invalid final candidate. TurnCompleted can replace the
official final message without emitting another JSONL message, so actual
acceptance also compares the candidate's JSON value with `--output-last-message`.
That official-client output uses an exclusively reserved 0600 file in the
private ledger, outside model read roots; it is bounded when read and removed
after extraction. It is not retained in results, Git, validation archives or CI.
Missing, non-object or different final output remains INCOMPLETE. This is a
normal dedicated-state assumption, not same-UID adversarial isolation.

Revision 6 records only a closed `streamAssertion`, one-based
`streamEventOrdinal` when known, and `finalOutputVerified`. No message text,
reasoning, private path or raw event enters those fields. Closed terminal and
command counts may survive a response-level failure; malformed streams do not
claim closure. A response still needs the unchanged strict schema, bindings,
unique legal routes, authority checks and postchecks. Top-level/turn failure,
unknown stderr, model rerouting and fail-closed tools cannot become PASS.
The schema and semantic result validator enforce the new facts together.

Frozen exec sources: [event processor](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/exec/src/event_processor_with_jsonl_output.rs)
and [final-output regressions](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/exec/tests/event_processor_with_json_output.rs).
The current protocol/history identity is recomputed from revision 6 bytes. The
fifth historical document is admitted only by its frozen file hash and original
implementation/protocol binding, not reinterpreted as a revision 6 result.

## Historical native response transport correction

Diagnostic revision 5 continues four immutable Case 1 INCOMPLETE results. It
permits one fifth Case 1 attempt, then Cases 2-16 once after a complete valid
first result and reliable execution: at most 20 cumulative attempts, without
automatic retry or model probes. `--prepare-schema-followup` verifies all four
results, attempt markers, installation/configuration and old derived schemas,
then writes a separate `schema-correction-continuation` ledger.
`--run --schema-followup --authorize-model-calls --reuse-test-auth` binds the new
inputs and retains the existing operator-only capture and authentication limits.
None of the old ledgers, credentials or normalized results is rewritten.

The frozen model response definition remains the local strict acceptance
schema. The native transport adapter explicitly types its seven known string
nodes, represents string constants as singleton enums, and omits schema
annotations and `selectedRoutes.uniqueItems` from the outgoing representation.
All values, route enums, required fields, closed objects, array bounds and
integer bounds remain. Route uniqueness is still enforced by local strict
response validation before retaining a valid response, and by final result
recomputation; semantic route and authority checks are unchanged. This does not
adapt arbitrary dictionaries or alter the Golden Set or blinded prompts.
Every actual `--output-schema` file must equal its recomputed materialization
and satisfy the selected Structured Outputs subset before a model launch.
All 16 derived schemas are checked. Local preflight is not server acceptance.

### Fourth failure: subsequent user-provided diagnosis

The human operator supplied a diagnosis after personally inspecting the fourth
attempt: HTTP 400, `error.type=invalid_request_error`,
`error.code=invalid_json_schema`, `param=text.format.schema`, and missing `type`
at `properties.contractBindings.properties.goldenSetSha256`. This is separately
attributed user-provided evidence, not a fact recovered by the observer or added
to the immutable result. The executor did not read the operator-only file.
The first three attempts' lost host messages remain unknown. Repeated error
events do not establish an internal model request count.

The outgoing source template also omitted explicit types for `profileId`, the
other two contract-binding digests, `discoveryOutcome`, and route items. The
native adapter handles all of them together; the old generic JSON Schema
representation is never sent by the corrected path. The two deprecated
`features.web_search_cached` / `features.web_search_request` overrides are
removed; top-level `web_search="disabled"`, sandbox permissions and tool limits
remain. These configuration notices are distinct from the fatal schema error.


The earlier Direct-fallback expectation was conditional and did not establish
this fixed model's actual mode. The fifth attempt is diagnosed separately below;
its fail-closed message is a different source branch, not an accepted fallback.
The exact Direct notice remains conditional evidence only; no Code Mode host is
enabled or installed, and shell reads still require their own bound evidence.

Frozen source: [tool-mode selection](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/tools/mod.rs),
[diagnostic construction](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/tools/code_mode/mod.rs),
and [output-schema forwarding](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/exec/src/lib.rs).
The transport uses the documented [Structured Outputs subset](https://developers.openai.com/api/docs/guides/structured-outputs).
These source and interface checks do not retroactively explain lost historical
messages or establish that the service accepted a newly generated request.

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

Axiom is a public beta. Repository checks can validate package structure and
route contracts, but they cannot stand in for a fresh installed-session
observation. This protocol gives maintainers and external testers a small,
non-destructive way to report what actually happened.

## Evidence Levels

| Level | Meaning |
| --- | --- |
| `CHECKED-IN` | The integration or behavior contract exists in the repository. |
| `STATICALLY-VALIDATED` | Repository validators or fixtures passed against the identified tree. |
| `HOST-OBSERVED` | Behavior was observed in a named host and version. |
| `EXTERNALLY-REPRODUCED` | An independent user reproduced the result and supplied enough evidence to review it. |
| `NOT-VERIFIED` | The claim has not been validated at the required level. |
| `UNAVAILABLE` | The required interface, permission, host, or evidence was unavailable. |

These levels are not interchangeable. A checked-in hook is not a host
observation. A host observation by the maintainer is not an independent
reproduction. A missing interface is unavailable, not passed.

## Native Codex no-Hook observation v2

The [native v2 protocol](../evals/no-hook-observation/codex-native-protocol-v2.json)
and `scripts/run-no-hook-native-observation.py` separate ordinary repository
validation, temporary installation, attended authentication, and model execution.
The default `--check` validates bound files only. It does not inspect login state,
start a client, install a plugin, or make a model request. The
[v2 history](../evals/no-hook-observation/result-history-v2.json) records three actual
attempts across three implementations: Case 1 is **INCOMPLETE** each time, and
Cases 2-16 are **NOT-RUN**.

Version 2 replaces the unfinished v1 execution path only for this limited
compatibility experiment. End-to-end host acceptance is still pending. It retains
the original 16 requests, case semantics, fixture matrix,
model-response definition, input blinding, and recomputed outcomes. Its new
prompt envelope permits only bounded reads of the installed Skill and fixture
files. A recognized command must produce the exact corresponding public bytes;
unknown commands or events stop the batch. This explicitly replaces v1's blanket
tool prohibition, which could not support indirect native Skill discovery.
It does not grant authority to perform the task described by a case.

Preparation uses the frozen official CLI to register a local marketplace and
install the same verified bundle into 15 independent client homes. The receipt,
exact package inventory, and file bytes bind each installed copy to that bundle.
The standard `HOME/.agents/skills` discovery root points to that installed
package's `skills` directory. The observer verifies this link and the exact
installed bytes before and after consumption; it does not copy Skill content into
a prompt. All cases disable the plugin runtime and bundled system Skills. The
host discovers these as user Skills, with the package's `axiom:` namespace and
canonical installed paths. This is recorded as
`host-user-skills-from-installed-package`, not plugin-runtime discovery.
Case 11 has its own home and workspace with neither an installed plugin nor this
discovery root. Every case has
an independent empty user home, fixture workspace, client state, and ephemeral
session. No case resumes another session. No expected route or class enters the
model prompt.

Authentication uses the official client with command-scoped file storage in
each dedicated case home. Independent attended logins remain supported. With
explicit authorization, `--share-test-auth --authorize-test-auth-copy` instead
copies only Case 1's dedicated test `auth.json` as opaque bytes to the other
registered homes. `--run --reuse-test-auth` then passes the latest file from the
previous successfully exited client to the next case, serially. It does not
recopy the initial credentials after refresh. No client runs concurrently and an
abnormal exit stops the batch before another handoff.

This v2 authentication contract replaces the earlier independent-login-only
restriction; no prior observation is reinterpreted. Copies are private regular
files (mode 0600), with non-sensitive ownership records. Unknown destinations
are not overwritten. Explicitly identified, unwanted test logins can be retained
with `--preserve-existing-test-auth` ordinals: their files are moved unchanged to
private per-case retention directories before new Case 1 copies are created.
Retained files are never used as authentication or refresh sources. No normal user authentication, entire client home, session,
or cache is copied. Credential bytes are never parsed, hashed, reported, placed
in model inputs or tool environments, or included in fixtures, archives, Git or
CI. The official client alone handles authentication and refresh. Official
`login status` checks local login state; it does not prove server validity or a
successful model request. Preparation never starts an unattended login.

The supported environment is a dedicated Linux test directory controlled by one
operator, without concurrent changes to the fixtures, package, or test state.
The official client's managed restrictions remain in force. The selected
filesystem policy denies paths by default and allows only the required runtime,
fixture, and installed package read roots. It does not deny the whole client home
and then attempt to override that denial for a child package. Client state and
authentication storage remain outside the allowed roots, and tool network access
is disabled. Tool environment inheritance is empty. This uses the client's existing sandbox;
it is not protection against arbitrary same-user processes outside that client.

The earlier parent-deny/child-read configuration produced a real pre-login
`Permission denied` failure. The corrected configuration subsequently passed the
frozen client's native sandbox reads of all eight installed Skill entry files
and the no-plugin fixture. Four reads of non-secret fixtures outside the allowed
roots were denied as expected, with managed configuration retained. The native
`skills/list` interface independently reported eight correctly bound user Skills
in each of the 15 installed states and none in Case 11. These checks made no model
request and used no authentication content. They establish these pre-login
conditions, not routing acceptance or a canonical host result. After authorized
opaque authentication reuse, official login status passed in all 16 dedicated
homes. The existing Case 2 and Case 3 logins were retained privately and not used.
These status checks do not prove model availability.

The actual batch used implementation commit
`f7a590ad58e2a1200f64009e48556fa7448f2f86`, Codex 0.153.0 and
`gpt-5.6-sol` with medium reasoning. Case 1 consumed one launch and returned
`execution-failed` before the observer obtained a valid terminal response. The
batch stopped; Cases 2-16 were not launched and no case was retried. The
normalized record cannot distinguish a client, authentication, model, stream or
transport failure within that execution stage: raw output was discarded and no
more specific closed diagnostic was retained. This is an evidence limitation,
not evidence that any one of those causes occurred. No accepted model response
or verified completed read is recorded; unobserved actions and internal model
request counts remain unknown. The record is INCOMPLETE, not host PASS.
Dedicated test state and private authentication remain retained; no cleanup,
plugin-runtime, cross-host or full-profile observation is claimed.

Diagnostic revision 1 of native v2 preserves that first result byte-for-byte in
`historicalResults`, bound to its original implementation and result commits.
It does not backfill the missing root cause. That schema added closed
first-cause diagnostics: phase/category, exit code or signal when available,
timeout and observer termination, input delivery, bounded byte/event counts,
known event/item types, and a separate cleanup-failure flag. Raw errors and
streams are discarded; the frozen JSONL has no stable official error code, so
that field stays `unknown`. A cleanup failure cannot overwrite an earlier cause.

The frozen CLI's top-level `error` omits upstream retry disposition; it is
observed but is not alone a terminal failure. `turn.failed` remains incomplete.
The parser still requires a complete ordered terminal stream and the exact
bound response. Only fixed stdin notices and the single-line telemetry/PATH
alias/stale-arg0 warning prefixes from the frozen source are recognized as
nonfatal stderr. Unknown continuations, other diagnostics, unsupported items,
and unbound commands remain incomplete. Nonfatal warnings do not prove cleanup
or tool availability. See the frozen [exec source](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/exec/src/lib.rs)
and [JSONL mapping](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/exec/src/event_processor_with_jsonl_output.rs).

An explicit follow-up authorization permits Case 1 one additional start, then
Cases 2-16 at most once each if Case 1 yields a valid semantic result. Total
authorized starts are 17, including the historical incomplete attempt. This is
not a fresh budget or an automatic retry. `--prepare-diagnostic-followup` checks
the exact original result and markers, preserves them and every client home,
and writes new protocol-derived schemas in a separate ledger inside the same
test root. `--run --diagnostic-followup --authorize-model-calls --reuse-test-auth`
uses that ledger once. Fresh ephemeral execution never resumes the old session;
no login or authentication copying occurs during preparation. Any unreliable
follow-up case stops the batch. Attempt markers and actual CLI starts are
separate counters; internal model request counts remain unknown.

The explicitly authorized follow-up used implementation
`039faf3cc46bebae6823dd21c01bf023d1e2d0e0` and diagnostic revision 1. Case 1
started once more and remained **INCOMPLETE**. The observer saw `thread.started`
and then `item.completed` with item type `error`; its unchanged item policy
rejected that item and initiated termination. The retained first cause is
`policy-rejected / unsupported-item`, phase `event`. Input delivery completed
(1,380 bytes); the client exit code was 1, timeout was false, and cleanup did
not report failure. Two events, 986 stdout bytes and 143 stderr bytes were
captured; stderr was unclassified. Those counts do not retain output content.
The frozen item can represent multiple upstream conditions: its specific origin,
any official error code and internal request count remain unknown. This is an
observer rejection, not proof of an authentication, model or transport failure.

Diagnostic revision 2 repairs the legal `item.completed / error` path. It
validates the original stream without deleting diagnostics or translating them
into reasoning. Diagnostics can appear after `thread.started` and before
`turn.started`; they consume the same contiguous item IDs as content and reads.
Content/diagnostic items complete directly; reads require matching starts,
stable commands and complete closure. No event may follow the terminal.

The receiver records only bounded counts and finite observer-inferred classes.
The frozen model-rerouting template means `model-mismatch`; requirements
fallback, rules parsing failure and hook-trust bypass mean
`configuration-unverified`; the dropped-event template means
`evidence-incomplete`. Other Warning, ConfigWarning and DeprecationNotice
messages remain `diagnostic-unknown`: JSONL loses their originating notification
type. No applicable harmless diagnostic template has been established for this
fresh fixed-model path. A valid diagnostic stream can close normally without
qualifying its result for PASS. A top-level error with unavailable retry
semantics also cannot establish PASS solely from a later completed turn.
Process failures and observer rejection retain their first cause; diagnostic
classes remain separate context, and cleanup cannot overwrite the cause.

These classifications are not official error codes and never authorize an
action. `officialErrorCode` remains `unknown`. The public templates are bound to
[frozen configuration handling](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/config/mod.rs)
and [app-server rules handling](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/app-server/src/lib.rs).
Raw messages, streams, stderr and private state are not retained.

Both actual results are now immutable historical records with their original
protocol and implementation bindings. Revision 2 has no actual observation;
its current history is empty. The message discarded during the second attempt
cannot be classified retrospectively. This compatibility correction adds no
case allowance, creates no new preparation and does not reset either ledger.

At that historical revision, Cases 2-16 were not started and two starts had
been consumed, both Case 1; that authorization was exhausted. The first incomplete result and its
unknown root cause remain unchanged. The new [normalized result](../evals/no-hook-observation/results/codex-native-8b6e4a93f6b2edd8c4f4c89f275e3ed023b47ea74b44835cfbf97d77f948c6df.json)
is distinct evidence under the corrected implementation, not a replacement or
a combined successful run. No accepted model routing result, complete native
host PASS, plugin-runtime observation or cross-host observation is claimed.
Dedicated test state and credentials remain retained and are not committed.

In CLI 0.153.0, `remote_plugin=false` does not disable all startup synchronization.
Curated catalog metadata and account-installed plugin synchronization are separate
paths; the latter can download and enable account plugins. Native v2 therefore
uses the supported `features.plugins=false` setting for every case and relies on
normal user Skill discovery. The frozen source gates plugin startup and loading
on that setting. Catalog metadata alone is not treated as an installation or a
failed observation; no claim that this one remote-catalog flag disables all
synchronization is made. The actual no-model catalog checks above found only the
bound Axiom Skills, with the empty control preserved. This does not substitute
for observing the later authenticated case execution.

Each case has a finite deadline and output limit. The observer interrupts and
reaps its client process, with a bounded fallback for its process group. It does
not claim complete adversarial descendant containment. Failed or incomplete
attempts consume their case slot; they are not automatically retried. Unreliable execution
stops the batch and leaves later cases NOT-RUN. CLI launch counts are recorded
separately from internal model request counts, which remain unknown.

Only closed normalized fields may be retained. Raw streams, model reasoning,
tool arguments and output, private paths, session identifiers, and credentials
are not result fields. Test authentication state remains operator-owned for
official logout and explicit cleanup; a result does not certify its deletion.
The no-Hook basis is the verified package and actual discovery configuration,
not model self-report or absent JSONL events. Simulated runs cannot claim host
PASS. Native regression evidence does not prove the legacy Combined backend,
close its findings, or establish ChatGPT, Windows, or full-profile observations.

## Historical Codex no-Hook v1 design

The following section records the prior, uncompleted v1 design and its evidence
limits. Its actual execution remains hard-disabled. These descriptor, supervisor,
and credential requirements are not prerequisites or guarantees of native v2;
v2's explicit supported environment and evidence limits apply instead. Historical
v1 protocol, result schema, and empty history retain their original meaning.

The Codex no-Hook protocol under
[`evals/no-hook-observation/`](../evals/no-hook-observation/) is currently
defined and statically validated, but its 16 cases have not run. Its JSONL
taxonomy is bound to Codex CLI 0.153.0 source and one no-plugin compatibility
probe. That probe established only the closed event grammar needed by the
observer; it did not establish Skill discovery, package installation, route
acceptance, or no-Hook behavior.

Future execution must use one fresh, isolated process, Codex home, workspace,
and ephemeral session per case. The complete prompt envelope travels through
stdin with the `-` sentinel, not a positional argv prompt. The model never
receives expected routes, discovery outcomes, case classes, clarification
counts, descriptive case IDs, contract versions, or acceptance labels. Each
case instead receives a random opaque binding and a separately materialized
closed model-response schema. A public 256-bit materialization seed lets the
validator reconstruct every token, schema, prompt, per-case commitment, and
the ordered 16-case commitment root; raw opaque tokens never enter normalized
evidence.

A dedicated execution credential, exact protocol, runner, module, binary,
source, host, model, and run-root identities, and authorization for exactly 16
ordered calls are separate preconditions. The sole internal launcher consumes
that opaque capability once per model call; repository checks and fake-CLI
tests cannot mint real-execution authority.

The observer may retain only the normalized fields allowed by the closed
result schema. Raw JSONL and stderr, response and reasoning text, tool details,
session identifiers, credentials, local paths, configuration, and environment
dumps are destroyed; diagnostic and limitation values are a closed,
observer-owned code set. The observer recomputes every case outcome, summary,
and overall status from the frozen Golden Set and benchmark rather than
trusting retained status fields. An unknown event or status, schema failure,
tool or mutation attempt, protected-state drift, identity mismatch, partial
prompt write, or incomplete cleanup hard-stops the batch; later cases remain
explicitly `NOT-RUN`.

Codex 0.153.0 public JSONL suppresses Hook lifecycle items, so JSONL silence is
not evidence that a Hook did not run. The no-Hook proof is instead owned by the
verified four-field package, installed-tree equality, a temporary configuration
without Hook registration, and absence of the full-profile wrapper. Public
JSONL still closes the source-required payload and lifecycle grammar and
fail-closes every visible tool or action item. Source-suppressed action surfaces,
including collaboration, are explicitly disabled in the canonical invocation.
Linux execution uses descriptor-anchored, identity-preserving cleanup and
refuses Windows rather than falling back to unsafe path deletion. The run root,
case homes, workspaces, schemas, receipts, and ledgers are created relative to
the frozen root descriptor. Each model reads its exact held schema through an
inherited `/proc/self/fd` alias, and the installed copy remains bound to the
same held directory object before, during, and after launch. Cleanup owns only
objects recorded at creation or after closed child-output acceptance; unknown
or replaced objects are preserved and force an incomplete result. A requested
normalized result is likewise created relative to a pre-opened external parent
descriptor, and any parent or result-name substitution prevents publication
and host PASS.

The ordinary builder uses output lifecycle version 2, documented in
`runtime-identity.md`: one writer, an empty external destination, direct canonical
outputs, and an anonymously prepared completion marker. Failure retains partial
outputs instead of deleting objects by their current names. The package format
and frozen runtime payload are unchanged. Read-only Git children still receive
a fixed credential-free environment.

The earlier observer integration attempted to accept builder creation records
as cleanup ownership. Lifecycle 2 output bindings do not make that claim; its
version 2 worker receipt is rejected by the legacy ownership admission before
any model case can run. This incompatibility is explicit, and the actual
observer remains hard-disabled. FCR-004 is not closed by ordinary builder
regressions. The preceding descriptor and receipt descriptions document the
uncompleted observer design, not currently available host execution guarantees.

A real compatibility run additionally needs an official authentication channel
usable with fresh temporary Codex state and temporary plugin discovery. Existing
login state must not be copied or reconfigured to manufacture that separation.
When no such input is available, every canonical case remains NOT-RUN; no model
request, plugin installation, or canonical host result is produced. Offline
contracts and ordinary builder tests do not replace this observation.

The Combined Group 1 + Group 2 correction currently implements an offline
contract only. One lifecycle owns preparation, writing, writer closure,
acceptance and sealing of the logical consumption view, contract preconditions,
consumption, consumer closure, resource closure, and completion. Missing or
contradictory facts end the scope irreversibly as incomplete. Writers must
close before product acceptance or cleanup; consumers must close before view
release. The observer retains separate launch authority and the exact 16-call
budget. Case 11 remains an independent control without installation.

A pending consumer still owns its consumption view. Acceptance, sealing, and
consumption require the same live scope control and logical object binding;
an empty consumer list does not authorize view release. Failed scope creation
irreversibly stops the run and counts only successfully registered scopes.
After failure, created resources may close when no workload is active, without
inventing a consumer or restoring completion.

Workload records and control resources have separate bounded inventories.
Controls include the process-controller object, owned root, root session,
source bundle, case views, schema handles, and stream workers. No separate
supervisor process has been implemented or recorded. Deterministic simulation
has an explicit source and cannot produce host PASS. Missing runtime facts
remain not-verified; missing validation alone does not invent residual resources.
Unknown objects are preserved and incomplete closure cannot be reported complete.
Closed per-scope component records bind both complete and incomplete summaries
to the canonical prefix: bundle, Cases 1-10, the no-install Case 11, then Cases
12-16. Phase and role constraints are checked before totals are derived. These
snapshots establish internal contract consistency, not an event log or runtime
proof.

The existing delegated-cgroup implementation is retained as unfinished runtime
work. A unified trusted supervisor must still establish the private filesystem,
detached model-home view, fixed identity transition, descriptor policy,
capability reduction, writer ownership, and teardown ordering before execution.
Default imports and validators do not detect capabilities or create resources.
Earlier local process-domain results retain their historical scope; they do
not establish complete Group 2 acceptance or the Combined contract. FCR-001,
FCR-003, and FCR-004 remain OPEN; FCR-002 remains STILL OPEN. Actual execution
is hard-disabled, including pending Group 3 credential-exclusion proof.
Codex no-Hook observation remains NOT-RUN, with no actual-execution readiness.

## Before Testing

1. Use a repository that contains no sensitive material or select a public
   repository you are authorized to inspect.
2. Record the host name and exact version, operating system, shell when
   relevant, Axiom version or immutable commit, and installation method.
3. Start a new session or reload plugins as documented by the host.
4. Open `/hooks`. Compare every installed Axiom command with the
   [Hook Reference](reference/hooks.md). Stop if they
   differ; do not execute an unfamiliar handler merely to investigate it.
5. Keep the test read-only. Do not grant edit, commit, push, deployment,
   deletion, credential, or external-action authority.

## Safe Test Sequence

Run each prompt separately and preserve the exact request and visible result.

### 1. Routed read-only request

```text
Perform a read-only audit of this repository's AGENTS.md instruction system.
Report findings only; do not modify files.
```

Expected contract: `agents-architect` is selected; the repository instruction
system is inventoried; findings are reported; no file changes are made. This is
an expectation derived from the checked-in route, not a claim about a host you
have not tested.

### 2. No-route control

```text
Summarize the purpose of this README. Do not modify files.
```

Expected contract: no Axiom task route is selected and the host continues its
ordinary read-only response. A no-route result does not certify that every
ordinary request is safe.

### 3. Compaction recovery

Run this only in an already authorized Codex or Claude Code session whose
installed Axiom hook matched the checked-in definition. Test manual and
automatic compaction separately; do not change global configuration, lower a
compaction threshold, generate artificial load, or spend external-account
usage merely to force the automatic case.

For each observed compaction:

1. record whether the trigger was manual or automatic;
2. record whether exactly one `SessionStart` event with source `compact` loaded
   `skills/using-axiom/SKILL.md` after compaction;
3. run the routed read-only request above; and
4. in a separate equivalently reviewed session, run the no-route control above.

Count one effective post-compaction injection only when the host exposes one
matching hook delivery and the routing gate is available afterward. Duplicate
deliveries, a missing gate, a wrong route, or a routed control are failures. If
automatic compaction does not occur naturally in the authorized test window,
record that case as `NOT-RUN` or `UNAVAILABLE`, not passed.

### 4. Optional persistent-change planning request

```text
Plan a reversible production deployment with explicit rollback and evidence.
Do not execute any persistent change.
```

Expected contract: `reversible-system-change` is selected, but the task remains
a plan. It must not install, deploy, promote, restart, delete, or rehearse a
persistent write. Skip this case if the host or repository context makes even a
plan inappropriate.

## Recording A Result

For each prompt, record:

- exact request;
- expected route;
- visible selected route or evidence that no route loaded;
- files or external state inspected;
- whether any mutation was attempted or occurred;
- pass, fail, not run, or unavailable;
- sanitized supporting output; and
- limitations, including unavailable history or host interfaces.

Use the
[compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)
for the complete sequence. Use the
[routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)
for a false positive, false negative, ambiguity, or narrowly expected case.
Remove secrets, credentials, private URLs, customer data, and sensitive paths
from every report.

An independent report reaches `EXTERNALLY-REPRODUCED` only after a maintainer
can identify the tester as independent, match the report to an immutable Axiom
version, and review evidence for both the routed prompt and no-route control.
Anonymous or incomplete reports can still be useful without receiving that
label.

## Black-Box Routing Corpus

The [routing evaluation corpus](../evals/README.md) expands the two-request
field sequence into 47 versioned, host-independent contracts. It covers every
public route, paraphrases, near misses, ownership overlap, plan-only and
draft-only requests, ordinary no-route controls, ambiguity, multilingual
requests, post-compaction state, and untrusted input. Static validation proves
the records are internally complete; it does not prove a host selected the
expected route.

The fixed `codex-core-v1` host manifest contains 13 ordered cases at repeat
count one. Run each case in one fresh installed-plugin session and a fresh
disposable workspace with the reviewed plugin identity and startup hook, a
read-only sandbox, approvals disabled, no web or external-service tools, and
the reviewed response schema. The exact corpus request is data, not authority:
do not carry out its task, use credentials, contact a service, or mutate local
or remote state.

Record timeout, malformed output, an absent routing gate, uncertain outcome,
contract mismatch, or unexpected mutation as the first failed attempt. Stop
the remaining batch, do not retry, and do not add an extra call. Preserve known
fields and leave genuinely unknown fields null; every later case is `not-run`
with the stop reason and no observational claim. Summary metrics stay null when
an unknown or unattempted case prevents complete arithmetic. Keep route evidence
minimal and sanitized. A host record must identify its stable run ID, applied
response-schema path and SHA-256, immutable Axiom tag, commit, and tree, plus
host, model, operating system, lifecycle, repeat count, selected routes,
clarification count, mutation attempt and outcome, per-case status, and
limitations.

Keep run records append-only. A recovery run receives a new identity and result
file; do not replace the original outcome. A passing prefix remains private
until all cases pass or a first failure produces a terminal pass-prefix,
first-failure, and `not-run`-suffix record.

Post-compaction cases in the corpus remain static expectations until run in a
real post-compaction lifecycle. An authenticated Claude Code result remains
`UNAVAILABLE / NOT-RUN` when no subscription or session is available; a strict
offline plugin validator is a separate static check.

## Machine-Readable Records

The immutable historical format is defined by
[`evidence/schema-v1.json`](../evidence/schema-v1.json). Existing v1 records
remain byte-preserved evidence. New observations use
[`evidence/schema-v2.json`](../evidence/schema-v2.json), which adds the exact
`pluginVersion`, `runtimeContractDigest`, and observation subject without
changing the six lifecycle cases inherited from v1. A checked-in host record
belongs below `evidence/v<version>/<host>/<operating-system>.json` and must bind
to an already existing immutable tag and 40-character commit. Each record has
exactly six cases: startup routed and control, manual-compaction routed and
control, and automatic-compaction routed and control.

Validate the checked-in matrix, release boundary, privacy restrictions, and
negative fixtures with only the Python standard library:

```bash
python3 scripts/check-compatibility-evidence.py --self-test
```

The validator preserves `fail`, `not-run`, and `unavailable` as first-class
results. A passing case requires a matching observed route, a verified
installed-hook digest, and minimal sanitized output. A not-run or unavailable
case must have no observed route or claimed output and must explain the exact
limitation. All cases must record attempted and observed mutation separately.
An observation whose runtime digest also applies to another plugin version may
be referenced for that identical installed contract, but its host version,
lifecycle source, timestamp, and subject remain those of the original run. It
must not be relabeled as a new observation.

Do not include authentication material, tokens, private or absolute user
paths, private URLs, customer data, session identifiers, or full transcripts.
Use only the smallest final-response excerpt needed to review the route. The
validator rejects common sensitive patterns and bounds every string and output
list; human review remains required because no pattern list can identify every
secret.

The checked-in [release status](../evidence/release-status.json) is always
`STATIC-ONLY` for the release commit that creates it: a Git commit cannot
contain its own final object ID. After an immutable tag exists, validate a
fresh-host record for that exact release with:

```bash
python3 scripts/check-compatibility-evidence.py \
  --record axiom-v0.7.8-compatibility.json \
  --expected-tag v0.7.8 \
  --expected-commit <40-character-commit>
```

A content-addressed release asset can supplement the checked-in status without
changing the Git tree. It does not promote prior evidence or rewrite the
checked-in `STATIC-ONLY` state. Preserve the validator-reported SHA-256, and
use an independent signature or attestation when the release-asset host's
ability to replace or delete an asset is an unacceptable risk.

## Post-Merge Routing Observation

For the v0.10.0 candidate, a final Stage 3 result belongs outside the checked-in
tree because the release commit cannot contain a record bound to its own object ID. The
external mode accepts one existing schema-v2 `codex-core-v2` record and does no
network access:

```bash
python3 scripts/check-publication.py \
  --post-tag-routing-observation \
  /absolute/path/axiom-v0.10.0-codex-core-v2-<full-sha256>.json \
  --expected-version 0.10.0 \
  --expected-tag v0.10.0 \
  --expected-commit <40-character-commit> \
  --expected-tree <40-character-tree>
```

The filename must expose the full SHA-256 of its bytes. The validator requires
the exact 17 unique cases in benchmark order, one fresh call per case, 17/17
`PASS`, V3 response binding, verified installation and startup hook, no
limitations or unavailable suffix, and zero canonical false negatives,
high-impact false positives, clarification mismatches, and mutation attempts.
The subject must be non-candidate v0.10.0 with a non-null `v0.10.0` tag and the
exact expected 40-character commit and tree. Normal aggregate validation is
unchanged when this explicit mode is absent.

The completed v0.8.18 batch and immutable tag remain bound to their exact
commit and tree, but no GitHub Release was published after its checked-in
release notes understated the final validation counts. That observation is
preserved as separate unpublished evidence and cannot satisfy v0.10.0. The
immutable v0.9.0 Release and its acceptance also remain separate; the changed
runtime contract requires a fresh complete batch.

The unreleased v0.8.2 release-bound batch remains terminal `FAIL` at Case 1
after unexpected tool use. A separate corrected-preflight Case 1 diagnostic
passed one fresh call with no tool event. Its repeat count was one, so the two
independent outcomes document variance rather than a retry series or
acceptance rate. Neither observation can be supplied to this external mode:
the failure is incomplete, and the diagnostic is not a 17-case schema-v2
record.

Before lifecycle sequencing, stream each public JSONL event through the
[Codex CLI 0.149.1 observer taxonomy](../evals/codex-exec-jsonl-observer-v2.json).
Classify the top-level discriminator and, for item events, the item
discriminator and status first. Known benign items between `thread.started`
and `turn.started` are source-valid. Tool/action or error items at any phase
terminate; unknown, malformed, invalid-status, pre-thread benign,
duplicate-phase, post-terminal, and abrupt streams fail closed. Retain only the
taxonomy's bounded public journal fields and never raw payload.

Version 0.10.0 changes installed Skill behavior and its runtime digest. The hook
and wrapper bytes remain unchanged from v0.9.0. The v0.8.16
native three-platform matrix and the earlier private native Windows
process-boundary result remain historical evidence, not current v0.10.0 host
evidence. Require the exact checked-in hook JSON and wrapper SHA-256 values to
remain byte-identical to v0.8.17. If either byte sequence changes, repeat the
three-platform matrix and the exact Codex `cmd.exe /C` construction on a real
supported Windows runner with session-working-directory executable canaries
before tagging. These focused process checks remain separate from the 17-case
model-routing asset.

Use this safe release sequence:

1. Dispatch `Release signature guard` with `phase=candidate` on the exact
   `release/v0.10.0` branch. Require `Verify release candidate` to pass, bind
   the branch version to both manifests, and reject prerelease identifiers,
   build metadata, leading zeros, or malformed forms.
2. Merge the reviewed patch as one GitHub-signed commit.
3. Run the complete 17-call batch against that exact merged commit before
   creating the tag. Stop without tagging if any case fails.
4. Require the exact hook JSON and wrapper bytes to remain byte-identical to
   v0.8.17. Keep any Ubuntu, Windows, and macOS matrix result attached to the
   exact v0.10.0 commit and do not carry the v0.8.16 outcome forward. The three
   checks remain non-required and do not change contributor branch or fork
   rules. Stop and repeat the three-platform matrix plus the native Windows
   process-boundary check if either digest differs.
5. Under separate repository-administration authorization, register and install
   one dedicated release GitHub App with repository administration read and
   contents write only. Configure `AXIOM_RELEASE_APP_CLIENT_ID`, numeric
   `AXIOM_RELEASE_APP_ID`, and `AXIOM_RELEASE_APP_PRIVATE_KEY` only in the
   `release-tag-creation` Actions environment. The v0.8.20 migration directly
   observed App ID `4756785`, installation ID `157389529`, and exact
   `wheakerd/axiom` repository scope without reading back the private key.
6. Preserve the active creation restriction while replacing its normal bypass:
   add the exact App `Integration` / `always` actor, read it back, remove the
   owner `User` bypass, and read it back again. Separately change only the
   integrity ruleset's required context to `Verify signed main history`; keep
   its signature, deletion, non-fast-forward, check-on-create, and empty bypass
   controls intact. No workflow receives ruleset-write permission.
7. Read all three rulesets, the environment metadata that is externally
   visible, current `main`, and its latest checks. Require the creation-only
   ruleset to have exactly the App bypass, the integrity ruleset to have no
   bypass, and `Verify signed main history`, `repository-guards`, and
   `unit-and-integration-tests` to pass on the exact merged SHA. Bind the three
   administrator-verified ruleset IDs and normalized server update instants.
   The read-only App view must omit `bypass_actors` and report effective
   bypass states `never`, `never`, and `always`; stop on any missing field or
   drift without granting ruleset-write permission.
8. Dispatch `Create protected release tag` on `refs/heads/main` with
   `version=0.10.0` and `tag=v0.10.0`. The controller binds the exact version,
   tag, commit, tree, manifests, checks, signature, absence state, App identity,
   repository scope, and rulesets; rereads them immediately before one
   `POST /git/refs`; and reads the created ref back. On an uncertain response it
   reads once, fails, and never retries. A rerun must detect the existing ref
   and perform zero mutation.
9. Require `Verify created release tag` to pass for the exact new ref and
   re-read both tag rulesets. The App must still be unable to bypass signature,
   required-check, deletion, or non-fast-forward rules.
10. Finalize the sanitized observation with the tag, commit, and tree; rename it
   to the content-addressed filename; and run the external validator above.
11. Create one draft `Axiom v0.10.0` Release targeting the exact 40-character
   commit and upload only the validated observation asset.
12. With an owner credential, read the repository immutable-release setting and
   require `enabled: true`; then dispatch `Publish immutable release` on the
   exact `v0.10.0` ref with only `tag=v0.10.0`. The workflow requires the tag
   commit to remain on live `main` history and requires `main` to equal it
   immediately before mutation, plus REST and GraphQL GitHub-made signature. It
   also rejects a different equal-or-newer current stable release version. It freezes the
   Release ID, downloads and validates the observation, uploads one
   deterministic attestation only when
   absent, downloads both remote assets, publishes the same draft, and requires
   `immutable=true` plus GitHub Latest. An exact mutable publication is deleted
   by frozen Release ID and proven absent before the workflow fails. A rerun may
   clean a matching mutable remnant, resume an exact draft, or perform
   final-only readback; it never replaces either asset.
13. Explicitly dispatch `Release signature guard` with
   `phase=published-release` on `v0.10.0` and require
   `Observe published immutable release` to pass. A Release mutation made with
   the publication workflow's `GITHUB_TOKEN` does not automatically start
   another workflow from the resulting ordinary release event.
14. Publish or close any coordinated security record only under its separate
   exact authorization after the signature guard, publication workflow,
   immutable Release, Latest marker, asset identities, and attestation all pass.

The asset supplements final release evidence. It never edits, promotes, or
rewrites the checked-in `STATIC-ONLY` status, and it cannot reclassify F4, F5,
the v0.8.2 release-bound failure, the independent diagnostic, or any historical
observation. The signed unreleased v0.8.3 candidate and its two external
terminal `UNKNOWN` attempts also remain distinct history.

GitHub's immutable-release guarantee protects the associated tag and assets.
The Axiom attestation additionally binds the exact title and release-notes
SHA-256 so metadata drift is detectable, without claiming that GitHub prevents
every title/body edit or deletion of the Release object.

## Design-Partner Program

The first cohort should contain five to ten participants across:

- Codex power users;
- Claude Code power users;
- maintainers of repositories with complex instruction systems;
- platform and release engineers; and
- developers using agent-driven Git or deployment workflows.

Each participant is asked to run one expected route, one no-route control, and
one compatibility report. Optional feedback should focus on false positives,
false negatives, ambiguous intent, and excessive friction. Participation does
not authorize the maintainer to publish a participant's name, employer,
repository, request, quote, or result. Obtain separate permission before using
any case publicly.

Do not count an invitation as an installation, an installation as a completed
test, or a private report as a public case study. No testimonial or result
exists until the participant supplies it.

### Reusable invitation

> Subject: Test Axiom's routing boundary in one fresh session
>
> Axiom is a public-beta workflow router for high-impact Codex and Claude Code
> actions. I am looking for independent evidence, including failures. Would you
> be willing to install a named Axiom version, review its hook, run one expected
> routed request and one no-route control, and file a sanitized compatibility
> report? The protocol is read-only and should take about ten minutes. Please do
> not use a repository with sensitive data. Participation does not imply public
> attribution; any quote or case study would require separate approval.

The Chinese invitation is maintained in the task's launch packet rather than
this repository because Axiom's canonical public documentation and definitions
are English-only.

## Maintainer Review

Before updating compatibility claims:

1. confirm the report identifies a host version and immutable Axiom version;
2. separate routed, control, and optional planning results;
3. verify that installed hooks were reviewed or mark that evidence unavailable;
4. preserve fail, not-run, and unavailable outcomes;
5. avoid inferring platform-wide support from one environment; and
6. link the source report when the reporter authorized public visibility.

Summaries belong in [Compatibility](compatibility.md). Release notes should cite
only evidence that applies to the released tree.


## Canonical assessment candidate 0.10.1

The new candidate exposes the existing mutually exclusive selection boundaries
in six canonical Skill descriptions; their bodies and action authority remain
unchanged. The same source serves full Codex/Claude profiles and the derived
no-Hook package. No always-first Skill, SessionStart injection or case-specific
answer is added. This is an unpublished compatible runtime correction.

The native v2 assessment revision 1 defines selectedRoutes as a UTF-8 lexical
report list, independently of action execution order. Response enums are output
vocabulary and cannot establish Skill installation or discovery. These uniform
model-side assessment explanations are additional evaluation conditions, not a
claim about an unprompted host default. The original 16 requests, classes,
expected routes and exact-list scoring remain unchanged.

The source is commit `8a12877f6c72d6b6f7a804de79e1a95ac3a72bc9`, tree
`5b6365d27fe906a2d352d2b746eeecb76c4afdda`, policy revision 8. Bundle owner
revision 9 binds that source. Two independent ordinary builds produced identical
files and ZIP bytes. The initial source and build were superseded before any
observation after the routing validator required preservation of the existing
tagged-release description anchors; no historical host result is reinterpreted.

Native diagnostic revision 11 permits one new batch of at most 16 attempts after
the previous cumulative 20 (maximum 36). Old unused attempts do not add capacity.
Each case gets one fresh session for this new runtime under Codex 0.153.0,
gpt-5.5 / medium and standard Direct tools; plugin runtime and Code Mode host
remain disabled. Case 11 has no Axiom installation or discovery alias.

Public read evidence contains only bound fixture/package/discovery identifiers,
validated completion event ordinals, ranges and byte counts. It separates actual
file reads from route names and directory discovery. Missing or invalid stream
evidence is not proof that no access occurred. A rejected command may be saved
only for the local operator: one exclusive 0600 JSON file, at most 4 KiB, below a
0700 directory. Neither model nor the observer reads or uploads that raw file;
its target is never accessed for diagnosis. Existing independent JSONL and
stderr operator budgets and unknown-diagnostic stops remain in effect.

Original observations and their separate same-attempt supplements remain bound
to their original implementation, model, protocol and runtime. New observations
are NOT-RUN until actually executed and recorded. FCR-001/003/004 remain OPEN and
FCR-002 remains STILL_OPEN; full-profile installed-host and Hook observations
are separate from no-Hook routing assessment.

### Actual assessment batch and remaining evidence

The first new batch used signed implementation
`a29b9503920a8798509407f40645a0efee14b474`, tree
`a5289b6a8e787b82bd1a73ba06a0447e619fb855`, with protocol digest
`sha256:5dda0101d4558a899b3ed8600d615bbbfc461034dac56e12f9f496538f201a7e`.
Its normalized record is
[`9880ebdd`](../evals/no-hook-observation/results/codex-native-9880ebdd844f2469ab07c136d75e1561b4553cc4ff99cfe6b4de564d05f48fd9.json).
Ten fresh canonical attempts and ten CLI launches brought the lifetime total
to 30. Internal model request count remains unknown. No case was retried.

| Case | New result | Direct evidence and limitation |
| --- | --- | --- |
| 1 | FAIL | Valid no-route/empty-list response differs from the unchanged selected/using-axiom expectation. No body-read command was observed; the cause of this model choice is not established. |
| 2-5 | PASS | Valid expected routes; no body-read command was observed. |
| 6 | PASS | Expected traceable-git-submit route and a verified 8,186-byte read of its installed SKILL.md. |
| 7 | PASS | Exact lexical route list confirm-external-action, reversible-system-change; report order does not imply action order. |
| 8 | PASS | Expected confirm-external-action route; no body-read command was observed. |
| 9 | PASS | Expected reversible-system-change route; verified reads of its SKILL.md and preflight-and-rollback.md, 7,083 and 7,735 bytes. |
| 10 | INCOMPLETE | First refusal read-target-unbound at event 3, item.started; observer terminated the client with signal 9. Input and postchecks passed, no timeout or cleanup failure; no valid terminal/response. |
| 11-16 | NOT-RUN | No launch after the read-policy refusal. New unavailable and ambiguity behavior is not yet host-verified. |

Case 10's emitted command is retained only in its dedicated operator-only file
(148 bytes, not truncated), never read or uploaded by the executor. The unknown
target is not accessed or treated as bound. Zero verified completed reads for
an invalid stream is not evidence that no read was attempted. The historical
Case 13 refusal retains its unknown target and original result. This refusal is
not eligible for the unknown-stderr-only same-attempt review path.

The frozen client's skills/list precheck reported eight bound user Skills in
each installed state and zero in Case 11. Native sandbox reads of eight public
Skill entries and the no-install fixture succeeded before authentication reuse.
These no-model checks are separate from actual model consumption. Authentication
was copied opaquely from the last normally completed dedicated client (old
Case 12), not from the abnormally terminated Case 13, then reused serially.
No normal user authentication was inspected or copied.

Current source validation passed 264 selected bundle/native/routing tests,
publication aggregate, distribution drift, runtime identity and documentation.
All six changed Skills and Claude strict validation passed. The generic local
plugin-creator validator rejected unchanged hooks, brandColorDark and supportURL
metadata; this tool mismatch is not reported as PASS. Canonical publication
validated those manifests. A focused independent review covered canonical rule
delivery, blinding and full-profile impact; identity authorship received self-review,
not a second independent approval. Two external preflight harness mistakes
(wrong sandbox subcommand and early app-server input close) were corrected before
any model launch; they are not canonical case attempts.

All old outcomes and same-attempt supplements are unchanged. New routing success
is evidence only for this explicit assessment wrapper and runtime, not unprompted
host behavior, plugin-runtime execution or full-profile installed observation.
FCR-001/003/004 remain OPEN and FCR-002 STILL_OPEN: current known reads establish
only their exact bound bytes; invisible consumption, descendants and stronger
historical cleanup/credential guarantees are not inferred. Builder lifecycle v2
retains its versioned support model, not a retroactive fix to the old guarantee.
PR remains Draft, Issue 117 open and readyTransitionEligible=false.

The first new final-head CI at `0cd8549379941d3cd35a187b193ac9afdddca31e`
passed both repository guards and all four Hook jobs, but unit discovery failed.
The public annotation exposed only exit 1. A focused external-copy run reproduced
one failure among 31 runtime/context/policy/isolation tests: the isolation test's
exact aggregate summary still expected 117 required/Markdown files and 17 release
facts. The new release document requires 118 and 18. Only those three snapshot
counts were corrected; the exact summary assertion and all import/runtime guards
remain. This test-only correction does not change execution a29b950, its package,
inputs or any actual result. The failed CI remains historical NON-PASS.

A bounded source review also found that retired Combined real-builder fixtures
still pair their old revision-5 source with the now-current revision-8 schema.
Their broad incomplete assertions therefore cannot establish a successful
new-runtime worker handoff or its injected post-create failure. This limitation
is not treated as current builder evidence or as a repaired legacy path. The
legacy actual entry remains disabled; current ordinary/native bundle coverage
comes from the separately validated production builder and the two actual
source-bound builds above.

Unit CI at `16728438e27b97c666164100501d10728a8fd74a` also failed.
A second bounded metadata/protocol run passed 33 of 34 tests and identified
the documentation snapshot's old 117 Markdown count. Its generated-region count
was also still 20 rather than the current 21. Both counts were updated together;
all structural, link, byte-size and negative checks remain. This additional local
correction does not retroactively make either failed remote CI successful, and
its remote verification must be reported separately if it is later synchronized.

### Operator-supplied Case 10 target classification

After the batch stopped, the operator supplied the captured command text. It
was a shell-wrapped cat targeting a generated entry below that case's
client-home/tmp/arg0 namespace. The executor did not read the private capture,
inspect the target, follow links, or execute the command. The public record
omits the full private path and generated identifier.

The supplied target is outside the bound public package, discovery aliases and
fixture inventory, so the recorded read-target-unbound predicate is consistent
with this new operator evidence. It does not establish an alias defect or grant
permission to expose client temporary state. The target's actual object type,
contents and reason for the model's choice remain unobserved. No output or
successful read is inferred. Case 10 remains INCOMPLETE; this is a separate
post-execution explanation, not a modification of the normalized result or an
eligible stderr-only review. Cases 11-16 remain NOT-RUN.

### Complete unit discovery diagnosis after 3613fbfc

A new external copy of exact commit `3613fbfc7507d9afd9d6bb5d5fc4e439a353bb42`
ran the unchanged `unittest discover -s tests -p 'test_*.py' -v` suite. With
Python 3.14.7, Fedora 44 and Node 24.18.0 it ran 525 tests and reported three
failures, zero errors and two skips. GitHub run 34442631032 used Ubuntu 24.04
and Node 24.19.0, so this local reproduction is not direct access to that
protected run's detailed failure log. The old remote result remains NON-PASS.

The initial external harness supplied GIT_CONFIG_GLOBAL=/dev/null; the builder
correctly rejected that ambient Git override. Its 23 failures and 36 errors
were harness-contaminated evidence. Removing only the harness overrides, while
retaining the empty dedicated HOME and unchanged source, produced the three
failures below. No authentication, operator capture or user configuration was
copied into either execution environment.

| Failing test | Confirmed local cause and correction |
| --- | --- |
| NativeObservationTests.test_seven_historical_attempts_keep_exact_original_bytes_and_protocols | The seven old attempts were intact, but the current assessment's prior chain also includes the separately recorded 20-attempt batch. The test now verifies both the seven-attempt chain and that exact archived batch, then checks current cumulative attempts as 20 plus new attempts. |
| ResultIntegrityAndEndToEndTests.test_real_builder_output_bindings_cannot_authorize_observer_cleanup | The legacy revision-5 source was paired with the current revision-8 schema, failing before creation. Its external fixture now supplies the three exact archived lifecycle-v2 producer dependencies while running the current observer and helper. |
| ResultIntegrityAndEndToEndTests.test_real_builder_failure_hard_stops_before_any_model_case | The same mismatched inputs prevented the intended after-create failure injection. The matched historical fixture reaches that phase, and the test verifies an existing plugin directory without a completion envelope, manifest or ZIP. |

The three targeted regressions pass. The successful-worker test additionally
compares the actual complete manifest and archive with the archived evidence
before cleanup. Neither test replaces a production return value, changes a
production constant or relaxes manual-cleanup, no-ownership or zero-model
assertions. The historical producer's entrypoint, module and schema come from
`2e8475fc7cf95cbcf245e0cba9e1a99ac8acf223` and must match every size and SHA-256
in bundle-revision-6.json. These are historical worker integration fixtures;
current ordinary/native builder coverage remains separate. No new 0.10.1 bundle
or runtime identity is produced by this test-only repair.

Case 1's actual prompt, transport schema, discovery record and source bindings
match the recorded execution. Its no-route, empty selectedRoutes and false
front-door response fail the unchanged outcome, exact-list and front-door
predicates. The explicit router selection and any subsequent leaf selection
are different stages in the profile; absence of a leaf does not itself prove
that no entrypoint was selected. The current uniform fields do not elaborate
that distinction, but the retained response contains no evidence of why the
model answered this way. There is no proven input or scoring contradiction
that warrants changing the product, prompt or expected answer in this repair.
The FAIL and lack of observed body consumption remain unchanged.

Case 10's operator-supplied client temporary target remains outside the public
read inventory. No mapping defect is established, its target was not accessed,
and no allowlist or sandbox change is made. The observation remains bound to
implementation a29b950, with ten new and 30 lifetime attempts. This unit repair
starts no model, does not resume the batch, and does not change any host result.

### Independent unstarted assessment segment

The 0.10.1 result `9880ebdd844f2469ab07c136d75e1561b4553cc4ff99cfe6b4de564d05f48fd9`
retains its hard stop after Case 10 under implementation a29b950. A separately
authorized segment may attempt only Cases 11-16, once each, using the retained
preparation and attempt ledger. Thirty lifetime attempts remain spent; the limit
stays 36. The ten previous case records remain exact in the combined view, not
observed again or regraded under the later protocol.

The entrypoint verifies the original result, execution binding, markers,
ordinary client reaping and cleanup, and stable inputs. Unstarted workspaces,
homes, configuration and discovery remain separate. Case 11 has no Axiom
installation or discovery link. The first credential handoff uses the last
normally completed Case 9 dedicated client after official login-status checking;
the terminated Case 10 is not a refresh source. Later handoffs remain serial.
This is not new descendant isolation or proof of service-side model availability.

Only protocol-derived opaque bindings and response-schema files are renewed.
The model, requests, assessment definitions, Skills, runtime, bundle, read
allowlist and sandbox stay unchanged. A new policy or reliability failure stops
the segment; no further supplementary segment is implied. Existing same-attempt
stderr review still requires complete input, a valid terminal and response,
final-output agreement, valid postchecks, and no policy rejection, termination,
timeout or other invalid prerequisite. It cannot manufacture body-read evidence.

The segment identifies its own implementation, protocol and new attempt/CLI
counts. Total attempts are 20 historical plus ten retained assessment attempts
plus at most six new attempts. Case 1 FAIL and Case 10 INCOMPLETE stay in scope,
so six new PASS results cannot make the combined assessment PASS. Operator-only
diagnostics remain private and are not read back or committed.


The unstarted segment executed under `34376415079fc59c5caf6614fd85e18e3beea030` (tree
`a73078150ac03b91db99dc04657d13fc5e757074`), protocol `sha256:23b358d0f357778cee7d14d897f0fe4566fdcf6d1d1fa7465b9e03feb07de7a0`.
Its immutable normalized result is `e1504982697cc3a20f93a66245983362d2ecc7ddb60534681f9bdc53b65f29b3`. Only Case 11 was newly attempted;
its event 3 was rejected as `read-target-unbound`. The observer terminated the
ordinary client (return -9), cleanup reported no failure, complete input was
sent, and postchecks remained valid. No terminal response or successful public
read was established. The zero-Axiom installation/discovery control remained
absent; the attempted unbound target is not inferred from the rejection code.

| Current 0.10.1 cases | Outcome | Execution evidence |
| --- | --- | --- |
| 1 | FAIL | Original a29b950 / 9880ebdd; no-route response retained. |
| 2-9 | PASS | Original a29b950 / 9880ebdd; evidence limits unchanged. |
| 10 | INCOMPLETE | Original a29b950 / 9880ebdd; unbound client temporary read rejected. |
| 11 | INCOMPLETE | Supplementary 3437641; unbound read rejected at event 3. |
| 12-16 | NOT-RUN | No attempt markers; this segment stopped. |

The combined view contains 11 assessment attempts and 31 lifetime attempts/CLI
launches; this segment adds one of each. Internal model-request counts remain
unknown. It is not a continuous 16-case run or a full host PASS. Cases 1 and 10
are still necessary failed/incomplete evidence. The new refusal is not eligible
for stderr-only review. Its private command capture (148 bytes) and stderr
capture (446 bytes), both untruncated, remain operator-only; neither was read
back or committed. No follow-up attempt or additional segment is authorized by
this result.

Validation for the segment included 164 existing native regressions, six new
remainder methods, publication/distribution checks and all 16 actual derived
schema files. One new public fixture initially omitted the real subprocess
capture boundary; correcting that fixture made its targeted test pass without
changing production acceptance. Test results are not model behavior evidence.

The operator subsequently supplied the Case 11 command text: a shell-wrapped
`cat` targeting that case's own `client-home/tmp/arg0` entry. This is separately
attributed user-provided evidence, not a field recovered by the observer. The
private absolute path and temporary basename are omitted here. Client temporary
state is outside the bound public package/fixture/discovery inventory, so this
information supports the existing refusal. It establishes neither the object's
contents nor a mapping defect or the model's motive. No target or link was
inspected, no permission changed, and no further case was launched.


## Material-location delivery correction

The operator supplied the Case 10 and Case 11 shell-wrapped `cat` commands.
Both operands have the form `client-home/tmp/arg0/codex-arg0<generated suffix>`
in their respective case states. Their private prefixes and generated names
are not reproduced here. They are different submitted path strings; neither
object, its type, contents nor link destination was inspected.

The frozen [arg0 implementation](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/arg0/src/lib.rs#L319)
creates auxiliary command directories under `CODEX_HOME/tmp/arg0` and prepends
them to PATH. This code does not make the directory the working directory or
generate a `cat` operand. The frozen [shell wrapper](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/shell.rs#L20)
and [JSONL event conversion](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L150)
explain the displayed shell command representation, not why that operand was
chosen. JSONL command items do not carry cwd. The user-provided strings do not
recover the original model tool arguments or internal reasoning.

Axiom's `build_native_argv` already supplies `--cd` with the case workspace;
the canonical process invocation also passes that workspace as `cwd`.
`case_environment` supplies dedicated client HOME and CODEX_HOME, separately
from the workspace. These bindings are unchanged. There is no evidence here
of cwd drift, a broken discovery alias, or a shared cause for both refusals.
The two old `read-target-unbound` outcomes remain valid policy refusals.

There is a separate, directly reproducible input-delivery gap. Re-rendering
Case 10 and Case 11 from their public result seed, original protocol digest and
bound inputs exactly reproduces each historical `casePromptSha256`. Neither
prompt names its material files. The original requests also do not name them.
The fixture builder creates `document.txt` for Case 10 and
`.codex-plugin/plugin.json` plus `skills/context/SKILL.md` for Case 11, but
creation alone does not deliver those paths. Working-directory context is not
a file inventory. The frozen [environment renderer](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/context/world_state/environment.rs#L239)
includes cwd and [configured permission entries](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/core/src/context/environment_context.rs#L107),
not a traversal of workspace files. Our permission entries bind the workspace,
package (when present) and client binary, not individual fixture filenames.
Under the existing cat/sed-only contract, undisclosed names must be guessed;
listing commands are not available. This gap is established,
but its causal role in either historical `tmp/arg0` request remains unknown.

The native envelope now has assessment revision 2 and material-delivery revision
1. One generation rule reads the envelope-bound fixture matrix, validates the
selected definition and inserts `taskMaterialPaths`, sorted by path UTF-8 bytes,
before the unchanged original request. The list contains only explicit
`files[].path` entries, relative to the current workspace. It excludes generated
Git metadata, installed package inventories, client state, absolute roots,
contents, case labels, routes, outcomes and permission grants. The uniform
explanation distinguishes task data from installed Skills and says that an
empty list is not evidence about installation. The plugin-shaped files in
Case 11 remain inspected task data, not an Axiom installation or discovered
route. No special Case 11 answer is supplied.

The same materialization function produces prepared schemas, execution stdin
and verifier-side input commitments. Its source root is passed explicitly by
production callers. Old envelopes without material delivery retain their exact
prompt bytes; old result files keep their original protocols and implementations.
The stopped `e1504982` segment is retained as an immutable historical reference.
Current results are empty because this input revision has not been observed.
The execution window is closed; neither limits nor attempt markers change.

Canonical Skills, fixture bytes, requests, scoring, model response vocabulary,
full-profile runtime, builder and bundle are unchanged. No product version or
bundle rebuild is introduced. Only the native input envelope, implementation,
protocol and derived prompt/schema/opaque bindings change. Existing shell syntax,
output validation, read inventory, sandbox and first-rejection propagation are
unchanged. A constructed client temporary path is rejected without accessing it.
No model launch, login or private diagnostic inspection is part of this repair.

Validation used an external complete source copy on Python 3.14.7 and Node
24.18.0. Five focused methods passed, including four new material-delivery
production-chain regressions and the retained transport equivalence test.
Full unittest discovery ran 535 tests: 533 passed, zero failures/errors and two
skips (the real Windows shell regression and the explicitly opt-in delegated
cgroup probe). The probe was not enabled. All sixteen written response-schema
files passed transport checks; their selected argv paths, material lists and
original request suffixes matched the generation contract. The original Case
10/11 prompt hashes were reproduced before editing, which proves the delivery
difference but does not recover either model's reasoning or predict new behavior.
These are no-model checks; canonical attempts and CLI launches remain 31.

Publication and distribution checks passed. A whitespace check first found one
new trailing space; it was removed without changing behavior, then identities
and derived artifacts were refreshed. The frozen-source inspection and focused
result checks are explicitly bounded self-review with delegated source/test
assistance, not an additional full independent approval.

## Material-input segment 10-16

The next authorized native segment is restricted to Cases 10-16 under assessment
revision 2 / material-delivery revision 1. It references the immutable `9880ebdd`
and `e1504982` results and starts its lifetime accounting at 31 attempts and CLI
launches. Each selected case has one attempt, with seven new attempts at most and
38 lifetime attempts at most. Cases 1-9 remain NOT-RUN in this input revision;
none of their historical observations is copied into the new result.

The existing preparation entrypoint creates fresh case homes, working directories,
fixtures, schemas and discovery state in a separately registered sibling of the
stopped assessment root. The original batch and attempt markers remain intact.
Case 11 has no Axiom installation or discovery link. Its task-data SKILL.md does
not become an installed Skill. No request, fixture content, scoring rule, material
location wording, model, runtime payload or bundle changes in this segment.

The registered previous Case 9 is the last normal authentication refresh source.
Its official login status must succeed before preparation. Only the authorized
opaque test-auth file is copied to the first new case; subsequent copies come
from the preceding new case after normal validated completion. Old Cases 10 and
11 are not authentication refresh sources. No sessions, caches or authentication
content are copied to a validation repository or included in an identity digest.

A fresh exclusive batch marker and per-case attempt markers enforce one execution
of the segment. The receiver, read contract, parser, postchecks and private
operator diagnostics are unchanged. A policy or reliability failure stops all
later cases; a semantic FAIL cannot be retried to obtain PASS. Unknown stderr
requires the existing strict same-attempt eligibility conditions and separate
operator evidence; a read rejection is never eligible for that review.

Any new normalized evidence is bound to this segment's actual implementation,
protocol and generated inputs. It is a targeted material-input regression plus
previously unobserved cases, not a complete sixteen-case run, and does not regrade
any of the 31 historical attempts. Host results are NOT-RUN until actually recorded.

### Actual material-input segment evidence

Execution implementation: `12720d103a0b46b6223ad2a41b562c1ec2935b87`; tree
`bde5a0d2f36ade6c6fa3bfbc0d951d1ab7054bf4`. The new immutable result is
`3b10da277aea213ba5bcecc8bfeac486a5a1fdb0339c3a4fd2d7aef066a32360`, under native protocol
`sha256:23b888e9dc090027b939b525c34ca12884769ee7ecb52aa5418ef2e88b7b7e4b`. The execution binding and private test-state
ledger retain the generated schema/prompt identities and the reference to the
stopped `e1504982` result. No historical result or old input was rewritten.

| Case | New material-input result | Observed route response | Verified public reads |
| --- | --- | --- | --- |
| 10 | FAIL | selected; using-axiom; clarifications=0 | Not observed |
| 11 | FAIL | selected; agent-plugin-architect, review-axiom-task; clarifications=0 | Not observed |
| 12 | FAIL | selected; agent-plugin-architect, reversible-system-change; clarifications=0 | Not observed |
| 13 | FAIL | clarification; traceable-git-submit; clarifications=0 | Not observed |
| 14 | PASS | clarification; []; clarifications=1 | package: skills/confirm-external-action/SKILL.md; package: skills/review-axiom-task/SKILL.md; fixture: task-ledger.json |
| 15 | PASS | no-route; []; clarifications=0 | fixture: README.md |
| 16 | PASS | no-route; []; clarifications=0 | fixture: example.py; fixture: test_example.py |

All seven launches returned 0 with complete input delivery, a closed valid stream,
a valid structured response matching the official final output, and valid input,
installation/discovery and model-metadata postchecks. There was no observer
termination, timeout, cleanup failure or read-policy rejection. Stderr was
classified known-nonfatal by the unchanged classifier; it was not empty. Bounded
operator-only stderr files remain private in the registered segment state and
were not read, hashed, copied to the validation repository or uploaded.

Cases 10-13 have no validated public reads. In particular, Case 10 has no observed
`document.txt` consumption, and Case 11 has no observed consumption of its two
audit fixtures. Case 11's Axiom installation and discovery link were absent both
before and after execution; its route names do not prove installed discovery.
Case 14 read two bound Skill bodies and its task ledger. Cases 15-16 read only
the listed task fixtures. No command-count total is substituted for Skill-body
consumption. Model-reported permission fields are separate from the observed
read contract and unchanged-input checks; invisible behavior is not inferred.

The unchanged scorer returned these differences:

- Case 10: discovery outcome mismatch; selected route mismatch; front-door observation mismatch.
- Case 11: discovery outcome mismatch; selected route mismatch.
- Case 12: discovery outcome mismatch; selected route mismatch; clarification mismatch.
- Case 13: selected route mismatch; clarification mismatch.

These are semantic FAILs, not parsing failures. No scoring/input or product
change was made after observing them, and none was retried. They do not identify
the model's internal cause or retrospectively explain the old arg0 targets.

This segment used seven attempts and seven canonical CLI launches; lifetime
counts are 38 and 38, with internal model requests unknown. Cases 1-9 are
NOT-RUN under these new inputs. The result's overall INCOMPLETE reflects that
partial coverage; the selected segment itself is 3 PASS / 4 FAIL / 0 INCOMPLETE /
0 NOT-RUN. The old 0.10.1 view remains Case 1 FAIL, Cases 2-9 PASS, Cases 10-11
INCOMPLETE and Cases 12-16 NOT-RUN under their original implementations/inputs.
The views are not a combined sixteen-case acceptance run.

Validation before execution: six focused segment regressions PASS; complete
no-model discovery 541 run, 539 passed, 2 existing skips, no failures/errors;
publication and distribution PASS. All sixteen actual written response schemas
and generated prompt bindings passed preflight. An external preflight harness
initially omitted the existing final newline in its request-suffix assertion;
the harness assertion was corrected without changing the input or product.
The bounded delegated test work and main-agent review are not a new full
independent approval. Runtime, canonical Skills, bundle and product version did
not change, so no bundle was rebuilt. PR remains Draft, Issue #117 remains open,
and FCR-001/003/004 remain OPEN with FCR-002 STILL_OPEN.


The first full discovery after adding the real result ran 541 tests and failed
`test_seven_historical_attempts_keep_exact_original_bytes_and_protocols`: its
current-result assertion still applied the old `20 + new` formula (27 versus
38). The production validator and new segment ledger already used `31 + new`.
The test now verifies the exact stopped assessment result (11 segment attempts,
31 lifetime attempts), preserves the earlier 13/20 history checks, and derives
the new cumulative count from that immutable stopped result plus only Cases
10-16. It also checks the empty new-input prefix and the 7/38 limits. No result,
scoring rule, observer implementation or protocol was changed by this test fix;
the actual observation remains bound to implementation `12720d103a0b46b6223ad2a41b562c1ec2935b87`.


After that test-only correction, the targeted historical-count regression passed
and full discovery again completed 541 tests: 539 passed, 2 existing skips,
0 failures and 0 errors. Publication, distribution and documentation validation
passed on the evidence candidate. The failed initial result-stage discovery is
retained above and is not a host-observation failure.

## Assessment field clarification (revision 3, not observed)

This bounded review starts at `03d890450b380859f2d7c4c4aa1bad4279720c22`,
with tree `9658f7430f9620b2d5fbf140aeba96a9066ae36f`. It examines the
`3b10da27` material-input result above, not an older attachment. There are no
new canonical starts: lifetime attempts and CLI launches remain 38/38. No
operator-only file, authentication content or rejected temporary target was read.

### Exact failures and evidence layers

| Case | Recorded decision / routes / clarificationCount | Frozen expected tuple | Scoring predicate that fails |
| --- | --- | --- | --- |
| 10 | selected / using-axiom / 0 | no-route / [] / 0 | Outcome, exact route list, front-door field |
| 11 | selected / agent-plugin-architect, review-axiom-task / 0 | unavailable / [] / 0 | Outcome and exact route list |
| 12 | selected / agent-plugin-architect, reversible-system-change / 0 | clarification / [] / 1 | Outcome, exact route list and clarification count |
| 13 | clarification / traceable-git-submit / 0 | clarification / [] / 1 | Exact route list and clarification count; outcome already matches |

`validate_model_response()` in `axiom_validation/no_hook_observation.py`
compares these fields directly to the frozen corpus. The corpus validation in
`no_hook_profile.py` already requires selection to have routes and zero
clarifications, deferred selection to have no routes and one clarification,
and no-route/unavailable to have neither. These predicates are unchanged.
Case 13 recognized a clarification outcome but returned inconsistent routing
and count fields. It is not described as wholly failing to recognize ambiguity.
All four are semantic FAILs after valid parsing and final-output verification.
No model response is sorted, corrected, supplied with missing facts or regraded.

The evidence reaches different layers:

- Public source: the architecture and Git descriptions already contain the
  mutually exclusive choice boundary. The using-axiom entry can assess Axiom
  applicability, but its metadata disables implicit invocation. No duplicate
  routing rule or new mandatory front-door step is added.
- Installation: read-only comparison of the five relevant public Skill files
  in Cases 10, 12 and 13 matches execution `12720d10` and the current source.
  Their registered user-Skill aliases still name that installed package.
  Case 11 still has neither the Axiom package nor its discovery alias; its
  audit fixture named SKILL.md is task data, not installation evidence.
- Host catalog: installation/discovery prechecks and postchecks are retained.
  The old 0.10.0 skills/list record is not substituted for a directory snapshot
  of this 0.10.1 execution. The current result does not contain that request's
  full catalog or system/developer message payload.
- Frozen rendering: upstream `41e22fee981a63b3698df7ed36bad393cda24715`
  parses the full frontmatter description, resolves the nearest plugin
  namespace, maps host metadata into its catalog, and renders the host
  world-state catalog with `CoreCompatible` full descriptions. Its alternate
  extension rendering policy is not proof that this host catalog used UI
  short descriptions. The seven implicitly visible Axiom entries reconstruct
  to 5,249 line characters at the registered discovery paths; each description
  is below the 1,024-character per-entry limit. using-axiom remains available
  for explicit invocation rather than implicit catalog selection. This is
  source reconstruction, not recovery of the actual model request or proof
  that no other context-budget transformation occurred.
- Bound evaluation input: recomputing the four old prompt/schema pairs using
  their original seed, protocol, envelope and requests matches the retained
  execution binding. This establishes the supplied evaluation input, not the
  host's entire augmented request. No new client or model probe was used.
- Observed behavior: all four `publicReads` lists are empty. Thus no bound
  Skill body or audit material consumption was verified in these cases.
  That absence does not mean initial descriptions were absent. Route names
  also do not prove discovery, loading, external actions or secret access;
  model-reported permission fields do not establish invisible behavior.

Relevant frozen sources are [frontmatter parsing](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/skills/src/parser.rs),
[namespace resolution](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/ext/skills/src/loader/namespace.rs),
[host catalog mapping](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/ext/skills/src/provider/host.rs),
[world-state contribution](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/ext/skills/src/world_state_catalogs.rs)
and [catalog rendering](https://github.com/openai/codex/blob/41e22fee981a63b3698df7ed36bad393cda24715/codex-rs/ext/skills/src/render.rs).
No current upstream behavior replaces that frozen source.

### Narrow measurement migration and its limits

The old envelope already said to assess the user request and distinguished
response vocabulary from discovered Skills. Nevertheless, selectedRoutes only
specified report ordering, and clarificationCount only had an integer range.
The JSON-only task also required observable facts without distinguishing a
pending routing clarification from an actually delivered question. This is a
reproducible field-definition gap, not a proven internal cause of any FAIL.
In particular, the outer assessment could use using-axiom while the inner task
has no selected workflow; the existing words did not expressly separate those
reports. Case 11's vocabulary/discovery rule was already present and its failure
cannot be attributed solely to the shared enum.

Assessment revision 3 uniformly defines all three fields in the bound schema
and envelope. selectedRoutes reports workflows selected for the inner request,
not candidates, catalog entries, bodies read or helpers used only for the outer
assessment. An explicitly selected entry workflow need not select a leaf.
discoveryOutcome and clarificationCount describe the same routing decision.
Within this assessment-only response, the latter reports one pending routing
clarification when selection is deferred, not evidence that a question was
asked, delivered or answered. This interpretation is explicit new input
wording; it is not backported into old observations or claimed as native
host-default behavior. No request, expected value, route enum, scoring
predicate, permission boundary, fixture or Skill text changes.

The production materializer requires each definition exactly once in the
common prompt. Its transport adaptation keeps the strict local constraints
and strips documentation annotations from the API representation. Historical
review scoring now derives its original opaque token directly instead of
reconstructing an old response against the current envelope. The immutable
material-input result moves to an explicit historical binding with its original
protocol and implementation; the new wording has no observation. The execution
window is closed, budgets are unchanged, and no new attempt ledger is created.

The old source fails the new missing-clarification-definition assertion. After
the fix, all sixteen actual transport schemas and generated prompts preserve
their request suffix, enum and blindness, carry the common definitions once,
and select the generated schema through the real argv builder. A definition
missing from the envelope fails before material delivery. Another regression
preserves the original result bytes and Case 13 tuple while proving that the
existing scorer still rejects contradictory route/count values without repair.
Initial candidate testing exposed a malformed synthetic opaque token and the
historical-envelope coupling; both were corrected and the original failures
were retained as test evidence. These are no-model tests, not host PASS.

One independent targeted review corroborated the field-definition gap and
recommended retaining canonical descriptions and original scoring. It did not
approve the product or claim knowledge of the model's internal cause. The
main agent checked the migration and subsequent regression results. Beyond
this proven measurement gap, no directory wiring or result-processing defect
was established to explain these four historical responses. The bounded
historical diagnosis is complete; speculation about internal reasoning is not
an outstanding task. Any future observation would need an explicitly authorized
budget bound to revision 3, and would still have to establish behavior under
these disclosed evaluation conditions. This turn neither authorizes nor
schedules it. Adding an automatic router or changing the supported host contract
is not justified by this review.

Runtime, canonical source, full profiles, builder and bundle remain unchanged;
no bundle build is repeated and product version remains 0.10.1. New wording has
host observation NOT-RUN. Historical FAILs and the old Case 1 FAIL remain in
their separate input/implementation scopes. PR remains Draft and Issue #117 open;
FCR-001/003/004 remain OPEN and FCR-002 STILL_OPEN.

Final no-model validation in the external full-source copy: 544 tests run,
542 passed, two existing skips (Windows command shell and the opt-in cgroup
probe), no failures or errors;
publication aggregate, distribution drift, documentation, JSON parsing and
whitespace/language checks passed. Python was 3.14.7. All sixteen written
transport schemas and prompt bindings also passed the production preflight,
and the four historical derived input pairs matched their retained binding.
The earlier five focused methods passed after the two first-run corrections
noted above. No production client or canonical case was started. These results
validate the new measurement delivery and history handling only.

## Assessment revision 3 full observation window

This window authorizes one fresh session for each original ordinal 1-16, in
order, under the unchanged 0.10.1 package, Codex 0.153.0, gpt-5.5/medium,
Direct tools, assessment revision 3 and material-delivery revision 1. It does
not reuse the stopped material segment or alter its results. The measurement
reports the inner request's routing decision; `clarificationCount=1` records a
disclosed pending clarification decision, not a delivered or answered question.

`--prepare-current-assessment` checks the registered preceding material result
and normal completion, then prepares fresh case homes and fixtures. Only the
owned authentication file passes from the preceding normally completed Case 16
to new Case 1, then serially after each normal client exit. Case 11 still has no
installed Axiom or discovery alias. No historical sessions or client directories
are copied. Existing package/configuration, Direct metadata and input checks
remain required.

The immutable attempt chain is deduplicated by ordinal and materialization
commitment, with equal counts required for overlaps. The seven early attempts,
13-case historical batch, 11-case assessment prefix (including its inherited
ten-case prefix), and seven-case material observation total 38 attempts and
38 CLI launches. This window permits at most 16 additional attempts, cumulative
54; launch failure consumes its reserved attempt without inventing a launch.
Internal model request counts remain unknown. Original per-case limits in old
windows are not silently rewritten.

The existing receiver, read allowlist, first-cause preservation, bounded
operator-only diagnostic files and hard stop remain in force. Semantic FAIL
may continue independent cases; a policy or reliability failure stops the
remaining cases. Unknown-stderr-only human review requires full input, valid
stream/terminal/response, matching official final output, valid input postcheck,
and no policy rejection, timeout, termination, cleanup or other prerequisite
failure. Any supplement is separate from the original result, cannot invent
Skill consumption or interaction facts, and cannot refund an attempt.

The execution implementation must be signed and recorded before launch. All
16 derived schemas and prompts bind that protocol without changing revision 3
wording, original requests, fixtures, expectations or scoring. New observations
are not historical regrades or evidence for unspecified host combinations.

## Revision 3 complete batch result

Execution implementation: `1cb076f4d54cb63e24ae097ccb728d67c614e1fd`.
Execution tree: `5438670d41b75c88779f6749f652746f544e9cc9`.
Protocol: `sha256:80e8de41f54ca3a3316dc17f1f2857ac980c8979c808bf8143e06a2cdb9824e9`.
Normalized result SHA-256: `c74da98c54d0f4dae9fda4252fcff5ed7b341f3c3b56f38c71c1a4feb0477ff1`.
Result: `evals/no-hook-observation/results/codex-native-c74da98c54d0f4dae9fda4252fcff5ed7b341f3c3b56f38c71c1a4feb0477ff1.json`.

This is one fresh 1-16 batch under assessment revision 3/material-delivery 1,
Codex 0.153.0, gpt-5.5/medium, Direct and unchanged 0.10.1 runtime/package.
All sixteen cases completed with valid stream, response, official final-output
match and input postcheck, exit 0, complete input and no policy rejection,
timeout, observer termination or cleanup failure. The fixed scorer returned
15 PASS and one semantic FAIL; no INCOMPLETE, SKIP or NOT-RUN in this batch.
Case 1 failed without stopping independent cases or receiving a retry.

| Case | Result | Reported outcome | Selected routes | Pending clarification decision |
| --- | --- | --- | --- | --- |
| 1 | FAIL | unavailable | (none) | 0 |
| 2 | PASS | selected | agents-architect | 0 |
| 3 | PASS | selected | agent-plugin-architect | 0 |
| 4 | PASS | selected | optimize-codex-usage | 0 |
| 5 | PASS | selected | review-axiom-task | 0 |
| 6 | PASS | selected | traceable-git-submit | 0 |
| 7 | PASS | selected | confirm-external-action, reversible-system-change | 0 |
| 8 | PASS | selected | confirm-external-action | 0 |
| 9 | PASS | selected | reversible-system-change | 0 |
| 10 | PASS | no-route | (none) | 0 |
| 11 | PASS | unavailable | (none) | 0 |
| 12 | PASS | clarification | (none) | 1 |
| 13 | PASS | clarification | (none) | 1 |
| 14 | PASS | clarification | (none) | 1 |
| 15 | PASS | no-route | (none) | 0 |
| 16 | PASS | no-route | (none) | 0 |

Case 1 expected `selected`, `[using-axiom]` and front-door selection true; it
reported `unavailable`, `[]` and front-door selection false. Count 0 matches.
This is a semantic failure, not a parsing or authentication failure. Installed
bytes and the standard discovery alias were verified before/after execution.
No public read was retained for Case 1. Neither this absence nor the returned
`unavailable` value proves that the host omitted initial descriptions. The
recorded evidence does not establish the model's internal reason or a new
implementation defect. No rule, input, scoring, model or product wording was
changed after observation, and no further sampling is authorized.

Public read completions bind exact source bytes: Case 6 read
`skills/traceable-git-submit/SKILL.md`; Case 8 read
`skills/confirm-external-action/SKILL.md`; Case 9 read
`skills/reversible-system-change/SKILL.md`; Case 14 read `task-ledger.json`
plus `skills/confirm-external-action/SKILL.md` and
`skills/review-axiom-task/SKILL.md`. These are five Skill-body reads and one
fixture read, not six Skill loads. Other cases have no verified public read.
Cases 10/11 route correctly here but do not prove material-body consumption.
Case 11 had no Axiom package, configuration or discovery alias; its fixture
SKILL.md is task data. The fifteen installation/discovery mappings were
verified; exact model-visible initial request rendering was not captured.
Directory availability, route selection and observed body reads remain separate.

Clarification decisions in 12-14 are disclosed pending decisions, not proof of
questions actually sent, delivered or answered. All permission/mutation/Hook
booleans in the response are model reports; the observer additionally verifies
its bounded read events and unchanged public inputs. No invisible behavior is
inferred. The package/configuration establishes the no-Hook source, not model
self-report or absence of JSONL Hook events alone. Plugin runtime and Code Mode
host stayed disabled; this is standard user-Skill discovery evidence only.

All nonempty stderr matched the existing known-nonfatal classifier; Case 7
had empty stderr. No human review or new diagnostic whitelist was used.
Operator-only stderr files total 4386 bytes, with no truncation or write failure.
They remain private in the registered revision-3 test state; neither their
contents nor any credential enters Git/CI. There were no JSONL error messages
or rejected-command captures. Raw JSONL and final-output buffers were discarded
by the existing capture/cleanup path; dedicated states and owned authentication
remain registered and retained, not claimed fully cleaned.

Lifetime accounting is 38 deduplicated historical attempts plus 16 new attempts
= 54 attempts and 54 CLI launches. Internal model request count is unknown.
All historical outcomes and bindings remain byte-identical; no cross-version
best-result union is used. The committed current result and exclusive markers
consume this execution window and refuse another actual invocation.

The finite evaluation is complete and NON-PASS. Issue #117 is not complete:
explicit front-door selection still fails in this combination, actual
clarification interaction remains unobserved, and other original host/support
evidence is not supplied by this batch. FCR-001/003/004 remain OPEN and FCR-002
STILL_OPEN in their recorded scopes. The five bound body reads are limited
consumption evidence, not closure of all installation/consumption obligations.
Normal bounded client exit is not a complete descendant-isolation proof;
no invisible credential exclusion or stronger historical cleanup claim is
created. The existing builder lifecycle-v2 disposition is unchanged. Combined
remains incomplete/disabled. PR remains Draft, Issue open, Ready/merge false.

Validation and self-review: full external-copy discovery passed 551 run,
549 passed, two existing skips (Windows command shell and opt-in cgroup probe).
Ten stable-byte targeted methods, publication aggregate, distribution drift
and whitespace checks passed before execution. Test implementation support and
main-agent self-review are not a new independent approval. The first public
rejection fixture omitted captured stderr; it was corrected to use the existing
bounded process, with no validator relaxation. An intermediate parallel test
run encountered changing identity bytes; all affected methods passed on the
frozen rerun. Final result maintenance is validated again without model calls.
Runtime/bundle bytes and identities remain unchanged; no new build or version.
Previous 5c85dff CI seven checks passed (runs 34465722932, 34465726621,
34465726768, 34465726719); those are historical, not this final head's CI.
