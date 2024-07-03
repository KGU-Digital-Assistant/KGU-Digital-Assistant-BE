
from fastapi import APIRouter, Form,Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from models import TrackRoutine
from domain.TrackRoutine import TrackRoutine_schema,TrackRoutine_crud
from datetime import datetime
from starlette import status

router=APIRouter(
    prefix="/TrackRoutine"
)

@router.get("/get/{track_id}", response_model=TrackRoutine_schema.TrackRoutine_schema)
def get_TrackRoutine_track_id(track_id: int, db: Session = Depends(get_db)):
    trackroutines = TrackRoutine_crud.get_TrackRoutine_bytrack_id(db,track_id=track_id)
    if trackroutines is None:
        raise HTTPException(status_code=404, detail="TrackRoutine not found")
    return trackroutines

