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

Keep the entry concise and user-facing. Case-level results, commit and tree
IDs, timing, token counts, candidate investigations, workflow internals, and
historical run ledgers belong in version notes or evidence rather than the
Changelog.

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
