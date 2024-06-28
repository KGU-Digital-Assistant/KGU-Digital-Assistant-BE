from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from domain.user.user_schema import UserCreate, UserUpdate, Rank, UserList
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_existing_user(db: Session, user_create: UserCreate):
    return db.query(User).filter(
        User.email == user_create.email
    ).first()


def create_user(db: Session, user_create: UserCreate):
    db_user = User(username=user_create.name,
                   nickname=user_create.nickname,
                   email=user_create.email,
                   cellphone=user_create.cellphone,
                   password=pwd_context.hash(user_create.password1),
                   gender=user_create.gender,
                   rank=Rank.BRONZE.value,
                   birth=user_create.birth,
                   create_date=datetime.now(),
                   )
    db.add(db_user)
    db.commit()


def update_user(db: Session, user_id: int, user_update: UserUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.username = user_update.name or user.username
        user.email = user_update.email or user.email
        if user_update.password:
            user.password = pwd_context.hash(user_update.password)
        db.commit()
        db.refresh(user)
    return user


def update_external_id(db: Session, external_id: int, user_name: str):
    user = db.query(User).filter(User.username == user_name).first()
    if user:
        user.external_id = external_id
        user.auth_type = "kakao"
        db.commit()
        db.refresh(user)

    return user


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_external_id(db: Session, external_id: int):
    return db.query(User).filter(User.external_id == external_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, _username: str):
    return db.query(User).filter(User.username == _username).first()


def get_users_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).all()