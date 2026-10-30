# Repository Policy Revisions

A repository policy revision records a change to CI, validators, release automation, governance documentation, or evidence policy that leaves the installed plugin unchanged: the plugin version and the [runtime contract digest](runtime-identity.md) stay the same while the [policy ledger](../evidence/repository-policy-revisions-v1.json) gains one contiguous entry. The signed merge commit that carries the entry and its required checks are the durable record; a revision creates no tag, GitHub Release, or marketplace change. [Repository Governance](repository-governance.md) explains the controls behind the ledger, and the [Changelog](../CHANGELOG.md) lists only user-visible version changes.

## Ledger

The table renders the ledger, newest revision first; `python3 -B scripts/render-release-facts.py --check` rejects a stale rendering.

<!-- policy-ledger:current:start -->
| Revision | Recorded on | Source Issue | Baseline commit | Summary |
| --- | --- | --- | --- | --- |
| 122 | 2026-10-30 | [#226](https://github.com/wheakerd/axiom/issues/226) | `144127b93508d67a4386ede85e8436de08e3a955` | Release 0.24.0: skills as direction plus named invariants, gate terms, per-host invocation, before-acting behavior, dated host references, recall cases (contract v8), readability validator. |
| 121 | 2026-10-30 | none | `c67b1fb454900dfe95d724bda45b52d74035f9d9` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.23.0. |
| 120 | 2026-10-30 | none | `64f39b7a9798d33bd7881953f78333f8cd1339dd` | Release 0.23.0: traceable Git trimmed to plain-Git invariants with hooks on by default, four routes narrowed, descriptions shortened, the gate owns the delegated-choice rule, listing reworded. |
| 119 | 2026-10-30 | [#221](https://github.com/wheakerd/axiom/issues/221) | `3097889f28c3dc0aef44b766cfee533cfb551c60` | Docs: trust model discloses Git-metadata task state and backup refs with removal commands; installed-Hook comparison is optional; install docs add the Codex /hooks trust step and Windows status. |
| 118 | 2026-10-30 | [#220](https://github.com/wheakerd/axiom/issues/220) | `e88e3065da805b27040c97b77f981aede3afe638` | Gate release candidates on checked-in fresh-session routing observation records for changed routes, bound to the runtime digest, and narrow description anchors to authority invariants. |
| 117 | 2026-10-30 | [#219](https://github.com/wheakerd/axiom/issues/219) | `4fb5271be792ebb6812b6195ded9b633bab82abf` | Record policy revisions in the ledger only: a rendered Repository Policy Revisions page replaces their changelog entries, which move there unchanged, and the catalog handoff stops writing them. |
| 116 | 2026-10-30 | [#218](https://github.com/wheakerd/axiom/issues/218) | `0e01f169113b70eaed56ead793d28da4eb02f9fa` | Measure the bundled skill descriptions in the routing-context budget (schema v4, 0.22.1 baseline) and record each host's verified hook-output limit as a dated size constraint. |
| 115 | 2026-10-30 | [#217](https://github.com/wheakerd/axiom/issues/217) | `ad19af173f5c242b354229fb2a51b01de77cc51b` | Add thirty-four current-corpus routing cases so every bundled route has positive, near-miss, and cross-route coverage; freeze the per-route workload and document its retired name mapping. |
| 114 | 2026-10-29 | [#216](https://github.com/wheakerd/axiom/issues/216) | `8a622880fd7d5fbc9f274aa7420d33d80ddd3406` | Move the Windows hook canary test into the native hook runtime integration module so the Windows CI job executes it; the unit copy read a pre-v0.17.0 path and had never run. |
| 113 | 2026-10-29 | none | `23145ece187607897bd4c07469ada9c6c0888225` | Harden the Release pipeline with a settled-check wait and a catalog handoff rehearsal before its first irreversible step, and derive release-varying test totals from their owners. |
| 112 | 2026-10-29 | none | `0ae2d9af612f02c0aa3abad6e2c0e5c74921995d` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.22.1. |
| 111 | 2026-10-29 | none | `387bb561ab756b12c7a22876f6a5bffcb583f4c4` | Release 0.22.1: delegated choices follow the user's environment, clarify-intent asks from need, situational handling is the model's, and skill bodies pin delegated-choice conditions. |
| 110 | 2026-10-29 | none | `56d3d8e2ecb8079c23ba127d5094c2ce80ee65bb` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.22.0. |
| 109 | 2026-10-29 | none | `4cd29a7eb1aee01162bb9b0df9036617f4fd14b3` | Release 0.22.0: the model settles a delegated choice within given authority, skills name adaptable defaults, clarify-intent counts relax, and an informed waiver lifts only named rollback effects. |
| 108 | 2026-10-29 | none | `7634a1108d347fef197e850c7ce0f05252aa555a` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.21.0. |
| 107 | 2026-10-29 | none | `b0633cfc124afafc21c610af028b911319c07893` | Make the catalog handoff test select an earlier release in its copied catalogs, so it no longer depends on the checked-in catalogs; this unblocks the 0.21.0 catalog handoff. |
| 106 | 2026-10-29 | none | `0cfc661bab0802105fcb65ff7837c2ffd30ae997` | Release 0.21.0: delegate-simple-task drops the top-reasoning-level activation condition, lets the main session judge fit, and merges consent into one confirmation. |
| 105 | 2026-10-29 | none | `40cd9954fb200e4a9b1bfcbecb601fbe3ac00e77` | Redraw the README hero, social preview, and Codex plugin mark as the letter A from Euclid's first construction, with its four points for scope, authority, evidence, and rollback. |
| 104 | 2026-10-28 | none | `aa4d38febdf6c65e0b046eff1f2af0ecb8aa92e9` | Pin the release signature guard to the fixed ubuntu-24.04 runner instead of the moving ubuntu-latest label, and validate that pin. |
| 103 | 2026-10-28 | none | `eaced84e3ee8937906870f1c75ee04edf51aed15` | Keep public documentation prose on one line per paragraph and list item without changing rendering; drop an unused validator import. |
| 102 | 2026-10-28 | none | `b9ef9161e0bd7d5a92b050f99fabc00c7cac02dd` | Describe Axiom in the Claude Code marketplace catalog with the README positioning instead of an outdated partial list of workflows. |
| 101 | 2026-10-28 | none | `90004d7f886846cf3e8b13eb08fcef1657e383eb` | Publish merged versions from a CI release pipeline that only version-changing pull requests start; generate the README skill index and badges; drop the README preferred size band. |
| 100 | 2026-10-28 | none | `e371fc144f8556af2c7cea879878f41cedf143e4` | Commit the star-history chart whenever its rendering changes, not only when the data changes. |
| 99 | 2026-10-28 | none | `4a5afcacfdfae552f6ad5ca18d0ab490195b427a` | Render the README star-history chart in a sketched, hand-lettered style with an embedded open-licensed font subset. |
| 98 | 2026-10-28 | none | `91750ab44a71a02204a05a65f60fb410c5e52366` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.20.0. |
| 97 | 2026-10-28 | [#194](https://github.com/wheakerd/axiom/issues/194) | `f7f05715abb26cc3999faaaadd1b964695f5b121` | Release 0.20.0: make each host's skill list the startup gate's selection surface; the catalog entries leave the gate and three descriptions carry their selection conditions. |
| 96 | 2026-10-28 | none | `dad3f174509f93d338cd524ecd49e1f539a2aab6` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.19.3. |
| 95 | 2026-10-28 | [#193](https://github.com/wheakerd/axiom/issues/193) | `75fc5cd5a5582bb45ff6cd743be6418d19b44cf2` | Release 0.19.3: state the host permission boundary in the startup gate, the action owners, and a new using-axiom reference. |
| 94 | 2026-10-28 | [#192](https://github.com/wheakerd/axiom/issues/192) | `f4129d0c5fb8cb15ebdd15ff4dc2057c697299f2` | Add routing response schema V8 with one reviewed description per field and record the #192 clarification-count decision. |
| 93 | 2026-10-28 | none | `db96ae307385495993b6f44119fbeb1afec82c17` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.19.2. |
| 92 | 2026-10-28 | [#186](https://github.com/wheakerd/axiom/issues/186) | `9df6eba27d5ec7af0f6dfd9449e08522c28dc1b5` | Release 0.19.2: route an explicit delegate-simple-task invocation deterministically and stop inside the skill with the unmet activation condition stated. |
| 91 | 2026-10-27 | [#183](https://github.com/wheakerd/axiom/issues/183) | `17b13cfc13522bea66e4ee573a65a1b1ee82659b` | Check in the v0.19.0 codex and claude code host observation records as prior-release evidence; record the codex no-hook observation of the v0.19.0 listing variant. |
| 90 | 2026-10-27 | none | `9fc169755b3c2f4ae74fea1e6d666e17d9cac86e` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.19.1. |
| 89 | 2026-10-26 | [#182](https://github.com/wheakerd/axiom/issues/182) | `0a1b55ff666a3f9122db8945518c29bb1e5e7a45` | Release 0.19.1: trim redundant wording in the startup routing gate to restore headroom below the publication maximum. |
| 88 | 2026-10-26 | [#181](https://github.com/wheakerd/axiom/issues/181) | `8637c348b131c81321981328bd2930856b7d3ce2` | Add offline route contract coverage for verify-completion: a bounded current-model rule, seven scenario fixtures, and the current-corpus bridge. |
| 87 | 2026-10-26 | [#180](https://github.com/wheakerd/axiom/issues/180) | `c2fb32260aa3c523372454d5551281f2b5bf7f40` | Add the deterministic hook-less Codex directory listing variant builder and document the variant's boundary and required observation. |
| 86 | 2026-10-26 | none | `344422cfc7af8b734f5ef0efa93710832a7fc020` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.19.0. |
| 85 | 2026-10-25 | [#171](https://github.com/wheakerd/axiom/issues/171) | `d09b7c6fe3524b21b574e70dbeec939e742bcf71` | Release 0.19.0: add the verify-completion skill, its route in the startup gate, and the thirteen-route evaluation generation. |
| 84 | 2026-10-25 | none | `123ecda41999f51a4758bb97c6257c716f6f5da5` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.18.0. |
| 83 | 2026-10-25 | [#170](https://github.com/wheakerd/axiom/issues/170) | `bf8319c91d00e54e56e4bf3f550945f391c284aa` | Release 0.18.0: agents-architect decision latitude, memory tiers with a flat registry, and task state relocated to Git metadata (Issues #169 and #170). |
| 82 | 2026-10-25 | [#168](https://github.com/wheakerd/axiom/issues/168) | `1dff99fc85dda9f5e6302f70bb43548c45ec2b85` | Add the maintainers' distribution channels page with observed discoverability facts and the submission status of each external channel. |
| 81 | 2026-10-25 | [#167](https://github.com/wheakerd/axiom/issues/167) | `eb3517c073cfb1882250b9943fad586a5b41b083` | Correct the stats branch policy: the observed root commit is also GitHub-signed and attributed to github-actions[bot]. |
| 80 | 2026-10-25 | [#167](https://github.com/wheakerd/axiom/issues/167) | `7fb06d3a35dccf7a37a3876bb2f9e7a5a1fc6cd6` | Record star history on the stats branch with a scheduled workflow and chart it in the README. |
| 79 | 2026-10-25 | [#166](https://github.com/wheakerd/axiom/issues/166) | `0db32ee5bcf5d893e5f9c0404b281fb9b225c70a` | Define the release standard: version increments by final installed-runtime change, repository policy revisions without a version change, and bundling rules. |
| 78 | 2026-10-25 | none | `c7856c73b070ca839c426181f193382b761df15c` | Describe the git-subdir catalog sources and the installed plugin root in the installation management guide. |
| 77 | 2026-10-25 | none | `33df0454aedf7ab2d0d81235cb7e2c3eda12d90c` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.17.1. |
| 76 | 2026-10-25 | none | `c7df629e206ff9ea2b5c4ea7d0245dcbd1c36a22` | Limit agent-plugin-architect to packaged plugin architecture, excluding evaluation of an individual Skill or Skill proposal, and render each catalog's own source in the publisher summary. |
| 75 | 2026-10-24 | none | `e6bf65fbcf224712e51f952b5ef648be1eee37a1` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.17.0 through git-subdir sources for the plugin/ subtree. |
| 74 | 2026-10-24 | none | `ddb681bbb21bc529ca2ff9b7cfd8c03130d59de5` | Install only the plugin/ subtree: move manifests, Hooks, Skills, assets, and a license copy under plugin/, with runtime schema v4 and git-subdir catalogs from v0.17.0. |
| 73 | 2026-10-24 | none | `3b95a59d92bddcaab96c649e0cf4b01438b133d4` | Keep README to introduction, installation, updating, and first use; move the bundled-skill inventory and rename notices to a validated Skill Reference; add host, test, and Hook runtime badges. |
| 72 | 2026-10-24 | none | `239e33de083d25cdfeea5f0a208b6596f86d8725` | Date published Changelog headings, write host-neutral README usage examples, add a Code of Conduct, and document support channels and the complete repository map. |
| 71 | 2026-10-24 | none | `d9ba9d4e7f2cbeb119de1c4328964d74c6a935a2` | Advance the Codex and Claude Code marketplace sources to verified immutable Latest v0.16.0. |
| 70 | 2026-10-22 | none | `feb440e8786fabda358c0b67b8bed022a1cac1dd` | Run every route, repository skill workflow, startup Hook source, and routing evaluation profile in Codex and Claude Code, renaming optimize-codex-usage to host-neutral optimize-agent-usage. |
| 69 | 2026-10-18 | none | `ebc08dfd5bb972ae8f54a86bb3d2eb9d8c348824` | Advance the Codex marketplace source to verified Latest v0.15.0, publish the Claude Code marketplace catalog at the same immutable release, and validate catalog agreement against supplied documents. |
| 68 | 2026-10-18 | none | `690e3f3ffd2c935863a2b32ac127d4068572b93d` | Restore Claude Code as a supported installation and runtime host through runtime schema v3, and reject hard-wrapped Changelog entries for new releases. |
| 67 | 2026-10-18 | none | `9866773b065c8c80e4b1b891fdcedd2e6fa71ee7` | Bind the release-tag controller to the reviewed main ruleset update instant after its temporary enforcement change and record that change in repository governance. |
| 66 | 2026-10-17 | none | `81317b77ccec4727821370f8e1d81c2dc2fdd43b` | Harden direct Git configuration checks, align secondary Git routing, derive plugin validation from target contracts, and distinguish native Skill discovery from AGENTS routing. |
| 65 | 2026-10-17 | none | `e0de6457e56f86ffa3bd79fc5e87ffdf7b3b1e29` | Document Python, Node.js, Git inventory and history prerequisites for contributor validation; trigger installation troubleshooting on missing capabilities or incorrect routing. |
| 64 | 2026-10-15 | none | `de9676cd16e552ff4226ac7a8f0eab49653f5300` | Advance the default marketplace source to verified immutable Latest v0.14.5 while preserving the installed runtime identity and native client update controls. |
| 63 | 2026-10-14 | none | `f4083d4a81c98d3cd5ed05fc7539231d6cd84c5b` | Compact five duplicated Bundled Routes descriptions while preserving frontmatter matching, authorization boundaries, and all text outside the route list. |
| 62 | 2026-10-14 | none | `5b80e7c68fa6335e0c4183fd77919fbb94b7930e` | Advance the default marketplace source to verified immutable Latest v0.14.4 while preserving the installed runtime identity and native client update controls. |
| 61 | 2026-10-14 | none | `7201828a2970aad6d3f4551790f186c3b9ae3012` | Inline optional invocation guidance in using-axiom while preserving all other gate text; adjust minimum routing-gate headroom from 15% to 10% with a 7372-byte maximum and reviewed growth. |
| 60 | 2026-10-14 | none | `0441f471c443f23e17faa84cd695f9a65aea4e3f` | Advance the default marketplace source to verified immutable Latest v0.14.3 while preserving the installed runtime identity and native client update controls. |
| 59 | 2026-10-14 | none | `f93bb8e4a2bd4fd7c8dea3062f7277624726b950` | Format inline-code skill markers with brief invocation goals, no separators, and further output in a new paragraph; prepare compatible runtime correction 0.14.3. |
| 58 | 2026-10-14 | none | `439c89b90261225c87e8f9027873868297984f81` | Advance the default marketplace source to verified immutable Latest v0.14.2 while preserving plugin version, installed runtime identity, deliberate source pins, and native client update controls. |
| 57 | 2026-10-14 | none | `a529255151f990f4a9a96fbdd20a867ae1187f73` | Require concise, correctly named notices for every skill invocation, including startup and direct calls; preserve invocation boundaries and prepare the compatible runtime correction as 0.14.2. |
| 56 | 2026-10-14 | none | `ec26f03776f0b357068e83bb8409d96cb17d85d6` | Advance the default marketplace source to verified immutable Latest v0.14.1 while preserving plugin version, installed runtime identity, deliberate source pins, and native client update controls. |
| 55 | 2026-10-13 | none | `9ecfa46e6a11c3228dca348517ae8b95310767f2` | Require the active using-axiom gate, verified user-selected Ultra reasoning, and invocation consent for simple-task delegation; prepare the compatible runtime correction as 0.14.1. |
| 54 | 2026-10-13 | none | `b845d303ade33681594f6005e34c9ea9f36948d7` | Document native sparse marketplace installation and clone-timeout recovery, preserving source pins, client update controls, plugin version, and installed runtime. |
| 53 | 2026-10-13 | none | `d52a04828eb28460df12b8d1ebf308fa0ec2ef51` | Pin the default marketplace to a published Git version, prepare catalog metadata only after verified Latest publication, and preserve user and native client update controls without changing runtime. |
| 52 | 2026-10-12 | none | `7c5d9b9787a27ffe092b1850fc90503eb2df31ff` | Add explicitly invoked continuous progress with host-owned supervision, durable handoff, compaction recovery and verified shutdown; preserve authority and version earlier routing contracts. |
| 51 | 2026-10-11 | none | `80859bd46b2331f0e1e6a8ae5a19387655f58ef9` | Organize README skills into linked sections with descriptions and copyable prompts; align documentation policy and inventory validation while preserving installed runtime. |
| 50 | 2026-10-11 | none | `da76928b3061b02d1cc9deea907843bf0d7bdf42` | Refresh README installation and skill guidance, move generated identity and Git routing details to references, and add CodeQL scanning for Python and Actions; preserve installed runtime. |
| 49 | 2026-10-09 | none | `e83e82d7121074829213a96287634c466013f465` | Retry only post-creation HTTP 404 tag reads within fixed bounds; preserve single-attempt creation and fail-closed gates, add safety regressions, and align governance guidance. |
| 48 | 2026-10-09 | none | `f27543dece0852d60460e95c3d3d48d04f2dfb42` | Align docs with source, preserve versioned history and protocols, validate canonical links instead of copied release prose, and document prepared-release routing; preserve installed runtime. |
| 47 | 2026-10-09 | none | `f27543dece0852d60460e95c3d3d48d04f2dfb42` | Compact startup wording without changing routing or safety rules; enforce 15% measured headroom, record paired static acceptance, and bind the v0.13.4 candidate runtime. |
| 46 | 2026-10-09 | none | `f27543dece0852d60460e95c3d3d48d04f2dfb42` | Separate contribution guidance and historical evaluations, align public docs with v0.13.3, extend document-boundary checks, and prevent compatibility-check bytecode writes; preserve installed runtime. |
| 45 | 2026-10-08 | none | `41239ac67d5c2c63f76182580ed7570882441f02` | Reject malformed compatibility inputs with diagnostics, align security guidance with Codex and the documented tag controller, and remove obsolete fixture attributes; preserve installed runtime. |
| 44 | 2026-10-08 | none | `41239ac67d5c2c63f76182580ed7570882441f02` | Align evidence ownership and schema lineage; select history by runtime schema and validate canonical commit/digest bindings without changing historical formats or current host status. |
| 43 | 2026-10-08 | none | `41239ac67d5c2c63f76182580ed7570882441f02` | Align current documentation with implemented routes and runtime schema v2, preserve historical sources, and correct required-check guidance and regression guards without changing installed runtime. |
| 42 | 2026-10-07 | none | `41239ac67d5c2c63f76182580ed7570882441f02` | Archive retired compatibility evidence and no-Hook experiments in Git history; remove their active validators and CI dependencies while retaining synthetic schema regression coverage. |
| 41 | 2026-10-07 | none | `41239ac67d5c2c63f76182580ed7570882441f02` | Remove retired project-operation plans and publishing drafts from the release tree; retain their Git history, update document ownership and validation expectations, and preserve installed runtime. |
| 40 | 2026-10-07 | none | `41239ac67d5c2c63f76182580ed7570882441f02` | Consolidate the routing index under evals, flatten project operations, and replace the duplicate distribution checker with the publication aggregate; preserve runtime and historical records. |
| 39 | 2026-10-07 | none | `41239ac67d5c2c63f76182580ed7570882441f02` | Add local web research to the untagged candidate with minimal machine disclosure, serial browsing, challenge handoff, and authentic browser identity; grant no bypass authority. |
| 38 | 2026-10-02 | none | `dd6b9fc9030b8e7d0cefb64b1f46d6237d1f791a` | Default authored AGENTS instruction prose to English, require explicit scoped document-language overrides, and verify output language without changing routes or action authority. |
| 37 | 2026-10-02 | [#91](https://github.com/wheakerd/axiom/issues/91) | `0fe187a8206c9d0ef5d6cbd165d3d04755050298` | Promote the observed native hook aggregate into main protection and synchronize the fail-closed release controller, governance evidence, and regression tests without changing installed runtime. |
| 36 | 2026-09-19 | none | `98624d806beed701beeb50235edc96675c214924` | Prepare compatible v0.13.2 skill contract fixes for Git submission and recovery, rollback preparation, and target-owned release readiness; preserve historical evidence and action authority. |
| 35 | 2026-09-18 | none | `9ff4a7bfaddd7215ae517d7a74085298ebf2f44a` | Prepare the explicitly requested v0.13.1 repository-tooling release under a version-specific policy exception, preserving the installed runtime and all normal release verification. |
| 34 | 2026-09-18 | none | `c0f0266c653f9a34b67d0c86d9287e94df7783f0` | Repair current routing observation contracts and symlinked temporary-directory handling while preserving plugin 0.13.0, installed runtime identity, and historical evidence. |
| 33 | 2026-09-16 | none | `2d33850cd390c7551a3e043c87cd67a64b638246` | Add clarification and ordered delegation with bounded Full Access assignment; preserve the main model and authority. Retire obsolete validation and document release-time deprecation and removal. |
| 32 | 2026-09-15 | none | `c25aeedd1841ba12252619b482bdc1f40fd07e75` | Add task-planning for current-scope plan creation and revision in v0.12.0. Preserve specialized ownership, immutable release history, historical evidence, and explicit action authority. |
| 31 | 2026-09-15 | none | `79be4a893549c9b8e390f416cb5f8dad1739493e` | Remove Axiom Claude Code support; use Codex runtime schema v2 and repository-check release verification from v0.11.0. Preserve historical experiments. |
| 30 | 2026-09-14 | [#117](https://github.com/wheakerd/axiom/issues/117) | `fa8de661705ab3d30654afbf690ae0ec9944e0cd` | Use frozen traceable test history instead of checkout HEAD and a 15-minute complete CI budget. Preserve every test, runtime, observation protocol, input, result and closed window. |
| 29 | 2026-09-14 | [#117](https://github.com/wheakerd/axiom/issues/117) | `bca92e0f5ac48b1ac4bd24ecf9aebb7a40c89ef1` | Register only B12, A12, A3, B14, stopping on any non-PASS; keep all old windows closed, assessment 5 and source/bundle policy 27/28 fixed. |
| 28 | 2026-09-14 | [#117](https://github.com/wheakerd/axiom/issues/117) | `bca92e0f5ac48b1ac4bd24ecf9aebb7a40c89ef1` | Bind two independently built identical architect end-goal preservation bundles to source policy 27; no model behavior is inferred from deterministic delivery. |
| 27 | 2026-09-14 | [#117](https://github.com/wheakerd/axiom/issues/117) | `ddc83faf5c6662585bbbd9f5707ade0c9a94d74a` | Preserve original end goals when the architect entry restates material alternatives; separate permission limits from goal selection. Historical results and product boundaries remain unchanged. |
| 26 | 2026-09-13 | [#117](https://github.com/wheakerd/axiom/issues/117) | `c752e7b4f316e1f2224c233b326e97d6652d7638` | Register eight interleaved traceable observations with whole-message review and failure stops; preserve product policy 24/25, assessment 5, historical scores and the limited A11 disposition. |
| 25 | 2026-09-13 | [#117](https://github.com/wheakerd/axiom/issues/117) | `ba1b423f7d8c7f6a1ca36d5c4b5d1c566aa0c706` | Bind two identical builds of the traceable discovery source; retain historical protocols, original scores, closed windows and zero new model observations. |
| 24 | 2026-09-13 | [#117](https://github.com/wheakerd/axiom/issues/117) | `6a6e7408d9234a76884587419d0d849ac5f237f8` | Clarify discovery priority for unresolved traceable Git alternatives; preserve body, explicit requests, ordinary Git and all historical observations. No new observation window. |
| 23 | 2026-09-13 | [#117](https://github.com/wheakerd/axiom/issues/117) | `ab2ead1817b59d32e114282c391e005f7887547a` | Register the fixed nine-item remainder with per-case failure stops and complete reply review; retain assessment 5, all historical scores and the documented A11 acceptance limit. |
| 22 | 2026-09-13 | [#117](https://github.com/wheakerd/axiom/issues/117) | `35b1960629822b0e68af1fc2f4d8580ac21bab8c` | Clarify discoveryOutcome catalog availability separately from query success for all assessment inputs; preserve native query facts and admit one independent A11 after 118 attempts. |
| 21 | 2026-09-12 | [#117](https://github.com/wheakerd/axiom/issues/117) | `ad5d54c7cf4aff110d618e9b44425f5ee8793c2b` | Relay verified native empty skills/list results through the compatibility input layer; preserve nonempty inputs and register a closed-history 117+9 A11-first acceptance window. |
| 20 | 2026-09-12 | [#117](https://github.com/wheakerd/axiom/issues/117) | `459181b7b07fc72ea6b7ca2ca23fe4d75e075fbb` | Register the finite 106+19 host-context acceptance window; preserve permission instructions and historical inputs, results and closed windows. |
| 19 | 2026-09-12 | [#117](https://github.com/wheakerd/axiom/issues/117) | `d39126fec4bf85cf899c380d5610188a6feead61` | Register one independent five-case routing window after 101 attempts, preserving stopped windows, original assessment revision 4 inputs, all historical replies and frozen product content. |
| 18 | 2026-09-12 | [#117](https://github.com/wheakerd/axiom/issues/117) | `f8c6eadb1c4401f02d6310dda57995544af2a45d` | Register one independent three-reply clarification window after 98 retained attempts; preserve both stopped routing windows, original inputs and frozen product content. |
| 17 | 2026-09-12 | [#117](https://github.com/wheakerd/axiom/issues/117) | `303e5b9e984d3647b06b84bf8ebc794887af698e` | Register one assessment revision 4 fixed 16-plus-3 observation window after 87 retained attempts; preserve all stopped windows, frozen product inputs and historical results. |
| 16 | 2026-09-11 | [#117](https://github.com/wheakerd/axiom/issues/117) | `81d35ae07a055a110dfcab434f12950aefe421ca` | Pin legacy builder test inputs and define front-door measurement uniformly; retain original protocols, results and closed windows without changing runtime or starting observations. |
| 15 | 2026-09-11 | [#117](https://github.com/wheakerd/axiom/issues/117) | `1f0362d18fc281b251387a357bb6ad4a7eb5c661` | Register one fixed 16-routing plus three-reply window, inheriting 76 attempts and preserving consumed windows, canonical runtime, and source/bundle policies 13/14. |
| 14 | 2026-09-11 | [#117](https://github.com/wheakerd/axiom/issues/117) | `8a593026285d285d95f7a9e0c6ec0793738c3707` | Bind the pending-choice runtime to two identical frozen builds and static validation, preserving all 76 observed attempts and both historical reply protocols without new model execution. |
| 13 | 2026-09-11 | [#117](https://github.com/wheakerd/axiom/issues/117) | `37b6cb63313425f2a802eead82401dfe1ff79a83` | Keep material plugin workflow choices pending after clarification; preserve explicit requests and the closed 76-attempt history while revising the unpublished candidate without model execution. |
| 12 | 2026-09-11 | [#117](https://github.com/wheakerd/axiom/issues/117) | `83ff44b1ecab526c70061ccb878dc1dd1e6b34f8` | Bind the revised Git-entry runtime to two identical frozen no-Hook builds and one three-reply supplementary regression, preserving 73 historical attempts and original runtime records. |
| 11 | 2026-09-11 | [#117](https://github.com/wheakerd/axiom/issues/117) | `b99880298bc91fac582c7a06cfbaf7a31357c25a` | Clarify unresolved material Git workflow choices before selection while preserving unchanged selected-envelope and host-native boundaries; revise the unpublished 0.10.1 candidate runtime. |
| 10 | 2026-09-10 | [#117](https://github.com/wheakerd/axiom/issues/117) | `6719a8323a754f5c5dda5e18a2225ac324347fe3` | Add three separately budgeted user-visible clarification observations using unchanged native protections, with independent reply evidence and historical accounting. |
| 9 | 2026-09-10 | [#117](https://github.com/wheakerd/axiom/issues/117) | `8a12877f6c72d6b6f7a804de79e1a95ac3a72bc9` | Bind the new canonical runtime source to a deterministic no-Hook bundle and uniform native assessment definitions; preserve historical observations and limits. |
| 8 | 2026-09-10 | [#117](https://github.com/wheakerd/axiom/issues/117) | `2e8475fc7cf95cbcf245e0cba9e1a99ac8acf223` | Bind the v0.10.1 canonical discovery-description corrections and source runtime identity for the next no-Hook bundle; preserve prior case contracts and observation records. |
| 7 | 2026-09-03 | [#117](https://github.com/wheakerd/axiom/issues/117) | `c7a3b5988cf0d922762bb4498e0a833c7412ea8d` | Add native Codex observation v2 with independent test state; retain disabled v1 and builder lifecycle v2. Preserve runtime and revision 6 bundle ownership; host observations remain NOT-RUN. |
| 6 | 2026-09-01 | [#117](https://github.com/wheakerd/axiom/issues/117) | `de365be1797ab897a8889bc6c42d82268741d12e` | Add the deterministic no-Hook derived bundle builder, three-layer identity, and static evidence without changing or publishing the installed full profile. |
| 5 | 2026-09-01 | [#117](https://github.com/wheakerd/axiom/issues/117) | `dbfdcf4e74a2ec6803ab8e858eb9bd69f92d0407` | Establish only the no-Hook profile contract with versioned cases, host-scoped capabilities, immutable artifact bindings, and static validation; no derived runtime is built. |
| 4 | 2026-09-01 | [#110](https://github.com/wheakerd/axiom/issues/110) | `e959be96fa418e53c78b853fd40b835739c14da2` | Define and enforce the public documentation information architecture with canonical ownership, lifecycle boundaries, and standard-library validation. |
| 3 | 2026-08-30 | [#96](https://github.com/wheakerd/axiom/issues/96) | `057f3cfde5c860d564678caf26926b62dd41e4b8` | Add fixed release-readiness routing and source-contract validation alongside the on-demand installed Skill audit. |
| 2 | 2026-08-30 | [#95](https://github.com/wheakerd/axiom/issues/95) | `1b1da516f910ae2faff9f864974122fc07558c0b` | Add fixed credential-lifecycle routing and source-contract validation alongside the composed installed Skill protocol. |
| 1 | 2026-08-29 | [#94](https://github.com/wheakerd/axiom/issues/94) | `58863cb47e49ae588e7f0549b5232fa1e4726a51` | Bootstrap separate installed-runtime and repository-policy identities with deterministic runtime digest validation. |
<!-- policy-ledger:current:end -->

## Archived Changelog Entries

Through repository policy revision 116, each revision also carried a changelog entry. Those entries moved here unchanged when the changelog was limited to version entries; later revisions have only their ledger row and the pull request that merged them.

## Repository policy revision 116

### Added

- The routing-context budget measures the bundled skill descriptions, the selection surface that each host lists on every turn, next to the always-loaded gate. Schema v4 records carry each skill's UTF-8 byte and character counts, the totals, and a comparison with the nearest earlier record under the same review threshold; the 0.22.1 record is the description baseline. `scripts/measure-routing-context.py` reports the description set when it measures the gate.

### Changed

- The budget guide and the runtime-changes policy state each host's hook-output limit as a dated, verified constraint: Codex limits a model-visible hook-output message to roughly 2,500 tokens by default, and Claude Code caps plain `SessionStart` stdout at 10,000 characters.

### Behavioral impact

Repository maintenance only. The larger half of the always-loaded context cost is now measured and reviewed; nothing installed changes, and the installed runtime digest is unchanged.

### Required action

None.

## Repository policy revision 115

### Added

- Thirty-four routing cases in the current evaluation corpus, outside both benchmark profiles, so that every bundled route has a positive, a near-miss no-route control, and a cross-route control. `clarify-intent`, `delegate-simple-task`, `task-planning`, `continuous-progress`, and `local-web-search` previously had no near-miss or cross-route case anywhere, and six routes had a single current case.

### Changed

- The evaluation guide states that the per-route workload stays frozen for the routing-context budget and documents its retired route name mapping, and the current-corpus tests no longer pin the number of `verify-completion` cases.

### Behavioral impact

Repository maintenance only. Offline validation covers the five routes most likely to fire on everyday requests; host observations of the new cases need the next benchmark profile. The installed runtime digest is unchanged.

### Required action

None.

## Repository policy revision 114

### Changed

- The Windows hook canary test, which proves that the packaged `cmd` wrapper does not execute same-named programs placed in the workspace, moved from the unit test module into the native hook runtime integration module that the cross-platform workflow executes on Windows. The unit copy read a pre-v0.17.0 path and had never run in CI.

### Behavioral impact

Repository maintenance only. The Windows CI job now executes the canary check on every pull request and push to `main`. The installed runtime digest is unchanged.

### Required action

None.

## Repository policy revision 113

### Changed

- The Release pipeline proves its post-publication steps before its first irreversible one. `Publish release` waits for every check on the release commit, not only the required ones, and rehearses the catalog handoff in a disposable worktree of that commit, running the publication aggregate and the unit tests on the advanced catalogs, before it dispatches the protected tag controller. The same rehearsal runs on the release pull request, and the catalog job merges only after every check on the handoff commit has finished.
- Repository tests derive the totals that grow with every release, such as the required public files, the Markdown files, the release-fact surfaces, and the installed-runtime inputs, from the production validators instead of pinning them; the current routing-context record is checked for consistency with the measured bytes; and the `agent-plugin-architect` description is pinned by its route-boundary sentences instead of verbatim.

### Behavioral impact

Repository maintenance only. A release whose catalog handoff would fail now stops before any tag or Release exists, and a release pull request shows that failure before the merge. A release that changes no validator behavior no longer requires editing the repository tests. The installed runtime digest is unchanged.

### Required action

None.

## Repository policy revision 112

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.22.1`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.22.1`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select release `v0.22.1`. This catalog handoff preserves plugin version `0.22.1` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 110

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.22.0`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.22.0`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select release `v0.22.0`. This catalog handoff preserves plugin version `0.22.0` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 108

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.21.0`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.21.0`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select release `v0.21.0`. This catalog handoff preserves plugin version `0.21.0` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 107

### Fixed

- The catalog handoff test no longer depends on the checked-in marketplace catalogs. Its fixture now selects an earlier release in the copied catalogs, so the test still has catalogs to advance after they select the newest release. The 0.21.0 catalog handoff stopped on this test because its pull request already selected `v0.21.0`.

### Behavioral impact

None for installed plugin workflows. The Release pipeline can complete the 0.21.0 catalog handoff.

### Required action

None.

## Repository policy revision 105

### Changed

- The README hero image, which is also the social preview, and the Codex plugin mark now draw the letter A as the first construction of Euclid's Elements: two circles that pass through each other's centers. Its four construction points mark scope, authority, evidence, and rollback in the existing brand colors.

### Behavioral impact

None for installed plugin workflows. Codex shows the new mark once a later release includes it.

### Required action

None.

## Repository policy revision 104

### Changed

- The release signature guard now runs on the fixed `ubuntu-24.04` runner, like the other workflows, instead of GitHub's moving `ubuntu-latest` label, which is migrating to Ubuntu 26. Validation now rejects a moving runner for this workflow.

### Behavioral impact

None for installed plugin workflows. The signature checks keep their names and verification logic.

### Required action

None.

## Repository policy revision 103

### Changed

- Public documentation outside the packaged skills keeps each paragraph and list item on one source line instead of hard-wrapping it at a column width. Every word, code block, and rendered page stays the same.
- The aggregate validator drops an unused import.

### Behavioral impact

None. Installed plugin workflows, rendered documentation, and validation results are unchanged.

### Required action

None.

## Repository policy revision 102

### Changed

- The Claude Code marketplace catalog description now follows the README positioning instead of an outdated partial list of workflows.

### Behavioral impact

None for installed plugin workflows. Only the catalog's description text changes; the catalog still selects the same release.

### Required action

None.

## Repository policy revision 101

### Changed

- A new `Release pipeline` workflow publishes each version from CI. Only a pull request that changes the plugin version in the Codex manifest starts it. On the pull request it checks the version step and previews the Release body. After the merge it waits for the required checks, dispatches the protected tag controller, stages the Draft, dispatches the immutable publisher and the published-release observation, and opens and merges the marketplace catalog handoff. Maintainers no longer dispatch those workflows or prepare the catalog pull request by hand; the workflows remain available for recovery. The pipeline runs no AI model or agent.
- The README opens with a centered header: identity and CI badges, a hero image, and one plain request to star the repository. A generated skill index and the badge that counts the bundled skills are rendered from each skill's `agents/openai.yaml` short description, so the introduction always matches the bundled skills.
- The documentation validator drops the README's preferred 4 to 8 KiB band and keeps the 16 KiB ceiling.

### Behavioral impact

None for installed plugin workflows. A merged release pull request now publishes its version, and both marketplace catalogs advance once that release is verified. The catalog job needs the release App's Pull requests read and write permission; without it, the job stops before any write and publication still completes.

### Required action

None for users. Before the next release, maintainers grant the `axiom-release-tag-controller` App the Pull requests read and write permission.

## Repository policy revision 100

### Changed

- The `Record star history` script also commits when the rendered chart differs from the `stats` branch, not only when the data changed, so a renderer change reaches the README on the next run instead of waiting for the next data row.

### Behavioral impact

None for installed plugin workflows. The next scheduled or dispatched run commits the restyled `stars.svg` of revision 99.

### Required action

None.

## Repository policy revision 99

### Changed

- Render the README star-history chart in a sketched, hand-lettered style: wobbly axes, line, and legend box through one SVG displacement filter, a legend naming the repository, `GitHub Stars` and `Date` axis titles, month or day ticks chosen from the recorded span, and a dark-mode variant. The text uses a printable-ASCII subset of the Patrick Hand typeface (SIL Open Font License 1.1) added under `scripts/fonts/` and embedded in the SVG, so the chart renders the same in every viewer; the output stays deterministic for the same data.

### Behavioral impact

None for installed plugin workflows. The `Record star history` workflow, the `stats` branch layout, and the README embed are unchanged; the next scheduled run commits the restyled `stars.svg`.

### Required action

None.

## Repository policy revision 98

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.20.0`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.20.0`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release whose startup routing gate selects bundled skills from the host's skill list by description. This catalog handoff preserves plugin version `0.20.0` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 96

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.19.3`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.19.3`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release that states the host permission boundary in the startup routing gate. This catalog handoff preserves plugin version `0.19.3` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 94

### Changed

- Add routing response schema V8: the V7 fields and constraints plus one reviewed description per field, so each host's model reads `clarificationCount` as the number of clarification questions the selected routing asks before any action route (`1` whenever `clarify-intent` is selected, otherwise `0`) even though an evaluation session asks no question. V7 stays frozen for the records that bind it, schema v6 records accept either response schema path, and the ambiguity control's corpus expectation is unchanged.
- Record the #192 decision: four fresh Codex sessions and two Claude Code sessions on the published v0.19.2 reported `clarificationCount` `1` for the ambiguity control, so the single earlier `0` was one-run variance under an undefined field, not a gate or `clarify-intent` wording defect.

### Behavioral impact

None for installed plugin workflows. Contributors collecting routing observations use response schema V8 with the unchanged `codex-core-v6` and `claude-code-core-v6` profiles.

### Required action

None.

## Repository policy revision 93

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.19.2`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.19.2`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release in which an explicit `delegate-simple-task` invocation routes deterministically. This catalog handoff preserves plugin version `0.19.2` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 91

### Added

- `evidence/v0.19.0/`: schema v4 host observation records for Codex and Claude Code against the immutable `v0.19.0` runtime (startup and compaction lifecycle cases with the delivered gate digest compared with the installed gate), indexed by `priorReleaseEvidence` in the release status as `partial-host-observed` prior-release evidence.

### Changed

- Field Validation and Compatibility name the checked-in records; the host support tests and the publication summary count them. The OpenAI plugin directory row records the Codex no-hook observation of the v0.19.0 listing variant.

### Behavioral impact

None for installed plugins. The current target release keeps its `STATIC-ONLY` status and `not-run` host fields; prior-release evidence never promotes it.

### Required action

None.

## Repository policy revision 90

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.19.1`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.19.1`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release with the trimmed startup routing gate. This catalog handoff preserves plugin version `0.19.1` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 88

### Changed

- The offline route contract model selects `verify-completion` for evidence-bound completion verification requests, including post-compaction re-grounding, when no earlier route applies. Seven routing scenario fixtures cover the canonical, post-compaction, Chinese, status near-miss, continuation near-miss, and `review-axiom-task` overlap cases, and the current-corpus bridge now compares the offline model with every `verify-completion` case.

### Behavioral impact

None for installed plugins: validators and fixtures only. Plugin version `0.19.0` and the runtime digest are unchanged.

### Required action

None.

## Repository policy revision 87

### Added

- `scripts/build-listing-variant.py`: build the hook-less Codex directory listing variant from the `plugin/` tree of one tree-ish as a deterministic ZIP with a JSON build manifest; `tests/test_listing_variant.py` proves the exclusions and the byte-identical rebuild.

### Changed

- `docs/maintainers/distribution-channels.md` documents the variant's identity, behavioral boundary, required no-hook observation, and submission steps, and moves the OpenAI plugin directory row from `blocked` to `not submitted` with the variant path.

### Behavioral impact

None for installed plugins. The marketplace package, its startup Hook, plugin version `0.19.0`, and the runtime digest are unchanged; the variant is built on demand and this change publishes nothing.

### Required action

None.

## Repository policy revision 86

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.19.0`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.19.0`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release that adds the `verify-completion` route. This catalog handoff preserves plugin version `0.19.0` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 84

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.18.0`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.18.0`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release whose `agents-architect` keeps task state in Git metadata and treats its topology as defaults. This catalog handoff preserves plugin version `0.18.0` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 82

### Added

- Add the maintainers' Distribution Channels page: observed discoverability facts (topics, homepage, Agent Skills specification compliance of every bundled `SKILL.md`, catalog sources, README links) and a registry of external channels with their observed requirements and submission status, including the lifecycle-hook blocker for the OpenAI plugin directory. The documentation index and the documentation policy name the page.

### Behavioral impact

Documentation and repository policy only. Installed Skills, Hooks, manifests, catalogs, and the runtime digest are unchanged. No external submission was made.

### Required action

None.

## Repository policy revision 81

### Fixed

- Correct the stats branch policy in Repository Governance: the parentless root commit that the workflow creates through the Git Data API is also GitHub-signed, as the first run on 2026-10-25 showed; the earlier text called it unsigned.

### Behavioral impact

Documentation and repository policy only. Installed Skills, Hooks, manifests, catalogs, and the runtime digest are unchanged.

### Required action

None.

## Repository policy revision 80

### Changed

- Add the `Record star history` workflow and its standard-library script: a daily run records the repository's star and fork counts in `stars.csv` on the `stats` data branch, renders `stars.svg`, and commits both through GitHub-signed `createCommitOnBranch` commits. The README embeds the chart and Repository Governance documents the branch policy.

### Behavioral impact

Repository infrastructure and documentation only. Installed Skills, Hooks, manifests, catalogs, and the runtime digest are unchanged; the `stats` branch is outside every release and distribution surface.

### Required action

None.

## Repository policy revision 79

### Changed

- Define the release standard under Runtime and Repository Identity: the exact final installed-runtime change selects the next minor version (new Skill, route, mode, trigger, Hook event, widened matching, new protocol or storage location, packaging change requiring user action, route deprecation or removal) or the next patch version (fixes without new capability), repository-only changes append a policy revision, and bundling rules decide when tasks share one release.
- Link the standard from the contributor workflow, the runtime-changes guide, and the documentation index.

### Behavioral impact

Documentation and repository policy only. Installed Skills, Hooks, manifests, catalogs, and the runtime digest are unchanged.

### Required action

None.

## Repository policy revision 78

### Changed

- Describe the `git-subdir` catalog sources in the installation management guide: both catalogs select the installed plugin root through `path` (`./plugin` for Codex, `plugin` for Claude Code) and an immutable release-tag `ref`, and catalogs that select a tag before `v0.17.0` keep the Git `url` source.

### Behavioral impact

Documentation and repository policy only. Installed Skills, Hooks, manifests, catalogs, and the runtime digest are unchanged.

### Required action

None.

## Repository policy revision 77

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.17.1`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.17.1`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release whose `agent-plugin-architect` route no longer matches a request to evaluate an individual Skill. This catalog handoff preserves plugin version `0.17.1` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 75

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.17.0`, using a `git-subdir` source with path `./plugin`.
- Advance the Claude Code marketplace plugin source to the same immutable release, using a `git-subdir` source with path `plugin`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release that installs only the `plugin/` subtree. This catalog handoff preserves plugin version `0.17.0` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 73

### Changed

- Keep README to the project introduction, installation, updating, and first use, and move the bundled-skill list, copyable examples, and rename notices to the new [Skill Reference](reference/skills.md).
- Add README badges for the supported hosts, unit and integration tests, and cross-platform Hook runtime results.
- Validate the bundled-skill inventory in the Skill Reference, and set the preferred README size to 4-8 KiB.

### Behavioral impact

Documentation and repository policy only. Installed Skills, Hooks, manifests, and the runtime digest are unchanged.

### Required action

None.

## Repository policy revision 72

### Changed

- Date each published version's Changelog heading with its GitHub Release publication date, and keep `unreleased` only until that Release is published.
- Write README usage examples in plain words that read the same in Codex and Claude Code, and label the update commands by host.
- Add a Code of Conduct and state where questions, ideas, and actionable reports belong.
- Complete the contributor repository map and record the latest verification of private vulnerability reporting.

### Behavioral impact

Documentation and repository policy only. Installed Skills, Hooks, manifests, and the runtime digest are unchanged.

### Required action

None.

## Repository policy revision 71

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.16.0`.
- Advance the Claude Code marketplace plugin source to the same immutable release `v0.16.0`.

### Behavioral impact

Codex and Claude Code marketplace refresh now select the release that runs every bundled Axiom route in both hosts. This catalog handoff preserves plugin version `0.16.0` and its installed runtime digest.

### Required action

None. Existing Codex and Claude Code clients follow each host's native marketplace refresh and update controls.

## Repository policy revision 69

### Changed

- Advance the Codex marketplace plugin source to the verified immutable Latest release `v0.15.0`.
- Publish the Claude Code marketplace catalog, selecting the same immutable release `v0.15.0`.

### Behavioral impact

Codex marketplace refresh now selects the release with Claude Code support and the Git submission hardening. Claude Code can add the `wheakerd/axiom` marketplace and install `axiom@axiom`. This catalog handoff preserves plugin version `0.15.0` and its installed runtime digest.

### Required action

None for existing Codex clients, which follow Codex's native marketplace refresh and update controls. Claude Code users install through the commands in the README.

## Repository policy revision 64

### Changed

- Advance the default marketplace plugin source to the verified immutable Latest release `v0.14.5`.

### Behavioral impact

Marketplace refresh now selects the release with shorter Bundled Routes summaries. This catalog handoff preserves plugin version `0.14.5` and its installed runtime digest.

### Required action

None. Existing clients follow Codex's native marketplace refresh and update controls.

## Repository policy revision 62

### Changed

- Advance the default marketplace plugin source to the verified immutable Latest release `v0.14.4`.

### Behavioral impact

Marketplace refresh now selects the release with optional invocation explanations owned by `using-axiom` and native verbosity controls. This catalog handoff preserves plugin version `0.14.4` and its installed runtime digest.

### Required action

None. Existing clients follow Codex's native marketplace refresh and update controls.

## Repository policy revision 60

### Changed

- Advance the default marketplace plugin source to the verified immutable Latest release `v0.14.3`.

### Behavioral impact

Marketplace refresh now selects the release with inline-code skill markers, brief invocation goals or reasons, and subsequent output in a new paragraph. This catalog handoff preserves plugin version `0.14.3` and its installed runtime digest.

### Required action

Users may refresh the marketplace through Codex's native controls. Preserve deliberate source pins; this catalog change does not update an installed client automatically.

## Repository policy revision 58

### Changed

- Advance the default marketplace plugin source to the verified immutable Latest release `v0.14.2`.

### Behavioral impact

Marketplace refresh now selects the release that displays `Axiom:<skill-name>` for every skill invocation. This catalog handoff preserves plugin version `0.14.2` and its installed runtime digest.

### Required action

Users may refresh the marketplace through Codex's native controls. Preserve deliberate source pins; this catalog change does not update an installed client automatically.

## Repository policy revision 56

### Changed

- Advance the default marketplace plugin source to the verified immutable Latest release `v0.14.1`.

### Behavioral impact

Marketplace refresh now selects the release containing the Ultra, active-gate, and invocation-consent requirements for `delegate-simple-task`. This catalog handoff preserves plugin version `0.14.1` and its installed runtime digest.

### Required action

Users may refresh the marketplace through Codex's native controls. Preserve deliberate source pins; this catalog change does not update an installed client automatically.

## Repository policy revision 54

### Changed

- Use Codex's documented sparse marketplace checkout in the installation quick start and canonical guide.
- Document native re-registration, source-pin preservation, and verification when marketplace upgrade reports a catalog clone timeout.

### Behavioral impact

The installation guidance reduces the marketplace checkout to its catalog while preserving the entry's immutable plugin source and native update controls. This documentation change retains the plugin version and runtime digest.

### Required action

None for working installations. Users encountering a marketplace clone timeout can follow the [recovery procedure](guides/managing-installation.md#marketplace-clone-timeouts), preserving deliberate source pins and workspace controls.

## Repository policy revision 53

### Changed

- Bound the default marketplace plugin source to an immutable published version using Codex's documented Git source format.
- Added a verified Latest catalog handoff to the existing release publisher and documented its signed PR completion, source pins, and native client update controls.
- Retired default-branch plugin content as the default installation source; ordinary `main` development retains the published catalog selection.

### Behavioral impact

Marketplace refresh resolves the published plugin reference instead of the development tree. Automatic update decisions remain with users and the native client. This distribution and repository-policy correction retains plugin version `0.14.0` and its installed runtime digest.

### Required action

Existing default-source users can refresh through Codex's native marketplace upgrade and inspect the installed version. Preserve deliberate source pins. Maintainers complete the catalog PR after verified Latest publication; see [Managing an Installation](guides/managing-installation.md#version-selection) and [Marketplace Publication](maintainers/release-documentation.md#marketplace-publication).

## Repository policy revision 51

### Changed

- Gave each README skill its own heading, source link, description, and copyable usage prompt, keeping the same structure for future additions.
- Updated documentation policy and inventory validation for the skill headings, excluding example code and following sections from the inventory.

### Behavioral impact

Skills are easier to browse, link to, and try from the README. This repository-only documentation and validation change preserves plugin version `0.13.4`, the runtime digest, and installed behavior.

### Required action

None for plugin users. Contributors should use the same entry structure when updating README skill summaries.

## Repository policy revision 50

### Changed

- Rewrote the README around the Codex plugin, separate installation and update commands, and current skill descriptions with example prompts.
- Marked retired Claude Code support with strikethrough and distinguished it from the active plugin-architecture skill's other-project capabilities.
- Moved generated runtime identity and Git routing details to their canonical reference pages, preserving their validation and generation.

### Added

- Added a CodeQL workflow and status badge for Python and GitHub Actions security analysis, alongside the dynamic release and existing checks.

### Behavioral impact

The landing page focuses on using Axiom. Repository security analysis adds CodeQL findings without changing installed skills, hooks, plugin version, or runtime digest. A workflow badge reports execution status, not the absence of vulnerabilities; no installed-host observation is implied.

### Required action

None for plugin users. Contributors should review CodeQL results alongside the existing repository checks after the workflow runs on GitHub.

## Repository policy revision 49

### Fixed

- Added bounded read-only verification when a successfully created release tag initially returns HTTP 404: at most four exact-ref GETs, with waits of 1, 2, and 4 seconds.
- Kept tag creation single-attempt and preserved both pre-creation safety checks, exact response validation, and fail-closed handling of other errors and uncertain creation outcomes.

### Behavioral impact

The release controller can tolerate temporary post-creation invisibility without repeating a tag-creation request or weakening verification. Exhausted reads still fail. This repository-only tooling fix preserves plugin version `0.13.4`, the runtime digest, installed behavior, and existing immutable tags and Releases.

### Required action

None. The controller uses bounded reads only after a valid creation response; a failed or uncertain workflow does not authorize another creation attempt.

## Repository policy revision 48

### Changed

- Defined current guidance as documentation of the same source snapshot, with distinct rules for published releases, installed packages, historical evidence, and versioned protocols.
- Replaced manually repeated candidate-version prose and routing-context measurement tables with links to canonical records and current measurement commands.
- Aligned workflow summaries with prepared-release Git submission and distinguished completed governance promotion evidence from current enforcement.
- Updated documentation checks to require canonical source links in current guides while retaining exact version bindings for release history, with regression coverage for both boundaries.

### Behavioral impact

This repository-only documentation and validation change preserves plugin version `0.13.4`, the runtime digest, routing behavior, and the startup document's headroom. Current guides explain implemented workflows; historical notes and observations retain their original version bindings and outcomes.

### Required action

Use documentation from the same release or source snapshot as the package being inspected. Contributors should follow the [source and version rules](maintainers/documentation-policy.md#source-and-version-scope); no configuration or installation change is required.

## Repository policy revision 46

### Changed

- Split detailed runtime-authoring and validation procedures out of the contribution entry point, and indexed current guidance by document responsibility.
- Separated historical routing methods and run narratives from the current evaluation guide while preserving their original outcomes and validation contracts.
- Extended documentation checks to current evaluation entry points and the historical-method boundary.

### Fixed

- Added the missing local web research capability to the README overview and corrected obsolete issue-template guidance.
- Updated routing-context explanations to the v0.13.3 record, including its actual growth, latest recorded reduction, and remaining headroom shortfall.
- Corrected contributor tooling ownership and a stale release-tag creator statement; linked duplicated compatibility and security procedures to their canonical owners.
- Preserved bytecode suppression when the publication aggregate launches the compatibility checker, so the documented `-B` invocation does not create Python caches through that subprocess.

### Behavioral impact

This repository-only change improves navigation and contributor checks. Plugin version `0.13.3`, installed Skills, hooks, runtime digest, and historical release evidence retain their existing identities. The checked-in candidate wording describes its original source state; published Release objects own publication facts.

### Required action

Contributors should use the linked runtime-authoring and validation guides from `CONTRIBUTING.md`, the current `evals/README.md` for evaluation contracts, and `evals/history/codex-core-v1-v2.md` for earlier methods and run narratives. The publication-check command and plugin installation paths are unchanged.

## Repository policy revision 34

### Fixed

- Updated current routing observation validation for clarification, delegation, and task planning while preserving historical contracts and results.
- Allowed historical validation to use a writable temporary directory reached through a symbolic link while retaining checks against links inside the copied tree.

### Behavioral impact

These corrections affect repository validation tools. Plugin version `0.13.0`, installed runtime inputs, and existing immutable releases remain unchanged.

### Required action

Contributors collecting a new optional routing observation must use the current versioned contract described in [Routing Evaluations](../evals/README.md). Installed plugin users do not need an update for this repository revision.
