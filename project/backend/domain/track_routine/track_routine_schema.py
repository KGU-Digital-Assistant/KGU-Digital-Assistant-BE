from datetime import datetime, time
from typing import Optional, List
from pydantic import BaseModel
from models import MealTime
from sqlalchemy import Time


# class TrackRoutine(BaseModel):
#     title: str
#     date: int
#     calories: int
#     week: int
#     weekdays: List[int]
#     times: str
#     is_repeat: bool

# ----------------------------------------

class TrackRoutineCreate(BaseModel):
    title: str
    date: str
    calorie: Optional[float]
    weekday: Optional[str]
    time: Optional[str]
    repeat: bool


class TrackRoutineSchema(BaseModel):
    id: int
    track_id: int
    title: str  # 식단 이름
    calorie: Optional[float] = None
    week: Optional[str] = None
    time: Optional[str] = None


class TrackRoutineCreateSchema(BaseModel):
    title: str
    calorie: float
    week: str
    time: str
    repeat: bool


class TrackRoutine_namecalorie_schema(BaseModel):
    title: str
    calorie: Optional[float] = None


class TrackRoutine_time_title_schema(BaseModel):
    time: Optional[str] = None
    title: Optional[str] = None


class TrackRoutine_time_title_schema(BaseModel):
    time: str
    title: str
    calorie: Optional[float] = None


class TrackRoutin_id_title(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    week: Optional[str] = None
    time: Optional[str] = None
    date: Optional[str] = None
    repeat: Optional[bool] = None


class TrackRoutineResponse(BaseModel):
    routine_id: int
    routine_date_id: int
    calorie: float
    weekday: int
    week: int
    time: MealTime
    title: str
    clock: time


class TrackRoutineDateSchema(BaseModel):
    id: int
    time: int
    weekday: int
    routine_id: int
    date: int
    clock: time

    class Config:
        orm_mode = True
        from_attributes = True


class TrackRoutineCreateNext(BaseModel):
    title: str
    clock: time
    weekday: str
    time: str
    calorie: float
    repeat: bool
    alarm: bool
