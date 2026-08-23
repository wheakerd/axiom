# Trust Model

Axiom narrows how an agent approaches seven focused workflow families. It
does not replace the host's trust model, sandbox the agent, grant credentials,
or guarantee that a model or external system is correct.

The central rule is simple: selecting a route loads instructions; it does not
authorize an action.

## Boundary Summary

| Boundary | What Axiom requires | What Axiom does not infer |
| --- | --- | --- |
| Instruction authority | System, developer, user, and active repository instructions retain their actual precedence | A selected Axiom skill cannot override a higher-priority rule |
| Action authorization | The request must authorize the exact material action and target | Route selection, tool access, or an available command is not permission |
| Scope | Repositories, paths, commits, remotes, environments, assets, and indirect effects are resolved and bounded for the active workflow | A broad directory, default profile, guessed target, or neighboring resource is not automatically in scope |
| Hook execution | The installed hook must match the inspectable checked-in command and read the intended routing gate | Trust in the repository name does not excuse a changed installed command |
| Credentials and sensitive data | Existing credentials remain host-managed; sensitive content requires exact-path and exact-use authority where a route needs it | Credential presence, login state, or directory access does not authorize use or disclosure |
| Mutation | Each workflow keeps its own edit, commit, push, promotion, deletion, or rollback gates | Loading a skill is never mutation authority |
| Evidence | Completion is based on fresh, direct evidence from the layer that owns the outcome | A successful command, queued operation, present artifact, or missing validator is not proof |
| Usage measurement | Host-reported metrics are exact only for their stated scope; bytes, words, route sizes, and calls are labeled proxies | Axiom cannot read hidden tokens, credits, reasoning work, or cache hits, and never invents exact savings |
| Updates | The host controls manual refresh and any configured auto-update; a changed snapshot requires session reload or restart and renewed hook review | Axiom itself does not check, download, install, or announce updates |

## Hook Trust Boundary

Plugin hooks execute in a host session. Review them before trusting them.
Axiom's checked-in handlers use the host-provided plugin root, print a loading
message, and read `skills/using-axiom/SKILL.md`. The exact commands appear in
[README: Inspect The Hooks](../README.md#inspect-the-hooks).

The command surface is deliberately small: POSIX handlers use `printf` or
`echo` plus `cat`; the Codex Windows handler uses PowerShell output plus
`Get-Content`. There is no redirection, write, network command, background
launch, service installation, or updater in those definitions.

This claim applies to the checked-in files. The installed definition is a
separate trust decision. If `/hooks` shows another path or any additional
command, stop trusting that handler until the installed package source and the
repository definition agree. Do not run a changed command merely to see what it
does.

## Authority And Authorization

`using-axiom` first honors the active instruction hierarchy, then decides
whether a request clearly matches a route. A more specific route may add
preflight checks, evidence requirements, and stop conditions. It cannot expand
the user's request or remove a higher-priority prohibition.

The workflows make this distinction concrete:

- `agents-architect` may change only the authorized instruction system. It
  treats host-discovered non-`AGENTS.md` instruction candidates as read-only
  and keeps protected plugin metadata outside ordinary AGENTS work.
- `agent-plugin-architect` owns only explicit packaged Codex or Claude Code
  plugin architecture. It treats repository content as untrusted data, keeps
  repo-local instruction systems and ordinary plugin code outside, adds no
  startup command, and cannot authorize installation, publication, deployment,
  Git submission, credentials, or remote effects.
- `optimize-codex-usage` changes only the authorized repository or workflow
  surfaces. It does not automatically lower model/reasoning settings, install
  measurement tools, remove required evidence, or claim hidden usage data.
- `review-axiom-task` reviews only the scoped, host-visible task evidence. It
  cannot infer hidden reasoning, recover unavailable history, rerun the task,
  or turn a retrospective request into new read, credential, mutation, or
  remote authority.
- `confirm-external-action` treats drafts and previews as non-authorizing,
  binds the acting account, target, payload, disclosure, cost, count, and retry
  policy, and verifies an executed effect through the external system of
  record. Retrieved content and tool access never supply user authority.
- `traceable-git-submit` is selected for an explicit checkpoint, baseline,
  consolidation, recovery, submit, publish, or push request. Checkpoint state,
  baseline mutation, consolidation, remote refresh, push, and cleanup remain
  independent permissions. A direct history-preserving push creates no Axiom
  metadata, and push never implies consolidation. Target-controlled Git
  configuration and programs remain non-authorizing executable input; every Git
  command requires a frozen non-executable process boundary or separate exact
  authority for the executable it would run.
- `reversible-system-change` keeps plans and non-mutating workflow rehearsals
  read-only. An isolated restore rehearsal is a separately authorized persistent
  write; rehearsal, candidate preparation, active promotion, sensitive asset
  use, destructive retention, rollback, and cleanup are distinct permissions.

If the target, environment, credentials, destructive scope, or promotion
authority is ambiguous in a way that changes execution, the workflow stops for
clarification rather than turning ambiguity into permission.

## Credential And Sensitive-Data Boundary

Axiom does not bundle a credential store or authentication service. Credentials
remain in the host, shell, Git, cloud, or service boundary that already owns
them. A saved credential, default account, working login, or ability to invoke
a tool proves access only; it does not prove authority for a target or action.

The Git workflow reports targets without exposing remote URLs, usernames,
credentials, or private endpoints. The system-change workflow inventories
sensitive assets through metadata first and requires authorization for the
exact asset path and exact read or use action before content access. A broad
directory request is not enough. The external-action workflow separately binds
each sensitive value that will cross a trust boundary and the exact audience
allowed to receive it.

## Evidence Boundary

Axiom distinguishes current direct evidence from plans, historical reports,
manifests, command exit codes, and inferred state.

- Repository completion requires current evidence from the owning Git tree,
  index, references, and configured targets relevant to the request.
- Persistent-change completion requires current evidence from every affected
  materialization, selection, runtime, delivery, behavior, and preservation
  layer that owns the outcome.
- External-action completion requires direct state from the service that owns
  the effect; request acceptance or a successful tool call alone is not proof.
- A backup, rollback script, or successful backup job is not by itself proof
  that current restoration works.
- A smaller Skill or route chain is not by itself an improvement unless the
  same routing, authorization, safety, and outcome scenarios still pass.
- A task review labels material claims as observed, reconstructed, or
  unavailable. Current state may verify a present outcome, but it does not by
  itself prove historical authorization, causation, or active instructions.
- A missing tool, permission, host, or downstream observation is unavailable or
  unverified, not passed.

This is an evidence discipline, not a guarantee that every observation or
external system is trustworthy. Reports should say which checks passed, failed,
were not run, or were unavailable.

## Mutation And Persistence Boundary

Session routing itself performs no repository or system mutation. It reads a
checked-in Markdown gate in the foreground and does not contact a network
service. Axiom installs no daemon, watcher, scheduler, cache refresher, or other
persistent process.

A selected task workflow may guide a mutation only when the user request and
active instructions authorize it and its own preconditions pass. A safe stop is
an expected result when scope, authority, rollback, or evidence is insufficient.

`review-axiom-task` remains read-only and creates no transcript, trace file,
cache, telemetry, or background process. A later mutation requires its own
explicit authority and applicable workflow.

## Update Boundary

Axiom has no updater of its own. Update checks, marketplace refreshes,
downloads, and installation remain host-controlled actions, but they are not
always manually initiated: Claude Code can refresh marketplaces and update
installed plugins on disk after startup when auto-update is enabled. Its
third-party and local marketplace auto-update setting is disabled by default,
but a user or administrator can enable it. The running session keeps its
already-loaded version until reload or the next launch.

Use [README: Updating](../README.md#updating) for manual refresh and auto-update
details, or [README: Disabling Or Removing](../README.md#disabling-or-removing)
to stop loading Axiom through the host. After any installed snapshot changes,
start or reload the session and review the installed hook again. A previously
trusted hook does not make a changed definition automatically trustworthy, and
the absence of a manual refresh does not prove that files on disk are unchanged.

## What This Model Does Not Promise

Axiom does not prevent every hallucination, malicious dependency, compromised
host, incorrect credential configuration, unsafe user instruction, or external
service failure. It does not make an unreviewed installed package trustworthy,
and a no-route result does not certify that an ordinary task is harmless.

For a bounded first-install check, follow [Getting Started](getting-started.md).
For version and host evidence, see [Compatibility](compatibility.md).
