from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import Command

from agent.pending_action import PendingAction
from providers.interfaces.email_provider import EmailProvider
from tools.email.schemas import SearchEmailsToolInput, GetEmailToolInput, CreateDraftToolInput, SendEmailToolInput, \
    UpdateDraftToolInput


def build_email_tools(
        email_provider: EmailProvider,
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
    def create_draft(
            recipients: list[str],
            subject: str,
            body: str,
            runtime: ToolRuntime
    ) -> Command:
        """
        Create a new email draft.

        Use this tool when a new email needs to be composed,
        whether the user wants to save it as a draft or send it afterward.

        This tool creates the draft only and does not send the email.

        Returns a draft_id that can be used to send the draft.
        """

        result = email_provider.create_draft(recipients, subject, body)

        pending_action = PendingAction(
            action="send_email",
            data={"email": result, }
        )

        return Command(
            update={
                "pending_action": pending_action,
                "requires_confirmation":True,
                "messages": [
                    ToolMessage(
                        content=str({
                            "success": True,
                            "result": result,
                            "requires_confirmation": True,
                        }),
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    @tool(args_schema=UpdateDraftToolInput)
    def update_draft(
            recipients: list[str] | None = None,
            subject: str | None = None,
            body: str | None = None,
            runtime: ToolRuntime = None
    ) -> Command:
        """
            Update a pending email draft.

            Use this tool when the user wants to modify the recipients,
            subject, or body of an existing unsent draft.

            Only fields explicitly requested by the user should be changed.
            This tool does not send the email.
            """
        pending_action = runtime.state.get("pending_action")

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

        return Command(
            update={
                "pending_action": PendingAction(
                    action="send_email",
                    data={"email": result, }
                ),
                "requires_confirmation":True,
                "messages": [
                    ToolMessage(
                        content=str({
                            "success": True,
                            "result": result,
                            "requires_confirmation": True,
                        }),
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    @tool(args_schema=SendEmailToolInput)
    def send_email(
            draft_id: str,
            runtime: ToolRuntime
    ) -> Command:
        """
        Send an existing email draft.

        This tool sends a previously created draft identified by draft_id.
        It does not compose a new email.

        Requires a valid draft_id.
        """
        pending_action = runtime.state.get("pending_action")

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

        return Command(
            update={
                "pending_action": None,
                "requires_confirmation":False,
                "messages": [
                    ToolMessage(
                        content=str({
                            "success": True,
                            "result": result,
                        }),
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    return [
        search_emails,
        get_email,
        create_draft,
        update_draft,
        send_email,
    ]
