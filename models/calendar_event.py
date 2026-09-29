from datetime import datetime

from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    id: str = Field(description="Unique identifier")
    calendar_id: str|None = Field(
        default=None,
        description="Unique identifier of calendar",
        exclude=True,
        repr=False,
    )
    title: str = Field(description="Title of the event")
    start_time: datetime = Field(description="Start time of the event")
    end_time: datetime = Field(description="End time of the event")
    location: str | None = Field(
        default=None,
        description="Location of the event",
    )
    attendees: list[str] | None = Field(
        default=None,
        description="List of attendees' email addresses",
    )
    status: str = Field(description="Status of the event")
    show_as:str|None = Field(
        default=None,
        description="Free/busy status of the event"
    )
