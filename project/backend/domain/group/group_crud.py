from datetime import timedelta, date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, insert, update
from domain.meal_day import meal_day_crud
from domain.track_routine import track_routine_crud
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

def get_Group_bytrack_id_state_ready(db: Session, user_id:int, track_id:int):
    groups = db.query(Group).filter(Group.track_id==track_id,
                                    Group.state=='ready').first()
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

def get_group_date_null_track_id_in_part(db: Session, user_id: int, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id)
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
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id)
        .join(Participation, Group.id == Participation.c.group_id)
        .filter(
            Participation.c.user_id == user_id,
        )
        .all()
    )
    return result if result else []

def get_group_by_date_track_id_all(db: Session, date: date, track_id: int):
    result = (
        db.query(Group, Participation.c.cheating_count, Participation.c.user_id)
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
        flag=None,
        finish_date=None
    )
    db.execute(stmt)
    db.commit()
    return


def update_group_mealday_pushing_start(db:Session, user_id: int, track_id: int, date: date, group_id: int, duration: int):
    date1 = date
    ##기존 사용중인 트랙 있을 경우에 해당 Group 종료일변경 및 Mealday의 goalcalorie, track_id 변경
    mealtoday= meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if mealtoday and mealtoday.track_id and mealtoday.track_id >=1:
        group_participation = get_group_by_date_track_id_in_part(db,user_id=user_id,date=date,track_id=mealtoday.track_id)
        if group_participation is None:
            raise HTTPException(status_code=404, detail="Group not found")
        group, cheating_count, user_id2, flag, finish_date = group_participation # 튜플 언패킹(group, participation obj 로 나눔)
        while date1 <= group.finish_day: ## 금일 ~ 과거 track 날짜까지 track_id, goalcalorie 초기화 // 트랙중도변경시
            mealold = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date1)
            if mealold:
                mealold.track_id=None
                mealold.goalcalorie=0.0
                db.add(mealold)
                db.commit()
                db.refresh(mealold)
            date1 += timedelta(days=1)
        # Participation 테이블에 실제종료일로 변경, flag=False로 종료처리 - 기존그룹
        stmt = (
            update(Participation)
            .where(Participation.c.user_id == user_id, Participation.c.group_id == group.id)
            .values(flag=False, finish_date=date-timedelta(days=1))
        )
        db.execute(stmt)
        db.commit()
    ## 새 트랙의 Group 시작 종료일 설정 ->추후 그룹시작날짜를 대표가할것인지, 아니면 모두가 같은걸선택해야 가능하게할건지 현재는그룹에 1명이므로 그렇게햇슴
    groupnew = get_group_by_id(db,group_id=group_id)
    groupnew.start_day = date
    groupnew.finish_day = date + timedelta(days=duration)
    groupnew.state = 'started'
    db.add(groupnew)
    db.commit()
    db.refresh(groupnew)
    ## Participation 테이블에 flag=True, 종료일설정 - 시작하는 그룹
    #  -> 추후 Participation 테이블에 그룹내 모든user의 flag true여야 아래가 동작되도록해야함 + group.state started로 변경
    stmt = (
        update(Participation)
        .where(Participation.c.user_id == user_id, Participation.c.group_id == group.id)
        .values(flag=True, finish_date=groupnew.finish_day)
    )
    db.execute(stmt)
    db.commit()
    ## MealDay의 새로운 Track_id및 goalcalorie 설정
    date2 = date
    while date2 <= groupnew.finish_day:
        mealnew=meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date2)
        days=(groupnew.finish_day - date2).days
        if mealnew:
            mealnew.track_id=track_id
            mealnew.goalcalorie=track_routine_crud.get_goal_caloire_bydate_using_trackroutine(db,days=days,track_id=track_id,date=date2)
            db.add(mealnew)
            db.commit()
            db.refresh(mealnew)
        else:
            new_meal = MealDay(
                user_id=user_id,
                water=0.0,
                coffee=0.0,
                alcohol=0.0,
                carb=0.0,
                protein=0.0,
                fat=0.0,
                cheating=0,
                goalcalorie=track_routine_crud.get_goal_caloire_bydate_using_trackroutine(db,days=days,track_id=track_id,date=date2),
                nowcalorie=0.0,
                gb_carb=None,
                gb_protein=None,
                gb_fat=None,
                date=date2,
                track_id=track_id  ## 트랙 user사용중일때 안할때 이거 변경해야할거같은데
            )
            db.add(new_meal)
            db.commit()
            db.refresh(new_meal)
        date2 += timedelta(days=1)
