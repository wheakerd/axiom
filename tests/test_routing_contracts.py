"""Focused tests for routing policy and fixtures."""

import unittest

from axiom_validation.routing_contracts import (
    check_cross_route_resume_contracts,
    check_routing_scenarios,
    check_routing_source_contracts,
    historical_route_contract,
    route_contract,
)
from axiom_validation.cases.routing import ROUTE_BOUNDARY_SCENARIOS, ROUTING_SCENARIOS


class RoutingContractTests(unittest.TestCase):
    def test_all_routing_fixtures(self):
        failures = []
        check_routing_scenarios(ROUTING_SCENARIOS, failures)
        self.assertEqual(68 + len(ROUTE_BOUNDARY_SCENARIOS), len(ROUTING_SCENARIOS))
        self.assertEqual(10, len(ROUTE_BOUNDARY_SCENARIOS))
        self.assertEqual([], failures)

    def test_ordinary_request_does_not_route(self):
        self.assertIsNone(route_contract("Summarize this README without changing files.")["route"])

    def test_ordinary_named_remote_push_does_not_route(self):
        self.assertIsNone(
            route_contract("Commit this change and git push origin main.")["route"]
        )

    def test_tagged_plugin_release_routes_without_broadening_ordinary_push(self):
        tagged_release = route_contract(
            "Commit, tag, and push the already-prepared plugin release without "
            "rewriting history."
        )
        self.assertEqual("traceable-git-submit", tagged_release["route"])
        self.assertEqual("prepared-release-submit", tagged_release["phase"])
        self.assertEqual(
            (
                "references/safe-git-values-and-metadata.md",
                "references/repository-and-remote-targets.md",
                "references/prepared-release-submit.md",
            ),
            tagged_release["references"],
        )
        self.assertEqual(
            frozenset({"read", "commit", "tag", "network-push"}),
            tagged_release["authorization"],
        )
        self.assertEqual(
            "hardened-submit",
            historical_route_contract(
                "Commit, tag, and push the already-prepared plugin release."
            )["phase"],
        )
        self.assertIsNone(
            route_contract(
                "Commit the staged plugin change and git push origin main once "
                "without force."
            )["route"]
        )

    def test_recovery_preparation_has_its_own_write_scope(self):
        preparation = route_contract(
            "Prepare missing recovery material for this persistent database migration."
        )
        self.assertEqual("recovery-material-preparation", preparation["phase"])
        self.assertEqual(
            (
                "references/preflight-and-rollback.md",
                "references/recovery-material-preparation.md",
            ),
            preparation["references"],
        )
        self.assertEqual(
            frozenset({"read", "recovery-preparation-write"}),
            preparation["authorization"],
        )
        for request in (
            "Plan how to prepare missing recovery material for this persistent database migration.",
            "Prepare a read-only plan to create a backup of this persistent database.",
        ):
            with self.subTest(request=request):
                plan = route_contract(request)
                self.assertEqual("plan", plan["phase"])
                self.assertEqual(frozenset({"read"}), plan["authorization"])
                self.assertNotIn(
                    "references/recovery-material-preparation.md", plan["references"]
                )

    def test_local_marketplace_readiness_stays_a_read_only_architecture_phase(self):
        contract = route_contract(
            "Audit release readiness of this packaged Codex plugin with a local "
            "marketplace, prerelease versions, and no GitHub repository."
        )
        self.assertEqual("agent-plugin-architect", contract["route"])
        self.assertEqual("release-readiness-audit", contract["phase"])
        self.assertEqual(frozenset({"read"}), contract["authorization"])
        self.assertIn("references/release-readiness.md", contract["references"])

    def test_explicit_direct_submit_loads_only_lightweight_owner(self):
        contract = route_contract(
            "$traceable-git-submit: git push origin main once without force."
        )
        self.assertEqual("traceable-git-submit", contract["route"])
        self.assertEqual("direct-submit", contract["phase"])
        self.assertEqual(("references/direct-submit.md",), contract["references"])

    def test_traceable_git_phase_partition_and_stale_constraint(self):
        scenarios = {
            scenario["name"]: scenario
            for scenario in ROUTING_SCENARIOS
            if scenario["name"]
            in {
                "baseline-metadata-audit",
                "traceable-workflow-audit",
                "local-checkpoint",
                "checkpoint-consolidation",
                "checkpoint-consolidation-and-push",
                "checkpoint-recovery",
                "checkpoint-remote-recovery",
                "direct-push",
                "stale-tracking-mention-no-match",
                "stale-tracking-live-baseline-direct-push",
            }
        }
        self.assertEqual(10, len(scenarios))
        for name, scenario in scenarios.items():
            with self.subTest(name=name):
                contract = route_contract(scenario["request"])
                self.assertEqual(scenario["route"], contract["route"])
                self.assertEqual(scenario["phase"], contract["phase"])
                self.assertEqual(scenario["references"], contract["references"])
                self.assertEqual(
                    scenario["authorization"], contract["authorization"]
                )

    def test_source_routes_and_phase_contracts_are_reachable(self):
        failures = []
        check_routing_source_contracts(failures)
        self.assertEqual(7, check_cross_route_resume_contracts(failures))
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
