from datetime import datetime
from typing import List

import requests
from fastapi import APIRouter, HTTPException, Depends, Request, status, Query, Form
from sqlalchemy.orm import Session
from database import get_db
from domain.mentor.mentor_crud import create_mentor, update_mentor_gym, mentor_delete, matching_mentor
from domain.mentor import mentor_schema, mentor_crud
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
def invite_user_to_mentor(_mentee: mentor_schema.MenteeSchema,
                           _mentor: User = Depends(user_router.get_current_user),
                           db: Session = Depends(get_db)):
    """
    트레이너가 회원을 담당하고자 요청보냄
    """
    if not mentor_crud.get_mentor(_mentor.id, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not Mentor",
        )

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

    invitation = mentor_crud.mentor_invite(mentee_id=_mentee.id, mentor_id=_mentor.id, db=db)

    fcm_token = mentee.fcm_token
    response = user_crud.send_push_invite(
        fcm_token=fcm_token,
        title="담당 트레이너 요청",
        body=f"{_mentor.username} 트레이너님이 회원님을 담당하고자 요청을 보냈습니다."
    )
    return {"response" : response, "invitation_id": invitation.id}


@router.post("/invitation/{invite_id}/respond", status_code=201)
def respond_mentee(invite_id: int,
                   response: str,
                   _mentee: User = Depends(user_router.get_current_user),
                   db: Session = Depends(get_db)):
    """
    회원이 수락 또는 거절 응답 api
    : response에 수락(accepted)인지 거절(rejected)인지 줘야함
    """
    invitation = mentor_crud.get_invite_by_id(invite_id, db)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if response.lower() not in ["accepted", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid response",
        )

    if _mentee.mentor_id:
        user_crud.invitation_respond(invitation_id=invitation.id,
                                     response="rejected",
                                     db=db,
                                     _mentee_id=_mentee.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already connected",
        )

    user_crud.invitation_respond(invitation_id=invitation.id,
                                 response=response,
                                 db=db,
                                 _mentee_id=_mentee.id)
    return {"status": "ok"}

@router.post("/manage/delete", status_code=201)



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
    Mentors = mentor_crud.get_mentor(db, user_id=id)
    if Mentors is None:
        raise HTTPException(status_code=404, detail="mentor not found")
    return Mentors ##전체 열 출력

@router.patch("/addUser/{id}", response_model=mentor_schema.Mentor_add_User_schema) ## mentor의 user.id 입력
def add_Mentor_to_User(id: int, email: str=Form(...), db: Session=Depends(get_db)):
    Mentors=mentor_crud.get_mentor(db, user_id=id)
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
    Users = mentor_crud.get_Users_byMentor_name(db, user_id=id, name=name)
    if Users is None:
        raise HTTPException(status_code=404, detail="Users not found")
    return Users

@router.get("/getUserInfo/{id}/{daytime}", response_model=mentor_schema.Mentor_get_UserInfo_schema)
def get_Mentors_User(id: int, daytime: str,db: Session = Depends(get_db)):
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
        # User의 meal_hour 정보를 특정 날짜에 맞게 찾습니다.
        meal_hours = db.query(MealHour).filter(
                MealHour.user_id == user.id,
                MealHour.time.like(f"{date_part}%")
        ).all()

        meal_names = [meal_hour.name for meal_hour in meal_hours]

        # User의 meal_day 정보를 특정 날짜에 맞게 찾습니다.
        meal_day = db.query(MealDay).filter(
                MealDay.user_id == user.id,
                MealDay.date == date
        ).first()

        now_calorie = meal_day.nowcalorie if meal_day else None
        cheating = meal_day.cheating if meal_day else None

        user_info = mentor_schema.Users_Info(
            user_id=user.id,
            user_name=user.name,
            user_rank=user.rank,
            meal_names=meal_names,
            meal_cheating=cheating,
            now_calorie=now_calorie
        )
        result.append(user_info)

    return mentor_schema.Mentor_get_UserInfo_schema(users=result)

@router.get("/get/{user_id}/{year}/{month}/cheatingday", response_model=List)
def get_cheating_days(user_id: int, year: int, month: int, db: Session = Depends(get_db)):
    cheating_day = mentor_crud.get_cheating_days(db, user_id, year, month)
    if cheating_day is None:
        raise HTTPException(status_code=404, detail="No data found")
    return cheating_day