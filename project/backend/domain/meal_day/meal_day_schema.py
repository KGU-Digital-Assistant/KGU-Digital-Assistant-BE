from datetime import datetime,date
from typing import Optional, List
from domain.meal_hour import meal_hour_schema
from domain.track_routine import track_routine_schema
from pydantic import BaseModel

class MealDay_schema(BaseModel):
    id: int
    user_id: int
    water: float
    coffee: float
    alcohol: float
    carb: float
    protein: float
    fat: float
    cheating: int
    goalcalorie: float
    nowcalorie: float
    gb_carb: Optional[str] = None
    gb_protein: Optional[str] = None
    gb_fat: Optional[str] = None
    date: date
    track_id: Optional[int]

class MealDay_cheating_get_schema(BaseModel):
    cheating: int

class MealDay_cheating_count_get_schema(BaseModel):
    cheating_count: int
    user_id2: int

class MealDay_wca_get_schema(BaseModel):
    water:float
    coffee: float
    alcohol: float

class Mealday_wca_update_schema(BaseModel): ##물, 커피, 알코올
    water: float
    coffee: float
    alcohol: float

class MealDay_calorie_get_schema(BaseModel): ## 목표, 현재 칼로리
    goalcalorie: float
    nowcalorie: float


class MealDay_track_hour_schema(BaseModel):
    name: Optional[str] = None
    calorie: Optional[float] = None
    date: Optional[datetime] =None
    heart: Optional[float] = None
    picture: Optional[str] = None
    track_goal: Optional[bool] =None

class MealDay_track_today_schema(BaseModel):
    mealday: List[MealDay_track_hour_schema]

class MealDay_track_dday_goal_real_schema(BaseModel):
    dday: Optional[int]=None
    goal: Optional[List[track_routine_schema.TrackRoutine_time_title_schema]]=None
    real: Optional[List[meal_hour_schema.MealHour_daymeal_get_schema]]=None

class MealDay_today_calorie_schema(BaseModel):
    todaycalorie: Optional[float]=None
    goalcalorie: Optional[float]=None
    nowcalorie: Optional[float]=None
    burncalorie: Optional[float]=None
    weight : Optional[float]=None

class MealDay_today_mealhour_schema(BaseModel):
    date: Optional[str] =None
    picture: Optional[str] = None

class MealDay_today_mealhour_list_schema(BaseModel):
    mealday: List[MealDay_today_mealhour_schema]

class MealDay_record_count_schecma(BaseModel):
    record_count: int
    days: int

class MealDay_trackroutine_schema(BaseModel):
    time: Optional[str] =None
    title: Optional[str] = None
    track_yn: Optional[bool] = None

class MealDay_trackroutine_list_schema(BaseModel):
    mealday: List[MealDay_trackroutine_schema]

class MealDay_today_nutrient_schema(BaseModel):
    carb: Optional[float]=None
    protein: Optional[float]=None
    fat: Optional[float]=None
    gb_carb: Optional[float]=None
    gb_protein: Optional[float]=None
    gb_fat: Optional[float]=None

class MealDay_avg_calorie_schecma(BaseModel):
    calorie: int