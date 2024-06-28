from enum import Enum

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean, Float, Interval, Table, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum as PyEnum

group_join = Table(
    'join', Base.metadata,
    Column('user_id', Integer, ForeignKey('User.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('Group.id'), primary_key=True)
)

class User(Base):  # 회원
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    cellphone = Column(String, nullable=False)
    gender = Column(Boolean)  # 1 남자, 0 여자
    birth = Column(DateTime)
    create_date = Column(DateTime, nullable=False)  # 가입일자
    nickname = Column(String, nullable=False)
    rank = Column(String, nullable=False)
    profile_picture = Column(String)
    mentor_id = Column(Integer, ForeignKey("Mentor.id"), )
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    external_id = Column(String)  # 연동했을 때 id
    auth_type = Column(String)  # 연동 방식 ex)kakao
    fcm_token = Column(String) # fcm 토큰 -> 앱 실행시(?), 회원가입(?)
    groups = relationship('Group', secondary=group_join, back_populates='users')


class Company(Base):  # 회사(소속헬스장)
    __tablename__ = "Company"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    owner = Column(String, nullable=False)
    cellphone = Column(String, nullable=False)
    certificate = Column(Boolean)


class Mentor(Base):  # 멘토
    __tablename__ = "Mentor"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id"), unique=True)
    company_id = Column(Integer, ForeignKey("Company.id"))
    gym = Column(String)
    FA = Column(Boolean)


class Track(Base):  # 식단트랙
    __tablename__ = "Track"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    water = Column(Float)
    coffee = Column(Float)
    alcohol = Column(Float)
    duration = Column(Integer)  # Interval : 일, 시간, 분, 초 단위로 기간을 표현 가능, 정확한 시간의 간격(기간)
    track_yn = Column(Boolean, nullable=False)  # 트랙 생성자가 이를 삭제하면 남들도 이거 사용 못하게 함


# class Suggestion(Base): ## 개발자에게 의견제출하는 테이블
# 	__tablename__ = "Suggestion"
#
# 	suggest_id = Column(Integer, primary_key=True)
# 	user_id = Column(Integer, ForeignKey("User.id"),primary_key=True)
# 	suggest_title = Column(String, nullable=False)
# 	suggest_content = Column(Text, )
# 	suggest_date = Column(DateTime, )
#
#
# class TrackRoutine(Base):  ## 식단트랙 루틴
#     __tablename__ = "TrackRoutine"
#
#     routine_id = Column(Integer, primary_key=True)
#     track_id = Column(Integer, ForeignKey("Track.track_id"), primary_key=True)
#     routine_name = Column(String, nullable=False)
#     routine_week = Column(String)
#     routine_time = Column(String)


class Group(Base):  ## 식단트랙을 사용하고 있는 user 있는지 확인 테이블
    __tablename__ = "Group"

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("Track.id"))
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    start_day = Column(DateTime, nullable=False)
    finish_day = Column(DateTime, nullable=False)
    users = relationship("User", secondary=group_join, back_populates="groups")

# InviteStatus Enum
# class InviteStatus(Enum):
#     PENDING = "pending"
#     ACCEPTED = "accepted"
#     DECLINED = "declined"

class Invitation(Base):
    __tablename__ = "invitation"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("Group.id"), nullable=False)
    status = Column(String, default="pending")

# class MealPosting_Daily(Base): ## 식단게시글(일일)
# 	__tablename__ = "MealPosting_Daily"
#
# 	daymeal_id = Column(Integer, primary_key=True)
# 	user_id = Column(Integer, ForeignKey("User.id"), primary_key=True)
# 	daymeal_water = Column(String, )
# 	daymeal_coffee = Column(String, )
# 	daymeal_alcohol = Column(Float, )
# 	daymeal_carb = Column(Float, )
# 	daymeal_protein = Column(Float, )
# 	daymeal_fat = Column(Float, )
# 	daymeal_cheating = Column(Float, )
# 	daymeal_goalcalorie = Column(Float, ) ## 목표칼로리
# 	daymeal_nowcalorie = Column(String, ) ## 현섭취칼로리
# 	daymeal_gb_carb = Column(Float, ) ## 탄수화물 구분
# 	daymeal_gb_protein = Column(String, ) ## 단백질 구분
# 	daymeal_gb_fat = Column(Float, ) ## 지방 구분
# 	daymeal_date = Column(String, ) ## 등록일자
# 	track_id = Column(Integer, ForeignKey("Track.track_id"),nullable=False)
#
# class MealPosting_Hourly(Base): ##식단게시글 (시간대별)
# 	__tablename__ = "MealPosting_Hourly"
#
# 	meal_id = Column(Integer, primary_key=True)
# 	user_id = Column(Integer, ForeignKey("User.id"), primary_key=True)
# 	meal_name = Column(String, nullable=False)
# 	meal_picture = Column(String, nullable=False)
# 	meal_text = Column(String, )
# 	meal_date = Column(DateTime, nullable=False) ## 등록시점 분단뒤
# 	meal_heart = Column(Boolean, )
# 	meal_time = Column(String, ) ## 등록시간대
# 	daymeal_id = Column(Integer, ForeignKey("MealPosting_Daily.daymeal_id"), nullable=False)
#
# class Comment(Base): ##댓글
# 	__tablename__ = "Comment"
#
# 	comment_id = Column(Integer, primary_key=True)
# 	meal_id = Column(Integer, ForeignKey("MealPosting_Hourly.meal_id"), primary_key=True)
# 	user_id = Column(Integer, ForeignKey("MealPosting_Hourly.id"), primary_key=True)
# 	comment_text = Column(String, )
# 	comment_date = Column(DateTime, )
# 	user_id2 = Column(Integer, ForeignKey("User.id"), nullable=False) ## 댓글 등록자
