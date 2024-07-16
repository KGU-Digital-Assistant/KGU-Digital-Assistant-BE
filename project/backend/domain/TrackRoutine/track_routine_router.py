
from fastapi import APIRouter, Form,Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from models import TrackRoutine
from domain.TrackRoutine import track_routine_schema, track_routine_crud
from domain.track import track_crud
from datetime import datetime
from starlette import status

router=APIRouter(
    prefix="/track/routine"
)

@router.get("/get/{track_id}", response_model=track_routine_schema.TrackRoutine_schema)
def get_TrackRoutine_track_id(track_id: int, db: Session = Depends(get_db)):
    track_routines = track_routine_crud.get_TrackRoutine_by_track_id(db,track_id=track_id)
    if track_routines is None:
        raise HTTPException(status_code=404, detail="TrackRoutine not found")
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