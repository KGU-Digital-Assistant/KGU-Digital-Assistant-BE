from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from domain.user.user_schema import UserCreate
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_existing_user(db: Session, user_create: UserCreate):
    return db.query(User).filter(
        (User.name == user_create.name) |
        (User.email == user_create.email)
    ).first()


def create_user(db: Session, user_create: UserCreate):

    db_user = User(name=user_create.name,
                   nickname=user_create.nickname,
                   email=user_create.email,
                   password=pwd_context.hash(user_create.password1),
                   address=user_create.address,
                   gender=user_create.gender,
                   birthday=user_create.birthday,
                   create_date=datetime.now(),
                   )
    db.add(db_user)
    db.commit()


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()