# Distribution Channels

Use this page to decide where Axiom is listed, what each channel requires, and
what has actually been submitted. It records channel facts observed on the
dates given; it does not prove a current listing. Submitting to any external
channel is a separate maintainer decision and action, and nothing on this page
authorizes one.

Installed distribution stays with the two marketplace catalogs described in
[Managing an Installation](../guides/managing-installation.md); the channels
below only help people and crawlers find the repository.

## Discoverability Facts

| Surface | State | Checked |
| --- | --- | --- |
| Repository topics | Twenty topics, the GitHub maximum, covering both hosts, plugin and skill terms, and workflow terms | 2026-10-25 |
| Repository homepage | The [documentation index](../README.md) | Set 2026-10-25 |
| `SKILL.md` frontmatter | All fourteen bundled skills satisfy the [Agent Skills specification](https://agentskills.io/specification): `name` matches its directory and its character rules, `description` is 1 to 1024 characters, and no field outside the specification is used | 2026-10-25 |
| Marketplace catalogs | Both catalogs select the installed `plugin/` subtree at the immutable release tag; see [marketplace publication](release-documentation.md#marketplace-publication) | Per release |
| README links and badges | Every absolute link and badge in the README returned HTTP 200 | 2026-10-25 |

## Channels

Status values: `not submitted`, `submitted <date>`, `listed <date>`,
`declined <date>`, `blocked <reason>`, `automatic`.

| Channel | Kind | Requirements observed | Status |
| --- | --- | --- | --- |
| [Claude plugin directory](https://github.com/anthropics/claude-plugins-official) (`external_plugins`) | Official directory | Submission form `https://clau.de/plugin-directory-submission`; `plugin.json` required; external plugins "must meet quality and security standards for approval"; hooks are part of the plugin format | not submitted |
| [OpenAI plugin directory](https://developers.openai.com/codex/submit-plugins) | Official directory | ZIP upload at `https://platform.openai.com/plugins`; organization owner or Apps Management Write permission; verified individual or business identity; skills-only format omits `review` and `mcpServers`; lifecycle hooks must be stripped before a public listing | blocked: the startup Hook is part of the installed runtime; a hook-less listing variant would need its own acceptance evidence |
| [ccplugins/awesome-claude-code-plugins](https://github.com/ccplugins/awesome-claude-code-plugins) | Curated README list | Entry under a category through a pull request; the list already names an unrelated "AxiomCore", so entry text must disambiguate | not submitted |
| [hashgraph-online/awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins) | Curated README list | Entry through a pull request | not submitted |
| [RoggeOhta/awesome-codex-cli](https://github.com/RoggeOhta/awesome-codex-cli) | Curated README list | Entry through a pull request | not submitted |
| [composio-community/awesome-codex-skills](https://github.com/composio-community/awesome-codex-skills) | Curated skill list | Entry through a pull request; skill-oriented | not submitted |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | Curated skill directory | Maintainer-curated; entry through a pull request | not submitted |
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | Curated skill list | Entry through a pull request; last push observed 2026-04 | not submitted |
| [majiayu000/claude-skill-registry](https://github.com/majiayu000/claude-skill-registry) | Automated registry | Crawls GitHub; already discovers this repository | automatic (observed 2026-10-25) |

## Listing Text

The Codex manifest's `interface.shortDescription` and
`interface.longDescription` are the canonical listing texts; the README's
opening paragraph is the canonical long form. Entries for channels that list a
similarly named project add one sentence: Axiom (`wheakerd/axiom`) is unrelated
to AxiomCore. Listing text must not compare Axiom with other plugins or
mention pricing; the OpenAI guidelines reject both.

## Recording A Submission

When a submission is made, update the channel row with the status, the date,
and the pull request, form confirmation, or listing link. Keep declined and
blocked outcomes with their reasons; do not remove a row to hide an outcome.
Submission drafts are maintained privately by the maintainer.
