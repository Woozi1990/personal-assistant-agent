from langchain_core.tools import BaseTool, tool
from pydantic import EmailStr, ValidationError

from models.contact import Contact
from providers.interfaces.contact_provider import ContactProvider
from tools.contact.schemas import (
    SearchContactToolInput,
    CreateContactToolInput,
    UpdateContactToolInput,
    DeleteContactToolInput,
    SearchContactToolOutput,
    CreateContactToolOutput,
    UpdateContactToolOutput,
    DeleteContactToolOutput
)


def handle_contact_validation_error(error: ValidationError) -> str:
    messages = []

    for item in error.errors():
        field = ".".join(str(part) for part in item["loc"])
        message = item["msg"]
        messages.append(f"{field}: {message}")

    return "Invalid contact information: " + "; ".join(messages)


def build_contact_tools(
        contact_provider: ContactProvider,
) -> list[BaseTool]:
    @tool(args_schema=CreateContactToolInput)
    async def create_contact(
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[str] | None = None,
            phone_numbers: list[str] | None = None,
    ) -> CreateContactToolOutput:
        """
        Create a new saved contact.

        Use this tool when the user wants to save a new person or
        organization in their contacts.

        The contact may include a name, email address, phone number,
        or other supported contact information.

        Output:
        - success: whether the creation completed successfully
        - contact: created contact
            - id
            - given_name
            - family_name
            - emails
            - phone_numbers
        """

        contact = await contact_provider.create_contact(given_name, family_name, emails, phone_numbers)

        return CreateContactToolOutput(
            success=True,
            contact=contact
        )

    create_contact.handle_validation_error = handle_contact_validation_error

    @tool(args_schema=UpdateContactToolInput)
    async def update_contact(
            contact_id: str,
            given_name: str | None = None,
            family_name: str | None = None,
            emails: list[str] | None = None,
            phone_numbers: list[str] | None = None,
    ) -> UpdateContactToolOutput:
        """
        Update an existing saved contact.

        Use this tool when the user wants to change information for
        an existing contact, such as their name, email address, or phone number.

        This tool requires the existing contact's contact_id.
        It does not create a new contact.

        Output:
        - success: whether the update completed successfully
        - contact: updated contact
            - id
            - given_name
            - family_name
            - emails
            - phone_numbers
        """
        contact = Contact(
            id=contact_id,
            given_name=given_name,
            family_name=family_name,
            emails=emails,
            phone_numbers=phone_numbers
        )

        updated_contact = await contact_provider.update_contact(contact)

        return UpdateContactToolOutput(
            success=True,
            contact=updated_contact
        )

    update_contact.handle_validation_error = handle_contact_validation_error

    @tool(args_schema=SearchContactToolInput)
    async def search_contact(query: str | None) -> SearchContactToolOutput:
        """
        Search the user's saved contacts.

        Use this tool when the user wants to find a saved contact,
        or when another task requires contact information.

        Output:
        - success: whether the search completed successfully
        - contacts: matching saved contacts
          - id: contact ID
          - given_name: given name
          - family_name: family name
          - emails: saved email addresses
          - phone_numbers: saved phone numbers
        """
        contacts = await contact_provider.search_contact(query)

        return SearchContactToolOutput(
            success=True,
            contacts=contacts
        )

    @tool(args_schema=DeleteContactToolInput)
    async def delete_contact(contact_id: str) -> DeleteContactToolOutput:
        """
        Delete an existing saved contact.

        Use this tool when the user wants to remove a person or
        organization from their saved contacts.

        This tool requires the existing contact's contact_id.

        Output:
        - success: whether the deletion completed successfully
        - id: contact ID of the deleted contact

        """
        await contact_provider.delete_contact(contact_id)

        return DeleteContactToolOutput(
            success=True,
            contact_id=contact_id
        )

    return [
        create_contact,
        update_contact,
        search_contact,
        delete_contact,
    ]
