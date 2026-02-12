"""Schedule import endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from backend.database.manager import db
from backend.models.event import Event
from backend.models.user import User
from backend.services.parser import parser

from backend.api.cache import clear_preview_events, get_preview_events, set_preview_events
from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import EventDTO, ScheduleConfirmResponse, ScheduleEventsResponse, SchedulePreviewResponse

router = APIRouter(prefix="/schedule", tags=["schedule"])


def _parse_upload(upload_file: UploadFile, content: bytes):
    file_name = (upload_file.filename or "").lower()
    if file_name.endswith(".ics"):
        return parser.parse_ics(content)
    if file_name.endswith(".csv"):
        return parser.parse_csv(content)
    raise_api_error("SCHEDULE_UNSUPPORTED_FORMAT")


@router.post("/preview", response_model=SchedulePreviewResponse)
async def preview_schedule(
    file: UploadFile = File(...),
    user: User = Depends(require_current_user),
):
    content = await file.read()
    if not content:
        raise_api_error("SCHEDULE_EMPTY_FILE")

    try:
        events = _parse_upload(file, content)
    except ValueError:
        raise_api_error("SCHEDULE_PREVIEW_FAILED")
    event_dicts = [event.to_dict() for event in events]
    set_preview_events(user.id, event_dicts)

    return SchedulePreviewResponse(
        events=[EventDTO(**event) for event in event_dicts],
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
