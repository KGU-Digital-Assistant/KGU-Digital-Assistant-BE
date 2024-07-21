from typing import List

from sqlalchemy import desc
from datetime import datetime
from models import User, Track, Invitation, MealDay
from sqlalchemy.orm import Session
from domain.track.track_schema import Track_list_get_schema,TrackCreate, TrackSchema
from domain.group import group_crud


def track_create(db: Session, user: User):
    db_track = Track(user_id=user.id)
    db.add(db_track)
    db.commit()
    return db_track


# 이름 track 찾기
def track_update(db: Session, _track_id: int, user: User, _track: TrackCreate):
    track = db.query(Track).filter(Track.id == _track_id).first()
    if (track is None):
        return None
    if (track.user_id != user.id):
        return None

    track.water = _track.water or track.water
    track.coffee = _track.coffee or track.coffee
    track.alcohol = _track.alcohol or track.alcohol
    track.duration = _track.duration
    track.track_yn = _track.track_yn
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

def get_Track_byuser_id(db: Session, user_id:int):
    tracks = db.query(Track).filter(
        Track.user_id == user_id
    ).first()
    return tracks

def get_Track_bytrack_id(db: Session, track_id:int):
    tracks =db.query(Track).filter(
        Track.id == track_id
    ).first()
    return tracks

def get_Track_mine_title_all(db:Session, user_id: int):
    tracks = db.query(Track.id, Track.name).filter(Track.user_id==user_id).all()
    return [Track_list_get_schema(track_id=track.id, name=track.name, using= check_today_track_id(db,user_id=user_id)) for track in tracks]

def get_Track_share_title_all(db:Session,user_id:int):
    invitations = db.query(Invitation.track_id).filter(Invitation.user_id==user_id).all()
    tracks = []
    for invitation in invitations:
        track_id = invitation[0]  # 튜플에서 track_id를 얻음
        track = db.query(Track.id, Track.name).filter(Track.id == track_id).first()
        if track:
            tracks.append(track)
    return [Track_list_get_schema(track_id=track.id, name=track.name, using=check_today_track_id(db, user_id)) for track in
            tracks]

def check_today_track_id(db:Session, user_id: int, track_id: int) -> bool:
    date = datetime.utcnow().date()+ timedelta(hours=9)
    mealtoday = db.query(MealDay).filter(MealDay.user_id==user_id, MealDay.date==date).first()
    if mealtoday and mealtoday.track_id==track_id:
        return True
    return False

def get_track_title_all(db:Session, user_id: int):
    groups = group_crud.get_group_by_user_id_all(db,user_id=user_id)
    tracks = []
    seen_trackid =set() #중복 track_id 확인용
    for group_info in groups:
        group, cheating_count, user_id = group_info
        track_id = group.track_id
        if track_id not in seen_trackid: #track_id 처리여부확인
            track = db.query(Track.id, Track.name, Track.start_date).filter(Track.id == track_id).first()
            if track:
                tracks.append(track)
                seen_trackid.add(track_id) #처리된 track_id 집합
    #start_date 기준으로 정렬
    tracks = sorted(tracks, key=lambda x: x.start_date, reverse=True)
    return [Track_list_get_schema(track_id=track.id, name=track.name, using=check_today_track_id(db, user_id=user_id,track_id=track.id)) for track in tracks]