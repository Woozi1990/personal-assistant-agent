import json
from calendar import Calendar
from datetime import datetime

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
        print([(calendar["name"], calendar["id"])for calendar in calendars])
        return []

    async def _list_calendars(self) -> list[dict]:
        result = await self.mcp_client.call_tool(
            "list-calendars",
            {}
        )

        if result.isError:
            raise RuntimeError("Failed to list Microsoft calendars")

        if not result.content:
            return []
        data = json.loads(result.content[0].text)

        return data.get("value", [])
