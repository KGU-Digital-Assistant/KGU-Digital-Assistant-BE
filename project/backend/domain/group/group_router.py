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
def get_Comment_date_user_id_text(user_id: int, daytime: str, db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    groups = group_crud.get_Group_bydate(db, user_id=user_id, date=date)
    if groups is None:
        raise HTTPException(status_code=404, detail="Comments not found")
    name=groups.name
    dday=groups.finish_day - date
    return {"name": name, "dday":dday} ##name, d-day 열출력

@router.get("/get/{track_id}/name", response_model=group_schema.Group_get_track_name_schema)
def get_track_name_before_startGroup(user_id: int, track_id, db:Session = Depends(get_db)):
    date = datetime.utcnow().date()
    mealtoday = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if mealtoday.track_id:
        trackoldrow=track_crud.get_Track_bytrack_id(db,track_id=mealtoday.track_id)
        trackold = trackoldrow.name
    else:
        trackold= None
    tracknewrow = track_crud.get_Track_bytrack_id(db,track_id=track_id)
    tracknew = tracknewrow.name
    return {"trackold" : trackold, "tracknew" : tracknew}


@router.post("/start_track/{user_id}/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def start_track_user_id_track_id(user_id: int, track_id: int, db: Session= Depends(get_db)):
    current_date= datetime.utcnow().date()
    current_datetime=datetime.utcnow()
    Track_willuse = track_crud.get_Track_bytrack_id(db,track_id=track_id)
    if Track_willuse is None:
        raise HTTPException(status_code=404, detail="Track not found")

    groups = Group(   ## 기존 그룹에서 시작하기전 해당 내용복사하여 다시 트랙사용할때 쓸수잇도록함
        track_id=track_id,
        user_id=user_id,
        start_day=current_date,
        finish_day=current_date + timedelta(days=Track_willuse.duration)
    )
    db.add(groups)
    db.commit()
    db.refresh(groups)

    date1 = current_datetime
    mealtoday= meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=current_date)
    if mealtoday and mealtoday.track_id and mealtoday.track_id >=1:
        group_past= group_crud.get_Group_byuserid_track_id_bystartfinishday(db, user_id=user_id,track_id=mealtoday.track_id, date=current_date)
        while date1 <= group_past.finish_day: ## 금일 ~ 과거 track 날짜까지 track_id, goalcalorie 초기화 // 트랙중도변경시
            date0=date1.date()
            mealold = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date0)
            if mealold:
                mealold.track_id=None
                mealold.goalcalorie=0.0
                db.add(mealold)
                db.commit()
                db.refresh(mealold)
            date1 += timedelta(days=1)
        group_past.finish_day = current_date - timedelta(days=1)
        db.add(group_past)
        db.commit()
        db.refresh(group_past) ## 중도포기한 트랙종료시점 작성

    date2 = current_datetime
    while date2 <= groups.finish_day:
        date3=date2.date()
        mealnew=meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date3)
        if mealnew:
            mealnew.track_id=track_id
            mealnew.goalcalorie=Track_willuse.goal_calorie
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
                goalcalorie=Track_willuse.goal_calorie,
                nowcalorie=0.0,
                gb_carb=None,
                gb_protein=None,
                gb_fat=None,
                date=date3,
                track_id=track_id  ## 트랙 user사용중일때 안할때 이거 변경해야할거같은데
            )
            db.add(new_meal)
            db.commit()
            db.refresh(new_meal)
        date2 += timedelta(days=1)

        nickname = user_crud.get_User_nickname(db,id=user_id)
    return {"trackname" : Track_willuse.name, "nickname" : nickname}