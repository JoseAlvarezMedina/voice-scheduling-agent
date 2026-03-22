import base64
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

logger = logging.getLogger(__name__)

CALENDAR_SCOPES: list[str] = ["https://www.googleapis.com/auth/calendar"]


class CalendarError(Exception):
    """Raised when calendar operations fail."""


def _load_credentials() -> Credentials:
    credentials_b64 = os.getenv("GOOGLE_CREDENTIALS_B64", "").strip()
    if not credentials_b64:
        raise CalendarError("Missing GOOGLE_CREDENTIALS_B64 environment variable.")

    try:
        decoded = base64.b64decode(credentials_b64).decode("utf-8")
        service_account_info: dict[str, Any] = json.loads(decoded)
    except (ValueError, json.JSONDecodeError) as exc:
        raise CalendarError(
            "GOOGLE_CREDENTIALS_B64 is invalid. Provide a base64-encoded JSON key."
        ) from exc

    try:
        return Credentials.from_service_account_info(
            service_account_info,
            scopes=CALENDAR_SCOPES,
        )
    except Exception as exc:
        raise CalendarError("Failed to load Google service account credentials.") from exc


def _build_event_times(date: str, time: str) -> tuple[str, str]:
    try:
        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(
            tzinfo=ZoneInfo("America/Bogota")
        )
    except ValueError as exc:
        raise CalendarError(
            "Invalid date/time format. Expected date=YYYY-MM-DD and time=HH:MM."
        ) from exc

    end_dt = start_dt + timedelta(hours=1)
    return start_dt.isoformat(), end_dt.isoformat()


def create_event(attendee_name: str, date: str, time: str, title: str) -> str:
    """Create a one-hour Google Calendar event and return its HTML link."""
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "").strip()
    if not calendar_id:
        raise CalendarError("Missing GOOGLE_CALENDAR_ID environment variable.")

    event_title = title.strip() if title and title.strip() else "Meeting"
    start_rfc3339, end_rfc3339 = _build_event_times(date=date, time=time)

    event_body: dict[str, Any] = {
        "summary": event_title,
        "description": f"Scheduled by voice assistant for {attendee_name}.",
        "start": {"dateTime": start_rfc3339, "timeZone": "America/Bogota"},
        "end": {"dateTime": end_rfc3339, "timeZone": "America/Bogota"},
    }

    try:
        credentials = _load_credentials()
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        created_event: dict[str, Any] = (
            service.events()
            .insert(calendarId=calendar_id, body=event_body)
            .execute()
        )
    except HttpError as exc:
        logger.exception("Google Calendar API request failed.")
        raise CalendarError("Google Calendar API request failed.") from exc
    except CalendarError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while creating calendar event.")
        raise CalendarError("Unexpected error while creating calendar event.") from exc

    html_link = created_event.get("htmlLink")
    if not html_link:
        raise CalendarError("Calendar event was created but no event link was returned.")

    return str(html_link)
