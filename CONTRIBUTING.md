# Contributing to Axiom

Thanks for helping improve Axiom. Keep changes narrow, evidence-based, and easy
to review. A route may help an agent decide how to work, but it must never
silently broaden what the user authorized.

## Repository layout

| Path | Ownership |
| --- | --- |
| `skills/` | Shared skill source installed by both hosts |
| `.codex-plugin/plugin.json` | Codex plugin manifest |
| `.agents/plugins/marketplace.json` | Codex marketplace wrapper |
| `.claude-plugin/plugin.json` | Claude Code plugin manifest |
| `.claude-plugin/marketplace.json` | Claude Code marketplace wrapper |
| `hooks/codex-hooks.json` | Codex-specific startup hook |
| `hooks/claude-hooks.json` | Claude Code-specific session and compaction hooks |
| `README.md` and `docs/` | Public onboarding, behavior, trust, and release documentation |
| `evidence/` | Version-bound, privacy-safe host records and current release status |
| `evals/` | Versioned black-box routing contracts and separately labeled host observations |
| `evals/context-budget/` | Versioned always-loaded routing proxies, lifecycle slots, and reduction evidence |
| `axiom_validation/` | Standard-library publication policy modules; not installed runtime behavior |
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
2. Identify whether the change affects shared skills, one platform wrapper, or
   both. A shared behavior change normally needs a parity review in Codex and
   Claude Code.
3. Separate route selection from action authorization. Loading a skill never
   grants permission to commit, push, deploy, delete, promote, read a secret,
   or mutate a remote system.
4. Keep the change within its stated scope. Call out any routing or
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
- Keep the two manifests pointed at the same `./skills/` directory and keep
  their versions synchronized.
- Use `Axiom` for the brand in prose and `axiom` for plugin, marketplace,
  route, path, and command identifiers.
- Preserve existing user work and treat missing evidence, tooling, or access as
  unverified rather than as a passing result.
- Keep volatile model prices, plan limits, and quotas out of always-loaded
  instructions. Label byte/word/call measurements as proxies unless the host
  exposes exact scoped usage, and never auto-change model or reasoning settings.

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

## Documentation consistency

- Keep public documentation in English and tie claims to checked-in behavior
  or clearly identified historical evidence.
- Preserve the `### Shared skills` heading and its parseable backtick list in
  `README.md`; the distribution drift guard reads that section.
- Keep installation and update commands aligned with the current host wrappers.
- Keep hook commands in the README synchronized exactly with the checked-in
  hook JSON. If an installed definition differs, documentation must tell users
  to stop and review it rather than trust it automatically.
- Update `CHANGELOG.md` from tags and commits. Do not infer a GitHub Release,
  release date, security fix, or breaking change from a version number alone.
- Use repository-relative links for checked-in documentation and run the link
  validation before opening a pull request.

## Hook changes need extra review

Platform hooks are deliberately separate. Codex declares
`./hooks/codex-hooks.json`; Claude Code declares
`./hooks/claude-hooks.json`. Both read the shared
`skills/using-axiom/SKILL.md` through `SessionStart`, including the `compact`
source after host compaction. Keep the conventional `hooks/hooks.json` absent
so one host does not auto-discover the other host's wrapper.

Do not add a Claude Code `PreCompact` context-loading handler. Ordinary
successful stdout from that event is not injected into model context;
post-compaction routing belongs to `SessionStart` with the `compact` matcher.

Review any hook change command by command. A hook must remain foreground-only,
locally inspectable, and limited to loading the routing gate. Do not add file
writes, network calls, credential access, a daemon, watcher, scheduled task, or
automatic update behavior. Update the relevant manifest and public trust
documentation whenever a declared hook path or command changes.

## Required local checks

Run checks from the repository root and record the exact commands and outcomes:

```bash
python3 scripts/check-distribution-drift.py
python3 scripts/check-compatibility-evidence.py --self-test
python3 scripts/measure-routing-context.py --check
python3 scripts/check-publication.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m unittest tests.test_routing_evals -v
git diff --check
```

Also run targeted checks required by the files you changed. Read the final
diff, confirm both manifest versions still match, and inspect
`git status --short` for unrelated paths.

Hook or hook-workflow changes also require the dedicated native integration
module on every available target host:

```bash
python -B -m unittest tests.hook_runtime_integration -v
```

Use the host's equivalent Python 3 launcher when it has a different name. Run
the module from a disposable repository copy. A Linux result proves only
Linux; report unavailable native Windows or macOS execution as `NOT-RUN`. The
three native matrix checks are intentionally non-required during their initial
stability-observation period, so a runner-specific failure does not immediately
block an external contributor's branch or fork.

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

Compatibility records must validate against `evidence/schema-v1.json`, bind to
an already existing immutable tag and commit, preserve every not-run or
unavailable case, and contain only minimal sanitized output. Never carry an old
record forward as evidence for a newer release. The checked-in current release
status stays `STATIC-ONLY`; use the validator's post-tag `--record` mode for a
same-release asset after the immutable tag and commit exist.

Host-native validation is valuable but optional because the relevant CLI may
not be installed. If a current Codex or Claude Code validator is already
available, run it against a disposable copy when it may write files, and report
the host and validator versions with the result. A missing validator is
`unavailable`, not `passed`; do not install or update proprietary tooling just
to satisfy a contribution check.

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
`not-run` with the stop reason. Claude Code results remain
`UNAVAILABLE / NOT-RUN` when no authenticated subscription or session is
available; offline validation is a separate static signal.

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
published immutable Release. A candidate or tag version must match both
manifests. Every target must remain on approved `main` history and carry a
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
- Which files are shared and which are Codex- or Claude Code-specific.
- Any route-selection or action-authorization impact, including an explicit
  `none` when there is no impact.
- Documentation changes or a reason none are needed.
- Every validation command and its exact result, including unavailable optional
  host checks.
- A Codex/Claude Code parity review when shared behavior or packaging changes.
- Confirmation that unrelated work was not reset, hidden, staged, or rewritten.

Do not mix opportunistic cleanup with the requested change. Do not commit
generated caches, disposable validation copies, local maintenance notes, or
tool output.
