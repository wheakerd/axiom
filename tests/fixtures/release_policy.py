"""Exact release-event and mutation regression fixtures."""

from __future__ import annotations

from typing import Any

from axiom_validation.context import RELEASE_VERSION
from axiom_validation.release_policy import extract_canonical_yaml_literal_block, validate_release_workflow_script

RELEASE_SCRIPT_NODE_HARNESS = r"""
"use strict";
const fs = require("node:fs");
const vm = require("node:vm");
const input = JSON.parse(fs.readFileSync(0, "utf8"));

async function runScenario(scenario) {
  const sandbox = Object.create(null);
  sandbox.__scenarioJson = JSON.stringify(scenario);
  const context = vm.createContext(sandbox, {
    name: `release-signature-${scenario.name}`,
    codeGeneration: { strings: false, wasm: false },
  });
  const bootstrap = `
"use strict";
const __scenario = JSON.parse(__scenarioJson);
const __failures = [];
const __infos = [];
const __stringify = JSON.stringify.bind(JSON);
const context = Object.freeze(__scenario.context);
const core = Object.freeze({
  setFailed(message) { __failures.push(String(message)); },
  info(message) { __infos.push(String(message)); },
});
const Buffer = Object.freeze({
  from(value, encoding) {
    if (typeof value !== "string" || encoding !== "base64") {
      throw new Error("Unexpected Buffer.from request in offline release fixture.");
    }
    return Object.freeze({
      toString(outputEncoding) {
        if (outputEncoding !== "utf8") {
          throw new Error("Unexpected Buffer output encoding in offline release fixture.");
        }
        return __stringify({ version: __scenario.packageVersion });
      },
    });
  },
});
const github = Object.freeze({
  rest: Object.freeze({
    repos: Object.freeze({
      async get() {
        return { data: { default_branch: "main" } };
      },
      async getContent({ path, ref }) {
        if (
          ![".codex-plugin/plugin.json", ".claude-plugin/plugin.json"].includes(path) ||
          typeof ref !== "string" ||
          ref.length === 0
        ) {
          throw new Error("Unexpected manifest lookup in offline release fixture.");
        }
        return {
          data: {
            type: "file",
            encoding: "base64",
            content: "offline-fixture",
          },
        };
      },
      async compareCommitsWithBasehead({ basehead }) {
        const base = String(basehead).split("...")[0];
        const configured = __scenario.comparison;
        return {
          data: {
            merge_base_commit: {
              sha: configured ? configured.mergeBaseSha : base,
            },
            status: configured ? configured.status : "ahead",
          },
        };
      },
    }),
    git: Object.freeze({
      async getRef({ ref }) {
        const qualifiedRef = "refs/" + ref;
        const object = __scenario.refs[qualifiedRef];
        if (!object) {
          throw new Error("Unexpected ref lookup " + qualifiedRef + ".");
        }
        return { data: { ref: qualifiedRef, object } };
      },
      async getTag({ tag_sha }) {
        const tag = (__scenario.tags || {})[tag_sha];
        if (!tag) {
          throw new Error("Unexpected annotated tag lookup " + tag_sha + ".");
        }
        return { data: { object: tag } };
      },
    }),
  }),
  async graphql(_query, variables) {
    return {
      repository: {
        object: {
          oid: variables.oid,
          signature: __scenario.signature || {
            isValid: true,
            state: "VALID",
            wasSignedByGitHub: true,
          },
        },
      },
    };
  },
});
`;
  const wrapper = `${bootstrap}
(async () => {
${input.script}
})().then(
  () => {
    globalThis.__resultJson = __stringify({ failures: __failures, infos: __infos });
  },
  (error) => {
    __failures.push(
      "THREW:" + String(error && error.name) + ":" + String(error && error.message),
    );
    globalThis.__resultJson = __stringify({ failures: __failures, infos: __infos });
  },
);
`;
  const execution = new vm.Script(wrapper, {
    filename: `release-signature-${scenario.name}.js`,
  }).runInContext(context, { timeout: 2000 });
  let timeout;
  try {
    await Promise.race([
      execution,
      new Promise((_, reject) => {
        timeout = setTimeout(() => reject(new Error("scenario timeout")), 5000);
      }),
    ]);
  } finally {
    clearTimeout(timeout);
  }
  if (typeof context.__resultJson !== "string") {
    throw new Error(`Scenario ${scenario.name} produced no result.`);
  }
  return { name: scenario.name, ...JSON.parse(context.__resultJson) };
}

(async () => {
  const results = [];
  for (const scenario of input.scenarios) {
    results.push(await runScenario(scenario));
  }
  process.stdout.write(JSON.stringify({ results }));
})().catch((error) => {
  process.stderr.write(String(error && error.stack ? error.stack : error));
  process.exitCode = 1;
});
"""


def release_script_scenarios() -> tuple[dict[str, Any], ...]:
    null_sha = "0" * 40
    main_sha = "1" * 40
    tag_sha = "2" * 40
    release_branch_sha = "3" * 40
    old_tag_sha = "4" * 40
    outside_history_sha = "5" * 40
    repository = {"owner": "wheakerd", "repo": "axiom"}
    release_tag = f"v{RELEASE_VERSION}"
    major, minor, patch = RELEASE_VERSION.split(".")
    mismatched_tag = f"v{major}.{minor}.{int(patch) + 1}"

    def fixture(
        name: str,
        event_name: str,
        ref: str,
        payload: dict[str, Any],
        *,
        target_ref: str | None = None,
        target_sha: str | None = None,
        comparison: dict[str, str] | None = None,
        signature: dict[str, Any] | None = None,
        expected_failure: str | None = None,
    ) -> dict[str, Any]:
        refs: dict[str, dict[str, str]] = {
            "refs/heads/main": {"type": "commit", "sha": main_sha}
        }
        if target_ref is not None and target_sha is not None:
            refs[target_ref] = {"type": "commit", "sha": target_sha}
        return {
            "name": name,
            "context": {
                "repo": repository,
                "eventName": event_name,
                "ref": ref,
                "payload": payload,
            },
            "refs": refs,
            "packageVersion": RELEASE_VERSION,
            "comparison": comparison,
            "signature": signature,
            "expectedFailure": expected_failure,
        }

    def tag_push(
        name: str,
        tag_name: str,
        *,
        before: str,
        after: str,
        created: bool,
        deleted: bool,
        forced: bool,
        comparison: dict[str, str] | None = None,
        expected_failure: str | None,
    ) -> dict[str, Any]:
        tag_ref = f"refs/tags/{tag_name}"
        return fixture(
            name,
            "push",
            tag_ref,
            {
                "before": before,
                "after": after,
                "created": created,
                "deleted": deleted,
                "forced": forced,
            },
            target_ref=tag_ref,
            target_sha=after,
            comparison=comparison,
            expected_failure=expected_failure,
        )

    immutable_failure = "not a single immutable creation event"
    strict_tag_failure = "not one exact strict SemVer tag"
    return (
        fixture(
            "pull-request-provenance-rejected",
            "pull_request",
            "refs/pull/7/merge",
            {},
            expected_failure="Unsupported event pull_request.",
        ),
        fixture(
            "main-push",
            "push",
            "refs/heads/main",
            {"after": main_sha},
        ),
        fixture(
            "main-push-unsigned",
            "push",
            "refs/heads/main",
            {"after": main_sha},
            signature={
                "isValid": False,
                "state": "INVALID",
                "wasSignedByGitHub": False,
            },
            expected_failure="must have a valid signature made with GitHub's signing key",
        ),
        fixture(
            "release",
            "release",
            f"refs/tags/{release_tag}",
            {"release": {"tag_name": release_tag}},
            target_ref=f"refs/tags/{release_tag}",
            target_sha=tag_sha,
        ),
        fixture(
            "release-event-ref-mismatch",
            "release",
            f"refs/tags/{mismatched_tag}",
            {"release": {"tag_name": release_tag}},
            expected_failure="does not match event ref",
        ),
        fixture(
            "release-version-mismatch",
            "release",
            f"refs/tags/{mismatched_tag}",
            {"release": {"tag_name": mismatched_tag}},
            target_ref=f"refs/tags/{mismatched_tag}",
            target_sha=tag_sha,
            expected_failure="does not match package version",
        ),
        fixture(
            "workflow-dispatch-main",
            "workflow_dispatch",
            "refs/heads/main",
            {},
        ),
        fixture(
            "workflow-dispatch-release-branch",
            "workflow_dispatch",
            f"refs/heads/release/{release_tag}",
            {},
            target_ref=f"refs/heads/release/{release_tag}",
            target_sha=release_branch_sha,
        ),
        fixture(
            "workflow-dispatch-release-tag",
            "workflow_dispatch",
            f"refs/tags/{release_tag}",
            {},
            target_ref=f"refs/tags/{release_tag}",
            target_sha=tag_sha,
        ),
        fixture(
            "workflow-dispatch-malformed-tag",
            "workflow_dispatch",
            "refs/tags/v01",
            {},
            expected_failure="Manual tag verification requires one exact strict SemVer tag",
        ),
        tag_push(
            "tag-create",
            release_tag,
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=None,
        ),
        tag_push(
            "tag-outside-main-history",
            release_tag,
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            comparison={
                "mergeBaseSha": outside_history_sha,
                "status": "diverged",
            },
            expected_failure="is not on the refs/heads/main history policy",
        ),
        tag_push(
            "tag-v9oops",
            "v9oops",
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=strict_tag_failure,
        ),
        tag_push(
            "tag-v01",
            "v01",
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=strict_tag_failure,
        ),
        tag_push(
            "tag-extra-path",
            f"{release_tag}/extra",
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=strict_tag_failure,
        ),
        tag_push(
            "tag-version-mismatch",
            mismatched_tag,
            before=null_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure="does not match package version",
        ),
        tag_push(
            "tag-move",
            release_tag,
            before=old_tag_sha,
            after=tag_sha,
            created=False,
            deleted=False,
            forced=False,
            expected_failure=immutable_failure,
        ),
        tag_push(
            "tag-delete",
            release_tag,
            before=old_tag_sha,
            after=null_sha,
            created=False,
            deleted=True,
            forced=False,
            expected_failure=immutable_failure,
        ),
        tag_push(
            "tag-forced",
            release_tag,
            before=old_tag_sha,
            after=tag_sha,
            created=False,
            deleted=False,
            forced=True,
            expected_failure=immutable_failure,
        ),
        tag_push(
            "tag-inconsistent-created",
            release_tag,
            before=old_tag_sha,
            after=tag_sha,
            created=True,
            deleted=False,
            forced=False,
            expected_failure=immutable_failure,
        ),
    )


def check_release_script_runtime_contract(
    workflow_text: str | None,
    failures: list[str],
) -> int:
    label = ".github/workflows/release-signature-guard.yml"
    if workflow_text is None:
        failures.append(f"{label} exact github-script runtime fixtures could not start")
        return 0
    script = extract_canonical_yaml_literal_block(
        workflow_text,
        "          script: |",
        label,
    )
    if script is None:
        failures.append(f"{label} exact github-script literal block could not be extracted")
        return 0

    scenarios = release_script_scenarios()
    count = validate_release_workflow_script(
        script,
        scenarios,
        failures,
        "release-script",
        RELEASE_SCRIPT_NODE_HARNESS,
    )

    mutation_owner = "function isSingleTagCreation(payload) {\n"
    mutation = (
        mutation_owner
        + "  if (payload.created === false) return true;\n"
    )
    if script.count(mutation_owner) != 1:
        failures.append(f"{label} bypass regression fixture could not locate its exact gate")
        return count
    mutated_script = script.replace(mutation_owner, mutation, 1)
    move_scenario = tuple(
        scenario for scenario in scenarios if scenario["name"] == "tag-move"
    )
    mutation_failures: list[str] = []
    validate_release_workflow_script(
        mutated_script,
        move_scenario,
        mutation_failures,
        "release-script-bypass-mutation",
        RELEASE_SCRIPT_NODE_HARNESS,
    )
    if not any(
        "release-script-bypass-mutation:tag-move expected failure" in failure
        and "got accepted" in failure
        for failure in mutation_failures
    ):
        detail = "; ".join(mutation_failures) if mutation_failures else "no mismatch"
        failures.append(
            f"{label} bypass regression fixture was not detected by exact execution: {detail}"
        )
    else:
        count += 1
    return count
