import asyncio
import json

from datetime import datetime
from zoneinfo import ZoneInfo

from models.calendar_event import CalendarEvent
from providers.interfaces.calendar_provider import CalendarProvider
from providers.microsoft.mcp_client import MicrosoftMCPClient


class MicrosoftCalendarProvider(CalendarProvider):
    def __init__(self, mcp_client: MicrosoftMCPClient):
        self.mcp_client = mcp_client

    async def list_events(
            self,
            start_time: datetime,
            end_time: datetime,
            query: str | None = None
    ) -> list[CalendarEvent]:
        calendars = await self._list_calendars()

        results = await asyncio.gather(
            *[
                self._list_calendar_event(
                    calendar["id"],
                    start_time,
                    end_time,
                )
                for calendar in calendars
            ]
        )

        events = [
            event
            for calendar_events in results
            for event in calendar_events
        ]

        return events

    async def check_availability(
            self,
            start_time: datetime,
            end_time: datetime,
            exclude_event_id: str | None = None
    ) -> bool:
        events = await self.list_events(start_time, end_time)

        if exclude_event_id is not None:
            events = [
                event for event in events
                if event.id != exclude_event_id
            ]

        for event in events:
            if event.show_as != "free":
                return False
        return True

    async def create_event(
            self,
            title: str,
            start_time: datetime,
            end_time: datetime,
            location: str | None = None,
            attendees: list[str] | None = None
    ) -> CalendarEvent:
        calendar = await self._get_default_calendar()

        body = {
            "subject": title,
            "start": self._parse_time(start_time),
            "end": self._parse_time(end_time),
            "showAs": "busy"
        }
        if location:
            body["location"] = {"displayName": location}

        if attendees:
            body["attendees"] = [
                {
                    "emailAddress": {
                        "address": email
                    },
                    "type": "required"
                }
                for email in (attendees or [])
            ]

        result = await self.mcp_client.call_tool(
            "create-specific-calendar-event",
            {
                "calendarId": calendar["id"],
                "body": body,
            }
        )

        if result.isError:
            print(result)
            raise RuntimeError(
                f"Failed to create Microsoft calendar event: {result.content}"
            )
        if not result.content:
            raise RuntimeError("Microsoft Calendar MCP returned empty content")

        data = json.loads(result.content[0].text)
        return self._parse_event(data, calendar["id"])

    async def update_event(self, event: CalendarEvent) -> CalendarEvent:
        body = {
            "subject": event.title,
            "start": self._parse_time(event.start_time),
            "end": self._parse_time(event.end_time),
            "location": {"displayName": event.location},
            "attendees": [
                {
                    "emailAddress": {
                        "address": email
                    },
                    "type": "required"
                }
                for email in (event.attendees or [])
            ],
        }
        if event.show_as is not None:
            body["showAs"] = event.show_as

        calendar_id = event.calendar_id

        if calendar_id is None:
            calendar_id = await self._find_calendar_id(event.id)

        if calendar_id is None:
            raise RuntimeError(
                f"Microsoft calendar not found for event: {event.id}"
            )

        result = await self.mcp_client.call_tool(
            "update-specific-calendar-event",
            {
                "calendarId": calendar_id,
                "eventId": event.id,
                "body": body,
            }
        )

        if result.isError:
            raise RuntimeError(
                f"Failed to update Microsoft calendar event: {result.content}"
            )
        if not result.content:
            raise RuntimeError("Microsoft Calendar MCP returned empty content")

        data = json.loads(result.content[0].text)
        return self._parse_event(data, calendar_id)

    async def delete_event(self, event_id: str) -> None:
        calendar_id = await self._find_calendar_id(event_id)

        if calendar_id is None:
            raise RuntimeError(
                f"Microsoft calendar not found for event: {event_id}"
            )

        result = await self.mcp_client.call_tool(
            "delete-specific-calendar-event",
            {
                "calendarId": calendar_id,
                "eventId": event_id,
            }
        )
        if result.isError:
            raise RuntimeError(
                f"Failed to delete Microsoft calendar event: {result.content}"
            )


    async def _list_calendars(self) -> list[dict]:
        result = await self.mcp_client.call_tool(
            "list-calendars",
            {}
        )

        if result.isError:
            raise RuntimeError(f"Failed to list Microsoft calendars: {result.content}")

        if not result.content:
            return []
        data = json.loads(result.content[0].text)

        return data.get("value", [])

    async def _find_calendar_id(self, event_id: str) -> str | None:
        calendars = await self._list_calendars()

        for calendar in calendars:
            result = await self.mcp_client.call_tool(
                "get-specific-calendar-event",
                {
                    "calendarId": calendar["id"],
                    "eventId": event_id,
                    "timezone": "Asia/Singapore",
                },
            )
            if not result.isError:
                return calendar["id"]
        return None


    async def _list_calendar_event(
            self,
            calendar_id: str,
            start_time: datetime,
            end_time: datetime
    ) -> list[CalendarEvent]:
        result = await self.mcp_client.call_tool(
            "get-specific-calendar-view",
            {
                "calendarId": calendar_id,
                "startDateTime": start_time.isoformat(),
                "endDateTime": end_time.isoformat(),
                "timezone": "Asia/Singapore"
            }
        )

        if result.isError:
            raise RuntimeError(f"Failed to list Microsoft calendars: {result.content}")

        if not result.content:
            return []

        data = json.loads(result.content[0].text)

        return [
            self._parse_event(event, calendar_id)
            for event in data.get("value", [])
        ]

    @staticmethod
    def _parse_datetime(value: dict) -> datetime:
        dt = datetime.fromisoformat(value["dateTime"])
        timezone = ZoneInfo(value["timeZone"])

        return dt.replace(tzinfo=timezone)

    def _parse_event(self, event: dict, calendar_id: str) -> CalendarEvent:
        return CalendarEvent(
            id=event["id"],
            calendar_id=calendar_id,
            title=event.get("subject") or "",
            start_time=self._parse_datetime(event["start"]),
            end_time=self._parse_datetime(event["end"]),
            location=event.get("location", {}).get("displayName") or None,
            attendees=[
                attendee["emailAddress"]["address"]
                for attendee in event.get("attendees", [])
                if attendee.get("emailAddress", {}).get("address")
            ],
            status="cancelled" if event.get("isCancelled") else "confirmed",
            show_as=event.get("showAs")
        )

    async def _get_default_calendar(self) -> dict:
        calendars = await self._list_calendars()

        default_calendar = next(
            (
                calendar
                for calendar in calendars
                if calendar.get("isDefaultCalendar")
            ),
            None
        )

        if default_calendar is None:
            raise RuntimeError(f"Microsoft default calendar not found")

        return default_calendar

    @staticmethod
    def _parse_time(time: datetime) -> dict:
        return {
            "dateTime": time.replace(tzinfo=None).isoformat(),
            "timeZone": "Asia/Singapore",
        }
