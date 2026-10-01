import json
from typing import Any

from models.contact import Contact
from providers.interfaces.contact_provider import ContactProvider
from providers.microsoft.mcp_client import MicrosoftMCPClient


class MicrosoftContactProvider(ContactProvider):
    def __init__(self, mcp_client: MicrosoftMCPClient) -> None:
        self.mcp_client = mcp_client

    async def create_contact(
            self,
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[str] | None = None,
            phone_numbers: list[str] | None = None,
    ) -> Contact:
        body = {}
        if given_name is not None:
            body["givenName"] = given_name

        if family_name is not None:
            body["surname"] = family_name

        if emails:
            body["emailAddresses"] = [
                {
                    "address": email,
                    "name": " ".join(
                        value for value in [given_name, family_name] if value
                    )

                }
                for email in emails
            ]

        if phone_numbers:
            body["businessPhones"] = phone_numbers

        result = await self.mcp_client.call_tool(
            "create-outlook-contact",
            {
                "body": body
            }
        )

        if result.isError:
            raise RuntimeError(f"Failed to create Microsoft contact: {result.content}")

        if not result.content:
            raise RuntimeError("Microsoft contact MCP returned empty content")

        data = json.loads(result.content[0].text)

        return self._parse_contact(data)

    async def update_contact(self, contact: Contact) -> Contact:
        existed_contact = await self.mcp_client.call_tool(
            "get-outlook-contact",
            {
                "contactId": contact.id,
                "select":"id"
            }
        )
        if existed_contact.isError:
            raise RuntimeError(f"Microsoft contact not found: {existed_contact.content}")

        body={}

        if contact.given_name is not None:
            body["givenName"] = contact.given_name
        if contact.family_name is not None:
            body["surname"] = contact.family_name
        if contact.emails is not None:
            body["emailAddresses"] = [
                {
                    "address":email,
                }
                for email in contact.emails
            ]
        if contact.phone_numbers is not None:
            body["businessPhones"] = contact.phone_numbers

        result = await self.mcp_client.call_tool(
            "update-outlook-contact",
            {
                "contactId": contact.id,
                "body": body
            }
        )

        if result.isError:
            raise RuntimeError(f"Failed to update Microsoft contact: {result.content}")
        if not result.content:
            raise RuntimeError("Microsoft contact MCP returned empty content")

        data = json.loads(result.content[0].text)

        return self._parse_contact(data)

    async def search_contact(self, query: str) -> list[Contact]:
        args = {
            "select": "id,givenName,surname,emailAddresses,businessPhones,homePhones,mobilePhone"
        }

        print(f"Query: {query}")

        if query:
            args["search"] = f'"{query}"'
            args["top"] = 10
        else:
            args["fetchAllPages"] = True

        result = await self.mcp_client.call_tool(
            "list-outlook-contacts",
            args
        )

        if result.isError:
            raise RuntimeError(f"Failed to search Microsoft contacts:{result.content}")

        data = json.loads(result.content[0].text)

        return [
            self._parse_contact(contact)
            for contact in data.get("value", [])
        ]

    async def delete_contact(self, contact_id: str) -> None:
        result = await self.mcp_client.call_tool(
            "delete-outlook-contact",
            {
                "contactId": contact_id,
            }
        )

        if result.isError:
            raise RuntimeError(
                f"Failed to delete Microsoft contact: {result.content}"
            )

    @staticmethod
    def _parse_contact(contact: Contact) -> Contact:
        return Contact(
            id=contact["id"],
            given_name=contact.get("givenName"),
            family_name=contact.get("surname"),
            emails=[
                email["address"]
                for email in contact.get("emailAddresses", [])
                if email.get("address")
            ],
            phone_numbers=[
                *contact.get("businessPhones", []),
                *contact.get("homePhones", []),
                *(
                    [contact["mobilePhone"]]
                    if contact.get("mobilePhone") else []
                )
            ]
        )

