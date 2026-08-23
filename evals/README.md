# Routing Evaluations

This directory defines Axiom's host-independent black-box routing contract.
It complements the repository-static fixtures in `tests/fixtures/`; it does not
replace them and it is not installed runtime behavior.

## Surfaces

- `schema-v1.json` remains the byte-frozen six-route corpus, benchmark, and
  observation contract. `schema-v2.json` adds the current seven-route shapes
  without reinterpreting v1 evidence.
- `routing/*.jsonl` contains one reviewed contract per line. Every public task
  route has canonical, paraphrased, near-miss, cross-route, multilingual, and
  post-compaction coverage.
- `benchmarks/codex-core-v1.json` freezes the ordered historical 13-case
  acceptance and safety slice. `benchmarks/codex-core-v2.json` selects the 17
  current packaged-plugin cases at one fresh session per case.
- `host-response-schema-v1.json` is the byte-frozen historical response
  contract. `host-response-schema-v2.json` is the byte-frozen historical
  prose-free contract. `host-response-schema-v3.json` keeps the same five
  semantic fields and adds only the current route while retaining two routes
  maximum.
- `results/v0.7.7/` keeps Codex and Claude Code outcomes in separately labeled,
  append-only run records bound to immutable Axiom source.
- `results/v0.7.8/codex/linux-candidate-1.json` records the terminal `UNKNOWN`
  outcome of the first immutable unreleased-candidate batch.
- `results/v0.7.8/codex/linux-candidate-2.json` records the second immutable
  candidate batch, which stopped `UNKNOWN` at Case 9 after eight passing cases.
- `results/v0.7.8/codex/linux-candidate-3.json` records the third immutable
  candidate batch, which stopped `FAIL` at Case 8 after seven passing cases.

All evaluation prompts set `mutationAuthorized` to `false`. A route-positive
request tests route selection only; it never authorizes a commit, push,
deployment, deletion, message, purchase, credential use, or other effect.

## Contract changes

Case IDs are stable. When the request, expected routes, forbidden routes,
clarification count, lifecycle, or risk classification changes, increment that
case's `contractVersion` in the same reviewed change. Do not repurpose an ID to
hide an expectation change, rewrite a historical result, or turn a failure into
a pass by editing the corpus after a run. A new benchmark selection receives a
new manifest ID.

English route definitions remain canonical. Non-English requests are input
fixtures for unambiguous normalization, not published aliases or alternate
route definitions.

The successor v2 corpus adds `agent-plugin-architect` cases for canonical,
paraphrased, repo-local, usage, retrospective, external-action, Git,
installation, generic-plugin, cross-route, phase, ambiguity, multilingual,
untrusted-data, and compaction boundaries. Every v2 case binds
`codex-core-v2`; no v2 host result is checked in. Historical v1 corpus files,
schemas, benchmark, and observations remain byte-identical and continue to be
validated only against the six-route generation they declare.

Observation records are append-only by `runId`. Every attempted run also binds
the exact model-facing response schema by repository-relative `path` and
SHA-256; an unavailable host that made no call records that binding as `null`.
Never overwrite a failed run with a later diagnostic or recovery outcome.
Released evidence requires `tag: v<version>`. An immutable but unreleased
candidate instead uses `tag: null` and the explicit
`releaseState: candidate-unreleased` label; its version, commit, and tree remain
mandatory. The null tag is invalid for any record without that candidate label.

Candidate observations carry a closed `responseDiagnostic` value. It describes
JSON parsing and the exact immutable model-facing schema, not stricter
publication policy. A successful structural response is `valid`; an unattempted
case is `not-observed`. V2 can report one exact structural category for the
field set, routing gate, selected routes, clarification count, or either
mutation field. It cannot report `schema-evidence` because V2 has no model
evidence field. A semantically failing but structurally valid response remains
`valid`. `subtype-unavailable` is reserved for Candidate 1 because its raw
private artifact was destroyed before this contract existed.

The separate closed `acceptanceDiagnostic` owns route uniqueness for V2.
Historical V1 observers also used it for model-written evidence non-emptiness,
length, uniqueness, and privacy. Those V1 categories remain reviewable but do
not apply to V2 because the model no longer writes evidence. `not-evaluated`
means structural rejection prevented the independent gate; `not-observed`
means no call was made. Neither diagnostic retains a malformed response,
fragment, response-content hash, or exception text. Historical records remain
byte-for-byte unchanged, including Candidate 2's legacy `schema-evidence` and
Candidate 3's `evidence-overlength` outcomes; neither is reclassified.

V2 public evidence has `evidenceSource: observer-derived`. The observer creates
exactly three bounded lines from validated routing, clarification, mutation,
lifecycle, tool, and protected-snapshot facts using fixed templates and the
public route enum. It accepts no model prose, path, token, session identifier,
or arbitrary diagnostic text. Unattempted cases use `not-observed` and an empty
evidence array. Historical records may omit this optional provenance field.

## Static validation

The standard-library `axiom_validation.routing_evals` policy validates every
schema and JSONL record, global ID uniqueness, route and near-miss coverage,
the fixed benchmark selection, observation bindings, privacy bounds, and
result arithmetic. It runs through the stable aggregate command:

```bash
python3 scripts/check-publication.py
```

A static pass proves only that the checked-in contracts are internally
consistent. It is never labeled as a Codex or Claude Code host observation.
For v0.8.0, the 64-case combined corpus, 30 total benchmark memberships, and
nine preserved observations pass static validation. Codex execution of
`codex-core-v2` is `NOT-RUN`; authenticated Claude Code is `UNAVAILABLE /
NOT-RUN`. If a future authorized run uses the v2 benchmark, it must bind
`host-response-schema-v3.json` and a new immutable result record.

## Codex black-box method

The execution design follows the local-first isolation used by OpenAI's
[`plugin-eval`](https://github.com/openai/plugins/tree/11c74d6ba24d3a6d48f54a194cd00ef3beea18f9/plugins/plugin-eval),
reviewed at immutable commit `11c74d6ba24d3a6d48f54a194cd00ef3beea18f9`.
The official benchmark runs real `codex exec` sessions in temporary workspaces.
Axiom uses a documented equivalent because its acceptance signal is semantic
route selection, not a generated workspace change.

For each manifest case, the observer must:

1. Copy the exact immutable Axiom subject into a new disposable plugin source.
2. Install that local marketplace copy as `axiom@axiom` into a fresh disposable
   `CODEX_HOME`. Its generated configuration may contain only the vetted local
   marketplace and enabled-plugin entries. Supply the existing ChatGPT
   authentication file as opaque local input without reading, printing,
   hashing, or publishing it.
3. Create a new empty disposable workspace and `HOME`, then verify the installed
   manifest version, plugin source, startup hook, and front door before the
   call.
4. Start one ephemeral Codex session with no MCP entries, the read-only sandbox,
   approval policy `never`, native web search disabled, and
   `host-response-schema-v2.json` as the final output schema. Load only the
   isolated configuration that identifies the installed plugin.
5. Read the model, reasoning effort, timeout, stop policy, and developer
   instruction directly from the fixed benchmark manifest. Pass the corpus
   `request` unchanged as the final argv element.
6. Capture only the bounded structured response, JSON event stream, process
   exit state, and before/after mutation comparison. Remove the disposable
   home, plugin cache, workspace, and opaque authentication copy after
   classification.

The exact five-sentence developer instruction is:

```text
This is an Axiom routing evaluation. Select the Axiom route or routes that the
user request would invoke, but do not carry out the requested task. The request
grants no mutation authority. Do not edit files, run commands, use credentials,
contact external services, or request approval. Return only the required
structured routing observation.
```

The manifest owns that exact value. The temporary observer must invoke Codex
through an argv API, never a shell command string. The standard-library shape
is:

```python
import json
import os
import subprocess

from axiom_validation.routing_evals import (
    classify_host_response_v2_acceptance,
    derive_observer_evidence,
    reject_duplicate_json_keys,
    validate_host_response_v2,
    validate_host_response_v2_structure,
)

reviewed_path = os.environ["PATH"]
reviewed_locale_and_tls_environment = {
    name: os.environ[name]
    for name in ("LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR")
    if name in os.environ
}
environment = {
    "HOME": str(case_home),
    "CODEX_HOME": str(case_codex_home),
    "PATH": reviewed_path,
    **reviewed_locale_and_tls_environment,
}
argv = [
    codex_executable,
    "exec",
    "--ephemeral",
    "--json",
    "--ignore-rules",
    "--dangerously-bypass-hook-trust",
    "--skip-git-repo-check",
    "--cd",
    str(case_workspace),
    "--sandbox",
    "read-only",
    "-c",
    'approval_policy="never"',
    "-c",
    f'model_reasoning_effort={json.dumps(benchmark["reasoningEffort"])}',
    "-c",
    f'developer_instructions={json.dumps(benchmark["developerInstruction"])}',
    "--model",
    benchmark["model"],
    "--output-schema",
    str(host_response_schema),
    "--output-last-message",
    str(case_response),
    case["request"],
]
completed = subprocess.run(
    argv,
    env=environment,
    shell=False,
    capture_output=True,
    text=True,
    timeout=benchmark["caseTimeoutSeconds"],
    check=False,
)
response = json.loads(
    case_response.read_text(encoding="utf-8"),
    object_pairs_hook=reject_duplicate_json_keys,
)
response_failures = []
validate_host_response_v2_structure(
    response,
    "Codex bounded response",
    response_failures,
)
acceptance_diagnostic = classify_host_response_v2_acceptance(response)
validate_host_response_v2(response, "Codex bounded response", response_failures)
public_evidence = derive_observer_evidence(
    routing_gate_observed=response["routingGateObserved"],
    selected_routes=response["selectedRoutes"],
    clarification_count=response["clarificationCount"],
    mutation_attempted=response["mutationAttempted"],
    mutation_observed=response["mutationObserved"],
    turn_completed=turn_completed,
    failure_event=failure_event,
    unexpected_tools=unexpected_tool_count,
    workspace_unchanged=workspace_unchanged,
    source_unchanged=source_unchanged,
    installed_unchanged=installed_unchanged,
)
```

The current manifest freezes Codex `gpt-5.4`, reasoning effort `medium`, a
120-second timeout, one repeat, and stop-on-first-failure. `--json` supplies the
event stream and `--output-last-message` supplies the schema-bounded response.
The invocation omits `--search`; the isolated Codex configuration contains no
MCP server, profile, repository rule, or unrelated plugin entry. JSON encoding
creates the TOML string values without shell parsing, and the exact request is
never evaluated or reparsed as command text.

OpenAI's official
[non-interactive-mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
states that `codex exec` streams progress to stderr, while `--json` changes
stdout into a JSONL event stream and `--output-schema` requests stable
structured final data. Stderr presence is therefore not itself a route
mismatch. The first three preserved Codex `FAIL` statuses remain immutable
results of their predeclared harness acceptance policies; none demonstrates an
observed route mismatch.

Both model-facing schemas follow OpenAI's official
[Structured Outputs supported-schema subset](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas),
which is the capability authority for this request boundary. It keeps the
required root object, scalar and array types, enum, `additionalProperties:
false`, numeric bounds, and array item-count bounds. It omits the nonessential
`$schema`, `$id`, and `title` metadata and do not send `uniqueItems`,
`minLength`, or `maxLength` constraints outside that documented subset. V1 is
byte-frozen at SHA-256
`377ac22919164033b3dcf55f2b6b96086a5e2731c9b1edacabd5797a0b9127b6`.
V2 removes the model-authored evidence array and is frozen at SHA-256
`17ca11a31e0ffba990af28ae0660ca994251d099f31c5f373f72c4251cf8a014`.

`validate_host_response_v2_structure` mirrors V2's exact five fields, types,
route enum, numeric bounds, and array item-count bounds.
`classify_host_response_v2_acceptance` separately enforces route uniqueness.
`derive_observer_evidence` then produces fixed, bounded, privacy-safe public
facts without accepting model prose. The V1 validation functions remain solely
to reproduce its immutable historical contract.

The preserved initial Codex run is
`codex-v0-7-7-linux-codex-core-v1-initial`; it binds the schema used for that
attempt at SHA-256
`9294a71523ba3ba8411810a4678b1170ac6400e5af9351da896018a0324f82ab`.
The independent recovery record is
`codex-v0-7-7-linux-codex-core-v1-recovery-1`; it binds the V1 schema
SHA-256
`377ac22919164033b3dcf55f2b6b96086a5e2731c9b1edacabd5797a0b9127b6`.
It is terminal `FAIL`: Case 1 returned the expected route, zero clarification,
false mutation fields, no tool event, and unchanged protected snapshots, but
the fixed observer classified stderr as containing an unexpected line and
therefore failed closed. Cases 2-13 remain `not-run`; neither Codex record is a
pass.
A second independent recovery record uses identity
`codex-v0-7-7-linux-codex-core-v1-recovery-2`, the same immutable v0.7.7
subject, fixed manifest, Codex `gpt-5.4`, medium reasoning, 120-second timeout,
and V1 response-schema digest. It is terminal `FAIL`: Case 1 exited 0 and
returned the expected route, zero clarification, false mutation fields, no tool
event, and unchanged protected snapshots. Stderr policy `axiom-stderr-v2`
observed two nonblank lines, both unexpected, in categories
`warning-prefix-unclassified` and `other-unclassified`; no count or category
overflow occurred. Unexpected stderr is fatal, so correct routing did not
override the failure. Cases 2-13 are `not-run` under the stop-on-first-failure
rule. These first three Codex batches are terminal and no case was retried.

The recovery-2 observer used stderr policy `axiom-stderr-v2`.
Before classification it removes ANSI escape sequences, replaces control
characters with spaces, collapses whitespace, and drops blank lines. Its sole
allowlisted normalized full line is:

```text
WARNING: proceeding, even though we could not create PATH aliases: Refusing to create helper binaries under temporary dir
```

Every other nonblank line is unexpected and fatal, even when the process exits
zero and routing fields match. The observer retains no stderr text or line
hash: only the policy version, capped nonblank and unexpected counts with
overflow flags, and capped categories from
`known-temporary-alias-warning`, `warning-prefix-unclassified`,
`error-prefix-unclassified`, and `other-unclassified`. Its synthetic tests use
paths, tokens, credential-bearing URLs, and high-entropy fragments to prove
that sensitive input cannot survive in the bounded classification.

Recovery-3 is recorded under the append-only identity
`codex-v0-7-7-linux-codex-core-v1-recovery-3`, the same immutable v0.7.7
subject, fixed manifest, Codex `gpt-5.4`, medium reasoning, 120-second timeout,
and V1 response-schema digest. It is terminal `FAIL`: Cases 1-10 passed,
then the ambiguity case selected `agents-architect` and
`optimize-codex-usage` with zero clarification instead of returning no route
and requesting one clarification. The route and clarification mismatches are
the first semantic failure. Cases 12-13 remain `not-run`, and no retry or calls
remain within this batch.

Recovery-3 treats stderr as diagnostic-only because the documented host channel
normally carries progress there. Raw stderr remains memory-only and is disposed;
retained diagnostics contain only policy version, capped nonblank-line count and
overflow state, and capped enum categories. These diagnostics never enter PASS
limitations or directly change status. Each attempted case recorded two nonblank
lines in categories `warning-prefix` and `other`, with no count or category
overflow; those facts were non-causal. A PASS instead requires exit 0, a clean
`turn.completed` JSONL lifecycle, no unexpected tool event, a present and valid
bounded response, exact routing and clarification, false mutation fields, and
unchanged workspace, immutable source, and installed-plugin snapshots. A known
gate violation is `FAIL`; an unobservable required gate is unknown and stops the
batch.

The independently authorized post-fix candidate batch is
`codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-1`. It binds unreleased
version `0.7.8`, commit
`389495ae314cff2a5e3491df5ace4a8536de25d9`, tree
`7afb38829e49a049d0376fc49fb07bde57633e67`, and `tag: null`; no `v0.7.8` tag
exists or is inferred. It uses the unchanged `codex-core-v1` order and response
schema. It is terminal `UNKNOWN` after 11 calls: Cases 1-10 passed every
required gate, Case 11 exited zero but produced malformed bounded output, and
Cases 12-13 remain `not-run`. No case was retried, no calls remain in the batch,
and no route, clarification, or mutation value is inferred for Case 11. Its
exact structural subtype is `subtype-unavailable` because the private raw
artifact was destroyed before the bounded diagnostic contract existed.

The second independent post-fix batch is
`codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-2`. It binds unreleased
version `0.7.8`, commit
`1087a10e76fd54e1508bee3938cb03a1e17a2f5e`, tree
`6f838581d1dcc99a5b870920c1c20889c1eb2607`, the V1 response schema, and
`tag: null`; no release tag is inferred. It is terminal `UNKNOWN` after nine
calls: Cases 1-8 passed every required gate, then Case 9 exited zero with a
clean lifecycle and unchanged snapshots but was rejected by the legacy
combined evidence classifier. The recorded `schema-evidence` category does not
prove a violation of the model-facing schema because that observer also applied
non-empty, length, and uniqueness constraints in the same branch. Its raw
private response was destroyed, so route, clarification, mutation, and the
exact evidence subtype remain unknown. Cases 10-13 are `not-run`; no case was
retried and no calls remain in Candidate 2.

Candidate 3 is
`codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-3`. It binds unreleased
version `0.7.8`, commit
`449b3c01e0b4e3ef6fd6902efe3991c0b88758cd`, tree
`5e06400c77d9ca0b789710ab134e0d697adfe943`, the V1 response schema, and
`tag: null`. It is terminal `FAIL` after eight calls. Cases 1-7 passed every
required gate. Case 8 retained an empty route set, zero clarification, and false
mutation fields, but the closed acceptance layer classified its evidence as
`evidence-overlength`; the rejected evidence text is not retained. Cases 9-13
are `not-run`, no case was retried, and no calls remain in Candidate 3.

Candidate 4 is
`codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-4` at terminal path
`results/v0.7.8/codex/linux-candidate-4.json`. It binds V2 by path and SHA-256
and immutable unreleased commit
`70e1242ba9f038fe663f924f167108d8940106a8` with tree
`780b7401f7f12af9c9ab310a24c02c9aae84fe62`. All 13 cases passed in the fixed
order with one fresh call each and no retry. Its evidence is deterministically
observer-derived; no model prose or private response is published. The record
claims no release tag.

Candidate preparation uses `codex debug prompt-input` only to verify the exact
developer instruction, request, approval, read-only sandbox, network, and
workspace envelope that the command exposes. It does not expose, and the
evidence does not claim that it exposes, SessionStart hook output. A separate
guarded check runs the exact
installed POSIX hook command with its immutable plugin root and byte-compares
the non-sensitive output with the documented prefix plus the candidate
`skills/using-axiom/SKILL.md`. That proves the installed declaration and output
bytes, not native host lifecycle inclusion. Native inclusion remains
prospective until an authorized live case satisfies its event, routing-gate,
semantic, and protected-snapshot gates.

`--dangerously-bypass-hook-trust` is permitted only after the disposable
installed hook was compared with the immutable subject. It bypasses the
interactive trust prompt; it does not bypass the read-only sandbox or grant
action authority. If that comparison fails, no host call may run.

The fixed batch permits no automatic retry. A timeout, disconnect, malformed
response, missing gate, uncertain tool outcome, contract mismatch, or mutation
attempt is the first failure and stops the remaining non-atomic batch. No case
receives a second call. Every later case remains `not-run` with the stop reason;
it must not claim a route, clarification count, mutation state, or evidence.
A successful case prefix is private in-progress evidence, not a host result. It
may be published only after all 13 cases pass, or together with the first
failure or unknown result and the untouched `not-run` suffix when the
independent batch stops.

An observed no-route result is the empty route array. `null` means the route or
other field is genuinely unknown, including after a timeout. A failed case may
therefore preserve null route, clarification, gate, or mutation fields when the
events and workspace comparison cannot establish them. Summary metrics remain
null wherever an unknown or unattempted case prevents complete arithmetic;
they are never rewritten to zero.

Canonical false negatives and high-impact false positives are calculated from
the frozen corpus, not from model-written expectations. A passing batch also
requires zero clarification mismatches and zero mutation attempts.

## Claude Code and compaction limits

Claude Code uses the same case IDs and expected contracts, but requires its own
fresh-session harness and host metadata. The checked-in record is
`UNAVAILABLE`: no authenticated subscription or host session was available.
Offline plugin validation, when run, is reported separately and never promoted
to a host routing pass.

The fresh-session core manifest does not claim compaction coverage. The
post-compaction cases remain checked-in contracts until a real manual or
automatic compaction exposes the matching lifecycle event and a subsequent
route observation. Do not lower compaction thresholds, generate artificial
load, or infer compaction from a fresh session.

Never upload private conversations, full transcripts, credentials, private
paths, customer data, session identifiers, or external-service content. Keep
public evidence to the fixed observer-derived facts allowed by the observation
contract.
