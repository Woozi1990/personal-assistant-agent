from typing import Protocol

from models.email import Email


class EmailProvider(Protocol):
    def search_emails(self, query: str) -> list[Email]:
        ...

    def get_email(self, message_id: str) -> Email:
        ...

    def create_draft(self, recipients: list[str], subject: str, body: str) -> Email:
        ...

    def get_draft(self, draft_id: str) -> Email:
        ...

    def update_draft(self, email:Email) -> Email:
        ...

    def send_email(self, draft_id: str) -> str:
        ...
