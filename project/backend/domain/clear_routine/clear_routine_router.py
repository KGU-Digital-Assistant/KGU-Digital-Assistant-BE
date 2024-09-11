import datetime
from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from rich import status
from sqlalchemy.orm import Session
from database import get_db
from domain.clear_routine import clear_routine_crud, clear_routine_schema
from domain.group import group_crud
from domain.track import track_crud
from domain.track_routine import track_routine_crud, track_routine_schema
from domain.user.user_router import get_current_user

from models import User, TrackRoutine

router = APIRouter(
    prefix="/clear/routine",
)


@router.post("/checking/{routine_date_id}", response_model=clear_routine_schema.ClearRoutineSchema)
def clear_routine(routine_date_id: int,
                  current_user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """
    홈화면 page2: routine 체크
    - 체크할 경우 : 테이블 생성 or status = true
    - 체크 해제 할 경우 : status = false
    """
    routine_date = track_routine_crud.get_routine_date_by_id(routine_date_id, db)
    if routine_date is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found"
        )
    routine = track_routine_crud.get_routine_by_routine_id(db, routine_date.routine_id)
    if routine is None:
        raise HTTPException(
            status_code=404,
            detail="Routine not found",
        )
    res = clear_routine_crud.create_clear_routine(db, routine, routine_date, current_user)
    return res


@router.get("/get_week", response_model=List[float])
def get_routine_week(cur_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    ### 홈화면 page1 : 3번 부분
    - 모든 날의 루틴 수행 퍼센테이지를 반환
    - 이날 아예 루틴이 없을 경우 -> -1
    """
    group = group_crud.get_group_by_id(db, cur_user.cur_group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    track = track_crud.get_track_by_id(db=db, track_id=group.track_id)

    routines_rate = clear_routine_crud.get_routine_all_by_group_id(group_id=group.id, track_id=track.id, user_id=cur_user.id, db=db)
    if routines_rate is None:
        raise HTTPException(status_code=404, detail="Routine not found")
    return routines_rate


@router.get("/success/routine/{date}", response_model=List[clear_routine_schema.ClearRoutineResponse])
def get_routine_success(date: datetime.date,
                        cur_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """
    특정 날짜의 [루틴 + 성공한 루틴들] 리스트 (ex) 홈화면 3page 7번
    - date : 2024-09-21
    - weekday : 0 ~ 6, 월요일 ~ 일요일
    """
    routines = clear_routine_crud.get_routines_by_date(db, date, cur_user)
    return routines


@router.get("/calendar/{year}/{month}")
def get_routine_calendar(year: int,
                         month: int,
                         cur_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    ### 3page 4번 달력에 나타내기
    ### 3page 3번에 수행 루틴 횟수(success_cnt) / 전체 루틴 횟수(all_cnt)

    - 0 : 루틴 하나도 안함
    - 1 : 루틴 한개 이상
    - 2 : 루틴 모두 함
    """
    calendar, success_cnt, all_cnt = clear_routine_crud.get_calendar(db, year, month, cur_user)
    return {"calendar": calendar, "success_cnt": success_cnt, "all_cnt": all_cnt}


@router.post("/create")
def create_clear_routine(current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    해당 날짜 되면 오늘의 루틴을 다 담을거임
    """
    group = group_crud.get_group_by_id(db, current_user.cur_group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    track = track_crud.get_track_by_id(db=db, track_id=group.track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found")

    count = clear_routine_crud.create_clear_routine_init(db, track, current_user, group)
    return {"count": count}


@router.get("/calendar/date")
def get_routine_calendar(_date: datetime.date,
                         cur_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    ### 홈화면 1page 5번에 몇일 차인지
    - date : 2024-09-21
    - response: 트랙이름, 몇일차
    """
    clear_routine = clear_routine_crud.get_clear_routine_by_date(db, _date, cur_user)
    if clear_routine is None:
        raise HTTPException(status_code=404, detail="Clear routine not found")
    group = group_crud.get_group_by_id(db, clear_routine.group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    track = track_crud.get_track_by_id(db=db, track_id=group.track_id)
    day = (group.start_day - _date).days + 1
    return {"track_name": track.name, "day": day}


