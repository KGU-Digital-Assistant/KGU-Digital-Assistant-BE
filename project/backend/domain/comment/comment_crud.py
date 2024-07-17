from datetime import datetime

from domain.comment.comment_schema import Comment, Comment_id_name_text
from models import Comment, MealHour,User
from sqlalchemy.orm import Session
from fastapi import HTTPException

def get_Comment(db: Session, user_id:int, time:str):
    user_meal = db.query(MealHour).filter(
        MealHour.user_id == user_id,
        MealHour.time == time
    ).first()
    if user_meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    comments = db.query(Comment.user_id, Comment.text).filter(
        Comment.meal_id == user_meal.id
    ).all()
    result = []
    for comment in comments:
        user_name = db.query(User.name).filter(User.id == comment.user_id).first()
        if user_name:
            result.append(Comment_id_name_text(user_id=comment.user_id, name=user_name.name, text=comment.text))
    return result


