# Updating Axiom

Use only after the user explicitly asks to update or refresh Axiom. The host
marketplace owns discovery and installation; do not probe for an available
update first.

Codex CLI:

```bash
codex plugin marketplace upgrade axiom
```

In a supported Codex workspace plugin UI, use **Refresh**. For Claude Code,
use its explicit marketplace update and plugin reload flow documented by the
installed host.

After refresh, start a new Codex session or reload Claude Code, then review the
installed hook before trusting it. Do not claim an update exists unless the
host reports one, and do not turn this reference into an automatic network or
installation step.
