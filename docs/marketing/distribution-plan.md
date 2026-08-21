# Distribution Plan

Status date: 2026-08-21. Requirements below were checked against the linked
first-party platform documentation or the community directory's own repository
on that date. A prepared submission is not an authorized submission.

## Product Listing Baseline

- Public name: **Axiom for Codex & Claude Code**
- Category: **Workflow guardrails for Codex and Claude Code**
- License: MIT
- Source: <https://github.com/wheakerd/axiom>
- Codex install:

  ```bash
  codex plugin marketplace add wheakerd/axiom
  codex plugin add axiom@axiom
  ```

- Claude Code install:

  ```text
  /plugin marketplace add wheakerd/axiom
  /plugin install axiom@axiom
  /reload-plugins
  ```

- Hook review and lifecycle details: [README](../../README.md#60-second-start).
- Evidence status: public beta; package and route contracts are checked in and
  statically validated for identified trees, while fresh host and independent
  results must be reported separately.
- Primary call to action: test one routed request and one no-route control, then
  report the observed evidence.

## Prepared Listing Copy

### One line

Axiom adds safety-first workflow guardrails to high-impact Codex and Claude Code
actions without intercepting ordinary coding requests.

### Short

Axiom is a safety-first workflow router for Codex and Claude Code. It makes
scope, authorization, evidence, and rollback explicit for high-impact agent
actions.

### Medium

Axiom routes focused workflows for high-impact Codex and Claude Code actions:
repository instruction audits, confirmed external actions, traceable Git
publication, and reversible persistent changes. Selecting a route never grants
mutation authority, and ordinary coding requests continue normally.

### Long

Axiom is a public-beta workflow router for developers and maintainers using
Codex or Claude Code. A small, inspectable session hook loads a shared routing
gate, which selects a focused Skill only when a request clearly needs explicit
scope, action authority, evidence, or rollback. Routes cover repository
instruction architecture, Codex usage optimization, read-only task review,
consequential external actions, traceable Git submission, and reversible
persistent system changes. Axiom is not a sandbox, does not grant credentials
or mutation authority, does not install a daemon, and collects no telemetry.
Users are asked to inspect the installed hook, run one routed request and one
no-route control, and report the result.

### Technical

Axiom packages seven shared Agent Skills behind platform-specific Codex and
Claude Code manifests and `SessionStart` hooks. The foreground hook reads a
checked-in Markdown routing gate; it contains no network, write, updater, or
background-service command. Static validators cover package drift, manifest
shape, links, route fixtures, authorization boundaries, and publication guards.
Those checks do not substitute for a named fresh-session host observation.

### Public beta

Axiom is in public beta. Checked-in integration contracts and static fixtures
are available for review; coverage across host versions, operating systems,
policies, shells, and installation paths remains evidence-bounded. Independent
compatibility reports and hostile routing cases are more useful than unverified
endorsements.

### Category, tags, and compatibility

- Preferred category: Developer Tools; use Productivity only when a directory
  lacks a developer-tools category.
- Tags: `codex`, `claude-code`, `ai-coding-agent`, `agent-safety`,
  `workflow-guardrails`, `approval-gates`, `agent-skills`, `agents-md`,
  `git-workflow`, `rollback`, `auditability`, `developer-tools`.
- Compatibility statement: checked-in wrappers target Codex and Claude Code;
  current compatibility depends on the identified host version and installed
  snapshot. See [Compatibility](../compatibility.md) and
  [Field Validation](../field-validation.md).

## Channel Readiness

| Channel | Audience | Status | Submission mechanism | Readiness | Authorization |
| --- | --- | --- | --- | --- | --- |
| OpenAI universal Plugins Directory | ChatGPT and Codex plugin users | Official; current submission portal documented | OpenAI Platform plugin submission draft, review, then separate developer publication | `NOT-READY` | Exact approval for portal submission; later separate approval to publish |
| Anthropic `claude-community` marketplace | Claude Code users | Official community marketplace; catalog syncs from reviewed submissions | Claude Console form for individual authors or claude.ai form for eligible organizations | `READY-AFTER-VALIDATION` | Exact approval to submit the form |
| `ccplugins/awesome-claude-code-plugins` | Claude Code plugin discoverers | Active community list; repository accepted PRs on the status date | Fork, add one entry to the canonical category, open one PR | `READY-AFTER-PUBLIC-BRANCH` | Exact approval to fork/push/open the external PR |
| OpenAI Developer Showcase | OpenAI and Codex builders | Official showcase exists; current public page does not expose a verifiable submission form | Submission path `NOT-VERIFIED`; community page links to the showcase | `NOT-VERIFIED` | Approval only after actor, form, payload, and visibility are re-verified |
| OpenAI Developer Forum, Codex category | Codex users and plugin builders | Public community forum on an OpenAI domain; active Codex project topics observed | Create one authenticated topic in the Codex category with project tags | `DRAFT-READY` | Exact approval for the account, topic, category, tags, and one post |
| GitHub repository discovery | Developers searching GitHub | Official repository settings | Repository API for description/topics; Settings UI for social preview and Discussions | Assets ready; settings unchanged | Separate approval for each settings mutation |
| Technical communities | Maintainers, DevEx, DevSecOps, release engineers | Community-specific | Platform-specific posts from the launch kit | Draft ready | Separate approval per platform and post |

## 1. OpenAI Universal Plugins Directory

The [official submission guide](https://developers.openai.com/plugins/deploy/submission)
requires plugin-submission write access, a verified developer or business
identity, listing details, a logo, category, website, support/privacy/terms
URLs, final Skills, starter prompts, five positive and three negative test
cases, availability, release notes, and policy attestations. Submission begins
review; an approved plugin is published only through a later developer action.

The [Claude-plugin conversion guide](https://developers.openai.com/plugins/guides/submit-claude-plugin)
states that ChatGPT does not run plugin hooks and that a plugin must not require
hooks for its core ChatGPT workflow. Axiom's current routing gate is loaded by a
session hook. Removing that dependency would be a product change, not a
marketing edit. Axiom is therefore not ready for an honest universal-directory
submission. Privacy and terms URLs are also not checked in.

- Required assets: final Skill bundle, non-logo-imitating product mark, listing
  copy, website, support/privacy/terms URLs, starter prompts, test cases, region
  selection, and release notes.
- Maintainer expectation: automated scans and human review; approval does not
  publish automatically.
- Exact next action: decide whether to build a useful hook-independent ChatGPT
  workflow. If yes, implement and validate it before preparing a portal draft.
- Verification after a later publication: locate the exact publisher and
  version in the universal directory and run directory-installed test cases.

## 2. Anthropic Community Marketplace

Anthropic's [current plugin guide](https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-community-marketplace)
documents the `claude-community` marketplace for third-party submissions. An
individual author can use <https://platform.claude.com/plugins/submit>; eligible
Team or Enterprise organizations can use the claude.ai directory form. The
review pipeline runs plugin validation and automated safety screening, approved
entries are pinned to a commit SHA, and the public catalog syncs on a schedule.
The separately curated official marketplace has no application process.

- Required assets: public repository, valid plugin and marketplace manifests,
  concise description, install guidance, source/license links, and a reachable
  immutable commit after publication of the candidate branch.
- Local prerequisite:

  ```bash
  claude plugin validate --strict .
  claude plugin validate --strict .claude-plugin/marketplace.json
  ```

- Exact next action after approval: submit one Console form for Axiom using the
  medium copy, source URL, MIT license, and validated commit.
- Verification: find `axiom` in the
  [community catalog](https://github.com/anthropics/claude-plugins-community),
  confirm its pinned commit, install `axiom@claude-community`, inspect `/hooks`,
  then run the field protocol.

## 3. Canonical Community Directory

The selected target is
[`ccplugins/awesome-claude-code-plugins`](https://github.com/ccplugins/awesome-claude-code-plugins).
Its own README invites plugin and marketplace contributions. On 2026-08-21 the
repository was active and had current submission PRs; no separate
`CONTRIBUTING.md` was present. This target is preferred over smaller duplicate
Codex lists because it has a maintained taxonomy and active review queue.

- Proposed category: Workflow Orchestration.
- Proposed entry:

  ```markdown
  - [Axiom](https://github.com/wheakerd/axiom) - Public-beta workflow guardrails for Codex and Claude Code that make scope, authorization, evidence, and rollback explicit for high-impact agent actions.
  ```

- Exact next action after approval: fork the repository, add only this entry in
  the existing alphabetical or local category style, run its documented checks
  if any are added before submission, and open one PR.
- Maintainer expectation: relevance, clear description, no duplicate entry,
  and readable placement based on the repository's own README.
- Verification: confirm the merged default-branch entry and link target. An open
  PR is not a completed listing.

## 4. OpenAI Developer Showcase

The official [community page](https://developers.openai.com/community) links
"Share what you built" to the
[OpenAI Developer Showcase](https://developers.openai.com/showcase). On the
status date, the public showcase page displayed projects but did not expose a
verifiable submission form in the accessible page content. Do not infer a
working submission mechanism from the call-to-action wording.

- Readiness: `NOT-VERIFIED`.
- Exact next action: re-open the official community page in an authenticated
  browser, resolve the actor and visible form, and record all required fields
  without submitting.
- Verification after a later submission: require a public project page owned by
  the showcase, not merely a form success message.

## 5. OpenAI Developer Forum Codex Category

The public
[Codex category](https://community.openai.com/c/codex/37) was active on the
status date and included project posts using `community-project` and
`built-with-codex` tags. The forum is a public community venue; a topic does not
imply OpenAI endorsement or create a private support case.

- Target: one new topic in category `Codex` (`/c/codex/37`).
- Proposed tags: `community-project`, `built-with-codex`, and `plugin-development`
  only if the composer still offers them to the posting account.
- Payload: the Codex Community Show And Tell title and body in
  [Launch Kit](launch-kit.md).
- Exact next action: recheck category guidance and available tags while signed
  in, freeze the preview, then create one topic after authorization.
- Verification: read the public topic URL, category, tags, title, body, and link
  from a logged-out session. Do not retry after an uncertain submit until the
  account's topic history is checked.

## 6. GitHub Discovery

GitHub permits up to 20 repository topics using lowercase letters, numbers, and
hyphens; each candidate below is within the documented limit. See GitHub's
[topic guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).

Prepared description:

> Safety-first workflow routing for Codex and Claude Code: explicit scope,
> authorization, evidence, and rollback for high-impact agent actions.

Prepared topic replacement, exactly 12 topics:

```text
codex
claude-code
ai-coding-agent
agent-safety
workflow-guardrails
approval-gates
agent-skills
agents-md
git-workflow
rollback
auditability
developer-tools
```

Exact operations, prepared only:

```bash
gh api --method PATCH repos/wheakerd/axiom \
  -f 'description=Safety-first workflow routing for Codex and Claude Code: explicit scope, authorization, evidence, and rollback for high-impact agent actions.'

gh api --method PUT repos/wheakerd/axiom/topics \
  -f 'names[]=codex' \
  -f 'names[]=claude-code' \
  -f 'names[]=ai-coding-agent' \
  -f 'names[]=agent-safety' \
  -f 'names[]=workflow-guardrails' \
  -f 'names[]=approval-gates' \
  -f 'names[]=agent-skills' \
  -f 'names[]=agents-md' \
  -f 'names[]=git-workflow' \
  -f 'names[]=rollback' \
  -f 'names[]=auditability' \
  -f 'names[]=developer-tools'
```

The topics operation replaces the full set. Re-read the current topic list
immediately before any authorized call and stop if the intended replacement is
no longer exact. Verify with `gh api repos/wheakerd/axiom --jq .description` and
`gh api repos/wheakerd/axiom/topics --jq .names`.

The 1280 x 640 PNG in `docs/assets/` is prepared for GitHub's
[social preview setting](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview).
The upload is a separate Settings action. Discussions and private vulnerability
reporting are also separate mutations.

### Social preview reproduction

- Editable source: `docs/assets/social-preview.svg`.
- Upload artifact: `docs/assets/social-preview.png`.
- Dimensions: 1280 x 640; static RGBA PNG; no third-party imagery or logos.
- Typeface request: Noto Sans with DejaVu Sans and generic sans-serif fallbacks;
  no font file is bundled.
- Render command used for the prepared artifact:

  ```bash
  magick -density 144 docs/assets/social-preview.svg \
    -resize '1280x640!' -strip PNG32:docs/assets/social-preview.png
  ```

The prepared render was visually reviewed at card size. Text-to-background
contrast ranged from 6.92:1 to 16.96:1 for the three text colors. Re-rendering
on a host without the requested fonts can change text metrics; inspect the PNG
before upload. In GitHub Settings, open the Social preview editor, upload the
PNG once, save, then verify a newly generated external share preview. Do not
treat the local file as proof that the repository setting changed.

## 7. Technical Communities

Use [Launch Kit](launch-kit.md) for platform-specific drafts. Before any post,
recheck the platform's current submission rules, bind the posting account and
community, and confirm whether edits or deletion are possible. Publish no more
than one initial post per approved channel. The primary conversion event is a
sanitized validation or routing report, not a Star.

## Submission Gate

No channel should move from prepared to submitted until:

1. task changes are based on the current remote default branch and publicly
   reachable at an immutable commit;
2. repository validators and strict Claude validation pass on that exact tree;
3. the installed hook and fresh-session protocol have at least one named Codex
   and one named Claude Code observation, or the listing clearly says they are
   not verified;
4. every listing uses the same bounded public-beta claims;
5. the actor, target, payload, public visibility, credential surface, count,
   retry boundary, verification source, correction path, and uncertainties are
   explicitly authorized for that one action.
