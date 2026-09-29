from models.contact import Contact
from providers.interfaces.contact_provider import ContactProvider
from providers.microsoft.mcp_client import MicrosoftMCPClient


class MicrosoftContact(ContactProvider):
    def __init__(self, mcp_client: MicrosoftMCPClient) -> None:
        self.mcp_client = mcp_client

    async def create_contact(
            self,
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[str] | None = None,
            phone_numbers: list[str] | None = None,
    ) -> Contact:
        pass

    async def update_contact(self, contact: Contact) -> Contact:
        pass

    async def search_contact(self, query: str) -> list[Contact]:
        pass

    async def delete_contact(self, event_id: str) -> None:
        pass
