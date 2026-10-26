# Evidence Ledger

## Purpose

Give every completion criterion one line that ties the claim to a current
observation, so the report shows what was checked, what was found, and what
remains open.

## Apply When

- Building or updating the ledger in the Direction steps.
- Deciding whether an earlier observation still counts.

## Ledger Line

Record one line per criterion:

| Field | Content |
| --- | --- |
| Criterion | The user's acceptance condition in their words or the task record's words |
| Check | The direct check that proves it now: file read, command, test, service query, record entry |
| Observed | The result as produced in this session, with enough detail to re-run the check |
| Verdict | `met`, `not met`, or `unverifiable` |
| Source | `observed` with the step or command, or the reason the check could not run |

Keep the ledger as plain text or a small table in the report. Do not store it
as a durable rule; it describes one task at one moment.

## Verdict Rules

- `met` requires an observed result that satisfies the criterion after the
  last mutation of its subject.
- `not met` requires an observed result that contradicts the criterion. Say
  what was observed; do not infer the cause.
- `unverifiable` covers a check that cannot run here (missing tool, access,
  host, or environment) and a criterion with no direct check. Name the reason
  and the host or tool that could verify it.
- A recalled or summarized fact never produces `met`. Re-observe it or mark
  the criterion `unverifiable`.
- A passing check on a copy, fixture, or earlier state does not prove the
  current target; name the subject that was checked.

## Freshness

An observation expires when a later mutation touches its subject: a file edit
invalidates the earlier read of that file, a push invalidates the earlier
remote state, a dependency change invalidates the earlier test run. Record the
observation order against the mutation order, and re-observe after the last
mutation before claiming `met`.

## Depth

Match depth to risk and reversibility. A one-line change needs the direct
check of its effect; a release, migration, or external effect needs each
promised property observed separately. When the number of criteria is large,
verify the irreversible and user-visible ones first and say which ones were
not re-observed.

## Prohibited

- Do not mark a criterion `met` from a summary, plan, earlier turn, or
  memory.
- Do not round partial evidence up: a passing subset of tests proves the
  subset.
- Do not drop a criterion the user stated because it is hard to check; keep it
  and mark it `unverifiable`.
