from datetime import timedelta, date, datetime
from domain.group.group_schema import GroupCreate, InviteStatus, GroupDate, Respond, GroupStatus
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, insert, update
from domain.meal_day import meal_day_crud
from domain.track_routine import track_routine_crud
from models import Group, Track, Invitation, User, MealDay, Participation
from fastapi import HTTPException

from models import FlagStatus


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
    track = db.query(Track).filter(Track.id == group.track_id).first()

    insert(Participation).values(
        user_id=user_id,
        group_id=group_id,
        cheating_count=track.cheating_count,
    )
    db.commit()


###########################################
#현빈
###########################################

def get_Group_bydate(db: Session, user_id: int, date: date):
    mealday = db.query(MealDay).filter(MealDay.user_id == user_id, MealDay.date == date).first()
    if mealday is None:
        return None
    group_info = db.query(Group).filter(Group.user_id == user_id, Group.track_id == mealday.track_id,
                                        Group.start_day >= date, Group.finish_day <= date).first()
    if group_info is None:
        return {"detail": "group not use today"}
    return group_info


def get_Group_bytrack_id_state_ready(db: Session, track_id: int):
    groups = db.query(Group).filter(Group.track_id == track_id,
                                    Group.status == GroupStatus.READY).first()
    return groups


def get_Group_byuserid_track_id_bystartfinishday(db: Session, user_id: int, track_id: int, date: date):
    groups = db.query(Group).filter(Group.user_id == user_id, Group.track_id == track_id,
                                    Group.start_day <= date, Group.finish_day >= date
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
    return {"detail": "group updated successfully"}


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

            _updated = update(Participation).where(Participation.c.user_id == user.id,
                                                   Participation.c.group_id == group.id
                                                   ).values({"flag": FlagStatus.TERMINATED})
            db.commit()


def get_group_by_date_track_id_in_part(db: Session, user_id: int, date: date, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag,
                 Participation.c.finish_date)
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
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag,
                 Participation.c.finish_date)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Participation.c.user_id == user_id,
            Group.track_id == track_id,
            Group.status == GroupStatus.STARTED
        )
        .first()
    )
    return result if result else None


def get_group_date_null_track_id_in_part(db: Session, user_id: int, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag,
                 Participation.c.finish_date)
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
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag,
                 Participation.c.finish_date)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Participation.c.user_id == user_id,
        )
        .all()
    )
    return result if result else []


def get_group_by_date_track_id_all(db: Session, date: date, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id, Participation.c.flag,
                 Participation.c.finish_date)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Group.start_day <= date,
            Group.finish_day >= date,
            Group.track_id == track_id
        )
        .all()
    )
    return result if result else None


def add_participation(db: Session, user_id: int, group_id: int, cheating_count: int):
    stmt = insert(Participation).values(
        user_id=user_id,
        group_id=group_id,
        cheating_count=cheating_count,
        flag=FlagStatus.READY,
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


def update_group_mealday_pushing_start(db: Session, user_id: int, track_id: int, date: date, group_id: int,
                                       duration: int):
    date_iter = date
    new_group_finish_date = date + timedelta(days=duration-1)

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
                .values(flag=FlagStatus.TERMINATED, finish_date=date - timedelta(days=1))
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
        .values(flag=FlagStatus.STARTED, finish_date=groupnew.finish_day)
    )
    db.execute(stmt)
    db.commit()

    # 새로운 MealDay의 Track_id 및 goalcalorie 설정
    date_iter = date
    days = 1
    while date_iter <= groupnew.finish_day:
        mealnew = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date_iter)
        if mealnew:
            mealnew.track_id = track_id
            mealnew.goalcalorie = track_routine_crud.get_goal_caloire_bydate_using_trackroutine(db, days=days,
                                                                                                track_id=track_id,
                                                                                                date=date_iter)
            db.add(mealnew)
        date_iter += timedelta(days=1)
        days += 1
    db.commit()


def exit_group(db: Session, user_id: int, date: date, group_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    past_group=get_group_by_id(db, group_id=user.cur_group_id)
    if past_group is None:
        raise HTTPException(status_code=404, detail="Not Using Group Now")
    if past_group.start_day > date or past_group.finish_day < date:
        raise HTTPException(status_code=404, detail="Using Group is not in date")
    date_iter = date+timedelta(days=1) ## 2024-07-02에 종료누르면 2024-07-02까지는 트랙사용
    finish_date = past_group.finish_day
    # MealDay 초기화
    while date_iter <= finish_date:
        mealold = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date_iter)
        if mealold:
            mealold.track_id = None
            mealold.goalcalorie = 0.0
            db.add(mealold)
        date_iter += timedelta(days=1)
    user.cur_group_id = None
    db.add(user)
    _updated = (update(Participation).where(Participation.c.user_id == user_id,
                                            Participation.c.group_id == group_id)
                .values(flag=FlagStatus.TERMINATED, finish_date=date.today()))
    db.execute(_updated)
    db.commit()


