from unittest.mock import AsyncMock, Mock
import pytest
from models.contact import Contact
from tools.contact.contact_tools import build_contact_tools

@pytest.fixture
def setup():
    provider = Mock()
    for name in ('create_contact','update_contact','search_contact','delete_contact'):
        setattr(provider, name, AsyncMock())
    tools = {tool.name: tool for tool in build_contact_tools(provider)}
    return provider, tools

@pytest.fixture
def contact():
    return Contact(id='contact-1', given_name='Alice', family_name='Lee', emails=['alice@example.com'], phone_numbers=['12345678'])

@pytest.mark.asyncio
async def test_create_contact(setup, contact):
    provider, tools = setup
    provider.create_contact.return_value = contact
    result = await tools['create_contact'].ainvoke({'given_name':'Alice','family_name':'Lee','emails':['alice@example.com'],'phone_numbers':['12345678']})
    assert result.success is True
    assert result.contact == contact
    provider.create_contact.assert_awaited_once_with('Alice','Lee',['alice@example.com'],['12345678'])

@pytest.mark.asyncio
async def test_search_contact(setup, contact):
    provider, tools = setup
    provider.search_contact.return_value = [contact]
    result = await tools['search_contact'].ainvoke({'query':'Alice'})
    assert result.success is True
    assert result.contacts == [contact]
    provider.search_contact.assert_awaited_once_with('Alice')

@pytest.mark.asyncio
async def test_search_no_results(setup):
    provider, tools = setup
    provider.search_contact.return_value = []
    result = await tools['search_contact'].ainvoke({'query':'Unknown'})
    assert result.contacts == []

@pytest.mark.asyncio
async def test_update_contact(setup, contact):
    provider, tools = setup
    provider.update_contact.return_value = contact
    result = await tools['update_contact'].ainvoke({'contact_id':'contact-1','emails':['alice@example.com']})
    assert result.success is True
    assert result.contact == contact
    sent = provider.update_contact.await_args.args[0]
    assert isinstance(sent, Contact)
    assert sent.id == 'contact-1'
    assert sent.emails == ['alice@example.com']
    assert sent.given_name is None
    assert sent.family_name is None

@pytest.mark.asyncio
async def test_delete_contact(setup):
    provider, tools = setup
    result = await tools['delete_contact'].ainvoke({'contact_id':'contact-1'})
    assert result.success is True
    assert result.contact_id == 'contact-1'
    provider.delete_contact.assert_awaited_once_with('contact-1')

@pytest.mark.asyncio
async def test_create_contact_invalid_email(setup):
    provider, tools = setup
    result = await tools['create_contact'].ainvoke({'given_name':'Alice','emails':['not-an-email']})
    assert isinstance(result, str)
    assert 'Invalid contact information' in result
    provider.create_contact.assert_not_awaited()
