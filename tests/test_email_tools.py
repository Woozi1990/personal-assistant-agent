from unittest.mock import AsyncMock, Mock
import pytest
from models.email import Email
from tools.email.email_tools import build_email_tools

@pytest.fixture
def setup():
    provider = Mock()
    for name in ('search_emails','get_email','create_draft','get_draft','update_draft','send_email'):
        setattr(provider, name, AsyncMock())
    tools = {tool.name: tool for tool in build_email_tools(provider)}
    return provider, tools

@pytest.fixture
def email():
    return Email(id='message-1', draft_id='draft-1', recipients=['alice@example.com'], subject='Original subject', body='Original body')

@pytest.mark.asyncio
async def test_search_emails(setup, email):
    provider, tools = setup
    provider.search_emails.return_value = [email]
    result = await tools['search_emails'].ainvoke({'query':'meeting'})
    assert result.success is True
    assert result.emails == [email]
    provider.search_emails.assert_awaited_once_with('meeting')

@pytest.mark.asyncio
async def test_search_emails_empty(setup):
    provider, tools = setup
    provider.search_emails.return_value = []
    result = await tools['search_emails'].ainvoke({'query':'missing'})
    assert result.emails == []

@pytest.mark.asyncio
async def test_get_email_message(setup, email):
    provider, tools = setup
    provider.get_email.return_value = email
    result = await tools['get_email_message'].ainvoke({'message_id':'message-1'})
    assert result.success is True
    assert result.email == email
    provider.get_email.assert_awaited_once_with('message-1')

@pytest.mark.asyncio
async def test_create_draft(setup, email):
    provider, tools = setup
    provider.create_draft.return_value = email
    result = await tools['create_draft'].ainvoke({'recipients':['alice@example.com'],'subject':'Original subject','body':'Original body'})
    assert result.success is True
    assert result.draft == email
    provider.create_draft.assert_awaited_once_with(['alice@example.com'],'Original subject','Original body')

@pytest.mark.asyncio
async def test_update_draft_subject_only(setup, email):
    provider, tools = setup
    provider.get_draft.return_value = email
    provider.update_draft.side_effect = lambda draft: draft
    result = await tools['update_draft'].ainvoke({'draft_id':'draft-1','subject':'New subject'})
    assert result.success is True
    assert result.draft.subject == 'New subject'
    assert result.draft.body == 'Original body'
    assert result.draft.recipients == ['alice@example.com']
    provider.get_draft.assert_awaited_once_with('draft-1')
    provider.update_draft.assert_awaited_once_with(email)

@pytest.mark.asyncio
async def test_update_draft_body_and_recipients(setup, email):
    provider, tools = setup
    provider.get_draft.return_value = email
    provider.update_draft.side_effect = lambda draft: draft
    result = await tools['update_draft'].ainvoke({'draft_id':'draft-1','body':'New body','recipients':['bob@example.com']})
    assert result.draft.subject == 'Original subject'
    assert result.draft.body == 'New body'
    assert result.draft.recipients == ['bob@example.com']

@pytest.mark.asyncio
async def test_send_email(setup):
    provider, tools = setup
    provider.send_email.return_value = 'sent-message-1'
    result = await tools['send_email'].ainvoke({'draft_id':'draft-1'})
    assert result.success is True
    assert result.message_id == 'sent-message-1'
    provider.send_email.assert_awaited_once_with('draft-1')
