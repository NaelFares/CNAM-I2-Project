"""Schedule import endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.database.manager import db
from backend.models.event import Event
from backend.models.user import User
from backend.services.planning_import_services import CSVParseResult, planning_import_parser

from backend.api.cache import clear_preview_events, get_preview_events, set_preview_events
from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import EventDTO, ScheduleConfirmResponse, ScheduleEventsResponse, SchedulePreviewResponse

router = APIRouter(prefix="/schedule", tags=["schedule"])
logger = logging.getLogger(__name__)


def _parse_upload(
    upload_file: UploadFile,
    content: bytes,
    privacy_mode: bool = False,
) -> tuple[list[Event], float | None, bool, str | None]:
    file_name = (upload_file.filename or "").lower()
    if file_name.endswith(".ics"):
        events = planning_import_parser.parse_ics(content)
        return events, None, False, None
    if file_name.endswith(".csv"):
        csv_result: CSVParseResult = planning_import_parser.parse_csv(content, privacy_mode=privacy_mode)
        return (
            csv_result.events,
            csv_result.confidence_score,
            csv_result.requires_user_review,
            csv_result.mapping_explanation,
        )
    raise_api_error("SCHEDULE_UNSUPPORTED_FORMAT")


@router.post("/preview", response_model=SchedulePreviewResponse)
async def preview_schedule(
    file: UploadFile = File(...),
    privacy_mode: bool = Form(False),
    user: User = Depends(require_current_user),
):
    content = await file.read()
    if not content:
        raise_api_error("SCHEDULE_EMPTY_FILE")

    try:
        events, confidence_score, requires_user_review, mapping_explanation = _parse_upload(
            file,
            content,
            privacy_mode=privacy_mode,
        )
    except ValueError as exc:
        logger.exception("Schedule preview parsing failed: %s", exc)
        raise_api_error("SCHEDULE_PREVIEW_FAILED", reason=str(exc))
    event_dicts = [event.to_dict() for event in events]
    set_preview_events(user.id, event_dicts)

    return SchedulePreviewResponse(
        events=[EventDTO(**event) for event in event_dicts],
        confidence_score=confidence_score,
        requires_user_review=requires_user_review,
        mapping_explanation=mapping_explanation,
        feedback=make_feedback("SCHEDULE_PREVIEW_SUCCESS", count=len(event_dicts)),
    )


@router.post("/confirm", response_model=ScheduleConfirmResponse)
def confirm_import(user: User = Depends(require_current_user)):
    preview_events = get_preview_events(user.id)
    if not preview_events:
        raise_api_error("SCHEDULE_IMPORT_EMPTY")

    db.delete_events_by_user(user.id)
    db.delete_rides_by_user(user.id)

    for event_dict in preview_events:
        event = Event.from_dict(event_dict)
        event.user_id = user.id
        db.create_event(event)

    clear_preview_events(user.id)

    events = [event.to_dict() for event in db.get_events_by_user(user.id)]
    return ScheduleConfirmResponse(
        events=[EventDTO(**event) for event in events],
        feedback=make_feedback("SCHEDULE_IMPORT_SUCCESS", count=len(events)),
    )


@router.post("/cancel", status_code=204)
def cancel_preview(user: User = Depends(require_current_user)):
    clear_preview_events(user.id)


@router.get("/events", response_model=ScheduleEventsResponse)
def list_schedule_events(user: User = Depends(require_current_user)):
    events = [event.to_dict() for event in db.get_events_by_user(user.id)]
    return ScheduleEventsResponse(events=[EventDTO(**event) for event in events])
