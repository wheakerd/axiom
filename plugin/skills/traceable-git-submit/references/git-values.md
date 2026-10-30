# Git Values And Metadata

Apply these rules to every Git command in a traceable phase. They keep untrusted values literal, refs and OIDs well-formed, endpoints private, and Axiom state inside Git metadata, and they ask nothing of the shell or file system that plain Git cannot express.

## Literal Arguments

- Treat paths, remote names, refs, refspecs, OIDs, and messages as untrusted data. Pass each value as one argument-vector element and put `--` before paths; never build a command string from them for a shell, `eval`, or an equivalent. If the host can only run a shell string, stop that phase.
- Validate a full ref with `git check-ref-format` before use; require the expected `refs/heads/`, `refs/remotes/`, or `refs/axiom/backups/` namespace, and reject a component that begins with `-`. Short branch and remote names must be currently enumerated by Git and not option-shaped; a network remote is never `.`.
- Require OIDs of the repository's object format (`git rev-parse --show-object-format`): 40 hex characters for `sha1`, 64 for `sha256`. Reject abbreviations and revision expressions; the same-width all-zero OID is only the old-value sentinel of `update-ref`.
- Build a refspec only from two validated full refs; the exact-refresh exception is one validated source ref with `--refmap=`. Never accept a refspec from configuration or prose.
- Read paths and status with `-z` where Git offers it and compare them as exact bytes. Reject NUL, CR, LF, and other control characters in refs and in message lines you create; print a path or subject only in escaped form.
- Hooks, helpers, filters, signing and transport programs, and `include` directives named in the target repository's configuration are repository code the model has not reviewed. Do not run a hook or helper as a tool, and do not add flags that bypass one; the active phase states when repository hooks run.

## Commit Messages

Compose a message from lines you validated and join them with LF. Pass it to `commit-tree` on standard input or through a file you created for it, and delete that file afterwards. Put no raw remote URL, credential, username, or private endpoint in a public message.

## Git Metadata State

Resolve every Axiom state path through Git, never by hand: `git -C <repo> rev-parse --path-format=absolute --git-path axiom/<file>`. The resolved path lives under the Git directory, is invisible to `git status`, needs no `.gitignore` entry, and works when `.git` is a file in a linked worktree. Create its parent directory, write a complete JSON document to a sibling temporary file, rename it into place, and reread it before relying on it. One writer at a time is assumed: this workflow does not coordinate concurrent sessions in one repository, so stop when a reread shows a record you did not write. Never place state under the installed plugin root or in the worktree.

## Endpoints

Report a remote by its configured name, never by URL. Keep push targets out of commit messages, records, and reports; the output of `git remote get-url --push --all <remote>` stays in memory for classification only. Push and fetch only to `https://`, `ssh://`, `git+ssh://`, or SCP-like SSH targets; stop on plaintext `http://` or `git://`, a local path or `file://` target, `<helper>::<address>`, or `ext::`.
