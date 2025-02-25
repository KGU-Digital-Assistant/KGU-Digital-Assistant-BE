import datetime

from fastapi import APIRouter,  Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from starlette import status
from database import get_db
from domain.meal_day import meal_day_schema, meal_day_crud
from domain.group import group_crud
from domain.meal_hour import meal_hour_crud
from domain.track_routine import track_routine_crud
from domain.user import user_crud
from domain.user.user_router import get_current_user
from models import MealDay, MealHour, User,TrackRoutine, TrackRoutineDate
from datetime import datetime,timedelta
from firebase_config import bucket
from calendar import monthrange

router=APIRouter(
    prefix="/meal_day"
)


@router.get("/get/calender/{user_id}", response_model=List[meal_day_schema.MealDay_schema])
def get_calendar(user_id: int, month: int, year: int, db: Session = Depends(get_db)):
    """
    user_id와 month 정보를 넘기면 해당 월에 식단 정보 날짜 순으로 반환
    """
    user = user_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    meals = meal_day_crud.get_meal_list(db, month, year, user_id)
    return meals


@router.get("/get/meal_day/{user_id}/{daytime}", response_model=List[meal_day_schema.MealDay_schema])
def get_MealDay_date(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    MealDaily = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if not MealDaily:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return [MealDaily] ##전체 열 출력

@router.get("/get/cheating/{daytime}", response_model=meal_day_schema.MealDay_cheating_get_schema)
def get_MealDay_date_cheating(daytime: str,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단일일(MealDay) cheating 여부 조회 : 9page 4-1번
     - 입력예시 : daytime = 2024-06-01
     - 출력 : MealDay.cheating
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    cheating = meal_day_crud.get_MealDay_bydate_cheating(db,user_id=current_user.id,date=date)
    if cheating is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return cheating  ## cheating 열만 출력

@router.get("/get/cheating_count/{daytime}", response_model=meal_day_schema.MealDay_cheating_count_get_schema)
def get_MealDay_date_cheating_count(daytime: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단일일(MealDay) cheating 갯수 조회 : 9page 4-2번
     - 입력예시 :  daytime = 2024-06-01
     - 출력 : Participation.cheating
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealcheating = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
    if mealcheating is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")

    if mealcheating.track_id is None:
        return {"cheating_count": 9999, "user_id2": current_user.id}

    group_participation = group_crud.get_group_by_date_track_id_in_part(db, user_id=current_user.id, date=date,
                                                                track_id=mealcheating.track_id)
    if group_participation is None:
        raise HTTPException(status_code=404, detail="Group not found")

    group, cheating_count, user_id2, flag, finish_date = group_participation
    return {"cheating_count": cheating_count, "user_id2": user_id2}

@router.patch("/update/cheating/{daytime}", status_code=status.HTTP_204_NO_CONTENT)
async def update_MealDay_date_cheating(daytime: str,current_user: User = Depends(get_current_user),
                                  db: Session = Depends(get_db)):
    """
    식단일일(MealDay) cheating 갯수 차감 : 9page 4-3번
     - 입력예시 : daytime = 2024-06-01
     - 결과 : Participation.cheating_count - 1
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealcheating = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
    if mealcheating is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")

    if mealcheating.track_id:
        group_participation = group_crud.get_group_by_date_track_id_in_part(db,user_id=current_user.id,date=date,track_id=mealcheating.track_id)
        if group_participation is None:
            raise HTTPException(status_code=404, detail="Group not found")

        group, cheating_count, user_id2, flag, finish_date = group_participation # 튜플 언패킹(group, participation obj 로 나눔)

        if mealcheating.cheating == 1:
            raise HTTPException(status_code=402, detail="Today already cheating_day")

        if cheating_count is None or cheating_count <= 0:
            raise HTTPException(status_code=403, detail="cheating count = 0")

        ##참여 Tbl의 cheating count를 1 감소
        stmt = meal_day_crud.minus_cheating_count_in_participation(db, group_id=group.id, user_id=current_user.id)
        ## cheating이 1이면 0으로, 0이면 1로 변경
        meal_day_crud.update_mealday_cheating(db, mealday = mealcheating)

        return {"detail": "cheating updated successfully"}
    else:
        ## cheating이 1이면 0으로, 0이면 1로 변경
        meal_day_crud.update_mealday_cheating(db, mealday = mealcheating)
        return {"detail": "cheating updated successfully"}


@router.get("/get/wca/mine/{daytime}", response_model=meal_day_schema.MealDay_wca_get_schema)
def get_MealDay_date_wca(daytime: str , current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단일일(MealDay) wca 조회 : 9page 5번, 13page 4번
     - 입력예시 : daytime = 2024-06-01
     - 출력 : MealDay.water, MealDay.coffee, MealDay.alcohol
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    wca = meal_day_crud.get_MealDay_bydate_wca(db,user_id=current_user.id,date=date)
    if wca is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return wca ## water, coffee, alcohol 열만 출력

@router.get("/get/wca/formentor/{user_id}/{daytime}", response_model=meal_day_schema.MealDay_wca_get_schema)
def get_MealDay_date_wca(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    """
    식단일일(MealDay) wca 조회 : 16page 4번
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

@router.patch("/update/wca/{daytime}", status_code=status.HTTP_204_NO_CONTENT)
def update_Daymeal_date_wca(daytime: str, mealdaily_wca_update: meal_day_schema.Mealday_wca_update_schema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단일일(MealDay) wca 업뎃 : 9page 5번
     - 입력예시 : daytime = 2024-06-01, Json{water=1, coffee=2, alcohol = 5}
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealwca = meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)

    if mealwca is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")
    meal_day_crud.update_wca(db=db,db_MealPosting_Daily=mealwca,wca_update=mealdaily_wca_update)

    return {"detail": "wca updated successfully"}

@router.post("/post/meal_day/{daytime}",status_code=status.HTTP_204_NO_CONTENT)
def post_MealDay_date(daytime: str, current_user: User = Depends(get_current_user), db: Session=Depends(get_db)):
    """
    식단일일(MealDay) db생성 : 앱실행시(당일날짜로), 13page 1번 (클릭시 생성), track시작시 해당기간에 생성
     - 입력예시 : daytime = 2024-06-01
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    meal=meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)
    if meal:
        return
    else:
        meal_day_crud.create_meal_day(db, user_id = current_user.id, date = date)

@router.post("/post/meal_day/{year}/{month}", status_code=status.HTTP_204_NO_CONTENT)
def post_MealDay_month(year: int, month: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    특정 월 동안의 식단일일(MealDay) db생성 : 앱실행시(해당월 입력) 해당기간에 생성
    - 입력예시 : year = 2024, month = 6
    """
    try:
        # 주어진 월의 첫날과 마지막 날을 구합니다.
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, monthrange(year, month)[1]).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # 해당 월의 모든 날짜에 대해 반복합니다.
    date_iter = first_day
    while date_iter <= last_day:
        meal = meal_day_crud.get_MealDay_bydate(db, user_id = current_user.id, date=date_iter)
        if not meal:
            meal_day_crud.create_meal_day(db, user_id = current_user.id, date = date_iter)
        # 다음 날짜로 이동
        date_iter += timedelta(days=1)


@router.get("/get/calorie/{daytime}", response_model=meal_day_schema.MealDay_calorie_get_schema)
def get_MealDay_date_calorie(daytime: str ,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단일일(MealDay) goal, now calorie : 13page 3-1번
     - 입력예시 : daytime = 2024-06-01
     - 출력 : MealDay.goalcaloire, MealDay.nowcaloire
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    calorie = meal_day_crud.get_MealDay_bydate_calorie(db,user_id=current_user.id,date=date)
    if calorie is None:
        raise HTTPException(status_code=404, detail="Calorie posting not found")
    return calorie ## goal,now calorie 열만 출력


@router.get("/get/track/mine/{daytime}", response_model=meal_day_schema.MealDay_track_today_schema)
def get_Track_Mealhour(daytime: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단일일(MealDay) 식단게시글(MealHour) 전체조회(track 이용중일떄만) : 13page 2-1번
     - 입력예시 : daytime = 2024-06-01
     - 출력 : 당일 식단게시글[MealHour.name, MealHour.calorie, MealHour.date, MealHour.heart, picture_url, Mealhour.track_goal]
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    meal_today = meal_day_crud.get_MealDay_bydate(db, user_id = current_user.id, date = date)
    if meal_today is None or meal_today.track_id is None:
        raise HTTPException(status_code=404, detail="Track not using")

    result = []
    meal_hours = meal_hour_crud.get_mealhour_all_by_mealday_id(db, user_id = current_user.id, daymeal_id = meal_today.id)

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

@router.get("/get/track/formentor/{id}/{daytime}", response_model=meal_day_schema.MealDay_track_today_schema)
def get_Track_Mealhour(id: int, daytime: str, db: Session = Depends(get_db)):
    """
    식단일일(MealDay) 식단게시글(MealHour) 전체조회(track 이용중일떄만) : 13page 2-1번
     - 입력예시 : user_id = 1, daytime = 2024-06-01
     - 출력 : 당일 식단게시글[MealHour.name, MealHour.calorie, MealHour.date, MealHour.heart, picture_url, Mealhour.track_goal]
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    meal_today = meal_day_crud.get_MealDay_bydate(db, user_id = id, date = date)

    if meal_today is None or meal_today.track_id is None:
        raise HTTPException(status_code=404, detail="Track not using")

    result = []
    meal_hours = meal_hour_crud.get_mealhour_all_by_mealday_id(db, user_id=id, daymeal_id=meal_today.id)

    for meal in meal_hours:
        try:
            # 서명된 URL 생성 (URL은 1시간 동안 유효)
            blob = bucket.blob(meal.picture)
            signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        meal_info = meal_day_schema.MealDay_track_hour_schema(
            name=meal.name,
            calorie=meal.nowcalorie,
            date=meal.date,
            heart=meal.heart,
            picture=signed_url,
            track_goal=meal.track_goal
        )
        result.append(meal_info)

    return meal_day_schema.MealDay_track_today_schema(mealday=result)

@router.get("/get/dday_goal_real/{daytime}",response_model=meal_day_schema.MealDay_track_dday_goal_real_schema)
def get_MealDay_dday_goal_real(daytime: str, current_user: User = Depends(get_current_user), db: Session=Depends(get_db)):
    """
    해당일 트랙 일차 및 루틴 표시 : 13page 6번
     - 입력예시 : daytime = 2024-06-01
     - 출력 : D-day, [TrackRoutin.time(아침,점심)], [MealHour.time(아침,점심), MealHour.name(음식명)]
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealday = meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)
    if mealday is None:
        raise HTTPException(status_code=404, detail="MealDay not found")
    if mealday.track_id is None:
        return {"dday" : None, "goal" : None, "real" : None}

    # 요일을 정수로 얻기 (월요일=0, 일요일=6)
    weekday_number = date.weekday()
    group_info = group_crud.get_group_by_date_track_id_in_part(db, user_id=current_user.id, date=date, track_id=mealday.track_id)
    if group_info is None:
        raise HTTPException(status_code=404, detail="Group not found")
    group, cheating_count, user_id2, flag, finish_date =group_info
    dday = (date - group.start_day).days + 1
    ## 트랙id를 가지고 있는 트랙루틴 전체 조회
    trackroutines = track_routine_crud.get_track_routine_by_track_id(db, track_id=mealday.track_id)
    goal_time=[]
    for trackroutine in trackroutines:
        trackroutinedates = track_routine_crud.get_trackroutinedate_all_by_routine_id_weekday_date(db, routine_id=trackroutine.id,
                                                                                                   weekday=weekday_number,
                                                                                                   date=dday)
        for trackroutinedate in trackroutinedates:
            info = {"time": trackroutinedate.time, "title":trackroutine.title}
            goal_time.append(info)

    meal_info = meal_hour_crud.get_User_Meal_all_name_time(db,user_id=current_user.id,daymeal_id=mealday.id)
    return {"dday" : dday, "goal" : goal_time, "real" : meal_info}

@router.get("/get/calorie_today/{daytime}", response_model=meal_day_schema.MealDay_today_calorie_schema)
def get_MealDay_calorie_today(daytime: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    금일 칼로리, 목표칼로리 조회, 섭취칼로리, 소모칼로리, 몸무게 조회
     - 입력예시 : 2024-06-01
     - 출력 : todaycalorie(nowcalorie - burncalorie), MealDay.goalcaloire,
             MealDay.nowcalorie, MealDay.burncalorie. MealDay.weight

    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    #date = (datetime.utcnow() + timedelta(hours=9)).date()
    mealtoday = meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)
    if mealtoday is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    todaycalorie = mealtoday.nowcalorie - mealtoday.burncalorie
    goalcalorie = mealtoday.goalcalorie
    nowcalorie =mealtoday.nowcalorie
    burncalorie=mealtoday.burncalorie
    weight = mealtoday.weight
    return {"todaycalorie" : todaycalorie, "goalcalorie" : goalcalorie, "nowcalorie": nowcalorie, "burncalorie": burncalorie,"weight": weight}

@router.get("/get/mealhour_today/{daytime}", response_model=meal_day_schema.MealDay_today_mealhour_list_schema)
def get_today_Mealhour(daytime: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    금일 식단게시사진(MealHour), 등록시간 전체 조회
     - 입력예시 : daytime = 2024-06-01
     - 출력 : 당일 식단게시글[picture_url, Mealhour.date]
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    meal_today = db.query(MealDay).filter(MealDay.user_id == current_user.id, MealDay.date == date).first()
    if meal_today is None:
        raise HTTPException(status_code=404, detail="Mealday not posting")

    result = []

    meal_hours = meal_hour_crud.get_mealhour_all_by_mealday_id(db, user_id=current_user.id,
                                                               daymeal_id=meal_today.id)
    for meal in meal_hours:
        try:
            # 서명된 URL 생성 (URL은 1시간 동안 유효)
            blob = bucket.blob(meal.picture)
            signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        time_str = meal.date.strftime('%H:%M')

        meal_info = meal_day_schema.MealDay_today_mealhour_schema(
            picture=signed_url,
            date=time_str,
        )
        result.append(meal_info)

    return meal_day_schema.MealDay_today_mealhour_list_schema(mealday=result)

@router.patch("/update/burncaloire/{daytime}/{burncalorie}", status_code=status.HTTP_204_NO_CONTENT)
def update_burncaloire(daytime: str, burncalorie: float, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단일일(MealDay) 소모칼로리 업뎃 :
     - 입력예시 : daytime = 2024-06-01, burncalorie = 15
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealtoday=meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)
    if mealtoday is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")

    meal_day_crud.update_burncalorie(db, mealday=mealtoday, burncalorie=burncalorie)

    return {"detail": "burncalorie updated successfully"}

@router.patch("/update/weight/{daytime}/{weight}", status_code=status.HTTP_204_NO_CONTENT)
def update_weight(daytime: str, weight: float, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단일일(MealDay) 몸무게 업뎃 :
     - 입력예시 : daytime = 2024-06-01,weight = 15.2
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealtoday=meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)
    if mealtoday is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")

    meal_day_crud.update_weight(db, mealday=mealtoday,weight=weight)

    return {"detail": "weight updated successfully"}

@router.get("/get/meal_recording_count/{year}/{month}", response_model=meal_day_schema.MealDay_record_count_schecma)
def get_meal_record_count(year: int, month: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
        특정 월 동안의 식단게시수 조회
        - 입력예시 : year = 2024, month = 6
        - 출력 : 식단기록일 / 해당월의 총 일수
    """
    try:
        # 주어진 월의 첫날과 마지막 날을 구합니다.
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, monthrange(year, month)[1]).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    record_count = 0
    # 해당 월의 모든 날짜에 대해 반복
    date_iter = first_day
    while date_iter <= last_day:
        meal = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date_iter)
        date_iter += timedelta(days=1)
        if meal and meal.nowcalorie > 0.0:
            record_count +=1

    days = (date_iter - first_day).days

    return {"record_count": record_count, "days": days}

@router.get("/get/meal_avg_calorie/{year}/{month}", response_model=meal_day_schema.MealDay_avg_calorie_schecma)
def get_meal_record_count(year: int, month: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db))->float:
    """
        특정 월 동안의 일 평균 칼로리 조회
        - 입력예시 : year = 2024, month = 6
        - 출력 : 식단기록일 / 해당월의 총 일수
    """
    try:
        # 주어진 월의 첫날과 마지막 날을 구합니다.
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, monthrange(year, month)[1]).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    total_calorie = 0
    count = 0
    # 해당 월의 모든 날짜에 대해 반복
    date_iter = first_day
    while date_iter <= last_day:
        meal = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date_iter)
        date_iter += timedelta(days=1)
        if meal and meal.nowcalorie > 0.0:
            count += 1
            total_calorie += meal.nowcalorie
    days = (date_iter - first_day).days
    if count >0:
        avg_calorie = total_calorie/count
    else:
        avg_calorie = 0
    return {"calorie": avg_calorie}

@router.get("/get/goal_now_nutrient/{daytime}", response_model=meal_day_schema.MealDay_today_nutrient_schema)
def get_MealDay_nutrient_today(daytime:str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    금일 탄단지, 목표 탄단지 출력
     - 입력예시 : 없음
     - 출력 : carb,protein,fat, gb_carb, gb_proteinm, gb_carb
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtoday = meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)
    if mealtoday is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return {"carb" : mealtoday.carb, "protein" : mealtoday.protein, "fat": mealtoday.fat,
            "gb_carb": mealtoday.gb_carb,"gb_protein": mealtoday.gb_protein, "gb_fat": mealtoday.gb_fat}


# @router.get("/get/trackroutine_today/{daytime}", response_model=meal_day_schema.MealDay_trackroutine_list_schema)
# def get_trackroutine_daily(daytime: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """
#     트랙루틴 시간대, Title, 트랙지킴여부 조회
#      - 입력예시 : daytime = 2024-06-01
#      - 출력 : 당일 트랙[Trackroutine.time, Trackroutine.title, Mealhour.track_goal]
#     """
#     try:
#         date = datetime.strptime(daytime, '%Y-%m-%d').date()
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid date format")
#
#     result = []
#     mealtoday = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
#     if mealtoday is None:
#         raise HTTPException(status_code=404, detail="MealDay not found")
#     if mealtoday.track_id is None:
#         return meal_day_schema.MealDay_trackroutine_list_schema(mealday=result)
#
#     # 요일을 정수로 얻기 (월요일=0, 일요일=6)
#     weekday_number = date.weekday()
#     # 요일을 한글로 얻기 (월요일=0, 일요일=6)
#     weekday_str = ["월", "화", "수", "목", "금", "토", "일"][weekday_number]
#
#     group_info = group_crud.get_group_by_date_track_id_in_part(db, user_id=current_user.id, date=date,
#                                                                track_id=mealtoday.track_id)
#     if group_info is None:
#         raise HTTPException(status_code=404, detail="Group not found")
#
#     group, cheating_count, user_id2, flag, finish_date = group_info
#     solodate = date - group.start_day
#     days = str(solodate.days + 1)
#
#     combined_results = db.query(TrackRoutine.time, TrackRoutine.title).filter(
#         and_(
#             TrackRoutine.track_id == mealtoday.track_id,
#             or_(
#                 TrackRoutine.week.like(f"%{weekday_str}%"),
#                 TrackRoutine.date.like(f"%{days}%"),
#             )
#         )
#     ).all()
#     if not combined_results:
#         raise HTTPException(status_code=404, detail="No Use TrackRoutine today")
#
#     time_priority = {"아침": 1, "아점": 2, "점심": 3, "점저:":4, "저녁": 5, "야식": 6}
#     # TrackRoutine.time 분리하여 처리
#     for routine in combined_results:
#     # "아침, 점심, 저녁" 같은 문자열을 분리
#         times = routine.time.split(", ")
#
#         for time in times:
#             # MealHour에서 track_goal 값 가져오기
#             track_goal = db.query(MealHour.track_goal).filter(
#                 MealHour.user_id == current_user.id,
#                 MealHour.time.like(f"%{time}%"),  # 해당 시간대에 맞는 MealHour 검색
#                 MealHour.daymeal_id == mealtoday.id
#             ).scalar()
#             if track_goal is None:
#                 track_goal = False
#             # 결과 리스트에 추가
#             result.append(meal_day_schema.MealDay_trackroutine_schema(
#                 time=time,  # 분리된 각 시간대
#                 title=routine.title,
#                 track_yn=track_goal  # 트랙 지킴 여부
#             ))
#     result_sorted = sorted(result, key=lambda x: time_priority.get(x.time, 99))
#
#     return meal_day_schema.MealDay_trackroutine_list_schema(mealday=result_sorted)

