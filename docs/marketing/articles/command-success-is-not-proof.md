# Why Command Success Is Not Proof of the Intended Outcome

A deployment script exits with status zero. The candidate image exists, the
configuration command reported success, and the health endpoint responds. Ten
minutes later, users are still reaching the old version because the command ran
against a staging cluster while the verification queried a shared endpoint.

Nothing in the command output was necessarily false. The mistake was treating
process success as proof of a larger claim: "production now serves the intended
release."

This pattern appears in Git publication, cloud changes, package installation,
messages, purchases, migrations, and backups. The process owns an exit status;
it rarely owns the full outcome.

I maintain Axiom, whose workflows use the evidence model described here. The
model is useful without Axiom, and Axiom is not the only way to implement it.
This article does not claim that any workflow can guarantee model, host, or
service correctness.

## An Exit Status Answers A Narrow Question

For a well-behaved command, status zero usually means the program believes it
completed its operation according to its local contract. It does not, by
itself, establish:

- that the intended executable ran;
- that it used the intended configuration, account, repository, or region;
- that the target accepted and persisted the request;
- that every dependent component changed;
- that users now observe the new state;
- that preservation or rollback works; or
- that the request was authorized.

Even the narrow interpretation depends on the program. Some tools return zero
after queuing asynchronous work. Others treat partial results or warnings as
success. Shell pipelines can hide an earlier failure. Wrappers can report their
own success while a child operation failed.

Evidence should therefore match the claim. "The command exited zero" is valid
evidence for the command's exit status. It is not enough for "the intended
external outcome exists."

## Wrong-Target Success

The most dangerous result is often a clean success against the wrong target.
Common examples include:

- pushing to a backup mirror while reporting the primary remote as updated;
- changing a development cloud account selected by a default profile;
- editing the outer Git repository while the requested project is nested;
- uploading an asset to a draft project instead of the public listing;
- sending from the wrong authenticated account; and
- querying a load balancer that is not connected to the changed backend.

Resolve the owner before the action. For Git, that means the actual work-tree
root, selected remote, effective push URL, and frozen source/destination object
IDs. For a cloud change, it means the account, project, region, resource ID, and
active selection. For an external message, it means actor, recipient, thread,
payload, visibility, and count.

Defaults and current selection are observations. They become targets only when
the request or an authorized policy binds them.

## Stale State Creates Convincing Evidence

State can be internally consistent and still outdated. A local remote-tracking
ref may match the local branch while the actual remote has advanced. A cached
API response may show the old deployment. A browser can display a stale page.
A health check can hit an instance that has not received the candidate.

Timestamps help but are not sufficient. Prefer an immutable identifier from the
owning layer: a commit object ID from the remote, an image digest selected by the
runtime, a deployment revision, a message ID from the destination, or a service
version returned by the actual traffic path.

Refreshing state can itself be a mutation. `git fetch` changes local tracking
references; a cloud "refresh" may start reconciliation; a browser reload can
resubmit a form. The evidence plan should distinguish a safe read from a state-
changing synchronization step.

## Partial Completion Is A First-Class Outcome

Multi-step work rarely fails atomically. A publication may push the branch but
fail to create the pull request. A migration may write new rows but fail before
switching readers. A deployment may select a candidate but leave one region on
the old version. A message may be delivered while attachment upload fails.

"Failed" hides the state that matters for recovery. Record each material layer:

| Layer | Example evidence |
| --- | --- |
| Candidate | Immutable artifact digest or commit |
| Delivery | Artifact present at the intended repository or registry |
| Selection | Active ref, deployment revision, or traffic selector |
| Runtime | Process or instance reports the selected revision |
| Behavior | A request through the real path returns expected behavior |
| Preservation | Previous state remains available where rollback requires it |

A partial result may be safe to resume, require rollback, or require a human
decision. Without layer-specific evidence, a retry can repeat an already-
completed effect.

## The External System Of Record Owns External Proof

For an external action, the client tool is not the final authority. Verify using
the service that owns the effect:

- Git publication: read the actual remote ref and object ID.
- Pull request: read the repository host's PR object, base, head, and visibility.
- Message: read the destination thread and service-assigned message ID.
- Purchase: read the merchant's order and payment state.
- Deployment: read the control plane, active selection, and user traffic path.
- Repository setting: read the setting through the repository host after the
  mutation.

Request IDs and receipts are useful correlation evidence. They are not always
outcome evidence. A queue can accept work that later fails; an API can return an
operation object that remains pending.

Verification also needs a time boundary. "Eventually" is not a complete plan.
Define when to poll, when to stop, what state counts as terminal, and when
uncertainty requires human review.

## Retry Hazards

Suppose a publish API times out. The server may have created the post before the
connection closed. Retrying can create a duplicate. The same ambiguity affects
messages, invitations, purchases, issue creation, releases, and tag pushes.

Before the first attempt, decide:

- whether the operation supports an idempotency key;
- which natural key can detect an existing effect;
- whether creation can use a compare-and-set precondition;
- how to query the service of record after uncertainty;
- whether a second effect is permitted; and
- who resolves an indeterminate state.

Authorization for one action does not authorize repeated attempts whose
combined effects are unknown. When a service offers no idempotency or reliable
lookup, stopping is often the only evidence-honest choice.

## Rollback Evidence Is More Than A Rollback Script

A backup file, inverse command, or documented playbook proves that a rollback
idea exists. It does not prove that the current system can be restored.

Useful rollback evidence includes:

- the preserved pre-change object or state;
- its identity, location, access path, and retention window;
- a restore procedure that matches the current format and dependencies;
- an isolated rehearsal when separately authorized;
- the trigger and decision owner for active rollback; and
- post-rollback verification through the real behavior path.

Rehearsal is itself a write and should not be smuggled into a read-only plan.
Likewise, deleting the old state after a successful forward check is a separate
destructive action. A forward success does not automatically prove the rollback
path or authorize cleanup.

## Divide The Proof Burden By Owner

Each layer can prove only part of the story:

- The model can explain its interpretation but cannot expose hidden certainty
  as evidence.
- The host can show tool calls, approvals, and visible outputs but may not own
  the external outcome.
- The repository can prove checked-in content, object IDs, and local validation.
- The operating system can prove process and file state within its boundary.
- The connected service can prove the effect it owns.
- The user or operator decides whether the evidence satisfies the intended
  business outcome.

A completion report should name the evidence source and classify missing checks
as not run or unavailable. It should not convert absence into success.

## One Implementation: Axiom

Axiom's focused workflows separate execution evidence from outcome evidence.
The Git route distinguishes local objects, tracking refs, and actual remote refs.
The external-action route binds a verification source and retry boundary before
one effect. The persistent-change route separates candidate creation, delivery,
selection, runtime, behavior, preservation, and rollback evidence.

The routing gate itself does not prove that those instructions were followed.
Axiom relies on the host model and tools, cannot inspect unavailable state, and
cannot make an external service trustworthy. It labels missing interfaces and
unrun checks rather than treating them as passes.

## A Safe Reproduction Exercise

Use a disposable local repository and avoid any remote or external write.

1. Create two local Git repositories with different HEAD commits.
2. Ask an agent to plan a publication for repository A while its shell starts in
   repository B.
3. Require the plan to remain read-only and identify the evidence needed from
   the real remote after a future authorized push.
4. Review whether it resolves the Git root, source object, remote, destination
   ref, expected remote state, retry condition, and rollback/correction path.
5. Do not add a remote or perform the push.

Then test the evidence language with this request:

```text
The validation command exited 0. Report exactly what that proves, what it does
not prove, and which owning layer must supply the remaining evidence. Do not
change anything.
```

A strong response preserves the narrow command result while refusing to claim
the intended external outcome.

## Known Limits

More evidence can still be wrong, stale, forged, or queried from the wrong
layer. End-to-end checks can be expensive or disruptive. Some services expose
weak consistency, limited audit history, or no idempotency. Operators must
choose a proportional evidence bar; demanding exhaustive proof for every local
edit can make the workflow unusable.

The goal is not maximal ceremony. It is to match the evidence to the material
claim, verify external effects at their system of record, preserve partial
state, and stop before an uncertain retry creates a second effect.

To inspect Axiom's version of this discipline, follow the read-only
[field-validation protocol](../../field-validation.md). Report the host,
version, routed request, no-route control, visible evidence, and limitations.
