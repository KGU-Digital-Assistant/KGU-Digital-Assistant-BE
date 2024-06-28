from fastapi.openapi.models import Schema

from pydantic import BaseModel, EmailStr


class MentorCreate(BaseModel):
    # user_id: int
    company_id: int
    gym: str
    FA: bool

    class Config:
        from_attributes = True
        check_fields = False
        arbitrary_types_allowed = True


class MentorGym(BaseModel):
    gym: str


class MenteeSchema(BaseModel):
    username: str
    email: EmailStr
