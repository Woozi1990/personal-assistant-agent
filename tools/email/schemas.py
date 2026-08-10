from pydantic import BaseModel, Field


class SearchEmailsToolInput(BaseModel):
    query: str = Field(
        description=(
            "Search query used to find matching emails. "
            "The query may contain keywords or filters based on "
            "sender, recipient, subject, date, or other email content."
        )
    )


class GetEmailToolInput(BaseModel):
    message_id: str = Field(
        description=(
            "The unique Gmail message ID of the email to retrieve. "
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
            "The unique Gmail draft ID of the draft to send. "
            "Use an existing draft ID or one returned by create_draft. "
            "Do not use a message ID and do not invent this value."
        )
    )
