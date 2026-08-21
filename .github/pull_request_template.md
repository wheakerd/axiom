## Scope

<!-- State the intended outcome and why this is the smallest useful change. -->

## Affected files and surfaces

<!-- List exact paths. Mark each as shared, Codex-specific, Claude Code-specific, documentation, or repository validation. -->

- Shared files:
- Codex-specific files:
- Claude Code-specific files:
- Documentation or validation files:

## Routing and authorization impact

<!-- Describe any change to route matching separately from any change to what an agent may inspect, plan, or mutate. Write "None" when there is no impact. -->

- Route-selection impact:
- Action-authorization impact:
- New or changed stop conditions:

## Documentation

<!-- Link the updated documentation, or explain why no documentation change is needed. Confirm installation and hook commands remain aligned when relevant. -->

## Validation

<!-- Include every command and its exact result. Mark optional host-native checks unavailable when they could not run; do not present them as passed. -->

<!-- These pull-request checks validate the proposed tree. They do not establish release provenance or authorize publication. -->

| Command | Result |
| --- | --- |
| `python3 scripts/check-distribution-drift.py` | |
| `python3 scripts/check-compatibility-evidence.py --self-test` | |
| `python3 scripts/check-publication.py` | |
| `git diff --check` | |
| Additional targeted checks | |

## Cross-platform parity

<!-- Explain how Codex and Claude Code wrappers were compared, or why the change is host-specific. -->

- [ ] Shared skill changes were reviewed against both hosts, or this change does not affect shared skills.
- [ ] Manifest, marketplace, and hook differences remain intentional and documented.
- [ ] Optional host-native validation results include the host/tool version, or are marked unavailable.

## Unrelated work

- [ ] I reviewed the final diff and did not reset, hide, stage, or rewrite unrelated work.
- [ ] I did not add generated caches, disposable validation copies, local maintenance notes, or tool output.
- [ ] I called out every affected file and any routing, authorization, documentation, or parity impact above.
