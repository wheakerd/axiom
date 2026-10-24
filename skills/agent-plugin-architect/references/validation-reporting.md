# Validation And Reporting

Run repository-owned validation proportional to every changed surface. Use a
frozen disposable copy outside the publishable tree for any validator whose
mutation behavior is uncertain.

Derive required commands, languages, byte limits, schemas, aggregate validators,
and test entrypoints from the target repository's current contract. For the
changed Skill and package surfaces, check applicable requirements:

- target-owned tests and aggregate validators, in their declared languages;
- target distribution, compatibility evidence, and routing-context contracts;
- changed-Skill quick validation when applicable and available;
- duplicate-aware JSON and JSONL parsing where those formats are used;
- Markdown links and fragments, declared language rules, and byte limits;
- declared root-to-reference reachability and Skill layout;
- manifest and hook parsing, supported-host parity, and hook non-expansion;
- expected path set and modes, historical byte preservation, and diff hygiene;
- target brand/document consistency and available offline host validation.

Missing target-required checks remain incomplete or `NOT-RUN`; do not import
an Axiom-named suite or undeclared ASCII policy.

Report the exact validated revision or tree, commands and outcomes, context
metrics, compatibility class, and any expected legacy-validator exception.
List Codex or Claude Code host, lifecycle, model, marketplace, portal,
authentication, or other checks as `NOT-RUN` or `UNAVAILABLE` when direct
evidence is absent.
Do not install, activate, publish, deploy, or contact external services merely
to improve a validation label.
