# Skill Invocation Notices

Every invoked Axiom skill must begin with a short user-visible commentary
line in this exact form: `Axiom:<skill-name>`. Replace `<skill-name>` with the
skill's frontmatter `name`, preserving its lowercase kebab-case spelling.
For example: `Axiom:task-planning`. Do not add a purpose statement to this
line; any useful progress update can follow separately.

Emit the notice before the skill's workflow actions, including routing,
questions, tool use, or delegation. This applies to explicit invocation,
automatic routing, startup, and a skill invoked by another skill. Each invoked
skill gets its own line. `using-axiom` emits `Axiom:using-axiom` even when its
routing decision selects no other skill.

Emit once per invocation. A later request or resume that selects the skill
again starts a new invocation, even if its instructions are already loaded.
Do not repeat a notice for another tool call, progress update, or reference
read within the same invocation. If the caller already emitted the exact
notice for that invocation, do not duplicate it. Merely mentioning a skill
or inspecting its files as source material is not an invocation.

The notice reports skill use; it is neither an invocation command nor a
permission request. Preserve each skill's selection, consent, authorization,
and stop conditions. Do not announce an unselected skill as active or treat
the notice as proof that any action or validation succeeded. A tool result,
internal log, or final-only summary cannot replace the visible notice.
