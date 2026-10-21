"""Tests for the routing facade: cache first, then OSRM, then estimate."""

import unittest
from unittest.mock import Mock, patch

from backend.services.routing import RoutingService

START, END = (43.60, 1.44), (43.61, 1.45)
OSRM_RESULT = {
    "geometry": [(43.60, 1.44), (43.605, 1.447), (43.61, 1.45)],
    "distance_m": 1500.0,
    "duration_s": 240.0,
}


class RoutingCacheTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.service = RoutingService(client=self.client)

    def test_cache_hit_does_not_call_osrm(self):
        cached = {"geometry": [[43.60, 1.44], [43.61, 1.45]], "distance_m": 1200.0, "duration_s": 240.0}

        with patch("backend.services.routing.db.get_routing_cache", return_value=cached):
            result = self.service.get_route_details(START, END)

        self.assertEqual(result, {**cached, "estimated": False})
        self.client.route.assert_not_called()

    def test_osrm_result_is_returned_and_cached(self):
        self.client.route.return_value = dict(OSRM_RESULT)

        with (
            patch("backend.services.routing.db.get_routing_cache", return_value=None),
            patch("backend.services.routing.db.upsert_routing_cache") as upsert,
        ):
            result = self.service.get_route_details(START, END)

        self.assertEqual(result, {**OSRM_RESULT, "estimated": False})
        self.client.route.assert_called_once_with([START, END])
        upsert.assert_called_once()

    def test_via_route_passes_the_pickup_point_between_start_and_end(self):
        via = (43.605, 1.445)
        self.client.route.return_value = dict(OSRM_RESULT)

        with (
            patch("backend.services.routing.db.get_routing_cache", return_value=None),
            patch("backend.services.routing.db.upsert_routing_cache"),
        ):
            self.service.get_route_via_waypoints(START, [via], END)

        self.client.route.assert_called_once_with([START, via, END])

    def test_unavailable_osrm_falls_back_to_an_uncached_estimate(self):
        """OSRM arrete : estimation renvoyee, jamais ecrite dans le cache."""
        self.client.route.return_value = None

        with (
            patch("backend.services.routing.db.get_routing_cache", return_value=None),
            patch("backend.services.routing.db.upsert_routing_cache") as upsert,
        ):
            result = self.service.get_route_details(START, END)

        self.assertTrue(result["estimated"])
        self.assertEqual(result["geometry"], [START, END])
        upsert.assert_not_called()

    def test_direct_and_via_routes_have_different_cache_keys(self):
        direct = RoutingService._cache_key([(43.60, 1.44), (43.61, 1.45)])
        via = RoutingService._cache_key(
            [(43.60, 1.44), (43.605, 1.445), (43.61, 1.45)]
        )
        self.assertNotEqual(direct, via)


if __name__ == "__main__":
    unittest.main()
