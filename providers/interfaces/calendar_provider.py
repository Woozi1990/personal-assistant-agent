from datetime import datetime
from typing import Protocol

from models.calendar_event import CalendarEvent


class CalendarProvider(Protocol):
    def create_event(self, title: str, start_time: datetime, end_time:datetime, location: str | None = None,
                     attendees: list[str] | None = None)-> CalendarEvent:
        ...

    def list_events(self, start_time:datetime, end_time:datetime, query: str | None=None)-> list[CalendarEvent]:
        ...

    def update_event(self, event:CalendarEvent)-> CalendarEvent:
        ...

    def delete_event(self, event_id:str)->None:
        ...

    def check_availability(self, start_time:datetime, end_time:datetime)->bool:
        ...

