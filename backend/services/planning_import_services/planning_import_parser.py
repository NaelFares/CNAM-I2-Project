"""Common entry point for schedule imports."""

from __future__ import annotations

from backend.models.event import Event
from backend.services.planning_import_services.csv_ai import CSVParseResult, csv_ai_planning_parser
from backend.services.planning_import_services.ics import parse_ics as parse_ics_file


class PlanningImportParser:
    """Import schedules from supported planning file formats."""

    @staticmethod
    def parse_ics(file_content: bytes) -> list[Event]:
        return parse_ics_file(file_content)

    @staticmethod
    def parse_csv(file_content: bytes) -> CSVParseResult:
        return csv_ai_planning_parser.parse(file_content)


planning_import_parser = PlanningImportParser()
