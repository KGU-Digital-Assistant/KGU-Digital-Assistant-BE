from typing import List

from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from sqlalchemy.sql.functions import current_user
from starlette import status
from datetime import datetime, timedelta
from database import get_db
from domain.user import user_router, user_crud
from domain.user.user_router import get_current_user
from models import Track, User, TrackRoutine
from domain.group import group_crud, group_schema
from domain.track_routine import track_routine_crud,track_routine_schema
from domain.track.track_schema import TrackCreate, TrackResponse, TrackSchema, TrackList
from domain.track import track_crud, track_schema

router = APIRouter(
    prefix="/track",
)


@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def create_track(current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    """
    트랙 생성,
    기능명세서 p.19 1번 누를때
    """
    track = track_crud.track_create(db, current_user)
    return {"track_id": track.id}


@router.patch("/create/next", status_code=status.HTTP_204_NO_CONTENT)
def update_track(_track_id: int,
                 _track: TrackCreate,
                 cheating_cnt: int,
                 _current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    """
    트랙 생성 하기 누를 때 적용 됨, 기능 명세서 p.20
    1. 트랙 내용 채우기
    2. 그룹 생성
    """
    track = track_crud.track_update(db, _track_id, _current_user, _track, cheating_cnt)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    group = group_crud.create_group(db, track, _current_user.id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="group not found")
    return track


@router.patch("/update/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_track(track_id: int,
                 _track: TrackCreate,
                 cheating_cnt: int,
                 _current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if track.user_id != _current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    track_crud.track_update(db, track_id, _current_user, _track, cheating_cnt)


@router.post("{track_id}/change/alone-to-multiple", status_code=status.HTTP_204_NO_CONTENT)
def change_track(track_id: int,
                 _current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    """
    change: 개인트랙 -> 공유트랙,
    개인트랙을 하나 복사해서 하나 더 만드는 로직
    """
    track = track_crud.get_track_by_id(db, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if track.user_id != _current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="트랙 권한이 없음")

    new_track = track_crud.copy_multiple_track(db, track, _current_user.id)
    return new_track


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


#@router.get("/get/{track_id}", response_model=TrackSchema, status_code=200)
#def get_track_by_id(track_id: int, db: Session = Depends(get_db)):
#    return track_crud.get_track_by_id(db=db, track_id=track_id)


###################################################

#@router.get("/get/{user_id}", response_model=track_schema.Track_schema)
#def get_Track_id(user_id: int, db: Session = Depends(get_db)):
#    tracks = track_crud.get_Track_byuser_id(db, user_id=user_id)
#    if tracks is None:
#        raise HTTPException(status_code=404, detail="Track not found")
#    return tracks

@router.get("/get/mytracks", response_model=List[track_schema.Track_list_get_schema])
def get_Track_mylist(current_user: User = Depends(get_current_user), db:Session = Depends(get_db)):
    """
    보유 트랙 정보 표시 : 19page 2-3번(개인트랙) *보류*
     - 입력예시 :
     - 출력 : [TrackRoutin.id, TrackRoutine.name, using:(True,False)]
     - 빈출력 = track 없음
     - Track.start_day가 느린순으로 출력
    """
    tracklist = track_crud.get_Track_mine_title_all(db,user_id=current_user.id)
    if tracklist is None:
        raise HTTPException(status_code=404, detail="Track not found")
        return 0
    return tracklist

@router.get("/get/sharetracks", response_model=List[track_schema.Track_list_get_schema])
def get_Track_sharelist(current_user: User = Depends(get_current_user), db:Session = Depends(get_db)):
    """
    보유 트랙 정보 표시 : 19page 2-3번(공유트랙)  *보류*
     - 입력예시 :
     - 출력 : [TrackRoutin.id, TrackRoutine.name, using:(True,False)]
     - 빈출력 = track 없음
     - Track.start_day가 느린순으로 출력
    """
    tracklist = track_crud.get_Track_share_title_all(db,user_id=current_user.id)
    if tracklist is None:
        raise HTTPException(status_code=404, detail="Track not found")
        return 0
    return tracklist

@router.get("/get/alltracks", response_model=List[track_schema.Track_list_get_schema])
def get_track_all_list(current_user: User = Depends(get_current_user), db:Session = Depends(get_db)):
    """
    보유 트랙 정보 표시 : 19page 2-3번(초대트랙)(만들어놓은 트랙 + 초대받아 시작한트랙)
     - 입력예시 :
     - 출력 : [TrackRoutin.id, TrackRoutine.name, using:(True,False)]
     - 빈출력 = track 없음
     - Track.start_day가 느린순으로 출력
    """
    tracklist = track_crud.get_track_title_all(db,user_id=current_user.id)
    if tracklist is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return tracklist


@router.get("/get/{track_id}/Info", response_model=track_schema.Track_get_Info)
def get_Track_Info(track_id: int, current_user: User = Depends(get_current_user), db:Session=Depends(get_db)):
    """
    트랙상세보기 : 23page 0번
     - 입력예시 : track_id = 2
     - 출력 : Track.name, User.name, Group.start_date, Group.finish_date, Track.duration, Count(트랙사용중인사람수), [TrackRoutin(반복)],[TrackRoutin(단독)]
    """
    tracks= track_crud.get_Track_bytrack_id(db,track_id=track_id)
    if tracks is None:
        raise HTTPException(status_code=404, detail="Track not found")
    username=user_crud.get_User_name(db,id=tracks.user_id)
    today=datetime.utcnow().date()+ timedelta(hours=9)
    #트랙을 공유한 횟수
    count = tracks.count
    #그룹 정보여부
    group_one=group_crud.get_group_by_date_track_id_in_part(db,user_id=current_user.id,date=today,track_id=track_id)
    if group_one and group_one is not None:
        group, cheating_count, user_id2, flag, finish_date =group_one
        group_startday = group.start_day
        group_finishday = group.finish_day
        real_finishday=finish_date
    else:
        group_startday=None
        group_finishday=None
    # calorie 계산
    calorie = track_routine_crud.get_calorie_average(track_id=track_id,db=db)
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
        "track_start_day": tracks.start_date,
        "track_finish_day": tracks.finish_date,
        "group_start_day": group_startday,
        "group_finish_day": group_finishday,
        "real_finish_day": real_finishday,
        "duration": tracks.duration,
        "caloire" : calorie,
        "count" : count,
        "repeatroutin": repeat,
        "soloroutin": solo
    }

#@router.post("/post/{user_id})", response_model=track_schema.Track_create_schema)##회원일경우
#def post_Track(user_id: int, track: track_schema.Track_create_schema,db:Session=Depends(get_db)):
#    db_track = Track(
#        user_id=user_id,
#        name=track.name,
#        water=track.water,
#        coffee=track.coffee,
#        alcohol=track.alcohol,
#        duration=track.duration,
#        track_yn=True,
#        cheating_count=track.cheating_count
#    )
#    db.add(db_track)
#    db.commit()
#    db.refresh(db_track)
#
#    for routine in track.routines:
#        db_routine= TrackRoutine(
#            track_id=db_track.id,
#            title=routine.title,
#            food=routine.food,
#            calorie=routine.calorie,
#            week=routine.week,
#            time=routine.time,
#            repeat=routine.repeat
#        )
#        db.add(db_routine)
#
#    db.commit()
#    db.refresh(db_track)


