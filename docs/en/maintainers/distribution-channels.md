# Distribution Channels

Use this page to decide where Axiom is listed, what each channel requires, and what has actually been submitted. It records channel facts observed on the dates given; it does not prove a current listing. Submitting to any external channel is a separate maintainer decision and action, and nothing on this page authorizes one.

Installed distribution stays with the two marketplace catalogs described in [Managing an Installation](../guides/managing-installation.md); the channels below help people and crawlers find the repository, and some of them would also distribute an accepted package.

## Discoverability Facts

| Surface | State |
| --- | --- |
| Repository topics | Twenty topics, the GitHub maximum, covering both hosts, plugin and skill terms, and workflow terms |
| Repository homepage | The [documentation index](../README.md) |
| `SKILL.md` frontmatter | Every bundled skill satisfies the [Agent Skills specification](https://agentskills.io/specification): `name` matches its directory and its character rules, `description` is 1 to 1024 characters, and no field outside the specification is used |
| Marketplace catalogs | Both catalogs select the installed `plugin/` subtree of the `release` branch; see [marketplace distribution](release-documentation.md#marketplace-distribution) |

## Channels

Status values: `not submitted`, `submitted <date>`, `listed <date>`, `declined <date>`, `blocked <reason>`, `automatic`.

| Channel | Kind | Requirements observed | Observed (UTC) | Status |
| --- | --- | --- | --- | --- |
| [Claude plugin directory](https://claude.com/docs/directory/publish) | Official directory | Submission through the developer portal `https://claude.ai/directory/manage`; `https://clau.de/plugin-directory-submission` redirects to the publishing guide, which says every plugin version gets automated validation and a security scan and a person reviews a new listing; its checklist requires `.claude-plugin/plugin.json`, except in a skills-only folder, and a README of at least 40 words in the plugin folder, which the released `plugin/` folder does not have; a plugin folder may hold hooks; the [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official) README says pull requests there are not monitored and its catalog is being reduced to Anthropic's own plugins | 2026-11-23 | not submitted |
| [OpenAI plugin directory](https://developers.openai.com/plugins/deploy/submission) | Official directory | ZIP upload at `https://platform.openai.com/plugins`; organization owner or Apps Management Write permission; verified individual or business identity; skills-only format omits `review` and `mcpServers`; lifecycle hooks must be stripped before a public listing | 2026-11-23 | not submitted |
| [ccplugins/awesome-claude-code-plugins](https://github.com/ccplugins/awesome-claude-code-plugins) | Curated README list | Entry under a category through a pull request; the list already names an unrelated "AxiomCore", so entry text must disambiguate | 2026-11-23 | not submitted |
| [hashgraph-online/awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins) | Curated list and plugin marketplace | Entry through a pull request that adds one line to the README; the catalog's own plugin scanner must score the plugin at least 75 of 100 for admission; on acceptance a generator mirrors the plugin bundle from its source repository and regenerates the catalog's marketplace files | 2026-11-23 | not submitted |
| [RoggeOhta/awesome-codex-cli](https://github.com/RoggeOhta/awesome-codex-cli) | Curated README list | Entry through an Issue that suggests the resource, or through a pull request that edits the README with a one-sentence description and a GitHub stars badge | 2026-11-23 | not submitted |
| [composio-community/awesome-codex-skills](https://github.com/composio-community/awesome-codex-skills) | Curated skill list | Entry through a pull request; skill-oriented | 2026-11-23 | not submitted |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | Curated skill directory | Maintainer-curated; entry through a pull request; a skill must show real community usage, and newly created skills are not accepted | 2026-11-23 | not submitted |
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | Curated skill list | Entry through a pull request; the guide closes the submission of a skill with fewer than 10 GitHub stars automatically and does not accept a pull request explicitly generated or submitted with AI assistance | 2026-11-23 | not submitted |
| [majiayu000/claude-skill-registry](https://github.com/majiayu000/claude-skill-registry) | Automated registry | Crawls GitHub; its [repository inventory](https://github.com/majiayu000/claude-skill-registry/blob/main/sources/learning/full-discovery-progress.json) includes `wheakerd/axiom` without a submission; a skill can also be proposed through an Issue or a pull request in `majiayu000/claude-skill-registry-core` | 2026-11-23 | automatic |

## Listing Text

The Codex manifest's `interface.shortDescription` and `interface.longDescription` are the canonical listing texts; the README's opening paragraph is the canonical long form. Entries for channels that list a similarly named project add one sentence: Axiom (`wheakerd/axiom`) is unrelated to AxiomCore. Listing text must not compare Axiom with other plugins or mention pricing; the OpenAI guidelines reject both.

## Codex Directory Listing Variant

The OpenAI plugin directory does not accept lifecycle hooks, while the marketplace package keeps Axiom's `SessionStart` and `UserPromptSubmit` Hooks. `.ci/scripts/build-listing-variant.py` derives a hook-less variant from the `plugin/` tree of one tree-ish whose manifests carry a version: the `release` branch, or the release commit of the version to be listed. For a published version, the same tree is in that Release's `axiom-vX.Y.Z-plugin.zip`.

```bash
python3 -B .ci/scripts/build-listing-variant.py --tree-ish origin/release --output /path/to/axiom-variant
```

The build keeps `.codex-plugin/plugin.json` with every field except `hooks`, copies `skills/`, `assets/`, and `LICENSE` byte for byte, and excludes `hooks/` and `.claude-plugin/` because the directory lists Codex plugins only. It writes `axiom-<version>-codex-directory-variant.zip` (stored entries in sorted order with fixed timestamps) and a JSON build manifest that names the source commit, the `plugin/` tree, the plugin version, every file digest, the removed paths and fields, and the archive digest. Two clean builds of the same tree are byte-identical; `.ci/tests/test_listing_variant.py` proves the exclusions and the determinism.

Boundaries:

- The variant is a derived distribution artifact identified by its source commit and archive digest. It is not an Axiom installed-runtime identity: the [runtime identity](../runtime-identity.md) binds versions to the marketplace `plugin/` tree, and the variant's manifest version only names its source.
- Without the startup Hook nothing loads the routing gate at session start. Route selection relies on each skill's description, and `using-axiom` with its cross-route rules loads only on explicit invocation. Observations of the marketplace package do not transfer to the variant.
- Before a submission decision, observe the variant in a fresh Codex session installed from a local marketplace without the hook: routed requests select their skills from descriptions, near-miss requests stay unselected, and no-route requests continue normally. Record that observation's UTC date and the Codex version in the OpenAI row, apart from the date in its `Observed (UTC)` cell.
- Building the variant installs and publishes nothing. Submission remains a separate maintainer action recorded under [Recording A Submission](#recording-a-submission).

## Recording A Submission

When a submission is made, update the channel row's status with its UTC date and add the pull request, form confirmation, or listing link; the `Observed (UTC)` cell keeps the date the channel's requirements were last read. Keep declined and blocked outcomes with their reasons; do not remove a row to hide an outcome. Submission drafts are maintained privately by the maintainer.
