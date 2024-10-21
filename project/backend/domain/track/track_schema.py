from typing import List, Optional
from datetime import date, datetime
from fastapi.openapi.models import Schema
from pydantic import BaseModel
from sqlalchemy import Interval
from domain.track_routine.track_routine_schema import TrackRoutineCreateSchema, TrackRoutin_id_title


class TrackCreate(BaseModel):
    name: str
    icon: Optional[str]
    water: float
    coffee: float
    alcohol: float
    duration: int
    cheating_cnt: int
    delete: bool
    alone: bool
    calorie: float
    start_date: date
    end_date: date

    class Config:
        orm_mode = True

    # user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    # name = Column(String, nullable=False)
    # water = Column(Float)
    # coffee = Column(Float)
    # alcohol = Column(Float)
    # duration = Column(Interval)  # Interval : 일, 시간, 분, 초 단위로 기간을 표현 가능, 정확한 시간의 간격(기간)
    # track_yn = Column(Boolean,


class TrackResponse(BaseModel):
    track_id: int


# 이거 원본이랑 column 이름까지 같아야함
class TrackSchema(BaseModel):
    id: int
    icon: Optional[str]
    user_id: int
    name: str
    origin_track_id: Optional[int]
    water: Optional[float] = None
    coffee: Optional[float] = None
    alcohol: Optional[float] = None
    duration: Optional[int] = None
    delete: bool
    cheating_count: Optional[int] = None
    daily_calorie: float

    class Config:
        orm_mode = True


class TrackList(BaseModel):
    total: int = 0
    tracks: list[TrackSchema] = []


class TrackSchemaHB(BaseModel):
    id: int
    icon: Optional[str]
    user_id: int
    name: str
    water: Optional[float] = None
    coffee: Optional[float] = None
    alcohol: Optional[float] = None
    duration: Optional[int] = None
    delete: bool
    cheating_count: Optional[int] = None


class TrackListGetSchema(BaseModel):
    track_id: int
    name: str
    icon: Optional[str] = None
    daily_calorie: Optional[float] = None
    create_time: datetime
    recevied_user_id: Optional[int] = None
    recevied_user_name: Optional[str] = None
    using: Optional[bool] = None


class TrackCreateSchema(BaseModel):
    name: str
    water: float
    coffee: float
    alcohol: float
    start_date: date
    finish_date: date
    routines: List[TrackRoutineCreateSchema] = []


class TrackGetInfo(BaseModel):
    track_name: str
    icon: str
    name: Optional[str]
    track_start_day: Optional[date] = None
    track_finish_day: Optional[date] = None
    group_start_day: Optional[date] = None
    group_finish_day: Optional[date] = None
    real_finish_day: Optional[date] = None
    duration: Optional[int] = None
    calorie: Optional[float] = None
    count: Optional[int] = None
    coffee: Optional[float] = None
    alcohol: Optional[float] = None
    water: Optional[float] = None
    cheating_count: Optional[int] = None


class TrackSearch(BaseModel):
    id: int
    track_name: str
    score: int


class TrackSearchResponse(BaseModel):
    total: int = 0
    tracks: List[TrackSearch] = []
