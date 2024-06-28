import datetime

from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core.core_schema import FieldValidationInfo
from enum import Enum

class UserTypeEnum(str, Enum):
    USER = "USER"
    TRAINER = "TRAINER"
    MEMBER = "MEMBER"

class UserCreate(BaseModel):
    name: str
    nickname: str
    password1: str
    password2: str
    address: str
    gender: str
    email: EmailStr
    birthday: datetime.date
    external_id: str    # 카카오 계정과 연결 여부 and 카카오 고유의 id를 저장함.
    auth_type: str


    class Config:
        from_attributes  = True
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

class UserKakao(BaseModel):
    name: str
    email: str
    address: str
    external_id: str
    auth_type: str

class UserUpdate(BaseModel):
    name: str
    nickname: str
    address: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
    name: str

class UserSchema(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True