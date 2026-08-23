# Validation And Reporting

Run repository-owned validation proportional to every changed surface. Use a
frozen disposable copy outside the publishable tree for any validator whose
mutation behavior is uncertain.

For a shared packaged Skill and release contract, check:

- the full standard-library test suite and aggregate publication validator;
- distribution drift, compatibility evidence, and routing-context results;
- changed-Skill quick validation when available;
- duplicate-aware JSON and JSONL parsing;
- Markdown links and fragments, exact ASCII policy, and instruction byte size;
- direct root-to-reference reachability and absence of nested Skills;
- manifest and hook parsing, cross-host parity, and hook non-expansion;
- expected path set and modes, historical byte preservation, and diff hygiene;
- brand/document consistency and available offline host validation.

Report the exact validated revision or tree, commands and outcomes, context
metrics, compatibility class, and any expected legacy-validator exception.
List Codex host, lifecycle, model, marketplace, portal, authenticated Claude,
or other checks as `NOT-RUN` or `UNAVAILABLE` when direct evidence is absent.
Do not install, activate, publish, deploy, or contact external services merely
to improve a validation label.
