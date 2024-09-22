import datetime
from enum import Enum
from typing import Optional, List

from fastapi.openapi.models import Schema
from pydantic import BaseModel, field_validator


class GroupStatus(Enum):
    READY = "READY"
    STARTED = "STARTED"
    TERMINATED = "TERMINATED"


class GroupCreate(BaseModel):
    name: str
    start_day: datetime.date

    # 시작일이 이미 지난 날이면 안됨
    @field_validator('start_day')
    def validate_start_day(cls, value):
        if value <= datetime.date.today():
            raise ValueError('start_day must be today or a future date')
        return value


class GroupSchema(BaseModel):
    id: int
    name: str
    track_id: int
    user_id: int
    start_date: datetime.date
    finish_date: datetime.date

    class Config:
        orm_mode = True


class InviteStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

#########################################

class Group_schema(BaseModel):
    id: int
    track_id: int
    user_id: int
    name: str
    start_day: datetime.date
    finish_day: datetime.date

class Group_name_dday_schema(BaseModel):
    name: Optional[str]
    dday: Optional[int]
    track_id: Optional[int]

class Group_get_track_name_schema(BaseModel):
    trackold: Optional[List[str]] = None
    tracknew: Optional[str] = None


class GroupDate(BaseModel):
    start_date: datetime.date
    end_date: datetime.date


class Respond(BaseModel):
    respond: str

    @field_validator('respond')
    def validate_respond(cls, value):
        if value not in ['accepted', 'rejected']:
            raise ValueError('respond must be either accepted or rejected')