from datetime import datetime, timedelta
from domain.suggestion.suggestion_schema import SuggestionTitleSchema
from models import Suggestion
from sqlalchemy.orm import Session
from fastapi import HTTPException


def get_Suggestion_content(db: Session, id: int):
    suggestions = db.query(Suggestion.title, Suggestion.content).filter(
        Suggestion.id == id
    ).first()
    return suggestions


def get_Suggestion_title_all(db: Session, user_id: int):
    suggestions = db.query(Suggestion.id, Suggestion.title).filter(
        Suggestion.user_id == user_id
    ).all()
    return [SuggestionTitleSchema(id=suggest.id, title=suggest.title) for suggest in suggestions]


def get_suggest(db: Session, id: int):
    suggest = db.query(Suggestion).filter(Suggestion.id == id).first()
    return suggest

def delete_suggest(db: Session, suggest: Suggestion):
    db.delete(suggest)
    db.commit()

def update_suggest(db: Session, suggest: Suggestion, title: str, content: str):
    suggest.title = title
    suggest.content = content
    db.commit()
    return suggest

def post_suggest(db:Session, user_id: int, title: str, content: str):
    new_suggest = Suggestion(
        user_id=user_id,
        title=title,
        content=content,
        date=datetime.utcnow() + timedelta(hours=9)
    )
    db.add(new_suggest)
    db.commit()
    return new_suggest