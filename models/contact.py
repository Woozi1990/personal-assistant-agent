from dataclasses import dataclass


@dataclass
class Contact:
    id: str
    given_name: str | None = None
    family_name: str | None = None
    emails: list[str] | None = None
    phone_numbers: list[str] | None = None
