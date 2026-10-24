# Release Documentation And Evidence

This policy separates release communication from release evidence. It applies
fix-forward to tags that contain it. Existing version notes, tags, GitHub
Releases, assets, attestations, and historical evidence remain unchanged.

## Responsibility Map

| Surface | Audience | It answers | Lifecycle and owner |
| --- | --- | --- | --- |
| `CHANGELOG.md` | Users and integrators | What changed, behavioral impact, and required action | Checked in with the candidate; canonical user-facing history |
| `docs/releases/v<version>.md` | Maintainers and auditors | Material migration, architecture, security, compatibility, or evidence detail | Checked in only when that detail is warranted; may truthfully describe candidate limitations |
| GitHub Release body | Release consumers | A concise tagged summary and immutable links to deeper documentation | Rendered from the tagged Changelog entry; never copied from the version note |
| Candidate evidence | Reviewers | What the source commit can prove before publication | Checked-in records and candidate reports; future remote states remain pending, not-run, or unavailable |
| Final immutable release evidence | Auditors | What tag, Release, assets, signatures, Latest state, and remote postconditions actually exist | Established only after publication and authoritative read-back |

No surface grants commit, tag, Release, asset-upload, publication, or Latest
authority. Preparation and validation remain separate from those external
actions.

## Changelog Contract

Every new version after `0.10.0` has one entry whose heading is
`## X.Y.Z - <state or date>`. The entry must contain:

- at least one change section such as `Added`, `Changed`, `Fixed`, `Removed`,
  `Deprecated`, or `Security`;
- `### Behavioral impact`; and
- `### Required action`, using `None` when users need do nothing.

Keep the heading state `unreleased` until the GitHub Release is published; the
tagged entry therefore always reads `unreleased`, and the rendered body omits
the heading. After publication, replace the state with the Release's UTC
publication date in the marketplace-publication pull request, or in the next
repository-policy change when that handoff does not apply. A version tagged
without a GitHub Release states that instead of a date.

Keep the entry concise and user-facing. Case-level results, commit and tree
IDs, timing, token counts, candidate investigations, workflow internals, and
historical run ledgers belong in version notes or evidence rather than the
Changelog.

## Deprecation And Removal

Before publishing a version, review the behavior and guidance superseded by
that release. Record each obsolete feature, command, configuration, validator,
or procedure in its Changelog entry under `Deprecated` or `Removed`. Name the
affected version, reason, supported replacement, and required user action;
put material migration detail in the version note.

Retire obsolete functionality in the same change: remove its active entry
points, calls, configuration, fallback paths, CI dependencies, and instructions.
A deprecation notice alone does not complete removal. Current documentation
must describe the supported replacement, and release checks must confirm that
the obsolete behavior cannot still be selected by the active workflow. Verify
actual support before retiring a format merely because a newer one exists.

Preserve immutable version notes and evidence with their original outcomes.
Historical records do not keep retired functionality enabled or turn its old
diagnostics into current release requirements. For host-owned external tools,
retire Axiom's dependency and invocations; removal from the user's system is a
separate action outside the package release.

## Version Notes

Create a version note only for material migration, architecture, security,
compatibility, or evidence detail. It is a durable technical record, not the
GitHub Release body. Before publication it may state that a tag, Release,
asset, workflow result, or host observation does not yet exist; that truthful
candidate text remains attached to the source commit and must not be presented
as final publication state.

Historical version notes are preserved. Correct an obsolete convention in the
next version or publication path instead of rewriting an immutable release.

## Deterministic Release Body

For a future tag that contains this policy, render the body offline from its
exact Changelog entry:

```bash
python3 scripts/check-release-evidence.py render-body --expected-version X.Y.Z
```

The renderer:

- omits the Changelog version heading, so `unreleased` is not copied into the
  final body;
- promotes entry subsections by one heading level;
- rewrites repository-relative links to immutable links under the exact tag;
- rejects traversal links, candidate-only publication text, duplicate version
  entries, missing fix-forward sections, and bodies above 8 KiB; and
- uses only the Python standard library, the checked-in Changelog, and standard
  output.

The separately authorized draft must use the exact rendered bytes. The
tag-owned release-evidence validator compares the draft, pre-publication, and
final body to the same rendering. The existing `notesSha256` attestation field
is retained for compatibility; it binds the GitHub Release body digest, not the
version-note file.

## Release Verification

From `0.11.0`, release verification uses repository checks, exact signed-main
and created-tag checks, and immutable Release verification. The checked-in
[tag controller](../../axiom_validation/release_tag_controller.py) requires
`repository-guards`, `unit-and-integration-tests`, and `hook-runtime-gate`
against the exact release commit. The [governance snapshot](../repository-governance.md#main-branch-policy)
records the dated server-side promotion of the hook aggregate.

The draft starts with one `axiom-v<version>-release-policy-<sha256>.json`
asset. Render it with `scripts/check-release-evidence.py render-policy` and
the exact version, tag, commit and tree arguments. Its closed
`repository-checks-v1` schema records `repository-guards` and
`unit-and-integration-tests` and binds the release subject. This artifact is
not the complete live ruleset: the tag controller separately enforces its
current prerequisites, including `hook-runtime-gate`. Preserve the artifact
schema's meaning rather than treating its shorter list as permission to skip
a current gate. The publisher
validates the downloaded bytes, uploads an integrity attestation, and verifies
both assets after publication. This record describes verification policy;
actual check results remain bound to their GitHub Actions runs. The attestation
states its `release-policy-and-artifact-integrity` scope.

Earlier version contracts and recorded experiments retain their historical
meaning. Asset names and validators are selected by the release version;
existing Releases and their evidence are not migrated.

## Marketplace Publication

The default [marketplace](../../.agents/plugins/marketplace.json) and the
[Claude Code catalog](../../.claude-plugin/marketplace.json) select the same
repository and immutable production `v<version>` ref, and both catalogs advance
together. From `v0.17.0` each catalog uses a `git-subdir` source whose `path`
is the installed plugin root, `./plugin` for Codex and `plugin` for Claude Code,
so hosts install only that subtree. A catalog that selects an earlier tag keeps
the Git `url` source, because those tags hold the plugin at the repository
root. Their selected plugin may
precede the development manifest version. Keep the
selection unchanged during ordinary `main` development and for releases that
are not Latest. The client and user own refresh and automatic-update policy;
there is no repository-side client updater or `main`-triggered release check.

After verifying final immutable publication and GitHub Latest, the
[publisher](../../.github/workflows/publish-immutable-release.yml) renders the
standard source object in its job summary. The same handoff runs during
final-only recovery. It reports **Marketplace publication pending** because
the workflow does not write to protected `main` or bypass its PR rules.

Complete the authorized catalog publication through the existing signed PR
process:

1. Verify the current Latest Release is final, stable, immutable, and identifies
   the intended tag and signed commit. For a deliberate Latest selection made
   outside the publisher, perform the same verification before preparing the
   catalog change; a Release event alone does not prove a Latest transition.
2. On a task branch from current `main`, replace only the Axiom entry's source
   in each catalog with the verified Git URL, version tag, and the source type
   and subtree path that tag requires. Preserve other
   catalog metadata, and date the released version's Changelog heading as the
   [Changelog Contract](#changelog-contract) describes.
   Record the next repository-policy revision and its baseline, retain the
   installed runtime identity, and run the contributor checks. This catalog
   operation requires publication scope; a policy revision does not grant it.
3. Recheck Latest before merging the signed PR with its required checks. If it
   changed, refresh the candidate for the selected release instead of merging
   a stale reference. Do not move a version tag or the legacy `latest` Git tag.
4. Read back both merged catalogs and resolve their plugin tag. Confirm that the
   selected manifest version matches that tag. Record the catalog commit for
   users who need a fixed catalog snapshot. A tag on the marketplace repository
   may contain a different plugin reference; it is not a per-plugin pin.

The directory update is complete only after that merge and readback. Release
publication or a generated job summary alone does not update the directory or
an installed client. A failed or delayed handoff leaves the previous catalog
selection available; resume it without republishing the immutable Release.

The Codex catalog format was last verified on 2026-10-24 against the official
[marketplace source specification](https://developers.openai.com/plugins/build/plugins#marketplace-metadata),
whose `git-subdir` plugin source takes `url`, `path`, and `ref` or `sha`. The
Claude Code catalog format was last verified on 2026-10-24 against the
official [marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources),
whose `git-subdir` plugin source takes `url`, `path`, `ref`, and `sha` and
checks out only that subdirectory. Use each format's native fields; do not add
an Axiom update channel or schedule to either plugin manifest.

## Candidate And Final Evidence

Candidate evidence is limited to facts observable at its source commit. It can
bind checked-in files, static validation, a candidate commit and tree, and
already existing remote prerequisites. It cannot claim its future merge, tag,
Release, assets, Latest selection, immutable state, post-publication checks, or
new host observation.

Final evidence exists only after all of the following are directly verified:

1. the immutable tag identifies the intended signed commit and tree;
2. the GitHub Release identifies that tag and exact rendered body;
3. the final asset set and content digests match their frozen identities;
4. the Release reports immutable and non-prerelease state;
5. GitHub Latest identifies the intended Release when that transition was
   authorized; and
6. required post-publication signature and publication checks pass.

An attestation generated while a draft is mutable is a candidate artifact. It
becomes part of final evidence only when the immutable Release and all remote
postconditions above are verified. A failed, unavailable, unknown, or not-run
result remains separate and is never relabeled by publication.

## Fix-Forward Boundary

Do not edit an immutable Release, move or recreate its tag, replace its assets,
or rewrite historical evidence to adopt this architecture. If a published body
or evidence design needs correction, document the discrepancy and apply the
new contract to the next authorized version or publication.
