from providers.google.gmail_provider import GmailProvider
from providers.google.google_auth_service import GoogleAuthService
from providers.google.google_calendar_provider import GoogleCalendarProvider
from providers.google.google_contact_provider import GoogleContactProvider
from providers.microsoft.mcp_client import MicrosoftMCPClient
from providers.microsoft.microsoft_calendar_provider import MicrosoftCalendarProvider
from tools.calendar.calendar_tools import build_calendar_tools
from tools.contact.contact_tools import build_contact_tools
from tools.email.email_tools import build_email_tools


def build_tools():
    google_auth_service = GoogleAuthService(
        scopes=[
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/contacts",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
        ]
    )
    microsoft_mcp_client = MicrosoftMCPClient()

    # calendar_provider = GoogleCalendarProvider(
    #     auth_service=google_auth_service
    # )

    # contact_provider = GoogleContactProvider(
    #     auth_service=google_auth_service
    # )

    email_provider = GmailProvider(
        auth_service=google_auth_service
    )

    calendar_provider = MicrosoftCalendarProvider(
        mcp_client=microsoft_mcp_client
    )



    return [
        *build_calendar_tools(calendar_provider),
        # *build_contact_tools(contact_provider),
        # *build_email_tools(email_provider)
    ]
