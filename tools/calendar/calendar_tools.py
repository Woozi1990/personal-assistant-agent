from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_core.tools import tool, BaseTool
from models.calendar_event import CalendarEvent
from providers.interfaces.calendar_provider import CalendarProvider

from tools.calendar.schemas import (
    CreateEventToolInput,
    ListEventsToolInput,
    UpdateEventToolInput,
    DeleteEventToolInput,
    CheckAvailabilityToolInput
)


def build_calendar_tools(
        calendar_provider: CalendarProvider,
) -> list[BaseTool]:
    @tool(args_schema=CreateEventToolInput)
    async def create_event(
            title: str,
            start_time: str,
            end_time: str | None = None,
            location: str | None = None,
            attendees: list[str] | None = None,
    ):
        """
        Create a calendar event for the user.
        Use this tool when the user asks to schedule a meeting,
        appointment, event, or reminder at a specific date and time.

        The requested time must already have been confirmed as available.
        """

        parsed_start_time = datetime.fromisoformat(start_time)

        if end_time:
            parsed_end_time = datetime.fromisoformat(end_time)
        else:
            parsed_end_time = parsed_start_time + timedelta(hours=1)

        event = await calendar_provider.create_event(
            title=title,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            location=location,
            attendees=attendees)

        return {
            "success": True,
            "event": event
        }

    @tool(args_schema=ListEventsToolInput)
    async def list_events(
            start_time: str,
            end_time: str,
            query: str | None = None
    ):
        """
        Search calendar events requested by the user.

        Use this tool when the user asks about their schedule,
        calendar events, or what they have planned during a period.

        Convert natural-language time periods into precise datetime ranges:
        - whole day: 00:00:00 to 23:59:59
        - morning: 08:00:00 to 12:00:00
        - afternoon: 12:00:00 to 18:00:00
        - evening: 18:00:00 to 23:59:59
        """

        parsed_start_time = _parse_datetime(start_time)
        parsed_end_time = _parse_datetime(end_time)

        events = await calendar_provider.list_events(
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            query=query,
        )
        return {
            "success": True,
            "events": events
        }

    @tool(args_schema=UpdateEventToolInput)
    async def update_event(
            event_id: str,
            title: str,
            start_time: str,
            end_time: str,
            event_status: str,
            location: str | None = None,
            attendees: list[str] | None = None,
    ):
        """
        Update an existing calendar event.

        Use this tool when the user wants to change an existing meeting,
        appointment, event, or reminder.

        This tool requires the existing event ID and current event details.
        Do not use it to create a new event.
        """

        parsed_start_time = datetime.fromisoformat(start_time)
        parsed_end_time = datetime.fromisoformat(end_time)

        event = CalendarEvent(
            id=event_id,
            title=title,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            location=location,
            attendees=attendees,
            status=event_status
        )
        updated_event =await calendar_provider.update_event(event)
        return {
            "success": True,
            "event": updated_event
        }

    @tool(args_schema=DeleteEventToolInput)
    async def delete_event(event_id: str, ):
        """
        Delete a calendar event for the user.
        Use this tool when the user asks to delete a meeting,
        appointment, event, or reminder at a specific date and time.

        When deleting an existing calendar event, first search for the event to obtain its event ID and current details.
        """

        await calendar_provider.delete_event(event_id)

        return {
            "success": True,
            "event_id": event_id
        }

    @tool(args_schema=CheckAvailabilityToolInput)
    async def check_availability(
            start_time: str,
            end_time: str,
    ):
        """
        Check whether a specific time range is available.

        This tool is required before creating or rescheduling a calendar
        event at a specific time.

        Use list_events instead for general schedule questions such as
        "Am I free tomorrow?" or "What do I have tomorrow?".
        """
        parsed_start_time = _parse_datetime(start_time)
        parsed_end_time = _parse_datetime(end_time)

        is_available = await calendar_provider.check_availability(
            start_time=parsed_start_time,
            end_time=parsed_end_time,
        )
        return {
            "success": True,
            "is_available": is_available,
        }

    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=ZoneInfo("Asia/Singapore")
            )

        return parsed

    return [
        create_event,
        list_events,
        update_event,
        delete_event,
        check_availability,
    ]
