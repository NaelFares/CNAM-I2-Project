"""Tests ciblés de l'archivage idempotent des trajets."""

import unittest
from unittest.mock import MagicMock, patch

from backend.database.manager import Database


class RideArchivingTests(unittest.TestCase):
    def test_archive_only_updates_expired_active_rides(self):
        database = Database()
        connection = MagicMock()
        cursor = MagicMock()
        cursor.rowcount = 2
        connection.cursor.return_value = cursor

        with patch.object(database, "get_connection", return_value=connection):
            archived_count = database.archive_expired_rides()

        query = cursor.execute.call_args.args[0]
        self.assertIn("status = 'active'", query)
        self.assertIn("LOCALTIMESTAMP - INTERVAL '3 hours'", query)
        self.assertEqual(archived_count, 2)
        connection.commit.assert_called_once_with()
        connection.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
