import firebase_admin
from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import credentials, messaging
from sqlalchemy.exc import NoResultFound
from domain.group import group_schema,group_crud
from sqlalchemy.orm import Session
from starlette import status
from starlette.config import Config
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
from domain.group.group_schema import GroupCreate, GroupSchema
from domain.meal_day import meal_day_crud
from domain.user import user_crud
from domain.track_routine import track_routine_crud
from domain.track import track_crud
from domain.group import group_crud
from domain.user import user_router
from models import Group, User, Track, MealDay
from database import get_db
from pyfcm import FCMNotification

router = APIRouter(
    prefix="/track/group",
)


# fcm_api_key = config('FIREBASE_FCM_API_KEY')
# push_service = FCMNotification(api_key=fcm_api_key)

@router.post("/append")
async def add_track(user_id: int, group_id: int, db: Session = Depends(get_db)):
    group_crud.create_invitation(db, user_id, group_id)
    group_crud.accept_invitation(db=db, user_id=user_id, group_id=group_id)


# 그룹 생성
@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def create_track_group(_group: GroupCreate,
                       track_id: int,
                       current_user: User = Depends(user_router.get_current_user),
                       db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track does not exist",
        )

    if track.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    group_crud.create_group(db=db, _group=_group, track=track, user_id=current_user.id)


@router.get("/get/{group_id}", status_code=status.HTTP_200_OK, response_model=GroupSchema)
def get_group(group_id: int, db: Session = Depends(get_db)):
    return group_crud.get_group_by_id(db=db, group_id=group_id)


# 초대
@router.post("/invite", status_code=status.HTTP_204_NO_CONTENT)
def invite_group(_user_id: int, _group_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == _user_id).one()
        group = db.query(Group).filter(Group.id == _group_id).one()

        # 초대 생성
        group_crud.create_invitation(db=db, user_id=user.id, group_id=group.id)

        # 푸시 알림 보내기
        if user.fcm_token:
            message_title = "group Invitation"
            message_body = f"Hello {user.username},\n\nYou have been invited to join the group '{group.name}'."
            message = messaging.Message(
                notification=messaging.Notification(
                    title=message_title,
                    body=message_body,
                ),
                token=user.fcm_token,
            )
            response = messaging.send(message)
            print('Successfully sent message:', response)

        return {"message": f"User {_user_id} has been invited to group {_group_id} and notified."}
    except NoResultFound:
        db.rollback()
        raise HTTPException(status_code=404, detail="User or Group not found")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_invitation(user_id: int, group_id: int, db: Session = Depends(get_db)):
    try:
        group_crud.accept_invitation(db=db, user_id=user_id, group_id=group_id)

        # 사용자와 트랙의 관계 설정
        # user = db.query(User).filter(User.id == user_id).one()
        # group = db.query(Group).filter(Group.id == group_id).one()
        # group.users.append(user)
        # db.commit()

        # return JSONResponse(status_code=200, content={"message": f"User {user_id} has accepted the invitation to Group {group_id}."})
        return {"message": f"User {user_id} has accepted the invitation to Track {group_id}."}
    except NoResultFound:
        db.rollback()
        raise HTTPException(status_code=404, detail="Invitation not found or already responded to")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

#########################################

@router.get("/get/{user_id}/{daytime}/name_dday", response_model=group_schema.Group_name_dday_schema)
def get_track_name_dday_byDate(user_id: int, daytime: str, db: Session = Depends(get_db)):
    """
    해당일 Track 사용시 Track.name, D-day 조회 : 9page 2번
     - 입력예시 : user_id = 1, time = 2024-06-01
     - 출력 : Track.name, Dday
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    meal_day = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
    if meal_day is None:
        raise HTTPException(status_code=404, detail="MealDay not found")
    track_name = None
    dday = None
    if meal_day and meal_day.track_id:
        using_track = track_crud.get_Track_bytrack_id(db, track_id=meal_day.track_id)
        if using_track:
            track_name = using_track.name
        group_info = group_crud.get_group_by_date_track_id(db, user_id=user_id, date=date, track_id=meal_day.track_id)
        if group_info and group_info is not None:
            group, cheating_count, user_id2 = group_info
            dday = (date - group.start_day).days + 1
    return {"name": track_name, "dday":dday} ##name, d-day 열출력

@router.get("/get/{user_id}/{track_id}/name", response_model=group_schema.Group_get_track_name_schema)
def get_track_name_before_startGroup(user_id: int, track_id, db:Session = Depends(get_db)):
    """
    트랙 시작전 사용중이였던 Track.name(old) / Track.name(new) 조회 : 23page 1-1번, 23page 1-2번
     - 입력예시 : user_id = 1, track_id = 14
     - 출력 : Track.name(old), Track.name(new)
    """
    date = datetime.utcnow().date() + timedelta(hours=9)
    mealtoday = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if mealtoday and mealtoday.track_id:
        trackoldrow=track_crud.get_Track_bytrack_id(db,track_id=mealtoday.track_id)
        trackold = trackoldrow.name
    else:
        trackold= None
    tracknewrow = track_crud.get_Track_bytrack_id(db,track_id=track_id)
    if tracknewrow and tracknewrow.name:
        tracknew = tracknewrow.name
    else:
        tracknew = None
    return {"trackold" : trackold, "tracknew" : tracknew}


@router.post("/start_track/{user_id}/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def start_track_user_id_track_id(user_id: int, track_id: int, db: Session= Depends(get_db)):
    """
    트랙 시작하기 (기존 Mealday의 track_id, goal_calorie 변경 -> 기존 group 종료일 변경 -> 새로운 Group의 시작종료일세팅 ->Mealday 정보수정
     - 입력예시 : user_id = 1, track_id = 14
     - 출력 : Track.name, User.nickname
    """
    Track_willuse = track_crud.get_Track_bytrack_id(db,track_id=track_id)
    if Track_willuse is None:
        raise HTTPException(status_code=404, detail="Track not found")
    if Track_willuse.start_date <= (datetime.utcnow() + timedelta(hours=9)).date():
        return {"detail" : "start_date <= today"}
    date=Track_willuse.start_date
    date1 = date
    ##기존 사용중인 트랙 있을 경우에 해당 Group 종료일변경 및 Mealday의 goalcalorie, track_id 변경
    mealtoday= meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if mealtoday and mealtoday.track_id and mealtoday.track_id >=1:
        group_participation = group_crud.get_group_by_date_track_id(db,user_id=user_id,date=date,track_id=mealtoday.track_id)
        if group_participation is None:
            raise HTTPException(status_code=404, detail="Group not found")
        group, cheating_count, user_id2 = group_participation # 튜플 언패킹(group, participation obj 로 나눔)
        while date1 <= group.finish_day: ## 금일 ~ 과거 track 날짜까지 track_id, goalcalorie 초기화 // 트랙중도변경시
            mealold = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date1)
            if mealold:
                mealold.track_id=None
                mealold.goalcalorie=0.0
                db.add(mealold)
                db.commit()
                db.refresh(mealold)
            date1 += timedelta(days=1)
        group.finish_day = date - timedelta(days=1)
        db.add(group)
        db.commit()
        db.refresh(group) ## 중도포기한 트랙종료시점 작성
    ## 새 트랙의 Group 시작 종료일 설정
    groupnew = group_crud.get_group_date_null_track_id(db, user_id=user_id,track_id=track_id)
    groupnew.start_day = date
    groupnew.finish_day = date + timedelta(days=Track_willuse.duration)
    db.add(groupnew)
    db.commit()
    db.refresh(groupnew)
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

        nickname = user_crud.get_User_nickname(db,id=user_id)
    return {"trackname" : Track_willuse.name, "nickname" : nickname}