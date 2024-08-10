import os
from typing import List
from datetime import datetime, timedelta
from models import MealDay, MealHour, TrackRoutine,User, Mentor
from firebase_config import send_fcm_data_noti,send_fcm_notification
from fastapi import APIRouter, Form,File,Depends, HTTPException,UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_,and_
from starlette import status
from database import get_db
from domain.user import user_crud
from domain.meal_hour import meal_hour_schema,meal_hour_crud
from domain.meal_day import  meal_day_crud
from domain.user.user_router import get_current_user
from firebase_config import bucket
import json
import uuid

router=APIRouter(
    prefix="/meal_hour"
)

@router.get("/get/meal_hour/mine/{time}", response_model=meal_hour_schema.MealHour_schema)
def get_MealHour_date(time:str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 전체 Column 조회 : 9page 6-1번, 9page 6-2번 (기록날짜, 게시글),
     - 입력예시 : time = 2024-06-01아침 / user_id = 2, time = 2024
    """
    User_Meal = meal_hour_crud.get_User_Meal(db,user_id=current_user.id,time=time)
    if User_Meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return User_Meal  ## 전체 열 출력

@router.get("/get/meal_hour/formentor/{user_id}/{time}", response_model=meal_hour_schema.MealHour_schema)
def get_MealHour_date(user_id: int, time:str, db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 전체 Column 조회 : 9page 6-1번, 9page 6-2번 (기록날짜, 게시글),
     - 입력예시 : user_id = 1, time = 2024-06-01아침 / user_id = 2, time = 2024
    """
    User_Meal = meal_hour_crud.get_User_Meal(db,user_id=user_id,time=time)
    if User_Meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return User_Meal  ## 전체 열 출력

@router.get("/get_mealhour_picture/formentor/{id}/{time}")
async def get_mealhour_picture(id: int, time: str, db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 사진 조회 : 12page 2-2번
     - 입력예시 : time = 2024-06-01아침
     - 출력 : image_url
    """
    try:
        # 사용자 조회
        mealhour = meal_hour_crud.get_User_Meal(db,user_id=id,time=time)
        if mealhour is None:
            raise HTTPException(status_code=404, detail="Mealhour not found")

        if not mealhour.picture:
            raise HTTPException(status_code=404, detail="Picture not found")

        # 서명된 URL 생성 (URL은 1시간 동안 유효)
        blob = bucket.blob(mealhour.picture)
        signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))

        return {"image_url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_mealhour_picture/mine/{time}")
async def get_mealhour_picture(time: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 사진 조회 : 17page 4번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
     - 출력 : image_url
    """
    try:
        # 사용자 조회
        mealhour = meal_hour_crud.get_User_Meal(db,user_id=current_user.id,time=time)
        if mealhour is None:
            raise HTTPException(status_code=404, detail="Mealhour not found")

        if not mealhour.picture:
            raise HTTPException(status_code=404, detail="Picture not found")

        # 서명된 URL 생성 (URL은 1시간 동안 유효)
        blob = bucket.blob(mealhour.picture)
        signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))

        return {"image_url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_temp") ## 임시로 파일을 firebase저장하고 yolo서버로 전송
async def upload_food(current_user: User = Depends(get_current_user), file: UploadFile = File(...)):
    """
    식단시간별(MealHour) 사진 입력시 firebase에 임시저장 및 yolo서버로부터 food정보 Get : 10page 2번
     - 입력예시 : 사진파일
     - 출력 : file_path, food_info, image_url
    """
    # 고유한 파일 이름 생성
    file_id = meal_hour_crud.create_file_name(user_id=current_user.id)

    #Firebase Storage에 파일 업로드
    temp_blob = bucket.blob(f"temp/{file_id}")
    temp_blob.upload_from_file(file.file, content_type=file.content_type)

    #Yolov 서버로 파일 전송(yolov 서버가 firebase 사진에 접근)
    url = temp_blob.generate_signed_url(expiration=timedelta(hours=1)) #60분 유효url
    ##response = requests.post("http://yoloserver", json={"url":url})

    #Yolov 서버 응답 확인 - 실패시 0 출력
    ##if response.status_code != 200:
    ##    temp_blob.delete()  #firebase에 저장된 임시파일삭제
    ##    raise HTTPException(status_code=400, detail="YOLOv Server failed")
    ##    return 0

    #Yolov 서버에서 반환된 정보
    ##food_info = response.json()
    food_info = {"name": "Oatmeal", "date": "2024-06-27T07:30:00", "heart": True, "carb": 50.0, "protein": 10.0, "fat": 5.0, "calorie": 300.0, "unit": "gram", "size": 200.0, "daymeal_id": 1}


    return {"file_path": temp_blob.name, "food_info": food_info, "image_url": url} ## 임시파일이름, food정보, url 반환

@router.delete("/remove/{time}")
async def remove_meal(time:str,current_user: User = Depends(get_current_user), db:Session = Depends(get_db)):
     """
     식단시간별(MealHour) 사진 입력시 firebase에 임시저장 및 yolo서버로부터 food정보 Get : 10page 2번
      - 입력예시 :time = 2024-06-01아침
      - 출력 : file_path, food_info, image_url
     """
     meal = meal_hour_crud.get_User_Meal(db,user_id=current_user.id,time=time)
     if meal is None:
         raise HTTPException(status_code=404, detail="Meal not found")

     daily_post=minus_daily_post(db,user_id=current_user.id,new_food=meal)

     blob = bucket.blob(meal.picture)

     if blob.exists():
         blob.delete()

     db.delete(밥)
     db.commit()
     return {"detail": "Meal posting deleted successfully"}


@router.post("/register_meal/{time}") ## 등록시 임시업로드에 사용한데이터 입력필요 (임시사진이름file_path, food_info, text)
async def register_meal(time: str, file_path: str = Form(...), food_info: str = Form(...),text:str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 등록 (/meal_hour/upload_temp api로 얻은 data 활용 : 10page 4번
     - 입력예시 : time = 2024-06-01점심, file_paht, food_info, text = 오늘점심등록햇당
    """
    date_part = time[:10]
    time_part = time[11:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    temp_blob = bucket.blob(file_path)

    if not temp_blob.exists():
        raise HTTPException(status_code=400, detail="Temporary file does not exist")

    # 임시 파일을 meal 폴더로 이동
    meal_blob = bucket.blob(f"meal/{os.path.basename(file_path)}")
    bucket.rename_blob(temp_blob, meal_blob.name)

    # 서명된 URL 생성
    signed_url = meal_blob.generate_signed_url(expiration=timedelta(hours=1)) #60분

    #food_info를 Json에서 파싱
    food_info_dict = json.loads(food_info)

    daymeal_id = db.query(MealDay.id).filter(MealDay.user_id==current_user.id,MealDay.date==date).first()

    new_food = MealHour(
        user_id=current_user.id,
        name=food_info_dict.get("name",""),
        picture=meal_blob.name,
        text=text,
        date=datetime.utcnow()+ timedelta(hours=9),  # 현재 시간을 기본값으로 설정
        heart=False,
        time=time,
        carb=food_info_dict.get("carb", 0.0),
        protein=food_info_dict.get("protein", 0.0),
        fat=food_info_dict.get("fat", 0.0),
        calorie=food_info_dict.get("calorie", 0.0),
        unit=food_info_dict.get("unit","gram"),
        size=food_info_dict.get("size", 0.0),
        track_goal=None,
        daymeal_id=daymeal_id
    )

    daily_post = plus_daily_post(db, current_user.id, new_food)

    mealtoday = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
    weekday_number = date.weekday()
    weekday_str = ["월", "화", "수", "목", "금", "토", "일"][weekday_number]
    tracktitle = db.query(TrackRoutine.title).filter(
        and_(
            TrackRoutine.track_id == mealtoday.track_id,
            TrackRoutine.time.like(f"%{time_part}%"),
            or_(
                TrackRoutine.week.like(f"%{weekday_str}%"),
                TrackRoutine.date == date_part
            )
        )
    ).first()

    goal = False
    if tracktitle is not None and new_food.name in tracktitle:
        goal=True

    add_food = MealHour(
        user_id=current_user.id,
        name=food_info_dict.get("name",""),
        picture=meal_blob.name,
        text=text,
        date=datetime.utcnow()+ timedelta(hours=9),  # 현재 시간을 기본값으로 설정
        heart=food_info_dict.get("heart", False),
        time=time,
        carb=food_info_dict.get("carb", 0.0),
        protein=food_info_dict.get("protein", 0.0),
        fat=food_info_dict.get("fat", 0.0),
        calorie=food_info_dict.get("calorie", 0.0),
        unit=food_info_dict.get("unit", "gram"),
        size=food_info_dict.get("size", 0.0),
        track_goal=goal,
        daymeal_id=daily_post.id
    )
    db.add(add_food)
    db.commit()
    db.refresh(add_food)

    username = user_crud.get_User_name(db,current_user.id)
    mealtime = time[10:]
    mentor_id = db.query(User.mentor_id).filter(User.id==current_user.id).first()
    if mentor_id:
        mentor_user_id=db.query(Mentor.user_id).filter(Mentor.id==mentor_id).first()
        if mentor_user_id:
            data = {
                "user_id": current_user.id,
                "mentor_id" : mentor_id,
                "message": f"{username}님이 f{mealtime}을 등록했습니다."
            }

            send_fcm_data_noti(mentor_user_id,"회원식사등록", data["message"],data)

    return {"food": add_food, "daily_post": daily_post, "signed_url": signed_url}


@router.post("/remove_temp_meal") ##식단게시 취소시 임시파일삭제(임시저장사진명 필요:file_path)
async def remove_temp_meal(file_path: str = Form(...)):
    """
    식단시간별(MealHour) 식단등록시 뒤로가기를 통한 임시저장된 음식사진삭제 : 10page 4-2번(뒤로가기)
     - 입력예시 : file_path (meal_hour/upload_temp api로 얻은 임시 파일경로)
    """
    temp_blob = bucket.blob(file_path)

    if temp_blob.exists():
        temp_blob.delete()

    return {"detail": "Temporary file removed"}

@router.patch("/update/gram/{daytime}", status_code=status.HTTP_204_NO_CONTENT)
def update_meal_gram(time: str, size: float = Form(...), current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 음식 size 수정 : 12page 3-2번
     - 입력예시 :  time = 2024-06-01아침
     - 출력 : MealHour.calorie, MealHour.carb, MealHour.protein, MealHour.fat
    """
    mealgram = meal_hour_crud.get_User_Meal(db,user_id=current_user.id,time=time)
    if mealgram is None:
        raise HTTPException(status_code=404, detail="MealHourly not found")

    minus_daily_post(db,user_id=current_user.id,new_food=mealgram)

    old_size = mealgram.size
    if old_size == 0:
        raise HTTPException(status_code=400, detail="Original size is zero, cannot update proportionally")

    percent = size/old_size
    mealgram.carb *= percent
    mealgram.protein *= percent
    mealgram.fat *= percent
    mealgram.calorie *= percent
    mealgram.size = size
    db.commit()
    db.refresh(mealgram)

    plus_daily_post(db, user_id=current_user.id, new_food=mealgram)

    return mealgram

def plus_daily_post(db: Session, user_id: int, new_food: MealHour):
    try:
        date_part = new_food.time[:10]
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    daily_post = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)

    if daily_post:
        # 기존 레코드 업데이트
        daily_post.carb += new_food.carb
        daily_post.protein += new_food.protein
        daily_post.fat += new_food.fat
        daily_post.nowcalorie += new_food.calorie

    db.add(daily_post)
    db.commit()
    db.refresh(daily_post)
    return daily_post

def minus_daily_post(db: Session, user_id: int,new_food: MealHour):
    try:
        date_part = new_food.time[:10]
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    daily_post = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if daily_post is None:
        raise HTTPException(status_code=404, detail="User not found")
    if daily_post:
        # 기존 레코드 업데이트
        daily_post.carb -= new_food.carb
        daily_post.protein -= new_food.protein
        daily_post.fat -= new_food.fat
        daily_post.nowcalorie -= new_food.calorie

    db.add(daily_post)
    db.commit()
    db.refresh(daily_post)
    return daily_post

@router.get("/get/daymeal/{daytime}", response_model=List[meal_hour_schema.MealHour_daymeal_get_schema])
def get_MealHour_date_all(daytime:str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    해당일 등록 식단Time, name 출력 : 13page 2-1번
     - 입력예시 : time = 2024-06-01아침
     - 출력 : 당일 식단게시글[MealHour.time, MealHour.name]
    """
    User_Meal = meal_hour_crud.get_User_Meal_all_name_time(db,user_id=current_user.id,time=daytime)

    if User_Meal is None:
        raise HTTPException(status_code=404, detail="Comments not found")
    return User_Meal  ## TIME, NAME 열출력(전체 행) ##time에 날짜만입력


@router.patch("update/heart/{user_id}/{time}", status_code=status.HTTP_204_NO_CONTENT)
def update_MealHour_heart(user_id: int, time: str, db:Session=Depends(get_db)):
    """
    회원들  : 16page 5-3번
     - 입력예시 : User.user_id(회원) = 1, time = 2024-06-01오후간식
    """
    User_Meal = meal_hour_crud.get_User_Meal(db, user_id=user_id, time=time)
    if User_Meal is None:
        raise HTTPException(status_code=404, detail="User_Meal not found")
    if User_Meal.heart == False:
        User_Meal.heart =True
    else:
        User_Meal.heart = False

    db.add(User_Meal)
    db.commit()
    db.refresh(User_Meal)

    if User_Meal.heart == True:
        mentor_id = db.query(User.mentor_id).filter(User.id==user_id).first()
        if mentor_id:
            mentor_user_id=db.query(Mentor.user_id).filter(Mentor.id==mentor_id).first()
            if mentor_user_id:
                mealtime = time[10:]
                mentor_name=user_crud.get_User_name(db,mentor_user_id)
                send_fcm_notification(user_id,"하트등록",f"{mentor_name}님이 {mealtime}식단을 칭찬했어요")

    return User_Meal

@router.get("/get/daymeal_time/{user_id}/{daytime}", response_model=List[meal_hour_schema.MealHour_daymeal_time_get_schema])
def get_MealHour_date_all(user_id: int, daytime:str, db: Session = Depends(get_db)):
    User_Meal = meal_hour_crud.get_User_Meal_all_time(db,user_id=user_id,time=daytime)
    if User_Meal is None:
        raise HTTPException(status_code=404, detail="Comments not found")
    return User_Meal  ## TIME ##time에 날짜만입력

@router.get("/get/track/mine/{time}", response_model=meal_hour_schema.MealHour_track_get_schema)
def get_MealHour_track_goal_user(time:str, current_user: User = Depends(get_current_user), db:Session =Depends(get_db)):
    """
    식단시간별(MealHour) track 지킴 유무 조회 : 12page 6-1번
     - 입력예시 : time = 2024-06-01아침
     - 출력 : MealHour.track_goal
    """
    mealhour=meal_hour_crud.get_User_Meal(user_id=current_user.id,time=time,db=db)
    if mealhour is None:
        raise HTTPException(status_code=404, detail="MealHour not found")
    return {"track_goal" : mealhour.track_goal}

@router.get("/get/track/formentor/{user_id}/{time}", response_model=meal_hour_schema.MealHour_track_get_schema)
def get_MealHour_track_goal_mentor(user_id: int, time:str, db:Session =Depends(get_db)):
    """
    식단시간별(MealHour) track 지킴 유무 조회 : 12page 6-1번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
     - 출력 : MealHour.track_goal
    """
    mealhour=meal_hour_crud.get_User_Meal(user_id=user_id,time=time,db=db)
    if mealhour is None:
        raise HTTPException(status_code=404, detail="MealHour not found")
    return {"track_goal" : mealhour.track_goal}

@router.patch("/update/track/mine/{time}", status_code=status.HTTP_204_NO_CONTENT)
def update_Mealhour_track_goal_user(time:str, current_user: User = Depends(get_current_user), db:Session=Depends(get_db)):
    """
    식단시간별(MealHour) track 지킴 유무 없뎃 : 12page 6-2번
     - 입력예시 : time = 2024-06-01아침
    """
    mealhour=meal_hour_crud.get_User_Meal(user_id=current_user.id,time=time,db=db)
    if mealhour is None:
        raise HTTPException(status_code=404, detail="MealHour not found")
    if mealhour.track_goal == True:
        mealhour.track_goal = False
    else:
        mealhour.track_goal = True
    db.commit()
    db.refresh(mealhour)
    return {"detail" : "track_goal updated successfully"}

@router.patch("/update/track/formentor/{user_id}/{time}", status_code=status.HTTP_204_NO_CONTENT)
def update_Mealhour_track_goal_mentor(user_id:int, time:str, db:Session=Depends(get_db)):
    """
    식단시간별(MealHour) track 지킴 유무 없뎃 : 17page 8번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
    """
    mealhour=meal_hour_crud.get_User_Meal(user_id=user_id,time=time,db=db)
    if mealhour is None:
        raise HTTPException(status_code=404, detail="MealHour not found")
    if mealhour.track_goal == True:
        mealhour.track_goal = False
    else:
        mealhour.track_goal = True
    db.commit()
    db.refresh(mealhour)
    return {"detail" : "track_goal updated successfully"}
