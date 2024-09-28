import datetime
from enum import Enum
from typing import Optional, List

from fastapi.openapi.models import Schema
from pydantic import BaseModel, field_validator
from models import MealTime


class ClearRoutineSchema(BaseModel):
    id: int
    user_id: int
    mealday_id: Optional[int]
    group_id: int
    routine_date_id: int
    date: datetime.date
    status: bool
    weekday: Optional[int]


class ClearRoutineResponse(BaseModel):
    routine_id: int
    routine_date_id: int
    title: str
    status: bool
    calories: int
    time: MealTime
    clock: datetime.time


class Calendar(BaseModel):
    calendar: List[int]
    all_routine_cnt: int
    clear_routine_cnt: int


class ClearRoutineListUp(BaseModel):
    res_list: List[ClearRoutineSchema] = []
    count: int = 0
