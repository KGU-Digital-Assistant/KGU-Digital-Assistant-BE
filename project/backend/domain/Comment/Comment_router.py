
from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from models import Comment
from domain.Comment import Comment_schema,Comment_crud
from domain.MealHour import MealHour_crud
from firebase_config import send_fcm_notification
from domain.User.user_crud import get_User,get_User_name
from datetime import datetime
from starlette import status

router=APIRouter(
    prefix="/Comment"
)

@router.get("/get/{user_id}/{time}/text", response_model=List[Comment_schema.Comment_id_text])
def get_Comment_date_user_id_text(user_id: int, time: str, db: Session = Depends(get_db)):
    comment = Comment_crud.get_Comment(db, user_id=user_id, time=time)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comments not found")
    return comment ##user_id, text 열출력(전체 행)

@router.post("/post/{user_id}/{time}/{user_id2}",status_code=status.HTTP_204_NO_CONTENT) ## 게시글 주인id, 시간대, 댓글작성자
async def post_comment(user_id: int, time: str,user_id2: int,text: str = Form(...), db: Session = Depends(get_db)):
    meal_post = MealHour_crud.get_User_Meal(db,user_id=user_id,time=time)
    if meal_post is None:
        raise HTTPException(status_code=404, detail="Meal post not Found")
    Users=get_User(db, id=user_id2)
    if Users is None:
        raise HTTPException(status_code=404, detail="User2 not Found")

    new_comment = Comment(
        meal_id=meal_post.id,
        text=text,
        date=datetime.utcnow(),
        user_id=user_id2
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    user2name= get_User_name(db,user_id2)
    send_fcm_notification(user_id,"댓글등록",f"{user2name}님의 댓글{text}")

    return {"comment": new_comment}