import firebase_admin
from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import credentials, messaging
from sqlalchemy.exc import NoResultFound
from domain.group import group_schema, group_crud
from sqlalchemy.orm import Session
from starlette import status
from starlette.config import Config
from starlette.responses import JSONResponse
from domain.group.group_schema import GroupCreate, GroupSchema, GroupDate, GroupStatus
from datetime import datetime, timedelta, date
from domain.meal_hour import meal_hour_crud
from domain.meal_day import meal_day_crud
from domain.user import user_crud
from domain.user.user_router import get_current_user
from domain.track_routine import track_routine_crud
from domain.track import track_crud
from domain.group import group_crud
from domain.user import user_router
from models import Group, User, Track, MealDay
from database import get_db
from pyfcm import FCMNotification

import schedule

router = APIRouter(
    prefix="/track/group",
)


# fcm_api_key = config('FIREBASE_FCM_API_KEY')
# push_service = FCMNotification(api_key=fcm_api_key)

@router.get("/test")
def update_group_status(db: Session = Depends(get_db)):
    """
    매일 끝난 그룹이 있는지 확인
    """
    group_crud.is_finished(db=db)
    return {"status": "ok"}

# 매일 한 번씩 실행.
schedule.every().day.at("00:00").do(update_group_status)


# @router.post("/append")
# async def add_track(user_id: int, group_id: int, db: Session = Depends(get_db)):
#     """
#     서버 테스트용
#     """
#     group_crud.create_invitation(db, user_id, group_id)
#     group_crud.accept_invitation(db=db, user_id=user_id, group_id=group_id)


@router.get("/get/my_group")
def get_my_group(current_user: User = Depends(user_router.get_current_user), db: Session = Depends(get_db)):
    group = group_crud.get_group_by_id(db, current_user.cur_group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="현재 참여 중인 그룹 없음."
        )
    return group


# 그룹 생성
# @router.post("/create/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
# def create_track_group(_group: GroupCreate,
#                        track_id: int,
#                        current_user: User = Depends(user_router.get_current_user),
#                        db: Session = Depends(get_db)):
#     track = track_crud.get_track_by_id(track_id=track_id, db=db)
#     if not track:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Track does not exist",
#         )
#
#     if track.user_id != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Unauthorized"
#         )
#
#     group = group_crud.create_group(db=db, _group=_group, track=track, user_id=current_user.id)
#     if not track.share:
#         group_crud.participate_group(db=db, user_id=current_user.id, group_id=group.id)


@router.get("/get/{group_id}", status_code=status.HTTP_200_OK)
def get_group(group_id: int, db: Session = Depends(get_db)):
    return group_crud.get_group_by_id(db=db, group_id=group_id)


@router.get("/get/{group_id}", status_code=status.HTTP_200_OK)


@router.patch("/update/date/{group_id}")
def update_track(group_id: int, date: group_schema.GroupDate, db: Session = Depends(get_db)):
    """
    날짜 수정
    """
    return group_crud.update_group_date(db=db, group_id=group_id, date=date)


@router.post("/invite-me", status_code=status.HTTP_204_NO_CONTENT)
def invite_me(group_id: int,
              current_user: User = Depends(user_router.get_current_user),
              db: Session = Depends(get_db)):
    """
    본인도 트랙에 참여
    """
    group = group_crud.get_group_by_id(db=db, group_id=group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group does not exist",
        )

    if group.status == GroupStatus.STARTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="트랙이 진행중 입니다."
        )

    if group.status == GroupStatus.TERMINATED:
        track = track_crud.get_track_by_id(track_id=group.track_id, db=db)
        group = group_crud.create_group(db, track, current_user.id)

    group.users.append(current_user)
    current_user.cur_group_id = group.id
    db.commit()
    return {"status": "ok"}


# 초대
@router.post("/invite", status_code=status.HTTP_204_NO_CONTENT)
def invite_group(_receive_user_id: int, _group_id: int,
                 current_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    try:
        recv_user = db.query(User).filter(User.id == _receive_user_id).one()
        group = db.query(Group).filter(Group.id == _group_id).one()

        if group.status == GroupStatus.STARTED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="트랙이 진행중 입니다."
            )

        if group.status == GroupStatus.TERMINATED:
            track = track_crud.get_track_by_id(track_id=group.track_id, db=db)
            group = group_crud.create_group(db, track, current_user.id)

        if group.track.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized"
            )

        # 초대 생성
        group_crud.create_invitation(db=db, user_id=recv_user.id, group_id=group.id)

        # 푸시 알림 보내기
        if recv_user.fcm_token:
            message_title = "group Invitation"
            message_body = f"Hello {recv_user.username},\n\nYou have been invited to join the group '{group.name}'."
            message = messaging.Message(
                notification=messaging.Notification(
                    title=message_title,
                    body=message_body,
                ),
                token=recv_user.fcm_token,
            )
            response = messaging.send(message)
            print('Successfully sent message:', response)

        return {"message": f"User {_receive_user_id} has been invited to group {_group_id} and notified."}
    except NoResultFound:
        db.rollback()
        raise HTTPException(status_code=404, detail="User or Group not found")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete/group/user")
def delete_track(cur_user: User = Depends(user_router.get_current_user),
                 db: Session = Depends(get_db)):
    group_crud.delete_group_in_user(cur_user, db)
    return {"message": "User has been deleted."}


@router.post("/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_invitation(group_id: int,
                      respond: group_schema.Respond,
                      current_user: User = Depends(user_router.get_current_user),
                      db: Session = Depends(get_db)):
    try:
        if current_user.cur_group_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="already group in current user, please delete origin group first"
            )
        res = group_crud.accept_invitation(db=db, user_id=current_user.id, group_id=group_id, respond=respond)
        # 사용자와 트랙의 관계 설정
        # user = db.query(User).filter(User.id == user_id).one()
        # group = db.query(Group).filter(Group.id == group_id).one()
        # group.users.append(user)
        # db.commit()

        # return JSONResponse(status_code=200, content={"message": f"User {user_id} has accepted the invitation to Group {group_id}."})
        return {"message": f"User {current_user.name} has accepted the invitation to Track {group_id}."}
    except NoResultFound:
        db.rollback()
        raise HTTPException(status_code=404, detail="Invitation not found or already responded to")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/exit/group/{daytime}", status_code=status.HTTP_204_NO_CONTENT)
def exit_group(daytime: str, current_user: User = Depends(user_router.get_current_user),
               db: Session = Depends(get_db)):
    """
    현재 참여중인 그룹 탈주하기
    입력 : daytiem : 2024-07-01(종료시점날짜) 해당일에 탈퇴므로 해당일부터 기존기간까지 목표칼로리등 변경
    """
    try:
        dates = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    if dates < date.today():
        raise HTTPException(status_code=404, detail="No Input Old date")
    group_crud.exit_group(db=db, user_id=current_user.id, date=dates,group_id=current_user.cur_group_id)



#########################################

@router.get("/get/{daytime}/name_dday", response_model=group_schema.Group_name_dday_schema)
def get_track_name_dday_byDate(daytime: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    해당일 Track 사용시 Track.name, D-day 조회 : 9page 2번
     - 입력예시 : time = 2024-06-01
     - 출력 : Track.name, Dday
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    meal_day = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
    if meal_day is None:
        raise HTTPException(status_code=404, detail="MealDay not found")
    track_name = None
    dday = None
    if meal_day and meal_day.track_id:
        using_track = track_crud.get_Track_bytrack_id(db, track_id=meal_day.track_id)
        if using_track:
            track_name = using_track.name
        group_info = group_crud.get_group_by_date_track_id_in_part(db, user_id=current_user.id, date=date, track_id=meal_day.track_id)
        if group_info and group_info is not None:
            group, cheating_count, user_id2, flag, finish_date =group_info
            dday = (date - group.start_day).days + 1
    return {"name": track_name, "dday":dday} ##name, d-day 열출력

@router.get("/get/{track_id}/{daytime}/name", response_model=group_schema.Group_get_track_name_schema)
def get_track_name_before_startGroup(track_id: int, daytime: str,current_user: User = Depends(get_current_user), db:Session = Depends(get_db)):
    """
    트랙 시작전 사용중이였던 Track.name(old)(사용중~사용예정트랙들) / Track.name(new) 조회 : 23page 1-1번, 23page 1-2번
     - 입력예시 : daytime = 2024-06-01, track_id = 14
     - 출력 : Track.name(old), Track.name(new)
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    Track_willuse = track_crud.get_Track_bytrack_id(db,track_id=track_id)
    if Track_willuse is None:
        raise HTTPException(status_code=404, detail="Track not found")
    finish_date=date +timedelta(days=Track_willuse.duration)
    trackids = group_crud.get_track_id_all_in_date(db,start_date=date,finish_date=finish_date,user_id=current_user.id)
    name_list=[]
    seen_trackname =set() #중복 track_id 확인용
    for track_id_iter in trackids:
        track_info=track_crud.get_Track_bytrack_id(db,track_id=track_id_iter)
        if track_info.name not in seen_trackname:
            name_list.append(track_info.name)
            seen_trackname.add(track_info.name)
    tracknewrow = track_crud.get_Track_bytrack_id(db,track_id=track_id)
    if tracknewrow and tracknewrow.name:
        tracknew = tracknewrow.name
    else:
        tracknew = None

    return {"trackold" : name_list, "tracknew" : tracknew}
    ## 현재사용중인것만 이름표시할 경우
#    date = datetime.utcnow().date() + timedelta(hours=9)
#    mealtoday = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
#    if mealtoday and mealtoday.track_id:
#        trackoldrow=track_crud.get_Track_bytrack_id(db,track_id=mealtoday.track_id)
#        trackold = trackoldrow.name
#    else:
#        trackold= None
#    tracknewrow = track_crud.get_Track_bytrack_id(db,track_id=track_id)
#    if tracknewrow and tracknewrow.name:
#        tracknew = tracknewrow.name
#    else:
#        tracknew = None
#    return {"trackold" : trackold, "tracknew" : tracknew}


@router.post("/start_track/{track_id}/{daytime}", status_code=status.HTTP_204_NO_CONTENT)
def start_track_user_id_track_id(track_id: int, daytime: str, current_user: User = Depends(get_current_user),db: Session= Depends(get_db)):
    """
    트랙 시작하기 (기존 Mealday의 track_id, goal_calorie 변경 -> 기존 group 종료일 변경 -> 새로운 Group의 시작종료일세팅 ->Mealday 정보수정
     - 입력예시 : track_id = 14, daytime : 2024-09-01
     - 출력 : Track.name, User.nickname
       코드 순서 = mealday tbl 없는경우 생성 -> 시작할 트랙 기간 start~finish 날짜 사이에 예정된 트랙있는 경우(but 트
        해당 트랙들에 정해진 mealday값들 초기화 및 참여tbl flag, 종료일 변경 -> 새 group tbl 시작일 종료일 설정
         -> 새 참여 tbl flag, 종료일 설정 -> mealday에 new_track정보 입력
      트랙시작시점에 group의 state = started, participtaion의 flag는 finish_Date 도달시 false로 변경, 모두 false가 돼면 해당일에 group state = terminated 로 변경

    - 진행중인 트랙이 있을 경우 409 에러 띄움.
    - /exit/group/{daytime} 그룹 탈주하기 api 실행 후 하면 됨.
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    if date.weekday() != 0:
        raise HTTPException(status_code=401, detail="Start only on Monday")

    if current_user.cur_group_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 진행중인 트랙이 있음"
        )

    Track_willuse = track_crud.get_Track_bytrack_id(db,track_id=track_id)
    if Track_willuse is None:
        raise HTTPException(status_code=404, detail="Track not found")
    Group_willuse = group_crud.get_Group_bytrack_id_state_ready(db, track_id=track_id)
    if Group_willuse is None:
        db_groupnew = Group(
            track_id = track_id,
            creator = Track_willuse.user_id,
            name = meal_hour_crud.create_file_name(user_id=current_user.id),
            start_day = None,
            finish_day = None,
            status = GroupStatus.READY
        )
        db.add(db_groupnew)
        db.commit()
        db.refresh(db_groupnew)
        Group_willuse = db_groupnew
    if Track_willuse.alone == True: # 개인 트랙일 경우
        group_crud.add_participation(db,user_id=current_user.id,group_id=Group_willuse.id,cheating_count=Track_willuse.cheating_count)
        group_crud.update_group_mealday_pushing_start(db,user_id=current_user.id, track_id=track_id, date=date, group_id= Group_willuse.id,duration=Track_willuse.duration)
    if Track_willuse.alone == False: # 개인 트랙이 아닐 경우
        group_crud.update_group_mealday_pushing_start(db,user_id=current_user.id, track_id=track_id, date=date, group_id= Group_willuse.id, duration=Track_willuse.duration)
    nickname = user_crud.get_User_nickname(db,id=current_user.id)
    return {"trackname" : Track_willuse.name, "nickname" : nickname}