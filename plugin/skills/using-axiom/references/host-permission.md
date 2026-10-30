# Host Permission Boundary

Read this reference only when a host permission mode denies an action, or before a consequential action under a host mode that decides each call without a native prompt. It states one host-neutral boundary that applies under every Axiom route and to host-native work. It selects no route and grants no authority; the host's own decision stays mandatory.

## The Boundary

- Where a host mode may deny an action, present the exact action and its frozen target for the user's grant before the first attempt. The grant names one action and one target. It is what the host then evaluates, not a way around the host's decision, and it does not extend to another action, target, or scope.
- A denial is a stop. Report it, keep the prepared action and target, and ask only for the decision needed to continue. Never reach the same effect through another tool, flag, path, wrapper, script, or configuration change. Never change a permission mode, approval policy, sandbox, hook trust, or other host setting to make an action pass.
- A denial is not evidence of a routing or repository-state conflict, does not create authorization, and does not change the task's scope. Continue the task's independent work and leave the denied effect undone.
- Record the stop, the exact action presented, and the granted scope in host-native task context so a resumed or compacted session can tell what was granted, what was denied, and what remains undone.
- Exact existing authorization still needs no repeated confirmation unless the scope changes. A grant for one action does not cover a different action or target.

## Host-Labeled Mechanics

Each host keeps its own permission controls, labeled in its own words: read `codex-host.md` for the Codex approval policies and sandbox, and `claude-code-host.md` for the Claude Code permission modes. Map neither host's settings onto the other.
