import datetime

from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core.core_schema import FieldValidationInfo
from enum import Enum

class UserTypeEnum(str, Enum):
    USER = "USER"
    TRAINER = "TRAINER"
    MEMBER = "MEMBER"

class Rank(Enum):
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    DIAMOND = "DIAMOND"

    def __str__(self):
        return self.name


class UserCreate(BaseModel):
    name: str
    nickname: str
    cellphone: str
    password1: str
    password2: str
    gender: bool
    email: EmailStr
    birth: datetime.date


    class Config:
        from_attributes = True
        check_fields = False
        arbitrary_types_allowed = True

    @field_validator('name', 'nickname', 'password1', 'password2', 'email')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError(v + ' and password cannot be empty')
        return v

    @field_validator('password2')
    def passwords_match(cls, v, info: FieldValidationInfo):
        if 'password1' in info.data and v != info.data['password1']:
            raise ValueError('Passwords do not match')
        return v

class UserKakao(BaseModel):
    name: str
    email: str
    external_id: str
    auth_type: str

class UserUpdate(BaseModel):
    name: str
    nickname: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

class UserSchema(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True