from dataclasses import dataclass
from datetime import datetime


@dataclass
class Email:
    id: str
    thread_id: str | None = None
    draft_id: str | None = None
    sender: str | None = None
    recipients: list[str] | None = None
    subject: str | None = None
    body: str | None = None
    received_at: datetime | None = None
    snippet: str | None = None