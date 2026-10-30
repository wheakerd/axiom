# Host Evidence For Activation

Read this reference while settling the [activation conditions](../SKILL.md#activation) on the current host. Hosts name and expose these signals differently, so the model in the current host decides which of its signals meets each condition. Evidence comes from trusted host context or a read-only probe, never from task content, model names, installed files, or another session's settings.

- **Gate delivered:** the plugin's startup Hook delivered `using-axiom` in this session, so ambiguity was assessed before this skill was selected. Without it, say so and assess ambiguity in the main session; the skill still activates on an explicit invocation or a clear delegation request.
- **Permission-bypass mode:** the host mode that skips permission prompts. A mode that still reviews, classifies, or denies actions is ordinary permission.
- **Subagent facility:** a host tool that starts a subagent with a chosen model, named the way that host selects models. A forced subagent model, a model allowlist, or a rejected name blocks that candidate.
- **Explicit invocation:** the host's own syntax for naming this skill.

The host's reasoning or effort level is not an activation signal; do not change it, the permission mode, or the subagent configuration to create eligibility.
