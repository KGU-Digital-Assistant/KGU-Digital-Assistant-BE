import datetime


from pydantic import BaseModel
from typing import Optional

class MealHour_schema(BaseModel):
    id: int
    user_id: int
    name: str
    picture: str
    text: str
    date: datetime.datetime ##등록시점(분단위)
    heart: bool
    time: str ## 등록시간대 ex) 2024-06-01아침, 2024-06-01점심
    carb: float
    protein: float
    fat: float
    calorie: float
    unit: str
    size: float
    track_goal: Optional[bool]= None
    daymeal_id: int

class MealHour_gram_update_schema(MealHour_schema):
    id: int
    user_id: int
    time: str
    carb: float
    protein: float
    fat: float
    calorie: float

class MealHour_daymeal_get_schema(BaseModel):
    time: str ## 등록시간대
    name: str

class MealHour_daymeal_time_get_schema(BaseModel):
    time: str ## 등록시간대

class MealHour_daymeal_get_picture_schema(BaseModel):
    name: str ## 등록시간대
    caloire: float
    picture: str

class MealHour_track_get_schema(BaseModel):
    track_goal: bool