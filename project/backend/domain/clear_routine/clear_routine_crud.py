from datetime import timedelta, date, datetime
from typing import List

from domain.clear_routine import clear_routine_schema
from domain.group.group_schema import GroupCreate, InviteStatus, GroupDate, Respond, GroupStatus
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, insert, update
from domain.meal_day import meal_day_crud
from domain.track_routine import track_routine_crud
from models import Group, Track, Invitation, User, MealDay, Participation, TrackRoutine, ClearRoutine, TrackRoutineDate
from fastapi import HTTPException


def create_clear_routine(db: Session, _routine: TrackRoutine, _routine_date: TrackRoutineDate, user: User):
    clear_routine = db.query(ClearRoutine).filter(ClearRoutine.user_id == user.id,
                                                  ClearRoutine.routine_date_id == _routine_date.id).first()
    if clear_routine:
        clear_routine.status = not clear_routine.status
        db.commit()
        return clear_routine

    meal_day = db.query(MealDay).filter(MealDay.user_id == user.id,
                                        MealDay.date == datetime.today().date()).first()
    db_clear_routine = ClearRoutine(
        user_id=user.id,
        routine_date_id=_routine_date.id,
        group_id=user.cur_group_id,
        date=datetime.today().date(),
        status=True,
    )
    db.add(db_clear_routine)
    db.commit()
    return db_clear_routine

# 근데 이 성공률은 언제 mealday에 추가하는가??
def get_routine_all_by_group_id(group_id: int, track_id: int,
                                user_id: int, db: Session):
    clear_routines = db.query(ClearRoutine).filter(ClearRoutine.user_id == user_id).all()
    group = db.query(Group).filter(Group.id == group_id).first()
    track = db.query(Track).filter(Track.id == track_id).first()

    arr = []
    success_arr = []
    ans = []

    for i in range(0, track.duration):
        arr.append(0)
        success_arr.append(0)

    for clear_routine in clear_routines:
        day_num = (clear_routine.date - group.start_day).days + 1 # 몇일차인지 계산
        arr[day_num] += 1
        if clear_routine.status:
            success_arr[day_num] += 1

    for i in range(0, track.duration):
        if success_arr[i] == 0 and arr[i] == 0:
            ans.append(-1)
        elif success_arr[i] == 0:
            ans.append(0)
        else:
            ans.append(success_arr[i] / arr[i] * 100)

    return ans


def get_routines_by_date(db: Session, date: date, cur_user: User) -> List[clear_routine_schema.ClearRoutineResponse]:
    clear_routines = db.query(ClearRoutine).filter(ClearRoutine.user_id == cur_user.id,
                                                     ClearRoutine.date == date).all()
    routines = []
    for clear_routine in clear_routines:
        rou_date = db.query(TrackRoutineDate).filter(TrackRoutineDate.id == clear_routine.routine_date_id,
                                                ).first()
        rou = db.query(TrackRoutine).filter(TrackRoutine.id == rou_date.routine_id).first()
        schema = clear_routine_schema.ClearRoutineResponse(
            routine_id=clear_routine.routine_date_id,
            routine_date_id=rou_date.id,
            title=rou.title,
            time=rou_date.time,
            calories=rou.calories,
            status=clear_routine.status,
            clock=rou_date.clock,
        )
        routines.append(schema)
    return routines


def create_clear_routine_init(db: Session, track: Track, current_user: User, group: Group):
    today = datetime.today().date()
    days = (today - group.start_day).days + 1
    count = 0
    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track.id,
                                             ).all()

    for routine in routines:
        routine_date = db.query(TrackRoutineDate).filter(
            TrackRoutineDate.routine_id == routine.id,
            TrackRoutineDate.date == days,
        ).first()

        if routine_date is None:
            continue
        db_clear_routine = ClearRoutine(
            user_id=current_user.id,
            routine_date_id=routine_date.id,
            date=datetime.today(),
            status=False,
            group_id=current_user.cur_group_id,
            weekday=routine_date.weekday,
        )
        db.add(db_clear_routine)
        db.commit()
        count += 1
    return count


def get_first_last_day(year, month):
    # 주어진 연도와 월에 대한 첫째 날과 마지막 날을 구함
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    return first_day, last_day


def get_calendar(db: Session, year: int, month: int, cur_user: User):
    first_day, last_day = get_first_last_day(year, month)
    success_cnt = []
    all_cnt = []
    calendar = []
    for day in range(0, last_day.day - first_day.day + 1):
        calendar.append(0)
        success_cnt.append(0)
        all_cnt.append(0)

    clear_routines = db.query(ClearRoutine).filter(ClearRoutine.user_id == cur_user.id,
                                                   ClearRoutine.date >= first_day,
                                                   ClearRoutine.date <= last_day
                                                   ).all()
    for clear_routine in clear_routines:
        index = clear_routine.date.day
        if clear_routine.status:
            success_cnt[index] += 1
        all_cnt[index] += 1

    for i in range(0, last_day.day - first_day.day + 1):
        if success_cnt[i] == 0 and all_cnt[i] == 0:
            calendar[i] = 0
        elif success_cnt[i] == all_cnt[i]:
            calendar[i] = 2
        elif success_cnt[i] > 0:
            calendar[i] = 1
        else:
            calendar[i] = 0

    return calendar, sum(success_cnt), sum(all_cnt)

