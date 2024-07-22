from datetime import datetime

import models
from domain.meal_hour.meal_hour_schema import MealHour_gram_update_schema,MealHour_daymeal_get_schema, MealHour_daymeal_get_picture_schema,MealHour_daymeal_time_get_schema
from models import MealDay, MealHour
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

def get_User_Meal(db: Session, user_id: int, time: str):
    user_meal = db.query(MealHour).filter(
        MealHour.user_id == user_id,
        MealHour.time == time
    ).first()
    return user_meal


def update_gram(db:Session, db_MealHourly: MealHour, gram_update: MealHour_gram_update_schema):
    db_MealHourly.id=gram_update.id
    db_MealHourly.user_id=gram_update.user_id
    db_MealHourly.time=gram_update.time
    db_MealHourly.calorie=gram_update.calorie
    db_MealHourly.carb=gram_update.carb
    db_MealHourly.protein=gram_update.protein
    db_MealHourly.fat=gram_update.fat
    db_MealHourly.unit=gram_update.unit
    db_MealHourly.size=gram_update.size
    db.add(db_MealHourly)
    db.commit()

def get_User_Meal_all_name_time(db: Session, user_id: int, time: str): ##time값 잘못입력하면 찾아도 찾을수가 없어서 빈칸 출력함
    date_part = time[:10]  # '2024-06-01 아침'에서 '2024-06-01' 부분만 추출
    user_meal = db.query(MealHour.time, MealHour.name).filter(
        MealHour.user_id == user_id,
        MealHour.time.like(f"{date_part}%")
    ).all()
    meals=[]
    for meal in user_meal:
        time=meal.time[10:]
        meals_schema = MealHour_daymeal_get_schema(
            time=time,
            name=meal.name
        )
        meals.append(meals_schema)
    return meals

def get_User_Meal_all_name(db: Session, user_id: int, time: str): ##time값 잘못입력하면 찾아도 찾을수가 없어서 빈칸 출력함
    date_part = time[:10]  # '2024-06-01 아침'에서 '2024-06-01' 부분만 추출
    user_meal = db.query(MealHour.name).filter(
        MealHour.user_id == user_id,
        MealHour.time.like(f"{date_part}%")
    ).all()
    if not user_meal:
        return []
    return [MealHour_daymeal_get_schema(name=meal.name) for meal in user_meal]


def get_User_Meal_all_time(db: Session, user_id: int, time: str): ##time값 잘못입력하면 찾아도 찾을수가 없어서 빈칸 출력함
    date_part = time[:10]  # '2024-06-01 아침'에서 '2024-06-01' 부분만 추출
    user_meal = db.query(MealHour.time).filter(
        MealHour.user_id == user_id,
        MealHour.time.like(f"{date_part}%")
    ).all()
    return [MealHour_daymeal_time_get_schema(time=meal.time) for meal in user_meal]

def get_User_Meal_all_picutre(db: Session, user_id: int, time: str): ##time값 잘못입력하면 찾아도 찾을수가 없어서 빈칸 출력함
    date_part = time[:10]  # '2024-06-01 아침'에서 '2024-06-01' 부분만 추출
    user_meal = db.query(MealHour.name, MealHour.calorie, MealHour.picture).filter(
        MealHour.user_id == user_id,
        MealHour.time.like(f"{date_part}%")
    ).all()
    return [MealHour_daymeal_get_picture_schema(name=meal.name, calorie=meal.calorie,picture=meal.picture) for meal in user_meal]

def create_file_name(user_id:int)->str:
    time=datetime.now().strftime('%Y-%m-%d-%H%M%S')
    filename = f"{user_id}_{time}"
    return filename