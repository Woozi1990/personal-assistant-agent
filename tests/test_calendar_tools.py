from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

import pytest

from models.calendar_event import CalendarEvent
from tools.calendar.calendar_tools import build_calendar_tools

START = "2026-10-20T15:00:00+08:00"
END = "2026-10-20T16:00:00+08:00"
ERROR = "The requested time slot is unavailable."


def event(**overrides):
    data = {
        "id": "event-123",
        "title": "Meeting",
        "start_time": datetime.fromisoformat(START),
        "end_time": datetime.fromisoformat(END),
        "status": "confirmed",
    }
    data.update(overrides)
    return CalendarEvent(**data)


@pytest.fixture
def calendar():
    provider = Mock()
    provider.check_availability = AsyncMock()
    provider.create_event = AsyncMock()
    provider.list_events = AsyncMock()
    provider.update_event = AsyncMock()
    provider.delete_event = AsyncMock()
    tools = {tool.name: tool for tool in build_calendar_tools(provider)}
    return provider, tools


@pytest.mark.asyncio
async def test_create_event_default_duration(calendar):
    provider, tools = calendar
    provider.check_availability.return_value = True
    provider.create_event.return_value = event()

    result = await tools["create_event"].ainvoke({"title": "Meeting", "start_time": START})

    assert result.success is True
    assert result.event.id == "event-123"
    provider.check_availability.assert_awaited_once_with(
        datetime.fromisoformat(START), datetime.fromisoformat(END)
    )
    provider.create_event.assert_awaited_once_with(
        title="Meeting", start_time=datetime.fromisoformat(START),
        end_time=datetime.fromisoformat(END), location=None, attendees=None
    )


@pytest.mark.asyncio
async def test_create_event_with_details(calendar):
    provider, tools = calendar
    provider.check_availability.return_value = True
    provider.create_event.return_value = event(location="MBS", attendees=["alice@example.com"])

    result = await tools["create_event"].ainvoke({
        "title": "Meeting", "start_time": START, "end_time": END,
        "location": "MBS", "attendees": ["alice@example.com"],
    })

    assert result.success is True
    assert result.event.location == "MBS"
    provider.create_event.assert_awaited_once_with(
        title="Meeting", start_time=datetime.fromisoformat(START),
        end_time=datetime.fromisoformat(END), location="MBS",
        attendees=["alice@example.com"],
    )


@pytest.mark.asyncio
async def test_create_event_unavailable(calendar):
    provider, tools = calendar
    provider.check_availability.return_value = False

    result = await tools["create_event"].ainvoke({"title": "Meeting", "start_time": START})

    assert result.success is False
    assert result.event is None
    assert result.error == ERROR
    provider.create_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_event_naive_time_uses_singapore_timezone(calendar):
    provider, tools = calendar
    provider.check_availability.return_value = True
    provider.create_event.return_value = event()

    await tools["create_event"].ainvoke({"title": "Meeting", "start_time": "2026-10-20T15:00:00"})

    expected_start = datetime(2026, 10, 20, 15, tzinfo=ZoneInfo("Asia/Singapore"))
    provider.check_availability.assert_awaited_once_with(
        expected_start, expected_start + timedelta(hours=1)
    )


@pytest.mark.asyncio
async def test_list_events(calendar):
    provider, tools = calendar
    provider.list_events.return_value = [event()]

    result = await tools["list_events"].ainvoke({
        "start_time": START, "end_time": END, "query": "Meeting"
    })

    assert result.success is True
    assert len(result.events) == 1
    assert result.events[0].id == "event-123"
    provider.list_events.assert_awaited_once_with(
        start_time=datetime.fromisoformat(START),
        end_time=datetime.fromisoformat(END), query="Meeting"
    )


@pytest.mark.asyncio
async def test_list_events_empty(calendar):
    provider, tools = calendar
    provider.list_events.return_value = []

    result = await tools["list_events"].ainvoke({"start_time": START, "end_time": END})

    assert result.success is True
    assert result.events == []
    provider.list_events.assert_awaited_once_with(
        start_time=datetime.fromisoformat(START),
        end_time=datetime.fromisoformat(END), query=None
    )


@pytest.mark.asyncio
async def test_update_event_success(calendar):
    provider, tools = calendar
    provider.check_availability.return_value = True
    provider.update_event.return_value = event(title="Updated Meeting")

    result = await tools["update_event"].ainvoke({
        "event_id": "event-123", "title": "Updated Meeting",
        "start_time": START, "end_time": END, "event_status": "confirmed",
    })

    assert result.success is True
    assert result.event.title == "Updated Meeting"
    provider.check_availability.assert_awaited_once_with(
        datetime.fromisoformat(START), datetime.fromisoformat(END), "event-123"
    )
    provider.update_event.assert_awaited_once_with(event(title="Updated Meeting"))


@pytest.mark.asyncio
async def test_update_event_unavailable(calendar):
    provider, tools = calendar
    provider.check_availability.return_value = False

    result = await tools["update_event"].ainvoke({
        "event_id": "event-123", "title": "Meeting",
        "start_time": START, "end_time": END, "event_status": "confirmed",
    })

    assert result.success is False
    assert result.event is None
    assert result.error == ERROR
    provider.check_availability.assert_awaited_once_with(
        datetime.fromisoformat(START), datetime.fromisoformat(END), "event-123"
    )
    provider.update_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_event(calendar):
    provider, tools = calendar

    result = await tools["delete_event"].ainvoke({"event_id": "event-123"})

    assert result.success is True
    assert result.event_id == "event-123"
    provider.delete_event.assert_awaited_once_with("event-123")


@pytest.mark.asyncio
@pytest.mark.parametrize("available", [True, False])
async def test_check_availability(calendar, available):
    provider, tools = calendar
    provider.check_availability.return_value = available

    result = await tools["check_availability"].ainvoke({"start_time": START, "end_time": END})

    assert result.success is True
    assert result.is_available is available
    provider.check_availability.assert_awaited_once_with(
        start_time=datetime.fromisoformat(START), end_time=datetime.fromisoformat(END)
    )
