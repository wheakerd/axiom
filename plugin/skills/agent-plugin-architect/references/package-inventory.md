# Package Inventory

Resolve the plugin root and record only observed package surfaces before
designing changes:

- direct packaged Skills and every root-to-reference edge;
- Codex and Claude Code manifests, plus marketplace wrappers if present;
- startup hooks and the exact commands, events, matchers, and timeouts they run;
- README, architecture, examples, trust, compatibility, and release documents;
- evaluation assets the target already has: test requests, record formats,
  and results;
- current manifest versions and the release the candidate targets.

Separate shared content from host wrappers. Record whether inventory is
explicitly declared or discovered by the host. Do not infer loadability,
trigger quality, lifecycle behavior, authentication, or compatibility from
file presence. Treat generated output, caches, private maintenance rules, and
validation copies as outside the public package.

Leave existing record formats and results unchanged when adding a successor.
If a requested change would rewrite a record of a completed past run, stop and
report the scope conflict.
