from dataclasses import dataclass
from datetime import datetime


@dataclass
class CalendarEvent:
    id:str
    title:str
    start_time:datetime
    end_time:datetime
    location:str|None
    attendees:list[str]|None
    status:str