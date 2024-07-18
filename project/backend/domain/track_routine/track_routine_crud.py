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


def get_routine_by_routine_id(db: Session, routine_id: int):
    return db.query(TrackRoutine).filter(TrackRoutine.id==routine_id).first()

#############################################


def get_track_routine_by_track_id(db: Session, track_id:int):
    trackroutines = db.query(TrackRoutine).filter(
        TrackRoutine.track_id==track_id
    ).all()
    return trackroutines

def get_trackRoutine_days(db: Session, user_id: int, track_id: int, start_day:date,finish_day:date):


    return


def update_routine(_routine_id: int, _routine: track_routine_schema.TrackRoutineCreate, db: Session):
    db_routine = db.query(TrackRoutine).filter(TrackRoutine.id==_routine_id).first()
    db_routine.time = _routine.time
    db_routine.title = _routine.title
    db_routine.calorie = _routine.calorie
    db_routine.food = _routine.food
    db_routine.week = _routine.week
    db_routine.repeat = _routine.repeat
    db.commit()
    db.refresh(db_routine)

