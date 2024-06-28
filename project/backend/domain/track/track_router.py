from typing import List

from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from starlette import status

from database import get_db
from domain.user import user_router
from models import Track, User
from domain.track.track_schema import TrackCreate, TrackResponse, TrackSchema, TrackList
from domain.track import track_crud

router = APIRouter(
    prefix="/api/track",
)

@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def create_track(_track: TrackCreate,
                 current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    track_crud.track_create(db, _track, current_user)


@router.patch("/update", status_code=status.HTTP_204_NO_CONTENT)
def update_track(track: TrackCreate,
                 current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    if (current_user.id != track.user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    track = track_crud.track_update(db, track, current_user)
    return track


# track 특정 이름 포함 모두 검색 : ex) `건강` 검색-> `건강한 식단트랙`  (단 두글자 이상 검색해야함)
@router.get("/search/{track_name}", response_model=TrackList, status_code=200)
def get_track_by_name(track_name: str, db: Session = Depends(get_db),
                      page: int = 0, size: int = 10):
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
