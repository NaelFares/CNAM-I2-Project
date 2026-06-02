"""ICS planning import parser."""

from __future__ import annotations

from datetime import datetime

from icalendar import Calendar

from backend.models.event import Event


def parse_ics(file_content: bytes) -> list[Event]:
    """Parse an ICS file and return planning events."""
    events: list[Event] = []
    try:
        calendar = Calendar.from_ical(file_content)
        for component in calendar.walk():
            if component.name != "VEVENT":
                continue

            title = str(component.get("summary", "Sans titre"))
            start_time = component.get("dtstart").dt
            end_time = component.get("dtend").dt
            location = str(component.get("location", ""))
            description = str(component.get("description", ""))

            if not isinstance(start_time, datetime):
                start_time = datetime.combine(start_time, datetime.min.time())
            if not isinstance(end_time, datetime):
                end_time = datetime.combine(end_time, datetime.min.time())

            events.append(
                Event(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    description=description,
                )
            )
    except Exception as exc:
        raise ValueError(f"Erreur lors du parsing ICS: {exc}") from exc

    return events
