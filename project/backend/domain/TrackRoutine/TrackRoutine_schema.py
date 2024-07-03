from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TrackRoutine_schema(BaseModel):
    id: int
    track_id: int
    title: str
    food: Optional[str] = None
    calorie: Optional[float] = None
    week: Optional[str] = None
    time: Optional[str] = None

class TrackRoutine_create_schema(BaseModel):
    title: str
    food: str
    calorie: float
    week: str
    time: str
    repeat: bool
