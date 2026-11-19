from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from models.calendar_event import CalendarEvent
from providers.google.google_calendar_provider import GoogleCalendarProvider

START = datetime.fromisoformat('2026-10-20T15:00:00+08:00')
END = datetime.fromisoformat('2026-10-20T16:00:00+08:00')


def event(event_id='e1'):
    return CalendarEvent(id=event_id, title='Meeting', start_time=START, end_time=END, status='confirmed')


@pytest.fixture
def provider():
    auth = Mock()
    client = Mock()
    with patch('providers.google.google_calendar_provider.build', return_value=client):
        obj = GoogleCalendarProvider(auth)
    return obj, client


@pytest.mark.asyncio
async def test_create_event(provider):
    obj, client = provider
    client.events.return_value.insert.return_value.execute.return_value = {
        'id': 'e1', 'summary': 'Meeting', 'status': 'confirmed', 'location': 'MBS'
    }
    result = await obj.create_event('Meeting', START, END, location='MBS', attendees=['a@example.com'])
    assert result.id == 'e1'
    assert result.attendees == ['a@example.com']
    kwargs = client.events.return_value.insert.call_args.kwargs
    assert kwargs['calendarId'] == 'primary'
    assert kwargs['body']['attendees'] == [{'email': 'a@example.com'}]
    assert kwargs['body']['start']['dateTime'] == START.isoformat()


@pytest.mark.asyncio
async def test_list_events(provider):
    obj, client = provider
    client.events.return_value.list.return_value.execute.return_value = {'items': [
        {'id': 'e1', 'summary': 'Meeting', 'start': {'dateTime': START.isoformat()},
         'end': {'dateTime': END.isoformat()}, 'status': 'confirmed',
         'attendees': [{'email': 'a@example.com'}]}
    ]}
    result = await obj.list_events(START, END, query='Meeting')
    assert len(result) == 1
    assert result[0].attendees == ['a@example.com']
    assert client.events.return_value.list.call_args.kwargs['q'] == 'Meeting'


@pytest.mark.asyncio
async def test_update_event(provider):
    obj, client = provider
    client.events.return_value.patch.return_value.execute.return_value = {
        'id': 'e1', 'summary': 'Meeting', 'start': {'dateTime': START.isoformat()},
        'end': {'dateTime': END.isoformat()}, 'status': 'confirmed'
    }
    result = await obj.update_event(event())
    assert result.id == 'e1'
    assert client.events.return_value.patch.call_args.kwargs['eventId'] == 'e1'


@pytest.mark.asyncio
async def test_delete_event(provider):
    obj, client = provider
    await obj.delete_event('e1')
    assert client.events.return_value.delete.call_args.kwargs['eventId'] == 'e1'


@pytest.mark.asyncio
@pytest.mark.parametrize('existing,excluded,expected', [
    ([], None, True), ([event()], None, False), ([event()], 'e1', True)
])
async def test_check_availability(provider, existing, excluded, expected):
    obj, _ = provider
    obj.list_events = AsyncMock(return_value=existing)
    assert await obj.check_availability(START, END, excluded) is expected
