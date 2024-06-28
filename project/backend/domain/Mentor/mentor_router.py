import requests
from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from database import get_db
from domain.Mentor.mentor_crud import create_mentor, update_mentor_gym, mentor_delete, matching_mentor
from domain.Mentor.mentor_schema import MentorCreate, MentorGym, MenteeSchema
from models import Mentor, User
from domain.user import user_crud, user_router

router = APIRouter(
    prefix="/api/mentor",
)

def get_current_mentor(_user_id: int, db: Session = Depends(get_db)):
    return user_router.get_current_user()

# 일반 회원 -> 트레이너가 될 때
@router.post("/create", status_code=201)
async def mentor_create(_mentor_create: MentorCreate,
                        _current_user: User = Depends(user_router.get_current_user),
                        db: Session = Depends(get_db)):
    if not _current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not User",
        )
    create_mentor(mentor_create=_mentor_create, _user_id=_current_user.id, db=db)
    return {"status": "ok"}

@router.post("/add/user", status_code=201)
def connect_user_to_mentor(_mentee: MenteeSchema,
                           _mentor: User = Depends(user_router.get_current_user),
                           db: Session = Depends(get_db)):
    mentee = user_crud.get_user_by_email(db, _mentee.email)
    if not mentee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentee not found",
        )
    if mentee.mentor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already connected to a mentor",
        )

    matching_mentor(mentee=mentee, _mentor_id=_mentor.id, db=db)
    return {"status": "ok"}

@router.patch("/gym/update", status_code=201)
def gym_update(_mentor_gym: MentorGym,
               _current_user: User = Depends(user_router.get_current_user),
               db: Session = Depends(get_db)):
    if not _current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not User",
        )
    mentor = update_mentor_gym(_current_user.id, _mentor_gym, db)
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found",
        )
    return {"status": "ok"}

@router.delete("/delete", status_code=204)
def delete_mentor(cur_user: User = Depends(user_router.get_current_user), db: Session = Depends(get_db)):
    if mentor_delete(cur_user.id, db):
        return {"status": "ok"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Mentor not found",
    )
