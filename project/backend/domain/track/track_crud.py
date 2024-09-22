from typing import List

from sqlalchemy import desc
from models import User, Track, Invitation, MealDay, TrackRoutine, TrackRoutineDate,Group
from sqlalchemy.orm import Session
from domain.track.track_schema import Track_list_get_schema, TrackCreate, TrackSchema
from datetime import datetime, timedelta
from domain.group import group_crud

def track_create(db: Session, user: User):
    db_track = Track(
        user_id=user.id,
        create_time=datetime.now(),
    )
    db.add(db_track)
    db.commit()
    return db_track


# 이름 track 찾기
def track_update(db: Session, _track_id: int, user: User, _track: TrackCreate, cheating_cnt: int):
    track = db.query(Track).filter(Track.id == _track_id).first()
    if (track is None):
        return None
    if (track.user_id != user.id):
        return None

    track.name = _track.name
    track.icon = _track.icon
    track.cheating_count = cheating_cnt
    track.water = _track.water or track.water
    track.coffee = _track.coffee or track.coffee
    track.alcohol = _track.alcohol or track.alcohol
    track.duration = _track.duration
    track.delete = _track.delete
    track.start_date = _track.start_date
    track.end_date = _track.end_date
    track.alone = _track.alone
    track.daily_calorie = _track.calorie
    db.commit()
    db.refresh(track)
    return track


def get_tracks_by_track_name(db: Session, track_name: str, skip: int = 0, limit: int = 10):
    query = db.query(Track).filter(Track.name.contains(track_name)).order_by(desc(Track.name))
    count = query.count()
    tracks = query.offset(skip).limit(limit).all()
    return count, tracks


def get_track_by_id(db: Session, track_id: int):
    return db.query(Track).filter(Track.id == track_id).first()


############################################

def get_Track_byuser_id(db: Session, user_id: int):
    tracks = db.query(Track).filter(
        Track.user_id == user_id
    ).first()
    return tracks


def get_Track_bytrack_id(db: Session, track_id: int):
    tracks = db.query(Track).filter(
        Track.id == track_id
    ).first()
    return tracks


def get_Track_mine_title_all(db:Session, user_id: int):
    tracks = db.query(Track).filter(Track.user_id==user_id).all()
    tracks = sorted(tracks, key=lambda x: x.create_time, reverse=True)
    return [Track_list_get_schema(track_id=track.id, name=track.name, icon=track.icon, daily_calorie=track.daily_calorie, create_time=track.create_time,using= check_today_track_id(db,user_id=user_id,track_id=track.id)) for track in tracks]


def get_Track_share_title_all(db: Session, user_id: int):
    invitations = db.query(Invitation.group_id).filter(Invitation.user_id == user_id,Invitation.status=="accepted").all()
    tracks = []
    for invitation in invitations:
        group_id = invitation[0]  # 튜플에서 track_id를 얻음
        groups= db.query(Group.track_id).filter(Group.id==group_id).first()
        track = db.query(Track).filter(Track.id == groups.track_id).first()
        if track:
            tracks.append(track)
    return [Track_list_get_schema(track_id=track.id, name=track.name, icon=track.icon, daily_calorie=track.daily_calorie, create_time=track.create_time,using= check_today_track_id(db,user_id=user_id,track_id=track.id)) for track in tracks]



def delete_track(db: Session, track_id: int):
    track = db.query(Track).filter(Track.id == track_id).first()
    db.delete(track)
    db.commit()


def copy_multiple_track(db: Session, track: Track, user_id: int):
    new_track = Track(
        user_id=user_id,
        name=track.name,
        water=track.water,
        coffee=track.coffee,
        alcohol=track.alcohol,
        duration=track.duration,
        track_yn=track.delete,
        start_date=track.start_date,
        finish_date=track.finish_date,
        cheating_count=track.cheating_count,
        alone=False,
        create_time=datetime.now(),
        share_count=track.share_count + 1,
        # origin_id=track.id
    )
    db.add(new_track)
    db.commit()

    routines = db.query(TrackRoutine).filter(TrackRoutine.track_id == track.id).all()
    for routine in routines:
        new_routine = TrackRoutine(
            track_id=new_track.id,
            calorie=routine.calorie,
            repeat=routine.repeat,
            title=routine.title,
            week=routine.week,
            date=routine.date,
        )
        db.add(new_routine)
        db.commit()

    return new_track
  
  
def check_today_track_id(db:Session, user_id: int, track_id: int) -> bool:
    date = datetime.utcnow().date()+ timedelta(hours=9)
    mealtoday = db.query(MealDay).filter(MealDay.user_id==user_id, MealDay.date==date).first()
    if mealtoday and mealtoday.track_id==track_id:
        return True
    return False

  
def get_track_title_all(db:Session, user_id: int):
    tracks = []
    seen_trackid =set() #중복 track_id 확인용
    # 현재 사용자의 track 추가
    trackmine = db.query(Track).filter(Track.user_id == user_id).all()

    # trackmine의 데이터를 tracks에 추가, 중복 제거
    for track in trackmine:
        tracks.append(track)
        seen_trackid.add(track.id)

    groups = group_crud.get_group_by_user_id_all(db,user_id=user_id)
    for group_info in groups:
        group, cheating_count, user_id2, flag, finish_date =group_info
        track_id = group.track_id
        if track_id not in seen_trackid: #track_id 처리여부확인
            track = db.query(Track).filter(Track.id == track_id).first()
            if track:
                tracks.append(track)
                seen_trackid.add(track_id) #처리된 track_id 집합

    return [Track_list_get_schema(track_id=track.id, name=track.name, icon=track.icon, daily_calorie=track.daily_calorie, create_time=track.create_time, using=check_today_track_id(db, user_id=user_id,track_id=track.id)) for track in tracks]

