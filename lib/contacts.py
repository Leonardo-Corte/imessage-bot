"""macOS Contacts loader via pyobjc Contacts framework."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Contact:
    id: str
    given: str = ""
    family: str = ""
    org: str = ""
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        parts = [p for p in (self.given, self.family) if p]
        return " ".join(parts) or self.org


def load_contacts() -> list[Contact]:
    from Contacts import (
        CNContactStore,
        CNContactFetchRequest,
        CNContactGivenNameKey,
        CNContactFamilyNameKey,
        CNContactOrganizationNameKey,
        CNContactPhoneNumbersKey,
        CNContactEmailAddressesKey,
        CNContactIdentifierKey,
    )

    store = CNContactStore.alloc().init()
    keys = [
        CNContactIdentifierKey,
        CNContactGivenNameKey,
        CNContactFamilyNameKey,
        CNContactOrganizationNameKey,
        CNContactPhoneNumbersKey,
        CNContactEmailAddressesKey,
    ]
    req = CNContactFetchRequest.alloc().initWithKeysToFetch_(keys)

    out: list[Contact] = []

    def handler(cn_contact, stop):
        phones = [p.value().stringValue() for p in cn_contact.phoneNumbers()]
        emails = [str(e.value()) for e in cn_contact.emailAddresses()]
        out.append(
            Contact(
                id=str(cn_contact.identifier()),
                given=str(cn_contact.givenName() or ""),
                family=str(cn_contact.familyName() or ""),
                org=str(cn_contact.organizationName() or ""),
                phones=phones,
                emails=emails,
            )
        )

    enum_method = (
        getattr(store, "enumerateContactsWithFetchRequest_error_usingBlock_", None)
        or getattr(store, "enumerateContactsWithFetchRequest_error_handler_", None)
    )
    if enum_method is None:
        raise RuntimeError("CNContactStore enumeration method not found in this pyobjc version")
    ok, err = enum_method(req, None, handler)
    if not ok:
        raise RuntimeError(f"Contacts enumeration failed: {err}")
    return out
