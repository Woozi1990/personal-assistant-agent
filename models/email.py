from datetime import datetime

from pydantic import BaseModel, Field


class Email(BaseModel):
    id: str = Field(description="The id of the email.")
    draft_id: str | None = Field(default=None,description="The draft id of the email.")
    sender: str | None = Field(default=None,description="The sender of the email.")
    recipients: list[str] | None = Field(default=None,description="The recipients of the email.")
    subject: str | None = Field(default=None,description="The subject of the email.")
    body: str | None = Field(default=None,description="The body of the email.")
    received_at: datetime | None = Field(default=None,description="The received at of the email.")
    snippet: str | None = Field(default=None,description="The snippet of the email.")