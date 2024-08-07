import datetime

from models import User, Mentor
from typing import List, Optional

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
    name: str # 실명
    username: str # 로그인 아이디
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

    # @field_validator('nickname')
    # def word_count(cls, v):
    #     if len(v) > 7:
    #         raise ValueError(v + ' and nickname cannot be longer than 7 characters')
    #
    # @field_validator('password1')
    # def password_validate(cls, v):
    #     if (len(v) > 10):
    #         raise ValueError(v + ' and password1 cannot be longer than 10 characters')
    #     # 영문 숫자 특수문자 여부 추가 예정


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
    name: Optional[str]
    nickname: Optional[str]
    email: Optional[EmailStr]


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    user_id: int
    nickname: str


class UserSchema(BaseModel):
    id: int
    email: str
    username: str
    name: str
    nickname: str
    cellphone: str
    gender: bool
    birth: datetime.date

    class Config:
        orm_mode = True


class UserList(BaseModel):
    users: List[UserSchema]

    class Config:
        orm_mode = True


class TokenRequest(BaseModel):
    access_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    profile_picture: str
    name: str
    nickname: str
    mentor_name: Optional[str] = None

#########################################

class User(BaseModel):
    id: int
    name: str
    cellphone: str
    gender: Optional[bool] = None
    birth: Optional[datetime.date] = None
    create_date: datetime.datetime
    nickname: str
    rank: str
    profile_picture: Optional[str] = None
    mentor_id: Optional[int] = None
    email: str
    password: str
    external_id: Optional[str] = None
    auth_type: Optional[str] = None
    fcm_token: Optional[str] =None
    cheating_count: Optional[int] = None

class UserRank(BaseModel):
    rank: str

class Usernickname(BaseModel):
    nickname: str

class Username(BaseModel):
    name: str

