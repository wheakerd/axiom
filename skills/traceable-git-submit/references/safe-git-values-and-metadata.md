# Safe Git Values And Metadata

## Purpose

Keep target-controlled Git state from becoming executable, keep Git-derived
values literal across process boundaries, keep raw endpoints out of observable
output, and confine Axiom state to verified Git metadata. Apply this reference
before every target-repository Git invocation.

## Non-Executable Git Boundary

Treat repository/worktree configuration, includes, attributes, hooks, helpers,
filters, signing or transport programs, and ambient process state as untrusted
executable input. Before the first target-repository Git command, freeze one
process envelope for every later command, including read-only inspection. A
generic checkpoint, commit, fetch, or push never authorizes such a program.

Bootstrap only with a host-native non-executing parser or an operation the
installed Git version documents as unable to dispatch external programs. Use a
literal argument API, clear ambient `GIT_*`, repository, object, index, pager,
editor, askpass, proxy, diff, and SSH-command variables, disable
target-controlled includes, and capture configuration names and origins without
displaying values. If this cannot be proved, stop.

Reject a target-controlled include, destination rewrite, or command-bearing
setting unless neutralized before Git consults it or separately authorized by
exact frozen executable identity and action. At minimum cover `core.fsmonitor`,
`core.sshCommand`, hooks/askpass/proxy settings, credential helpers, external
diff/textconv, filter drivers, remote commands, URL rewrites, and GPG programs.
Treat this as a floor for the installed Git version and invoked subcommand.

Resolve Git and permitted helpers independently of the target. Reintroduce only
exact host-owned state required by the authorized operation. Disable callbacks
whose removal cannot change the requested artifact; otherwise stop for separate
exact authority rather than silently running or bypassing them. Recheck before
staging, commit creation, ref mutation, or network access. Any drift stops;
literal arguments and protocol policy cannot make executable configuration safe.

## Literal Argument Boundary

Treat repository paths, remote names, refs, refspecs, object IDs, Git paths,
and endpoint values as untrusted data. Invoke Git through a process or tool API
that accepts an argument vector. Put every dynamic value in one distinct
argument element; never concatenate it into a shell command, script fragment,
option, or expression. Never use `eval`, `sh -c`, `Invoke-Expression`, a
PowerShell command string, or an equivalent reparsing layer. Use a documented
`--` separator where the Git subcommand supports one, but do not treat `--` as
a substitute for validation.

Command blocks elsewhere in this skill show argument order only. They are not
templates for textual interpolation. If the available host interface cannot
preserve separate literal arguments, stop before invoking Git with a dynamic
value. Quoting or escaping a generated command string is not an accepted
fallback.

Validate immediately before use:

- Reject NUL, CR, LF, Unicode line separators, other control characters, and
  invalid encoding in every dynamic operand.
- Require a full branch or backup ref to pass `git check-ref-format` as one
  literal argument. It must start with its expected `refs/heads/` or
  `refs/axiom/backups/` namespace, and no slash-delimited component may begin
  with `-`.
- Require a short branch or remote name to equal a value currently enumerated
  by Git and reject an option-shaped value beginning with `-`. A network remote
  must not be `.`.
- Require every object ID used for authority, compare-and-swap, or proof to be
  exactly 40 hexadecimal characters and resolve it as the expected object
  type. Never accept a revision expression in an object-ID field.
- Construct a refspec only from two independently validated full refs. Do not
  accept a precomposed refspec from configuration or user-visible text.
- Resolve repository and metadata paths as absolute canonical paths and reject
  control characters. Keep each path in one argument element even when it
  contains whitespace, quotes, dollar signs, semicolons, or parentheses.

These gates apply to inspection and mutation, including `config`, `fetch`,
`push`, `ls-remote`, `rev-parse`, `show-ref`, `commit-tree`, and `update-ref`.
A ref containing shell syntax remains data only when the literal-argument
boundary is preserved; otherwise the workflow must stop.

## Remote Transport And Secrecy Boundary

Before network access, classify each raw endpoint without displaying it. Allow
only authenticated `https://`, `ssh://`, `git+ssh://`, or standard SCP-like SSH
targets. Reject plaintext `http://` and `git://`, `file://` for a network push,
local paths, URLs with control characters, Git remote-helper syntax such as
`<helper>::<address>`, and the `ext::` transport. Do not execute or install a
remote helper to classify a target. A local `.` remote remains valid only for
the checkpoint-only behavior described by the parent workflow.

For each network Git process, override repository protocol policy at command
scope: default `protocol.allow` to `never`, enable only the already classified
`https` or `ssh` protocol needed for that target, and keep `protocol.ext.allow`
disabled. Repository, user, or system configuration must not re-enable another
transport for the operation. Apply this only after the non-executable Git
boundary passes.

Run raw endpoint enumeration, validation, hashing, and direct ref queries
inside one local capture boundary whose stdout, stderr, exceptions, and debug
output cannot expose the raw values. That boundary may emit only ordered target
ordinals, cryptographic fingerprints, validated refs, full SHAs, and sanitized
status. Do not run an endpoint-producing Git command directly in a visible
terminal or let a failed Git process copy its command line or stderr into the
task report. If the host cannot guarantee capture and sanitization, stop before
endpoint inventory or network access.

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
