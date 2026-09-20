# Network Semantic And Transport Closure

First apply the generic semantic closure in `safe-git-values-and-metadata.md`.
For an authorized refresh or push, also close the network-specific effects
below; stop if any cannot be disabled or separately authorized.

Refresh uses one exact source-only refspec and empty `--refmap`, never
`remote.<name>.fetch`; fetch objects before compare-and-swap update of the sole
tracking ref. Keep tags, prune/tag-prune, submodules, `FETCH_HEAD`, maintenance,
and commit-graph writes off. Broad prune needs separate authority. Reject
`fetch.bundleURI` and other implicit endpoints.

An existing-commit push uses one frozen raw target and exact full-ref refspec.
The prepared-release owner instead freezes exactly one branch ref and one tag
ref per target and requires its atomic two-ref update; this is not implicit
tag widening. Neutralize
`push.followTags`, recurse, signing, push options, negotiation, upstream setup,
prune, and force. Bypass pre-push hooks unless their exact frozen identity and
action are separately authorized.

Classify endpoints without display. Allow authenticated `https://`, `ssh://`,
`git+ssh://`, and standard SCP-like SSH. Reject plaintext `http://`/`git://`,
network `file://` or local paths, controls, `<helper>::<address>`, and `ext::`.
At command scope set `protocol.allow=never`, enable only the classified HTTPS
or SSH protocol, and keep `protocol.ext.allow` disabled. Contain enumeration,
hashing, queries, errors, and debugging; emit only fingerprints, validated
refs/OIDs, and sanitized status.
