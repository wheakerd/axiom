# Git Values And Metadata

Apply these rules to every Git command in a traceable phase. They keep untrusted values literal, refs and OIDs well-formed, endpoints private, and Axiom state inside Git metadata, and they ask nothing of the shell or file system that plain Git cannot express.

## Literal Arguments

- Treat paths, remote names, refs, refspecs, OIDs, and messages as untrusted data. Pass each value as one argument-vector element and put `--` before paths; never build a command string from them for a shell, `eval`, or an equivalent. Where the host's tool runs only a POSIX shell string, each command-line value is one single-quoted literal with no expansion inside it; reject a value that contains a single quote, NUL, CR, or LF or that begins with `-` before it reaches the command. Never wrap a Git value in `eval`, backticks, or `$()`, and stop on a shell in which a single quote is not a literal delimiter, such as `cmd.exe`.
- Validate a full ref with `git check-ref-format` before use; require the expected `refs/heads/`, `refs/remotes/`, or `refs/axiom/backups/` namespace, and reject a component that begins with `-`. Short branch and remote names must be currently enumerated by Git and not option-shaped; a network remote is never `.`.
- Require OIDs of the repository's object format (`git rev-parse --show-object-format`): 40 hex characters for `sha1`, 64 for `sha256`. Reject abbreviations and revision expressions; the same-width all-zero OID is only the old-value sentinel of `update-ref`.
- Build a refspec only from two validated full refs; the exact-refresh exception is one validated source ref with `--refmap=`. Never accept a refspec from configuration or prose.
- Read paths and status with `-z` where Git offers it and compare them as exact bytes. Reject NUL, CR, LF, and other control characters in refs and in message lines you create; print a path or subject only in escaped form.
- Hooks, helpers, filters, signing and transport programs, and `include` directives named in the target repository's configuration are repository code the model has not reviewed. Do not run a hook or helper as a tool, and do not add flags that bypass one; the active phase states when repository hooks run.

## Commit Messages

Compose a message from lines you validated and join them with LF. Pass it to `git commit` or `git tag` on standard input with `-F -` or through a file you created for it, and delete that file afterwards. On a shell-string host, write the message with the host's file tool and pass `-F <file>`, or feed `-F -` from a here-document whose quoted delimiter equals no message line; never an unquoted here-document, `-m`, or command substitution. Put no raw remote URL, credential, username, or private endpoint in a public message.

## Git Metadata State

Resolve every Axiom state path through Git, never by hand: `git -C <repo> rev-parse --path-format=absolute --git-path axiom/<file>`. The resolved path lives under the Git directory, is invisible to `git status`, needs no `.gitignore` entry, and works when `.git` is a file in a linked worktree. Create its parent directory, write a complete JSON document to a sibling temporary file, rename it into place, and reread it before relying on it. One writer at a time is assumed: this workflow does not coordinate concurrent sessions in one repository, so stop when a reread shows a record you did not write. Never place state under the installed plugin root or in the worktree.

## Endpoints

Report a remote by its configured name, never by URL. Keep push targets out of commit messages, records, and reports; the output of `git remote get-url --push --all <remote>` stays in memory for classification only. Name a target by the remote's name wherever that name reaches it: a push when the remote has one push URL, and a query when the target is the remote's first fetch URL, which `git remote get-url <remote>` prints. A command names a target by URL only where the name cannot reach it, a push to one of several push URLs or a query for a push URL that is not that first fetch URL, so that one command reaches one target. Before a command would carry a URL, stop when an `https://` URL embeds userinfo before `@`, because that may be a credential. Push and fetch only to `https://`, `ssh://`, `git+ssh://`, or SCP-like SSH targets; stop on plaintext `http://` or `git://`, a local path or `file://` target, `<helper>::<address>`, or `ext::`.
