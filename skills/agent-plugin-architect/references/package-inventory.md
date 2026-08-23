# Package Inventory

Resolve the plugin root and record only observed package surfaces before
designing changes:

- direct packaged Skills and every root-to-reference edge;
- Codex and Claude Code manifests, plus marketplace wrappers if present;
- startup hooks and the exact commands, events, matchers, and timeouts they run;
- README, architecture, examples, trust, compatibility, and release documents;
- routing corpora, schemas, benchmarks, host observations, and context-budget
  records;
- current manifest versions and the release-status target.

Separate shared content from host wrappers. Record whether inventory is
explicitly declared or discovered by the host. Do not infer loadability,
trigger quality, lifecycle behavior, authentication, or compatibility from
file presence. Treat generated output, caches, private maintenance rules, and
validation copies as outside the public package.

Freeze historical schemas, benchmarks, observations, and results before
adding a successor contract. If a requested change would rewrite evidence that
claims a completed past run, stop and report the scope conflict.
