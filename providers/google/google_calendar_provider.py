from datetime import datetime
import threading

from googleapiclient.discovery import build

from models.calendar_event import CalendarEvent
from providers.google.google_auth_service import GoogleAuthService
from providers.interfaces.calendar_provider import CalendarProvider


class GoogleCalendarProvider(CalendarProvider):
    def __init__(self, auth_service: GoogleAuthService):

        self._lock = threading.Lock()
        self.auth_service = auth_service

        credentials = self.auth_service.get_credentials()

        self.calendar_client = build("calendar", "v3", credentials=credentials)

    def create_event(
            self,
            title: str,
            start_time: datetime,
            end_time: datetime,
            location: str | None = None,
            attendees: list[str] | None = None
    ):

        event_body = {
            "summary": title,
            "location": location,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "Asia/Singapore"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "Asia/Singapore"
            }
        }
        if attendees is not None:
            event_body["attendees"] = [
                {"email": email}
                for email in attendees
            ]
        with self._lock:
            google_event = self.calendar_client.events().insert(
                calendarId="primary",
                body=event_body
            ).execute()

        return CalendarEvent(
            id=google_event["id"],
            title=google_event["summary"],
            start_time=start_time,
            end_time=end_time,
            location=google_event.get("location"),
            attendees=attendees,
            status=google_event["status"]
        )

    def list_events(self, start_time: datetime, end_time: datetime, query: str | None = None) -> list[
        CalendarEvent]:
        request_params = {
            "calendarId": "primary",
            "timeMin": start_time.isoformat(),
            "timeMax": end_time.isoformat(),
            "singleEvents": True,
            "orderBy": "startTime",
            "timeZone": "Asia/Singapore"
        }
        if query:
            request_params["q"] = query

        with self._lock:
            result = self.calendar_client.events().list(**request_params).execute()

        calendar_events = []

        for google_event in result.get("items", []):
            attendees = [
                attendee["email"]
                for attendee in google_event.get("attendees", [])
                if "email" in attendee
            ]

            event_start_time = datetime.fromisoformat(
                google_event["start"]["dateTime"]
            )

            event_end_time = datetime.fromisoformat(
                google_event["end"]["dateTime"]
            )

            calendar_events.append(
                CalendarEvent(
                    id=google_event["id"],
                    title=google_event.get("summary", "Untitled event"),
                    start_time=event_start_time,
                    end_time=event_end_time,
                    location=google_event.get("location"),
                    attendees=attendees or None,
                    status=google_event.get("status", "confirmed"),
                )
            )
        return calendar_events

    def update_event(self, event: CalendarEvent) -> CalendarEvent:
        event_body = {
            "summary": event.title,
            "location": event.location,
            "start": {
                "dateTime": event.start_time.isoformat(),
                "timeZone": "Asia/Singapore"
            },
            "end": {
                "dateTime": event.end_time.isoformat(),
                "timeZone": "Asia/Singapore"
            }
        }
        if event.attendees is not None:
            event_body["attendees"] = [
                {"email": email}
                for email in event.attendees
            ]

        event_id = event.id

        with self._lock:
            google_event = self.calendar_client.events().patch(
                calendarId="primary",
                eventId=event_id,
                body=event_body
            ).execute()

        attendees = [
            attendee["email"]
            for attendee in google_event.get("attendees", [])
            if "email" in attendee
        ]
        event_start_time = datetime.fromisoformat(
            google_event["start"]["dateTime"]
        )

        event_end_time = datetime.fromisoformat(
            google_event["end"]["dateTime"]
        )
        return CalendarEvent(
            id=google_event["id"],
            title=google_event["summary"],
            start_time=event_start_time,
            end_time=event_end_time,
            location=google_event.get("location"),
            attendees=attendees or None,
            status=google_event["status"]
        )

    def delete_event(self, event_id: str) -> None:
        print(f"Deleting event: {event_id}")
        with self._lock:
            self.calendar_client.events().delete(
                calendarId="primary",
                eventId=event_id
            ).execute()

        print(f"Deleted event: {event_id}")

    def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        events = self.list_events(start_time, end_time, query=None)
        return len(events) == 0
