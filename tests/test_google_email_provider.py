import base64
from unittest.mock import patch, Mock

import pytest

from models.email import Email
from providers.google.gmail_provider import GmailProvider


def google_provider():
    with patch('providers.google.gmail_provider.build') as build:
        client = build.return_value
        provider = GmailProvider(Mock())
    return provider, client

def gmail_response(value):
    command = Mock()
    command.execute.return_value = value
    return command

@pytest.mark.asyncio
async def test_google_search_emails():
    provider, client = google_provider()
    messages = client.users.return_value.messages.return_value
    messages.list.return_value = gmail_response({'messages': [{'id': 'msg-1'}]})
    messages.get.return_value = gmail_response({'id': 'msg-1', 'payload': {
        'headers': [{'name': 'Subject', 'value': 'Hello'}]}})
    result = await provider.search_emails('Hello')
    assert len(result) == 1 and result[0].subject == 'Hello'
    messages.list.assert_called_once_with(userId='me', q='Hello', maxResults=100)


@pytest.mark.asyncio
async def test_google_get_email_body():
    provider, client = google_provider()
    encoded = base64.urlsafe_b64encode(b'Hello body').decode()
    messages = client.users.return_value.messages.return_value
    messages.get.return_value = gmail_response({'id': 'msg-1', 'payload': {
        'headers': [], 'mimeType': 'text/plain', 'body': {'data': encoded}}})
    result = await provider.get_email('msg-1')
    assert result.body == 'Hello body'
    messages.get.assert_called_once_with(userId='me', id='msg-1', format='full')


@pytest.mark.asyncio
async def test_google_create_draft():
    provider, client = google_provider()
    drafts = client.users.return_value.drafts.return_value
    drafts.create.return_value = gmail_response({'id': 'draft-1', 'message': {'id': 'msg-1'}})
    result = await provider.create_draft(['alice@example.com'], 'Hello', 'Body')
    assert result.draft_id == 'draft-1' and result.id == 'msg-1'
    kwargs = drafts.create.call_args.kwargs
    assert kwargs['userId'] == 'me'
    raw = base64.urlsafe_b64decode(kwargs['body']['message']['raw'])
    assert b'alice@example.com' in raw and b'Hello' in raw


@pytest.mark.asyncio
async def test_google_invalid_recipient():
    provider, client = google_provider()
    with pytest.raises(ValueError, match='Invalid recipient'):
        await provider.create_draft(['not-an-email'], 'Hello', 'Body')
    client.users.assert_not_called()


@pytest.mark.asyncio
async def test_google_get_draft():
    provider, client = google_provider()
    drafts = client.users.return_value.drafts.return_value
    drafts.get.return_value = gmail_response({'id': 'draft-1', 'message': {
        'id': 'msg-1', 'payload': {'headers': []}}})
    result = await provider.get_draft('draft-1')
    assert result.draft_id == 'draft-1' and result.id == 'msg-1'


@pytest.mark.asyncio
async def test_google_update_draft():
    provider, client = google_provider()
    drafts = client.users.return_value.drafts.return_value
    drafts.update.return_value = gmail_response({'message': {'id': 'new-msg'}})
    email = Email(id='old-msg', draft_id='draft-1', recipients=['alice@example.com'], subject='Updated', body='Body')
    result = await provider.update_draft(email)
    assert result.id == 'new-msg'
    assert drafts.update.call_args.kwargs['id'] == 'draft-1'


@pytest.mark.asyncio
async def test_google_update_requires_draft_id():
    provider, _ = google_provider()
    with pytest.raises(ValueError, match='Draft id is required'):
        await provider.update_draft(Email(id='msg-1'))


@pytest.mark.asyncio
async def test_google_send_draft():
    provider, client = google_provider()
    drafts = client.users.return_value.drafts.return_value
    drafts.send.return_value = gmail_response({'id': 'sent-1'})
    assert await provider.send_email('draft-1') == 'sent-1'
    drafts.send.assert_called_once_with(userId='me', body={'id': 'draft-1'})
