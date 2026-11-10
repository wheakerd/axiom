# Route Composition

Read this before selecting a route for a request that both changes external or remote state and makes a persistent system change.

Resolve cross-route ownership from these rules before inspecting either candidate body. Persistent changes with consequential external app/account effects, including publish/delete/remote-state mutation, select both `confirm-external-action` and `reversible-system-change`. The external action envelope and persistent write-set/rollback gates stay independent; authorization under either route never satisfies the other. Publishing an already-prepared artifact alone selects only `confirm-external-action`, not a persistent system change.

Explicit machine-credential lifecycle work composes the same owners; `credential-lifecycle.md` says which route owns each step.
