from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):  # 회원
    __tablename__ = "User"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    cellphone = Column(String, nullable=False)
    gender = Column(Boolean, nullable=True)  # 1 남자, 0 여자
    birth = Column(DateTime, nullable=True)
    create_date = Column(DateTime, nullable=False)  # 가입일자
    nickname = Column(String, nullable=False)
    rank = Column(String, nullable=False)
    profile_picture = Column(String, nullable=True)
    mentor_id = Column(Integer, ForeignKey("Mentor.id"), nullable=True)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    external_id = Column(String, nullable=True)  # 연동했을 때 id
    auth_type = Column(String, nullable=True)  # 연동 방식 ex)kakao


class Company(Base):  # 회사(소속헬스장)
    __tablename__ = "Company"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    cellphone = Column(String, nullable=False)
    certificate = Column(Boolean, nullable=True)


class Mentor(Base):  # 멘토
    __tablename__ = "Mentor"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id"), unique=True)
    company_id = Column(Integer, ForeignKey("Company.id"), nullable=True)
    gym = Column(String, nullable=True)
    FA = Column(Boolean, nullable=True)



# class Suggestion(Base): ## 개발자에게 의견제출하는 테이블
# 	__tablename__ = "Suggestion"
#
# 	suggest_id = Column(Integer, primary_key=True)
# 	user_id = Column(Integer, ForeignKey("User.id"),primary_key=True)
# 	suggest_title = Column(String, nullable=False)
# 	suggest_content = Column(Text, nullable=True)
# 	suggest_date = Column(DateTime, nullable=True)
#
# class Track(Base): ## 식단트랙
# 	__tablename__ = "Track"
#
# 	track_id = Column(Integer, primary_key=True)
# 	user_id = Column(Integer, ForeignKey("User.id"),primary_key=True)
# 	track_name = Column(String, nullable=False)
# 	track_water = Column(Float,nullable=True)
# 	track_coffee = Column(Float,nullable=True)
# 	track_alcohol = Column(Float,nullable=True)
# 	track_duration = Column(String, nullable=True)
# 	track_yn = Column(Boolean, nullable=False) ## 트랙 참여가능여부 - 트랙생성자가 이를 삭제하면 남들도 이거 사용못하게함
#
# class TrackRoutine(Base): ## 식단트랙 루틴
# 	__tablename__ = "TrackRoutine"
#
# 	routine_id = Column(Integer, primary_key=True)
# 	track_id = Column(Integer, ForeignKey("Track.track_id"),primary_key=True)
# 	routine_name = Column(String, nullable=False)
# 	routine_week = Column(Text,nullable=True)
# 	routine_time = Column(Text,nullable=True)
#
#
# class TrackGroup(Base): ## 식단트랙을 사용하고 있는 user 있는지 확인 테이블
# 	__tablename__ = "TrackGroup"
#
# 	group_id = Column(Integer, primary_key=True)
# 	track_id = Column(Integer, ForeignKey("Track.track_id"), primary_key=True)
# 	group_start = Column(DateTime, nullable=False)
# 	group_finish = Column(DateTime, nullable=False)
# 	group_userlist = Column(Text, nullable=False)
#
#
# class MealPosting_Daily(Base): ## 식단게시글(일일)
# 	__tablename__ = "MealPosting_Daily"
#
# 	daymeal_id = Column(Integer, primary_key=True)
# 	user_id = Column(Integer, ForeignKey("User.id"), primary_key=True)
# 	daymeal_water = Column(String, nullable=True)
# 	daymeal_coffee = Column(String, nullable=True)
# 	daymeal_alcohol = Column(Float, nullable=True)
# 	daymeal_carb = Column(Float, nullable=True)
# 	daymeal_protein = Column(Float, nullable=True)
# 	daymeal_fat = Column(Float, nullable=True)
# 	daymeal_cheating = Column(Float, nullable=True)
# 	daymeal_goalcalorie = Column(Float, nullable=True) ## 목표칼로리
# 	daymeal_nowcalorie = Column(String, nullable=True) ## 현섭취칼로리
# 	daymeal_gb_carb = Column(Float, nullable=True) ## 탄수화물 구분
# 	daymeal_gb_protein = Column(String, nullable=True) ## 단백질 구분
# 	daymeal_gb_fat = Column(Float, nullable=True) ## 지방 구분
# 	daymeal_date = Column(String, nullable=True) ## 등록일자
# 	track_id = Column(Integer, ForeignKey("Track.track_id"),nullable=False)
#
# class MealPosting_Hourly(Base): ##식단게시글 (시간대별)
# 	__tablename__ = "MealPosting_Hourly"
#
# 	meal_id = Column(Integer, primary_key=True)
# 	user_id = Column(Integer, ForeignKey("User.id"), primary_key=True)
# 	meal_name = Column(String, nullable=False)
# 	meal_picture = Column(String, nullable=False)
# 	meal_text = Column(String, nullable=True)
# 	meal_date = Column(DateTime, nullable=False) ## 등록시점 분단뒤
# 	meal_heart = Column(Boolean, nullable=True)
# 	meal_time = Column(String, nullable=True) ## 등록시간대
# 	daymeal_id = Column(Integer, ForeignKey("MealPosting_Daily.daymeal_id"), nullable=False)
#
# class Comment(Base): ##댓글
# 	__tablename__ = "Comment"
#
# 	comment_id = Column(Integer, primary_key=True)
# 	meal_id = Column(Integer, ForeignKey("MealPosting_Hourly.meal_id"), primary_key=True)
# 	user_id = Column(Integer, ForeignKey("MealPosting_Hourly.id"), primary_key=True)
# 	comment_text = Column(String, nullable=True)
# 	comment_date = Column(DateTime, nullable=True)
# 	user_id2 = Column(Integer, ForeignKey("User.id"), nullable=False) ## 댓글 등록자



