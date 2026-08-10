from langchain_core.tools import BaseTool, tool

from models.contact import Contact
from providers.interfaces.contact_provider import ContactProvider
from tools.contact.schemas import SearchContactToolInput, CreateContactToolInput, UpdateContactToolInput, \
    DeleteContactToolInput


def build_contact_tools(
        contact_provider: ContactProvider,
) -> list[BaseTool]:
    @tool(args_schema=CreateContactToolInput)
    def create_contact(
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[str] | None = None,
            phone_numbers: list[str] | None = None,
    ):
        """
        Create a new saved contact.

        Use this tool when the user wants to save a new person or
        organization in their contacts.

        The contact may include a name, email address, phone number,
        or other supported contact information.
        """

        contact = contact_provider.create_contact(given_name,family_name, emails, phone_numbers)

        return {
            "success": True,
            "contact": contact,
        }

    @tool(args_schema=UpdateContactToolInput)
    def update_contact(
            contact_id: str,
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[str] | None = None,
            phone_numbers: list[str] | None = None,
    ):
        """
        Update an existing saved contact.

        Use this tool when the user wants to change information for
        an existing contact, such as their name, email address, or phone number.

        This tool requires the existing contact's contact_id.
        It does not create a new contact.
        """
        contact = Contact(
            id=contact_id,
            given_name=given_name,
            family_name=family_name,
            emails=emails,
            phone_numbers=phone_numbers
        )

        updated_contact = contact_provider.update_contact(contact)

        return {
            "success": True,
            "contact": updated_contact,
        }

    @tool(
        "search_saved_contacts",
        args_schema=SearchContactToolInput)
    def search_contact(query: str):
        """
        Search the user's saved contacts.

        Use this tool when the user wants to find a saved contact,
        or when the current task requires contact information that
        has not been explicitly provided, such as an email address
        or phone number.

        Returns matching saved contacts and their contact details.
        """

        contacts = contact_provider.search_contact(query)

        return {
            "success": True,
            "contacts": contacts,
        }

    @tool(args_schema=DeleteContactToolInput)
    def delete_contact(contact_id: str):
        """
        Delete an existing saved contact.

        Use this tool when the user wants to remove a person or
        organization from their saved contacts.

        This tool requires the existing contact's contact_id.
        """
        contact_provider.delete_contact(contact_id)

        return {
            "success": True,
            "contact_id": contact_id,
        }

    return [
        create_contact,
        update_contact,
        search_contact,
        delete_contact,
    ]
