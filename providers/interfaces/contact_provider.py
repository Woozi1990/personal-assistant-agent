from typing import Protocol

from pydantic import EmailStr

from models.contact import Contact


class ContactProvider(Protocol):
    async def create_contact(
            self,
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[EmailStr] | None = None,
            phone_numbers: list[str] | None = None,
    ) -> Contact:
        ...

    async def update_contact(self, contact: Contact) -> Contact:
        ...

    async def search_contact(self, query: str) -> list[Contact]:
        ...

    async def delete_contact(self, contact_id: str) -> None:
        ...
