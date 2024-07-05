from datetime import timedelta, date
from sqlalchemy.orm import Session
from models import Group, Track, Invitation, User
from fastapi import HTTPException
from domain.group.group_schema import GroupCreate, InviteStatus




def create_group(db: Session, _group: GroupCreate, track: Track, user_id: int):
    db_group = Group(
                    name=_group.name,
                    track_id=track.id,
                    user_id=user_id,
                    start_day=_group.start_day,
                    finish_day=_group.start_day + timedelta(days=track.duration)
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
                                             Invitation.status == InviteStatus.PENDING).first()
    invitation.status = InviteStatus.ACCEPTED
    db.commit()

    user = db.query(User).filter(User.id == user_id).one()
    group = db.query(Group).filter(Group.id == group_id).one()
    group.users.append(user)
    db.commit()

#########################################

def get_Group_bydate(db: Session, user_id:int, date:date):
    group_info = db.query(Group).filter(Group.user_id==user_id, Group.start_day>=date, Group.finish_day<=date).first()
    if group_info is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group_info

