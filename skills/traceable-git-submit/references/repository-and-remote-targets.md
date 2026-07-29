# Repository And Remote Targets

## Purpose

Resolve one exact target Git repository and the complete set of destinations a
named remote will push to without leaking endpoint secrets.

## Exact Repository Root

Resolve the target from the user's explicit path or scoped files before using
the session working directory. Canonicalize the path and query Git rather than
inferring a root from folder names:

```bash
git -C <candidate> rev-parse --show-toplevel
git -C <candidate> rev-parse --path-format=absolute --git-common-dir
```

For every path in the intended write set, resolve its owning Git root. Require
all paths to belong to the same target root.

Stop before changing state when:

- The target is not inside a Git repository.
- An explicit path and the session directory resolve to different plausible
  repositories and the user did not identify which one is authoritative.
- Scoped paths span a parent repository and a nested repository or span two
  worktrees/repositories.
- A nested repository makes ownership ambiguous.
- The requested path is outside the resolved target root.

Report the canonical target root and Git common directory with reversible path
escaping. Do not silently switch to a parent or nested repository. A linked
worktree is valid when both roots are resolved from Git.

## Push Target Inventory

Apply this and the remaining sections only to submit, push, or
post-consolidation recovery. Checkpoint-only work does not need push targets;
a resolvable local upstream whose branch remote is `.` is valid for checkpoint
baseline and provenance checks.

After push preflight resolves `remote`, enumerate every configured push URL:

```bash
git -C <repo> remote get-url --push --all <remote>
```

Capture this output without echoing it into user-visible logs. Collapse
repeated byte-identical URL values to one target and retain first-occurrence
order. Do not substitute the fetch URL for this inventory.

For each distinct target, derive:

- A one-based ordinal.
- A stable cryptographic fingerprint of the complete raw target value.
- The authorized `mergeRef`.
- The expected baseline and final SHAs when known.

Use an available native hashing facility. Keep raw URLs in process memory or a
permission-restricted temporary file only as long as required, then remove that
temporary material. Never persist raw endpoints in the baseline cache,
provenance record, commit message, task report, or plugin directory.

## Authorization Gate

- Zero push targets stops submit, push, and recovery, but never checkpoint-only
  work.
- One distinct push target may proceed under an explicit submit, publish, or
  push request.
- More than one target stops by default. Report only the ordered fingerprints
  and request explicit authorization for that exact set plus acknowledgement
  that sequential pushes are not atomic and may leave partial remote state.
- If the configured target set changes after authorization, stop and request
  authorization again.
- Do not select one target from a multi-target remote while still invoking the
  named remote as though only that target will receive the push.

Freeze the authorized fingerprint set before consolidation. Persist target
fingerprints, never raw URLs, in post-consolidation provenance so recovery can
detect configuration drift.

## Immediate Pre-Push Drift Gate

Immediately before the first push, re-enumerate targets and require the frozen
ordered fingerprint set to be unchanged. Then query every frozen target's
`mergeRef` directly. Require exactly one matching ref result and
`mergeRef == baselineSha` for every target before issuing any push command.

If any target is missing, unreadable, changed, or at another SHA, perform zero
pushes. Retain provenance and the backup ref, and report only target
ordinal/fingerprint plus escaped ref and expected/observed SHA. Do not begin
with targets that happened to pass while another target drifted.

## Push And Verification Boundary

A push to a named remote may affect every configured push target. Completion
requires direct current evidence that every authorized target's `mergeRef`
equals `newCommit`.

Use each captured target internally for direct remote-ref verification. Capture
and sanitize command failures before reporting them; Git errors can repeat a
raw URL or username. A successful fetch, an updated `@{u}`, or success from only
one target does not prove the other push targets were updated.

If targets disagree, retain the backup ref and provenance record, do not update
the baseline cache, and report each target only as ordinal/fingerprint plus
expected and observed ref/SHA.

## Sensitive Reporting

Never report or commit:

- Raw fetch or push URLs.
- Embedded credentials, tokens, or usernames.
- Private hostnames, IP addresses, filesystem endpoints, or internal network
  paths.

Reports use repository root, remote name, target ordinal/fingerprint,
`mergeRef`, and expected/observed SHAs. If sanitization cannot be guaranteed,
report only that target verification failed and retain recovery state. Render
repository and ref paths with JSON-string, Git C-style, or equivalent
reversible escaping; never emit raw control characters or newlines.
