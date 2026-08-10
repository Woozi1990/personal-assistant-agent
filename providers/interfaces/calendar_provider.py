import uuid
from datetime import datetime
from typing import Protocol

from models.calendar_event import CalendarEvent


class CalendarProvider(Protocol):
    async def create_event(self, title: str, start_time: datetime, end_time:datetime, location: str | None = None,
                     attendees: list[str] | None = None)-> CalendarEvent:
        ...

    async def list_events(self, start_time:datetime, end_time:datetime, query: str | None=None)-> list[CalendarEvent]:
        ...

    async def update_event(self, event:CalendarEvent)-> CalendarEvent:
        ...

    async def delete_event(self, event_id:str)->None:
        ...

    async def check_availability(self, start_time:datetime, end_time:datetime)->bool:
        ...

