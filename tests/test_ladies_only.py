import sys
import types
import unittest
from datetime import datetime
from unittest.mock import patch

# Meme approche que tests/test_ai_config.py : importer le moteur de matching
# tire toute la chaine backend (config, manager BD, routing). On stubbe les
# dependances tierces absentes pour que la suite reste lancable sans installer
# backend/requirements.txt — aucune n'est sollicitee par ces tests.
for name, attributes in (
    ("dotenv", {"load_dotenv": lambda *a, **k: None}),
    ("psycopg2", {"OperationalError": type("OperationalError", (Exception,), {}), "connect": None}),
    ("psycopg2.extras", {"RealDictCursor": object, "Json": lambda v: v}),
    ("psycopg2.extensions", {"connection": object}),
    ("requests", {}),
):
    if name.split(".")[0] not in sys.modules:
        try:
            __import__(name)
            continue
        except ModuleNotFoundError:
            pass
    if name not in sys.modules:
        module = types.ModuleType(name)
        module.__dict__.update(attributes)
        sys.modules[name] = module
        if "." in name:
            parent, child = name.rsplit(".", 1)
            setattr(sys.modules[parent], child, module)

from backend.models.ride import Ride
from backend.models.user import User
from backend.services.matching import MatchingService


def _user(user_id: int, gender: str, role: str = "driver") -> User:
    """Conducteur par defaut : seul un conducteur peut etre propose en match."""
    return User(
        id=user_id,
        name=f"User {user_id}",
        gender=gender,
        role=role,
        car_seats=4 if role == "driver" else None,
    )


def _ride(user_id: int) -> Ride:
    return Ride(
        id=user_id * 10,
        user_id=user_id,
        event_id=1,
        ride_type="to_campus",
        ride_time=datetime(2026, 9, 21, 8, 0),
        # Depart propre a chaque utilisateur (quelques centaines de metres
        # d'ecart), pour pouvoir identifier qui a ete evalue via le waypoint
        # transmis au routing.
        start_lat=43.6 + user_id * 0.002,
        start_lon=1.44,
        end_lat=43.56,
        end_lon=1.47,
    )


class GenderModelTests(unittest.TestCase):
    def test_is_woman(self):
        self.assertTrue(_user(1, "femme").is_woman())
        self.assertFalse(_user(2, "homme").is_woman())
        self.assertFalse(_user(3, "autre").is_woman())

    def test_legacy_row_without_gender_falls_back_to_neutral(self):
        user = User.from_dict({"name": "Ancien compte"})
        self.assertEqual(user.gender, "autre")
        self.assertFalse(user.is_woman())


class LadiesOnlyFilterTests(unittest.TestCase):
    """Le filtre doit ecarter les non-femmes avant tout appel de routing."""

    def setUp(self):
        self.searcher = _user(1, "femme", role="passenger")
        self.others = {2: _user(2, "femme"), 3: _user(3, "homme"), 4: _user(4, "autre")}
        self.all_rides = [_ride(uid) for uid in self.others]

    def _run(self, ladies_only: bool) -> set:
        """Renvoie les ids des utilisateurs evalues apres le filtre bon marche.

        On coupe le routing (retour None) : `find_matches` abandonne alors la
        paire, ce qui laisse le filtre comme seul comportement observable.
        """
        evaluated = set()

        by_start = {(ride.start_lat, ride.start_lon): ride.user_id for ride in self.all_rides}

        def fake_detour(start, _waypoint, _end):
            # Le conducteur est l'origine de l'itineraire ; la passagere qui
            # cherche est le point de passage.
            evaluated.add(by_start[start])
            return None

        all_users = list(self.others.values()) + [self.searcher]
        with patch("backend.services.matching.db.get_all_users", return_value=all_users),              patch("backend.services.matching.routing_service.get_route_details", return_value=None),              patch("backend.services.matching.routing_service.get_route_via_waypoint", side_effect=fake_detour):
            MatchingService.find_matches(
                current_user=self.searcher,
                my_rides=[_ride(1)],
                all_rides=self.all_rides,
                selection_counts={},
                selected_ride_ids=set(),
                reserved_times=set(),
                ladies_only=ladies_only,
            )
        return evaluated

    def test_disabled_by_default_keeps_every_gender(self):
        self.assertEqual(self._run(ladies_only=False), {2, 3, 4})

    def test_enabled_keeps_only_women(self):
        # L'homme et le profil "autre" sont ecartes sans appel de routing.
        self.assertEqual(self._run(ladies_only=True), {2})


if __name__ == "__main__":
    unittest.main()
