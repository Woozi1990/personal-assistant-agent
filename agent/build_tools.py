from enum import Enum, unique

from providers.google.google_auth_service import GoogleAuthService
from providers.google.google_calendar_provider import GoogleCalendarProvider
from providers.google.google_contact_provider import GoogleContactProvider
from providers.google.gmail_provider import GmailProvider
from providers.microsoft.mcp_client import MicrosoftMCPClient
from providers.microsoft.microsoft_calendar_provider import MicrosoftCalendarProvider
from providers.microsoft.microsoft_contact_provider import MicrosoftContactProvider
from providers.microsoft.microsoft_email_provider import MicrosoftEmailProvider
from tools.calendar.calendar_tools import build_calendar_tools
from tools.contact.contact_tools import build_contact_tools
from tools.email.email_tools import build_email_tools


@unique
class Provider(Enum):
    MICROSOFT = "microsoft"
    GOOGLE = "google"


def build_tools():
    provider = Provider.MICROSOFT

    calendar_provider, contact_provider, email_provider = _get_provider(provider)

    return [
        *build_calendar_tools(calendar_provider),
        *build_contact_tools(contact_provider),
        *build_email_tools(email_provider)
    ]


def _get_provider(provider: Provider):
    if provider == Provider.GOOGLE:
        google_auth_service = GoogleAuthService(
            scopes=[
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/contacts",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.compose",
            ]
        )
        return (
            GoogleCalendarProvider(google_auth_service),
            GoogleContactProvider(google_auth_service),
            GmailProvider(google_auth_service)
        )

    elif provider == Provider.MICROSOFT:
        microsoft_mcp_client = MicrosoftMCPClient()
        return (
            MicrosoftCalendarProvider(microsoft_mcp_client),
            MicrosoftContactProvider(microsoft_mcp_client),
            MicrosoftEmailProvider(microsoft_mcp_client)
        )

    else:
        raise ValueError(f"Unknown provider: {provider}")
