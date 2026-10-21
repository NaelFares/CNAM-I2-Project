"""Tests for the OSRM HTTP client and the straight-line estimate."""

import unittest
from unittest.mock import Mock, patch

import requests

from backend.services.osrm_client import OsrmClient
from backend.services.route_estimate import AVERAGE_SPEED_KMH, ROAD_FACTOR, estimate_route


def osrm_response(payload):
    response = Mock()
    response.json.return_value = payload
    return response


class OsrmClientTests(unittest.TestCase):
    def setUp(self):
        self.client = OsrmClient("http://osrm:5000/")

    def test_route_converts_osrm_response_to_lat_lon(self):
        payload = {
            "code": "Ok",
            "routes": [
                {
                    "geometry": {"coordinates": [[1.44, 43.60], [1.45, 43.61]]},
                    "distance": 1500.4,
                    "duration": 240.2,
                }
            ],
        }

        with patch("backend.services.osrm_client.requests.get", return_value=osrm_response(payload)) as get:
            result = self.client.route([(43.60, 1.44), (43.61, 1.45)])

        self.assertEqual(
            result,
            {"geometry": [(43.60, 1.44), (43.61, 1.45)], "distance_m": 1500.4, "duration_s": 240.2},
        )
        # OSRM attend "lon,lat" ; le slash final de l'URL de base est ignore.
        url = get.call_args.args[0]
        self.assertEqual(url, "http://osrm:5000/route/v1/driving/1.44,43.6;1.45,43.61")

    def test_route_returns_none_when_osrm_finds_no_route(self):
        payload = {"code": "NoSegment", "message": "Could not find a matching segment"}

        with patch("backend.services.osrm_client.requests.get", return_value=osrm_response(payload)):
            self.assertIsNone(self.client.route([(0.0, 0.0), (0.1, 0.1)]))

    def test_route_returns_none_when_osrm_is_unreachable(self):
        with patch(
            "backend.services.osrm_client.requests.get",
            side_effect=requests.ConnectionError("connection refused"),
        ):
            self.assertIsNone(self.client.route([(43.60, 1.44), (43.61, 1.45)]))


class RouteEstimateTests(unittest.TestCase):
    def test_estimate_uses_road_factor_and_average_speed(self):
        # Points distants d'environ 10 km en ligne droite (Toulouse, est-ouest).
        start, end = (43.6047, 1.3800), (43.6047, 1.5040)

        result = estimate_route([start, end])

        road_km = result["distance_m"] / 1000
        self.assertAlmostEqual(road_km, 10.0 * ROAD_FACTOR, delta=0.2)
        self.assertAlmostEqual(result["duration_s"], road_km / AVERAGE_SPEED_KMH * 3600, places=3)
        self.assertEqual(result["geometry"], [start, end])
        self.assertTrue(result["estimated"])


if __name__ == "__main__":
    unittest.main()
