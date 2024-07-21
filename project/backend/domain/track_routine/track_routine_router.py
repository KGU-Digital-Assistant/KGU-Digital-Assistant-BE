
from fastapi import APIRouter, Form,Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database import get_db
from typing import List

from domain.track_routine.track_routine_schema import TrackRoutineSchema
from models import TrackRoutine
from domain.track_routine import track_routine_schema, track_routine_crud
from domain.track import track_crud
from domain.meal_day import meal_day_crud
from domain.group import group_crud
from datetime import datetime
from starlette import status

router=APIRouter(
    prefix="/track/routine"
)

@router.get("/get/{track_id}", response_model=track_routine_schema.TrackRoutineSchema)
def get_TrackRoutine_track_id(track_id: int, db: Session = Depends(get_db)):
    track_routines = track_routine_crud.get_TrackRoutine_by_track_id(db,track_id=track_id)
    if track_routines is None:
        raise HTTPException(status_code=404, detail="track_routine not found")
    return track_routines


@router.post("/create/{track_id}", status_code=status.HTTP_201_CREATED)
def create_TrackRoutine(track_id: int,
                        routineCreate: track_routine_schema.TrackRoutineCreate,
                        db: Session = Depends(get_db)):
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track does not exist")

    routine = track_routine_crud.create(db, track_id, routineCreate)
    return {"routine": routine}


@router.delete("/delete/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_TrackRoutine(track_id: int, db: Session = Depends(get_db)):
    """
    트랙 생성 중에 뒤로가기 눌렀을 때, 만든 루틴 다 삭제
    """
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track does not exist")

    track_routine_crud.delete_all(db, track_id)


@router.patch("/update/{routine_id}")
def update_track_routine(routine_id: int,
                         _routine: track_routine_schema.TrackRoutineCreate,
                         db: Session = Depends(get_db)):
    routine = track_routine_crud.get_routine_by_routine_id(db=db, routine_id=routine_id)
    if routine is None:
        raise HTTPException(status_code=404, detail="Routine does not exist")
    track_routine_crud.update_routine(_routine=_routine, _routine_id=routine_id, db=db)

    return {"status": "ok"}


@router.get("/get/{routine_id}", response_model=TrackRoutineSchema)
def get_track_routine(routine_id: int, db: Session = Depends(get_db)):
    """
    routine 하나 반환
    """
    routine = track_routine_crud.get_routine_by_routine_id(db=db, routine_id=routine_id)
    if routine is None:
        raise HTTPException(status_code=404, detail="Routine does not exist")
    return routine


####################################################


@router.get("/get/{track_id}", response_model=List[track_routine_schema.TrackRoutineSchema])
def get_TrackRoutine_track_id_all(track_id: int, db: Session = Depends(get_db)):
    trackroutines = track_routine_crud.get_track_routine_by_track_id(db, track_id=track_id)
    if trackroutines is None:
        raise HTTPException(status_code=404, detail="TrackRoutine not found")
    return [trackroutines]


@router.get("/get/{user_id}/{time}",response_model=track_routine_schema.TrackRoutine_naemcalorie_schema)
def get_TrackRoutine_track_title_calorie(user_id: int, time: str, db: Session=Depends(get_db)):
    date_part = time[:10]
    time_part = time[11:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtoday= meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    # 요일을 정수로 얻기 (월요일=0, 일요일=6)
    weekday_number = date.weekday()
    weekday_str = ["월", "화", "수", "목", "금", "토", "일"][weekday_number]
    group_info = group_crud.get_Group_bydate(db,date=date_part)
    solodate = group_info.finish_day - date
    days = str(solodate.days)

    if mealtoday.track_id is None:
        return {"detail" : "track not use"}
    trackroutines = db.query(TrackRoutine.title, TrackRoutine.calorie).filter(and_(TrackRoutine.track_id==mealtoday.track_id,
                                                                              TrackRoutine.time.like(f"{time_part}"),
                                                                                or_(TrackRoutine.week.like(f"{weekday_str}"),
                                                                                    TrackRoutine.date.like(f"{days}")
                                                                       ))).first()
    return trackroutines


@router.get("/get/avg-calorie/{track_id}")
def get_avg_calorie(track_id: int, db: Session = Depends(get_db)):
    """
    목표 일일 칼로리 -> 모든 루틴 칼로리의 합 / 루틴 일 수
    """
    return track_routine_crud.get_calorie_average(track_id=track_id, db=db)
