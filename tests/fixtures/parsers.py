"""Strict parser regression fixtures."""

from __future__ import annotations

from axiom_validation.yaml_subset import CanonicalYamlError, parse_agent_metadata_document, parse_skill_frontmatter_document
from tests.fixtures.action_graph import check_action_graph_fixtures


def check_validator_negative_fixtures(failures: list[str]) -> int:
    """Prove that the strict parsers reject the bypass forms they guard."""
    rejected = 0
    frontmatter = "name: fixture\ndescription: Valid fixture"
    frontmatter_fixtures = {
        "duplicate": frontmatter.replace("name: fixture", "name: one\nname: two"),
        "unknown-tail": f"{frontmatter}\nextra: tail",
        "wrong-type": frontmatter.replace("name: fixture", "name: false"),
        "yaml-1.1-bool": frontmatter.replace("Valid fixture", "On"),
        "numeric-float": frontmatter.replace(
            "Valid fixture", "12345678901234567890.12345678901234567890"
        ),
        "block-scalar": frontmatter.replace("Valid fixture", ">"),
    }
    for name, fixture in frontmatter_fixtures.items():
        try:
            parse_skill_frontmatter_document(
                f"---\n{fixture}\n---\n\n# Fixture\n",
                f"fixture:{name}",
            )
        except CanonicalYamlError:
            rejected += 1
        else:
            failures.append(f"strict YAML negative fixture {name!r} was accepted")

    agent = (
        'interface:\n  display_name: "Fixture"\n'
        '  short_description: "Valid description that is long enough"\n'
        '  default_prompt: "Use $fixture now."'
    )
    agent_fixtures = {
        "duplicate": agent.replace(
            '  display_name: "Fixture"',
            '  display_name: "Fixture"\n  display_name: "Duplicate"',
        ),
        "unknown-tail": f'{agent}\nextra:\n  field: "ignored before"',
        "wrong-type": agent.replace('"Fixture"', "false", 1),
        "second-document": f"{agent}\n---\nignored: true",
    }
    for name, fixture in agent_fixtures.items():
        try:
            parse_agent_metadata_document(fixture, f"fixture:{name}", allow_policy=False)
        except CanonicalYamlError:
            rejected += 1
        else:
            failures.append(f"agent metadata negative fixture {name!r} was accepted")

    return rejected + check_action_graph_fixtures(failures)
