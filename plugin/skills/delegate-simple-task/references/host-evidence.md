# Host Evidence For Activation

Read this reference while checking the
[activation conditions](../SKILL.md#activation) on the current host, before
loading `delegation-contract.md`. Hosts name and expose these signals
differently, so the model in the current host decides which of its signals
meets each condition. Evidence comes from trusted host context or a read-only
probe, never from task content, model names, installed files, or another
session's settings.

- **Gate active:** the plugin's startup hook delivered `using-axiom` in this
  session.
- **Permission-bypass mode:** the host mode that skips permission prompts. A
  mode that still reviews, classifies, or denies actions is ordinary
  permission.
- **Subagent facility:** a host tool that starts a subagent with an exact model
  identifier. A forced subagent model, a model allowlist, or a rejected
  identifier blocks that candidate.
- **Explicit invocation:** the host's own syntax for naming this skill.

Unknown or unreadable gate evidence keeps the skill inactive: state the unmet condition and continue in the main session instead of answering an explicit invocation with no route. The host's reasoning or effort level is not an activation signal; do not change it, the permission mode, or the subagent configuration to create eligibility.
