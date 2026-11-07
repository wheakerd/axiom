# Evaluation And Evidence

Two rules cover a target plugin's evaluation assets and what you say about
host behavior.

## The Target's Evaluation Assets

Use the evaluation assets the target repository already has, such as a routing
evaluator, test requests, result records, and their formats, as they are.
Extend them only where the authorized change requires it, and leave existing
records unchanged. When the target has none, review the change by reading it
against realistic requests. Do not create an evaluator, a set of test
requests, or a record format, and do not install tooling, to satisfy this
Skill.

If the target has an always-loaded startup surface, compare its size before
and after and justify material growth, using the target's own measure and
threshold when it has them. Do not invent a startup gate or a threshold for a
target that has none.

## Host Behavior

Say what you observed and how you observed it: by reading files, by running a
check without a host, or in a host session. Never infer from files how a host
discovers, loads, selects, or runs the package. When a host session, a
subscription, or a tool was not available, or you did not run a check, say so
plainly; that is never a pass.
