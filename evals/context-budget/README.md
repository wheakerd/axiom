# Routing Context Budget

This directory records Axiom's repeatable budget for the always-loaded
`skills/using-axiom/SKILL.md` routing gate. It measures a repository surface;
it does not expose hidden Codex or Claude Code accounting and does not invoke a
model, start a host session, contact a network service, or collect telemetry.

## Measurement Boundary

The standard-library measurement reports exact UTF-8 byte, whitespace-delimited
word, logical-line, and unique direct-reference counts. Those exact counts are
still context-cost **proxies**, not host token or credit totals. The only token
figure is `ceil(UTF-8 bytes / 4)`, explicitly labeled as an estimate suitable
only for before/after comparison of the same English Markdown surface. It must
not be compared with billed, cached, or host-reported tokens as if equivalent.

The immutable v0.7.9 gate is the cumulative baseline for v0.8.2:

| Metric | Baseline | v0.8.2 candidate | Delta | Classification |
| --- | ---: | ---: | ---: | --- |
| UTF-8 bytes | 5,899 | 6,293 | +394 | exact static count used as a proxy |
| Whitespace-delimited words | 757 | 805 | +48 | exact static count used as a proxy |
| Logical lines | 107 | 114 | +7 | exact static count used as a proxy |
| Unique direct references | 1 | 1 | 0 | exact static count used as a proxy |
| `ceil(bytes / 4)` | 1,475 | 1,574 | +99 | estimate for the same English surface only |

Reproduce the candidate measurement from any working directory:

```bash
python3 scripts/measure-routing-context.py
python3 scripts/measure-routing-context.py --check
```

The first command emits deterministic JSON to stdout. The second verifies the
versioned record, fixed workload identity, threshold arithmetic, lifecycle
matrix, and duplicate-injection semantics. Neither command writes files.

## Lifecycle Matrix

The v0.8.2 record represents all required paths: fresh startup with a no-route
request, fresh startup with a routed request, resume with no route, clear with
a routed request, manual compaction with no route, automatic compaction with a
routed request, and three repeated no-route requests in one otherwise unchanged
session. The checked-in hook contract expects one gate injection in each
scenario. That expected count is static configuration evidence, not an observed
host event. Routed slots bind canonical, paraphrased, and post-compaction
`agent-plugin-architect` contracts; this does not turn them into host results.

Each host observation stores its injection events and observed count. The
validator derives `duplicateInjectionDetected` as observed count greater than
the scenario's expected count. A passing observation must have the exact count
and no duplicate. Unrun or unavailable observations must retain null counts,
null duplicate state, and an empty event list. Codex lifecycle observation for
v0.8.2 is `NOT-RUN`; authenticated Claude Code observation is
`UNAVAILABLE / NOT-RUN`. F5 Case 17 used a fresh session and therefore does not
claim actual post-compaction behavior.

The record separately preserves F5 candidate usage: 279,939 input tokens,
156,288 cached input tokens, and 350,053 milliseconds. The host also reported
2,436 output tokens, but schema v1 has no output-token field, so that value
remains in routing and release documentation. F5 passed 19 planned candidate
calls, including three Case 1 variance samples; those metrics are not final
v0.8.2 host, lifecycle, tag, or Stage 3 evidence. The deterministic static
measurement remains local and telemetry-free; the separately authorized Codex
model calls necessarily used the host network, so the combined record sets
`networkOrTelemetryUsed` to true.

## Growth Review And Reduction Evidence

Always-loaded growth is compared cumulatively with the immutable baseline. An
increase of at least 256 UTF-8 bytes **or** 5% requires explicit review and a
substantive justification in the versioned record. Reaching that threshold is
not an automatic rejection, and smaller changes are not described as free or
exact-token savings.

The absolute branch provides a stable signal when the gate is already large;
the relative branch scales the same review expectation to a smaller gate. The
cumulative immutable comparison prevents a sequence of individually small
increases from resetting the baseline. These values decide when human review
and rationale become mandatory; routing and safety acceptance remain separate.

Any candidate that reduces the routing gate must attach equivalent before and
after results over the same fixed workload identity. Both the routed set and
all no-route controls must pass, with static contract validation kept distinct
from host-observed evidence. A reduction without that paired evidence fails the
context-budget validator. Safety rules, authorization boundaries, stop
conditions, evidence gates, and model or reasoning settings cannot be removed
or changed merely to obtain a smaller number.

The 394-byte cumulative increase is about 6.68%. It reaches both the 256-byte
absolute and 5% relative review triggers. The record classifies it as reviewed
and preserves the substantive justification: the added sentence is the narrow
publication-only negative boundary needed to prevent a high-impact false
positive. The threshold does not replace routing, safety, or static validation.

The machine-readable contract is [schema v1](schema-v1.json), and the current
versioned record is [v0.8.2](results/v0.8.2.json).
