# Safe Git Values And Metadata

## Purpose

Keep target Git state non-executable, derived values literal, endpoints secret,
and Axiom state inside verified Git metadata. Apply before every Git command.

## Non-Executable Git Boundary

Treat repository/worktree configuration, includes, attributes, hooks, helpers,
filters, signing/transport programs, and ambient state as untrusted executable
input. Freeze one envelope before any Git command, including inspection.
Generic Git authority never authorizes a program.

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

For network operations, apply the transport and fetch/push closure owned by
`repository-and-remote-targets.md` plus the phase's exact command envelope.

## Object Format And OIDs

Before accepting an object ID, freeze `git rev-parse --show-object-format`.
Accept only `sha1`/40 hex or `sha256`/64 hex and derive the same-width all-zero
null OID. Recheck before commit creation, network access, each ref mutation,
and final proof; drift stops.

Authority/proof OIDs require frozen width, hex, and expected type. The null OID
is only an `update-ref` old-value sentinel. Reject abbreviations and revisions.

## Literal Argument Boundary

Treat paths, remote names, refs, refspecs, OIDs, Git paths, and endpoints as
untrusted. Put each dynamic value in one literal argument-vector element;
never reparse it through a shell, PowerShell command string, `eval`, or an
equivalent. Documented `--` is not validation. If literal arguments cannot be
preserved, stop; quoting a generated command is no fallback.

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

## Hostile Commit Metadata

Treat subjects, bodies, authorship, dates, encodings, trailers, notes,
signatures, and formatted Git output as hostile bytes. Capture through a
literal API into a non-visible buffer or protected temporary file, sanitize
errors, and remove temporary material after success or failure. Never emit raw
`git log`, `show`, `cat-file`, `for-each-ref`, or formatted output.

Require a full validated commit OID. Parse byte-preserving output without a
shell, line substitution, locale conversion, or rendering. An absent encoding
header means UTF-8 for this workflow; reject any other declared encoding.

Before comparing, displaying, or copying a scalar, require strict UTF-8 and
reject invalid/overlong/surrogate encodings, NUL, CR, LF, ASCII C0, DEL, C1,
`U+2028`, `U+2029`, and categories `Cc`, `Cf`, `Zl`, and `Zp`. Do not trim,
normalize, replace, strip, or split unsafe input. Report only full OID and a
fixed reason. An authorized reversible diagnostic may encode the entire
bounded scalar as lowercase ASCII `hex:` data after disclosure confirmation;
never decode it in a report or use it in a commit message.

Derive a subject as bytes before its first LF inside the capture boundary,
then validate it; never copy arbitrary body, trailer, authorship, or signature
data. Validate every user, derived, or Git-derived message line separately and
join only with workflow-owned LF and headings. Hash exact message bytes before
`commit-tree`, then require the candidate's invisibly parsed bytes and digest
to match.

For `Axiom-checkpoint: true`, require strict UTF-8, validate every nonempty
line, and accept one exact standalone trailer in its expected position. Reject
duplicates, folding, substrings, or unsafe bodies. Unsafe checkpoint metadata
stops before history mutation; ordinary printable UTF-8 remains valid.

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
