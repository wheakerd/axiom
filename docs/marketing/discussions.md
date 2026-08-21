# GitHub Discussions Plan

Status checked: 2026-08-21. GitHub Discussions was disabled for the repository
at that time. Enabling it,
creating categories, and publishing each seed discussion are separate remote
actions. The material below is prepared but not published.

## Categories

| Category | Format | Purpose |
| --- | --- | --- |
| Compatibility Reports | Open-ended discussion | Fresh-session host observations, installation differences, and evidence questions |
| Routing Cases | Question and answer | False positives, false negatives, ambiguous requests, and expected route boundaries |
| Ideas and Design | Open-ended discussion | New high-impact workflow families and friction-reduction ideas |

If GitHub requires an initial category during enablement, create only the three
above. Do not add an announcements category until there is a recurring,
evidence-backed need.

## Seed 1: Report your first fresh-session Axiom test

Category: Compatibility Reports

### Body

Axiom is in public beta, and repository checks are not a substitute for an
installed-session observation. Please try the safe
[field-validation protocol](../field-validation.md) in a fresh Codex or Claude
Code session:

1. record the host, exact host version, operating system, Axiom version or
   immutable commit, and installation method;
2. inspect the installed Axiom handlers in `/hooks` and compare them with the
   checked-in commands;
3. run the routed read-only `AGENTS.md` audit;
4. run the no-route README-summary control; and
5. report pass, fail, not run, and unavailable outcomes separately.

Please remove secrets, private URLs, customer data, and sensitive repository
content. A manifest or successful command is not an end-to-end pass. Use the
[compatibility Issue form](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)
when you have a complete report; use this discussion for questions and partial
observations.

## Seed 2: Share a routing false positive or false negative

Category: Routing Cases

### Body

Which smallest sanitized request caused Axiom to select a route when it should
have continued normally, or to continue normally when a focused workflow was
expected?

Include the exact request, expected route, observed route, host and Axiom
versions, whether any mutation was attempted, and the smallest visible
evidence. Route selection itself never authorizes a write. If the case could
expose an exploitable security issue, do not publish the details; follow
[SECURITY.md](../../SECURITY.md).

For a structured report, use the
[routing-case Issue form](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml).
Hostile cases and unclear boundaries are useful even when the result is a
failure.

## Seed 3: Which high-impact agent workflow should Axiom cover next?

Category: Ideas and Design

### Body

Axiom should add a route only when a distinct high-impact workflow needs its
own scope, authority, evidence, stop, or rollback contract. It should not turn
ordinary coding into a special process.

Describe one concrete user outcome and answer:

- what can go materially wrong;
- which target, credential, external system, persistent state, or retry boundary
  needs to be bound;
- why the current routes and normal host behavior are insufficient;
- what must remain explicitly user-authorized; and
- what direct evidence would prove the intended outcome.

Preference goes to narrow, reproducible cases over broad requests for "more
safety." Feature proposals can use the existing
[feature-request form](https://github.com/wheakerd/axiom/issues/new?template=feature_request.yml)
after the problem boundary is clear.

## Enablement And Verification

Follow GitHub's current
[Discussions enablement](https://docs.github.com/en/discussions/quickstart)
and
[category management](https://docs.github.com/en/discussions/managing-discussions-for-your-community/managing-categories-for-discussions)
documentation. After authorization, verify the repository exposes the
Discussions tab, the three category names and formats match this plan, and each
seed appears once in the intended category. A created draft or accepted API
request is not proof of public visibility.
