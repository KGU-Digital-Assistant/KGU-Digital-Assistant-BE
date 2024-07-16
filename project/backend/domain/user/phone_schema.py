from pydantic import BaseModel


class PhoneNumberRequest(BaseModel):
    phone_number: str


class VerificationRequest(BaseModel):
    phone_number: str
    code: str
