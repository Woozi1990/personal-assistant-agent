from typing import Any

from googleapiclient.discovery import build

from models.contact import Contact
from providers.google.google_auth_service import GoogleAuthService
from providers.interfaces.contact_provider import ContactProvider


class GoogleContactProvider(ContactProvider):
    def __init__(self, auth_service: GoogleAuthService):
        self.auth_service = auth_service

        credentials = self.auth_service.get_credentials()

        self.people_client = build(
            serviceName="people",
            version="v1",
            credentials=credentials,
        )

    def create_contact(
            self,
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[str] | None = None,
            phone_numbers: list[str] | None = None,
    ) -> Contact:
        person = {}
        if given_name or family_name:
            person["names"] = [{
                "givenName": given_name,
                "familyName": family_name,
            }]

        if emails:
            person["emailAddresses"] = [
                {"value": email}
                for email in emails
            ]

        if phone_numbers:
            person["phoneNumbers"] = [
                {"value": phone_number}
                for phone_number in phone_numbers
            ]

        result = self.people_client.people().createContact(body=person).execute()

        return self._parse_contact(result)

    def update_contact(self, contact: Contact):
        person = (
            self.people_client
            .people()
            .get(
                resourceName=contact.id,
                personFields="names,emailAddresses,phoneNumbers"
            )
            .execute()
        )

        update_fields = []

        if contact.given_name is not None or contact.family_name is not None:
            current_name = person.get("names", [{}])[0]

            person["names"] = [{
                "givenName": (
                    contact.given_name
                    if contact.given_name is not None
                    else current_name.get("givenName")
                ),
                "familyName": (
                    contact.family_name
                    if contact.family_name is not None
                    else current_name.get("familyName")
                ),
            }]
            update_fields.append("names")

        if contact.emails is not None:
            person["emailAddresses"] = [
                {
                    "value": email
                } for email in contact.emails]
            update_fields.append("emailAddresses")

        if contact.phone_numbers is not None:
            person["phoneNumbers"] = [
                {"value": phone_number}
                for phone_number in contact.phone_numbers
            ]
            update_fields.append("phoneNumbers")

        result = (
            self.people_client
            .people()
            .updateContact(
                resourceName=contact.id,
                updatePersonFields=",".join(update_fields),
                body=person,
            ).execute()
        )

        return self._parse_contact(result)

    def search_contact(
            self,
            query: str,
    ) -> list[Contact]:

        # Before searching, clients should send a warmup request
        # with an empty query to update the cache
        self.people_client.people().searchContacts(
            query="",
            readMask="names,emailAddresses,phoneNumbers",
            pageSize=1,
        ).execute()

        result = self.people_client.people().searchContacts(
            query=query,
            readMask="names,emailAddresses,phoneNumbers",
            pageSize=10,
        ).execute()

        contacts = []

        for result_item in result.get("results", []):
            person = result_item["person"]

            contacts.append(self._parse_contact(person))
        return contacts

    def delete_contact(self, contact_id: str) -> None:
        self.people_client.people().deleteContact(resourceName=contact_id).execute()

    @staticmethod
    def _parse_contact(person: dict[str, Any]) -> Contact:
        name = person.get("names", [{}])[0]

        return Contact(
            id=person["resourceName"],
            given_name=name.get("givenName"),
            family_name=name.get("familyName"),
            emails=[
                       email["value"]
                       for email in person.get("emailAddresses", [])
                   ] or None,
            phone_numbers=[
                              phone["value"]
                              for phone in person.get("phoneNumbers", [])
                          ] or None,
        )
