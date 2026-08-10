from datetime import datetime

from google.auth.transport.requests import Request
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from models.calendar_event import CalendarEvent
from providers.google.google_auth_service import GoogleAuthService
from providers.interfaces.calendar_provider import CalendarProvider


class MCPCalendarProvider(CalendarProvider):
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service

    async def _get_mcp_tools(self) -> list[BaseTool]:
        credentials = self.auth_service.get_credentials()
        if credentials.expired or not credentials.token:
            credentials.refresh(Request())

        client = MultiServerMCPClient(
            {
                "calendar": {
                    "transport": "http",
                    "url": "https://calendarmcp.googleapis.com/mcp/v1",
                    "headers": {
                        "Authorization": f"Bearer {credentials.token}"
                    },
                }
            }
        )

        return await client.get_tools()

    async def _get_mcp_tool(self, tool_name:str)->BaseTool:
        tools =await self._get_mcp_tools()

        for tool in tools:
            if tool.name == tool_name:
                return tool

        raise RuntimeError(f"No tool named {tool_name}")

    async def create_event(self, title: str, start_time: datetime, end_time:datetime|None, location: str | None = None,
                     attendees: list[str] | None = None) -> CalendarEvent:
        pass

    async def update_event(self, event: CalendarEvent) -> CalendarEvent:
        pass

    async def list_events(self, start_time:datetime, end_time:datetime, query: str | None=None) -> list[CalendarEvent]:
        list_events_tool = await self._get_mcp_tool(
            "list_events"
        )
        print("Tool Input Schema:", list_events_tool.args)

        arguments = {
            "calendarId": "primary",
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "orderBy": "startTime",
            "timeZone":"Asia/Singapore",
        }

        if query:
            arguments["fullText"] = query

        print(f"Executing tool with arguments: {arguments}")
        result = await list_events_tool.ainvoke(arguments)
        print(result)
        return []

    async def delete_event(self, event_id:str) ->None:
        pass

    async def check_availability(self, start_time:datetime, end_time:datetime) ->bool:
        pass

