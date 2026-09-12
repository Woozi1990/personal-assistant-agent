from typing import Protocol

from models.email import Email


class EmailProvider(Protocol):
    async def search_emails(self, query: str) -> list[Email]:
        ...

    async def get_email(self, message_id: str) -> Email:
        ...

    async def create_draft(self, recipients: list[str], subject: str, body: str) -> Email:
        ...

    async def get_draft(self, draft_id: str) -> Email:
        ...

    async def update_draft(self, email:Email) -> Email:
        ...

    async def send_email(self, draft_id: str) -> str:
        ...
