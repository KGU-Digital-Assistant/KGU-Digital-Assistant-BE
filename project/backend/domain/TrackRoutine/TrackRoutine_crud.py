from datetime import datetime
from domain.TrackRoutine import TrackRoutine_schema
from models import TrackRoutine
from sqlalchemy.orm import Session
from fastapi import HTTPException

def get_TrackRoutine_bytrack_id(db: Session, track_id:int):
    trackroutines = db.query(TrackRoutine).filter(
        TrackRoutine.track_id==track_id
    ).first()
    return trackroutines

#def get_Suggestion_title_all(db: Session, user_id: int):
 #   suggestions = db.query(Suggestion.id,Suggestion.title).filter(
 #       Suggestion.user_id == user_id
 #  ).all()
 #   return [Suggestion_title_schema(id=suggest.id, title=suggest.title) for suggest in suggestions]