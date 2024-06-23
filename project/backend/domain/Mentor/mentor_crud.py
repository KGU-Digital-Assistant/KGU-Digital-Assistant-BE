from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from domain.Mentor.mentor_schema import MentorCreate, MentorGym, MenteeSchema
from models import Mentor, User

def create_mentor(mentor_create: MentorCreate, _user_id: int, db: Session):

    db_mentor = Mentor(
        user_id=_user_id,
        gym=mentor_create.gym,
        FA=mentor_create.FA,
        company_id=mentor_create.company_id
    )
    db.add(db_mentor)
    db.commit()

def update_mentor_gym(_user_id: int, mentor_update: MentorGym, db: Session):
    mentor = db.query(Mentor).filter(Mentor.user_id == _user_id).one()
    if mentor:
        db_mentor = Mentor(
            gym=mentor_update.gym,
        )
        db.add(db_mentor)
        db.commit()
    return mentor

def mentor_delete(user_id: int, db: Session):
    mentor = db.query(Mentor).filter(Mentor.user_id == user_id).one()
    if not mentor:
        return False
    db.delete(mentor)
    db.commit()
    return True


def matching_mentor(mentee: User, _mentor_id: int, db: Session):
    mentee.mentor_id = _mentor_id
    db.commit()
    db.refresh(mentee)

    return mentee
