from typing import Protocol

from models.contact import Contact


class ContactProvider(Protocol):
    def create_contact(
            self,
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[str] | None = None,
            phone_numbers: list[str] | None = None,
    ) -> Contact:
        ...

    def update_contact(self, contact: Contact) -> Contact:
        ...

    def search_contact(self, query: str) -> list[Contact]:
        ...

    def delete_contact(self, contact_id: str) -> None:
        ...