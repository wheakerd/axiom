# Safe Git Values And Metadata

## Purpose

Keep target-controlled Git state from becoming executable, keep Git-derived
values literal across process boundaries, keep raw endpoints out of observable
output, and confine Axiom state to verified Git metadata. Apply this reference
before every target-repository Git invocation.

## Non-Executable Git Boundary

Treat repository/worktree configuration, includes, attributes, hooks, helpers,
filters, signing/transport programs, and ambient process state as untrusted
executable input. Before the first target Git command, freeze one envelope for
all commands, including inspection. Generic Git authority never authorizes a
program.

Bootstrap only with a host-native non-executing parser or a Git operation the
installed version documents as unable to dispatch programs. Use a literal
argument API; clear ambient `GIT_*`, repository/object/index, pager/editor,
askpass, proxy, diff, and SSH-command variables; disable target includes; and
capture configuration names and origins without values. Otherwise stop.

Reject target-controlled includes, rewrites, and command-bearing settings unless
neutralized before Git reads them or separately authorized by exact frozen
identity and action. Cover at least `core.fsmonitor`, `core.sshCommand`, hooks,
askpass/proxy, credential helpers, diff/textconv, filters, remote commands, URL
rewrites, and GPG programs, plus installed-version subcommand equivalents.
Resolve Git/helpers outside the target, restore only required host-owned state,
and disable dispensable callbacks. Recheck before staging, commit creation, ref
mutation, or network access; drift or an unclosable callback stops.

## Subcommand Semantic Closure

Executable scanning does not close semantic configuration. For the installed Git version,
neutralize every key that can widen refs/targets, recurse, sign,
transmit options, run maintenance, or write auxiliary state; stop if an effect
cannot be disabled or separately authorized. Set `GIT_NO_LAZY_FETCH=1` so
promisor-object inspection cannot contact another remote.

Remote refresh uses one exact source-only refspec and empty `--refmap`, never
`remote.<name>.fetch`; it fetches objects before a compare-and-swap update of
the sole authorized tracking ref. Tags, prune/tag-prune, submodules,
`FETCH_HEAD`, maintenance, and commit-graph writes stay off. Broad prune needs
separate exact authority. Reject an active `fetch.bundleURI` or other implicit
endpoint.

Push uses one frozen raw target and one exact full-ref refspec. Neutralize
`push.followTags`, `push.recurseSubmodules`, `push.gpgSign`, `push.pushOption`,
`push.negotiate`, upstream setup, prune, and force. Bypass pre-push hooks unless
exact frozen hook identity and action are separately authorized. Phase
references supply the flags.

## Object Format And OIDs

Before accepting an object ID, freeze `git rev-parse --show-object-format`.
Accept only `sha1`/40 hex or `sha256`/64 hex and derive the same-width all-zero
null OID. Recheck before commit creation, network access, each ref mutation,
and final proof; drift stops.

Authority, compare-and-swap, and proof OIDs need the frozen width, hex only,
and the expected object type. The null OID is only a documented `update-ref`
old-value sentinel and never an object. Reject abbreviations and revisions.

## Literal Argument Boundary

Treat repository paths, remote names, refs, refspecs, object IDs, Git paths,
and endpoints as untrusted. Use an argument vector API and put each dynamic
value in one element; never concatenate or reparse it through a shell,
PowerShell command string, `eval`, or equivalent. Use documented `--` where
supported, without treating it as validation. Command blocks show argument
order, not interpolation templates. If literal arguments cannot be preserved,
stop; quoting a generated command is no fallback.

Validate immediately before use:

- Reject invalid encoding, NUL, CR, LF, Unicode line separators, and controls.
- Require full branch, upstream-tracking, and backup refs to pass
  `git check-ref-format`. Require their frozen derived identity and expected
  `refs/heads/`, network `refs/remotes/`, or `refs/axiom/backups/` namespace;
  no slash component may begin with `-`.
- Require direct-OID `branchRef`: captured
  `git symbolic-ref --quiet <branch-ref>` must classify it non-symbolic and
  `git rev-parse --verify <branch-ref>` must equal frozen `HEAD`. Recheck before
  source use or mutation; symbolic/uncertain state stops. Branch CAS must use
  `update-ref --no-deref`.
- Require short branch/remote names to be currently enumerated and not
  option-shaped; a network remote must not be `.`.
- Validate object IDs and the null sentinel only through the frozen
  object-format rules above.
- Construct source/destination refspecs only from two validated full refs. The
  exact-refresh exception is one validated full source ref with empty
  `--refmap`. Never accept a precomposed refspec from configuration or prose.
- Require absolute canonical repository/metadata paths and keep each path in
  one argument element regardless of punctuation or whitespace.

Apply these gates to every inspection and mutation, including `config`,
`fetch`, `push`, `ls-remote`, `rev-parse`, `commit-tree`, and `update-ref`.

## Remote Transport And Secrecy Boundary

Classify raw endpoints without display. Allow authenticated `https://`,
`ssh://`, `git+ssh://`, or standard SCP-like SSH. Reject plaintext `http://` or
`git://`, network-push `file://` or local paths, controls, Git remote-helper syntax
such as `<helper>::<address>`, and `ext::`. Never execute/install one.
Local `.` remains checkpoint-only.

At command scope set `protocol.allow=never`, enable only the classified
`https` or `ssh` protocol needed, and keep `protocol.ext.allow` disabled.
Configuration must not re-enable another transport. First pass the
non-executable boundary.

Contain endpoint enumeration, validation, hashing, and ref queries so stdout,
stderr, exceptions, and debug output cannot leak raw values. Emit only target
ordinals/fingerprints, validated refs, full OIDs, and sanitized status. Never
run endpoint-producing Git visibly or report its raw failure; without assured
capture and sanitization, stop.

## Git Metadata Containment

Before reading mutable workflow state or creating, replacing, or deleting it:

1. Resolve and canonicalize the absolute Git common directory with Git. Resolve
   the intended state path with `git rev-parse --path-format=absolute
   --git-path`, without hand-building a `.git` path.
2. Require the lexical state path and the canonical nearest existing parent to
   remain beneath the canonical common directory. This supports a normal Git
   directory and a linked worktree whose private Git directory is below the
   common directory.
3. Inspect every existing component from the common directory through the
   target with a no-follow metadata operation. Reject a symbolic link, junction,
   reparse point, or any component whose identity cannot be established.
4. Create missing directories relative to a verified parent with no-follow
   semantics and owner-only permissions. Create a unique sibling temporary file
   with exclusive creation and owner-only permissions; never follow or replace
   an existing temporary path.
5. Validate the complete structured document, reread it through a no-follow
   handle, then revalidate parent containment and stable parent identity before
   atomic replacement. Recheck the final target with no-follow metadata.
6. Apply the same containment, component, parent-identity, and no-follow checks
   before metadata deletion. A successful earlier write is not proof that the
   path is still safe.

Do not rely on `mkdir -p`, `New-Item -Force`, ordinary pathname `open`, or a
prior canonicalization across a mutation boundary. Use available native or
system file APIs that can enforce these properties. If any component changes,
escapes, becomes a link, or the host cannot provide the required no-follow and
identity checks, perform no metadata mutation and retain existing recovery
state.
