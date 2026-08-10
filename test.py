import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from providers.google.google_auth_service import GoogleAuthService
from providers.google.mcp_calendar_provider import MCPCalendarProvider


async def main():
    auth_service = GoogleAuthService(
        scopes=[
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/contacts",
        ]
    )

    provider = MCPCalendarProvider(auth_service)

    events = await provider.list_events(
        start_time=datetime(
            2026, 8, 10, 0, 0,
            tzinfo=ZoneInfo("Asia/Singapore")
        ),
        end_time=datetime(
            2026, 8, 10, 23, 59, 59,
            tzinfo=ZoneInfo("Asia/Singapore")
        ),
    )

    print(events)
asyncio.run(main())