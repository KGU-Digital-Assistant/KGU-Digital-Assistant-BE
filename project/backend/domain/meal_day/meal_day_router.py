import datetime

from fastapi import APIRouter,  Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_,and_
from typing import List
from starlette import status
from database import get_db
from domain.meal_day import meal_day_schema, meal_day_crud
from domain.group import group_crud
from domain.meal_hour import meal_hour_crud
from models import MealDay, MealHour, User,TrackRoutine
from datetime import datetime,timedelta
from firebase_config import bucket

router=APIRouter(
    prefix="/meal_day"
)

@router.get("/get/{user_id}/{daytime}", response_model=List[meal_day_schema.MealDay_schema])
def get_MealDay_date(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    MealDaily = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if not MealDaily:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return [MealDaily] ##전체 열 출력

@router.get("/get/{user_id}/{daytime}/cheating", response_model=meal_day_schema.MealDay_cheating_get_schema)
def get_MealDay_date_cheating(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    cheating = meal_day_crud.get_MealDay_bydate_cheating(db,user_id=user_id,date=date)
    if cheating is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return cheating  ## cheating 열만 출력

@router.patch("/update/{user_id}/{daytime}/cheating", status_code=status.HTTP_204_NO_CONTENT)
async def update_MealDay_date_cheating(user_id: int, daytime: str,
                                  db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealcheating = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
    if mealcheating is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")

    if mealcheating.track_id:
        user_cheating_count = db.query(User).filter(User.id == mealcheating.user_id).first()
        if user_cheating_count.cheating_count == 0:
            return {"detail": " cheating is 0"}
        else:
            if mealcheating.cheating == 1:
                return {"detail": "today already cheating"}
            if user_cheating_count.cheating_count is not None and user_cheating_count.cheating_count >=1:
                user_cheating_count.cheating_count -= 1
                db.commit()
                db.refresh(user_cheating_count)
                mealcheating.cheating = 1
                db.commit()
                db.refresh(mealcheating)
                return {"detail": "cheating updated successfully"}
    else:
        if mealcheating.cheating == 1:
            mealcheating.cheating = 0
            db.commit()
            db.refresh(mealcheating)
        else:
            mealcheating.cheating = 1
            db.commit()
            db.refresh(mealcheating)
        return {"detail": "cheating updated successfully"}


@router.get("/get/{user_id}/{daytime}/wca", response_model=meal_day_schema.MealDay_wca_get_schema)
def get_MealDay_date_wca(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    """
    식단일일(MealDay) wca 조회 : 9page 5번
     - 입력예시 : user_id = 1, daytime = 2024-06-01
     - 출력 : MealDay.water, MealDay.coffee, MealDay.alcohol
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    wca = meal_day_crud.get_MealDay_bydate_wca(db,user_id=user_id,date=date)
    if wca is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return wca ## water, coffee, alcohol 열만 출력

@router.patch("/update/{user_id}/{daytime}/wca", status_code=status.HTTP_204_NO_CONTENT)
def update_Daymeal_date_wca(user_id: int,daytime: str,
                       mealdaily_wca_update: meal_day_schema.Mealday_wca_update_schema, db: Session = Depends(get_db)):
    """
    식단일일(MealDay) wca 업뎃 : 9page 5번
     - 입력예시 : user_id = 1, daytime = 2024-06-01, Json{water=1, coffee=2, alcohol = 5}
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealwca = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)

    if mealwca is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")
    meal_day_crud.update_wca(db=db,db_MealPosting_Daily=mealwca,wca_update=mealdaily_wca_update)

    return {"detail": "wca updated successfully"}

@router.post("/post/{user_id}/{daytime}",status_code=status.HTTP_204_NO_CONTENT)
def post_MealDay_date(user_id: int, daytime: str, db: Session=Depends(get_db)):
    """
    식단일일(MealDay) db생성 : 앱실행시(당일날짜로), 13page 1번 (클릭시 생성), track시작시 해당기간에 생성
     - 입력예시 : user_id = 1, daytime = 2024-06-01
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    meal=meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if meal:
        return
    else:
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
            gb_carb = None,
            gb_protein = None,
            gb_fat = None,
            date = date,
            track_id = None ## 트랙 user사용중일때 안할때 이거 변경해야할거같은데
        )
        db.add(new_meal)
        db.commit()
        db.refresh(new_meal)

@router.get("/get/{user_id}/{daytime}/calorie", response_model=meal_day_schema.MealDay_calorie_get_schema)
def get_MealDay_date_calorie(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    """
    식단일일(MealDay) goal, now calorie : 13page 3-1번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
     - 출력 : MealDay.goalcaloire, MealDay.nowcaloire
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    calorie = meal_day_crud.get_MealDay_bydate_calorie(db,user_id=user_id,date=date)
    if calorie is None:
        raise HTTPException(status_code=404, detail="Calorie posting not found")
    return calorie ## goal,now calorie 열만 출력


@router.get("/get/{id}/{daytime}/track", response_model=meal_day_schema.MealDay_track_today_schema)
def get_Track_Mealhour(id: int, daytime: str, db: Session = Depends(get_db)):
    """
    식단일일(MealDay) 식단게시글(MealHour) 전체조회(track 이용중일떄만) : 13page 2-1번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
     - 출력 : 당일 식단게시글[MealHour.name, MealHour.calorie, MealHour.date, MealHour.heart, picture_url, Mealhour.track_goal]
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    meal_today = db.query(MealDay).filter(MealDay.user_id == id, MealDay.date == date).first()
    if meal_today is None or meal_today.track_id is None:
        raise HTTPException(status_code=404, detail="Track not using")

    result = []
    date_part = daytime[:10]
    meal_hours = db.query(MealHour).filter(
        MealHour.user_id == id,
        MealHour.time.like(f"{date_part}%")
    ).all()

    for meal in meal_hours:
        try:
            # 서명된 URL 생성 (URL은 1시간 동안 유효)
            blob = bucket.blob(meal.picture)
            signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        meal_info = meal_day_schema.MealDay_track_hour_schema(
            name=meal.name,
            calorie=meal.calorie,
            date=meal.date,
            heart=meal.heart,
            picture=signed_url,
            track_goal=meal.track_goal
        )
        result.append(meal_info)

    return meal_day_schema.MealDay_track_today_schema(mealday=result)

@router.get("/get/{user_id}/{daytime}/dday_goal_real",response_model=meal_day_schema.MealDay_track_dday_goal_real_schema)
def get_MealDay_dday_goal_real(id: int, daytime: str, db: Session=Depends(get_db)):
    """
    식단일일(MealDay) 모 : 13page 2-1번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
     - 출력 : 당일 식단게시글[MealHour.name, MealHour.calorie, MealHour.date, MealHour.heart, picture_url, Mealhour.track_goal]
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealday = meal_day_crud.get_MealDay_bydate(db,user_id=id,date=date)
    if mealday.track_id is None:
        return {"detail" : "track not use"}

    group_info = group_crud.get_Group_bydate(db,user_id=id,date=date)
    dday = group_info.finish_day - date

    weekday_number = date.weekday()
    weekday_str = ["월", "화", "수", "목", "금", "토", "일"][weekday_number]
    track_info = db.query(TrackRoutine.time).filter(and_(TrackRoutine.track_id==mealday.track_id,
                                                          or_(TrackRoutine.date==date,
                                                              TrackRoutine.week.like(f"{weekday_str}"))))
    goal_time = List[track_info]

    meal_info = meal_hour_crud.get_User_Meal_all_name(db,user_id=id,time=daytime)

    return {"dday" : dday, "goal" : goal_time, "real" : meal_info}
