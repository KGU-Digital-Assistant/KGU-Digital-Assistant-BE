from typing import List

from fastapi.openapi.models import Schema
from pydantic import BaseModel
from sqlalchemy import Interval


class TrackCreate(BaseModel):
    name: str
    water: float
    coffee: float
    alcohol: float
    duration: int
    track_yn: bool

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
    user_id: int
    name: str
    water: float
    coffee: float
    alcohol: float
    duration: int
    track_yn: bool

    class Config:
        orm_mode = True


class TrackList(BaseModel):
    total: int = 0
    tracks: list[TrackSchema] = []
