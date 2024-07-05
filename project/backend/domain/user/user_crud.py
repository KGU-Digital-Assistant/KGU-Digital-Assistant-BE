from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Optional
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
    user = db.query(User).filter(User.external_id == external_id).first()
    return user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, _username: str):
    return db.query(User).filter(User.username == _username).first()


def get_users_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).all()

#########################################

def get_User(db: Session, id:int):
    Users=db.query(User).get(id)
    return Users

def get_User_rank(db: Session, id:int) -> Optional[str]:
    Users=db.query(User).filter(User.id == id).first()
    if Users is None:
        return None

    user_rank = Users.rank
    all_ranks = db.query(User.rank).order_by(User.rank.desc()).all()

    rank_list=[rank[0] for rank in all_ranks]
    total_users = len(rank_list)

    user_position = rank_list.index(user_rank) +1
    percentile = (user_position/total_users) * 100

    rank_category = "기타"
    if percentile <= 5:
        rank_category = "올림피아"
    elif percentile <= 15:
        rank_category = "마스터"
    elif percentile <= 25:
        rank_category = "플레티넘"

    return f"{rank_category} {user_rank}"

def get_User_nickname(db: Session, id:int) -> str:
    Users=db.query(User).get(id)
    if Users is None:
        return None
    return Users.nickname

def get_User_name(db: Session, id:int) -> str:
    Users=db.query(User).get(id)
    if Users is None:
        return None
    return Users.name
def get_User_byemail(db: Session, mail: str):
    Users=db.query(User).filter(User.email== mail).first()
    return Users