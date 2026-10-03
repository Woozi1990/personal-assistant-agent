import json
from datetime import datetime

from models.email import Email
from providers.interfaces.email_provider import EmailProvider
from providers.microsoft.mcp_client import MicrosoftMCPClient


class MicrosoftEmailProvider(EmailProvider):
    def __init__(self, mcp_client: MicrosoftMCPClient):
        self.mcp_client = mcp_client

    async def search_emails(self, query: str) -> list[Email]:
        args = {
            "top": 5,
            "select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview",
        }

        if query:
            args["search"] = f'"{query}"'
        else:
            args["orderby"] = "receivedDateTime desc"

        result = await self.mcp_client.call_tool(
            "list-mail-messages",
            args
        )

        if result.isError:
            raise RuntimeError(f"Failed to list Microsoft emails: {result.content}")

        if not result.content:
            raise RuntimeError("Microsoft emails returned empty content")

        data = json.loads(result.content[0].text)

        return [
            self._parse_email_message(item)
            for item in data.get("value", [])
        ]

    async def get_email(self, message_id: str) -> Email:
        result = await self.mcp_client.call_tool(
            "get-mail-message",
            {
                "messageId": message_id,
                "select": "id,subject,from,toRecipients,receivedDateTime,body",
            }
        )

        if result.isError:
            raise RuntimeError(f"Failed to get Microsoft email. {result.content}")

        if not result.content:
            raise RuntimeError("Microsoft emails returned empty content")

        data = json.loads(result.content[0].text)
        return self._parse_email_message(data)

    async def create_draft(self, recipients: list[str], subject: str, body: str) -> Email:
        message_body = {
            "subject": subject,
            "body": {
                "content": body,
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient,
                    }
                    for recipient in recipients
                }
            ],
            "isDraft": True,
        }
        result = await self.mcp_client.call_tool(
            "create-draft-email",
            {
                "body": message_body,
            }
        )

        if result.isError:
            raise RuntimeError(f"Failed to create Microsoft email draft. {result.content}")

        if not result.content:
            raise RuntimeError("Microsoft emails returned empty content")

        data = json.loads(result.content[0].text)
        return self._parse_email_message(data)

    async def get_draft(self, draft_id: str) -> Email:
        result = await self.mcp_client.call_tool(
            "get-mail-message",
            {
                "messageId": draft_id,
                "select": "id,subject,toRecipients,lastModifiedDateTime,isDraft",
            }
        )

        if result.isError:
            raise RuntimeError(f"Failed to get Microsoft email draft. {result.content}")

        if not result.content:
            raise RuntimeError("Microsoft draft returned empty content")

        data = json.loads(result.content[0].text)
        return self._parse_email_message(data)

    async def update_draft(self, email: Email) -> Email:
        if not email.draft_id:
            raise ValueError("Draft id is required")

        message_body = {
            "subject": email.subject,
            "body": {
                "content": email.body,
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient,
                    }
                }
                for recipient in email.recipients
            ],
        }

        result = await self.mcp_client.call_tool(
            "update-mail-message",
            {
                "messageId": email.draft_id,
                "body": message_body,
            }
        )

        if result.isError:
            raise RuntimeError(f"Failed to update Microsoft draft. {result.content}")
        if not result.content:
            raise RuntimeError("Microsoft draft returned empty content")

        data = json.loads(result.content[0].text)

        return self._parse_email_message(data)

    async def send_email(self, draft_id: str) -> str:
        result = await self.mcp_client.call_tool(
            "send-draft-message",
            {
                "messageId": draft_id,
            }
        )

        if result.isError:
            raise RuntimeError(f"Failed to send Microsoft email. {result.content}")

        return draft_id

    @staticmethod
    def _parse_email_message(data: dict) -> Email:
        sender = data.get("from", {}).get("emailAddress", {}).get("address")

        recipients = [
            recipient["emailAddress"]["address"]
            for recipient in data.get("toRecipients", [])
            if recipient.get("emailAddress", {}).get("address")
        ]

        received_at = (
            datetime.fromisoformat(
                data["receivedDateTime"].replace("Z", "+00:00")
            )
            if data.get("receivedDateTime")
            else None
        )

        body = (
            data.get("body", {}).get("content")
        )

        return Email(
            id=data["id"],
            draft_id=data["id"],
            sender=sender,
            recipients=recipients,
            subject=data.get("subject"),
            body=body,
            received_at=received_at,
            snippet=data.get("bodyPreview"),
        )
