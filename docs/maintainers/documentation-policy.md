# Documentation Policy

This policy defines how Axiom's public documentation is organized and kept
accurate. It governs repository documentation only; it does not change an
installed Skill, route, authorization boundary, Hook, wrapper, manifest, or
runtime contract.

## Principles

1. Each document has one primary audience and responsibility.
2. Each durable fact has one canonical owner. Other documents link, summarize,
   or render that fact instead of maintaining a competing manual copy.
3. Current guidance, historical evidence, generated facts, and project plans
   remain visibly distinct.
4. Static validation is not host-observed evidence, and a plan is not an
   implemented capability.
5. Navigation favors user tasks without hiding maintainer and audit material.
6. Documentation must not grant action authority or imply behavior that the
   checked-in runtime does not provide.

## Document Classes

| Class | Primary audience | Responsibility |
| --- | --- | --- |
| User guide | Plugin users | Installation, first use, updating, removal, and troubleshooting |
| Concept | Users and reviewers | Architecture, routing, trust, and runtime identity |
| Reference | Users and auditors | Skills, Hooks, compatibility, and validation protocols |
| Maintainer | Contributors and maintainers | Documentation, governance, release, and validator policy |
| Evidence or generated | Auditors and automation | Machine facts, host observations, digests, and bounded summaries |
| Project operations | Maintainers | Marketing, distribution, channel status, plans, and archives |

A document may link across classes, but it must not silently acquire another
class's ownership.

## Lifecycle States

Use this vocabulary when a document's role is not obvious from its location:

| State | Meaning |
| --- | --- |
| `current` | Maintained guidance for the present product |
| `historical` | Immutable or append-only past evidence or narrative |
| `generated` | Content derived from a canonical machine-readable source |
| `project-plan` | Intended work or channel activity, not product capability |
| `archived` | Retained for traceability and excluded from current navigation |

Lifecycle metadata is optional when the directory and index make the state
unambiguous. If metadata is present, it must use one of these values. A claim
about an external platform or channel must include an absolute
`last_verified` date; conceptual prose does not need an artificial timestamp.

## Current Repository State

The documentation migration began with overlapping responsibilities:

- `README.md` owns the bounded public introduction and safe-start summary;
- `docs/guides/` owns installation, first use, update, removal, and
  troubleshooting;
- `docs/reference/hooks.md` renders the canonical Hook declarations and
  wrapper, while `docs/getting-started.md` is a compatibility entry for
  historical links;
- `docs/compatibility.md` combines the current support contract with historical
  runs and candidate investigations;
- `docs/releases/` contains version notes;
- `docs/marketing/` contains project-operation plans beside current guidance;
- `evidence/` and `evals/results/` retain machine records and observations.

During migration, [the documentation index](../README.md) must describe these
current locations truthfully. A target path does not become canonical until
the content and its links move in a merged change.

## Target Structure

The repository should converge on this responsibility split without creating
unnecessary short documents:

```text
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
docs/
|-- README.md
|-- guides/
|-- concepts/
|-- reference/
`-- maintainers/
project/
|-- marketing/
|-- distribution/
`-- archive/
evidence/
evals/
```

Equivalent, simpler groupings are acceptable when ownership remains clear.

## Canonical Ownership

| Fact | Canonical owner | Migration status |
| --- | --- | --- |
| Product introduction and safe first step | `README.md` | Current and within the documented size budget |
| Public Skill inventory | `skills/*/SKILL.md` and manifests | Current; README keeps a validated rendering |
| Hook declarations and executable commands | `hooks/*.json` and packaged wrappers | Current; `docs/reference/hooks.md` is the validated rendering |
| Installation, first use, update, removal, troubleshooting | `docs/guides/getting-started.md` and `docs/guides/managing-installation.md` | Current; `docs/getting-started.md` is a compatibility entry only |
| Current plugin version | Synchronized plugin manifests | Current |
| Runtime contract identity | Versioned runtime-identity inputs and machine output | Current |
| Current compatibility boundary | Current release-status evidence with a concise rendered reference | Compatibility reduction is pending |
| Historical host observations | `evidence/**` and `evals/results/**` | Current and preserved |
| User-visible release changes | `CHANGELOG.md` | Current; responsibility clarification is pending |
| Exceptional migration or release detail | Version notes when warranted | Current; responsibility clarification is pending |
| Final remote publication facts | Immutable post-publication Release evidence | Current; responsibility clarification is pending |
| Repository governance | Dated governance evidence and maintainer reference | Current |
| Marketing and channel status | `project/**` with absolute verification dates | Migration from `docs/marketing/` is pending |

Machine-derived facts should use bounded generated regions or deterministic
checks where practical. Human prose may explain their meaning but must not
redefine their values.

## Update Triggers

| Changed surface | Documentation action |
| --- | --- |
| Skill, route, trigger, or stop condition | Update the owning reference and any validated summary in the same change |
| Hook declaration or wrapper command | Regenerate or update the Hook reference and verify it against both sources |
| Installation, update, removal, or troubleshooting behavior | Update the canonical guide; link from other surfaces instead of copying steps |
| Host support or observed compatibility | Update current status from the owning evidence and preserve prior records unchanged |
| Manifest version or runtime digest | Render the current identity from its machine-readable owner |
| User-visible change | Add a concise `CHANGELOG.md` entry that states impact and required action |
| Exceptional migration, architecture, security, compatibility, or evidence detail | Add or update a version note only when the detail is material |
| External publication or channel state | Record an absolute verification date and do not promote planned or submitted work to published |
| Document move or lifecycle change | Update inbound links, the documentation index, and the lifecycle classification atomically |

## Migration Rules

- Use staged, reviewable changes and keep links valid at every merged phase.
- Describe the current repository before the target state; do not claim a later
  phase has completed.
- Move a fact only after identifying its canonical owner. Remove the competing
  copy or replace it with a concise link in the same change.
- Preserve Git history where practical and never delete or rewrite immutable
  evidence, evaluation results, failure records, or historical Release facts
  to simplify navigation.
- Keep project plans and channel status out of current user guidance. Preserve
  their absolute verification dates and truthful planned, submitted, or
  published state.
- Use repository-relative links for checked-in files. External URLs are
  permitted when the external destination is the actual owner.
- Keep public documentation free of non-public repository content,
  credentials, internal endpoints, and operational coordination detail.
- Reclassify the exact final diff against the runtime-identity contract. A
  documentation reorganization must not assume that a changed runtime input is
  policy-only.

## Validation Expectations

Every documentation change must, at minimum:

- keep `README.md` at or below the 16 KiB migration ceiling once the README
  reduction phase lands, and report the preferred 8--12 KiB range;
- preserve repository-relative links and valid local anchors;
- contain exactly one level-one heading in each current Markdown document and
  avoid skipped heading levels;
- keep `docs/README.md` complete for current public documents and reject
  current-document orphans;
- accept only the documented lifecycle values;
- preserve generated marker boundaries and compare rendered machine facts with
  their canonical sources;
- keep current public guidance from linking to non-public sources;
- preserve the parseable README `### Shared skills` inventory until its owning
  validator is migrated atomically;
- validate the public Hook reference against checked-in declarations and
  wrappers; and
- keep historical and project-plan documents out of current user navigation.

The repository will add a deterministic, offline where practical,
Python-standard-library-only validator as the final migration phase. Until that
validator lands, contributors must perform the applicable checks manually and
run the existing publication aggregate and unit suite. External URL
availability, spelling, and prose style remain advisory or scheduled signals
rather than unstable required gates.
