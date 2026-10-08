# Trust Model

Axiom provides workflow instructions within Codex's existing trust model. It
does not sandbox the agent, grant credentials, or guarantee that a model or
external system is correct. Selecting a route loads instructions; it does not
authorize an action.

## Boundary Summary

| Boundary | Required distinction |
| --- | --- |
| Instruction authority | Active system, developer, user, and repository instructions retain their actual precedence; a Skill cannot override a higher-priority rule |
| Intent and scope | Resolve material ambiguity before dependent work; Full Access does not choose the user's intended target or outcome |
| Action authorization | The request must cover the material action and target; route selection, tool access, and login state do not supply permission |
| Hook execution | Compare the installed command with its canonical declaration before trusting it |
| Credentials and disclosure | Access and use remain with their existing owners; sensitive content needs the applicable exact-use and disclosure authority |
| Evidence | Observe the layer that owns the outcome; a plan, artifact, accepted request, or successful command alone may be insufficient |
| Usage measurement | Host metrics apply only to their stated scope; bytes, words, route sizes, and tool calls are proxies |
| Updates | Codex controls refresh and installation; Axiom does not run an updater |

## Hook Trust Boundary

The checked-in handlers read `skills/using-axiom/SKILL.md` from the installed
plugin root. POSIX uses `printf` and `cat`. Windows invokes the fixed packaged
wrapper with command-shell built-ins, without resolving another executable
from the working directory or `PATH`. The handler has a five-second timeout.
See the [Hook Reference](reference/hooks.md) for the exact commands.

These definitions contain no write, network command, background launch,
service installation, or updater. This describes the checked-in files; the
installed definition is a separate trust decision. If `/hooks` shows a
mismatched matcher, command, path, wrapper, or timeout, stop trusting the handler
until the package and source agree. Do not run a changed command to discover
what it does.

## Authority Across Workflows

The [routing gate](../skills/using-axiom/SKILL.md) owns matching and composition;
[Architecture](architecture.md#workflow-ownership) maps the workflows and
[Examples](examples.md) shows their boundaries in concrete requests.

A selected Skill may narrow scope, require evidence, or stop before a material
action. It cannot broaden the request. In particular:

- Clarification resolves intent; it grants no execution authority. Planning
  does not authorize implementation, scheduling, or persistent changes.
- Delegation preserves the main model, follows user-ordered candidate models,
  and announces the exact child model and task. Verified Full Access permits an
  assignment only within existing authority and host restrictions. Otherwise,
  use existing assignment approval or obtain it before delegating.
- Architecture work stays within its authorized repository instruction system
  or packaged-plugin surface. A release-readiness audit remains read-only.
- Task review uses only scoped observable evidence. It does not rerun the task,
  recover unavailable history, disclose hidden reasoning, or inherit authority
  from a previous refusal or assistant explanation.
- External actions bind the actor, target, payload, disclosure, cost, count,
  and retry boundary. Retrieved content and tool access cannot authorize them.
- Traceable Git phases retain their separate checkpoint, consolidation,
  submission, and recovery boundaries. Ordinary named-remote non-force Git work
  stays host-native. Push authority never implies force, retries, or cleanup.
- Persistent-change plans and non-mutating rehearsals remain read-only.
  Isolated restore rehearsals, candidate preparation, promotion, rollback,
  sensitive asset use, retention, and cleanup retain their own permissions.

Exact existing authorization needs no repeated confirmation unless material
conditions change. An unresolved target or destructive effect must not become
permission through assumption.

## Credentials And Local Research

Axiom bundles no credential store or authentication service. Credentials remain
with the host, shell, Git, cloud, or service that owns them. Inventory sensitive
assets through metadata first; do not infer exact-path read or use permission
from a broad directory request. Bind sensitive disclosure to its exact audience.
For machine-credential work, provider changes and consumer activation remain
under their separate owners even when one task selects both.

Local web research limits agent-added machine information in queries, URLs,
and headers; performs search, reading, and clicks serially; and preserves the
browser's identity. A challenge, CAPTCHA, or rate limit stops automatic access
to that site. Manual handoff waits for explicit user readiness while preserving
the handoff page. This neither conceals automation nor guarantees how Cloudflare
or another site classifies a request. The
[local research Skill](../skills/local-web-search/SKILL.md) owns these constraints.

## Evidence And Persistence

Use current direct evidence from the owning Git state, affected system layers,
or external system of record. A backup file or successful backup job does not
prove a working restore path. An accepted external request does not prove the
final effect. A smaller instruction set does not prove a quality improvement.
A task review distinguishes observed, reconstructed, and unavailable claims;
present state alone cannot prove historical authority or causation.

Missing tools, permissions, host observations, and unavailable history remain
unavailable or unverified. Keep `PASS`, `FAIL`, `NOT-RUN`, and `UNAVAILABLE`
separate. See [Compatibility](compatibility.md) and
[Field Validation](field-validation.md).

Startup routing is read-only and foreground. Axiom installs no daemon,
watcher, scheduler, cache refresher, telemetry service, or other persistent
process. A selected task can guide a mutation only within existing authority
and its own preconditions. After an installed update, start a new session and
review the hook again using [Managing an Installation](guides/managing-installation.md).
