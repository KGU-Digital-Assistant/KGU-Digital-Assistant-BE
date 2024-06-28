from typing import List

from sqlalchemy import desc

from models import User, Track
from sqlalchemy.orm import Session
from domain.track.track_schema import TrackCreate, TrackSchema


def track_create(db: Session, _track: TrackCreate, user: User):
    db_track = Track(name=_track.name,
                     user_id=user.id,
                     water=_track.water,
                     coffee=_track.coffee,
                     alcohol=_track.alcohol,
                     duration=_track.duration,
                     track_yn=_track.track_yn
                     )
    db.add(db_track)
    db.commit()


# 이름 track 찾기
def track_update(db: Session, _track: TrackCreate, user: User):
    track = db.query(Track).filter(Track.name == _track.name).first()
    if track:
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




def get_track_by_id(track_id: int, db: Session) -> TrackSchema:
    return db.query(Track).filter(Track.id == track_id).first()