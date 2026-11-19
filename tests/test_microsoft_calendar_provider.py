import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from models.calendar_event import CalendarEvent
from providers.microsoft.microsoft_calendar_provider import MicrosoftCalendarProvider

START = datetime.fromisoformat('2026-10-20T15:00:00+08:00')
END = datetime.fromisoformat('2026-10-20T16:00:00+08:00')


def response(data=None, error=False):
    return SimpleNamespace(isError=error, content=[] if data is None else [SimpleNamespace(text=json.dumps(data))])


def graph_event(event_id='e1', show_as='busy'):
    return {
        'id': event_id, 'subject': 'Meeting',
        'start': {'dateTime': '2026-10-20T15:00:00', 'timeZone': 'Asia/Singapore'},
        'end': {'dateTime': '2026-10-20T16:00:00', 'timeZone': 'Asia/Singapore'},
        'showAs': show_as, 'isCancelled': False,
    }


def calendar_event(calendar_id='c1'):
    return CalendarEvent(id='e1', calendar_id=calendar_id, title='Meeting', start_time=START,
                         end_time=END, status='confirmed', show_as='busy')


@pytest.fixture
def provider():
    client = SimpleNamespace(call_tool=AsyncMock())
    return MicrosoftCalendarProvider(client), client


@pytest.mark.asyncio
async def test_list_events_all_calendars(provider):
    obj, client = provider
    async def call(name, args):
        if name == 'list-calendars':
            return response({'value': [{'id': 'c1'}, {'id': 'c2'}]})
        if name == 'get-specific-calendar-view':
            return response({'value': [graph_event(args['calendarId'] + '-event')]})
        raise AssertionError(name)
    client.call_tool.side_effect = call
    result = await obj.list_events(START, END)
    assert {e.calendar_id for e in result} == {'c1', 'c2'}
    assert {e.id for e in result} == {'c1-event', 'c2-event'}


@pytest.mark.asyncio
@pytest.mark.parametrize('show_as,expected', [('free', True), ('busy', False), ('tentative', False)])
async def test_check_availability(provider, show_as, expected):
    obj, _ = provider
    obj.list_events = AsyncMock(return_value=[calendar_event().model_copy(update={'show_as': show_as})])
    assert await obj.check_availability(START, END) is expected
    assert await obj.check_availability(START, END, exclude_event_id='e1') is True


@pytest.mark.asyncio
async def test_create_event(provider):
    obj, client = provider
    async def call(name, args):
        if name == 'list-calendars':
            return response({'value': [{'id': 'c1', 'isDefaultCalendar': True}]})
        if name == 'create-specific-calendar-event':
            assert args['calendarId'] == 'c1'
            assert args['body']['showAs'] == 'busy'
            assert args['body']['attendees'][0]['emailAddress']['address'] == 'a@example.com'
            return response(graph_event())
        raise AssertionError(name)
    client.call_tool.side_effect = call
    result = await obj.create_event('Meeting', START, END, attendees=['a@example.com'])
    assert result.id == 'e1'
    assert result.calendar_id == 'c1'


@pytest.mark.asyncio
async def test_update_event(provider):
    obj, client = provider
    client.call_tool.return_value = response(graph_event())
    result = await obj.update_event(calendar_event())
    assert result.id == 'e1'
    assert client.call_tool.await_args.args[0] == 'update-specific-calendar-event'
    assert client.call_tool.await_args.args[1]['calendarId'] == 'c1'


@pytest.mark.asyncio
async def test_delete_event(provider):
    obj, client = provider
    async def call(name, args):
        if name == 'list-calendars':
            return response({'value': [{'id': 'c1'}]})
        if name == 'get-specific-calendar-event':
            return response(graph_event())
        if name == 'delete-specific-calendar-event':
            assert args == {'calendarId': 'c1', 'eventId': 'e1'}
            return response()
        raise AssertionError(name)
    client.call_tool.side_effect = call
    await obj.delete_event('e1')


@pytest.mark.asyncio
async def test_mcp_error(provider):
    obj, client = provider
    client.call_tool.return_value = response({'message': 'failure'}, error=True)
    with pytest.raises(RuntimeError, match='Failed to list Microsoft calendars'):
        await obj.list_events(START, END)


@pytest.mark.asyncio
async def test_missing_default_calendar(provider):
    obj, client = provider
    client.call_tool.return_value = response({'value': [{'id': 'c1'}]})
    with pytest.raises(RuntimeError, match='default calendar not found'):
        await obj.create_event('Meeting', START, END)
