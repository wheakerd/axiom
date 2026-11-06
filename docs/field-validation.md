# Field Validation

Use this page to report a bounded observation of Axiom in Codex or Claude Code. Current support and installed-host status are owned by [Compatibility](compatibility.md) and [release-status.json](../evidence/release-status.json). A static repository check does not establish installation, Skill discovery, routing, or lifecycle behavior in a host session.

## Evidence Levels

Keep static validation, native package parsing, installed-host observation, and independent reproduction separate. Preserve `PASS`, `FAIL`, `NOT-RUN`, `UNKNOWN`, and `UNAVAILABLE` as distinct outcomes. Every observation retains its original version, commit, host, lifecycle, date, and evidence limits.

## Evidence Directory

`evidence/` contains current identity and status, the policy ledger, and runtime digest history. Retired observations, their record formats, and the routing evaluations remain in the [archive](#archived-experiments).

| File | Role and lifecycle |
| --- | --- |
| [runtime-identity.json](../evidence/runtime-identity.json) | Current plugin version, policy revision, runtime schema, digest, and input count |
| [release-status.json](../evidence/release-status.json) | Current candidate binding and host-observation state; derived identity fields must agree with the canonical identity |
| [repository-policy-revisions-v1.json](../evidence/repository-policy-revisions-v1.json) | Append-only repository policy ledger; older entries retain their original baselines and meaning |
| [runtime-contract-history-v3.json](../evidence/runtime-contract-history-v3.json) | Immutable release subjects and digests calculated under the current runtime schema v3 |
| [runtime-contract-history-v2.json](../evidence/runtime-contract-history-v2.json) | Immutable release subjects and digests calculated under runtime schema v2 |
| [runtime-contract-history-v1.json](../evidence/runtime-contract-history-v1.json) | Preserved release subjects and digests under runtime schema v1 |

The history files are schema-specific bindings, not duplicate release catalogs or host observations; none promises to list every published tag. Keep existing history entries unchanged. A new format needs its own version rather than repurposing an old filename.

## Recording A Result

1. Use a disposable, non-sensitive workspace and a read-only request. Place the workspace in a directory with no `AGENTS.md` or `CLAUDE.md` in itself or in any ancestor and no enclosing Git repository, so the host loads no project instruction file beside Axiom.
2. Record the exact host version, operating system, immutable Axiom tag and commit, installation method, and lifecycle source.
3. Compare the installed Hook with the [Hook Reference](reference/hooks.md).
4. Follow the routed example and no-route control in [Getting Started](guides/getting-started.md). A fresh session does not prove manual or automatic compaction behavior; leave unobserved cases `NOT-RUN`.
5. Retain only minimal sanitized facts. Never include credentials, private paths, raw transcripts, session identifiers, or external-service content.
6. Use the [compatibility report](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml) or the [routing-case report](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml).

The repository does not validate machine-readable compatibility records: repository policy revision 141 archived their formats and validator with the routing evaluations.

## Archived Experiments

Repository policy revision 42 retires the v0.7.4 compatibility snapshots and the frozen v0.10.0/v0.10.1 no-Hook experiment from the current release tree. Their exact files are preserved at immutable source commit `41239ac67d5c2c63f76182580ed7570882441f02`:

- [v0.7.4 host records](https://github.com/wheakerd/axiom/tree/41239ac67d5c2c63f76182580ed7570882441f02/evidence/v0.7.4);
- [derived profile bundle evidence](https://github.com/wheakerd/axiom/tree/41239ac67d5c2c63f76182580ed7570882441f02/evidence/profiles);
- [no-Hook contracts](https://github.com/wheakerd/axiom/tree/41239ac67d5c2c63f76182580ed7570882441f02/evals/no-hook) and [protocols, results, and failure records](https://github.com/wheakerd/axiom/tree/41239ac67d5c2c63f76182580ed7570882441f02/evals/no-hook-observation);
- [experiment implementations](https://github.com/wheakerd/axiom/tree/41239ac67d5c2c63f76182580ed7570882441f02/axiom_validation), [commands](https://github.com/wheakerd/axiom/tree/41239ac67d5c2c63f76182580ed7570882441f02/scripts), and [tests and fixtures](https://github.com/wheakerd/axiom/tree/41239ac67d5c2c63f76182580ed7570882441f02/tests); and
- [original field report](https://github.com/wheakerd/axiom/blob/41239ac67d5c2c63f76182580ed7570882441f02/docs/field-validation.md), [identity history narrative](https://github.com/wheakerd/axiom/blob/41239ac67d5c2c63f76182580ed7570882441f02/docs/runtime-identity.md), and [evaluation narrative](https://github.com/wheakerd/axiom/blob/41239ac67d5c2c63f76182580ed7570882441f02/evals/README.md).

Before removal, every retired file was compared byte-for-byte with that commit. Original source and result bindings remain inside the archived records. Retention in Git does not promote any old result to current evidence.

Repository policy revision 141 retires the routing evaluations, the routing-context budget records, and the compatibility-evidence records, formats, and validator from the current release tree, because the repository no longer measures host model behavior. Their exact files are preserved at the immutable release tag `v0.27.2`:

- [routing corpora, benchmark profiles, schemas, observer definitions, and observation records](https://github.com/wheakerd/axiom/tree/v0.27.2/evals), with their [narrative](https://github.com/wheakerd/axiom/blob/v0.27.2/evals/README.md);
- [routing-context budget method and per-version records](https://github.com/wheakerd/axiom/tree/v0.27.2/evals/context-budget);
- [v0.19.0 host observation records](https://github.com/wheakerd/axiom/tree/v0.27.2/evidence/v0.19.0) and the [compatibility-record formats](https://github.com/wheakerd/axiom/tree/v0.27.2/evidence); and
- [their validators](https://github.com/wheakerd/axiom/tree/v0.27.2/axiom_validation), [commands](https://github.com/wheakerd/axiom/tree/v0.27.2/scripts), and [tests](https://github.com/wheakerd/axiom/tree/v0.27.2/tests).

Version notes link each record at the tag of the release that carried it.

The current aggregate and CI no longer run the no-Hook experiment, build its bundle, import its test harness, or fetch its source commit. The runtime histories remain available for checking a release subject against its recorded digest.

Historical reproduction belongs to an explicitly scoped task using a separate checkout of the archive commit and its original prerequisites. Restoring source alone grants no authority to install, authenticate, run models, or publish.

## Architect goal-preservation observed acceptance

This anchor preserves links from immutable v0.10.1 notes. The original results, accepted limitations, and judgments remain in the [archived observation](https://github.com/wheakerd/axiom/blob/41239ac67d5c2c63f76182580ed7570882441f02/docs/field-validation.md#architect-goal-preservation-observed-acceptance). They are not acceptance evidence for the current package.

## Post-Merge Routing Observation

This anchor preserves links from earlier version notes. Their original publication requirements remain in the [archived protocol](https://github.com/wheakerd/axiom/blob/41239ac67d5c2c63f76182580ed7570882441f02/docs/field-validation.md#post-merge-routing-observation). Current publication follows the [release verification contract](maintainers/release-documentation.md#release-verification).
