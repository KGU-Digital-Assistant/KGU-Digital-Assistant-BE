from sqlalchemy import Date,Column,Integer,ForeignKey,String,Float,DateTime,Text,Boolean,UniqueConstraint,Interval, Table, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum as PyEnum

Participation = Table(
    'Participation', Base.metadata,
    Column('user_id', Integer, ForeignKey('User.id'), primary_key=True), ## 그룹가입 user(회원들)
    Column('group_id', Integer, ForeignKey('Group.id'), primary_key=True), ## 그룹id
    Column('cheating_count', Integer, nullable=True), ##치팅 횟수
    Column('flag', Boolean), #None == ready, False = Terminated, True = Started
    Column('finish_date', Date, nullable=True) #실제종료일 입력
)

class User(Base):  # 회원
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False) # 회원가입 ID로 쓸 예정 ( 컬럼 이름은 oauth2 form에 맞춰야해서 고정)
    name = Column(String, nullable=False) # 실명
    cellphone = Column(String, unique=True, nullable=False)
    gender = Column(Boolean)  # 1 남자, 0 여자
    birth = Column(DateTime)
    create_date = Column(DateTime, nullable=False)  # 가입일자
    nickname = Column(String, unique=True, nullable=False)
    rank = Column(Float, nullable=False)
    profile_picture = Column(String)
    mentor_id = Column(Integer, ForeignKey("Mentor.id"), )
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    external_id = Column(String)  # 연동했을 때 id
    auth_type = Column(String)  # 연동 방식 ex)kakao
    fcm_token = Column(String) # fcm 토큰 -> 앱 실행시(?), 회원가입(?)
    groups = relationship('Group', secondary=Participation, back_populates='users')

class Mentor(Base): ## 멘토
    __tablename__ = "Mentor"

    id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"),unique=True)
    gym = Column(String, nullable=True)
    FA = Column(Boolean, nullable=True)
    company_id = Column(Integer, ForeignKey("Company.id"), nullable=True)

class Company(Base): ## 회사(소속헬스장)
    __tablename__ = "Company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    cellphone = Column(String, nullable=False)
    certificate = Column(Boolean, nullable=True)

class Suggestion(Base): ## 개발자에게 의견제출하는 테이블
    __tablename__ = "Suggestion"

    id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)

class Track(Base):  # 식단트랙
    __tablename__ = "Track"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    name = Column(String, default="새로운 식단 트랙")
    water = Column(Float, default=0)
    coffee = Column(Float, default=0)
    alcohol = Column(Float, default=0)
    duration = Column(Integer)  # Interval : 일, 시간, 분, 초 단위로 기간을 표현 가능, 정확한 시간의 간격(기간)
    track_yn = Column(Boolean, default=True)  # 트랙 생성자가 이를 삭제하면 남들도 이거 사용 못하게 함
    cheating_count = Column(Integer, default=0)
    start_date = Column(Date)
    finish_date = Column(Date)
    count = Column(Integer, default=0) #트랙 공유, 초대횟수에 따른 count ++
    alone = Column(Boolean, default=True) ## 개인트랙, 공유초대트랙여부
    routines = relationship("TrackRoutine", back_populates="track")

class Group(Base):  ## 식단트랙을 사용하고 있는 user 있는지 확인 테이블
    __tablename__ = "Group"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("Track.id"))
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)  ## track을 만든 회원의 id
    name = Column(String, unique=True, nullable=False)
    start_day = Column(Date, nullable=True)
    finish_day = Column(Date, nullable=True)
    state = Column(String, nullable=False)
    users = relationship("User", secondary=Participation, back_populates="groups")

class TrackRoutine(Base): ## 식단트랙 루틴
    __tablename__ = "Track_Routine"

    id = Column(Integer, primary_key=True,autoincrement=True)
    track_id = Column(Integer, ForeignKey("Track.id"))
    title = Column(String, nullable=False)
    calorie = Column(Float, nullable=False)
    week = Column(String,nullable=True) ## 요일에 따른 1 2 3 4 5 6 7
    time = Column(String,nullable=True) ## 아침, 점심, 저녁 등
    date = Column(String,nullable=True) ## n번째 1,5  9, 14 등
    repeat = Column(Boolean,nullable=False) #1은 반복, 0은 단독
    track = relationship("Track", back_populates="routines")

class Invitation(Base):
    __tablename__ = "Invitation"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("Group.id"), nullable=False)
    status = Column(String, default="pending")

class MealDay(Base):
    __tablename__ = "Meal_Day"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    water = Column(Float, nullable=True)
    coffee = Column(Float, nullable=True)
    alcohol = Column(Float, nullable=True)
    carb = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    cheating = Column(Integer, nullable=True)
    goalcalorie = Column(Float, nullable=True)  # 목표칼로리
    nowcalorie = Column(Float, nullable=True)  # 현섭취칼로리
    gb_carb = Column(String, nullable=True)  # 탄수화물 구분
    gb_protein = Column(String, nullable=True)  # 단백질 구분
    gb_fat = Column(String, nullable=True)  # 지방 구분
    date = Column(Date, nullable=True)  # 등록일자
    track_id = Column(Integer, ForeignKey("Track.id"), nullable=True)
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='_user_date_daily_uc'),
    )

class MealHour(Base): ##식단게시글 (시간대별)
    __tablename__ = "Meal_Hour"

    id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=False,index=True)
    text = Column(String, nullable=True)
    date = Column(DateTime, nullable=False) ## 등록시점 분단뒤
    heart = Column(Boolean, nullable=True)
    time = Column(String, nullable=True) ## 등록시간대 아침, 점심, 저녁, 오후간식 등
    carb = Column(Float, nullable=True)
    protein = Column(Float, nullable=True)
    fat = Column(Float, nullable=True)
    calorie = Column(Float, nullable=True) ## 섭취칼로리
    unit =Column(String, nullable=True) ##저장단위
    size = Column(Float, nullable=True) ##사이즈
    track_goal = Column(Boolean, nullable=True)  ##트랙지켯는지 안지켰는지 유무
    daymeal_id = Column(Integer, ForeignKey("Meal_Day.id"), nullable=False)
    __table_args__ = (
        UniqueConstraint('user_id', 'time', name='_user_date_hour_uc'),
    )

class Comment(Base): ##댓글
    __tablename__ = "Comment"

    id = Column(Integer, primary_key=True,autoincrement=True)
    meal_id = Column(Integer, ForeignKey("Meal_Hour.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=True)
    date = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False) ## 댓글 등록자
