from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TrackRoutineCreate(BaseModel):
    title: str
    food: Optional[str]
    calorie: Optional[float]
    week: Optional[str]
    time: Optional[str]
    repeat: bool

################################################


class TrackRoutineSchema(BaseModel):
    id: int
    track_id: int
    title: str
    food: Optional[str] = None
    calorie: Optional[float] = None
    week: Optional[str] = None
    time: Optional[str] = None


class TrackRoutineCreateSchema(BaseModel):
    title: str
    calorie: float
    week: str
    time: str
    repeat: bool


class TrackRoutine_naemcalorie_schema(BaseModel):
    title: str
    calorie: Optional[float] = None


class TrackRoutin_id_title(BaseModel):
    id: Optional[int]= None
    title: Optional[str] =None
    week: Optional[str] =None
    time: Optional[str] =None
    date: Optional[str] =None
    repeat: Optional[bool]= None