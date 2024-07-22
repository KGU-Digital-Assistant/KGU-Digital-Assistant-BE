from datetime import datetime
from typing import List

import requests
from fastapi import APIRouter, HTTPException, Depends, Request, status, Query, Form
from sqlalchemy.orm import Session
from database import get_db
from domain.group import group_crud
from domain.meal_day import meal_day_crud
from domain.mentor.mentor_crud import create_mentor, update_mentor_gym, mentor_delete, matching_mentor
from domain.mentor import mentor_schema, mentor_crud
from domain.track import track_crud
from models import Mentor, User, MealHour, MealDay
from domain.user import user_crud, user_router


router = APIRouter(
    prefix="/mentor",
)

def get_current_mentor(_user_id: int, db: Session = Depends(get_db)):
    return user_router.get_current_user()

# 일반 회원 -> 트레이너가 될 때
@router.post("/create", status_code=201)
async def mentor_create(_mentor_create: mentor_schema.MentorCreate,
                        _current_user: User = Depends(user_router.get_current_user),
                        db: Session = Depends(get_db)):
    if not _current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not User",
        )
    create_mentor(mentor_create=_mentor_create, _user_id=_current_user.id, db=db)
    return {"status": "ok"}

@router.post("/add/user", status_code=201)
def connect_user_to_mentor(_mentee: mentor_schema.MenteeSchema,
                           _mentor: User = Depends(user_router.get_current_user),
                           db: Session = Depends(get_db)):
    mentee = user_crud.get_user_by_username(db, _mentee.username)
    if not mentee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentee not found",
        )
    if mentee.mentor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already connected",
        )

    matching_mentor(mentee=mentee, _mentor_id=_mentor.id, db=db)
    return {"status": "ok"}

@router.patch("/gym/update", status_code=201)
def gym_update(_mentor_gym: mentor_schema.MentorGym,
               _current_user: User = Depends(user_router.get_current_user),
               db: Session = Depends(get_db)):
    if not _current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not User",
        )
    mentor = update_mentor_gym(_current_user.id, _mentor_gym, db)
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="mentor not found",
        )
    return {"status": "ok"}

@router.delete("/delete", status_code=204)
def delete_mentor(cur_user: User = Depends(user_router.get_current_user), db: Session = Depends(get_db)):
    if mentor_delete(cur_user.id, db):
        return {"status": "ok"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="mentor not found",
    )

##############################

@router.get("/get/{id}", response_model=mentor_schema.Mentor_schema)
def get_id_Mentor(id: int, db: Session = Depends(get_db)):
    Mentors = mentor_crud.get_Mentor(db,user_id=id)
    if Mentors is None:
        raise HTTPException(status_code=404, detail="mentor not found")
    return Mentors ##전체 열 출력

@router.patch("/addUser/{id}", response_model=mentor_schema.Mentor_add_User_schema) ## mentor의 user.id 입력
def add_Mentor_to_User(id: int, email: str=Form(...), db: Session=Depends(get_db)):
    Mentors=mentor_crud.get_Mentor(db,user_id=id)
    if Mentors is None:
        raise HTTPException(status_code=404, detail="mentor not found")
    Users =user_crud.get_User_byemail(db,mail=email)
    if Users is None:
        raise HTTPException(status_code=404, detail="User not found")
    Users.mentor_id = Mentors.id
    db.add(Users)
    db.commit()
    db.refresh(Users)
    return Users

@router.get("/findUser/{id}",response_model=List[mentor_schema.find_User])
def find_User(id: int, name:str = Query(...), db: Session = Depends(get_db)):
    """
    회원들  : 15page 1번
     - 입력예시 : Mentor.user_id = 1
     - 출력 : 회원목록[User.id, User.name]
    """
    Users = mentor_crud.get_Users_byMentor_name(db, user_id=id, name=name)
    if Users is None:
        raise HTTPException(status_code=404, detail="Users not found")
    return Users

@router.get("/getUserInfo/{id}/{daytime}", response_model=mentor_schema.Mentor_get_UserInfo_schema)
def get_Mentors_User(id: int, daytime: str,db: Session = Depends(get_db)):
    """
    회원들리스트 정보(당일 Calorie, 식단내용 등) 조회 : 15page 4번
     - 입력예시 : user_id = 1, daytime = 2024-06-01
     - 출력 : 회원들리스트정보 출력
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    Users = mentor_crud.get_Users_name_rank_byMentor(db,user_id=id)
    if Users is None:
        raise HTTPException(status_code=404, detail="Users not found")
    result=[]

    date_part=daytime[:10]

    for user in Users:
        ranks = user_crud.get_User_rank(db,user.id)
        # User의 meal_hour 정보를 특정 날짜에 맞게 찾기.
        meal_hours = db.query(MealHour).filter(
                MealHour.user_id == user.id,
                MealHour.time.like(f"{date_part}%")
        ).all()

        meal_names = [meal_hour.name for meal_hour in meal_hours]

        # User의 meal_day 정보를 특정 날짜에 맞게 찾기.
        meal_day = meal_day_crud.get_MealDay_bydate(db,user_id=user.id,date=date)
        now_calorie = meal_day.nowcalorie if meal_day else None
        cheating = meal_day.cheating if meal_day else None
        track_name=None
        dday=None
        if meal_day and meal_day.track_id:
            using_track = track_crud.get_Track_bytrack_id(db,track_id=meal_day.track_id)
            if using_track:
                track_name = using_track.name
            group_info = group_crud.get_group_by_date_track_id_in_part(db,user_id=user.id, date=date,track_id=meal_day.track_id)
            if group_info and group_info is not None:
                group, cheating_count, user_id2, flag, finish_date =group_info
                dday= (date - group.start_day).days + 1

        user_info = mentor_schema.Users_Info(
            user_id=user.id,
            user_name=user.name,
            user_rank=ranks,
            meal_names=meal_names,
            meal_cheating=cheating,
            now_calorie=now_calorie,
            track_name=track_name,
            dday=dday
        )
        result.append(user_info)

    return mentor_schema.Mentor_get_UserInfo_schema(users=result)

@router.get("/get/{user_id}/{year}/{month}/cheatingday", response_model=List)
def get_cheating_days(user_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """
    회원의 월별 cheating 날짜 조회  : 16page 3-1번
     - 입력예시 : User.user_id(회원) = 1, year = 2024, month = 07
     - 출력 : cheating 날짜[2024-07-01,2024-07-06]
    """
    cheating_day = mentor_crud.get_cheating_days(db, user_id, year, month)
    if cheating_day is None:
        raise HTTPException(status_code=404, detail="No data found")
    return cheating_day