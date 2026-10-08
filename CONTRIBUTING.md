# Contributing to Axiom

Thanks for helping improve Axiom. Keep changes narrow, evidence-based, and easy
to review. A route may help an agent decide how to work, but it must never
silently broaden what the user authorized.

## Repository layout

| Path | Ownership |
| --- | --- |
| `skills/` | Skill source installed by Codex |
| `.codex-plugin/plugin.json` | Codex plugin manifest |
| `.agents/plugins/marketplace.json` | Codex marketplace wrapper |
| `hooks/codex-hooks.json` | Codex-specific startup hook |
| `README.md` | Product landing page and safe-start entry point |
| `docs/README.md` and `docs/` | Task navigation, user guidance, concepts, references, and maintainer policy |
| `evidence/` | Current identity and status, append-only policy ledger, compatibility schemas, and version-bound runtime digest histories |
| `evals/` | Versioned routing contracts, their historical index, context budgets, and separately labeled host observations |
| `axiom_validation/` | Standard-library publication policy modules and versioned installed-runtime input classification |
| `tests/` | Focused unit tests and isolated policy fixtures; not installed runtime behavior |
| `scripts/` and `.github/workflows/` | Stable validation entrypoints and CI wiring; not installed runtime behavior |

The direct children of `skills/` that contain a `SKILL.md` are Axiom's public
routes. A route may own supporting `references/` and `agents/` resources, but
those resources are not independent public routes. Do not create a
platform-specific copy of a shared skill.

## Before making a change

1. Inspect the worktree and preserve edits you did not create. Do not reset,
   stash, clean, stage, or rewrite unrelated work to make your change appear
   clean.
2. Identify whether the change affects Skills, the Codex wrapper, or repository
   tooling. Review installed behavior in Codex when the runtime changes.
3. Classify the change against
   [`docs/runtime-identity.md`](docs/runtime-identity.md). An included runtime
   change must alter the digest and advance `pluginVersion`; a repository-only
   change appends `repositoryPolicyRevision` and must retain the digest.
4. Separate route selection from action authorization. Loading a skill never
   grants permission to commit, push, deploy, delete, promote, read a secret,
   or mutate a remote system.
5. Keep the change within its stated scope. Call out any routing or
   authorization impact explicitly in the pull request.

## Shared routing invariants

- `using-axiom` remains the startup routing gate. It honors higher-priority
  instructions, selects the smallest clearly matching route, and continues
  normally when no Axiom route applies.
- Do not turn Axiom into a catch-all for ordinary coding, documentation, Git,
  or status requests.
- Route `optimize-codex-usage` only from an explicit Codex credit, token,
  context, Skill/AGENTS/MCP-loading, or consumption-diagnosis goal. Do not use
  software performance wording alone as a trigger.
- Keep route definitions and triggers in English. Unambiguous requests in
  other languages may normalize to the canonical English route.
- Keep the Codex manifest pointed at `./skills/` and bind its version to the
  current runtime identity.
- Use `Axiom` for the brand in prose and `axiom` for plugin, marketplace,
  route, path, and command identifiers.
- Preserve existing user work and treat missing evidence, tooling, or access as
  unverified rather than as a passing result.
- Keep volatile model prices, plan limits, and quotas out of always-loaded
  instructions. Label byte/word/call measurements as proxies unless the host
  exposes exact scoped usage, and never auto-change the main model or reasoning
  settings. Child model selection belongs to `delegate-simple-task`: use the
  user's ordered candidates and current host support, disclose the exact model
  and task, and retain the Full Access and assignment-authority boundaries.

Compare always-loaded routing growth cumulatively with the immutable baseline
in `evals/context-budget/`. An increase of at least 256 UTF-8 bytes or 5%
requires review and a substantive justification; this is a review trigger, not
a quality pass/fail shortcut. Any reduction experiment must use the same fixed
routing workload before and after and report both routed and no-route results
as passing. Do not remove a safety, authorization, stop, or evidence rule merely
to meet a size target.

Keep the always-loaded gate at least 15% below the 8,192-byte instruction
boundary after equivalent routing and safety acceptance, with roughly 6-6.5
KiB preferred when precision permits. Treat 8,192 bytes as a rejection guard,
not an authoring target. Bind reduction evidence to the immediate predecessor
while retaining v0.7.9 as the cumulative growth baseline.

When editing a route, review its direct references and examples for accidental
permission expansion. State separately whether the change affects matching,
planning, mutation authority, stop conditions, rollback, or completion
evidence.

## Documentation policy

Use the public [Documentation Policy](docs/maintainers/documentation-policy.md)
to classify documents, select one canonical owner for each fact, apply
lifecycle states, and update navigation. The [documentation index](docs/README.md)
is the task- and audience-oriented entry point.

Keep public documentation in English and tie claims to checked-in behavior or
clearly identified historical evidence. Preserve the parseable README
`### Shared skills` inventory, keep current Hook renderings synchronized with
the checked-in declarations and wrappers, and do not claim a proposed location
is current before its content and links move. Use repository-relative links and
run the applicable documentation, publication, and unit checks before opening a
pull request.

## Hook changes need extra review

Codex declares `./hooks/codex-hooks.json` and reads
`skills/using-axiom/SKILL.md` through `SessionStart`, including `compact`.
Keep the conventional `hooks/hooks.json` absent.

Review any hook change command by command. A hook must remain foreground-only,
locally inspectable, and limited to loading the routing gate. Do not add file
writes, network calls, credential access, a daemon, watcher, scheduled task, or
automatic update behavior. Update the relevant manifest and public trust
documentation whenever a declared hook path or command changes.

## Required local checks

Run checks from the repository root and record the exact commands and outcomes:

```bash
python3 -B scripts/check-publication.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

The aggregate owns distribution agreement, runtime identity, compatibility
evidence, routing context, documentation, and publication checks. Use focused
scripts to diagnose a failing domain; a passing aggregate does not require
repeating those checks. Run any additional checks required by the changed
surface, read the final diff, confirm the manifest version matches the release
identity, and inspect `git status --short` for unrelated paths.

Hook or hook-workflow changes also require the dedicated native integration
module on every available target host:

```bash
python -B -m unittest tests.hook_runtime_integration -v
```

Use the host's equivalent Python 3 launcher when it has a different name. Run
the module from a disposable repository copy. A Linux result proves only
Linux; report unavailable native Windows or macOS execution as `NOT-RUN`. The
three native matrix checks remain directly visible for diagnosis. After the
completed stability-observation period, their stable `hook-runtime-gate`
aggregate is a required `main` check alongside `repository-guards` and
`unit-and-integration-tests`. A failed or incomplete native matrix blocks the
normal merge path for both same-repository and fork pull requests. The weekly
scheduled run remains read-only compatibility evidence.

`scripts/check-publication.py` is the stable aggregate entrypoint. Production
parsers and policy gates live in `axiom_validation/`; deterministic mutation
and event fixtures live in `tests/fixtures/`; focused `unittest` modules own
domain-local assertions. Keep fixture names in failure messages, and let the
aggregate reporter add the policy domain. Do not move fixture payloads back
into production modules or add a third-party test/runtime dependency.

The aggregate summary's `immutable external action and image pins` total adds
one for each validated full-SHA GitHub Action, digest-pinned `docker://` action,
workflow job or service image, and digest-pinned remote Dockerfile source. Its
parenthetical breakdown reports remote `FROM` sources as `Dockerfile base-image
pins` and digest-pinned `COPY --from` or `RUN --mount=from` sources as `other
Dockerfile input pins`. `FROM scratch`, references to an already validated
local build stage, and validated action-local `COPY` or `ADD` sources are
accepted but do not increase either Dockerfile count.

The v0.7.4 host snapshots and frozen no-Hook experiment are retained in the
[verified Git archive](docs/field-validation.md#archived-experiments). Their
commands, tests, and source downloads are retired from current publication.
The compatibility validator uses `tests/fixtures/compatibility-v3.json` for
synthetic schema regression; no fixture is reported as a host observation.

Historical compatibility records retain their original schema: v1 supplies the
shared definitions, v2 binds runtime schema v1, and v3 supports runtime schemas
v1 and v2. New current observations use `evidence/schema-v3.json`, bind to an
already existing immutable tag and commit, include the exact plugin version and
runtime digest, preserve every not-run or unavailable case, and contain only
minimal sanitized output. The [evidence inventory](docs/field-validation.md#evidence-directory)
explains these distinct versions and the offline validator's limits. A prior observation may be referenced for an identical
runtime digest, but never relabeled as evidence of a new host, lifecycle,
version, or date. The checked-in current release status stays `STATIC-ONLY`;
use the validator's post-tag `--record` mode for a same-release asset after the
immutable tag and commit exist.

Host-native validation is valuable but optional because the relevant CLI may
not be installed. Inspect the installed CLI's help before choosing a command;
do not assume a `codex plugin validate` subcommand exists. If a validator is
available, run it against a disposable copy when it may write files. A bounded
app-server `plugin/read` can additionally check local package discovery, but
is not a strict schema validator or an installed-session test. Report its
exact host version and only the components actually returned.

The repository aggregate owns Axiom's strict package checks. The obsolete
`plugin-creator` allowlist validator is retired from the active workflow,
including optional diagnostics and fallbacks. Follow the
[v0.13.0 retirement and migration notice](docs/releases/v0.13.0.md#retired-validator).
Current checks follow the supported
[Codex package contract](docs/compatibility.md#codex-package-format-and-validation).
A missing tool is `unavailable`, not `passed`; do not install, update, or patch
system tooling merely to satisfy a contribution check.

## Routing evaluation contracts

The JSONL records under `evals/routing/` are public behavior contracts, not
prompt suggestions. Keep case IDs stable. If a request, expected route,
forbidden route, clarification count, lifecycle precondition, or risk class
changes, increment that record's `contractVersion` and explain the contract
change in the pull request. Do not edit an expectation after a host failure to
make the result pass. Create a new benchmark manifest ID when the ordered live
case set changes.

Static validation and host observation are separate evidence levels. The
publication validator checks schema, coverage, benchmark membership, privacy,
and result arithmetic without invoking a model. A host result must identify a
stable run ID, the applied response-schema path and SHA-256, an immutable Axiom
tag, commit, and tree, plus the exact host, model, operating system, lifecycle,
repeat count, route evidence, clarification count, mutation attempt state, and
`pass`, `fail`, `unavailable`, or `not-run` status. An unavailable host that made
no call uses a null response-schema binding.

Evaluation requests grant no mutation authority. Run live cases only in fresh
disposable workspaces with one isolated installed-plugin session per case, a
read-only sandbox, approvals disabled, no web or external-service tools, and
the reviewed output schema. Do not upload private conversations or credentials.
Keep that model-facing schema within OpenAI's documented Structured Outputs
subset; enforce omitted uniqueness, string-length, privacy, and semantic checks
in the deterministic standard-library validator and its negative fixtures.
The first failure or unknown outcome stops the remaining batch without retry.
Preserve that case's known and null fields honestly, then mark every later case
`not-run` with the stop reason. Historical Claude Code records retain their
original outcomes; current Axiom installation support is Codex-only. Offline
validation is a separate static signal.

Host run records are append-only. A recovery batch receives a new run ID and a
new result file; it never replaces the original failure. Do not create that file
from a passing prefix: keep partial success private until all cases pass or the
first failure makes the batch terminal. At repeat count one, a terminal failure
contains only a pass prefix, one first failure, and a `not-run` suffix.

See [Routing Evaluations](evals/README.md) for the fixed corpus and bounded host
method.

## Runtime boundary

Axiom installs Markdown skills and foreground hook definitions. It has no
installed daemon, background updater, network update check, or bundled runtime
dependency. Repository validation may use a host-provided interpreter in CI,
but that check must not become a dependency of the installed plugin. Prefer
focused, standard-library-only validation when adding repository checks.

## Pull-request validation and release provenance

Release documentation and evidence have separate canonical owners. Read
[`docs/maintainers/release-documentation.md`](docs/maintainers/release-documentation.md)
before preparing a version. For a future tag that contains this policy, render
the exact draft Release body from its Changelog entry with:

```bash
python3 scripts/check-release-evidence.py render-body --expected-version X.Y.Z
```

This command is offline and writes only to standard output. It does not create
a tag, draft, Release, asset, or Latest transition. The separately authorized
draft must use the exact rendered bytes; publication validation compares those
bytes again at the tag commit.

`Distribution and publication guards` runs for pull requests targeting `main`,
including same-repository and fork pull requests. It validates the proposed
merge tree with repository-local distribution and publication checks. The
workflow uses `pull_request`, grants only `contents: read`, references no
repository secret, and checks out with `persist-credentials: false`. GitHub may
still require maintainer approval before a first-time fork contributor's run.

These checks do not require the contributor head commit to be GitHub-signed or
hosted in `wheakerd/axiom`. Passing them proves only that the proposed merge
tree satisfies the checked-in static policy. It does not establish release
provenance and does not authorize publication.

`Release signature guard` starts after protected history or release state
changes. Its stable check names distinguish signed `main` history, a manual
`release/v<version>` candidate, a newly created `v<version>` tag, and a
published immutable Release. A candidate or tag version must match the Codex
manifest. Every target must remain on approved `main` history and carry a
valid signature made with GitHub's signing key. Candidate evidence never
authorizes tag creation.

`Create protected release tag` is the only checked-in normal creation path. It
runs manually on current `main`, uses the dedicated release GitHub App only
inside the `release-tag-creation` environment, validates live rulesets and
exact commit evidence twice, attempts one `POST /git/refs`, and reads the ref
back. Pull-request code receives neither the private key nor the App token.
Repository code cannot configure the App or ruleset bypass: until a live
authenticated read-back matches the documented migration target, the
controller must reject before mutation. GitHub rulesets remain the server-side
prevention layer for unsigned `main` updates and tag creation, movement, or
deletion.

## Pull requests

Keep a pull request focused and include:

- The intended outcome and exact affected files.
- Which files are shared and which are Codex-specific.
- Any route-selection or action-authorization impact, including an explicit
  `none` when there is no impact.
- Documentation changes or a reason none are needed.
- Every validation command and its exact result, including unavailable optional
  host checks.
- A Codex behavior review when Skills or packaging changes.
- Confirmation that unrelated work was not reset, hidden, staged, or rewritten.

Do not mix opportunistic cleanup with the requested change. Do not commit
generated caches, disposable validation copies, local maintenance notes, or
tool output.
