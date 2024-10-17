from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from starlette.config import Config
# from models import GroupStatus

config = Config('.env')
SQLALCHEMY_DATABASE_URL = config('SQLALCHEMY_DATABASE_URL')


if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)


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

## 트리거 만들어야함
#1. group내 모든인원이 시작하기를 누를경우(참여 tbl의 flag 전부 true) -> group.state = started
#2. group내 모든인원이 종료될 경우(참여 tbl의 flag 전부 false) -> group.state = terminated(초기는 flag == NOne)ready상태
#3. 참여 tbl 내 finish_date의 날짜에 도달하는경우 -> flag = false > 쓰레드 무기한먹음 aps-scheduler사용

#@event.listens_for(engine, "connect")
#def create_triggers(dbapi_connection, connection_record):
#    cursor = dbapi_connection.cursor()
#    cursor.executescript("""
#    -- 모든 flag가 'started'일 때 Group 테이블의 state를 'started'로 변경
#    CREATE TRIGGER IF NOT EXISTS group_start
#    AFTER UPDATE OF flag ON Participation
#    FOR EACH ROW
#    WHEN (SELECT COUNT(*) FROM Participation WHERE group_id = NEW.group_id AND flag != 'STARTED') = 0
#    AND (SELECT COUNT(*) FROM Participation WHERE group_id = NEW.group_id AND flag = 'STARTED') > 0
#    BEGIN
#        UPDATE "Group"
#        SET status = 'STARTED'
#        WHERE id = NEW.group_id;
#    END;

#    -- 모든 flag가 'terminated'일 때 Group 테이블의 state를 'terminated'로 변경
#    CREATE TRIGGER IF NOT EXISTS group_terminate
#    AFTER UPDATE OF flag ON Participation
#    FOR EACH ROW
#    WHEN (SELECT COUNT(*) FROM Participation WHERE group_id = NEW.group_id AND flag != 'TERMINATED') = 0
#    AND (SELECT COUNT(*) FROM Participation WHERE group_id = NEW.group_id AND flag = 'TERMINATED') > 0
#    BEGIN
#        UPDATE "Group"
#        SET status = 'TERMINATED'
#        WHERE id = NEW.group_id;
#    END;
#    """)
#    cursor.close()