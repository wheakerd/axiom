# Routing Context Budget

This directory records Axiom's repeatable budget for the always-loaded
`plugin/skills/using-axiom/SKILL.md` routing gate; records before `0.17.0`
measured the same gate at `skills/using-axiom/SKILL.md`. It measures a repository surface;
it does not expose hidden host accounting and does not invoke a
model, start a host session, contact a network service, or collect telemetry.

## Measurement Boundary

The standard-library measurement reports exact UTF-8 byte, whitespace-delimited
word, logical-line, and unique direct-reference counts. Those exact counts are
still context-cost **proxies**, not host token or credit totals. The only token
figure is `ceil(UTF-8 bytes / 4)`, explicitly labeled as an estimate suitable
only for before/after comparison of the same English Markdown surface. It must
not be compared with billed, cached, or host-reported tokens as if equivalent.

The [Codex manifest](../../plugin/.codex-plugin/plugin.json) selects the
`results/v<version>.json` record in [results/](results/). That record owns the
candidate's measured values and its comparison with the immutable v0.7.9
cumulative baseline. This guide explains the current measurement contract;
version notes and records retain each candidate's counts and change narrative.

Measure the checked-in routing gate and validate its selected record from the
repository root:

```bash
python3 -B scripts/measure-routing-context.py
python3 -B scripts/measure-routing-context.py --check
```

The first command emits the actual file's digest and metrics as deterministic
JSON to stdout. The second checks those bytes against the selected record and
verifies the fixed workload identity, byte boundary, growth-review arithmetic,
lifecycle matrix, and duplicate-injection semantics. Neither command writes
files. A mismatch requires correcting the candidate or its record; changing a
guide's prose cannot make stale measurements valid.

## Lifecycle Matrix

The versioned record represents all required paths: fresh startup with a no-route
request, fresh startup with a routed request, resume with no route, clear with
a routed request, manual compaction with no route, automatic compaction with a
routed request, three repeated no-route requests in one otherwise unchanged
session, and a forked session with no route. The forked-session scenario
starts with `0.16.0`, when both startup Hooks gained the `fork` source; earlier
records keep the seven-scenario schema v1 matrix. The checked-in hook contract
expects one gate injection in each scenario. That expected count is static configuration evidence, not an observed
host event. Routed slots bind canonical, paraphrased, and post-compaction
observable-refusal and independent-audit `review-axiom-task` contracts,
plus the post-compaction `agent-plugin-architect` contract; this does not turn
them into host results. The context-budget comparison retains the fixed
corpus in `evals/routing/`; the manifest-selected record states its current
file, case, routed, and no-route counts.
This workload identity is separate from the current routing corpus and its
Codex and Claude Code benchmark profiles described in
[Routing Evaluations](../README.md).

Each host observation stores its injection events and observed count. The
validator derives `duplicateInjectionDetected` as observed count greater than
the scenario's expected count. A passing observation must have the exact count
and no duplicate. Unrun or unavailable observations must retain null counts,
null duplicate state, and an empty event list. Read the manifest-selected
record for each scenario's actual status; the presence of a scenario or a
passing static check does not turn `NOT-RUN` into a host observation.
Claude Code entries recorded before `0.15.0` retain their original status;
current Axiom installation and runtime support covers Codex and Claude Code.

Prior observations remain separate evidence and cannot be copied into a new
candidate's host metrics. Static measurement is local and telemetry-free;
exact host usage remains unobserved unless a separate observation supplies it.
A record's `targetRelease` describes its own binding. In particular,
`pending-immutable-release` does not establish current publication status; see
[Runtime and Repository Identity](../../docs/runtime-identity.md) for the
separate publication and observation boundaries.

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
SemVer record; the immutable cumulative baseline is not reset to that
predecessor. When the gate shrinks, `routingQuality.reductionExperiment` must
bind both document digests and equivalent passing routing and no-route results
over the same fixed workload. Without a reduction from that predecessor, the
field must be null. Clause review separately checks route conditions and
safety boundaries because static fixtures do not execute natural-language
instructions. Static results cannot stand in for paired host observations.

## Byte Boundary And Record Ownership

[Runtime Changes](../../docs/maintainers/runtime-changes.md#always-loaded-context)
requires at least 10% headroom below the 8,192-byte authoring boundary, not a
platform limit. The publication aggregate rejects more than 7,372 UTF-8 bytes
(`8192 * 90 // 100`) against the actual startup file, independently of recorded
metrics. Reviewed growth within that maximum is allowed; an earlier gate size
is not a ceiling.
Passing this check does not replace routing and safety acceptance or permit
lower model or reasoning settings.

Records from `0.16.0` use [schema v2](schema-v2.json), which adds the
forked-session scenario; earlier records keep [schema v1](schema-v1.json). The
current semantic checks are implemented in
[context_budget.py](../../axiom_validation/context_budget.py). Preserve earlier
records with their original metrics, workload identities, host vocabulary,
and evidence boundaries. Do not rewrite them to match the present gate or
infer the current host set from a historical schema alone. Change this guide
when the measurement contract changes; record new candidate measurements in
their versioned owner without maintaining a second manual table here.
