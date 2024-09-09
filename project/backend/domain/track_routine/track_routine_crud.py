from calendar import calendar
from datetime import date, datetime, timedelta, time
from typing import List, Any, Type

from rich import status

from domain.track_routine import track_routine_schema
from domain.group import group_crud
from models import TrackRoutine, User, MealHour, Group, Track, TrackRoutineDate, MealTime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException


def get_trackRoutine_by_track_id(db: Session, track_id: int):
    trackroutines = db.query(TrackRoutine).filter(
        TrackRoutine.track_id == track_id
    ).first()
    return trackroutines


# def get_Suggestion_title_all(db: Session, user_id: int):
#    suggestions = db.query(suggestion.id,suggestion.title).filter(
#        suggestion.user_id == user_id
#   ).all()
#    return [Suggestion_title_schema(id=suggest.id, title=suggest.title) for suggest in suggestions]


def create(db: Session, track_id: int,
           routine_create: track_routine_schema.TrackRoutineCreate):
    db_routine = TrackRoutine(
        track_id=track_id,
        time=routine_create.time,
        title=routine_create.title,
        calorie=routine_create.calorie,
        week=routine_create.week,
        repeat=routine_create.repeat,
        date=routine_create.date,
    )
    db.add(db_routine)
    db.commit()
    db.refresh(db_routine)
    return db_routine


def delete_all(db, track_id):
    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track_id).all()
    for routine in routines:
        routines_date = db.query(TrackRoutineDate).fillter(TrackRoutineDate.routine_id == routine.id).all()
        for routine_date in routines_date:
            db.delete(routine_date)
            db.commit()
        db.delete(routine)
        db.commit()
        # db.refresh(routine)


def get_routine_by_routine_id(db: Session, routine_id: int):
    return db.query(TrackRoutine).filter(TrackRoutine.id == routine_id).first()


#############################################


def get_track_routine_by_track_id(db: Session, track_id: int):
    track_routines = db.query(TrackRoutine).filter(
        TrackRoutine.track_id == track_id
    ).all()

    return track_routines


def get_goal_caloire_bydate_using_trackroutine(db: Session, days: int, track_id: int, date: date) -> float:
    # 요일을 정수로 얻기 (월요일=0, 일요일=6)
    weekday_number = date.weekday()
    # 요일을 한글로 얻기 (월요일=0, 일요일=6)
    weekday_str = ["월", "화", "수", "목", "금", "토", "일"][weekday_number]
    days_str = str(days) + ','

    # 요일과 날짜에 맞는 트랙 루틴 조회
    results = db.query(TrackRoutine).filter(
        and_(
            TrackRoutine.track_id == track_id,
            or_(
                TrackRoutine.week.like(f"%{weekday_str}%"),
                TrackRoutine.date.like(f"%{days_str}%"),
            )
        )
    ).all()

    calorie = 0.0
    if not results:
        return calorie

    for result in results:
        # 쉼표의 개수만큼 칼로리를 곱하도록 수정
        count_time = result.time.count(',') + 1 if result.time else 1
        calorie += (count_time * result.calorie)
        calorie -= result.calorie

    return calorie


def get_calorie_average(track_id: int, db: Session):
    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track_id).all()
    sum = 0
    for routine in routines:
        sum += routine.calorie


def update_routine(_routine_id: int, _routine: track_routine_schema.TrackRoutineCreate, db: Session):
    db_routine = db.query(TrackRoutine).filter(TrackRoutine.id == _routine_id).first()
    db_routine.time = _routine.time
    db_routine.title = _routine.title
    db_routine.calorie = _routine.calorie
    db_routine.week = _routine.week
    db_routine.date = _routine.date
    db_routine.repeat = _routine.repeat
    db.commit()
    db.refresh(db_routine)


def get_calorie_average(track_id: int, db: Session):
    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track_id).all()

    sum = 0
    for routine in routines:
        sum += routine.calorie

    if sum == 0:
        return 0
    return sum / len(routines)


def get_routine_all_by_track_id(track_id: int, db: Session):
    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track_id).all()
    return routines


def get_routine_clear_rate(current_user: User,
                           track_id: int,
                           group: Group,
                           db: Session):
    start_date = group.start_day
    today = date.today()

    track = db.query(Track).filter(Track.id == track_id).first()
    if track is None:
        return None
    meal_hours = db.query(MealHour).filter(MealHour.user_id == current_user.id,
                                           MealHour.date >= start_date,
                                           MealHour.date <= today
                                           ).all()
    routines = []
    success_routines = []
    ans = []
    for i in range(0, track.duration):
        routines.append(0)
        success_routines.append(0)
        ans.append(0)

    for meal_hour in meal_hours:
        diff = meal_hour.date.date() - start_date
        if meal_hour.track_goal:
            success_routines[diff] += 1
        else:
            routines[diff] += 1

    cnt = 0
    for i in range(0, track.duration):
        if success_routines[i] == 0 or routines[i] == 0:
            ans[i] = 0
        else:
            ans[i] = success_routines[i] / success_routines[i] + routines[i] * 100
        cnt += success_routines[i]
    return ans, cnt


def get_routine_clear_routines(current_user: User, year: int, month: int, db: Session):
    start_date = datetime(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = datetime(year, month, last_day)

    meal_hours = [db.query(MealHour).filter(
        MealHour.user_id == current_user.id,
        MealHour.date >= start_date,
        MealHour.date <= end_date,
        MealHour.track_goal == True,
    ).all()]

    return meal_hours.count()


# --------------- 240906 새로운 루틴 버젼 --------------------------

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


# def create_routines(track: Track, track_routine: track_routine_schema.TrackRoutine, db: Session):
#     db_routine = TrackRoutine(
#         track_id=track.id,
#         title=track_routine.title,
#         calorie=track_routine.calorie,
#     )
#     db.add(db_routine)
#     db.commit()
#
#     for weekday in track_routine.weekdays:
#         day = (track_routine.week - 1) * 7 + weekday + 1  # 몇일 차인지
#         time = time_parse(track_routine.time)
#         db_routine_date = TrackRoutineDate(
#             routine_id=db_routine.id,
#             date=day,
#             time=time,
#             weekday=weekday,
#         )
#         db.add(db_routine_date)
#         db.commit()


def create_routine(db: Session, track_id: int):
    db_routine = TrackRoutine(
        track_id=track_id,
    )
    db.add(db_routine)
    db.commit()
    return db_routine


def weekday_parse(weekday: str):
    weekday = weekday[0]
    if weekday == "월":
        return 0
    if weekday == "화":
        return 1
    if weekday == "수":
        return 2
    if weekday == "목":
        return 3
    if weekday == "금":
        return 4
    if weekday == "토":
        return 5
    if weekday == "일":
        return 6


def init_routine_date(week: int, weekday: str, routine_id: int, db: Session):
    weekday_int = weekday_parse(weekday)
    day = (week - 1) * 7 + weekday_int + 1

    db_routine_date = TrackRoutineDate(
        routine_id=routine_id,
        weekday=weekday_int,
        date=day,
    )
    db.add(db_routine_date)
    db.commit()
    return db_routine_date


def update_title(db: Session, routine_id: int, title: str):
    db_routine = db.query(TrackRoutineDate).filter(TrackRoutineDate.routine_id == routine_id).first()
    db_routine.title = title
    db.commit()
    return db_routine


def update_weekday(db: Session, routine_id: int, weekday: str):
    """
    요일 바꿈 -> 몇일차인지도 바뀜
    """
    weekday_int = weekday_parse(weekday)
    db_routine = db.query(TrackRoutineDate).filter(TrackRoutineDate.routine_id == routine_id).first()
    day = db_routine.date // 7
    day = day * 7 + weekday_int + 1
    db_routine.weekday = weekday_int
    db_routine.date = day
    db.commit()
    return db_routine


def update_calorie(db: Session, routine_id: int, calorie: int):
    db_routine = db.query(TrackRoutine).filter(TrackRoutine.id == routine_id).first()
    db_routine.calorie = calorie
    db.commit()


def create_track_routine_repeat(routine_id: int, user: User, db: Session) -> list[track_routine_schema.TrackRoutineDateSchema]:
    routine = db.query(TrackRoutine).filter(TrackRoutine.id == routine_id).first()
    routine_date = db.query(TrackRoutineDate).filter(TrackRoutineDate.routine_id == routine_id).first()
    track = db.query(Track).filter(Track.id == routine.track_id).first()
    routines = []
    for i in range(routine_date.date + 7, track.duration + 1, 7):
        db_routine_date = TrackRoutineDate(
            routine_id=routine_id,
            date=i,
            time=routine_date.time,
            weekday=routine_date.weekday,
            clock=routine_date.clock
        )
        db.add(db_routine_date)
        db.commit()
        routines.append(track_routine_schema.TrackRoutineDateSchema.from_orm(db_routine_date))


    return routines


def update_clock(db: Session, routine_date_id: int, hour: int, minute: int):
    db_routine_date = db.query(TrackRoutineDate).filter(TrackRoutineDate.id == routine_date_id).first()
    my_time = time(hour, minute)

    db_routine_date.clock = my_time
    db.commit()
    return db_routine_date


def delete_routine(db: Session, routine_id: int):
    routine = db.query(TrackRoutine).filter(TrackRoutine.id == routine_id).first()
    routine.delete = True
    db.commit()


def get_routine_list(db: Session, track_id: int, week: int, weekday: int):
    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track_id,
                                             TrackRoutine.delete == False,
                                             ).all()
    day = (week - 1) * 7 + weekday + 1
    routine_date_list = []
    for routine in routines:
        routine_dates = db.query(TrackRoutineDate).filter(
            TrackRoutineDate.routine_id == routine.id,
            TrackRoutineDate.date == day,
        ).all()
        for routine_date in routine_dates:
            res = track_routine_schema.TrackRoutineResponse(
                routine_id=routine.id,
                routine_date_id=routine_date.id,
                title=routine.title,
                week=week,
                weekday=weekday,
                time=routine_date.time,
                calorie=routine.calorie,
                clock=routine_date.clock
            )
            routine_date_list.append(res)

    sorted_data = sorted(
        routine_date_list,
        key=lambda x: x.clock if x.clock is not None else time.min  # time 객체를 비교
    )
    # sorted_data = sorted(routine_date_list, key=lambda x: datetime.strptime(x.clock, "%H:%M:%S").time())

    return sorted_data

def get_routine_date_by_id(routine_date_id: int, db: Session):
    return db.query(TrackRoutineDate).filter(TrackRoutineDate.id == routine_date_id).first()


def update_meal_time(meal_time: int, routine_date_id: int, db: Session):
    routine_date = db.query(TrackRoutineDate).filter(TrackRoutineDate.id == routine_date_id).first()
    routine_date.time = meal_time
    db.commit()
    return routine_date.time


def delete_routine_date(id: int, db: Session):
    db_routine_date = db.query(TrackRoutineDate).filter(TrackRoutineDate.id == id).first()
    db.delete(db_routine_date)
    db.commit()
