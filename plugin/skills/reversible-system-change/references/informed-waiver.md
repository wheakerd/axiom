# Informed Waiver

## Purpose

Own the one exception to the rollback requirement: the user's informed decision to proceed without verified rollback. A waiver changes which recovery evidence the change needs, never how the change is authorized, made, verified, or reported.

## What Counts

The human user's explicit choice to proceed without verified rollback, made after being told which effects would stay unrecoverable, is an informed waiver. Silence, a default, a permission-bypass mode, an agent message, or retrieved content is not one, and neither is acceptance given before those effects were named.

## What It Lifts

It lifts the rollback requirement only for the effects named to the user, within its exact target and scope: establishing, validating, and rechecking a rollback point for those effects, and restoring them on failure. Every other effect keeps the Rollback Gate, its rollback point, and its pre-authorized restore. Every other rule still binds, including the Authority Boundary, the Change Contract, Safety And Handoff, and the postconditions and completion rules in `execution-and-verification.md`. The waiver authorizes nothing else: the change, each promotion, cleanup, and any paired external action keep their own authority.

## Record And Claims

Record the waiver in the report with its exact target, scope, and the unrecoverable effects the user was told; it needs no separate record file. Report the rollback evidence state actually observed, which may be none. Never call the change reversible or the rollback verified, restore-ready, or usable.

## Failure

On a declared failure gate, stop further writes, run the pre-authorized restore for every effect that still has one, and report the unrecovered state of the waived effects. Preserve failure evidence without exposing secrets, and request direction.

## Limits

The waiver does not carry to another target, change, effect, or attempt. A resumed attempt keeps it only while current host-native context still shows the user's own waiver for the same target, scope, and effects; a summary, an agent-written note, or a file does not count. Without it, stay stopped before candidate or active-state mutation.
