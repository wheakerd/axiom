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

The immutable v0.7.9 gate is the cumulative baseline for the v0.8.11 candidate:

| Metric | Baseline | v0.8.11 candidate | Delta | Classification |
| --- | ---: | ---: | ---: | --- |
| UTF-8 bytes | 5,899 | 6,673 | +774 | exact static count used as a proxy |
| Whitespace-delimited words | 757 | 852 | +95 | exact static count used as a proxy |
| Logical lines | 107 | 120 | +13 | exact static count used as a proxy |
| Unique direct references | 1 | 1 | 0 | exact static count used as a proxy |
| `ceil(bytes / 4)` | 1,475 | 1,669 | +194 | estimate for the same English surface only |

Reproduce the candidate measurement from any working directory:

```bash
python3 scripts/measure-routing-context.py
python3 scripts/measure-routing-context.py --check
```

The first command emits deterministic JSON to stdout. The second verifies the
versioned record, fixed workload identity, threshold arithmetic, lifecycle
matrix, and duplicate-injection semantics. Neither command writes files.

## Lifecycle Matrix

The v0.8.11 record represents all required paths: fresh startup with a no-route
request, fresh startup with a routed request, resume with no route, clear with
a routed request, manual compaction with no route, automatic compaction with a
routed request, and three repeated no-route requests in one otherwise unchanged
session. The checked-in hook contract expects one gate injection in each
scenario. That expected count is static configuration evidence, not an observed
host event. Routed slots bind canonical, paraphrased, and post-compaction
`agent-plugin-architect` contracts; this does not turn them into host results.
The fixed workload now contains 67 cases: two append-only direct-submit
boundary cases join the stale-tracking case without changing either frozen
benchmark.

Each host observation stores its injection events and observed count. The
validator derives `duplicateInjectionDetected` as observed count greater than
the scenario's expected count. A passing observation must have the exact count
and no duplicate. Unrun or unavailable observations must retain null counts,
null duplicate state, and an empty event list. Codex lifecycle observation for
v0.8.11 is `NOT-RUN`; authenticated Claude Code observation is
`UNAVAILABLE / NOT-RUN`. The preserved independent v0.8.2 diagnostic used one
fresh Case 1 session and therefore does not claim current or actual
post-compaction behavior.

The immutable v0.8.10 release and prior observations remain separate evidence and
are not copied into the v0.8.11 candidate's host metrics. Current exact host
usage is therefore `NOT-RUN`; the deterministic static measurement is local and telemetry-free,
so the record keeps `networkOrTelemetryUsed` false.

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

Reduction evidence binds its before surface to the nearest earlier stable
SemVer record; v0.7.9 remains only the cumulative growth baseline. The v0.8.11
experiment therefore compares v0.8.10 and v0.8.11 over the same byte-identical
67-case workload:

| Metric | v0.8.10 before | v0.8.11 after | Delta |
| --- | ---: | ---: | ---: |
| UTF-8 bytes | 7,739 | 6,673 | -1,066 |
| Whitespace-delimited words | 1,001 | 852 | -149 |
| Logical lines | 135 | 120 | -15 |
| Unique direct references | 1 | 1 | 0 |
| `ceil(bytes / 4)` | 1,935 | 1,669 | -266 |

The cumulative 774-byte increase is about 13.12%, so both growth-review
triggers remain reached and reviewed. Headroom below the 8,192-byte instruction
boundary rises from 453 bytes (5.53%) to 1,519 bytes (18.54%). Contributors
must preserve at least 15% headroom after equivalent acceptance and should
prefer roughly 6-6.5 KiB when precision permits. The hard limit is a rejection
guard, not an authoring target.

The machine-readable contract is [schema v1](schema-v1.json), and the current
versioned record is [v0.8.11](results/v0.8.11.json). The v0.8.10 record remains
byte-for-byte historical evidence; the current record binds the reduced gate,
unchanged workload, and static-only evidence boundary.
