# Release Documentation And Evidence

A maintainer releases a version by pushing its tag. CI checks the tagged commit, builds the versioned installed tree on the `release` branch, and publishes an immutable GitHub Release with its notes and evidence. This page describes the procedure, what CI does, the notes and assets a Release carries, and recovery. Existing tags, Releases, assets, and attestations remain unchanged.

## Responsibility Map

| Surface | Audience | It answers | Source |
| --- | --- | --- | --- |
| Release tag `vX.Y.Z` | Everyone | Which `main` commit is that version | Pushed by a maintainer; the version's only source |
| GitHub Release body | Users and integrators | What changed, behavioral impact, required action | The annotated tag's message, or the tagged commit's message |
| `release` branch | Hosts | The installed tree of every published version | One GitHub-signed commit per release, made by the Release workflow |
| Release assets | Auditors | The exact installed files, the release subject, and what was verified | Built and attached by the Release workflow and the publisher |

No surface grants commit, tag, Release, asset-upload, publication, or Latest authority.

## Cut A Release

1. Merge the change to `main` through the normal signed pull request, and wait until `repository-guards`, `unit-and-integration-tests`, `hook-runtime-gate`, and `Verify signed main history` have passed on the merge commit.
2. Classify the change and choose the version with [Runtime Identity](../runtime-identity.md#classify-a-change). A repository-only change creates no tag.
3. Write the release notes as the message of a signed annotated tag on that commit, and push the tag:

   ```bash
   git tag -s vX.Y.Z -m "Release notes in Markdown" <commit>
   git push origin vX.Y.Z
   ```

   For longer notes, write them to a file and use `git tag -s vX.Y.Z -F notes.md <commit>`. A lightweight tag on a GitHub-signed commit also releases; its notes are then the commit's full message.

The [Release workflow](../../../.github/workflows/release.yml) starts on the tag push. Watch its run; its job summary names the Release, the tagged commit, the `release` commit, the installed tree, the zip digest, and the runtime digest.

Write the notes for users: what changed, its behavioral impact, and the required action, saying `None` when users need do nothing. When a release retires a feature, command, configuration, or procedure, say so and name the replacement, and remove the retired active entry points, configuration, and instructions in the same change; a notice alone does not complete a removal. Case-level results, commit and tree IDs, timing, and workflow internals belong in the pull request or its Issue.

## What CI Does

The Release workflow runs [`.ci/scripts/release.py run`](../../../.ci/scripts/release.py) on the tag. Before any write, it requires every gate that [Repository Governance](../repository-governance.md#release-workflow) lists: the tag name, the commit's place on `main` and its GitHub-made signature, the required checks, the version step, a changed runtime digest, an absent Release, a `release` branch of the expected shape, and the repository checks on the stamped tree.

The version must be the immediate patch, minor, or major successor of the highest release tag below it. That tag is GitHub Latest's unless a later attempt failed after its tag was pushed.

The runtime digest must differ from Latest's, with one exception: the bootstrap release, the one that runs while the `release` branch holds no release commit yet, may carry Latest's runtime unchanged, because until then the catalogs have no installed tree to resolve. Every other gate still applies to it, and its policy and evidence assets record `"bootstrap": true`.

It then writes, in order:

1. one commit on `release`, made with the GraphQL `createCommitOnBranch` mutation and `GITHUB_TOKEN`, so GitHub signs it. Its tree is exactly the tagged `plugin/` directory with `"version": "X.Y.Z"` inserted after `name` in both plugin manifests, plus `LICENSE`. Its parent is the previous release commit. `createCommitOnBranch` always builds on an existing branch head, so when the branch does not exist, the workflow first creates it at `main`'s root commit `fb86eb61e8161642c627bcce84c214730634b570`, whose tree holds only `LICENSE`. The branch carries no other path, because `GITHUB_TOKEN` cannot be granted the `workflows` permission and GitHub refuses a token write that creates, changes, or deletes a file under `.github/workflows/`;
2. the Draft at the tag, with the notes, the plugin zip, and the release-policy asset;
3. the [immutable publisher](../../../.github/workflows/publish-immutable-release.yml) run, which derives the same subject on its own, adds the evidence asset, and publishes the Draft as the immutable Latest Release; and
4. the `Verify release branch commit` and `Observe published immutable release` checks.

Check a stamped tree locally with `python3 -B .ci/check.py --release-version X.Y.Z`; without the option the checks validate `main`, whose manifests declare no version.

## Release Notes

The Release body is the annotated tag's message when the tag is annotated, otherwise the tagged commit's full message. A trailing PGP or SSH signature block is removed, line endings become LF, and one final line links the comparison with the previous published release, `https://github.com/wheakerd/axiom/compare/vPREV...vX.Y.Z`; the line is omitted when there is no previous release. The workflow checks only structure: the notes must be non-empty and within GitHub's 125,000-character limit.

## Release Assets And Evidence

Each Release carries three assets and GitHub's own release attestation:

- `axiom-vX.Y.Z-plugin.zip`: the stamped `plugin/` tree, members relative to the plugin root, sorted, stored without compression, with the fixed timestamp 1980-01-01 00:00 and Unix mode 0644. Equal trees give byte-identical zips; the publisher rebuilds it from the tag and compares bytes.
- `axiom-vX.Y.Z-release-policy-<sha256>.json`: the release subject and the `repository-checks-v2` policy, which names the four required checks. The subject binds the version, tag object, tagged commit and tree, `release` commit and tree, zip name, SHA-256, and size, runtime digest, previous release tag, and notes SHA-256.
- `axiom-vX.Y.Z-release-evidence-<sha256>.json`: written by the publisher after it validates the Draft. It records the tag, tagged commit, `release` commit, stamped tree, zip SHA-256, runtime digest under `runtimeContract.digest`, notes SHA-256, whether the release was the bootstrap release, and the identities of the two other assets. The next release reads the digest from here; when Latest's evidence asset records no digest, the Release workflow computes Latest's digest with the same generator on Latest's tagged tree.

Verify a published Release and a downloaded zip with GitHub's attestation:

```bash
gh release verify vX.Y.Z --repo wheakerd/axiom
gh release verify-asset vX.Y.Z axiom-vX.Y.Z-plugin.zip --repo wheakerd/axiom
```

These records describe verification policy and artifact integrity; check results remain bound to their GitHub Actions runs.

## Marketplace Distribution

The default [marketplace](../../../.agents/plugins/marketplace.json) and the [Claude Code catalog](../../../.claude-plugin/marketplace.json) select the `release` branch of the same repository through a `git-subdir` source whose `path` is the installed plugin root, `./plugin` for Codex and `plugin` for Claude Code, so hosts install only that subtree. Releases never edit the catalogs. A host sees a new version when it refreshes the marketplace; the client and user own refresh and automatic-update policy.

To install one fixed version, select the release commit by `sha` in a catalog of your own; each commit on `release` names its tag in its message.

The Codex catalog format follows the official [marketplace source specification](https://developers.openai.com/plugins/build/plugins#marketplace-metadata), whose `git-subdir` plugin source takes `url`, `path`, and `ref` or `sha`. The Claude Code catalog format follows the official [marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources), whose `git-subdir` plugin source takes `url`, `path`, `ref`, and `sha` and checks out only that subdirectory. Use each format's native fields; do not add an Axiom update channel or schedule to either plugin manifest.

## Recovery

The Release workflow has no resume path, and tags are never moved or deleted.

- **A gate fails.** Nothing was written except the tag. Fix the cause on `main` if needed, then tag the next version; the failed tag stays without a Release.
- **The workflow fails after the `release` commit.** The branch then holds that version without a Release, and hosts that refresh may install it. Tag the next version promptly; its release commit supersedes the unreleased one.
- **The publisher fails while the Draft exists.** Dispatch `Publish immutable release` on the same tag after inspecting its run. It resumes the exact Draft or performs final-only readback, and it requires the `release` head to still hold that tag's tree. If that is impossible, delete the Draft and tag the next version.
- **GitHub publishes the Release without immutability.** The publisher deletes that exact mutable Release and fails; tag the next version.

A failure, unavailable result, or unexecuted check stays as it happened and is never relabeled by a later publication.

## Fix-Forward Boundary

Do not edit an immutable Release, move or recreate its tag, replace its assets, or rewrite historical evidence. If a published body or evidence design needs correction, document the discrepancy and apply the new contract to the next version.
