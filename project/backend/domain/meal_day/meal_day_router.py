import datetime

from fastapi import APIRouter,  Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_,and_, update
from typing import List
from starlette import status
from database import get_db
from domain.meal_day import meal_day_schema, meal_day_crud
from domain.group import group_crud
from domain.meal_hour import meal_hour_crud
from models import MealDay, MealHour, User,TrackRoutine, Participation
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
    """
    식단일일(MealDay) cheating 여부 조회 : 9page 4-1번
     - 입력예시 : user_id = 1, daytime = 2024-06-01
     - 출력 : MealDay.cheating
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    cheating = meal_day_crud.get_MealDay_bydate_cheating(db,user_id=user_id,date=date)
    if cheating is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return cheating  ## cheating 열만 출력

@router.get("/get/{user_id}/{daytime}/cheating_count", response_model=meal_day_schema.MealDay_cheating_count_get_schema)
def get_MealDay_date_cheating_count(user_id: int, daytime: str, db: Session = Depends(get_db)):
    """
    식단일일(MealDay) cheating 갯수 조회 : 9page 4-2번
     - 입력예시 : user_id = 1, daytime = 2024-06-01
     - 출력 : Participation.cheating
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealcheating = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
    if mealcheating is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")

    if mealcheating.track_id is None:
        return {"cheating_count": 9999}

    group_participation = group_crud.get_group_by_date_track_id(db, user_id=user_id, date=date,
                                                                track_id=mealcheating.track_id)
    if group_participation is None:
        raise HTTPException(status_code=404, detail="Group not found")

    group, cheating_count, user_id2 = group_participation
    return {"cheating_count": cheating_count, "user_id2": user_id2}

@router.patch("/update/{user_id}/{daytime}/cheating", status_code=status.HTTP_204_NO_CONTENT)
async def update_MealDay_date_cheating(user_id: int, daytime: str,
                                  db: Session = Depends(get_db)):
    """
    식단일일(MealDay) cheating 갯수 차감 : 9page 4-3번
     - 입력예시 : user_id = 1, daytime = 2024-06-01
     - 결과 : Participation.cheating_count - 1
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealcheating = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
    if mealcheating is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")

    if mealcheating.track_id:
        group_participation = group_crud.get_group_by_date_track_id(db,user_id=user_id,date=date,track_id=mealcheating.track_id)
        if group_participation is None:
            raise HTTPException(status_code=404, detail="Group not found")

        group, cheating_count, user_id2 = group_participation # 튜플 언패킹(group, participation obj 로 나눔)

        if mealcheating.cheating == 1:
            return {"detail": "today already cheating"}

        if cheating_count is None or cheating_count <= 0:
            return {"detail": " cheating is 0"}

        # SQLAlchemy Core를 사용하여 cheating_count 업데이트
        stmt = update(Participation).where(
            Participation.c.group_id == group.id,
            Participation.c.user_id == user_id
        ).values(cheating_count=Participation.c.cheating_count - 1)
        db.execute(stmt)
        db.commit()

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
def get_MealDay_dday_goal_real(user_id: int, daytime: str, db: Session=Depends(get_db)):
    """
    해당일 트랙 일차 및 루틴 표시 : 13page 6번
     - 입력예시 : user_id = 1, time = 2024-06-01
     - 출력 : D-day, [TrackRoutin.time(아침,점심)], [MealHour.time(아침,점심), MealHour.name(음식명)]
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealday = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if mealday is None:
        raise HTTPException(status_code=404, detail="MealDay not found")
    if mealday.track_id is None:
        raise HTTPException(status_code=404, detail="No Use Track today")

    # 요일을 정수로 얻기 (월요일=0, 일요일=6)
    weekday_number = date.weekday()
    # 요일을 한글로 얻기 (월요일=0, 일요일=6)
    weekday_str = ["월", "화", "수", "목", "금", "토", "일"][weekday_number]
    group_info = group_crud.get_group_by_date_track_id(db, user_id=user_id, date=date, track_id=mealday.track_id)
    if group_info is None:
        raise HTTPException(status_code=404, detail="Group not found")
    group, cheating_count, user_id2 = group_info
    solodate = date - group.start_day
    days = str(solodate.days + 1)

    dday = (date - group.start_day).days + 1
    combined_results = db.query(TrackRoutine.time, TrackRoutine.title).filter(
        and_(
            TrackRoutine.track_id == mealday.track_id,
            or_(
                TrackRoutine.week.like(f"%{weekday_str}%"),
                TrackRoutine.date.like(f"%{days}%"),

            )
        )
    ).all()

    # goal_time을 문자열 리스트로 변환
    goal_time = [{"time": routine.time, "title": routine.title} for routine in combined_results]

    meal_info = meal_hour_crud.get_User_Meal_all_name_time(db,user_id=user_id,time=daytime)
    return {"dday" : dday, "goal" : goal_time, "real" : meal_info}
