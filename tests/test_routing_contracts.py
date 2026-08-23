"""Focused tests for routing policy and fixtures."""

import unittest

from axiom_validation.routing_contracts import (
    check_cross_route_resume_contracts,
    check_routing_scenarios,
    check_routing_source_contracts,
    route_contract,
)
from tests.fixtures.routing import ROUTING_SCENARIOS


class RoutingContractTests(unittest.TestCase):
    def test_all_routing_fixtures(self):
        failures = []
        check_routing_scenarios(ROUTING_SCENARIOS, failures)
        self.assertEqual(47, len(ROUTING_SCENARIOS))
        self.assertEqual([], failures)

    def test_ordinary_request_does_not_route(self):
        self.assertIsNone(route_contract("Summarize this README without changing files.")["route"])

    def test_source_routes_and_phase_contracts_are_reachable(self):
        failures = []
        check_routing_source_contracts(failures)
        self.assertEqual(5, check_cross_route_resume_contracts(failures))
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
