from datetime import timedelta, date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, insert, update
from domain.meal_day import meal_day_crud
from domain.track_routine import track_routine_crud
from models import Group, Track, Invitation, User,MealDay, Participation
from fastapi import HTTPException
from domain.group.group_schema import GroupCreate, InviteStatus
from models import FlagStatus




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

def get_Group_bytrack_id_state_ready(db: Session, track_id:int):
    groups = db.query(Group).filter(Group.track_id==track_id,
                                    Group.state=="ready").first()
    return groups

def get_Group_byuserid_track_id_bystartfinishday(db: Session, user_id:int, track_id:int, date: date):

    groups = db.query(Group).filter(Group.user_id==user_id, Group.track_id==track_id,
                                    Group.start_day<=date, Group.finish_day>=date
                                    ).first()
    if groups is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return groups


def get_group_by_date_track_id_in_part(db: Session, user_id: int, date: date, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag, Participation.c.finish_date)
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

def get_group_track_id_in_part_state_start(db: Session, user_id: int, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag, Participation.c.finish_date)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Participation.c.user_id == user_id,
            Group.track_id == track_id,
            Group.state =='started'
        )
        .first()
    )
    return result if result else None

def get_group_date_null_track_id_in_part(db: Session, user_id: int, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag, Participation.c.finish_date)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Participation.c.user_id == user_id,
            Group.start_day == None,
            Group.finish_day == None,
            Group.track_id == track_id
        )
        .first()
    )
    return result if result else None

def get_group_by_user_id_all(db: Session, user_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag, Participation.c.finish_date)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Participation.c.user_id == user_id,
        )
        .all()
    )
    return result if result else []

def get_group_by_date_track_id_all(db: Session, date: date, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag, Participation.c.finish_date)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Group.start_day <= date,
            Group.finish_day >= date,
            Group.track_id == track_id
        )
        .all()
    )
    return result if result else None

def add_participation(db:Session, user_id:int, group_id: int, cheating_count: int):
    stmt = insert(Participation).values(
        user_id=user_id,
        group_id=group_id,
        cheating_count=cheating_count,
        flag=FlagStatus.ready,
        finish_date=None
    )
    db.execute(stmt)
    db.commit()
    return

def get_track_id_all_in_date(db: Session, start_date: date, finish_date: date, user_id: int):
    track_ids = []
    date_iter = start_date
    while date_iter <= finish_date:
        mealtoday = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date_iter)
        if mealtoday and mealtoday.track_id is not None:
            track_id = mealtoday.track_id
            track_ids.append(track_id)
        date_iter += timedelta(days=1)
    return track_ids

def update_group_mealday_pushing_start(db: Session, user_id: int, track_id: int, date: date, group_id: int, duration: int):
    date_iter = date
    new_group_finish_date = date + timedelta(days=duration)

    # MealDay 초기화
    while date_iter <= new_group_finish_date:
        mealnew = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date_iter)
        if mealnew is None:
            new_meal = MealDay(
                user_id=user_id,
                water=0.0,
                coffee=0.0,
                alcohol=0.0,
                carb=0.0,
                protein=0.0,
                fat=0.0,
                cheating=0,
                goalcalorie=0.0,
                nowcalorie=0.0,
                gb_carb=None,
                gb_protein=None,
                gb_fat=None,
                date=date_iter,
                track_id=None
            )
            db.add(new_meal)
        date_iter += timedelta(days=1)
    db.commit()

    track_ids = get_track_id_all_in_date(db, start_date=date, finish_date=new_group_finish_date, user_id=user_id)
    if track_ids:
        for track_id_iter in track_ids:
            date_iter = date
            group_part = get_group_track_id_in_part_state_start(db, user_id=user_id, track_id=track_id_iter)
            if group_part is None:
                continue
            group, cheating_count, user_id2, flag, finish_date = group_part
            while date_iter <= group.finish_day:
                mealold = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date_iter)
                if mealold:
                    mealold.track_id = None
                    mealold.goalcalorie = 0.0
                    db.add(mealold)
                date_iter += timedelta(days=1)
            stmt = (
                update(Participation)
                .where(Participation.c.user_id == user_id, Participation.c.group_id == group.id)
                .values(flag=FlagStatus.terminated, finish_date=date - timedelta(days=1))
            )
            db.execute(stmt)
        db.commit()

    # 새 트랙의 Group 시작 종료일 설정
    groupnew = get_group_by_id(db, group_id=group_id)
    groupnew.start_day = date
    groupnew.finish_day = new_group_finish_date
    db.add(groupnew)
    db.commit()
    db.refresh(groupnew)

    # 새로운 Participation 설정
    stmt = (
        update(Participation)
        .where(Participation.c.user_id == user_id, Participation.c.group_id == group_id)
        .values(flag=FlagStatus.started, finish_date=groupnew.finish_day)
    )
    db.execute(stmt)
    db.commit()

    # 새로운 MealDay의 Track_id 및 goalcalorie 설정
    date_iter = date
    days=1
    while date_iter <= groupnew.finish_day:
        mealnew = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date_iter)
        if mealnew:
            mealnew.track_id = track_id
            mealnew.goalcalorie = track_routine_crud.get_goal_caloire_bydate_using_trackroutine(db, days=days, track_id=track_id, date=date_iter)
            db.add(mealnew)
        date_iter += timedelta(days=1)
        days+=1
    db.commit()