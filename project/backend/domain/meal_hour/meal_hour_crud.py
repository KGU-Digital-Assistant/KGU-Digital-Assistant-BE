from datetime import datetime, date

import models
from domain.meal_hour.meal_hour_schema import MealHour_gram_update_schema,MealHour_daymeal_get_schema, MealHour_daymeal_get_picture_schema,MealHour_daymeal_time_get_schema
from models import MealDay, MealHour, MealTime
from domain.meal_day import meal_day_crud
from domain.meal_day.meal_day_crud import get_MealDay_bydate
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

def get_user_meal(db: Session, user_id: int, daymeal_id: int,mealtime: MealTime):
    user_meal = db.query(MealHour).filter(
        MealHour.user_id == user_id,
        MealHour.time == mealtime,
        MealHour.daymeal_id == daymeal_id
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

def get_User_Meal_all_name_time(db: Session, user_id: int, daymeal_id: int): ##time값 잘못입력하면 찾아도 찾을수가 없어서 빈칸 출력함
    user_meal = db.query(MealHour.time, MealHour.name).filter(
        MealHour.user_id == user_id,
        MealHour.daymeal_id==daymeal_id
    ).all()
    meals=[]
    for meal in user_meal:
        time=meal.time.name
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


# def get_User_Meal_all_time(db: Session, user_id: int, time: str): ##time값 잘못입력하면 찾아도 찾을수가 없어서 빈칸 출력함
#     date_part = time[:10]  # '2024-06-01 아침'에서 '2024-06-01' 부분만 추출
#     user_meal = db.query(MealHour.time).filter(
#         MealHour.user_id == user_id,
#         MealHour.time.like(f"{date_part}%")
#     ).all()
#     return [MealHour_daymeal_time_get_schema(time=meal.time) for meal in user_meal]

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

def get_mealhour_all_by_mealday_id(db: Session, user_id: int, daymeal_id: int):
    meal_hours = db.query(MealHour).filter(
        MealHour.user_id == user_id,
        MealHour.daymeal_id == daymeal_id
    ).all()
    return meal_hours

def update_mealgram(db: Session, mealhour: MealHour, percent: float, size: float):
    mealhour.carb *= percent
    mealhour.protein *= percent
    mealhour.fat *= percent
    mealhour.calorie *= percent
    mealhour.size = size
    db.commit()
    return mealhour

def plus_daily_post(db: Session, user_id: int, date: date,new_food: MealHour):
    daily_post = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)

    if daily_post:
        # 기존 레코드 업데이트
        daily_post.carb += new_food.carb
        daily_post.protein += new_food.protein
        daily_post.fat += new_food.fat
        daily_post.nowcalorie += new_food.calorie

    db.add(daily_post)
    db.commit()
    db.refresh(daily_post)
    return daily_post

def minus_daily_post(db: Session, user_id: int,date: date, new_food: MealHour):
    daily_post = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if daily_post is None:
        raise HTTPException(status_code=404, detail="User not found")
    if daily_post:
        # 기존 레코드 업데이트
        daily_post.carb -= new_food.carb
        daily_post.protein -= new_food.protein
        daily_post.fat -= new_food.fat
        daily_post.nowcalorie -= new_food.calorie

    db.add(daily_post)
    db.commit()
    db.refresh(daily_post)
    return daily_post

def update_heart(db:Session, mealhour: MealHour):
    if mealhour.heart == False:
        mealhour.heart = True
    else:
        mealhour.heart = False
    db.add(mealhour)
    db.commit()
    return mealhour

def update_track_goal(db:Session,mealhour:MealHour):
    if mealhour.track_goal == True:
        mealhour.track_goal = False
    else:
        mealhour.track_goal = True
    db.commit()

def create_mealhour(db:Session, mealhour: MealHour, track_goal: bool):
    mealhour.track_goal =track_goal
    db.add(mealhour)
    db.commit()
    return mealhour