import firebase_admin
from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import credentials, messaging
from sqlalchemy.exc import NoResultFound

from sqlalchemy.orm import Session
from starlette import status
from starlette.config import Config
from starlette.responses import JSONResponse

from domain.group.group_schema import GroupCreate, GroupSchema
from domain.group import group_crud
from domain.user import user_router
from models import Group, User, Track
from database import get_db
from pyfcm import FCMNotification

router = APIRouter(
    prefix="/api/track/group",
)


# fcm_api_key = config('FIREBASE_FCM_API_KEY')
# push_service = FCMNotification(api_key=fcm_api_key)

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