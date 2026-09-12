from pydantic import BaseModel, Field


class Contact(BaseModel):
    id: str = Field(
        description="Unique contact ID."
    )

    given_name: str | None = Field(
        default=None,
        description="Contact's given name."
    )

    family_name: str | None = Field(
        default=None,
        description="Contact's family name."
    )

    emails: list[str] = Field(
        default_factory=list,
        description="Email addresses saved for this contact."
    )

    phone_numbers: list[str] = Field(
        default_factory=list,
        description="Phone numbers saved for this contact."
    )
