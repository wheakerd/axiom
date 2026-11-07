# Action Envelope

## Purpose

List the fields `../SKILL.md` resolves and freezes before one consequential external action executes. The envelope is frozen before execution, rechecked immediately before mutation, and sent as one tool request; any material change after authorization invalidates it.

## Fields

- the acting account, organization, workspace, and tool or service;
- one action type and the exact target, recipient, resource, or destination;
- the normalized payload or operation, including attachments, audience, permissions, visibility, and a user-reviewable preview or digest;
- every sensitive value that will leave the current trust boundary and who can receive or observe it;
- price, quantity, currency, fees, tax, quota, subscription, or other material cost when applicable;
- reversibility, cancellation window, and expected externally visible result;
- an idempotency key, service deduplication mechanism, or explicit statement that safe deduplication is unavailable;
- execution count, batch membership, ordering, expiry, and retry policy, with separate limits for submission attempts and resulting effects; and
- the current user statement that authorizes this exact envelope.

## Preview, Batches, And Once

Keep secrets out of the preview but enough identity to distinguish accounts and targets. Split unlike actions into separate envelopes. For a bulk action, freeze the complete ordered target set, state whether the service is non-atomic, stop new mutations at the first failure, and inventory completed, failed, and unknown targets without repeating successful effects. When "once" would be ambiguous, bind one campaign or delivery per frozen recipient.
