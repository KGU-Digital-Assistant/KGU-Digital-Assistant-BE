from datetime import timedelta, date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, join
from models import Group, Track, Invitation, User,MealDay, Participation
from fastapi import HTTPException
from domain.group.group_schema import GroupCreate, InviteStatus




def create_group(db: Session, _group: GroupCreate, track: Track, user_id: int):
    track_duration = track.duration if track.duration is not None else 0
    db_group = Group(
                    name=_group.name,
                    track_id=track.id,
                    user_id=user_id,
                    start_day=_group.start_day,
                    finish_day=_group.start_day + timedelta(days=track_duration)
                    # 종료일 = 시작일 + (track.duration)일
                )
    db.add(db_group)
    db.commit()


def get_group_by_id(db, group_id):
    return db.query(Group).filter(Group.id == group_id).first()


def create_invitation(db: Session, user_id: int, group_id: int):
    db_invitation = Invitation(
        user_id=user_id,
        group_id=group_id
    )
    db.add(db_invitation)
    db.commit()


def accept_invitation(db: Session, user_id: int, group_id: int):
    invitation = db.query(Invitation).filter(Invitation.user_id == user_id,
                                             Invitation.group_id == group_id,
                                             Invitation.status == "pending").first()
    invitation.status = "accepted"
    db.commit()

    user = db.query(User).filter(User.id == user_id).one()
    group = db.query(Group).filter(Group.id == group_id).one()
    group.users.append(user)
    db.commit()

###########################################
#현빈
###########################################

def get_Group_bydate(db: Session, user_id:int, date:date):
    mealday = db.query(MealDay).filter(MealDay.user_id==user_id,MealDay.date==date).first()
    if mealday is None:
        return None
    group_info = db.query(Group).filter(Group.user_id==user_id, Group.track_id==mealday.track_id,Group.start_day>=date, Group.finish_day<=date).first()
    if group_info is None:
        return {"detail" : "group not use today"}
    return group_info

def get_Group_byuserid_track_id(db: Session, user_id:int, track_id:int):
    groups = db.query(Group).filter(Group.user_id==user_id, Group.track_id==track_id
                                    ).first()
    if groups is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return groups

def get_Group_byuserid_track_id_bystartfinishday(db: Session, user_id:int, track_id:int, date: date):
    date2 = datetime.combine(date, datetime.min.time())
    groups = db.query(Group).filter(Group.user_id==user_id, Group.track_id==track_id,
                                    Group.start_day<=date2, Group.finish_day>=date2
                                    ).first()
    if groups is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return groups


def get_group_by_date_track_id(db: Session, user_id: int, date: date, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Participation.c.user_id == user_id,
            Group.start_day <= date,
            Group.finish_day >= date,
            Group.track_id == track_id
        )
        .first()
    )
    return result if result else None

def get_group_by_user_id_all(db: Session, user_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Participation.c.user_id == user_id,
        )
        .all()
    )
    return result if result else []

