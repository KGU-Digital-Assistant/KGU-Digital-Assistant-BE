
from fastapi import APIRouter, Form,Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.sql.functions import current_user

from database import get_db
from typing import List

from domain.track_routine.track_routine_schema import TrackRoutineSchema
from models import TrackRoutine, User, TrackRoutineDate
from domain.track_routine import track_routine_schema, track_routine_crud
from domain.track import track_crud
from domain.user.user_router import get_current_user
from domain.meal_day import meal_day_crud
from domain.group import group_crud
from datetime import datetime
from starlette import status

router=APIRouter(
    prefix="/track/routine"
)


@router.post("/create/{track_id}")
def create_track_routine(track_id: int, week: int, weekday: str,
                         _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    | 2024-09-28 수정
    # 트랙 루틴 생성 하기
    - (+)버튼 눌렀을 때 api 임.
    - week 몇주차인지
    - weekday 몇요일인지 (ex: 월, 화, 수, ... )
    """
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track does not exist")
    if track.user_id != _current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="권한 없음")

    routine = track_routine_crud.create_routine(db, track_id)
    routine_date = track_routine_crud.init_routine_date(week, weekday, routine.id, db)
    return {"routine_id": routine.id, "routine_date_id": routine_date.id}


def valid_routine_when_update(routine_id: int, user_id, db: Session):
    routine = track_routine_crud.get_routine_by_routine_id(db, routine_id)
    if routine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine does not exist")
    track = track_crud.get_track_by_id(db, routine.track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track does not exist")
    if track.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="권한 없음")


@router.post("/create/next/{routine_date_id}")
def create_next_routine(routine_date_id: int,
                        track_routine: track_routine_schema.TrackRoutineCreateNext,
                        _current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """
    # 루틴 만들기
    - 순서: /track/routine/create/{trakc_id} -> /track/routine/next/{routine_date_id}
    - weekday : 월, 화, 수, ...
    - time: 아침, 점심, 아점, ....
    """
    routine_date = track_routine_crud.get_routine_date_by_id(routine_date_id, db)
    if routine_date is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine does not exist")

    valid_routine_when_update(routine_date.routine_id, _current_user.id, db)
    rou_date, rou = track_routine_crud.update_routine_and_date(routine_date.id, track_routine, db)
    return {"state": "ok"}


@router.patch("/title/{routine_id}")
def create_track_routine(routine_id: int, title: str,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    title 바꾸기
    """
    valid_routine_when_update(routine_id, current_user.id, db)
    return track_routine_crud.update_title(db, routine_id, title)


@router.patch("/weekday/{routine_id}")
def create_track_routine(routine_id: int, weekday: str,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    요일 바꾸기
    """
    valid_routine_when_update(routine_id, current_user.id, db)

    return track_routine_crud.update_weekday(db, routine_id, weekday)


@router.patch("/weekday/{routine_id}")
def create_track_routine(routine_id: int, calorie: int,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    목표 칼로리 바꾸기
    """
    valid_routine_when_update(routine_id, current_user.id, db)
    return track_routine_crud.update_calorie(db, routine_id, calorie)


@router.post("/repeat/{routine_id}")
def create_routine_repeat(routine_id: int,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    """
    ### 이 루틴 반복 설정하기
    - 1주차, 월요일에 반복설정 -> 2, 3, 4, .. 주차 적용
    - 2주차, 월요일에 반복설정 -> 3, 4, 5, .. 주차 적용
    """
    valid_routine_when_update(routine_id, current_user.id, db)
    routines = track_routine_crud.create_track_routine_repeat(routine_id, current_user, db)
    return {"routines": routines}


@router.patch("/mealtime/{routine_date_id}")
def update_routine_mealtime(routine_date_id: int, _meal_time: str,
                            current_user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    """
    ### 아침, 점심, 저녁 등 MealTime 바꾸기
    """
    meal_time = track_routine_crud.time_parse(_meal_time)
    routine_date = track_routine_crud.get_routine_date_by_id(routine_date_id, db)
    valid_routine_when_update(routine_date.id, current_user.id, db)
    res = track_routine_crud.update_meal_time(meal_time, routine_date.id, db)
    return {"routine_date_time": res}


@router.patch("/clock/{routine_date_id}")
def update_routine_clock(routine_date_id: int, hour: int, minute: int,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    ### 시간 설정 하기
    """
    try:
        routine_date = track_routine_crud.get_routine_date_by_id(routine_date_id, db)
        valid_routine_when_update(routine_date.routine_id, current_user.id, db)
        return track_routine_crud.update_clock(db, routine_date_id, hour, minute)
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fail time set")


@router.delete("/delete/{routine_id}")
def delete_track_routine(routine_id: int,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    ### 반복 루틴 모두 지우기
    - 논리적 삭제만 진행함
    """
    valid_routine_when_update(routine_id, current_user.id, db)
    track_routine_crud.delete_routine(db, routine_id)


@router.delete("/delete/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_TrackRoutine(track_id: int,
                        current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """
    트랙 생성 중에 `저장하기` 안누르고 뒤로가기 눌렀을 때, 만든 루틴과 트랙 다 삭제
    """
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track does not exist")

    if track.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="권한 없음")

    track_routine_crud.delete_all(db, track_id)
    track_crud.delete_track(db, track_id)


@router.delete("/delete/{routine_date_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_RoutineRoutine(routine_date_id: int,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    """
    ## TrackRoutineDate 삭제하기
    """
    routine_date = track_routine_crud.get_routine_date_by_id(routine_date_id, db)
    valid_routine_when_update(routine_date.routine_id, current_user.id, db)
    track_routine_crud.delete_routine_date(routine_date.id, db)
    return {"status": "ok"}


@router.get("/list/{track_id}")
def get_track_routine(track_id: int, week: int, weekday: str,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """
        트랙 상세보기에서 `몇주차`이고 `몇요일`인지 클릭하면 루틴이 뜸
        | EX) 홈화면 2page 1번
        - week: 1, 2 ..
        - weekday: 월, 화, 수 ..
    """
    # group_crud.is_join_track(db, track_id, current_user.id)
    # 트랙할 때 따로 트랙 복제 예정..
    return track_routine_crud.get_routine_list(db, track_id, week,
                                               track_routine_crud.weekday_parse(weekday))


@router.get("/routine_date/{routine_date_id}")
def get_routine_date(routine_date_id: int,
                     current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """
    routine date랑 routine 가져오기
    """
    routine_date = track_routine_crud.get_routine_date_by_id(routine_date_id, db)
    if routine_date is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine does not exist")
    routine = track_routine_crud.get_routine_by_routine_id(db, routine_date.routine_id)
    return {"routine": routine, "routine_date": routine_date}

# ------------------ 위에껀 새로 만든 거 --------------------------

@router.get("/get/{track_id}", response_model=track_routine_schema.TrackRoutineSchema)
def get_TrackRoutine_track_id(track_id: int, db: Session = Depends(get_db)):
    track_routines = track_routine_crud.get_trackRoutine_by_track_id(db, track_id=track_id)
    if track_routines is None:
        raise HTTPException(status_code=404, detail="track_routine not found")
    return track_routines


# @router.patch("/update/{routine_id}")
# def update_track_routine(routine_id: int,
#                          _routine: track_routine_schema.TrackRoutineCreate,
#                          db: Session = Depends(get_db)):
#     routine = track_routine_crud.get_routine_by_routine_id(db=db, routine_id=routine_id)
#     if routine is None:
#         raise HTTPException(status_code=404, detail="Routine does not exist")
#     track_routine_crud.update_routine(_routine=_routine, _routine_id=routine_id, db=db)
#
#     return {"status": "ok"}


@router.get("/get/{routine_id}", response_model=track_routine_schema.TrackRoutineSchema)
def get_track_routine(routine_id: int, db: Session = Depends(get_db)):
    """
    routine 하나 반환
    """
    routine = track_routine_crud.get_routine_by_routine_id(db=db, routine_id=routine_id)
    if routine is None:
        raise HTTPException(status_code=404, detail="Routine does not exist")
    return routine


####################################################


# @router.get("/get/{track_id}", response_model=List[track_routine_schema.TrackRoutineSchema])
# def get_TrackRoutine_track_id_all(track_id: int, db: Session = Depends(get_db)):
#     """
#     해당 트랙의 루틴 전체 반환
#     """
#     trackroutines = track_routine_crud.get_track_routine_by_track_id(db, track_id=track_id)
#     if trackroutines is None:
#         raise HTTPException(status_code=404, detail="TrackRoutine not found")
#     return [trackroutines]
#
@router.get("/get/{time}/title_calorie/mine", response_model=List[track_routine_schema.TrackRoutine_namecalorie_schema])
def get_TrackRoutine_track_title_calorie_user(time: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    해당일 시간대에 Track 사용시 먹어야할 음식title, caloire 조회 : 9page 7-2번
     - 입력예시 : user_id = 1, time = 2024-06-01오후간식
     - 출력 : [TrackRoutine.title, TrackRouint.calorie]
    """
    date_part = time[:10]
    time_part = time[11:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = track_routine_crud.time_parse(time_part)

    mealtoday = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
    if mealtoday is None:
        raise HTTPException(status_code=404, detail="MealDay not found")
    if mealtoday.track_id is None:
        return [{"title": None, "calorie": None}]

    # 요일을 정수로 얻기 (월요일=0, 일요일=6)
    weekday_number = date.weekday()

    group_info = group_crud.get_group_by_date_track_id_in_part(db, user_id=current_user.id, date=date, track_id=mealtoday.track_id)
    if group_info is None:
        raise HTTPException(status_code=404, detail="Group not found")

    group, cheating_count, user_id2, flag, finish_date =group_info
    days = date - group.start_day

    combine_result=[]
    trackroutines = db.query(TrackRoutine).filter(
            TrackRoutine.track_id == mealtoday.track_id
    ).all()

    if not trackroutines:
        raise HTTPException(status_code=404, detail="No Use TrackRoutine today")
    for trackroutine in trackroutines:
        trackroutinedates = db.query(TrackRoutineDate).filter(
            and_(TrackRoutineDate.routine_id==trackroutine.id,
                 TrackRoutineDate.weekday==weekday_number,
                 TrackRoutineDate.date==days)
        ).all()
        for trackroutinedate in trackroutinedates:
            result = {"title":trackroutine.title,"calorie":trackroutine.calorie}
            combine_result.append(result)

    return combine_result
#
# @router.get("/get/{user_id}/{time}/title_calorie/formentor", response_model=List[track_routine_schema.TrackRoutine_namecalorie_schema])
# def get_TrackRoutine_track_title_calorie_mentor(user_id: int, time: str, db: Session = Depends(get_db)):
#     """
#     해당일 시간대에 Track 사용시 먹어야할 음식title, caloire 조회 : 16page 6번
#      - 입력예시 : user_id = 1, time = 2024-06-01오후간식
#      - 출력 : [TrackRoutine.title, TrackRouint.calorie]
#     """
#     date_part = time[:10]
#     time_part = time[11:]
#     try:
#         date = datetime.strptime(date_part, '%Y-%m-%d').date()
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid date format")
#
#     mealtoday = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
#     if mealtoday is None:
#         raise HTTPException(status_code=404, detail="MealDay not found")
#     if mealtoday.track_id is None:
#         return [{"title": None, "calorie": None}]
#
#     # 요일을 정수로 얻기 (월요일=0, 일요일=6)
#     weekday_number = date.weekday()
#     # 요일을 한글로 얻기 (월요일=0, 일요일=6)
#     weekday_str = ["월", "화", "수", "목", "금", "토", "일"][weekday_number]
#
#     group_info = group_crud.get_group_by_date_track_id_in_part(db, user_id=user_id, date=date, track_id=mealtoday.track_id)
#     if group_info is None:
#         raise HTTPException(status_code=404, detail="Group not found")
#
#     group, cheating_count, user_id2, flag, finish_date =group_info
#     solodate = date - group.start_day
#     days = str(solodate.days + 1)
#
#     combined_results = db.query(TrackRoutine.title, TrackRoutine.calorie).filter(
#         and_(
#             TrackRoutine.track_id == mealtoday.track_id,
#             TrackRoutine.time.like(f"%{time_part}%"),
#             or_(
#                 TrackRoutine.week.like(f"%{weekday_str}%"),
#                 TrackRoutine.date.like(f"%{days}%"),
#
#             )
#         )
#     ).all()
#
#     if not combined_results:
#         raise HTTPException(status_code=404, detail="No Use TrackRoutine today")
#
#     return [{"title": routine.title, "calorie": routine.calorie} for routine in combined_results]
#
#
# @router.get("/get/avg-calorie/{track_id}")
# def get_avg_calorie(track_id: int, db: Session = Depends(get_db)):
#     """
#     목표 일일 칼로리 -> 모든 루틴 칼로리의 합 / 루틴 일 수
#     """
#     return track_routine_crud.get_calorie_average(track_id=track_id, db=db)
#
#
# @router.get("/clear/rate", response_model=List[float])
# def get_clear_rate(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """
#     홈화면 1page 3번
#     - 일일 지킨 정도를 퍼센트로 나타냄
#     - 인덱스 == 몇일째
#     """
#     group = group_crud.get_group_by_id(db, current_user.cur_group_id)
#     if group is None:
#         raise HTTPException(status_code=404, detail="Group not found")
#     if group.start_day is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="group is not started")
#
#     ans, cnt = track_routine_crud.get_routine_clear_rate(current_user=current_user,
#                                                     track_id=group.track_id, group=group, db=db)
#     if ans is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tarck not found")
#     return ans, cnt
#
#
# @router.get("/clear/routine/count/{year}/{month}", response_model=int)
# def get_clear_routine_count(year: int, month: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """
#     홈화면 3page 4번 : 지킨 루틴 수
#     """
#     cnt = track_routine_crud.get_routine_clear_routines(current_user=current_user, year=year, month=month, db=db)
#     return cnt