from datetime import timedelta, date, datetime
from sqlalchemy.orm import Session
from models import Group, Track, Invitation, User, MealDay, Participation
from fastapi import HTTPException
from domain.group.group_schema import GroupCreate, InviteStatus, GroupDate, Respond, GroupStatus


def create_group(db: Session, track: Track, user_id: int):
    db_group = Group(
                    track_id=track.id,
                    creator=user_id,
                    status=GroupStatus.READY
                    # 종료일 = 시작일 + (track.duration)일
                )
    db.add(db_group)
    db.commit()
    return db_group


def get_group_by_id(db, group_id):
    return db.query(Group).filter(Group.id == group_id).first()


def create_invitation(db: Session, user_id: int, group_id: int):
    db_invitation = Invitation(
        user_id=user_id,
        group_id=group_id
    )
    db.add(db_invitation)
    db.commit()


def accept_invitation(db: Session, user_id: int, group_id: int, respond: Respond):
    user = db.query(User).filter(User.id == user_id).first()

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


def update_group_date(db: Session, group_id: int, date: GroupDate):
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    group.start_day = date.start_date
    group.finish_day = date.end_date
    db.commit()
    return {"detail" : "group updated successfully"}


def participate_group(db: Session, user_id: int, group_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    group = db.query(Group).filter(Group.id == group_id).first()
    group.users.append(user)
    db.commit()


def delete_group_in_user(cur_user: User, db: Session):
    cur_user.cur_group_id = None
    db.commit()


def is_finished(db: Session):
    now = datetime.now()
    groups = db.query(Group).filter(Group.finish_day < now, Group.status == GroupStatus.STARTED).all()
    for group in groups:
        group.status = GroupStatus.TERMINATED
        db.commit()

        for user in group.users:
            user.cur_group_id = None
            db.commit()






