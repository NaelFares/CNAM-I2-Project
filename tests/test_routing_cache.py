"""Tests for persistent routing caching and ORS quota protection."""

import unittest
from unittest.mock import Mock, patch

from backend.core.config import config
from backend.services.routing import RoutingQuotaExceededError, RoutingService


class RoutingCacheTests(unittest.TestCase):
    def test_cache_hit_does_not_call_ors(self):
        cached = {
            "geometry": [[43.60, 1.44], [43.61, 1.45]],
            "distance_m": 1200.0,
            "duration_s": 240.0,
        }
        service = RoutingService()

        with (
            patch("backend.services.routing.db.get_routing_cache", return_value=cached),
            patch("backend.services.routing.requests.request") as request,
        ):
            result = service.get_route_details((43.60, 1.44), (43.61, 1.45))

        self.assertEqual(result, cached)
        request.assert_not_called()

    def test_successful_ors_result_is_saved(self):
        response = Mock(status_code=200, headers={})
        response.json.return_value = {
            "features": [
                {
                    "geometry": {"coordinates": [[1.44, 43.60], [1.45, 43.61]]},
                    "properties": {"summary": {"distance": 1200, "duration": 240}},
                }
            ]
        }
        service = RoutingService()

        with (
            patch("backend.services.routing.db.get_routing_cache", return_value=None),
            patch("backend.services.routing.db.upsert_routing_cache") as upsert,
            patch("backend.services.routing.requests.request", return_value=response) as request,
            patch.object(config, "ORS_API_KEY", "test-key"),
        ):
            result = service.get_route_details((43.60, 1.44), (43.61, 1.45))

        self.assertEqual(result["duration_s"], 240.0)
        request.assert_called_once()
        upsert.assert_called_once()

    def test_daily_quota_error_blocks_following_requests_immediately(self):
        response = Mock(status_code=403, headers={})
        service = RoutingService()

        with (
            patch("backend.services.routing.db.get_routing_cache", return_value=None),
            patch("backend.services.routing.requests.request", return_value=response) as request,
            patch.object(config, "ORS_API_KEY", "test-key"),
        ):
            with self.assertRaises(RoutingQuotaExceededError):
                service.get_route_details((43.60, 1.44), (43.61, 1.45))
            with self.assertRaises(RoutingQuotaExceededError):
                service.get_route_details((43.62, 1.46), (43.63, 1.47))

        request.assert_called_once()

    def test_direct_and_via_routes_have_different_cache_keys(self):
        direct = RoutingService._cache_key([(43.60, 1.44), (43.61, 1.45)])
        via = RoutingService._cache_key(
            [(43.60, 1.44), (43.605, 1.445), (43.61, 1.45)]
        )
        self.assertNotEqual(direct, via)


if __name__ == "__main__":
    unittest.main()
