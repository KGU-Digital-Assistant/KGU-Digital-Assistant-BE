from datetime import datetime, date

from domain.comment.comment_schema import Comment, Comment_id_name_text
from models import Comment, MealHour,User, MealTime
from domain.meal_day.meal_day_crud import get_MealDay_bydate
from sqlalchemy.orm import Session
from fastapi import HTTPException

def get_Comment(db: Session, user_id:int, date: date, mealtime: MealTime):
    mealtoday = get_MealDay_bydate(db,user_id=user_id, date=date)
    if mealtoday is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    user_meal = db.query(MealHour).filter(
        MealHour.user_id == user_id,
        MealHour.time == mealtime,
        MealHour.daymeal_id == mealtoday.id
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
def time_parse(time: str):
    if time == "아침":
        return MealTime.BREAKFAST
    if time == "아점":
        return MealTime.BRUNCH
    if time == "점심":
        return MealTime.LUNCH
    if time == "점저":
        return MealTime.LINNER
    if time == "저녁":
        return MealTime.DINNER
    if time == "간식":
        return MealTime.SNACK

