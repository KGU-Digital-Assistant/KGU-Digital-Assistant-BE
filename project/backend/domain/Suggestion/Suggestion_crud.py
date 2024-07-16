from datetime import datetime
from domain.Suggestion.Suggestion_schema import Suggestion_title_schema
from models import Suggestion
from sqlalchemy.orm import Session
from fastapi import HTTPException

def get_Suggestion_content(db: Session, id:int):
    suggestions = db.query(Suggestion.title, Suggestion.content).filter(
        Suggestion.id == id
    ).first()
    return suggestions

def get_Suggestion_title_all(db: Session, user_id: int):
    suggestions = db.query(Suggestion.id,Suggestion.title).filter(
        Suggestion.user_id == user_id
    ).all()
    return [Suggestion_title_schema(id=suggest.id, title=suggest.title) for suggest in suggestions]