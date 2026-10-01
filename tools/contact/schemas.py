from pydantic import BaseModel, Field

from models.contact import Contact


class CreateContactToolInput(BaseModel):
    given_name: str | None = Field(
        default=None,
        description="Given or first name of the contact, if provided."
    )
    family_name: str | None = Field(
        default=None,
        description="Family or last name of the contact, if provided."
    )
    emails: list[str] | None = Field(
        default=None,
        description=(
            "Email addresses explicitly provided for the contact. "
            "Do not guess or fabricate missing email addresses."
        )
    )
    phone_numbers: list[str] | None = Field(
        default=None,
        description=(
            "Phone numbers explicitly provided for the contact. "
            "Do not guess or fabricate missing phone numbers."
        )
    )


class UpdateContactToolInput(BaseModel):
    contact_id: str = Field(
        description=(
            "Unique ID of the existing contact to update. "
            "Use a contact ID returned by a contact search result; "
            "do not invent or guess this value."
        )
    )
    given_name: str | None = Field(
        default=None,
        description="Updated given or first name, if it should be changed."
    )
    family_name: str | None = Field(
        default=None,
        description="Updated family or last name, if it should be changed."
    )
    emails: list[str] | None = Field(
        default=None,
        description=(
            "Updated email addresses for the contact, if they should be changed. "
            "Do not guess or fabricate email addresses."
        )
    )
    phone_numbers: list[str] | None = Field(
        default=None,
        description=(
            "Updated phone numbers for the contact, if they should be changed. "
            "Do not guess or fabricate phone numbers."
        )
    )


class SearchContactToolInput(BaseModel):
    query: str|None = Field(
        default=None,
        description=(
            "Name, email address, phone number, organization, "
            "or other known contact information used to search saved contacts."
            "Omit this parameter when the user wants to list all contacts."
        )
    )


class DeleteContactToolInput(BaseModel):
    contact_id: str = Field(
        description=(
            "Unique ID of the existing contact to delete. "
            "Use a contact ID returned by a contact search result; "
            "do not invent or guess this value."
        )
    )


class CreateContactToolOutput(BaseModel):
    success: bool = Field(
        description="Whether the contact create completed successfully."
    )
    contact: Contact = Field(
        description="The newly created contact, including its generated contact ID and saved contact information."
    )


class UpdateContactToolOutput(BaseModel):
    success: bool = Field(
        description="Whether the contact update completed successfully."
    )
    contact: Contact = Field(
        description="The updated contact, including its contact ID and current contact information."
    )


class SearchContactToolOutput(BaseModel):
    success: bool = Field(
        description="Whether the contact search completed successfully.")
    contacts: list[Contact] = Field(
        description="List of saved contacts matching the search query."
    )


class DeleteContactToolOutput(BaseModel):
    success: bool = Field(
        description="Whether the contact delete completed successfully."
    )
    contact_id: str = Field(
        description="Deleted contact ID"
    )
