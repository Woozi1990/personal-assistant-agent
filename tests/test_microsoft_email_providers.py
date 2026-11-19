
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from models.email import Email
from providers.microsoft.microsoft_email_provider import MicrosoftEmailProvider


def microsoft_provider(payload=None, error=False):
    client = Mock()
    client.call_tool = AsyncMock(return_value=SimpleNamespace(
        isError=error,
        content=[SimpleNamespace(text=json.dumps(payload))] if payload is not None else [],
    ))
    return MicrosoftEmailProvider(client), client


def ms_message(**kwargs):
    return {'id': 'msg-1', 'subject': 'Hello', 'toRecipients': [
        {'emailAddress': {'address': 'alice@example.com'}}], **kwargs}


@pytest.mark.asyncio
async def test_microsoft_search_emails():
    provider, client = microsoft_provider({'value': [ms_message()]})
    result = await provider.search_emails('Hello')
    assert len(result) == 1 and result[0].subject == 'Hello'
    name, args = client.call_tool.await_args.args
    assert name == 'list-mail-messages' and args['search'] == '"Hello"'


@pytest.mark.asyncio
async def test_microsoft_get_email():
    provider, client = microsoft_provider(ms_message(body={'content': 'Body'}))
    result = await provider.get_email('msg-1')
    assert result.body == 'Body'
    assert client.call_tool.await_args.args[1]['messageId'] == 'msg-1'


@pytest.mark.asyncio
async def test_microsoft_create_draft():
    provider, client = microsoft_provider(ms_message())
    result = await provider.create_draft(['alice@example.com'], 'Hello', 'Body')
    assert result.draft_id == 'msg-1'
    name, args = client.call_tool.await_args.args
    assert name == 'create-draft-email'
    assert args['body']['isDraft'] is True
    assert args['body']['toRecipients'][0]['emailAddress']['address'] == 'alice@example.com'


@pytest.mark.asyncio
async def test_microsoft_get_draft():
    provider, client = microsoft_provider(ms_message())
    result = await provider.get_draft('msg-1')
    assert result.draft_id == 'msg-1'
    assert client.call_tool.await_args.args[0] == 'get-mail-message'


@pytest.mark.asyncio
async def test_microsoft_update_draft():
    provider, client = microsoft_provider(ms_message(subject='Updated'))
    email = Email(id='msg-1', draft_id='msg-1', subject='Updated', body='Body', recipients=['alice@example.com'])
    result = await provider.update_draft(email)
    assert result.subject == 'Updated'
    name, args = client.call_tool.await_args.args
    assert name == 'update-mail-message' and args['messageId'] == 'msg-1'
    assert args['body']['subject'] == 'Updated'


@pytest.mark.asyncio
async def test_microsoft_update_requires_draft_id():
    provider, client = microsoft_provider()
    with pytest.raises(ValueError, match='Draft id is required'):
        await provider.update_draft(Email(id='msg-1'))
    client.call_tool.assert_not_awaited()


@pytest.mark.asyncio
async def test_microsoft_send_draft():
    provider, client = microsoft_provider()
    assert await provider.send_email('msg-1') == 'msg-1'
    client.call_tool.assert_awaited_once_with('send-draft-message', {'messageId': 'msg-1'})


@pytest.mark.asyncio
async def test_microsoft_mcp_error():
    provider, _ = microsoft_provider(error=True)
    with pytest.raises(RuntimeError, match='Failed to send Microsoft email'):
        await provider.send_email('msg-1')


@pytest.mark.asyncio
async def test_microsoft_empty_content():
    provider, _ = microsoft_provider()
    with pytest.raises(RuntimeError, match='empty content'):
        await provider.get_email('msg-1')
