from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from domain.user.user_crud import pwd_context
from domain.user.user_router import get_current_user
from domain.user.user_schema import Rank
from main import app
from database import Base, get_db
from models import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=TestingSessionLocal().bind)
    Base.metadata.create_all(bind=TestingSessionLocal().bind)
    yield
    # 트랜잭션 종료 후 DB 초기화 (테이블 삭제)
    Base.metadata.drop_all(bind=TestingSessionLocal().bind)


# pytest fixture로 유저 생성 후 테스트가 끝난 뒤 삭제
@pytest.fixture(scope="function")
def setup_user():
    global db_user
    db = TestingSessionLocal()
    try:
        db_user = User(
            name="test_user",
            username="test_username",
            nickname="test_nickname",
            email="test_user@example.com",
            cellphone="010-1234-5678",
            password=pwd_context.hash("password123"),
            gender=True,
            rank=Rank.BRONZE.value,
            birth=datetime.strptime("2000-01-01", "%Y-%m-%d").date(),
            create_date=datetime.now()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # 유저 객체를 반환하여 테스트에서 사용
        yield db_user

    finally:
        # 트랜잭션 롤백 및 유저 삭제
        db.delete(db_user)
        db.commit()
        db.close()

@pytest.fixture(scope="function")
def client(setup_user):
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    # 의존성 주입 재정의
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: setup_user

    with TestClient(app) as client:
        yield client

# 가짜 유저 생성 테스트
def test_create_user():
    db = TestingSessionLocal()
    db_user = User(
        name="1",
        username="1",
        nickname="1",
        email="1@example.com",
        cellphone="010-2315-7195",
        password=pwd_context.hash("1"),
        gender=True,
        rank=Rank.BRONZE.value,
        birth=datetime.strptime("2000-01-01", "%Y-%m-%d").date(),
        create_date=datetime.now()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    assert db_user.id is not None  # 유저가 생성되었는지 확인

    db.delete(db_user)
    db.commit()
    db.close()


@pytest.fixture(scope="function")
def session():
    db = TestingSessionLocal()
    transaction = db.begin()  # 트랜잭션 시작
    yield db  # 테스트 수행
    transaction.rollback()  # 트랜잭션 롤백 후 데이터 제거
    db.close()  # 세션 닫기

