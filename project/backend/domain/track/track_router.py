from typing import List

from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from starlette import status
from datetime import datetime
from database import get_db
from domain.user import user_router, user_crud
from models import Track, User, TrackRoutine
from domain.group import group_crud
from domain.track_routine import track_routine_crud,track_routine_schema
from domain.track.track_schema import TrackCreate, TrackResponse, TrackSchema, TrackList
from domain.track import track_crud, track_schema

router = APIRouter(
    prefix="/track",
)


@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def create_track(current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    track = track_crud.track_create(db, current_user)
    return {"track_id": track.id}


@router.patch("/update", status_code=status.HTTP_204_NO_CONTENT)
def update_track(_track_id: int,
                 _track: TrackCreate,
                 current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    track = track_crud.track_update(db, _track_id, current_user, _track)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return track


# track 특정 이름 포함 모두 검색 : ex) `건강` 검색-> `건강한 식단트랙`  (단 두글자 이상 검색해야함)
@router.get("/search/{track_name}", response_model=TrackList, status_code=200)
def get_track_by_name(track_name: str, db: Session = Depends(get_db),
                      page: int = 0, size: int = 10):
    """
    이건 안쓸듯
    """
    track_name.strip() # 앞뒤 공백 제거
    if (len(track_name) < 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Track name must be at least 1 character",
        )
    total, tracks = track_crud.get_tracks_by_track_name(db=db, track_name=track_name,
                                                        skip=page * size, limit=size)
    return {
        'total': total,
        'tracks': tracks
    }


@router.get("/get/{track_id}", response_model=TrackSchema, status_code=200)
def get_track_by_id(track_id: int, db: Session = Depends(get_db)):
    return track_crud.get_track_by_id(db=db, track_id=track_id)


###################################################

@router.get("/get/{user_id}", response_model=track_schema.Track_schema)
def get_Track_id(user_id: int, db: Session = Depends(get_db)):
    tracks = track_crud.get_Track_byuser_id(db, user_id=user_id)
    if tracks is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return tracks

@router.get("/get/{user_id}/mytracks", response_model=List[track_schema.Track_list_get_schema])
def get_Track_mylist(user_id: int, db:Session = Depends(get_db)):
    tracklist = track_crud.get_Track_mine_title_all(db,user_id=user_id)
    if tracklist is None:
        raise HTTPException(status_code=404, detail="Track not found")
        return 0
    return tracklist

@router.get("/get/{user_id}/sharetracks", response_model=List[track_schema.Track_list_get_schema])
def get_Track_sharelist(user_id: int, db:Session = Depends(get_db)):
    tracklist = track_crud.get_Track_share_title_all(db,user_id=user_id)
    if tracklist is None:
        raise HTTPException(status_code=404, detail="Track not found")
        return 0
    return tracklist

@router.get("/get/{user_id}/{track_id}/Info", response_model=track_schema.Track_get_Info)
def get_Track_Info(user_id: int, track_id: int, db:Session=Depends(get_db)):
    tracks= track_crud.get_Track_bytrack_id(db,track_id=track_id)
    if tracks is None:
        raise HTTPException(status_code=404, detail="Track not found")
    username=user_crud.get_User_name(db,id=tracks.user_id)
    today=datetime.utcnow().date()
    groups=group_crud.get_Group_bydate(db,user_id=user_id,date=today)
    if groups:
        startday=groups.start_day
        finishday=groups.finish_day
    else:
        startday=None
        finishday=None
    trackroutins=track_routine_crud.get_TrackRoutine_bytrack_id(db, track_id=track_id)
    repeat=[]
    solo=[]
    for trackroutin in trackroutins:
        routin_data = track_routine_schema.TrackRoutin_id_title(
            id=trackroutin.id,
            title=trackroutin.title,
            week=trackroutin.week,
            time=trackroutin.time,
            date=trackroutin.date,
            repeat=trackroutin.repeat
        )
        if trackroutin.repeat:
            repeat.append(routin_data)
        else:
            solo.append(routin_data)

    return {
        "track_name": tracks.name,
        "name": username,
        "start_day": startday,
        "finish_day": finishday,
        "duration": tracks.duration,
        "repeatroutin": repeat,
        "soloroutin": solo
    }

@router.post("/post/{user_id})", response_model=track_schema.Track_create_schema)##회원일경우
def post_Track(user_id: int, track: track_schema.Track_create_schema,db:Session=Depends(get_db)):
    db_track = Track(
        user_id=user_id,
        name=track.name,
        water=track.water,
        coffee=track.coffee,
        alcohol=track.alcohol,
        duration=track.duration,
        track_yn=True,
        cheating_count=track.cheating_count
    )
    db.add(db_track)
    db.commit()
    db.refresh(db_track)

    for routine in track.routines:
        db_routine= TrackRoutine(
            track_id=db_track.id,
            title=routine.title,
            food=routine.food,
            calorie=routine.calorie,
            week=routine.week,
            time=routine.time,
            repeat=routine.repeat
        )
        db.add(db_routine)

    db.commit()
    db.refresh(db_track)


