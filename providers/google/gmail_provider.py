import asyncio
import base64
from email.message import EmailMessage
from email.utils import getaddresses, parsedate_to_datetime, parseaddr

from googleapiclient.discovery import build

from models.email import Email
from providers.google.google_auth_service import GoogleAuthService
from providers.interfaces.email_provider import EmailProvider


class GmailProvider(EmailProvider):
    def __init__(self, auth_service: GoogleAuthService):
        self._lock = asyncio.Lock()
        self.auth_service = auth_service

        credentials = self.auth_service.get_credentials()

        self.email_client = build("gmail", "v1", credentials=credentials)

    async def search_emails(self, query: str) -> list[Email]:
        async with self._lock:
            result = await asyncio.to_thread(lambda: self.email_client.users().messages().list(
                userId="me",
                q=query,
                maxResults=100,
            ).execute())

        messages = result.get("messages", [])
        emails = []

        for item in messages:
            async with self._lock:
                message = await asyncio.to_thread(lambda: self.email_client.users().messages().get(
                    userId="me",
                    id=item["id"],
                ).execute())

            email = self._parse_email(message)
            emails.append(email)

        return emails

    async def get_email(self, message_id: str) -> Email:
        async with self._lock:
            message = await asyncio.to_thread(lambda: self.email_client.users().messages().get(
                userId="me",
                id=message_id,
                format="full",
            ).execute())

        email = self._parse_email(message)
        email.body = self._parse_email_body(message["payload"])

        return email

    async def create_draft(self, recipients: list[str], subject: str, body: str) -> Email:
        invalid_recipients = [
            recipient
            for recipient in recipients
            if not self._is_valid_email(recipient)
        ]

        if invalid_recipients:
            raise ValueError(
                f"Invalid recipient email addresses: {invalid_recipients}"
            )

        email = Email(
            id="",
            recipients=recipients,
            subject=subject,
            body=body,
        )

        raw = self._build_raw_message(email)

        async with self._lock:
            result = await asyncio.to_thread(lambda: self.email_client.users().drafts().create(
                userId="me",
                body={"message": {"raw": raw}},
            ).execute())

        return Email(
            id=result["message"]["id"],
            draft_id=result["id"],
            thread_id=result["message"].get("threadId"),
            recipients=recipients,
            subject=subject,
            body=body,
        )

    async def get_draft(self, draft_id: str) -> Email:
        async with self._lock:
            draft = await asyncio.to_thread(lambda: self.email_client.users().drafts().get(
                userId="me",
                id=draft_id,
                format="full",
            ).execute())

        message = draft["message"]
        email = self._parse_email(message)
        email.draft_id = draft["id"]
        email.body = self._parse_email_body(message["payload"])

        return email

    async def update_draft(self, email: Email) -> Email:
        if not email.draft_id:
            raise ValueError("Draft id is required")

        raw = self._build_raw_message(email)

        async with self._lock:
            result = await asyncio.to_thread(lambda: self.email_client.users().drafts().update(
                userId="me",
                id=email.draft_id,
                body={"message": {"raw": raw}},
            ).execute())

        email.id = result["message"]["id"]
        email.thread_id = result["message"].get("threadId")

        return email

    async def send_email(self, draft_id: str) -> str:
        async with self._lock:
            result = await asyncio.to_thread(lambda: self.email_client.users().drafts().send(
                userId="me",
                body={
                    "id": draft_id,
                }
            ).execute())

        return result["id"]

    @staticmethod
    def _parse_email(message) -> Email:
        headers = {
            header["name"].lower(): header["value"]
            for header in message["payload"].get("headers", [])
        }

        sender_addresses = getaddresses([headers.get("from", "")])
        sender = sender_addresses[0][1] if sender_addresses else None

        recipient_addresses = getaddresses([headers.get("to", "")])
        recipients = [
            address
            for _, address in recipient_addresses
        ]

        date_value = headers.get("date")
        received_at = (
            parsedate_to_datetime(date_value)
            if date_value
            else None
        )

        return Email(
            id=message["id"],
            thread_id=message.get("threadId"),
            sender=sender,
            recipients=recipients,
            subject=headers.get("subject"),
            received_at=received_at,
            snippet=message.get("snippet"),
        )

    def _parse_email_body(self, payload: dict) -> str | None:
        plain_body = self._find_body_part(
            payload,
            "text/plain"
        )

        if plain_body:
            return plain_body

        html_body = self._find_body_part(
            payload,
            "text/html"
        )

        if html_body:
            return html_body

        return None

    def _find_body_part(
            self,
            payload: dict,
            target_mime_type: str
    ) -> str | None:

        if payload.get("mimeType") == target_mime_type:
            data = payload.get("body", {}).get("data")

            if data:
                return self._decode_body(data)

        for part in payload.get("parts", []):
            body = self._find_body_part(
                part,
                target_mime_type
            )

            if body:
                return body

        return None

    @staticmethod
    def _build_raw_message(email: Email) -> str:
        message = EmailMessage()

        message["To"] = ",".join(email.recipients or [])
        message["Subject"] = email.subject or ""
        message.set_content(email.body or "")

        return base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

    @staticmethod
    def _decode_body(data: str) -> str:
        decoded = base64.urlsafe_b64decode(data)
        return decoded.decode("utf-8", errors="replace")

    @staticmethod
    def _is_valid_email(value: str) -> bool:
        _, address = parseaddr(value)

        return bool(
            address
            and "@" in address
            and "." in address.split("@")[-1]
            and address == value
        )
