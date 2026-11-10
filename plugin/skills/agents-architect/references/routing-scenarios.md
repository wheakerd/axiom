# Routing Scenarios

## Purpose

Choose and record the routing scenarios that cover a completed AGENTS change, from a narrow wording edit to a broad migration. `validation-reporting.md` owns the other checks and the final report.

## Scenario Set

Use the smallest set that covers every changed branch plus its important rejection boundary:

- A narrow leaf or wording change normally needs two to four scenarios.
- A route-table or owner change needs each changed route, one no-match, one sibling rejection, and one cross-route or ambiguous case.
- A broad initialization or migration needs at least eight representative scenarios spanning direct, grouped, workflow, risk, docs/test-only, non-English, unknown-path, and no-match behavior.

For each scenario record the signal, expected and actual route, loaded files, unexpected files, active bytes, authorization boundary, and result. Add current-session versus inactive evidence and host-discovered shadowing cases only when those behaviors are in scope.

When task-context maintenance, update-trigger, or compaction handling changes, include one regression scenario with an early proposal that a later user message narrows or reverses, followed by compaction before the durable update. Verify that the canonical mode is reported, only the controlling decision is admitted, superseded and unrelated one-off candidates are rejected, read depth and unopened raw outputs are reported apart, and the current-run versus later-run activation boundary is explicit. Use a Markdown scenario or a disposable host prompt; do not add a custom harness merely for this case.

When implementation reconciliation changes, cover both exact canonical modes, an explicit unambiguous non-English normalization, and these boundaries:

- ordinary `update AGENTS` stays on normal maintenance, while implementation drift or an execution or context discontinuity without an explicit request does not activate reconciliation;
- when `HEAD` supports a rule but material working-tree content contradicts it, the live tree controls by default; a user-selected ref remains explicit and any live divergence is reported;
- partial rollback and bounded negative evidence do not over-delete, and a normative constraint is not removed merely because code has no analogue;
- worker conflict is resolved from direct evidence, not majority vote, and an active rule found stale remains binding for the current run; and
- preview never writes, apply uses one writer after ledger freeze, and missing roles or writer isolation safe-stop, reported as incomplete with nothing written.

Include material staged, unstaged, untracked, and ignored content in the baseline scenarios.

Static construction, Codex `codex debug prompt-input`, or the Claude Code `/memory` and `/context` listings can prove file discovery or prompt assembly but not semantic model selection. Label actual host routing as not run or unavailable unless directly observed in a fresh session.

### Document-Language Regressions

When the document-language contract changes, review these semantic cases across root `AGENTS.md`, linked indexes, leaves, references, and scoped repo-local Skills. Inspect authored prose, not merely route selection or ASCII characters:

- Non-English task with no document-language request: English documents.
- Non-English reply or explanation requested: English documents; the response follows its separate language instruction.
- Explicit non-English document request: that language only within the named document scope; unrelated files remain unchanged.
- Non-English existing docs or source material: newly authored prose defaults to English; preserve exact literals and out-of-scope content.
- Narrow maintenance or repo-local Skill update: apply the parent contract even when the document-contract reference is not loaded.
- Resume or compaction: retain the controlling explicit document-language decision and its scope; do not infer one from the latest message language.
- Conflicting active instruction: honor actual precedence and report the outcome-changing conflict; do not claim an inferred user exception.

Structural checks and source review do not reproduce an intermittent model failure or establish generated output behavior; keep those claims separate from a directly observed run.

## References

- `validation-reporting.md`
- `routing-architecture.md`
