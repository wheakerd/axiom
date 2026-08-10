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
| `scripts/` and `.github/workflows/` | Repository validation; not installed runtime behavior |

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
`skills/using-axiom/SKILL.md`, while Claude Code also owns `PreCompact`
behavior. Keep the conventional `hooks/hooks.json` absent so one host does not
auto-discover the other host's wrapper.

Review any hook change command by command. A hook must remain foreground-only,
locally inspectable, and limited to loading the routing gate. Do not add file
writes, network calls, credential access, a daemon, watcher, scheduled task, or
automatic update behavior. Update the relevant manifest and public trust
documentation whenever a declared hook path or command changes.

## Required local checks

Run checks from the repository root and record the exact commands and outcomes:

```bash
python3 scripts/check-distribution-drift.py
python3 scripts/check-publication.py
git diff --check
```

Also run targeted checks required by the files you changed. Read the final
diff, confirm both manifest versions still match, and inspect
`git status --short` for unrelated paths.

Host-native validation is valuable but optional because the relevant CLI may
not be installed. If a current Codex or Claude Code validator is already
available, run it against a disposable copy when it may write files, and report
the host and validator versions with the result. A missing validator is
`unavailable`, not `passed`; do not install or update proprietary tooling just
to satisfy a contribution check.

## Runtime boundary

Axiom installs Markdown skills and foreground hook definitions. It has no
installed daemon, background updater, network update check, or bundled runtime
dependency. Repository validation may use a host-provided interpreter in CI,
but that check must not become a dependency of the installed plugin. Prefer
focused, standard-library-only validation when adding repository checks.

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
