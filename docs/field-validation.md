# Field Validation

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

## Before Testing

1. Use a repository that contains no sensitive material or select a public
   repository you are authorized to inspect.
2. Record the host name and exact version, operating system, shell when
   relevant, Axiom version or immutable commit, and installation method.
3. Start a new session or reload plugins as documented by the host.
4. Open `/hooks`. Compare every installed Axiom command with
   [the checked-in commands](../README.md#inspect-the-hooks). Stop if they
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

### 3. Claude Code compaction recovery

Run this only in an already authorized Claude Code session whose installed
Axiom hook matched the checked-in definition. Test manual and automatic
compaction separately; do not change global configuration, lower a compaction
threshold, generate artificial load, or spend external-account usage merely to
force the automatic case.

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
