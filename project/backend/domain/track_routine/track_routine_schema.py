from datetime import datetime
from typing import Optional
from pydantic import BaseModel

##전체변경
class TrackRoutineCreate(BaseModel):
    title: str
    date: Optional[str]
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


class TrackRoutine_namecalorie_schema(BaseModel):
    title: str
    calorie: Optional[float] = None

class TrackRoutine_time_title_schema(BaseModel):
    time: Optional[str]=None
    title: Optional[str]=None

class TrackRoutine_time_title_schema(BaseModel):
    time: str
    title: str
    calorie: Optional[float] = None


class TrackRoutin_id_title(BaseModel):
    id: Optional[int]= None
    title: Optional[str] =None
    week: Optional[str] =None
    time: Optional[str] =None
    date: Optional[str] =None
    repeat: Optional[bool]=None
