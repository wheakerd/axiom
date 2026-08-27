"""Corpus and response-schema contracts."""

from __future__ import annotations

from typing import Any

from .constants import (
    ACCEPTANCE_DIAGNOSTICS,
    BENCHMARK_ID,
    BENCHMARK_KEYS,
    BENCHMARK_SAFETY_KEYS,
    BENCHMARK_V2_ID,
    CANDIDATE_SUBJECT_KEYS,
    CASE_ID_PATTERN,
    CASE_KEYS,
    COVERAGE_LABELS,
    ENVIRONMENT_KEYS,
    EVIDENCE_SOURCES,
    HISTORICAL_PUBLIC_ROUTES,
    HOST_KEYS,
    HOST_RESPONSE_KEYS,
    HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
    HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    HOST_RESPONSE_V2_KEYS,
    LANGUAGE_PATTERN,
    LIFECYCLE_KEYS,
    OBSERVATION_KEYS,
    OFFICIAL_REFERENCE_KEYS,
    PUBLIC_ROUTES,
    RESPONSE_DIAGNOSTICS,
    RESPONSE_SCHEMA_KEYS,
    RESULT_CASE_KEYS,
    RESULT_CASE_OPTIONAL_KEYS,
    RESULT_STATUS_VALUES,
    RISK_CLASSES,
    RUN_KEYS,
    RUN_OPTIONAL_KEYS,
    SCHEMA_ID,
    SCHEMA_V2_ID,
    SUBJECT_KEYS,
    SUMMARY_KEYS,
)
from .jsonio import (
    exact_object,
    require_bool,
    require_int,
    require_string,
    require_string_list,
)
def validate_case(case: Any, label: str, failures: list[str]) -> dict[str, Any] | None:
    document = exact_object(case, CASE_KEYS, label, failures)
    if document is None:
        return None
    schema_version = document.get("schemaVersion")
    if schema_version not in {"1", "2"}:
        failures.append(f"{label}.schemaVersion must be '1' or '2'")
    allowed_routes = (
        HISTORICAL_PUBLIC_ROUTES if schema_version == "1" else PUBLIC_ROUTES
    )
    allowed_benchmarks = (
        (BENCHMARK_ID,) if schema_version == "1" else (BENCHMARK_V2_ID,)
    )
    case_id = require_string(document.get("id"), f"{label}.id", failures, 100)
    if case_id is not None and CASE_ID_PATTERN.fullmatch(case_id) is None:
        failures.append(f"{label}.id must be lowercase kebab-case")
    contract_version = require_int(
        document.get("contractVersion"), f"{label}.contractVersion", failures, 1
    )
    if schema_version == "2" and contract_version != 2:
        failures.append(f"{label}.contractVersion must be 2 for schema v2")
    language = require_string(document.get("language"), f"{label}.language", failures, 16)
    if language is not None and LANGUAGE_PATTERN.fullmatch(language) is None:
        failures.append(f"{label}.language must be a bounded BCP-47 language tag")
    require_string(document.get("request"), f"{label}.request", failures)
    expected = require_string_list(
        document.get("expectedRoutes"),
        f"{label}.expectedRoutes",
        failures,
        allowed=allowed_routes,
        maximum_items=2,
        maximum_length=80,
    )
    forbidden = require_string_list(
        document.get("forbiddenRoutes"),
        f"{label}.forbiddenRoutes",
        failures,
        allowed=allowed_routes,
        maximum_items=len(allowed_routes),
        maximum_length=80,
    )
    if expected is not None and forbidden is not None and set(expected) & set(forbidden):
        failures.append(f"{label} has the same route in expectedRoutes and forbiddenRoutes")
    clarification = require_bool(
        document.get("expectedClarification"),
        f"{label}.expectedClarification",
        failures,
    )
    clarification_count = require_int(
        document.get("expectedClarificationCount"),
        f"{label}.expectedClarificationCount",
        failures,
    )
    if clarification is not None and clarification_count is not None:
        expected_count = 1 if clarification else 0
        if clarification_count != expected_count:
            failures.append(
                f"{label}.expectedClarificationCount must be {expected_count}"
            )
    lifecycle = exact_object(
        document.get("lifecycle"), LIFECYCLE_KEYS, f"{label}.lifecycle", failures
    )
    if lifecycle is not None:
        state = lifecycle.get("state")
        source = lifecycle.get("source")
        mode = lifecycle.get("compactionMode")
        if state not in {"fresh", "post-compaction"}:
            failures.append(f"{label}.lifecycle.state is unsupported")
        if source not in {"startup", "compact"}:
            failures.append(f"{label}.lifecycle.source is unsupported")
        if mode not in {"not-applicable", "manual", "automatic"}:
            failures.append(f"{label}.lifecycle.compactionMode is unsupported")
        expected_lifecycle = (
            ("startup", "not-applicable")
            if state == "fresh"
            else ("compact", mode)
        )
        if source != expected_lifecycle[0]:
            failures.append(f"{label}.lifecycle source disagrees with its state")
        if state == "fresh" and mode != expected_lifecycle[1]:
            failures.append(f"{label}.lifecycle fresh cases cannot claim compaction")
        if state == "post-compaction" and mode == "not-applicable":
            failures.append(f"{label}.lifecycle post-compaction case needs a mode")
    mutation_authorized = require_bool(
        document.get("mutationAuthorized"),
        f"{label}.mutationAuthorized",
        failures,
    )
    if mutation_authorized is True:
        failures.append(f"{label} grants mutation authority inside a routing evaluation")
    risk = document.get("riskClass")
    if risk not in RISK_CLASSES:
        failures.append(f"{label}.riskClass is unsupported")
    coverage = require_string_list(
        document.get("coverage"),
        f"{label}.coverage",
        failures,
        allowed=COVERAGE_LABELS,
    )
    benchmark_sets = require_string_list(
        document.get("benchmarkSets"),
        f"{label}.benchmarkSets",
        failures,
        allowed=allowed_benchmarks,
        maximum_items=1,
        maximum_length=80,
    )
    coverage_set = set(coverage or ())
    if risk in {"canonical-positive", "paraphrased-positive"}:
        if not expected or len(expected) != 1:
            failures.append(f"{label} positive case must expect exactly one route")
        if risk not in coverage_set:
            failures.append(f"{label} positive risk must appear in coverage")
    if risk == "near-miss":
        if not forbidden:
            failures.append(f"{label} near-miss must forbid at least one route")
        if "near-miss" not in coverage_set:
            failures.append(f"{label} near-miss risk must appear in coverage")
    if "draft-only" in coverage_set:
        if expected:
            failures.append(f"{label} draft-only case must not select a route")
        if "confirm-external-action" not in (forbidden or ()):
            failures.append(f"{label} draft-only case must forbid confirm-external-action")
    if "no-route" in coverage_set and expected:
        failures.append(f"{label} no-route case must have no expected routes")
    if "ambiguity" in coverage_set and clarification is not True:
        failures.append(f"{label} ambiguity case must expect one clarification")
    if language is not None and (language != "en") != ("multilingual" in coverage_set):
        failures.append(f"{label} multilingual coverage disagrees with language")
    if lifecycle is not None:
        post_compaction = lifecycle.get("state") == "post-compaction"
        if post_compaction != ("post-compaction" in coverage_set):
            failures.append(f"{label} post-compaction coverage disagrees with lifecycle")
    if not coverage_set:
        failures.append(f"{label}.coverage must not be empty")
    if benchmark_sets is None:
        return document
    return document


def check_schema_contract(schema: dict[str, Any], failures: list[str]) -> None:
    if schema.get("$id") != SCHEMA_ID:
        failures.append("evals/schema-v1.json has the wrong immutable schema identifier")
    definitions = schema.get("$defs")
    expected = {
        "case": CASE_KEYS,
        "lifecycle": LIFECYCLE_KEYS,
        "benchmarkManifest": BENCHMARK_KEYS,
        "benchmarkSafety": BENCHMARK_SAFETY_KEYS,
        "officialReference": OFFICIAL_REFERENCE_KEYS,
        "responseSchema": RESPONSE_SCHEMA_KEYS,
        "host": HOST_KEYS,
        "environment": ENVIRONMENT_KEYS,
        "run": RUN_KEYS,
        "resultCase": RESULT_CASE_KEYS,
        "summary": SUMMARY_KEYS,
        "observationRecord": OBSERVATION_KEYS,
    }
    expected_names = set(expected) | {"route", "subject"}
    if type(definitions) is not dict or set(definitions) != expected_names:
        failures.append("evals/schema-v1.json definitions drifted from owned records")
        return
    for name, keys in expected.items():
        definition = definitions.get(name)
        if type(definition) is not dict:
            failures.append(f"evals/schema-v1.json is missing definition {name!r}")
            continue
        if definition.get("additionalProperties") is not False:
            failures.append(f"evals/schema-v1.json {name} must reject unknown fields")
        if set(definition.get("required", ())) != keys:
            failures.append(f"evals/schema-v1.json {name} required fields drifted")
        optional_keys = {
            "run": RUN_OPTIONAL_KEYS,
            "resultCase": RESULT_CASE_OPTIONAL_KEYS,
        }.get(name, frozenset())
        properties = definition.get("properties")
        if type(properties) is not dict or set(properties) != keys | optional_keys:
            failures.append(f"evals/schema-v1.json {name} properties drifted")
    subject = definitions.get("subject")
    if type(subject) is not dict:
        failures.append("evals/schema-v1.json is missing definition 'subject'")
    else:
        if subject.get("additionalProperties") is not False:
            failures.append("evals/schema-v1.json subject must reject unknown fields")
        if set(subject.get("required", ())) != SUBJECT_KEYS:
            failures.append("evals/schema-v1.json subject required fields drifted")
        properties = subject.get("properties")
        if type(properties) is not dict or set(properties) != CANDIDATE_SUBJECT_KEYS:
            failures.append("evals/schema-v1.json subject properties drifted")
        expected_subject_variants = [
            {
                "properties": {"tag": {"type": "string"}},
                "not": {"required": ["releaseState"]},
            },
            {
                "required": ["releaseState"],
                "properties": {
                    "tag": {"type": "null"},
                    "releaseState": {"const": "candidate-unreleased"},
                },
            },
        ]
        if subject.get("oneOf") != expected_subject_variants:
            failures.append(
                "evals/schema-v1.json subject candidate/released variants drifted"
            )
    route_definition = definitions.get("route")
    if type(route_definition) is not dict or route_definition.get("enum") != list(
        HISTORICAL_PUBLIC_ROUTES
    ):
        failures.append("evals/schema-v1.json route enum drifted from public routes")
    response_schema_definition = definitions.get("responseSchema")
    response_schema_properties = (
        response_schema_definition.get("properties")
        if type(response_schema_definition) is dict
        else None
    )
    if type(response_schema_properties) is not dict or response_schema_properties.get(
        "path"
    ) != {
        "enum": [
            HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
            HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
        ]
    }:
        failures.append("evals/schema-v1.json response schema paths drifted")
    run_definition = definitions.get("run")
    run_properties = run_definition.get("properties") if type(run_definition) is dict else None
    if (
        type(run_properties) is not dict
        or run_properties.get("status", {}).get("enum") != list(RESULT_STATUS_VALUES)
    ):
        failures.append("evals/schema-v1.json run status enum drifted")
    elif run_properties.get("callCount") != {
        "type": "integer",
        "minimum": 0,
        "maximum": 13,
    }:
        failures.append("evals/schema-v1.json call count contract drifted")
    result_definition = definitions.get("resultCase")
    result_properties = (
        result_definition.get("properties") if type(result_definition) is dict else None
    )
    if type(result_properties) is not dict:
        failures.append("evals/schema-v1.json resultCase properties are missing")
    else:
        if result_properties.get("status", {}).get("enum") != list(
            RESULT_STATUS_VALUES
        ):
            failures.append("evals/schema-v1.json result case status enum drifted")
        if result_properties.get("responseDiagnostic", {}).get("enum") != list(
            RESPONSE_DIAGNOSTICS
        ):
            failures.append("evals/schema-v1.json response diagnostic enum drifted")
        if result_properties.get("acceptanceDiagnostic", {}).get("enum") != list(
            ACCEPTANCE_DIAGNOSTICS
        ):
            failures.append("evals/schema-v1.json acceptance diagnostic enum drifted")
        if result_properties.get("evidenceSource", {}).get("enum") != sorted(
            EVIDENCE_SOURCES
        ):
            failures.append("evals/schema-v1.json evidence source enum drifted")
    summary_definition = definitions.get("summary")
    summary_properties = (
        summary_definition.get("properties")
        if type(summary_definition) is dict
        else None
    )
    if (
        type(summary_properties) is not dict
        or summary_properties.get("overallStatus", {}).get("enum")
        != list(RESULT_STATUS_VALUES)
    ):
        failures.append("evals/schema-v1.json summary status enum drifted")


def check_schema_contract_v2(schema: dict[str, Any], failures: list[str]) -> None:
    """Check the additive seven-route corpus and future-observation contract."""
    label = "evals/schema-v2.json"
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        failures.append(f"{label} has the wrong JSON Schema dialect")
    if schema.get("$id") != SCHEMA_V2_ID:
        failures.append(f"{label} has the wrong schema identifier")
    definitions = schema.get("$defs")
    expected = {
        "case": CASE_KEYS,
        "lifecycle": LIFECYCLE_KEYS,
        "benchmarkManifest": BENCHMARK_KEYS,
        "benchmarkSafety": BENCHMARK_SAFETY_KEYS,
        "officialReference": OFFICIAL_REFERENCE_KEYS,
        "responseSchema": RESPONSE_SCHEMA_KEYS,
        "host": HOST_KEYS,
        "environment": ENVIRONMENT_KEYS,
        "run": RUN_KEYS,
        "resultCase": RESULT_CASE_KEYS,
        "summary": SUMMARY_KEYS,
        "observationRecord": OBSERVATION_KEYS,
    }
    expected_names = set(expected) | {"route", "subject"}
    if type(definitions) is not dict or set(definitions) != expected_names:
        failures.append(f"{label} definitions drifted from owned records")
        return
    for name, keys in expected.items():
        definition = definitions.get(name)
        if type(definition) is not dict:
            failures.append(f"{label} is missing definition {name!r}")
            continue
        if definition.get("additionalProperties") is not False:
            failures.append(f"{label} {name} must reject unknown fields")
        if set(definition.get("required", ())) != keys:
            failures.append(f"{label} {name} required fields drifted")
        optional_keys = {
            "run": RUN_OPTIONAL_KEYS,
            "resultCase": RESULT_CASE_OPTIONAL_KEYS,
        }.get(name, frozenset())
        properties = definition.get("properties")
        if type(properties) is not dict or set(properties) != keys | optional_keys:
            failures.append(f"{label} {name} properties drifted")

    subject = definitions.get("subject")
    if type(subject) is not dict:
        failures.append(f"{label} is missing definition 'subject'")
    else:
        if subject.get("additionalProperties") is not False:
            failures.append(f"{label} subject must reject unknown fields")
        if set(subject.get("required", ())) != SUBJECT_KEYS:
            failures.append(f"{label} subject required fields drifted")
        if set(subject.get("properties", ())) != CANDIDATE_SUBJECT_KEYS:
            failures.append(f"{label} subject properties drifted")

    route_definition = definitions.get("route")
    if type(route_definition) is not dict or route_definition.get("enum") != list(
        PUBLIC_ROUTES
    ):
        failures.append(f"{label} route enum drifted from current public routes")

    case_properties = definitions.get("case", {}).get("properties", {})
    if case_properties.get("schemaVersion") != {"const": "2"}:
        failures.append(f"{label} case schema version drifted")
    if case_properties.get("forbiddenRoutes", {}).get("maxItems") != len(
        PUBLIC_ROUTES
    ):
        failures.append(f"{label} forbidden-route bound drifted")
    if case_properties.get("benchmarkSets", {}).get("items") != {
        "const": BENCHMARK_V2_ID
    }:
        failures.append(f"{label} case benchmark binding drifted")

    benchmark_properties = definitions.get("benchmarkManifest", {}).get(
        "properties", {}
    )
    expected_benchmark_fields = {
        "schemaVersion": {"const": "2"},
        "id": {"const": BENCHMARK_V2_ID},
        "corpusSchema": {"const": SCHEMA_V2_ID},
    }
    for name, expected_value in expected_benchmark_fields.items():
        if benchmark_properties.get(name) != expected_value:
            failures.append(f"{label} benchmark {name} binding drifted")
    if benchmark_properties.get("caseIds") != {
        "type": "array",
        "minItems": 17,
        "maxItems": 17,
        "uniqueItems": True,
        "items": {"type": "string"},
    }:
        failures.append(f"{label} benchmark case-count contract drifted")

    response_properties = definitions.get("responseSchema", {}).get(
        "properties", {}
    )
    if response_properties.get("path") != {
        "enum": [
            HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
            HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
            HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
        ]
    }:
        failures.append(f"{label} response schema paths drifted")

    run_properties = definitions.get("run", {}).get("properties", {})
    if run_properties.get("callCount") != {
        "type": "integer",
        "minimum": 0,
        "maximum": 17,
    }:
        failures.append(f"{label} call count contract drifted")
    observation_properties = definitions.get("observationRecord", {}).get(
        "properties", {}
    )
    if observation_properties.get("schemaVersion") != {"const": "2"}:
        failures.append(f"{label} observation schema version drifted")
    if observation_properties.get("benchmarkId") != {"const": BENCHMARK_V2_ID}:
        failures.append(f"{label} observation benchmark binding drifted")

    result_properties = definitions.get("resultCase", {}).get("properties", {})
    if result_properties.get("status", {}).get("enum") != list(
        RESULT_STATUS_VALUES
    ):
        failures.append(f"{label} result status enum drifted")
    if result_properties.get("responseDiagnostic", {}).get("enum") != list(
        RESPONSE_DIAGNOSTICS
    ):
        failures.append(f"{label} response diagnostic enum drifted")
    if result_properties.get("acceptanceDiagnostic", {}).get("enum") != list(
        ACCEPTANCE_DIAGNOSTICS
    ):
        failures.append(f"{label} acceptance diagnostic enum drifted")
    if result_properties.get("evidenceSource", {}).get("enum") != sorted(
        EVIDENCE_SOURCES
    ):
        failures.append(f"{label} evidence source enum drifted")


def check_host_response_schema(schema: dict[str, Any], failures: list[str]) -> None:
    """Check the byte-frozen V1 model-facing schema contract."""
    expected_root_keys = {"type", "additionalProperties", "required", "properties"}
    if set(schema) != expected_root_keys:
        failures.append(
            "host response schema root keywords drifted from the documented model subset"
        )
    if schema.get("type") != "object":
        failures.append("host response schema root must be an object")
    if schema.get("additionalProperties") is not False:
        failures.append("host response schema must reject unknown fields")
    if set(schema.get("required", ())) != HOST_RESPONSE_KEYS:
        failures.append("host response schema required fields drifted")
    properties = schema.get("properties")
    if type(properties) is not dict or set(properties) != HOST_RESPONSE_KEYS:
        failures.append("host response schema properties drifted")
        return
    expected_properties = {
        "routingGateObserved": {"type": "boolean"},
        "selectedRoutes": {
            "type": "array",
            "maxItems": 2,
            "items": {"enum": list(HISTORICAL_PUBLIC_ROUTES)},
        },
        "clarificationCount": {"type": "integer", "minimum": 0, "maximum": 1},
        "mutationAttempted": {"type": "boolean"},
        "mutationObserved": {"type": "boolean"},
        "evidence": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {"type": "string"},
        },
    }
    if properties != expected_properties:
        failures.append(
            "host response schema properties drifted from the reviewed model subset"
        )


def check_host_response_schema_v2(
    schema: dict[str, Any], failures: list[str]
) -> None:
    """Check the prose-free V2 schema against the supported model subset."""
    expected_root_keys = {"type", "additionalProperties", "required", "properties"}
    if set(schema) != expected_root_keys:
        failures.append(
            "V2 host response schema root keywords drifted from the documented model subset"
        )
    if schema.get("type") != "object":
        failures.append("V2 host response schema root must be an object")
    if schema.get("additionalProperties") is not False:
        failures.append("V2 host response schema must reject unknown fields")
    if list(schema.get("required", ())) != [
        "routingGateObserved",
        "selectedRoutes",
        "clarificationCount",
        "mutationAttempted",
        "mutationObserved",
    ]:
        failures.append("V2 host response schema required fields drifted")
    properties = schema.get("properties")
    if type(properties) is not dict or set(properties) != HOST_RESPONSE_V2_KEYS:
        failures.append("V2 host response schema properties drifted")
        return
    expected_properties = {
        "routingGateObserved": {"type": "boolean"},
        "selectedRoutes": {
            "type": "array",
            "minItems": 0,
            "maxItems": 2,
            "items": {
                "type": "string",
                "enum": list(HISTORICAL_PUBLIC_ROUTES),
            },
        },
        "clarificationCount": {"type": "integer", "minimum": 0, "maximum": 1},
        "mutationAttempted": {"type": "boolean"},
        "mutationObserved": {"type": "boolean"},
    }
    if properties != expected_properties:
        failures.append(
            "V2 host response schema properties drifted from the reviewed model subset"
        )


def check_host_response_schema_v3(
    schema: dict[str, Any], failures: list[str]
) -> None:
    """Check the prose-free seven-route V3 model-facing schema."""
    expected_root_keys = {"type", "additionalProperties", "required", "properties"}
    if set(schema) != expected_root_keys:
        failures.append(
            "V3 host response schema root keywords drifted from the documented model subset"
        )
    if schema.get("type") != "object":
        failures.append("V3 host response schema root must be an object")
    if schema.get("additionalProperties") is not False:
        failures.append("V3 host response schema must reject unknown fields")
    if list(schema.get("required", ())) != [
        "routingGateObserved",
        "selectedRoutes",
        "clarificationCount",
        "mutationAttempted",
        "mutationObserved",
    ]:
        failures.append("V3 host response schema required fields drifted")
    properties = schema.get("properties")
    if type(properties) is not dict or set(properties) != HOST_RESPONSE_V2_KEYS:
        failures.append("V3 host response schema properties drifted")
        return
    expected_properties = {
        "routingGateObserved": {"type": "boolean"},
        "selectedRoutes": {
            "type": "array",
            "minItems": 0,
            "maxItems": 2,
            "items": {"type": "string", "enum": list(PUBLIC_ROUTES)},
        },
        "clarificationCount": {"type": "integer", "minimum": 0, "maximum": 1},
        "mutationAttempted": {"type": "boolean"},
        "mutationObserved": {"type": "boolean"},
    }
    if properties != expected_properties:
        failures.append(
            "V3 host response schema properties drifted from the reviewed model subset"
        )
