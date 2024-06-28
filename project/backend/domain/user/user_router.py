from typing import List

import requests

from datetime import timedelta, datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.testing.plugin.plugin_base import logging
from starlette import status
from starlette.responses import RedirectResponse
from starlette.config import Config
from database import get_db
from domain.user import user_crud, user_schema
from domain.user.user_crud import pwd_context
from models import User
from domain.user.my_oauth2 import OAuth2PasswordRequestFormWithEmail, OAuth2PasswordBearerWithEmail

config = Config('.env')
KAKAO_CLIENT_ID = config('KAKAO_CLIENT_ID')
ACCESS_TOKEN_EXPIRE_MINUTES = int(config('ACCESS_TOKEN_EXPIRE_MINUTES'))
SECRET_KEY = config('SECRET_KEY')
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")

router = APIRouter(
    prefix="/api/user",
)

# 로그인
@router.post("/login", response_model=user_schema.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                           db: Session = Depends(get_db)):

    # check user and password
    # username -> email
    user = user_crud.get_user_by_email(db, form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client_id or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # make access token
    data = {
        "sub": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.email
    }


# 회원가입
@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def user_create(_user_create: user_schema.UserCreate, db: Session = Depends(get_db)):
    user = user_crud.get_existing_user(db, user_create=_user_create)
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="이미 존재하는 사용자입니다.")
    user_crud.create_user(db=db, user_create=_user_create)


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = user_crud.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user


# 회원 업데이트
@router.patch("/update", response_model=user_schema.UserUpdate)
def user_update(user_update: user_schema.UserUpdate,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    user = user_crud.update_user(db, user_id=current_user.id, user_update=user_update)
    if not user:
        raise HTTPException(status_code=404, detail="사용자가 존재하지 않습니다.")
    return user


# 회원 탈퇴
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def user_delete(current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=404,
                            detail="사용자가 존재하지 않습니다.")
    db.delete(current_user)
    db.commit()
    return {"ok": True}


# 인가 코드 받기
@router.get("/kakao/code")
async def kakao_login_connect():
    redirect_uri = "http://localhost:8000/api/user/login/kakao/callback"  # 카카오 로그인 후 리디렉트될 URL
    return RedirectResponse(
        url=f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )


@router.get("/kakao/code/login")
async def kakao_login():
    redirect_uri = "http://localhost:8000/api/user/login/kakao"  # 카카오 로그인 후 리디렉트될 URL
    return RedirectResponse(
        url=f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )


@router.get("/login/kakao/callback")
async def kakao_callback(code: str, db: Session = Depends(get_db)):
    redirect_uri = "http://localhost:8000/api/user/login/kakao/callback"
    token_response = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "code": code,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token_response_data = token_response.json()
    access_token = token_response_data.get("access_token")

    user_response = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user_data = user_response.json()

    # 일단 이름으로 비교하는데 나중에 사업자등록 후 카카오 비즈 신청할 예정
    user_name = user_data['properties']['nickname']
    # user_email = user_data.get('kakao_account', {}).get('email', '')
    external_id = user_data['id']

    if user_crud.get_user_by_external_id(db, external_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이미 연동되었습니다.",
        )

    if not user_crud.update_external_id(db, external_id, user_name):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="회원가입부터 하세용"
        )

    # 사용자 정보를 데이터베이스에 저장하거나 업데이트
    # user_info = {
    #     "name": user_data['properties']['nickname'],
    #     "email": user_data.get('kakao_account', {}).get('email', ''),
    #     "external_id": user_data['id'],
    #     "auth_type": "kakao"
    # }
    # user_crud.create_or_update_user(db, user_info)  # 사용자 CRUD 로직 적용

    return {"token": access_token, "user_data": external_id}


# 로그인하기 with KAKAO **
@router.get("/login/kakao")
def login_with_kakao(code: str, db: Session = Depends(get_db)):
    # logging.info("hi")
    redirect_uri = "http://localhost:8000/api/user/login/kakao"
    token_response = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "code": code,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token_response_data = token_response.json()
    access_token = token_response_data.get("access_token")

    user_response = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user_data = user_response.json()

    external_id = user_data['id']

    # 외부 ID로 사용자 조회
    user = user_crud.get_user_by_external_id(db, external_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="카카오 계정이 연동되지 않은 사용자입니다.",
        )

    # 액세스 토큰 생성
    data = {
        "sub": user.username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username
    }


# username으로 검색해서 리스트 반환
# 이거 되는지 확인하기
@router.get("/users/username/{username}", response_model=List[user_schema.UserSchema])
def get_users_by_username(username: str, db: Session = Depends(get_db)):
    users = user_crud.get_users_by_username(db, username)
    if not users:
        raise HTTPException(status_code=404, detail="Users not found")
    return users


# user id로 1명 반환
@router.get("/users/{user_id}", response_model=user_schema.UserSchema)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return user_crud.get_user(db=db, user_id=user_id)


# 토큰 발급받아 저장하기 !!
@router.post("/register")
async def register_token(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    token = data.get('token')
    user_id = data.get('user_id')

    if not token or not user_id:
        raise HTTPException(status_code=400, detail="Token and user_id required")

    try:
        user = db.query(User).filter(User.id == user_id).one()
        user.fcm_token = token
        db.commit()
        return {"message": "Token registered successfully"}
    except NoResultFound:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))