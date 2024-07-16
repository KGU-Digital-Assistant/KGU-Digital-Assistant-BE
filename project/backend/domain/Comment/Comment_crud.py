from datetime import datetime

from domain.Comment.Comment_schema import Comment, Comment_id_text
from models import Comment, MealHour
from sqlalchemy.orm import Session
from fastapi import HTTPException

def get_Comment(db: Session, user_id:int, time:str):
    user_meal = db.query(MealHour).filter(
        MealHour.user_id == user_id,
        MealHour.time == time
    ).first()
    if user_meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    comments = db.query(Comment.user_id,Comment.text).filter(
        Comment.meal_id == user_meal.id
    ).all()
    return [Comment_id_text(user_id=comment.user_id, text=comment.text) for comment in comments]


