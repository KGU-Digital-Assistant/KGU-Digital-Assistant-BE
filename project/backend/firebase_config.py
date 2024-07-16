import firebase_admin
from firebase_admin import credentials,storage, messaging
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from models import User, MealDay
from database import engine, get_db
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException

# 환경 변수에서 서비스 계정 키 파일 경로 읽기
cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if not cred_path:
    raise ValueError("The GOOGLE_APPLICATION_CREDENTIALS environment variable is not set or the file path is incorrect.")

print(f"Using credentials from: {cred_path}")

# Firebase Admin SDK 초기화
cred = credentials.Certificate(cred_path)
default_app = firebase_admin.initialize_app(cred, {'storageBucket': 'ieat-76bd6.appspot.com'})

bucket = storage.bucket()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#사용자 FCM 토큰 얻기
def get_user_fcm_token(user_id):
    db: Session=SessionLocal()
    users=db.query(User).filter(User.id == user_id).first()
    db.close()
    if users is None:
        return None
    return users

#FCM 알림 보내는 함수
def send_fcm_notification(user_id, title, body):
    fcm_token = get_user_fcm_token(user_id)

    if fcm_token:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,
        )
        try:
            response = messaging.send(message)
            print('Success sent msg:', response)
        except Exception as e:
            print('Fail send msg:',e)

def send_fcm_data_noti(user_id, title, body,data):
    fcm_token = get_user_fcm_token(user_id)

    if fcm_token:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data,
            token=fcm_token,
        )
        try:
            response = messaging.send(message)
            print('Success sent msg:', response)
        except Exception as e:
            print('Fail send msg:',e)

