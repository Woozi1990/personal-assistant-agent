from pydantic import BaseModel, Field

from models.email import Email


class SearchEmailsToolInput(BaseModel):
    query: str|None = Field(
        default=None,
        description=(
            "Search query used to find matching emails. "
            "The query may contain keywords or filters based on "
            "sender, recipient, subject, date, or other email content."
        )
    )


class GetEmailToolInput(BaseModel):
    message_id: str = Field(
        description=(
            "The unique message ID of the email to retrieve. "
            "Use an ID returned by an email search result; do not invent or guess this value."
        )
    )


class CreateDraftToolInput(BaseModel):
    recipients: list[str] = Field(
        description=(
            "Email addresses of the recipients. "
            "Use only email addresses explicitly provided by the user or returned by a tool result. "
            "Do not infer, guess, or fabricate email addresses from names."
        )
    )
    subject: str = Field(
        description="Subject line of the email to be drafted."
    )
    body: str = Field(
        description="Full text content of the email to be drafted."
    )


class UpdateDraftToolInput(BaseModel):
    draft_id: str = Field(
        description=(
            "The draft ID of the draft to update. "
            "Use only a draft ID returned by an existing tool result. "
            "Do not invent or guess this value."
        )
    )
    recipients: list[str] | None = Field(
        default=None,
        description=(
            "New recipient email addresses, only if the user wants "
            "to change the recipients."
        )
    )
    subject: str | None = Field(
        default=None,
        description=(
            "New subject, only if the user wants to change the subject."
        )
    )
    body: str | None = Field(
        default=None,
        description=(
            "New complete email body, only if the user wants "
            "to change the body."
        )
    )


class SendEmailToolInput(BaseModel):
    draft_id: str = Field(
        description=(
            "The unique draft ID of the draft to send. "
            "Use an existing draft ID or one returned by create_draft. "
            "Do not use a message ID and do not invent this value."
        )
    )


class CreateDraftToolOutput(BaseModel):
    success: bool = Field(description="Whether the email draft created completed successfully.")
    draft: Email = Field(description="The email draft created.")


class UpdateDraftToolOutput(BaseModel):
    success: bool = Field(description="Whether the email draft updated completed successfully.")
    draft: Email = Field(description="The email draft updated.")


class SearchEmailsToolOutput(BaseModel):
    success: bool = Field(description="Whether the email search completed successfully.")
    emails: list[Email] = Field(description="List of email matching the search query.")


class GetEmailToolOutput(BaseModel):
    success: bool = Field(description="Whether the email get completed successfully.")
    email: Email = Field(description="The email matching search ID.")


class SendEmailToolOutput(BaseModel):
    success: bool = Field(description="Whether the email send completed successfully.")
    message_id: str = Field(description="The email message ID of the sent email.")
