import secrets
import ssl
from typing import List, Dict, Optional, Tuple
from urllib import parse

import aiohttp
import certifi
import requests

from datetime import timedelta, datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Form, Header
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.testing.plugin.plugin_base import logging
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from starlette.config import Config
from database import get_db
from domain.mentor import mentor_crud
from domain.meal_hour import meal_hour_crud
from domain.user import user_crud, user_schema
from domain.user.user_crud import pwd_context
from models import User
from domain.user.my_oauth2 import OAuth2PasswordRequestFormWithEmail, OAuth2PasswordBearerWithEmail
from exceptions import InvalidAuthorizationCode, InvalidToken
import uuid
from firebase_config import bucket

config = Config('.env')

KAKAO_OAUTH_URL = "https://kauth.kakao.com/oauth"
KAKAO_CLIENT_ID = config('KAKAO_CLIENT_ID')
KAKAO_CLIENT_SECRET = config('KAKAO_CLIENT_SECRET')

KAKAO_REDIRECT_URI = config('KAKAO_REDIRECT_URI')
KAKAO_API_HOST = "https://kapi.kakao.com"
KAKAO_USER_ME_ENDPOINT = "/v2/user/me"
STATE = secrets.token_urlsafe(32)

_verify_uri = "https://kapi.kakao.com/v1/user/access_token_info"

ACCESS_TOKEN_EXPIRE_MINUTES = int(config('ACCESS_TOKEN_EXPIRE_MINUTES'))
REDIRECT_URI = config('REDIRECT_URI')
SECRET_KEY = config('SECRET_KEY')
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

router = APIRouter(
    prefix="/user",
)

# 기존 유저와의 연동을 잘 해봐야할듯
# 카카오 유저랑 기존 유저랑 따로 만들기?
# 가입 타입으로 access_token을 어떻게 할지 고민하기
# state 는 빼자
# 토큰 유효기간 지났는지 확인


# 로그인
@router.post("/login", response_model=user_schema.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                           db: Session = Depends(get_db)):
    # check user and password

    user = user_crud.get_user_by_username(db, form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client_id or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # make access token
    data = {
        "sub": user.username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    user_crud.update_external_id(db, user.id, None, None)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "user_id": user.id,
        "nickname": user.nickname
    }


@router.post("/create/test")
def test(_user_create: user_schema.UserCreate, db: Session = Depends(get_db)):
    user = user_crud.create_user(db=db, user_create=_user_create)
    return {"user_id": user.id, "user_username": user.username}

# 회원가입
@router.post("/create")
def user_create(_user_create: user_schema.UserCreate, db: Session = Depends(get_db)):
    nickname_user = user_crud.get_user_by_nickname(db, user_create=_user_create)
    if nickname_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "닉네임 중복",
                "error_code": 2,
            }
        )
    email_user = user_crud.get_user_by_email(db, email=_user_create.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "이메일 중복",
                "error_code": 3,
            }
        )
    cellphone_user = user_crud.get_user_by_cellphone(db, _user_create.cellphone)
    if cellphone_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "휴대폰 중복",
                "error_code": 4,
            }
        )

    user = user_crud.create_user(db=db, user_create=_user_create)
    return {"user_id": user.id, "user_username": user.username}


def get_authorization_token(authorization: str = Header(...)) -> str:
    """
    access or refresh token을 받기 위한 예제용 Depends 용 함수
    """
    scheme, _, param = authorization.partition(" ")
    if not authorization or scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return param


@router.post("/username/valid/{username}")
def username_valid(username: str, db: Session = Depends(get_db)):
    user = user_crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "아이디 중복",
                "error_code": 1,
            },
        )
    return {"status": "ok"}


@router.post("/register/fcm-token")
def register_fcm_token(_fcm_token: str, _user_name: str, db: Session = Depends(get_db)):
    """
    fcm 토큰을 클라이언트(프론트)에서 발급받아서 서버에 저장
    회원가입하고 바로 해줘야함
    """

    user = user_crud.save_fcm_token(db, _user_name, _fcm_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user is not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"status": "ok"}



def extract_tokens(authorization: str = Header(...)):
    parts = authorization.split()

    if len(parts) == 2:
        return None, None

    if len(parts) != 6 or parts[0].lower() != "bearer" or parts[2].lower() != "bearer" or parts[4].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[3], parts[5]


async def refresh_access_token(refresh_token: str) -> Dict:
    tokens = await _request_post_to(
        url=f"{KAKAO_OAUTH_URL}/token",
        payload={
            "client_id": KAKAO_CLIENT_ID,
            "client_secret": KAKAO_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    if tokens is None:
        raise InvalidToken
    return tokens


# def get_current_user(token: str = Depends(oauth2_scheme),
#                      db: Session = Depends(get_db)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     user = user_crud.get_user_by_email(db, email)
#     if user is None:
#         raise credentials_exception
#     return user


def verify_local_token(local_token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(local_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
    except JWTError:
        return credentials_exception


def verify_kakao_token(kakao_token: str):
    url = "https://kapi.kakao.com/v1/user/access_token_info"
    headers = {"Authorization": f"Bearer {kakao_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def get_current_user(token: str = Depends(oauth2_scheme),
                    db: Session = Depends(get_db)):
    # 로컬 토큰 검증
    username = verify_local_token(token)
    if username:
        return user_crud.get_user_by_username(db, username)


    # 카카오 토큰 검증 (로컬 토큰이 아니라면)
    kakao_user_info = verify_kakao_token(token)
    if kakao_user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="try refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_crud.get_user_by_cellphone(db, kakao_user_info.get("phone_number"))
    return user


# 회원 업데이트
@router.patch("/update", response_model=user_schema.UserUpdate)
def user_update(_user_update: user_schema.UserUpdate,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    user = user_crud.update_user(db, user_id=current_user.id, user_update=_user_update)
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


# 인가 코드 받기 -> 인가 코드는 FrontEnd 에서 받아옴 -> 그냥 내가 받아도 될듯
@router.get("/kakao/code")
async def kakao_login_connect():
    return RedirectResponse(
        url=f"https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=${KAKAO_CLIENT_ID}&redirect_uri=${KAKAO_REDIRECT_URI}&state=${STATE}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )


#
#
# @router.get("/kakao/code/login")
# async def kakao_login():
#     redirect_uri = "http://localhost:8000/api/user/login/kakao"  # 카카오 로그인 후 리디렉트될 URL
#     return RedirectResponse(
#         url=f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code",
#         status_code=status.HTTP_307_TEMPORARY_REDIRECT
#     )

# 인가코드가 아닌 토큰이 들어올 것임
# axios.get('http://your-api-endpoint/user', {
#   headers: {
#     'Authorization': `Bearer ${accessToken}`
#   }
# })


async def is_authenticated(access_token: str) -> bool:
    """
    토큰 유효성 검사
    """
    headers = {_header_name: f"{_header_type} {access_token}"}
    res = await _request_get_to(
        url=_verify_uri,
        headers=headers,
    )
    return res is not None

async def login_required(
        access_token: str = Depends(get_authorization_token),
):
    """
    토큰 header 에서 가져오고,
    토큰 인증 된건지 확인
    """
    if not await is_authenticated(access_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def get_oauth_login_url(state: str) -> str:
    """
    인가 코드 받기
    """
    params = {
        "response_type": "code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "state": state
    }
    query_param = parse.urlencode(params, doseq=True)

    return f"{KAKAO_OAUTH_URL}/authorize?{query_param}"


@router.get("/create_day")
def create_day(current_user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """
    회원가입 한지 몇일 째 인지 반환
    """
    days = user_crud.get_create_day(db, current_user.id)
    return {"days": days}


@router.get("/kakao/login")
async def login():
    state = secrets.token_urlsafe(32)
    login_url = get_oauth_login_url(state)
    return RedirectResponse(login_url)


@router.get("/kakao/get-token")
def kakao_get_token(
        code: str = Form(...),
        client_id: str = Form(default=KAKAO_CLIENT_ID),
        client_secret: str = Form(default=KAKAO_CLIENT_SECRET),
        redirect_uri: str = Form(default=KAKAO_REDIRECT_URI),
        state: str = None
):
    """
    토큰 발급
    """
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
        "state": state
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(f"{KAKAO_OAUTH_URL}/token", data=data, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to get access token")

    token_info = response.json()
    return JSONResponse(content=token_info)


def _get_connector_for_ssl() -> aiohttp.TCPConnector:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    return aiohttp.TCPConnector(ssl=ssl_context)


async def _request_get_to(url, headers=None) -> Optional[Dict]:
    conn = _get_connector_for_ssl()
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(url, headers=headers) as resp:
            return None if resp.status != 200 else await resp.json()


async def _request_post_to(url, payload=None) -> Optional[Dict]:
    conn = _get_connector_for_ssl()
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.post(url, data=payload) as resp:
            return None if resp.status != 200 else await resp.json()


async def get_tokens(code: str, state: str) -> Dict:
    tokens = await _request_post_to(
        url=f"{KAKAO_OAUTH_URL}/token",
        payload={
            "client_id": KAKAO_CLIENT_ID,
            "client_secret": KAKAO_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "state": state,
        },
    )
    if tokens is None:
        raise InvalidAuthorizationCode

    if tokens.get("access_token") is None or tokens.get("refresh_token") is None:
        raise InvalidAuthorizationCode

    return tokens


@router.get("/kakao/callback")
async def kakao_callback(code: str, state: Optional[str] = None,
                         db: Session = Depends(get_db)):
    token_response = await get_tokens(
        code=code,
        state=state
    )

    access_token = token_response.get("access_token")
    await login_required(access_token)  # 토큰 검증
    user_info = await get_user_info(access_token)  # 다른 함수로 빼기

    external_id = user_info.get("id")
    user_name = user_info.get("nickname")
    user_email = user_info.get("kakao_account", {}).get("email")
    user_phone = user_info.get("kakao_account", {}).get("phone_number")
    user_gender = user_info.get("kakao_account", {}).get("gender")  # 성별 정보 추가

    # 같은 이메일 uesr가 이미 있고 연동되어 있을 경우 경우 -> 로그인
    # 같은 이메일 user가 있지만 연동 안되어 있을 경우 -> external_id 쓰고 로그인
    # 같은 이메일 user가 없을 경우 -> 회원가입
    user = user_crud.get_user_by_cellphone(db, user_phone)
    if user is None:
        return {
            "success": False,
            "message": "회원 가입 페이지로 이동",
            "user_info": user_info,
            "phone_number": user_phone
        }
    if user.external_id != external_id:
        user_crud.update_external_id(db, external_id=external_id, user_id=user.id, _auth_type="kakao")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": user_info
    }

    # make access token
    # data = {
    #     "sub": user.username,
    #     "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # }
    # local_access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    #
    # return {
    #     "access_token": local_access_token,
    #     "token_type": "bearer",
    #     "username": user.username
    # }

    # access_token = token_response_data.get("access_token")

    # user_response = requests.get(
    #     "https://kapi.kakao.com/v2/user/me",
    #     headers={"Authorization": f"Bearer {access_token}"}
    # )
    # user_data = user_response.json()

    # 일단 이름으로 비교하는데 나중에 사업자등록 후 카카오 비즈 신청할 예정
    # user_name = user_data['properties']['nickname']
    # # user_email = user_data.get('kakao_account', {}).get('email', '')
    # external_id = user_data['id']

    # if user_crud.get_user_by_external_id(db, external_id):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="이미 연동되었습니다.",
    #     )
    #
    # if not user_crud.update_external_id(db, external_id, user_name):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="회원가입부터 하세용"
    #     )

    # 사용자 정보를 데이터베이스에 저장하거나 업데이트
    # user_info = {
    #     "name": user_data['properties']['nickname'],
    #     "email": user_data.get('kakao_account', {}).get('email', ''),
    #     "external_id": user_data['id'],
    #     "auth_type": "kakao"
    # }
    # user_crud.create_or_update_user(db, user_info)  # 사용자 CRUD 로직 적용

    # return {"token": access_token, "user_data": external_id}


# @router.post("/kakao/verify-token")
# def verify_token(token_request: user_schema.TokenRequest):
#     url = "https://kapi.kakao.com/v1/user/access_token_info"
#     headers = {
#         "Authorization": f"Bearer {token_request.access_token}"
#     }
#     response = requests.get(url=url, headers=headers)
#
#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail="Token verification failed")
#
#     token_info = response.json()
#     user_id = token_info.get("id")
#
#     if user_id is None:
#         raise HTTPException(status_code=400, detail="Failed to retrieve user ID")
#
#     return {"user_id": user_id}


@router.post("/kakao/refresh-token")
def refresh(refresh_token: str = Depends(get_authorization_token)):
    """
    토큰이 만료되면 리프레쉬
    """
    token_response = refresh_access_token(refresh_token=refresh_token)

    return {"response": token_response}


_header_name = "Authorization"
_header_type = "Bearer"


async def get_user_info(access_token: str) -> Dict:
    headers = {_header_name: f"{_header_type} {access_token}"}
    user_info = await _request_get_to(url=KAKAO_API_HOST + KAKAO_USER_ME_ENDPOINT, headers=headers)
    if user_info is None:
        return None
    return user_info


@router.get("/kakao/user", dependencies=[Depends(login_required)])
async def get_user(
        access_token: str = Depends(get_authorization_token),
):
    """
    받은 access_token으로
    유저 정보 가져오기
    """
    user_info = await get_user_info(access_token=access_token)
    return {"user": user_info}


# 로그인하기 with KAKAO **
# @router.get("/login/kakao")
# def login_with_kakao(code: str, db: Session = Depends(get_db)):
#     # logging.info("hi")
#     redirect_uri = "http://localhost:8000/api/user/login/kakao"
#     token_response = requests.post(
#         "https://kauth.kakao.com/oauth/token",
#         data={
#             "grant_type": "authorization_code",
#             "client_id": KAKAO_CLIENT_ID,
#             "redirect_uri": redirect_uri,
#             "code": code,
#             "client_secret": KAKAO_CLIENT_SECRET
#         },
#         headers={"Content-Type": "application/x-www-form-urlencoded"}
#     )
#     token_response_data = token_response.json()
#     access_token = token_response_data.get("access_token")
#
#     user_response = requests.get(
#         "https://kapi.kakao.com/v2/user/me",
#         headers={"Authorization": f"Bearer {access_token}"}
#     )
#     user_data = user_response.json()
#
#     external_id = user_data['id']
#
#     # 외부 ID로 사용자 조회
#     user = user_crud.get_user_by_external_id(db, external_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="카카오 계정이 연동되지 않은 사용자입니다.",
#         )
#
#     # 액세스 토큰 생성
#     data = {
#         "sub": user.username,
#         "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     }
#     access_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
#
#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "username": user.username
#     }


# username으로 검색해서 리스트 반환
# 이거 되는지 확인하기
@router.get("/users/username/{username}", response_model=List[user_schema.UserSchema])
def get_users_by_username(username: str, db: Session = Depends(get_db)):
    users = user_crud.get_users_by_username(db, username)
    if not users:
        raise HTTPException(status_code=404, detail="Users not found")
    return users


# user id로 1명 반환
@router.get("/user/info", response_model=user_schema.UserSchema)
def get_user_by_id(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    현재 유저 정보 반환
    """
    return user_crud.get_user(db=db, user_id=current_user.id)


@router.get("/user/setting/info")
def get_user_by_id(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    현재 유저 정보 반환
    """
    user = user_crud.get_user_by_id(db, id=current_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    gym = ''
    mentor_name = ''
    if user.mentor_id:
        mentor = mentor_crud.get_mentor_by_id(db, user.mentor_id)
        gym = mentor.gym
        mentor_info = user_crud.get_user_by_id(db, id=mentor.user_id)
        mentor_name = mentor_info.name

    return {"username": user.username, "name": user.name,
            "gym": gym, "mentor_name": mentor_name}


# fcm 토큰 발급받아 저장하기 !!
@router.post("/register")
async def register_token(request: Request, db: Session = Depends(get_db)):
    """
    fcm token 발급받아서 저장하기 !
    """
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


# 추가적으로 external_id를 받아서 저장하는 코드 필요해보임 ( 기존 아이디와 연동 )


# class ValidateUserMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         db: Session = next(get_db())
#
#         # 특정 URI에 대해서만 미들웨어를 적용
#         if request.url.path not in ["/api/user"]:
#             response = await call_next(request)
#             return response
#
#         # 쿠키에서 카카오 토큰 가져오기
#         kakao_token = request.cookies.get("kakao_token")
#
#         if kakao_token:
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(KAKAO_OAUTH_URL, headers={"Authorization": f"Bearer {kakao_token}"}) as resp:
#                     if resp.status == 200:
#                         user_info = await resp.json()
#                         email = user_info["kakao_account"]["email"]
#                         user = user_crud.get_user_by_email(db, email)
#                         if user:
#                             request.state.user = user
#                             response = await call_next(request)
#                             return response
#                     elif resp.status == 401:
#                         refresh_token = request.cookies.get("kakao_refresh_token")
#                         new_kakao_token = await (refresh_token)
#                         if new_kakao_token:
#                             async with session.get(KAKAO_OAUTH_URL,
#                                                    headers={"Authorization": f"Bearer {new_kakao_token}"}) as new_resp:
#                                 if new_resp.status == 200:
#                                     user_info = await new_resp.json()
#                                     email = user_info["kakao_account"]["email"]
#                                     user = user_crud.get_user_by_email(db, email)
#                                     if user:
#                                         request.state.user = user
#                                         response = await call_next(request)
#                                         response.set_cookie(key="kakao_token", value=new_kakao_token, httponly=True)
#                                         return response
#                         return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
#                                             content={"detail": "Could not validate Kakao token"})
#
#         token = request.headers.get("Authorization")
#         if token is None:
#             return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 content={"detail": "Authorization header missing"})
#
#         token = token.split(" ")[1]
#         try:
#             payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#             email: str = payload.get("sub")
#             if email is None:
#                 raise credentials_exception
#         except JWTError:
#             return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 content={"detail": "Could not validate credentials"})
#
#         user = get_user_by_email(db, email)
#         if user is None:
#             return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "User not found"})
#
#         request.state.user = user
#         response = await call_next(request)
#         return response

###############################################################
## 현빈제작
###############################################################
@router.get("/get/{id}", response_model=user_schema.User)
def get_id_User(id: int, db: Session = Depends(get_db)):
    """

    """
    User = user_crud.get_User(db, id=id)
    if User is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User  ##전체 열 출력


@router.get("/get/rank", response_model=user_schema.UserRank)
def get_id_User_rank(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    유저랭크 조회 : 9page 3번 (현재 보류)
     - 입력예시 : user_id = 1
     - 출력 : user.rank
    """
    rank = user_crud.get_User_rank(db, id=current_user.id)
    if rank is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"rank": rank}  ##rank 열만 출력


@router.get("/get/nickname/mine", response_model=user_schema.Usernickname)
def get_id_User_nickname_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    유저 Nickname 조회 : 11page 1번, 12page 1번
     - 입력예시 : user_id = 1
     - 출력 : user.nickname
    """
    nickname = user_crud.get_User_nickname(db, id=current_user.id)
    if nickname is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"nickname": nickname}  ##nickname 열만 출력

@router.get("/get/{id}/nickname/formentor", response_model=user_schema.Usernickname)
def get_id_User_nickname_mentor(id: int, db: Session = Depends(get_db)):
    """
    유저 Nickname 조회 : 17page 3번
     - 입력예시 : user_id = 1
     - 출력 : user.nickname
    """
    nickname = user_crud.get_User_nickname(db, id=id)
    if nickname is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"nickname": nickname}  ##nickname 열만 출력


@router.get("/get/{id}/name", response_model=user_schema.Username)
def get_id_User(id: int, db: Session = Depends(get_db)):
    """
    유저 name 조회 : 17page 2번
     - 입력예시 : user_id = 1
     - 출력 : user.name
    """
    name = user_crud.get_User_nickname(db, id=id)
    if name is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"name": name}  ##name 열만 출력


@router.post("/upload_profile_picture")
async def upload_profile_picture(current_user: User = Depends(get_current_user), file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # 사용자 조회
        user = user_crud.get_User(db, id=current_user.id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # 고유한 파일 이름 생성
        file_id = meal_hour_crud.create_file_name(user_id=current_user.id)
        blob = bucket.blob(f"profile_pictures/{file_id}")

        # 파일 업로드
        blob.upload_from_file(file.file, content_type=file.content_type)

        # 기존 프로필 사진 삭제
        if user.profile_picture:
            old_blob = bucket.blob(user.profile_picture)
            if old_blob.exists():
                old_blob.delete()

        # 서명된 URL 생성 (URL은 1시간 동안 유효)
        signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))

        # 데이터베이스에 파일 경로와 URL 저장
        user.profile_picture = f"profile_pictures/{file_id}"
        db.commit()

        return {"file_id": file_id, "image_url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_profile_picture")
async def get_profile_picture(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # 사용자 조회
        user = user_crud.get_User(db, id=current_user.id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.profile_picture:
            raise HTTPException(status_code=404, detail="Profile picture not found")

        # 서명된 URL 생성 (URL은 1시간 동안 유효)
        blob = bucket.blob(user.profile_picture)
        signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))

        return {"image_url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


############################## user setting ################################


@router.get("/get")
async def get_user(db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """
    기능명세서 p.26 프로필 수정 시, 기존 정보 불러올 때
    """
    user = user_crud.get_User(db, id=current_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    mentor_name = ""
    mentor = mentor_crud.get_mentor_by_id(db, current_user.mentor_id)
    if mentor:
        _mentor = user_crud.get_user_by_id(db, id=mentor.user_id)
        mentor_name = _mentor.name

    return {
        "profile_picture": user.profile_picture,
        "name": user.name,
        "nickname": user.nickname,
        "mentor_name": mentor_name
    }


@router.patch("/update/profile", response_model=user_schema.UserSchema)
async def profile_update(_user_profile: user_schema.UserProfile,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    user = user_crud.get_user_by_id(db, id=current_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 현재 닉네임을 유지라면 넘기기
    if user.nickname != _user_profile.nickname:
        if user_crud.get_user_by_only_nickname(db, _user_profile.nickname):
            raise HTTPException(status_code=404, detail="Nickname is already taken")

    if user.username == _user_profile.mentor_username:
        raise HTTPException(status_code=404, detail="멘토로 본인을 추가할 순 없습니다.")
    user_crud.update_profile(db=db, profile_user=_user_profile, current_user=current_user)
    return current_user