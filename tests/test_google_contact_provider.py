from unittest.mock import MagicMock, patch

import pytest

from models.contact import Contact
from providers.google.google_contact_provider import GoogleContactProvider


@pytest.fixture
def google():
    auth = MagicMock()
    with patch('providers.google.google_contact_provider.build') as build:
        api = build.return_value
        provider = GoogleContactProvider(auth)
    return provider, api


@pytest.mark.asyncio
async def test_google_create_contact(google):
    provider, api = google
    api.people.return_value.createContact.return_value.execute.return_value = {'resourceName': 'people/123',
                                                                               'names': [{'givenName': 'Alice'}],
                                                                               'emailAddresses': [
                                                                                   {'value': 'alice@example.com'}]}
    result = await provider.create_contact(given_name='Alice', emails=['alice@example.com'])
    assert result.id == 'people/123'
    assert result.emails == ['alice@example.com']
    api.people.return_value.createContact.assert_called_once_with(
        body={'names': [{'givenName': 'Alice', 'familyName': None}],
              'emailAddresses': [{'value': 'alice@example.com'}]})


@pytest.mark.asyncio
async def test_google_search_contact(google):
    provider, api = google
    api.people.return_value.searchContacts.return_value.execute.side_effect = [{}, {
        'results': [{'person': {'resourceName': 'people/123', 'names': [{'givenName': 'Alice'}]}}]}]
    result = await provider.search_contact('Alice')
    assert len(result) == 1
    assert result[0].given_name == 'Alice'
    calls = api.people.return_value.searchContacts.call_args_list
    assert calls[0].kwargs['query'] == ''
    assert calls[1].kwargs['query'] == 'Alice'


@pytest.mark.asyncio
async def test_google_update_contact(google):
    provider, api = google
    api.people.return_value.get.return_value.execute.return_value = {'resourceName': 'people/123', 'names': [
        {'givenName': 'Alice', 'familyName': 'Smith'}]}
    api.people.return_value.updateContact.return_value.execute.return_value = {'resourceName': 'people/123', 'names': [
        {'givenName': 'Alicia', 'familyName': 'Smith'}]}
    result = await provider.update_contact(Contact(id='people/123', given_name='Alicia'))
    assert result.family_name == 'Smith'
    api.people.return_value.updateContact.assert_called_once_with(resourceName='people/123', updatePersonFields='names',
                                                                  body={'resourceName': 'people/123', 'names': [
                                                                      {'givenName': 'Alicia', 'familyName': 'Smith'}]})


@pytest.mark.asyncio
async def test_google_delete_contact(google):
    provider, api = google
    await provider.delete_contact('people/123')
    api.people.return_value.deleteContact.assert_called_once_with(resourceName='people/123')
    api.people.return_value.deleteContact.return_value.execute.assert_called_once()


@pytest.mark.asyncio
async def test_google_create_error(google):
    provider, api = google

    api.people.return_value.createContact.return_value.execute.side_effect = (
        RuntimeError("Google API error")
    )

    with pytest.raises(RuntimeError, match="Google API error"):
        await provider.create_contact(given_name="Alice")
