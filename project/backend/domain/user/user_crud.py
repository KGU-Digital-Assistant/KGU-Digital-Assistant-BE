from datetime import datetime, date
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Optional
from domain.user.user_schema import UserCreate, UserUpdate, Rank, UserProfile
from models import User, Invitation
from firebase_admin import messaging


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_existing_user(db: Session, user_create: UserCreate):
    return db.query(User).filter(
        User.cellphone == user_create.cellphone or
        User.nickname == user_create.nickname or
        User.email == user_create.email
    ).first()


def create_user(db: Session, user_create: UserCreate):
    _cellphone = user_create.cellphone.replace("-", "")
    db_user = User(name=user_create.name,
                   username=user_create.username,
                   nickname=user_create.nickname,
                   email=user_create.email,
                   cellphone=_cellphone,
                   password=pwd_context.hash(user_create.password1),
                   gender=user_create.gender,
                   rank=Rank.BRONZE.value,
                   birth=user_create.birth,
                   create_date=datetime.now(),
                   )
    db.add(db_user)
    db.commit()
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.name = user_update.name or user.username
        user.email = user_update.email or user.email
        user.nickname = user_update.nickname or user.nickname
        db.commit()
        db.refresh(user)
    return user


def update_external_id(db: Session, external_id: int, user_id: int, _auth_type: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.external_id = external_id
        user.auth_type = _auth_type
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

# def update_profile(db: Session, profile_user: UserProfile,
#                    current_user: User):
#     current_user.profile_picture = profile_user.profile_picture
#     current_user.username = profile_user.username
#     current_user.nickname = profile_user.nickname
#     current_user.mentor_id = profile_user.mentor.id
#     db.commit()
#     db.refresh(current_user)


def update_kakao_tokens(db: Session, user_id: int, new_access_token: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    db_user.access_token = new_access_token
    db.commit()
    db.refresh(db_user)


# def get_user_by_cellphone(db: Session, _cellphone: str):
#     cellphone = _cellphone.replace('-', '')
#     phone_number = "010" + cellphone[-8:]
#     return db.query(User).filter(User.cellphone==phone_number).first()

###########################################

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

def update_profile(db: Session, profile_user: UserProfile,
                   current_user: User):
    _mentor = None
    if profile_user.mentor_name:
        _mentor = db.query(User).filter(User.username == profile_user.mentor_name).first()

    current_user.name = profile_user.name
    current_user.nickname = profile_user.nickname
    if _mentor is not None:
        current_user.mentor_id = _mentor.user_id
    db.commit()
    db.refresh(current_user)


def update_kakao_tokens(db: Session, user_id: int, new_access_token: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    db_user.access_token = new_access_token
    db.commit()
    db.refresh(db_user)


def get_user_by_cellphone(db: Session, _cellphone: str):
    cellphone = _cellphone.replace('-', '')
    return db.query(User).filter(User.cellphone==cellphone).first()


def save_fcm_token(db: Session, _user_name: str, _fcm_token: str):
    db_user = db.query(User).filter(User.username == _user_name).first()
    if db_user is not None:
        db_user.fcm_token = _fcm_token
        db.commit()
        db.refresh(db_user)
    return db_user


def send_push_invite(fcm_token: str, title: str, body: str):
    """
    fcm 메시지 생성
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=fcm_token
    )

    response = messaging.send(message)
    return response


def invitation_respond(invitation_id: int, response: str, db: Session, _mentee_id: int):
    invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
    invitation.status = response.lower()
    db.commit()

    if response.lower() == "accepted":
        mentee = db.query(User).filter(User.id == _mentee_id).first()
        mentee.mentor_id = invitation.mentor.id
        db.commit()


def delete_mentor(id: int, db: Session):
    user = db.query(User).filter(User.id == id).first()
    if user is None:
        return False
    user.mentor_id = None
    return True


def get_user_by_id(db: Session, id: int):
    return db.query(User).filter(User.id == id).first()


def get_user_by_nickname(db: Session, user_create: UserCreate):
    return db.query(User).filter(User.nickname == user_create.nickname).first()


def get_create_day(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()

    create_date = user.create_date
    delta = datetime.now() - create_date
    days = delta.days
    return days


def get_user_by_only_nickname(db: Session, nickname: str):
    return db.query(User).filter(User.nickname == nickname).first()