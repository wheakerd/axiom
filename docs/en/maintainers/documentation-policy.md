# Documentation Policy

This policy defines how Axiom's public documentation is organized and kept accurate. It governs repository documentation only; it does not change an installed Skill, route, authorization boundary, Hook, wrapper, manifest, or runtime contract.

## Principles

1. Each document has one primary audience and responsibility.
2. Each durable fact has one canonical owner. Other documents link, summarize, or render that fact instead of maintaining a competing manual copy.
3. The tree describes the current implementation. Release history lives in the Changelog, the release tags, and Git history.
4. Static validation is not host-observed evidence, and a plan is not an implemented capability.
5. Navigation favors user tasks without hiding maintainer and audit material.
6. Documentation must not grant action authority or imply behavior that the checked-in runtime does not provide.

## Source And Version Scope

Current guides, concepts, references, and contributor procedures describe the implementation and contracts in the same repository snapshot. Write the supported workflow in the present tense, verify it against its source owner, and replace obsolete instructions in place. Put release-by-release additions, removals, and migration narratives in the Changelog.

"Current" means the checked-in tree that accompanies the document. `main` may contain unreleased changes; its documentation does not prove that the latest published or installed package has those changes. Users checking an installed release should use the documentation at that release's tag. Source inspection establishes declared behavior; installation, host observations, and remote publication still require evidence from their own owners.

| Content | Version rule |
| --- | --- |
| Current usage, architecture, security, and contribution guidance | Follow the same checked-in source; avoid manual copies of the current release number and version-by-version narration |
| Current version, digest, status, or measured counts | Link to the canonical manifest, record, or measurement command; use a checked generated region when displaying the values |
| Changelog entries and migration history | Retain the version whose change or migration they describe |
| Observations and failures | Preserve the exact original subject, version, date, and outcome; never relabel them as current |
| Supported schema or protocol selectors, compatibility limits, and prerequisites | Keep exact versions when they determine valid behavior; update their current selection only with the owning implementation |

Version information is therefore not limited to change history. A format such as `schema-v3.json`, an immutable evidence link, or an exact compatibility boundary is part of a usable contract. Do not remove it merely to make prose appear version-neutral. Conversely, a heading such as "Current vX.Y.Z" or a manually copied measurement table does not belong in a maintained guide when its canonical source already supplies that value.

When reviewing a current document, distinguish an implemented capability from a plan, an example, and an observed result. Update the capability description from source, keep examples tied to their actual contract, and preserve stated evidence limits until new observations justify a change.

## Document Classes

| Class | Primary audience | Responsibility |
| --- | --- | --- |
| User guide | Plugin users | Installation, first use, updating, removal, and troubleshooting |
| Concept | Users and reviewers | Architecture, routing, trust, and runtime identity |
| Reference | Users and auditors | Skills, Hooks, compatibility, and validation protocols |
| Maintainer | Contributors and maintainers | Documentation, governance, release, and validator policy |
| Evidence or generated | Auditors and automation | Machine facts, host observations, digests, and bounded summaries |

A document may link across classes, but it must not silently acquire another class's ownership.

Project-operation plans, marketing drafts, and channel-status ledgers belong outside the plugin release tree. Retired material remains in Git history and does not establish current product guidance or external state.

## Current Repository State

The current repository assigns these responsibilities:

- `README.md` owns the bounded public introduction, the generated skill index, installation and update quick start, and first-use example; each skill's `SKILL.md` owns its description and `docs/en/examples.md` owns example requests;
- `CONTRIBUTING.md` owns contribution intake and the repository map; `docs/en/maintainers/runtime-changes.md` owns runtime-authoring rules and `docs/en/maintainers/validation.md` owns contributor check procedures;
- `SECURITY.md` owns vulnerability reporting and security boundaries, while `CHANGELOG.md` owns user-visible changes and required action;
- `CODE_OF_CONDUCT.md` owns community conduct expectations and the enforcement contact;
- `docs/en/guides/` owns installation, first use, update, removal, and troubleshooting;
- `docs/en/reference/hooks.md` renders the canonical Hook declarations and wrapper;
- `docs/en/compatibility.md` owns the concise current support contract, the procedure for reporting a host result, and the pointer to the release tag that keeps earlier records;
- `docs/en/maintainers/release-documentation.md` defines release-document and evidence responsibilities for future releases; and
- `.ci/` holds the repository checks and the machine-readable runtime identity.

[The documentation index](../README.md) describes these current locations by audience and task. A proposed path does not become canonical until the content and inbound links move in one merged change.

## Canonical Structure

The repository uses this responsibility split without creating unnecessary short documents:

```text
README.md
CHANGELOG.md
CODE_OF_CONDUCT.md
CONTRIBUTING.md
SECURITY.md
docs/
|-- README.md
|-- en/
|   |-- README.md
|   |-- guides/
|   |-- reference/
|   `-- maintainers/
`-- zh-CN/
.ci/
```

Each direct subdirectory of `docs/` is a localized documentation set named by its BCP 47 language tag, and `docs/README.md` only selects the language. Topical current references may remain directly under a language directory such as `docs/en/` when another directory would create artificial fragmentation.

README stays a landing page: identity, a generated skill index, installation, updating, first use, and links. The skill index and the badge row that counts the bundled skills are generated regions rendered in canonical order from each skill's `agents/openai.yaml` short description; `python3 .ci/scripts/render-release-facts.py --render` refreshes them, and the publication checks reject a stale rendering. README may ask readers once, in plain words, to star the repository; the request offers nothing in exchange and does not claim that a star brings release notifications.

## Translations

English documentation is canonical and the default. English documents live in `docs/en/`. A document may have one Simplified Chinese twin at the same path under `docs/zh-CN/`, for readers who prefer Chinese; the root `README.zh-CN.md` is the twin of `README.md`. The twin translates prose and table headers only. It keeps its source's heading structure, fenced code blocks, generated regions, and link targets, substituting a linked document's own twin where one exists and nothing else. Each pair links to the other through a language switcher after the title: the English document links to its twin, and the twin links back to its source. Skill descriptions, example requests, commands, identifiers, and trigger definitions stay English, and no localized alias is published.

A twin is not indexed separately and does not count as a current document of its own; it is reached through its source. It changes in the same change as its source, and the documentation validator rejects a twin whose structure, code, generated facts, or links drift from the source. Maintainer, evidence, release, and reference documents stay English unless a twin is deliberately added under the same rules.

## Canonical Ownership

| Fact | Canonical owner | Current rule |
| --- | --- | --- |
| Product introduction and safe first step | `README.md` | Current and within the documented size budget |
| Contribution intake and repository map | `CONTRIBUTING.md` | Current; links to detailed authoring and validation owners |
| Runtime-authoring requirements | `docs/en/maintainers/runtime-changes.md` | Contributor policy; installed behavior remains owned by Skills, hooks, and manifests |
| Contributor check procedures | `docs/en/maintainers/validation.md` | Current; CI and executable validators own the actual checks |
| Discoverability facts and external listing status | `docs/en/maintainers/distribution-channels.md` | Dated observations; a submission is recorded only when it was made |
| Vulnerability reporting | `SECURITY.md` | Private reporting instructions and bounded security claims |
| Community conduct and enforcement contact | `CODE_OF_CONDUCT.md` | Current; adapted from the Contributor Covenant |
| Public Skill inventory | `plugin/skills/*/SKILL.md` and manifests | Current; `README.md` keeps a generated index of each skill's short description |
| Hook declarations and executable commands | `plugin/hooks/*.json` and packaged wrappers | Current; `docs/en/reference/hooks.md` is the validated rendering |
| Installation, first use, update, removal, troubleshooting | `docs/en/guides/getting-started.md` and `docs/en/guides/managing-installation.md` | Current |
| Current plugin version | Codex plugin manifest | Current |
| Runtime contract identity | Versioned runtime-identity inputs and machine output | Current; `docs/en/runtime-identity.md` renders the checked identity |
| Git workflow routing boundary | The `traceable-git-submit` skill | Current; `docs/en/architecture.md` summarizes it |
| Current compatibility boundary | `docs/en/compatibility.md` | Current |
| Records from earlier releases | The release tags; `docs/en/compatibility.md` names the tag that keeps them | Not part of the current tree; they do not establish current support |
| User-visible release changes and required action | `CHANGELOG.md` | Current; future Release bodies render this entry at the exact tag |
| GitHub Release body | Deterministic rendering of the tagged `CHANGELOG.md` entry | Current |
| Candidate evidence | Checked-in machine records bound to the source commit | Current; may state only what that commit can prove |
| Final remote publication facts | Immutable Release, assets, attestation, and verified remote postconditions | Current; produced only after those objects exist |
| Repository governance | `docs/en/repository-governance.md`; the live rulesets are the source for their own settings | Current |
| Simplified Chinese translations | The English source in `docs/en/` and its twin at the same path under `docs/zh-CN/` | Current; the twin translates prose and table headers and changes with its source |

Machine-derived facts should use bounded generated regions or deterministic checks where practical. Human prose may explain their meaning but must not redefine their values.

## Update Triggers

| Changed surface | Documentation action |
| --- | --- |
| Skill, route, trigger, or stop condition | Update the owning reference and any validated summary in the same change |
| Hook declaration or wrapper command | Regenerate or update the Hook reference and verify it against both sources |
| Installation, update, removal, or troubleshooting behavior | Update the canonical guide; keep README install/update quick-start commands aligned and link to the guide for full procedures |
| Host support or observed compatibility | Update current status from the owning evidence and preserve prior records unchanged |
| Manifest version or runtime digest | Render the current identity from its machine-readable owner |
| Current guidance contains release-specific narration or copied measurements | Replace the narration with the implemented workflow and link to the canonical measurement source |
| User-visible change | Add a concise `CHANGELOG.md` entry that states impact and required action |
| External publication or channel state | Record an absolute verification date and do not promote planned or submitted work to published |
| Document move | Update inbound links and the documentation index atomically |

## Migration And Move Rules

- Use staged, reviewable changes and keep links valid at every merged phase.
- Describe the current repository before the target state; do not claim a later phase has completed.
- Move a fact only after identifying its canonical owner. Remove the competing copy or replace it with a concise link in the same change.
- Never rewrite a published tag, a Release, or its assets. Material that describes an earlier release leaves the current tree once it exists at a release tag; link the tag instead of keeping a copy, and retire its active commands, default checks, and CI dependencies in the same change.
- Keep project plans and channel status outside the plugin release tree. Preserve retired records in Git history with their absolute verification dates and truthful planned, submitted, or published state.
- Do not copy candidate-only absence or future-tense publication text into a final Release body. Render future bodies from the tagged Changelog entry and establish final evidence only from the immutable remote objects.
- Use repository-relative links for checked-in files. External URLs are permitted when the external destination is the actual owner.
- Keep public documentation free of non-public repository content, credentials, internal endpoints, and operational coordination detail.
- Reclassify the exact final diff against the runtime-identity contract. A documentation reorganization must not assume that a changed runtime input is policy-only.

## Validation Expectations

Every documentation change must, at minimum:

- review current instructions against their same-snapshot source owners and separate release history, schema selectors, and observed evidence from current capability claims;
- preserve repository-relative links and valid local anchors;
- contain exactly one level-one heading in each current Markdown document and avoid skipped heading levels;
- keep `docs/README.md` complete for current public documents and reject current-document orphans;
- name every direct subdirectory of `docs/` by a BCP 47 language tag and keep the language selector as its only direct file;
- preserve generated marker boundaries and compare rendered machine facts with their canonical sources;
- keep current public guidance from linking to non-public sources;
- validate the public Hook reference against checked-in declarations and wrappers;
- keep each `docs/zh-CN/` twin bound to its `docs/en/` source: the source exists, both carry the language switcher, and the heading structure, fenced code blocks, generated regions, and link targets match.

Run the deterministic, Python-standard-library-only documentation validator from the repository root:

```bash
python3 .ci/scripts/check-documentation.py
```

It runs offline checks for repository-owned facts and is included in the publication aggregate and full unit suite. External URL availability, spelling, and prose style remain advisory or scheduled signals rather than unstable required gates.
