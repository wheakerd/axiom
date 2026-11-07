# Validation And Reporting

Run repository-owned validation proportional to every changed surface. Use a
frozen disposable copy outside the publishable tree for any validator whose
mutation behavior is uncertain.

Derive required commands, languages, byte limits, schemas, aggregate validators,
and test entrypoints from the target repository's current contract. For the
changed Skill and package surfaces, check applicable requirements:

- target-owned tests and aggregate validators, in their declared languages;
- the target's distribution and compatibility contracts;
- changed-Skill quick validation when applicable and available;
- duplicate-aware JSON and JSONL parsing where those formats are used;
- Markdown links and fragments, declared language rules, and byte limits;
- declared root-to-reference reachability and Skill layout;
- manifest and hook parsing, supported-host parity, and hook non-expansion;
- expected path set and modes, historical byte preservation, and diff hygiene;
- target brand/document consistency and available offline host validation.

A check the target requires and you did not run stays reported as not run; do
not import an Axiom-named suite or undeclared ASCII policy.

Report the exact validated revision or tree, the commands and their outcomes,
and any expected legacy-validator exception. Say which Codex or Claude Code
host, lifecycle, model, marketplace, portal, authentication, or other checks
you did not run or could not run.
Do not install, activate, publish, deploy, or contact external services merely
to make a report look more complete.
