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

## Source And Version Scope

Current guides, concepts, references, and contributor procedures describe the
implementation and contracts in the same repository snapshot. Write the
supported workflow in the present tense, verify it against its source owner,
and replace obsolete instructions in place. Put release-by-release additions,
removals, and migration narratives in the Changelog or version notes.

"Current" means the checked-in tree that accompanies the document. `main` may
contain unreleased changes; its documentation does not prove that the latest
published or installed package has those changes. Users checking an installed
release should use the documentation at that release's tag. Source inspection
establishes declared behavior; installation, host observations, and remote
publication still require evidence from their own owners.

| Content | Version rule |
| --- | --- |
| Current usage, architecture, security, and contribution guidance | Follow the same checked-in source; avoid manual copies of the current release number and version-by-version narration |
| Current version, digest, status, or measured counts | Link to the canonical manifest, record, or measurement command; use a checked generated region when displaying the values |
| Changelog, version notes, and migration history | Retain the version whose change or migration they describe |
| Observations, failures, evaluation results, and historical methods | Preserve the exact original subject, version, date, schema, and outcome; never relabel them as current |
| Supported schema or protocol selectors, compatibility limits, and prerequisites | Keep exact versions when they determine valid behavior; update their current selection only with the owning implementation |

Version information is therefore not limited to change history. A format such
as `schema-v3.json`, an immutable evidence link, or an exact compatibility
boundary is part of a usable contract. Do not remove it merely to make prose
appear version-neutral. Conversely, a heading such as "Current vX.Y.Z" or a
manually copied measurement table does not belong in a maintained guide when
its canonical source already supplies that value.

When reviewing a current document, distinguish an implemented capability from
a plan, an example, and an observed result. Update the capability description
from source, keep examples tied to their actual contract, and preserve
`NOT-RUN` or other evidence limits until new observations justify a change.

## Document Classes

| Class | Primary audience | Responsibility |
| --- | --- | --- |
| User guide | Plugin users | Installation, first use, updating, removal, and troubleshooting |
| Concept | Users and reviewers | Architecture, routing, trust, and runtime identity |
| Reference | Users and auditors | Skills, Hooks, compatibility, and validation protocols |
| Maintainer | Contributors and maintainers | Documentation, governance, release, and validator policy |
| Evidence or generated | Auditors and automation | Machine facts, host observations, digests, and bounded summaries |

A document may link across classes, but it must not silently acquire another
class's ownership.

Project-operation plans, marketing drafts, and channel-status ledgers belong
outside the plugin release tree. Retired material remains in Git history and
does not establish current product guidance or external state.

## Lifecycle States

Use this vocabulary when a document's role is not obvious from its location:

| State | Meaning |
| --- | --- |
| `current` | Maintained guidance for the implementation in the same checked-in tree |
| `historical` | Immutable or append-only past evidence or narrative |
| `generated` | Content derived from a canonical machine-readable source |
| `project-plan` | Intended work or channel activity, not product capability |
| `archived` | Retained for traceability and excluded from current navigation |

Lifecycle metadata is optional when the directory and index make the state
unambiguous. If metadata is present, it must use one of these values. A claim
about an external platform or channel must include an absolute
`last_verified` date; conceptual prose does not need an artificial timestamp.
Place optional metadata near the document H1 using this exact form:

```markdown
<!-- lifecycle: current -->
```

## Current Repository State

The current repository assigns these responsibilities:

- `README.md` owns the bounded public introduction and safe-start summary;
- `CONTRIBUTING.md` owns contribution intake and the repository map;
  `docs/maintainers/runtime-changes.md` owns runtime-authoring rules and
  `docs/maintainers/validation.md` owns contributor check procedures;
- `SECURITY.md` owns vulnerability reporting and security boundaries, while
  `CHANGELOG.md` owns user-visible changes and required action;
- `docs/guides/` owns installation, first use, update, removal, and
  troubleshooting;
- `docs/reference/hooks.md` renders the canonical Hook declarations and
  wrapper, while `docs/getting-started.md` is a compatibility entry for
  historical links;
- `docs/compatibility.md` owns the concise current support contract and links
  to historical records without reproducing their run narratives;
- `docs/releases/` contains version notes;
- `docs/maintainers/release-documentation.md` defines release-document and
  evidence responsibilities for future releases;
- `evidence/` and `evals/results/` retain machine records and observations;
  `docs/field-validation.md` indexes retired records at immutable archive sources;
- `evals/README.md` and `evals/context-budget/README.md` own current evaluation
  guidance; `evals/history/` retains earlier methods and run narratives.

[The documentation index](../README.md) describes these current locations by
audience and task. A proposed path does not become canonical until the content,
inbound links, and lifecycle classification move in one merged change.

## Canonical Structure

The repository uses this responsibility split without creating unnecessary
short documents:

```text
README.md
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
docs/
|-- README.md
|-- guides/
|-- reference/
|-- maintainers/
`-- releases/
evidence/
evals/
```

Topical current references may remain directly under `docs/` when another
directory would create artificial fragmentation.

## Canonical Ownership

| Fact | Canonical owner | Current rule |
| --- | --- | --- |
| Product introduction and safe first step | `README.md` | Current and within the documented size budget |
| Contribution intake and repository map | `CONTRIBUTING.md` | Current; links to detailed authoring and validation owners |
| Runtime-authoring requirements | `docs/maintainers/runtime-changes.md` | Contributor policy; installed behavior remains owned by Skills, hooks, and manifests |
| Contributor check procedures | `docs/maintainers/validation.md` | Current; CI and executable validators own the actual checks |
| Vulnerability reporting | `SECURITY.md` | Private reporting instructions and bounded security claims |
| Public Skill inventory | `skills/*/SKILL.md` and manifests | Current; README keeps a validated rendering |
| Hook declarations and executable commands | `hooks/*.json` and packaged wrappers | Current; `docs/reference/hooks.md` is the validated rendering |
| Installation, first use, update, removal, troubleshooting | `docs/guides/getting-started.md` and `docs/guides/managing-installation.md` | Current; `docs/getting-started.md` is a compatibility entry only |
| Current plugin version | Codex plugin manifest | Current |
| Runtime contract identity | Versioned runtime-identity inputs and machine output | Current |
| Current compatibility boundary | Current release-status evidence with `docs/compatibility.md` as the concise reference | Current |
| Historical host observations | Version-bound records under `evidence/**`, `evals/results/**`, and immutable sources indexed by `docs/field-validation.md` | Preserve original subjects and outcomes; archived records do not establish current support |
| User-visible release changes and required action | `CHANGELOG.md` | Current; future Release bodies render this entry at the exact tag |
| Exceptional migration, architecture, security, compatibility, or evidence detail | `docs/releases/v<version>.md` when warranted | Candidate detail until publication; then preserved history, never reused as the final Release body |
| GitHub Release body | Deterministic rendering of the tagged `CHANGELOG.md` entry | Current for future tags after v0.10.0 |
| Candidate evidence | Checked-in version note and machine records bound to the source commit | Current; may state only what that commit can prove |
| Final remote publication facts | Immutable Release, assets, attestation, and verified remote postconditions | Current; produced only after those objects exist |
| Repository governance | Dated governance evidence and maintainer reference | Current |
| Routing evaluation contracts and optional observation method | `evals/README.md` with versioned cases, schemas, and benchmark manifests | Current; earlier methods remain under `evals/history/` |
| Routing-context measurements | Versioned `evals/context-budget/results/` records with `evals/context-budget/README.md` | Counts are static proxies; historical records keep their original bindings |

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
| Current guidance contains release-specific narration or copied measurements | Replace the narration with the implemented workflow and link to version notes or the canonical measurement source; preserve original evidence |
| User-visible change | Add a concise `CHANGELOG.md` entry that states impact and required action |
| Exceptional migration, architecture, security, compatibility, or evidence detail | Add or update a version note only when the detail is material |
| External publication or channel state | Record an absolute verification date and do not promote planned or submitted work to published |
| Document move or lifecycle change | Update inbound links, the documentation index, and the lifecycle classification atomically |

## Migration And Move Rules

- Use staged, reviewable changes and keep links valid at every merged phase.
- Describe the current repository before the target state; do not claim a later
  phase has completed.
- Move a fact only after identifying its canonical owner. Remove the competing
  copy or replace it with a concise link in the same change.
- Preserve Git history where practical and never delete or rewrite immutable
  evidence, evaluation results, failure records, or historical Release facts
  to simplify navigation. Retired experiments may leave the current tree after
  their exact bytes are verified at an immutable Git commit and the canonical
  evidence owner links to that archive. Retire their active commands, default
  checks, and CI dependencies together; preserve applicable generic regression
  coverage with synthetic fixtures.
- Keep project plans and channel status outside the plugin release tree.
  Preserve retired records in Git history with their absolute verification
  dates and truthful planned, submitted, or published state.
- Do not copy candidate-only absence or future-tense publication text into a
  final Release body. Render future bodies from the tagged Changelog entry and
  establish final evidence only from the immutable remote objects.
- Use repository-relative links for checked-in files. External URLs are
  permitted when the external destination is the actual owner.
- Keep public documentation free of non-public repository content,
  credentials, internal endpoints, and operational coordination detail.
- Reclassify the exact final diff against the runtime-identity contract. A
  documentation reorganization must not assume that a changed runtime input is
  policy-only.

## Validation Expectations

Every documentation change must, at minimum:

- review current instructions against their same-snapshot source owners and
  separate release history, schema selectors, and observed evidence from
  current capability claims;
- keep `README.md` at or below the enforced 16 KiB ceiling, and report the
  preferred 8--12 KiB range;
- preserve repository-relative links and valid local anchors;
- contain exactly one level-one heading in each current Markdown document and
  avoid skipped heading levels;
- keep `docs/README.md` complete for current public documents and reject
  current-document orphans, including the current evaluation and context-budget
  entry points outside `docs/`;
- accept only the documented lifecycle values;
- preserve generated marker boundaries and compare rendered machine facts with
  their canonical sources;
- require current entry points to link their canonical status and identity
  owners, while the Changelog and selected version note retain exact release
  bindings; a repeated version number is not a substitute for those links;
- keep current public guidance from linking to non-public sources;
- preserve the parseable README `### Shared skills` inventory until its owning
  validator is migrated atomically;
- validate the public Hook reference against checked-in declarations and
  wrappers; and
- keep historical and project-plan documents, including `evals/history/`, out
  of current task navigation.

Run the deterministic, Python-standard-library-only documentation validator
from the repository root:

```bash
python3 scripts/check-documentation.py
```

It runs offline checks for repository-owned facts and is included in the
publication aggregate and full unit suite. External URL availability, spelling,
and prose style remain advisory or scheduled signals rather than unstable
required gates.
