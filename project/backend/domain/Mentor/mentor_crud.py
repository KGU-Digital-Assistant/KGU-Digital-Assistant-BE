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

########################
def get_Mentor(db: Session, user_id:int):
    Mentors=db.query(Mentor).filter(Mentor.user_id == user_id).first()
    return Mentors

def get_Users_name_rank_byMentor(db: Session, user_id:int):
    Mentors=get_Mentor(db,user_id=user_id)
    if not Mentors:
        raise HTTPException(status_code=404,detail="Mentor not found")
    Users=db.query(User.id, User.name,User.rank).filter(User.mentor_id==Mentors.id).all()
    return Users

def get_Users_byMentor_name(db: Session, user_id:int, name: str):
    Mentors=get_Mentor(db,user_id=user_id)
    Users=db.query(User.id, User.name).filter(User.mentor_id==Mentors.id, User.name == name).all()
    return Users

def get_cheating_days(db: Session, user_id: int, year: int, month: int):
    # 필터링할 날짜의 범위 계산
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31"

    cheating_day = db.query(MealDay.date).filter(
        MealDay.user_id == user_id,
        MealDay.cheating >= 1,
        MealDay.date >= start_date,
        MealDay.date <= end_date
    ).all()
    return [day[0] for day in cheating_day]

