
from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from models import Comment, User
from domain.user.user_router import get_current_user
from domain.comment import comment_schema,comment_crud
from domain.meal_hour import meal_hour_crud
from firebase_config import send_fcm_notification
from domain.user.user_crud import get_User,get_User_name
from datetime import datetime, timedelta
from starlette import status

router=APIRouter(
    prefix="/comment"
)

@router.get("/get/{user_id}/{time}/text/mine", response_model=List[comment_schema.Comment_id_name_text])
def get_Comment_date_user_id_text(time: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    유저 식단게시(MealHour) 관한 댓글 조회 : 9page 5번, 12page 5번
     - 입력예시 : user_id = 1, time = 2024-07-01 오후간식
     - 출력 : Comment.user_id, User.name, MealDay.alcohol
    """
    comment = comment_crud.get_Comment(db, user_id=current_user.id, time=time)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comments not found")
    return comment ##user_id, text 열출력(전체 행)

@router.get("/get/{user_id}/{time}/text/formentor", response_model=List[comment_schema.Comment_id_name_text])
def get_Comment_date_user_id_text(user_id: int, time: str, db: Session = Depends(get_db)):
    """
    유저 식단게시(MealHour) 관한 댓글 조회 : 16page 5번, 17page 7번
     - 입력예시 : user_id = 1, time = 2024-07-01 오후간식
     - 출력 : Comment.user_id, User.name, MealDay.alcohol
    """
    comment = comment_crud.get_Comment(db, user_id=user_id, time=time)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comments not found")
    return comment ##user_id, text 열출력(전체 행)

@router.post("/post/{user_id}/{time}/{user_id2}",status_code=status.HTTP_204_NO_CONTENT) ## 게시글 주인id, 시간대, 댓글작성자
async def post_comment(user_id: int, time: str,text: str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    유저 식단게시(MealHour) 관한 댓글 입력 : 12page 5-2번, 17page 7번 (user_id2 = 댓글 작성자)
     - 입력예시 : user_id = 1(식단게시글주인), time = 2024-06-01저녁, text = 맛잇겟다
    """
    meal_post = meal_hour_crud.get_User_Meal(db,user_id=user_id,time=time)
    if meal_post is None:
        raise HTTPException(status_code=404, detail="Meal post not Found")
    Users=get_User(db, id=current_user.id)
    if Users is None:
        raise HTTPException(status_code=404, detail="User2 not Found")

    new_comment = Comment(
        meal_id=meal_post.id,
        text=text,
        date=datetime.utcnow() + timedelta(hours=9),
        user_id=current_user.id
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    user2name= get_User_name(db,current_user.id)
    send_fcm_notification(user_id,"댓글등록",f"{user2name}님의 댓글{text}")

    return {"comment": new_comment}