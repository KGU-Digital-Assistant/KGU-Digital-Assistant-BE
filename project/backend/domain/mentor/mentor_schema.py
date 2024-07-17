from fastapi.openapi.models import Schema

from pydantic import BaseModel, EmailStr
from typing import Optional,List

class MentorCreate(BaseModel):
    # user_id: int
    company_id: int
    gym: str
    FA: bool

    class Config:
        from_attributes = True
        check_fields = False
        arbitrary_types_allowed = True

class MentorGym(BaseModel):
    gym: str


class MenteeSchema(BaseModel):
    username: str

###################


class Mentor_schema(BaseModel):
    id: int
    user_id: int
    gym: Optional[str] = None
    FA: Optional[bool] = None
    company_id: Optional[int] = None

class Mentor_add_User_schema(BaseModel):
    mentor_id: int

class Mentor_get_UserInfo_schema(BaseModel):
    id: int
    time: str

class find_User(BaseModel):
    id: int
    name: str

class Users_Info(BaseModel):
    user_id: int
    user_name: str
    user_rank: float
    meal_names: List[str]
    meal_cheating: Optional[int] = None
    now_calorie: Optional[float] = None

class Mentor_get_UserInfo_schema(BaseModel):
    users: List[Users_Info]


