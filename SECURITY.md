# Security Policy

Axiom is a public-beta workflow router. It adds instruction and hook surfaces to
Codex and Claude Code, so a changed manifest, hook, Skill, or trust boundary can
be security-relevant. A routing-quality bug is not automatically a security
vulnerability.

## Supported Versions

Security reports are evaluated against the latest published release and the
current `main` branch. Older releases are not actively maintained, and a
reporter may be asked to reproduce an issue on the latest release. Fixes are not
promised for every older version, and this project does not publish a response
time or remediation SLA.

## Report A Vulnerability Privately

Do not publish exploitable details, secrets, proof-of-concept payloads, or
sensitive repository data in an Issue, Discussion, pull request, or public
comment.

GitHub private vulnerability reporting was verified as enabled on 2026-08-21.
Use the repository's
[Report a vulnerability](https://github.com/wheakerd/axiom/security/advisories/new)
form to create a private security advisory. Do not open a public placeholder
Issue for a vulnerability.

Include:

- the affected Axiom version, tag, or immutable commit;
- the affected host and version;
- the smallest safe reproduction;
- expected and observed trust-boundary behavior;
- impact and preconditions;
- whether a mutation, credential, external effect, or persistent change was
  involved; and
- a suggested correction, if known.

## Route-Quality And Compatibility Reports

Use the public
[routing-case form](https://github.com/wheakerd/axiom/issues/new?template=routing_case.yml)
for a false positive, false negative, ambiguity, or expected routing case that
does not expose a vulnerability. Use the
[compatibility form](https://github.com/wheakerd/axiom/issues/new?template=compatibility_report.yml)
for a fresh-session host observation. Sanitize every request and attachment.

If a routing case caused or could plausibly cause unauthorized credential use,
external publication, destructive retention, unsafe Git publication, a
persistent change outside the bound target, or execution of a changed hook,
treat it as potentially security-sensitive and do not disclose the details
publicly.

## Security Boundaries

Read the [Trust Model](docs/trust-model.md) before assessing impact. In
particular:

- selecting a route loads instructions; it never grants action authority;
- installed hooks must be compared with the exact checked-in definitions;
- host, operating-system, repository, credential, and connected-service
  permissions remain outside Axiom's control;
- request acceptance and command exit status are not proof of the intended
  outcome; and
- missing or unavailable evidence must not be reported as a pass.

Axiom is not a sandbox, policy-enforcement kernel, credential broker, malware
detector, or guarantee that an agent, host, dependency, or external service is
correct. It does not prevent every error or unsafe instruction. See the
[field-validation protocol](docs/field-validation.md) for evidence labels and
safe reproduction prompts.
