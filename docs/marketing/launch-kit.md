# Launch Kit

Every draft presents Axiom as a public beta. Replace bracketed evidence fields
only with current, directly observed facts. Publishing, sending, or cross-posting
any item requires separate authorization for that actor, target, and payload.

Primary call to action:

> Test one routed request and one no-route control, then report the observed
> evidence.

Canonical source: <https://github.com/wheakerd/axiom>

## Show HN

### Title

Show HN: Axiom - workflow guardrails for Codex and Claude Code

### Body

Capable coding agents can start before the target, authority, rollback path, or
proof of success is clear. A command can succeed against the wrong repository;
a publish request can leave the target ambiguous; a deployment plan can quietly
become an execution.

I built Axiom as a small workflow router for those boundaries. It uses an
inspectable session hook and a checked-in routing gate to select focused Skills
for repository instruction audits, usage optimization, task review, confirmed
external actions, traceable Git submission, and reversible persistent changes.
Ordinary coding requests continue normally when no route matches.

The model is: scope, authority, evidence, rollback. Selecting a workflow is not
action authorization. Axiom is not a sandbox, permission system, or guarantee
that a model cannot make a mistake. It installs no daemon and collects no
telemetry.

The package and route contracts have static validators, but fresh-session
behavior across host versions and environments remains evidence-bounded. I am
looking for hostile routing cases and independent reproductions, including
failures.

If you try it, inspect `/hooks`, run the read-only `AGENTS.md` audit and the
README-summary no-route control from the field protocol, then file the observed
result. Which request makes the routing model fail or add too much friction?

Source and protocol: <https://github.com/wheakerd/axiom>

## Codex Community Show And Tell

### Title

Axiom public beta: explicit boundaries for high-impact Codex workflows

### Body

Axiom is a Codex plugin and shared Agent-Skills package for requests where
ordinary execution needs an explicit boundary: instruction-system maintenance,
Git publication, an external action, or a persistent system change.

Its `SessionStart` hook prints and reads one checked-in Markdown routing gate.
The installed command is intentionally inspectable and has no write, network,
updater, or background-service operation. The gate selects the smallest matching
workflow; if no route fits, Codex continues normally.

The important boundary is that route selection does not grant mutation
authority. Static fixtures exercise that contract, but they are not a claim
that every Codex release or environment behaves identically.

I would value one fresh-session reproduction: review the installed hook, run
one expected `agents-architect` request and one no-route control, and report the
host version plus visible evidence. Failures and false positives are welcome.

Repository: <https://github.com/wheakerd/axiom>

## Claude Code Community

### Title

Testing Axiom's routing boundary in Claude Code

### Body

Axiom is a public-beta Claude Code plugin with shared Skills and foreground
`SessionStart`/`PreCompact` hooks. It routes a narrow set of high-impact
workflows while ordinary requests continue through Claude Code normally.

The design separates choosing instructions from granting action authority. An
external-action route still needs the exact actor, target, payload, disclosure,
count, and retry boundary. A persistent-change route can remain a read-only
plan. A Git route does not infer push permission.

The checked-in package has static validators and can be validated with
`claude plugin validate --strict`, but I am not treating that as a fresh-session
compatibility result. Please inspect `/hooks`, run the safe routed/control pair,
and report the exact Claude Code and Axiom versions. I am especially interested
in false positives, false negatives, and compaction behavior.

Repository and protocol: <https://github.com/wheakerd/axiom>

## Reddit

### Suggested communities

Choose one community whose current rules permit open-source project posts and
technical feedback requests. Recheck self-promotion, flair, and frequency rules
before posting; do not post the same body to multiple communities at once.

### Title

I built a public-beta workflow router for high-impact Codex and Claude Code actions - looking for routing failures

### Body

The failure mode I am working on is not "the model wrote bad code." It is the
agent beginning before the target, action authority, rollback path, or evidence
of success is explicit.

Axiom adds an inspectable session hook and shared Skills for six focused
workflow families. It does not sandbox the agent or grant writes. When a
request does not match, normal coding continues.

I have static package and routing fixtures, but not enough independent
fresh-session evidence to make broad compatibility claims. The useful test is
small and read-only: run an `AGENTS.md` audit expected to route, then a README
summary expected not to route. Please include exact versions and sanitized
visible evidence. I would rather receive a reproducible failure than a generic
endorsement.

Source: <https://github.com/wheakerd/axiom>

## X

### Four-post thread

1. A coding agent can execute the right command against the wrong target. Axiom
   is a public-beta workflow router for Codex and Claude Code that makes scope,
   authority, evidence, and rollback explicit for high-impact actions.

2. Route selection is not action authorization. A Git route does not imply
   push permission; an external-action route still binds actor, target, payload,
   count, disclosure, and retry; a deployment route can remain planning-only.

3. Axiom uses an inspectable foreground hook and shared Skills. It is not a
   sandbox, installs no daemon, and collects no telemetry. Ordinary coding
   continues normally when no route matches.

4. I need adversarial evidence, not only Stars: inspect the hook, test one
   routed request and one no-route control, then report what happened.
   <https://github.com/wheakerd/axiom>

## LinkedIn

Coding-agent failures often begin one layer before code quality: the target is
ambiguous, permission is inferred, the retry boundary is undefined, or command
success is treated as proof of the intended outcome.

Axiom is a public-beta workflow router for Codex and Claude Code. It selects a
focused workflow for high-impact requests and makes four boundaries explicit:
scope, authority, evidence, and rollback. Selecting the route never grants a
write, push, deployment, deletion, credential use, or external action.

The repository includes inspectable hooks, shared versioned Skills, and static
contract fixtures. Those checks do not establish universal host compatibility,
so the next milestone is independent fresh-session evidence from maintainers,
platform engineers, DevSecOps practitioners, and release engineers.

If this is your problem space, test one read-only routed request and one
no-route control, then file the observed evidence - especially failures or excess
friction: <https://github.com/wheakerd/axiom>

## Chinese Technical Communities

V2EX, Zhihu, and Juejin need native Chinese copy rather than a line-by-line
translation. Repository policy keeps canonical public documentation
English-only, so the Chinese publish-ready drafts remain in the task
authorization packet.

- V2EX: concise builder post; lead with a concrete wrong-target or inferred-
  authority scenario, disclose the public-beta limits, and ask for one
  reproducible routing case.
- Zhihu: explanatory article; distinguish route selection from authorization,
  then walk through routed and no-route prompts and evidence labels.
- Juejin: engineering implementation note; focus on the foreground hook, shared
  Skills, static fixtures, and why command success is insufficient evidence.

Do not publish all three at once. Start with the audience most likely to run the
protocol, then adapt the next post using observed questions rather than copying
the first.

## Direct Design-Partner Outreach

### Subject

Test Axiom's routing boundary in one fresh session

### Message

I am looking for five to ten independent testers for Axiom, a public-beta
workflow router for high-impact Codex and Claude Code actions. The test is
read-only and should take about ten minutes: install a named version, inspect
the hook, run one request expected to route and one no-route control, then file
a sanitized compatibility report.

I am specifically looking for failures, ambiguous cases, and unnecessary
friction. Please use a non-sensitive repository. Participation does not imply
public attribution, and I would request separate permission before using any
name, quote, repository, or case study.

Protocol: <https://github.com/wheakerd/axiom/blob/main/docs/field-validation.md>

## FAQ

### Is Axiom just a prompt collection?

No. It packages versioned Skills behind a small routing gate, platform
manifests, inspectable session hooks, route-specific authority and evidence
contracts, and checked-in fixtures. Its instructions are still interpreted by
the host model, so packaging does not make them an enforcement kernel.

### Is Axiom a sandbox?

No. Host sandboxing, repository permissions, operating-system controls, and
connected-service permissions remain outside Axiom.

### Does selecting a workflow authorize a write?

No. Route selection identifies relevant instructions. Exact mutation authority
must come from the active user request and instruction chain.

### Does Axiom run a daemon or background service?

No. The checked-in Axiom package starts no service, watcher, scheduler, or
background updater. A host may independently manage plugin updates.

### Does Axiom collect telemetry?

No. The checked-in package contains no analytics or telemetry mechanism.

### Why is a hook involved?

The hook makes the small routing gate available at session start and supported
compaction events without loading every task workflow.

### How can users inspect the hook?

Open `/hooks` in the installed host and compare every handler with the exact
commands in the README. Stop if they differ.

### What happens when no route matches?

The host continues its ordinary workflow. No-route is not a certificate that
the request has no risk.

### What evidence has actually been validated?

Identified repository trees have package, manifest, link, schema, and route-
contract checks recorded in release documentation. Fresh installed-session and
independent evidence must be reported separately.

### Why support both Codex and Claude Code?

Both hosts support distributable Skills and hooks, and the safety boundary is
host-independent. Axiom keeps one shared Skill source while preserving separate
host wrappers and lifecycle behavior.

### Can Axiom guarantee that an agent will never make a mistake?

No. It cannot guarantee model correctness, host integrity, dependency safety,
credential configuration, external-service behavior, or user intent.

## Pre-Publication Checklist

- Re-read the target community's current rules.
- Freeze the actor, destination, exact body, links, disclosure, and number of
  posts.
- Replace no evidence placeholder with an inference.
- Confirm the linked branch or release is public and immutable enough for the
  claim.
- Verify no secret, private path, participant identity, or unapproved quote is
  present.
- Decide the retry rule before posting; an uncertain result is not retried
  blindly.
- Record the authoritative public URL after publication and correct or delete
  through the platform's supported path if the payload is wrong.
