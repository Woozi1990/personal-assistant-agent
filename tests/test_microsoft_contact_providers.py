import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.contact import Contact
from providers.microsoft.microsoft_contact_provider import MicrosoftContactProvider


def mcp_result(data=None, *, error=False):
    return SimpleNamespace(isError=error, content=[SimpleNamespace(text=json.dumps(data))] if data is not None else [])


@pytest.fixture
def microsoft():
    client = MagicMock()
    client.call_tool = AsyncMock()
    return MicrosoftContactProvider(client), client


@pytest.mark.asyncio
async def test_microsoft_create_contact(microsoft):
    provider, client = microsoft
    client.call_tool.return_value = mcp_result(
        {'id': '123', 'givenName': 'Alice', 'surname': 'Smith', 'emailAddresses': [{'address': 'alice@example.com'}]})
    result = await provider.create_contact('Alice', 'Smith', ['alice@example.com'], ['123456'])
    assert result.id == '123'
    assert result.emails == ['alice@example.com']
    client.call_tool.assert_awaited_once_with('create-outlook-contact', {
        'body': {'givenName': 'Alice', 'surname': 'Smith',
                 'emailAddresses': [{'address': 'alice@example.com', 'name': 'Alice Smith'}],
                 'businessPhones': ['123456']}})


@pytest.mark.asyncio
async def test_microsoft_update_contact(microsoft):
    provider, client = microsoft
    client.call_tool.side_effect = [mcp_result({'id': '123'}), mcp_result({'id': '123', 'givenName': 'Alice'})]
    result = await provider.update_contact(Contact(id='123', given_name='Alice'))
    assert result.given_name == 'Alice'
    assert client.call_tool.await_args_list[0].args == ('get-outlook-contact', {'contactId': '123', 'select': 'id'})
    assert client.call_tool.await_args_list[1].args == ('update-outlook-contact',
                                                        {'contactId': '123', 'body': {'givenName': 'Alice'}})


@pytest.mark.asyncio
async def test_microsoft_search_contact(microsoft):
    provider, client = microsoft
    client.call_tool.return_value = mcp_result(
        {'value': [{'id': '123', 'givenName': 'Alice', 'businessPhones': ['111'], 'mobilePhone': '222'}]})
    result = await provider.search_contact('Alice')
    assert len(result) == 1
    assert result[0].phone_numbers == ['111', '222']
    client.call_tool.assert_awaited_once_with('list-outlook-contacts', {
        'select': 'id,givenName,surname,emailAddresses,businessPhones,homePhones,mobilePhone', 'search': '"Alice"',
        'top': 10})


@pytest.mark.asyncio
async def test_microsoft_delete_contact(microsoft):
    provider, client = microsoft
    client.call_tool.return_value = mcp_result()
    await provider.delete_contact('123')
    client.call_tool.assert_awaited_once_with('delete-outlook-contact', {'contactId': '123'})


@pytest.mark.asyncio
async def test_microsoft_create_error(microsoft):
    provider, client = microsoft
    client.call_tool.return_value = mcp_result({'error': 'failure'}, error=True)
    with pytest.raises(RuntimeError, match='Failed to create'):
        await provider.create_contact(given_name='Alice')
