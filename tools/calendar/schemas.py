from pydantic import BaseModel, Field


class CreateEventToolInput(BaseModel):
    title: str = Field(
        description="The title of the calendar event"
    )
    start_time: str = Field(
        description=(
            "Start date and time of the event in ISO 8601 format, "
            "for example 2026-08-06T15:00:00+08:00."
        )
    )
    end_time: str | None = Field(
        default=None,
        description=(
            "End date and time of the event in ISO 8601 format. "
            "Leave this unset if the user did not specify an end time."
        )
    )
    location: str | None = Field(
        default=None,
        description=(
            "Physical location, address, room, or online meeting location "
            "explicitly associated with the event."
        )
    )
    attendees: list[str] | None = Field(
        default=None,
        description=(
            "Email addresses of event attendees. "
            "Use only email addresses explicitly provided by the user "
            "or returned by a tool result. "
            "Do not infer, guess, or fabricate email addresses from attendee names."
        )
    )


class ListEventsToolInput(BaseModel):
    start_time: str = Field(
        description=(
            "Start of the calendar search range in ISO 8601 format."
        )
    )
    end_time: str = Field(
        description=(
            "End of the calendar search range in ISO 8601 format."
        )
    )
    query: str | None = Field(
        default=None,
        description=(
            "Optional text used to filter calendar events by relevant event content, "
            "such as title or other searchable event information. "
            "Leave unset when the user only specifies a time range."
        )
    )


class UpdateEventToolInput(BaseModel):
    event_id: str = Field(
        description=(
            "Unique ID of the existing calendar event to update. "
            "Use an event ID returned by a calendar search result; "
            "do not invent or guess this value."
        )
    )
    title: str = Field(
        description="Title of the existing calendar event."
    )
    start_time: str = Field(
        description="Start date and time of the event in ISO 8601 format."
    )
    end_time: str = Field(
        description="End date and time of the event in ISO 8601 format."
    )
    event_status: str = Field(
        description="Current status of the existing calendar event."
    )
    location: str | None = Field(
        default=None,
        description="Physical or online location of the calendar event."
    )
    attendees: list[str] | None = Field(
        default=None,
        description=(
            "Email addresses of event attendees. "
            "Use only addresses explicitly provided by the user "
            "or returned by a tool result. "
            "Do not infer, guess, or fabricate email addresses."
        )
    )


class DeleteEventToolInput(BaseModel):
    event_id: str = Field(
        description=(
            "Unique ID of the existing calendar event to delete. "
            "Use an event ID returned by a calendar search result; "
            "do not invent or guess this value."
        )
    )


class CheckAvailabilityToolInput(BaseModel):
    start_time: str = Field(
        description="Start of the time range to check in ISO 8601 format."
    )
    end_time: str = Field(
        description="End of the time range to check in ISO 8601 format."
    )
