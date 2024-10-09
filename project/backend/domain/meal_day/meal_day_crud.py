from datetime import datetime, date
from sqlalchemy import or_,and_, update
from domain.meal_day.meal_day_schema import Mealday_wca_update_schema
from models import MealDay, Participation
from sqlalchemy.orm import Session
from fastapi import HTTPException


def get_MealDay_bydate(db: Session, user_id: int, date: date):
    mealDaily = db.query(MealDay).filter(
        MealDay.user_id == user_id,
        MealDay.date == date).first()
    if mealDaily is None:
        return None
    return mealDaily


def get_MealDay_bydate_cheating(db: Session, user_id: int, date: date):
    mealDaily = db.query(MealDay.cheating).filter(
        MealDay.user_id == user_id,
        MealDay.date == date).first()
    if mealDaily:
        return mealDaily


def get_MealDay_bydate_wca(db: Session, user_id: int, date: date):
    mealDaily = db.query(
        MealDay.water,
        MealDay.coffee,
        MealDay.alcohol
    ).filter(
        MealDay.user_id == user_id,
        MealDay.date == date
    ).first()
    if mealDaily:
        return mealDaily
    return None


def update_wca(db: Session, db_MealPosting_Daily: MealDay,
               wca_update: Mealday_wca_update_schema):
    db_MealPosting_Daily.water = wca_update.water
    db_MealPosting_Daily.coffee = wca_update.coffee
    db_MealPosting_Daily.alcohol = wca_update.alcohol
    db.add(db_MealPosting_Daily)
    db.commit()


def get_MealDay_bydate_calorie(db: Session, user_id: int, date: date):
    mealDaily = db.query(
        MealDay.goalcalorie,
        MealDay.nowcalorie
    ).filter(
        MealDay.user_id == user_id,
        MealDay.date == date
    ).first()
    if mealDaily:
        return mealDaily
    return None


def get_meal_list(db: Session, month: int, year: int, user_id: int):
    meals = (db.query(MealDay).order_by(MealDay.date.asc()).
             filter(MealDay.user_id == user_id,
                    MealDay.date >= date(year, month, 1),
                    MealDay.date <= date(year, month, 31)).all())

    return meals

def minus_cheating_count_in_participation(db:Session, group_id: int, user_id: int):
    stmt = update(Participation).where(
        Participation.c.group_id == group_id,
        Participation.c.user_id == user_id
    ).values(cheating_count=Participation.c.cheating_count - 1)
    db.execute(stmt)
    db.commit()
    return stmt

def update_mealday_cheating(db:Session, mealday: MealDay):
    if mealday.cheating == 1:
        mealday.cheating = 0
    else:
        mealday.cheating = 1
    db.commit()

def create_meal_day(db: Session, user_id: int, date: date):
    new_meal = MealDay(
        user_id=user_id,
        water=0.0,
        coffee=0.0,
        alcohol=0.0,
        carb=0.0,
        protein=0.0,
        fat=0.0,
        cheating=0,
        goalcalorie=0.0,
        nowcalorie=0.0,
        burncalorie=0.0,
        gb_carb=300.0,
        gb_protein=60.0,
        gb_fat=65.0,
        weight=0.0,
        date=date,
        track_id=None  ## 트랙 user사용중일때 안할때 이거 변경해야할거같은데
    )
    db.add(new_meal)
    db.commit()
    db.refresh(new_meal)
    return new_meal

def update_burncalorie(db: Session, mealday: MealDay, burncalorie: float):
    mealday.burncalorie = burncalorie
    db.add(mealday)
    db.commit()
    return mealday

def update_weight(db: Session, mealday: MealDay, weight: float):
    mealday.weight = weight
    db.add(mealday)
    db.commit()
    return mealday