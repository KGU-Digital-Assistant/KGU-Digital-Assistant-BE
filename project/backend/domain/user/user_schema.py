import datetime

from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core.core_schema import FieldValidationInfo


class UserCreate(BaseModel):
    id: int
    name: str
    nickname: str
    password1: str
    password2: str
    address: str
    gender: str
    email: EmailStr
    birthday: datetime.date

    class Config:
        orm_mode = True
        check_fields = False
        arbitrary_types_allowed = True

    @field_validator('name', 'nickname', 'password1', 'password2', 'email', 'gender')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Username and password cannot be empty')
        return v

    @field_validator('password2')
    def passwords_match(cls, v, info: FieldValidationInfo):
        if 'password1' in info.data and v != info.data['password1']:
            raise ValueError('Passwords do not match')
        return v


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str