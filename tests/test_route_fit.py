"""Le passager est-il sur la route du conducteur, et au bon moment ?"""

from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

from backend.models.ride import Ride
from backend.models.user import User
from backend.services.matching import (
    MatchingService,
    overlaps_reserved_slot,
    passage_gap_min,
    time_tolerance_min,
)
from backend.services.route_fit import fit_on_route, nearest_on_route

# Route nord-sud d'environ 22 km : Aucamville -> Castanet.
LONG_ROUTE = [(43.6700, 1.4300), (43.6000, 1.4500), (43.5200, 1.4950)]


class RouteFitTests(unittest.TestCase):
    def test_passenger_near_the_end_of_a_long_route_is_a_candidate(self):
        # Le passager habite a 18 km du depart du conducteur (l'ancien filtre
        # "departs a moins de 10 km" l'ecartait), mais la route passe a cote.
        pickup = (43.5500, 1.4800)
        fit = fit_on_route(LONG_ROUTE, pickup, None, max_km=2.0)
        self.assertIsNotNone(fit)
        self.assertLess(fit.pickup_km, 1.0)

    def test_point_too_far_from_the_route_is_rejected(self):
        far_away = (43.6000, 1.3300)  # ~10 km a l'ouest
        self.assertIsNone(fit_on_route(LONG_ROUTE, far_away, None, max_km=2.0))

    def test_dropoff_before_pickup_means_the_wrong_direction(self):
        # Pris pres de l'arrivee, depose pres du depart : il va dans l'autre sens.
        pickup, dropoff = (43.5300, 1.4900), (43.6600, 1.4320)
        self.assertIsNone(fit_on_route(LONG_ROUTE, pickup, dropoff, max_km=2.0))
        self.assertIsNotNone(fit_on_route(LONG_ROUTE, dropoff, pickup, max_km=2.0))

    def test_straight_estimated_route_still_works(self):
        # Sans OSRM, la route estimee n'a que deux points : on mesure la
        # distance au segment, pas aux seuls sommets.
        distance, _ = nearest_on_route((43.6000, 1.4630), [(43.6700, 1.4300), (43.5200, 1.4950)])
        self.assertLess(distance, 1.0)


class PassageTimeTests(unittest.TestCase):
    def test_tolerance_is_the_passengers(self):
        # Le conducteur garde son horaire : seule compte l'heure a laquelle
        # le passager est depose ou pris, donc sa tolerance a lui.
        self.assertEqual(time_tolerance_min(User(time_tolerance_min=30)), 30)

    def test_way_in_must_drop_before_the_target_time(self):
        course = datetime(2026, 10, 26, 8, 0)
        # Depose a 7h50 : 10 min d'avance, ecart positif.
        self.assertEqual(passage_gap_min("to_campus", course - timedelta(minutes=10), course), 10)
        # Depose a 8h05 : en retard, ecart negatif, donc refuse.
        self.assertLess(passage_gap_min("to_campus", course + timedelta(minutes=5), course), 0)

    def test_way_back_must_pick_up_after_the_target_time(self):
        end_of_class = datetime(2026, 10, 26, 12, 0)
        self.assertEqual(passage_gap_min("from_campus", end_of_class + timedelta(minutes=8), end_of_class), 8)
        self.assertLess(passage_gap_min("from_campus", end_of_class - timedelta(minutes=5), end_of_class), 0)

    def test_passage_time_follows_the_driver_along_his_route(self):
        # A l'aller, l'heure du conducteur est son arrivee : il depose le
        # passager avant, de la duree de la fin de son trajet.
        way_in = Ride(ride_type="to_campus", ride_time=datetime(2026, 10, 26, 8, 0))
        self.assertEqual(MatchingService._passage_time(way_in, 600), datetime(2026, 10, 26, 7, 50))
        # Au retour, c'est son depart : il prend le passager apres.
        way_back = Ride(ride_type="from_campus", ride_time=datetime(2026, 10, 26, 17, 0))
        self.assertEqual(MatchingService._passage_time(way_back, 600), datetime(2026, 10, 26, 17, 10))


class SharedCarTests(unittest.TestCase):
    """Plusieurs passagers dans la meme voiture, et creneaux qui se chevauchent."""

    def test_rides_fifteen_minutes_apart_overlap(self):
        booked = {datetime(2026, 10, 26, 8, 0)}
        self.assertTrue(overlaps_reserved_slot(booked, datetime(2026, 10, 26, 8, 15)))
        self.assertFalse(overlaps_reserved_slot(booked, datetime(2026, 10, 26, 12, 0)))

    def test_total_detour_adds_up_every_stop_in_route_order(self):
        driver_ride = Ride(start_lat=43.6700, start_lon=1.4300, end_lat=43.5200, end_lon=1.4950)
        direct = {"geometry": LONG_ROUTE, "duration_s": 1200}
        first = ((43.6400, 1.4380), None)    # deja accepte, au nord
        second = ((43.5600, 1.4700), None)   # nouveau, au sud
        calls = []

        def via(start, waypoints, end):
            calls.append(list(waypoints))
            return {"duration_s": 1200 + 600 * len(waypoints)}

        with patch("backend.services.matching.routing_service.get_route_via_waypoints", side_effect=via):
            total = MatchingService._total_detour_min(direct, driver_ride, [second, first])

        # Deux arrets a 10 min chacun ; visites dans l'ordre de la route.
        self.assertEqual(total, 20)
        self.assertEqual(calls[0], [(43.6400, 1.4380), (43.5600, 1.4700)])

    def test_accepting_warns_only_when_the_total_goes_over_the_limit(self):
        driver_ride = Ride(start_lat=43.6700, start_lon=1.4300, end_lat=43.5200, end_lon=1.4950)
        direct = {"geometry": LONG_ROUTE, "duration_s": 1200}
        new = ((43.5600, 1.4700), None)
        accepted = [((43.6400, 1.4380), None), ((43.6000, 1.4500), None)]

        # 10 min par arret : 1 arret seul ne compte pas, 3 arrets = 30 min > 20.
        with (
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct),
            patch(
                "backend.services.matching.routing_service.get_route_via_waypoints",
                side_effect=lambda start, waypoints, end: {"duration_s": 1200 + 600 * len(waypoints)},
            ),
        ):
            self.assertFalse(MatchingService.accept_exceeds_total_detour(driver_ride, new, []))
            self.assertTrue(MatchingService.accept_exceeds_total_detour(driver_ride, new, accepted))
            self.assertFalse(MatchingService.accept_exceeds_total_detour(driver_ride, new, accepted[:1]))


if __name__ == "__main__":
    unittest.main()
