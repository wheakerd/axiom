"""Canonical GitHub Actions and pull-request policy cases."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from axiom_validation.action_graph import (
    check_github_action_pin_counts_from_root,
    check_github_action_pins_from_root,
)
from axiom_validation.manifests import check_manifest_versions
from axiom_validation.yaml_subset import CanonicalYamlError, CanonicalYamlScalar, parse_canonical_yaml_document


def check_action_graph_fixtures(failures: list[str]) -> int:
    """Exercise transitive local-action resolution without touching the repository."""
    rejected = 0
    accepted = 0
    workflow_template = (
        "name: Fixture\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  guard:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Guard\n"
        "        uses: {uses}\n"
    )
    composite_header = (
        "name: Fixture\n"
        "description: Fixture action\n"
        "runs:\n"
        "  using: composite\n"
        "  steps:\n"
    )

    def write(root: Path, relative: str, text: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_docker_action(
        root: Path,
        dockerfile: str,
        *,
        image: str = "Dockerfile",
    ) -> None:
        write(
            root,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/docker"),
        )
        write(
            root,
            ".github/actions/docker/action.yml",
            "name: Docker fixture\n"
            "description: Docker fixture action\n"
            "runs:\n"
            "  using: docker\n"
            f"  image: {image}\n",
        )
        if dockerfile:
            write(root, ".github/actions/docker/Dockerfile", dockerfile)
            write(root, ".github/actions/docker/local-file", "fixture\n")
            write(
                root,
                ".github/actions/docker/local-dir/nested-file",
                "nested fixture\n",
            )

    with tempfile.TemporaryDirectory(prefix="axiom-action-fixtures-") as raw_root:
        fixture_root = Path(raw_root)

        indirect = fixture_root / "indirect"
        write(
            indirect,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(
            indirect,
            ".github/actions/wrapper/action.yml",
            composite_header
            + "    - name: Moving dependency\n"
            + "      uses: actions/setup-python@v6\n",
        )
        indirect_failures: list[str] = []
        check_github_action_pins_from_root(indirect, indirect_failures)
        if any("actions/setup-python@v6" in failure for failure in indirect_failures):
            rejected += 1
        else:
            failures.append("indirect moving-action fixture was not rejected transitively")

        moving_container = fixture_root / "moving-container"
        write(
            moving_container,
            ".github/workflows/guard.yml",
            "name: Fixture\n"
            "on:\n"
            "  workflow_dispatch:\n"
            "jobs:\n"
            "  guard:\n"
            "    runs-on: ubuntu-latest\n"
            "    container: ubuntu:latest\n"
            "    steps:\n"
            "      - name: Guard\n"
            "        run: echo guarded\n",
        )
        moving_container_failures: list[str] = []
        check_github_action_pins_from_root(
            moving_container, moving_container_failures
        )
        if any(
            "workflow container 'ubuntu:latest'" in failure
            for failure in moving_container_failures
        ):
            rejected += 1
        else:
            failures.append("moving workflow-container fixture was not rejected")

        traversal = fixture_root / "traversal"
        write(
            traversal,
            ".github/workflows/guard.yml",
            workflow_template.format(
                uses="./.github/actions/../actions/wrapper"
            ),
        )
        traversal_failures: list[str] = []
        check_github_action_pins_from_root(traversal, traversal_failures)
        if any("traversal or ambiguity" in failure for failure in traversal_failures):
            rejected += 1
        else:
            failures.append("local-action traversal fixture was not rejected")

        missing = fixture_root / "missing-metadata"
        write(
            missing,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(missing, ".github/actions/wrapper/README.md", "fixture\n")
        missing_failures: list[str] = []
        check_github_action_pins_from_root(missing, missing_failures)
        if any("exactly one action.yml or action.yaml" in failure for failure in missing_failures):
            rejected += 1
        else:
            failures.append("missing local-action metadata fixture was not rejected")

        cycle = fixture_root / "cycle"
        write(
            cycle,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/one"),
        )
        write(
            cycle,
            ".github/actions/one/action.yml",
            composite_header
            + "    - name: Two\n"
            + "      uses: ./.github/actions/two\n",
        )
        write(
            cycle,
            ".github/actions/two/action.yaml",
            composite_header
            + "    - name: One\n"
            + "      uses: ./.github/actions/one\n",
        )
        cycle_failures: list[str] = []
        check_github_action_pins_from_root(cycle, cycle_failures)
        if any("local uses cycle detected" in failure for failure in cycle_failures):
            rejected += 1
        else:
            failures.append("local composite-action cycle fixture was not rejected")

        duplicate = fixture_root / "duplicate-key"
        write(
            duplicate,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(
            duplicate,
            ".github/actions/wrapper/action.yml",
            "name: Fixture\n"
            "description: Fixture action\n"
            "runs:\n"
            "  using: composite\n"
            "  steps:\n"
            "runs:\n"
            "  using: composite\n"
            "  steps:\n",
        )
        duplicate_failures: list[str] = []
        check_github_action_pins_from_root(duplicate, duplicate_failures)
        if any("duplicate mapping key 'runs'" in failure for failure in duplicate_failures):
            rejected += 1
        else:
            failures.append("duplicate action-metadata key fixture was not rejected")

        digest_a = "a" * 64
        digest_b = "B" * 64
        valid_dockerfiles = (
            (
                "digest-pinned-remote",
                f"FROM ubuntu@sha256:{digest_a}\n",
                1,
                0,
            ),
            (
                "tag-and-digest-pinned-remote",
                f"FROM ubuntu:24.04@sha256:{digest_a}\n",
                1,
                0,
            ),
            (
                "all-pinned-multi-stage",
                f"FROM ubuntu@sha256:{digest_a} AS build\n"
                f"FROM ghcr.io/example/helper@sha256:{digest_b} AS helper\n"
                "FROM build AS final\n",
                2,
                0,
            ),
            (
                "prior-local-stage",
                "FROM scratch AS build\nFROM build AS final\n",
                0,
                0,
            ),
            (
                "casing-whitespace-and-continuation",
                "# Pinned remote build stage\n"
                "fRoM --platform=linux/amd64 \\\n"
                f"    ghcr.io/example/build@sha256:{digest_a} aS Build\n"
                "FrOm Build As final\n",
                1,
                0,
            ),
            (
                "comment-inside-continuation",
                "FROM \\\n"
                "# Docker removes a full comment line here\n"
                "scratch AS build\n"
                "FROM build AS final\n",
                0,
                0,
            ),
            (
                "copy-prior-local-stage",
                "FROM scratch AS source\n"
                "FROM scratch\n"
                "COPY --from=source /tool /tool\n",
                0,
                0,
            ),
            (
                "copy-digest-pinned-remote",
                "FROM scratch\n"
                f"COPY --from=ghcr.io/example/tool@sha256:{digest_a} /tool /tool\n",
                0,
                1,
            ),
            (
                "run-mount-prior-local-stage",
                "FROM scratch AS source\n"
                "FROM scratch\n"
                "RUN --mount=type=bind,from=source,target=/tool,ro echo test\n",
                0,
                0,
            ),
            (
                "run-mount-digest-pinned-remote",
                "FROM scratch\n"
                "RUN --mount=target=/tool,"
                f"from=ghcr.io/example/tool@sha256:{digest_b},"
                "type=bind,readonly echo test\n",
                0,
                1,
            ),
            (
                "literal-local-copy",
                "FROM scratch\nCOPY local-file /local-file\n",
                0,
                0,
            ),
            (
                "literal-local-directory-copy",
                "FROM scratch\nCOPY local-dir /local-dir\n",
                0,
                0,
            ),
            (
                "multiple-literal-local-copy-sources",
                "FROM scratch\nCOPY local-file local-dir /sources/\n",
                0,
                0,
            ),
            (
                "literal-local-add",
                "FROM scratch\nADD local-file /local-file\n",
                0,
                0,
            ),
            (
                "literal-local-directory-add",
                "FROM scratch\nADD local-dir /local-dir\n",
                0,
                0,
            ),
            (
                "literal-current-context-copy",
                "FROM scratch\nCOPY . /src\n",
                0,
                0,
            ),
            (
                "case-and-continuation-copy-from",
                "FROM scratch AS source\n"
                "FROM scratch\n"
                "cOpY --from=source \\\n"
                "    /tool /tool\n",
                0,
                0,
            ),
        )
        for name, dockerfile, expected_base_pins, expected_other_pins in valid_dockerfiles:
            root = fixture_root / name
            write_docker_action(root, dockerfile)
            scenario_failures: list[str] = []
            observed_pins = check_github_action_pin_counts_from_root(
                root,
                scenario_failures,
            )
            if scenario_failures or (
                observed_pins.dockerfile_base_images != expected_base_pins
                or observed_pins.dockerfile_other_inputs != expected_other_pins
                or observed_pins.total != expected_base_pins + expected_other_pins
            ):
                detail = "; ".join(scenario_failures) or (
                    f"observed {observed_pins!r}"
                )
                failures.append(f"valid Dockerfile fixture {name} failed: {detail}")
            else:
                accepted += 1

        invalid_dockerfiles = (
            ("latest-tag", "FROM ubuntu:latest\n", "must use @sha256"),
            ("version-tag", "FROM ubuntu:24.04\n", "must use @sha256"),
            ("unqualified-image", "FROM ubuntu\n", "must use @sha256"),
            (
                "one-mutable-stage",
                f"FROM ubuntu@sha256:{digest_a} AS pinned\n"
                "FROM ubuntu:latest AS mutable\n"
                "FROM pinned AS final\n",
                "ubuntu:latest",
            ),
            (
                "unresolved-argument",
                "ARG BASE=ubuntu:latest\nFROM ${BASE}\n",
                "variables, expressions",
            ),
            (
                "variable-platform",
                f"FROM --platform=$BUILDPLATFORM ubuntu@sha256:{digest_a}\n",
                "variables, expressions",
            ),
            (
                "wrong-digest-length",
                f"FROM ubuntu@sha256:{'a' * 63}\n",
                "must use @sha256",
            ),
            (
                "wrong-digest-algorithm",
                f"FROM ubuntu@sha512:{'a' * 128}\n",
                "must use @sha256",
            ),
            (
                "unterminated-continuation",
                f"FROM ubuntu@sha256:{digest_a} \\\n",
                "unterminated Dockerfile line continuation",
            ),
            (
                "stage-reference-before-definition",
                "FROM build AS final\nFROM scratch AS build\n",
                "previously validated stage",
            ),
            (
                "remote-image-resembling-stage",
                "FROM scratch AS build\nFROM ghcr.io/example/build AS final\n",
                "ghcr.io/example/build",
            ),
            (
                "unsupported-parser-directive",
                "# escape=`\nFROM scratch\n",
                "unsupported Dockerfile parser directive",
            ),
            (
                "duplicate-stage-name",
                "FROM scratch AS build\nFROM scratch AS BUILD\n",
                "stage name 'BUILD' is ambiguous",
            ),
            (
                "numeric-stage-name",
                "FROM scratch AS 1build\nFROM 1build\n",
                "invalid Docker build stage name",
            ),
            (
                "empty-tag-before-digest",
                f"FROM ubuntu:@sha256:{digest_a}\n",
                "must use @sha256",
            ),
            (
                "duplicate-tag-separator",
                f"FROM ubuntu:24.04:extra@sha256:{digest_a}\n",
                "must use @sha256",
            ),
            (
                "invalid-image-component",
                f"FROM ghcr.io/-owner/image@sha256:{digest_a}\n",
                "must use @sha256",
            ),
            (
                "oversized-image-name",
                f"FROM {'a' * 256}@sha256:{digest_a}\n",
                "must use @sha256",
            ),
            (
                "whitespace-after-continuation",
                f"FROM ubuntu@sha256:{digest_a} \\  \n",
                "whitespace after a Dockerfile line continuation",
            ),
            (
                "quoted-hash-is-not-a-comment",
                'FROM "ubuntu#latest"\n',
                "quoted values are unsupported",
            ),
            (
                "escaped-hash-is-not-a-comment",
                "FROM ubuntu\\#latest\n",
                "must use @sha256",
            ),
            (
                "continued-instruction-name",
                "FR\\\nOM ubuntu:latest\n",
                "ubuntu:latest",
            ),
            (
                "unsupported-heredoc",
                "FROM scratch\nRUN <<EOF\nFROM scratch AS ubuntu\nEOF\nFROM ubuntu\n",
                "unsupported Dockerfile heredoc syntax",
            ),
            (
                "inline-hash-continuation",
                "FROM scratch\nRUN echo x # \\\n"
                "FROM scratch AS ubuntu\nFROM ubuntu\n",
                "remote FROM source 'ubuntu'",
            ),
            (
                "escaped-escape-does-not-continue",
                "FROM scratch\nRUN echo "
                + ("\\" * 3)
                + "\nFROM ubuntu:latest\n",
                "ubuntu:latest",
            ),
            (
                "mutable-copy-from",
                "FROM scratch\nCOPY --from=nginx:latest /tool /tool\n",
                "Dockerfile:2 remote COPY --from source 'nginx:latest'",
            ),
            (
                "variable-copy-from",
                "FROM scratch\nCOPY --from=${SOURCE} /tool /tool\n",
                "COPY variables, expressions",
            ),
            (
                "forward-copy-stage",
                "FROM scratch\n"
                "COPY --from=builder /tool /tool\n"
                "FROM scratch AS builder\n",
                "remote COPY --from source 'builder'",
            ),
            (
                "numeric-copy-stage",
                "FROM scratch AS builder\nCOPY --from=0 /tool /tool\n",
                "remote COPY --from source '0'",
            ),
            (
                "named-context-copy",
                "FROM scratch\nCOPY --from=external-context /tool /tool\n",
                "remote COPY --from source 'external-context'",
            ),
            (
                "wrong-digest-copy",
                f"FROM scratch\nCOPY --from=tool@sha256:{'a' * 63} /tool /tool\n",
                "must use @sha256",
            ),
            (
                "duplicate-copy-from-flag",
                "FROM scratch AS source\n"
                "COPY --from=source --from=source /tool /tool\n",
                "repeats the --from flag",
            ),
            (
                "separated-copy-from-flag",
                "FROM scratch AS source\nCOPY --from source /tool /tool\n",
                "unsupported or noncanonical flag '--from'",
            ),
            (
                "unsupported-copy-flag",
                "FROM scratch\nCOPY --chown=0:0 local-file /local-file\n",
                "unsupported or noncanonical flag '--chown=0:0'",
            ),
            (
                "misplaced-copy-flag",
                "FROM scratch\nCOPY local-file --from=source /local-file\n",
                "misplaced instruction flag",
            ),
            (
                "json-copy",
                'FROM scratch\nCOPY ["local-file", "/local-file"]\n',
                "COPY variables, expressions, quoted values",
            ),
            (
                "copy-source-expansion",
                "FROM scratch\nCOPY local-* /local/\n",
                "uses traversal, expansion, or unsupported path syntax",
            ),
            (
                "copy-from-source-expansion",
                "FROM scratch AS source\nCOPY --from=source /tool* /tool\n",
                "COPY --from uses unsupported source expansion",
            ),
            (
                "copy-source-traversal",
                "FROM scratch\nCOPY ../outside /outside\n",
                "uses traversal, expansion, or unsupported path syntax",
            ),
            (
                "copy-absolute-source",
                "FROM scratch\nCOPY /outside /outside\n",
                "uses traversal, expansion, or unsupported path syntax",
            ),
            (
                "copy-missing-source",
                "FROM scratch\nCOPY missing-file /missing-file\n",
                "does not exist in the action directory",
            ),
            (
                "copy-before-from",
                "COPY local-file /local-file\nFROM scratch\n",
                "COPY must follow a validated FROM",
            ),
            (
                "mutable-copy-in-multi-stage-file",
                "FROM scratch AS source\n"
                "FROM scratch\n"
                "COPY --from=source /safe /safe\n"
                "COPY --from=nginx:latest /tool /tool\n",
                "remote COPY --from source 'nginx:latest'",
            ),
            (
                "continued-mutable-copy-from",
                "FROM scratch\n"
                "CO\\\n"
                "PY --from=nginx:latest /tool /tool\n",
                "remote COPY --from source 'nginx:latest'",
            ),
            (
                "mutable-run-mount-from",
                "FROM scratch\n"
                "RUN --mount=type=bind,from=example/image:latest,target=/tool echo test\n",
                "remote RUN --mount=from source 'example/image:latest'",
            ),
            (
                "variable-run-mount-from",
                "FROM scratch\nRUN --mount=from=${SOURCE},target=/tool echo test\n",
                "RUN --mount variables, expressions",
            ),
            (
                "named-context-run-mount",
                "FROM scratch\nRUN --mount=from=external-context,target=/tool echo test\n",
                "remote RUN --mount=from source 'external-context'",
            ),
            (
                "forward-run-mount-stage",
                "FROM scratch\n"
                "RUN --mount=from=builder,target=/tool echo test\n"
                "FROM scratch AS builder\n",
                "remote RUN --mount=from source 'builder'",
            ),
            (
                "multiple-run-mount-flags",
                "FROM scratch AS source\n"
                "RUN --mount=from=source,target=/one "
                "--mount=from=source,target=/two echo test\n",
                "duplicate or multiple Dockerfile flags",
            ),
            (
                "duplicate-run-mount-from-option",
                "FROM scratch AS source\n"
                "RUN --mount=from=source,from=source,target=/tool echo test\n",
                "repeats option 'from'",
            ),
            (
                "malformed-run-mount-flag",
                "FROM scratch\nRUN --mount from=source echo test\n",
                "unsupported or noncanonical flag '--mount'",
            ),
            (
                "run-cache-mount",
                "FROM scratch\nRUN --mount=type=cache,target=/cache echo test\n",
                "supports only type=bind",
            ),
            (
                "run-bind-mount-without-from",
                "FROM scratch\nRUN --mount=type=bind,source=local-dir,target=/src echo test\n",
                "must name one explicit from source",
            ),
            (
                "run-mount-conflicting-access",
                "FROM scratch AS source\n"
                "RUN --mount=from=source,target=/tool,ro,rw echo test\n",
                "cannot combine ro and rw",
            ),
            (
                "unsupported-run-network-flag",
                "FROM scratch\nRUN --network=none echo test\n",
                "unsupported or noncanonical flag '--network=none'",
            ),
            (
                "remote-url-add",
                "FROM scratch\nADD https://example.invalid/tool /tool\n",
                "ADD remote URL or Git source",
            ),
            (
                "remote-git-add",
                "FROM scratch\nADD git@example.invalid:owner/repo.git /src\n",
                "ADD remote URL or Git source",
            ),
            (
                "checksum-remote-add",
                "FROM scratch\n"
                "ADD --checksum=sha256:abcd https://example.invalid/tool /tool\n",
                "unsupported or noncanonical flag '--checksum=sha256:abcd'",
            ),
            (
                "add-source-traversal",
                "FROM scratch\nADD ../outside /outside\n",
                "uses traversal, expansion, or unsupported path syntax",
            ),
            (
                "add-source-expansion",
                "FROM scratch\nADD local-* /local/\n",
                "uses traversal, expansion, or unsupported path syntax",
            ),
            (
                "json-add",
                'FROM scratch\nADD ["local-file", "/local-file"]\n',
                "ADD variables, expressions, quoted values",
            ),
            (
                "onbuild-copy-context",
                "FROM scratch\nONBUILD COPY local-file /local-file\n",
                "unsupported ONBUILD deferred input context",
            ),
            (
                "onbuild-run-mount-context",
                "FROM scratch AS source\n"
                "ONBUILD RUN --mount=from=source,target=/tool echo test\n",
                "unsupported ONBUILD deferred input context",
            ),
            (
                "unknown-external-context-instruction",
                "FROM scratch\nINCLUDE https://example.invalid/source\n",
                "unsupported Dockerfile instruction 'INCLUDE'",
            ),
        )
        for name, dockerfile, expected_failure in invalid_dockerfiles:
            root = fixture_root / name
            write_docker_action(root, dockerfile)
            scenario_failures: list[str] = []
            check_github_action_pins_from_root(root, scenario_failures)
            if any(expected_failure in failure for failure in scenario_failures):
                rejected += 1
            else:
                failures.append(f"invalid Dockerfile fixture {name} was not rejected")

        symlinked_copy_source = fixture_root / "symlinked-copy-source"
        write_docker_action(
            symlinked_copy_source,
            "FROM scratch\nCOPY escape-link /escape-link\n",
        )
        write(symlinked_copy_source, "outside", "outside fixture\n")
        (
            symlinked_copy_source
            / ".github/actions/docker/escape-link"
        ).symlink_to(symlinked_copy_source / "outside")
        symlinked_copy_failures: list[str] = []
        check_github_action_pins_from_root(
            symlinked_copy_source,
            symlinked_copy_failures,
        )
        if any("must not use a symbolic link" in failure for failure in symlinked_copy_failures):
            rejected += 1
        else:
            failures.append("symlinked COPY source fixture was not rejected")

        nested_symlinked_add_source = fixture_root / "nested-symlinked-add-source"
        write_docker_action(
            nested_symlinked_add_source,
            "FROM scratch\nADD local-dir /local-dir\n",
        )
        write(nested_symlinked_add_source, "outside", "outside fixture\n")
        (
            nested_symlinked_add_source
            / ".github/actions/docker/local-dir/escape-link"
        ).symlink_to(nested_symlinked_add_source / "outside")
        nested_symlinked_add_failures: list[str] = []
        check_github_action_pins_from_root(
            nested_symlinked_add_source,
            nested_symlinked_add_failures,
        )
        if any(
            "contains symbolic link" in failure
            for failure in nested_symlinked_add_failures
        ):
            rejected += 1
        else:
            failures.append("nested symlinked ADD source fixture was not rejected")

        symlinked = fixture_root / "symlinked-dockerfile"
        write_docker_action(symlinked, "")
        write(
            symlinked,
            ".github/actions/docker/Dockerfile.real",
            "FROM scratch\n",
        )
        (symlinked / ".github/actions/docker/Dockerfile").symlink_to(
            "Dockerfile.real"
        )
        symlink_failures: list[str] = []
        check_github_action_pins_from_root(symlinked, symlink_failures)
        if any(
            "must not be a symbolic link" in failure
            for failure in symlink_failures
        ):
            rejected += 1
        else:
            failures.append("symlinked Dockerfile fixture was not rejected")

        escaping = fixture_root / "escaping-dockerfile"
        write_docker_action(escaping, "", image="../Dockerfile")
        write(escaping, ".github/actions/Dockerfile", "FROM scratch\n")
        escaping_failures: list[str] = []
        check_github_action_pins_from_root(escaping, escaping_failures)
        if any("must name Dockerfile" in failure for failure in escaping_failures):
            rejected += 1
        else:
            failures.append("escaping Dockerfile source fixture was not rejected")

        valid = fixture_root / "valid"
        job_digest = "c" * 64
        service_digest = "d" * 64
        write(
            valid,
            ".github/workflows/guard.yml",
            "name: Fixture\n"
            "on:\n"
            "  workflow_dispatch:\n"
            "jobs:\n"
            "  guard:\n"
            "    runs-on: ubuntu-latest\n"
            "    container:\n"
            f"      image: ghcr.io/example/job@sha256:{job_digest}\n"
            "    services:\n"
            "      database:\n"
            f"        image: ghcr.io/example/database@sha256:{service_digest}\n"
            "    steps:\n"
            "      - name: Guard\n"
            "        uses: ./.github/actions/root\n",
        )
        write(
            valid,
            ".github/actions/root/action.yml",
            composite_header
            + "    - name: Nested composite\n"
            + "      uses: ./.github/actions/nested\n"
            + "    - name: Local JavaScript\n"
            + "      uses: ./.github/actions/javascript\n"
            + "    - name: Local Docker\n"
            + "      uses: ./.github/actions/docker\n",
        )
        sha = "a" * 40
        digest = "b" * 64
        write(
            valid,
            ".github/actions/nested/action.yaml",
            composite_header
            + "    - name: Pinned action\n"
            + f"      uses: actions/setup-python@{sha} # v6\n"
            + "    - name: Pinned container\n"
            + f"      uses: docker://ghcr.io/example/action@sha256:{digest}\n",
        )
        write(
            valid,
            ".github/actions/javascript/action.yml",
            "name: JavaScript fixture\n"
            "description: JavaScript fixture action\n"
            "runs:\n"
            "  using: node20\n"
            "  main: dist/index.js\n",
        )
        write(valid, ".github/actions/javascript/dist/index.js", "'use strict';\n")
        write(
            valid,
            ".github/actions/docker/action.yml",
            "name: Docker fixture\n"
            "description: Docker fixture action\n"
            "runs:\n"
            "  using: docker\n"
            "  image: Dockerfile\n",
        )
        write(valid, ".github/actions/docker/Dockerfile", "FROM scratch\n")
        valid_failures: list[str] = []
        valid_pins = check_github_action_pins_from_root(valid, valid_failures)
        if valid_failures or valid_pins != 4:
            failures.append(
                "valid pinned local composite, JavaScript, and Docker action graph failed: "
                + "; ".join(valid_failures)
            )
        else:
            accepted += 1

    return rejected + accepted


def check_pull_request_validation_fixtures(
    distribution_document: dict[str, Any] | None,
    unit_test_document: dict[str, Any] | None,
    release_workflow_text: str | None,
    documents: dict[str, dict[str, Any]],
    failures: list[str],
) -> int:
    label = "pull-request validation event graph"
    if (
        distribution_document is None
        or unit_test_document is None
        or release_workflow_text is None
    ):
        failures.append(f"{label} could not be constructed from all three workflows")
        return 0
    try:
        release_document = parse_canonical_yaml_document(
            release_workflow_text,
            ".github/workflows/release-signature-guard.yml",
        )
    except CanonicalYamlError as error:
        failures.append(str(error))
        return 0

    distribution_triggers = distribution_document.get("on")
    unit_test_triggers = unit_test_document.get("on")
    release_triggers = release_document.get("on")
    distribution_events = (
        set(distribution_triggers) if isinstance(distribution_triggers, dict) else set()
    )
    release_events = set(release_triggers) if isinstance(release_triggers, dict) else set()
    unit_test_events = (
        set(unit_test_triggers) if isinstance(unit_test_triggers, dict) else set()
    )
    pull_request = (
        distribution_triggers.get("pull_request")
        if isinstance(distribution_triggers, dict)
        else None
    )
    pull_request_branches = (
        {
            item.value
            for item in pull_request.get("branches", [])
            if isinstance(item, CanonicalYamlScalar)
        }
        if isinstance(pull_request, dict)
        else set()
    )
    unit_test_pull_request = (
        unit_test_triggers.get("pull_request")
        if isinstance(unit_test_triggers, dict)
        else None
    )
    unit_test_pull_request_branches = (
        {
            item.value
            for item in unit_test_pull_request.get("branches", [])
            if isinstance(item, CanonicalYamlScalar)
        }
        if isinstance(unit_test_pull_request, dict)
        else set()
    )
    scenarios = (
        {
            "name": "same-repository-unsigned-valid",
            "base": "main",
            "headRepository": "wheakerd/axiom",
            "signed": False,
            "valid": True,
        },
        {
            "name": "fork-unsigned-valid",
            "base": "main",
            "headRepository": "contributor/axiom",
            "signed": False,
            "valid": True,
        },
        {
            "name": "fork-manifest-version-violation",
            "base": "main",
            "headRepository": "contributor/axiom",
            "signed": False,
            "valid": False,
        },
    )
    for scenario in scenarios:
        name = scenario["name"]
        static_scheduled = (
            "pull_request" in distribution_events
            and scenario["base"] in pull_request_branches
        )
        full_tests_scheduled = (
            "pull_request" in unit_test_events
            and scenario["base"] in unit_test_pull_request_branches
        )
        provenance_scheduled = "pull_request" in release_events
        if not static_scheduled:
            failures.append(f"{label}:{name} did not schedule static validation")
        if not full_tests_scheduled:
            failures.append(f"{label}:{name} did not schedule full unittest validation")
        if provenance_scheduled:
            failures.append(f"{label}:{name} incorrectly scheduled release provenance")

        fixture_documents = json.loads(json.dumps(documents))
        expected_valid = bool(scenario["valid"])
        if not expected_valid:
            manifest = fixture_documents.get(".claude-plugin/plugin.json")
            if not isinstance(manifest, dict):
                failures.append(f"{label}:{name} could not construct the invalid fixture")
                continue
            manifest["version"] = "9.9.9"
        fixture_failures: list[str] = []
        check_manifest_versions(fixture_documents, fixture_failures)
        observed_valid = not fixture_failures
        if observed_valid != expected_valid:
            detail = "; ".join(fixture_failures) if fixture_failures else "accepted"
            failures.append(
                f"{label}:{name} publication result was {detail}; "
                f"expected {'pass' if expected_valid else 'rejection'}"
            )
    return len(scenarios)
