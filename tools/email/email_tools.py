from langchain_core.tools import BaseTool, tool

from models.email import Email
from providers.interfaces.email_provider import EmailProvider
from tools.email.schemas import SearchEmailsToolInput, GetEmailToolInput, CreateDraftToolInput, SendEmailToolInput, \
    CreateDraftToolOutput, SearchEmailsToolOutput, GetEmailToolOutput, SendEmailToolOutput, UpdateDraftToolInput, \
    UpdateDraftToolOutput


def build_email_tools(
        email_provider: EmailProvider,
) -> list[BaseTool]:
    @tool(args_schema=SearchEmailsToolInput)
    async def search_emails(query: str) -> SearchEmailsToolOutput:
        """
        Search the user's mailbox for matching emails.

        Use this tool to find emails by keyword, sender, recipient,
        subject, topic, date, or other email search criteria.

        Returns matching email metadata and message IDs.


        Output:
        - success: whether the search completed successfully
        - emails: match emails
            - id
            - draft_id
            - sender
            - recipients
            - subject
            - body
            - received_at
            - snippet
        """
        emails = await email_provider.search_emails(query)

        return SearchEmailsToolOutput(
            success=True,
            emails=emails,
        )

    @tool(args_schema=GetEmailToolInput)
    async def get_email_message(message_id: str) -> GetEmailToolOutput:
        """
        Retrieve the full content of a specific mailbox email message by message ID.

        Use this tool only to read an existing email message from the mailbox.
        Do not use this tool to retrieve a person's email address.

        Output:
        - success: whether the get email completed successfully
        - email: matching Email Message
            - id
            - draft_id
            - sender
            - recipients
            - subject
            - body
            - received_at
            - snippet
        """
        email = await email_provider.get_email(message_id)
        return GetEmailToolOutput(
            success=True,
            email=email,
        )

    @tool(args_schema=CreateDraftToolInput)
    async def create_draft(
            recipients: list[str],
            subject: str,
            body: str,
    ) -> CreateDraftToolOutput:
        """
        Create an email draft.

        The recipients argument must contain real email addresses.

        If the user provides only a person's name and no email
        address is present in the conversation, the address must be
        obtained from another available tool.

        Never invent or guess an email address.

        Output:
        - success: whether the create draft completed successfully
        - draft: created Email draft
            - id
            - draft_id
            - sender
            - recipients
            - subject
            - body
            - received_at
            - snippet
        """

        draft = await email_provider.create_draft(recipients, subject, body)

        return CreateDraftToolOutput(
            success=True,
            draft=draft,
        )

    @tool(args_schema=UpdateDraftToolInput)
    async def update_draft(
            draft_id: str,
            recipients: list[str] | None = None,
            subject: str | None = None,
            body: str | None = None,

    ) -> UpdateDraftToolOutput:
        """
        Update an existing email draft.

        Use this tool to modify a draft that already exists.

        Only provide fields that should be changed.
        Fields left as null retain their existing values.

        A valid draft_id must come from an existing tool result.
        Never invent or guess a draft_id.

        Output:
        - success: whether the draft update completed successfully
        - result: the complete updated Email draft
        """

        email = await email_provider.get_draft(draft_id)

        if recipients is not None:
            email.recipients = recipients
        if subject is not None:
            email.subject = subject
        if body is not None:
            email.body = body

        updated_draft = await email_provider.update_draft(email)
        return UpdateDraftToolOutput(
            success=True,
            draft=updated_draft,
        )

    @tool(args_schema=SendEmailToolInput)
    async def send_email(
            draft_id: str,
    ) -> SendEmailToolOutput:
        """
        Send an existing email draft.

        This tool sends a previously created draft identified by draft_id.
        It does not compose a new email.

        Requires a valid draft_id.

        Output:
        - success: whether the Email sent completed successfully
        - message_id: sent Email Message

        """

        message_id = await email_provider.send_email(draft_id)

        return SendEmailToolOutput(
            success=True,
            message_id=message_id,
        )

    return [
        search_emails,
        get_email_message,
        create_draft,
        update_draft,
        send_email,
    ]
