from datetime import date
from domain.track_routine import track_routine_schema
from models import TrackRoutine
from sqlalchemy.orm import Session
from fastapi import HTTPException

def get_TrackRoutine_by_track_id(db: Session, track_id:int):
    trackroutines = db.query(TrackRoutine).filter(
        TrackRoutine.track_id==track_id
    ).first()
    return trackroutines

#def get_Suggestion_title_all(db: Session, user_id: int):
 #   suggestions = db.query(suggestion.id,suggestion.title).filter(
 #       suggestion.user_id == user_id
 #  ).all()
 #   return [Suggestion_title_schema(id=suggest.id, title=suggest.title) for suggest in suggestions]


def create(db: Session, track_id: int,
           routine_create: track_routine_schema.TrackRoutineCreate):
    db_routine = TrackRoutine(
        track_id=track_id,
        time=routine_create.time,
        title=routine_create.title,
        calorie=routine_create.calorie,
        food=routine_create.food,
        week=routine_create.week,
        repeat=routine_create.repeat,
    )
    db.add(db_routine)
    db.commit()
    db.refresh(db_routine)
    return db_routine


def delete_all(db, track_id):
    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id==track_id).all()
    for routine in routines:
        db.delete(routine)
        db.commit()
        db.refresh(routine)

#############################################

def get_TrackRoutine_bytrack_id(db: Session, track_id:int):
    trackroutines = db.query(TrackRoutine).filter(
        TrackRoutine.track_id==track_id
    ).all()
    return trackroutines

def get_trackRoutine_days(db: Session, user_id: int, track_id: int, start_day:date,finish_day:date):


    return