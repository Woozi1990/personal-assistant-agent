from langchain_core.tools import BaseTool, tool

from agent.session_state import SessionState, PendingAction
from providers.interfaces.email_provider import EmailProvider
from tools.email.schemas import SearchEmailsToolInput, GetEmailToolInput, CreateDraftToolInput, SendEmailToolInput, \
    UpdateDraftToolInput


def build_email_tools(
        email_provider: EmailProvider,
        session_state: SessionState,
) -> list[BaseTool]:
    @tool(args_schema=SearchEmailsToolInput)
    def search_emails(query: str):
        """
        Search the user's mailbox for matching emails.

        Use this tool to find emails by keyword, sender, recipient,
        subject, topic, date, or other Gmail search criteria.

        Returns matching email metadata and message IDs.
        """
        result = email_provider.search_emails(query)

        return {
            "success": True,
            "result": result,
        }

    @tool(args_schema=GetEmailToolInput)
    def get_email(message_id: str):
        """
        Retrieve the full content of a specific email by message ID.

        Use this tool when the full body of a particular email is needed.
        Returns the email metadata and full body content.
        """
        result = email_provider.get_email(message_id)
        return {
            "success": True,
            "result": result,
        }

    @tool(args_schema=CreateDraftToolInput)
    def create_draft(recipients: list[str], subject: str, body: str):
        """
        Create a new email draft.

        Use this tool when a new email needs to be composed,
        whether the user wants to save it as a draft or send it afterward.

        This tool creates the draft only and does not send the email.

        Returns a draft_id that can be used to send the draft.
        """

        result = email_provider.create_draft(recipients, subject, body)

        session_state.pending_action = PendingAction(
            action="send_email",
            data={
                "email": result,
            }
        )
        return {
            "success": True,
            "result": result,
            "requires_confirmation": True
        }

    @tool(args_schema=UpdateDraftToolInput)
    def update_draft(
            recipients: list[str] | None = None,
            subject: str | None = None,
            body: str | None = None,
    ):
        """
            Update a pending email draft.

            Use this tool when the user wants to modify the recipients,
            subject, or body of an existing unsent draft.

            Only fields explicitly requested by the user should be changed.
            This tool does not send the email.
            """
        pending_action = session_state.pending_action

        if pending_action is None:
            raise ValueError("There is no pending action")

        email = pending_action.data.get("email")

        if email is None:
            raise ValueError("The draft id does not match the pending action")
        if recipients is not None:
            email.recipients = recipients
        if subject is not None:
            email.subject = subject
        if body is not None:
            email.body = body

        result = email_provider.update_draft(email)

        session_state.pending_action = PendingAction(
            action="send_email",
            data={"email": result, }
        )

        return {
            "success": True,
            "result": result,
            "requires_confirmation": True
        }

    @tool(args_schema=SendEmailToolInput)
    def send_email(draft_id: str):
        """
        Send an existing email draft.

        This tool sends a previously created draft identified by draft_id.
        It does not compose a new email.

        Requires a valid draft_id.
        """
        pending_action = session_state.pending_action

        if pending_action is None:
            raise ValueError("There is no pending action.")

        email = pending_action.data.get("email")

        if email is None:
            raise ValueError("There is no pending email draft.")

        if email.draft_id != draft_id:
            raise ValueError(
                "The draft id does not match the pending email."
            )

        result = email_provider.send_email(draft_id)

        session_state.pending_action = None

        return {
            "success": True,
            "result": result,
        }

    return [
        search_emails,
        get_email,
        create_draft,
        update_draft,
        send_email,
    ]
