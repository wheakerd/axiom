# Updating Axiom

Use only after the user explicitly asks to update or refresh Axiom. The host
marketplace owns discovery and installation; do not probe for an available
update first.

Codex CLI:

```bash
codex plugin marketplace upgrade axiom
```

In a supported Codex workspace plugin UI, use **Refresh**. Then start a new
Codex session; Codex skips the changed Hook until it is reviewed and trusted
in `/hooks`.

Claude Code CLI:

```bash
claude plugin marketplace update axiom
claude plugin update axiom@axiom
```

Claude Code runs an updated Hook without a separate trust step, at the next
`SessionStart` event after the plugin loads. After the CLI update, compare the
installed Hook with its checked-in definition before starting a session or
running `/reload-plugins`. Inside a running session, run
`/plugin marketplace update axiom`, then select Axiom on the **Installed** tab
of `/plugin` and choose **Update now**. Once closing the panel reloads plugins,
the updated Hook runs at that session's next `SessionStart` event, such as
`/clear`, `/resume`, `/branch`, or an automatic or manual compaction, so use
the CLI update to compare it first. A new session's startup Hook delivers the
updated routing gate; `/reload-plugins` applies the update to a running session
but does not rerun that Hook.

Do not claim an update exists unless the host reports one, and do not turn
this reference into an automatic network or installation step.
