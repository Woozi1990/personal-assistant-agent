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
    CheckAvailabilityToolInput, CreateEventToolOutput, ListEventsToolOutput, UpdateEventToolOutput,
    DeleteEventToolOutput, CheckAvailabilityToolOutput
)


def build_calendar_tools(
        calendar_provider: CalendarProvider,
) -> list[BaseTool]:
    @tool(args_schema=CreateEventToolInput)
    def create_event(
            title: str,
            start_time: str,
            end_time: str | None = None,
            location: str | None = None,
            attendees: list[str] | None = None,
    ) -> CreateEventToolOutput:
        """
        Create a calendar event.

        Before creating an event, use check_availability to check the
        requested time range. Only create the event if is_available=True.

        If the user does not specify an end time, use a default duration
        of one hour.

        The attendees argument must contain real email addresses.
        If the user provides only a person's name, use an available
        contact tool to obtain the email address first.

        Never invent or guess an attendee email address.

        Output:
        - success: whether the creation completed successfully
        - event: created calendar event
            - id
            - title
            - start_time
            - end_time
            - location
            - attendees
            - status
        """

        parsed_start_time = _parse_datetime(start_time)

        if end_time:
            parsed_end_time = _parse_datetime(end_time)
        else:
            parsed_end_time = parsed_start_time + timedelta(hours=1)

        event = calendar_provider.create_event(
            title=title,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            location=location,
            attendees=attendees)

        return CreateEventToolOutput(
            success=True,
            event=event,
        )

    @tool(args_schema=ListEventsToolInput)
    def list_events(
            start_time: str,
            end_time: str,
            query: str | None = None
    ) -> ListEventsToolOutput:
        """
        Search calendar events requested by the user.

        Use this tool when the user asks about their schedule,
        calendar events, or what they have planned during a period.

        Convert natural-language time periods into precise datetime ranges:
        - whole day: 00:00:00 to 23:59:59
        - morning: 08:00:00 to 12:00:00
        - afternoon: 12:00:00 to 18:00:00
        - evening: 18:00:00 to 23:59:59

        Output:
        - success: whether the search completed successfully
        - events: matching saved calendar events
            - id
            - title
            - start_time
            - end_time
            - location
            - attendees
            - status
        """

        parsed_start_time = _parse_datetime(start_time)
        parsed_end_time = _parse_datetime(end_time)

        events = calendar_provider.list_events(
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            query=query,
        )
        return ListEventsToolOutput(
            success=True,
            events=events,
        )

    @tool(args_schema=UpdateEventToolInput)
    def update_event(
            event_id: str,
            title: str,
            start_time: str,
            end_time: str,
            event_status: str,
            location: str | None = None,
            attendees: list[str] | None = None,
    ) -> UpdateEventToolOutput:
        """
        Update an existing calendar event.

        Use this tool when the user wants to modify an existing event.

        The event_id must come from a previous tool result and must not be invented.

        If the event time is being changed, first use check_availability
        for the new time range. Only update the event if is_available=True.

        Output:
        - success: whether the update completed successfully
        - event: updated event
            - id
            - title
            - start_time
            - end_time
            - location
            - attendees
            - status
        """

        parsed_start_time = _parse_datetime(start_time)
        parsed_end_time = _parse_datetime(end_time)

        event = CalendarEvent(
            id=event_id,
            title=title,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            location=location,
            attendees=attendees,
            status=event_status
        )
        updated_event = calendar_provider.update_event(event)
        return UpdateEventToolOutput(
            success=True,
            event=updated_event,
        )

    @tool(args_schema=DeleteEventToolInput)
    def delete_event(event_id: str, ) -> DeleteEventToolOutput:
        """
        Delete a calendar event for the user.
        Use this tool when the user asks to delete a meeting,
        appointment, event, or reminder at a specific date and time.

        When deleting an existing calendar event, first search for the event to obtain its event ID and current details.

        Output:
        - success: whether the deletion completed successfully
        - event_id: deleted event ID
        """

        calendar_provider.delete_event(event_id)

        return DeleteEventToolOutput(
            success=True,
            event_id=event_id
        )

    @tool(args_schema=CheckAvailabilityToolInput)
    def check_availability(
            start_time: str,
            end_time: str,
    ) -> CheckAvailabilityToolOutput:
        """
        Check whether a requested calendar time range is available.

        Output:
        - success: Whether the calendar event check completed successfully.
        - is_available: Whether the calendar event is available in the time range from start_time to end_time.

        This tool produces the availability result required by
        calendar operations that create or reschedule an event.
        """
        parsed_start_time = _parse_datetime(start_time)
        parsed_end_time = _parse_datetime(end_time)

        is_available = calendar_provider.check_availability(
            start_time=parsed_start_time,
            end_time=parsed_end_time,
        )
        return CheckAvailabilityToolOutput(
            success=True,
            is_available=is_available,
        )

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
