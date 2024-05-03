from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./myapi.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# autocommit=False로 설정하면 데이터를 변경했을때 commit 이라는 사인을 주어야만 실제 저장이 된다.
# 데이터를 잘못 저장했을 경우 rollback 사인으로 되돌리는 것이 가능
# autocommit=True로 설정할 경우에는 commit이라는 사인이 없어도 즉시 데이터베이스에 변경사항이 적용됨
# rollback 도 불가능
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
naming_convertion = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convertion)


# db 세션 객체를 리턴하는 제너레이터인 get_db함수 추가
# db를 안전하게 열고 닫을 수 있음

def get_db():
    db = SessionLocal()
    try:
        yield db  # 컨넥션 풀에 db세션 반환
    finally:
        db.close() # 데이터 베이스 자원을 해제하고 연결을 안전하게 닫음