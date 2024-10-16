import os
from urllib.parse import quote
from typing import List
from datetime import datetime, timedelta, time, date
from models import MealDay, MealHour, TrackRoutine,User, Mentor, TrackRoutineDate
from firebase_config import send_fcm_data_noti,send_fcm_notification
from fastapi import APIRouter, Form,File,Depends, HTTPException,UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_,and_
import requests
from starlette import status
from database import get_db
from domain.track_routine import track_routine_crud
from domain.user import user_crud
from domain.mentor import mentor_crud
from domain.meal_hour import meal_hour_schema,meal_hour_crud
from domain.meal_day import  meal_day_crud
from domain.user.user_router import get_current_user
from domain.group.group_crud import get_group_track_id_in_part_state_start
from firebase_config import bucket
import json
import uuid

router=APIRouter(
    prefix="/meal_hour"
)

@router.get("/get/meal_hour/mine/{times}", response_model=meal_hour_schema.MealHour_schema)
def get_MealHour_date(times:str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 전체 Column 조회 : 9page 6-1번, 9page 6-2번 (기록날짜, 게시글),
     - 입력예시 : time = 2024-06-01아침 / user_id = 2, time = 2024
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = meal_hour_crud.time_parse(time=time_part)
    daymeal = meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    User_Meal = meal_hour_crud.get_user_meal(db,user_id=current_user.id,daymeal_id=daymeal.id, mealtime=mealtime)
    if User_Meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return User_Meal  ## 전체 열 출력

@router.get("/get/meal_hour/formentor/{user_id}/{times}", response_model=meal_hour_schema.MealHour_schema)
def get_MealHour_date(user_id: int, times:str, db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 전체 Column 조회 : 9page 6-1번, 9page 6-2번 (기록날짜, 게시글),
     - 입력예시 : user_id = 1, time = 2024-06-01아침 / user_id = 2, time = 2024
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = meal_hour_crud.time_parse(time=time_part)
    daymeal = meal_day_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    User_Meal = meal_hour_crud.get_user_meal(db,user_id=user_id,daymeal_id=daymeal.id, mealtime=mealtime)
    if User_Meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return User_Meal  ## 전체 열 출력

@router.get("/get_mealhour_picture/formentor/{id}/{times}")
async def get_mealhour_picture(user_id: int, times: str, db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 사진 조회 : 12page 2-2번
     - 입력예시 : time = 2024-06-01아침
     - 출력 : image_url
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    try:
        # 사용자 조회
        mealtime = meal_hour_crud.time_parse(time=time_part)
        daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
        if daymeal is None:
            raise HTTPException(status_code=404, detail="Meal not found")
        mealhour = meal_hour_crud.get_user_meal(db, user_id=user_id, daymeal_id=daymeal.id, mealtime=mealtime)
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

@router.get("/get_mealhour_picture/mine/{times}")
async def get_mealhour_picture(times: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 사진 조회 : 17page 4번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
     - 출력 : image_url
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    try:
        # 사용자 조회
        mealtime = meal_hour_crud.time_parse(time=time_part)
        daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
        if daymeal is None:
            raise HTTPException(status_code=404, detail="Meal not found")
        mealhour = meal_hour_crud.get_user_meal(db, user_id=current_user.id, daymeal_id=daymeal.id, mealtime=mealtime)
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
    print(url)
    encoded_url = quote(url, safe='')

    # YOLO 서버에 POST 요청을 보내고, 응답 받기
    response = requests.post(f"http://110.8.6.21/yolo/?url={encoded_url}", headers={'accept': 'application/json'})
    print(response.status_code)
    # Yolov 서버 응답 확인 - 실패시 0 출력
    if response.status_code != 201:
       temp_blob.delete()  #firebase에 저장된 임시파일삭제
       raise HTTPException(status_code=400, detail="YOLOv Server failed")
       return 0

    #Yolov 서버에서 반환된 정보
    food_info = response.json()
    print(food_info)

    return {"file_path": temp_blob.name, "food_info": food_info, "image_url": url} ## 임시파일이름, food정보, url 반환

@router.delete("/remove/{times}")
async def remove_meal(times:str,current_user: User = Depends(get_current_user), db:Session = Depends(get_db)):
     """
     식단시간별(MealHour) 사진 입력시 firebase에 임시저장 및 yolo서버로부터 food정보 Get : 10page 2번
      - 입력예시 :time = 2024-06-01아침
      - 출력 : file_path, food_info, image_url
     """
     date_part = times[:10]
     time_part = times[10:]
     try:
         date = datetime.strptime(date_part, '%Y-%m-%d').date()
     except ValueError:
         raise HTTPException(status_code=400, detail="Invalid date format")
     mealtime = meal_hour_crud.time_parse(time=time_part)
     daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
     if daymeal is None:
         raise HTTPException(status_code=404, detail="Meal not found")
     meal = meal_hour_crud.get_user_meal(db, user_id=current_user.id, daymeal_id=daymeal.id, mealtime=mealtime)
     if meal is None:
         raise HTTPException(status_code=404, detail="Meal not found")

     daily_post=meal_hour_crud.minus_daily_post(db,user_id=current_user.id,date=date,new_food=meal)

     blob = bucket.blob(meal.picture)

     if blob.exists():
         blob.delete()

     db.delete(meal)
     db.commit()
     return {"detail": "Meal posting deleted successfully"}


@router.post("/register_meal/{times}/{hourminute}") ## 등록시 임시업로드에 사용한데이터 입력필요 (임시사진이름file_path, food_info, text)
async def register_meal(times: str, hourminute: str,file_path: str = Form(...), food_info: str = Form(...),text:str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 등록 (/meal_hour/upload_temp api로 얻은 data 활용 : 10page 4번
     - 입력예시 : times = 2024-06-01점심, file_paht, food_info, text = 오늘점심등록햇당
    """
    date_part = times[:10]
    time_part = times[10:]
    mealtime =meal_hour_crud.time_parse(time_part)
    if mealtime is None:  # time_parse에서 None이 반환된 경우 처리
        raise HTTPException(status_code=400, detail="Invalid meal time.")
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    # hourminute 값을 받아 시간과 분으로 변환
    try:
        hour = int(hourminute[:2])
        minute = int(hourminute[2:])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid hourminute format. Use HHMM format like 1240.")
    # 오늘 날짜와 hourminute를 결합한 datetime 객체 생성
    date_time = datetime.combine(date,time(hour, minute))
    daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date= date)
    mealhour_check = meal_hour_crud.get_user_meal(db, user_id=current_user.id,daymeal_id=daymeal.id, mealtime=mealtime)
    if mealhour_check:
        raise HTTPException(status_code=400, detail="Already registered mealhour")

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


    new_food = MealHour(
        user_id=current_user.id,
        name=food_info_dict.get("name",""),
        picture=meal_blob.name,
        text=text,
        date=date_time,  # 현재 시간을 기본값으로 설정
        heart=False,
        time=mealtime,
        carb=float(food_info_dict.get("carb", 0.0)),
        protein=float(food_info_dict.get("protein", 0.0)),
        fat=float(food_info_dict.get("fat", 0.0)),
        calorie=float(food_info_dict.get("kcal", 0.0)),
        unit="gram",
        size=float(food_info_dict.get("weight", 0.0)),
        track_goal=None,
        daymeal_id=daymeal.id,
        label= int(food_info_dict.get("labels", [None])[0])
    )
    daily_post = meal_hour_crud.plus_daily_post(db, current_user.id, date, new_food)

    weekday_number = date.weekday()
    goal = False
    ###아래 코드 test 필요 식단 등록 잘햇는지 판단하는 내용 goal true false 여부
    if daymeal and daymeal.track_id:
        group_part = get_group_track_id_in_part_state_start(db, user_id=current_user.id, track_id=daymeal.track_id)
        if group_part is None:
            raise HTTPException(status_code=404, detail="User or Group not found")
        group, cheating_count, user_id2, flag, finish_date = group_part
        days = (date - group.start_day).days + 1
        trackroutines = track_routine_crud.get_track_routine_by_track_id(db, track_id=daymeal.track_id)
        if trackroutines is not None:
            for trackroutin in trackroutines:
                trackroutindates = track_routine_crud.get_trackroutinedate_by_trackroutine_id_weekday_time_date(db, trackroutin_id=trackroutin.id,
                                                                                                                weekday= weekday_number,time=mealtime,
                                                                                                                date=days)
                if trackroutindates and new_food.name in trackroutin.title:
                    goal = True
                    break;

    add_food = meal_hour_crud.create_mealhour(db, mealhour=new_food,track_goal=goal)

    username = current_user.name
    mentor_id = current_user.mentor_id
    if mentor_id:
        mentor_user_info=mentor_crud.get_mentor_by_id(db, mentor_id = mentor_id)
        if mentor_user_info.user_id:
            data = {
                "user_id": current_user.id,
                "mentor_id" : mentor_id,
                "message": f"{username}님이 f{time_part}을 등록했습니다."
            }

            send_fcm_data_noti(mentor_user_info.user_id,"회원식사등록", data["message"],data)

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

@router.patch("/update/gram/{times}", status_code=status.HTTP_204_NO_CONTENT)
def update_meal_gram(times: str, size: float = Form(...), current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    """
    식단시간별(MealHour) 음식 size 수정 : 12page 3-2번
     - 입력예시 :  time = 2024-06-01아침
     - 출력 : MealHour.calorie, MealHour.carb, MealHour.protein, MealHour.fat
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = meal_hour_crud.time_parse(time=time_part)
    daymeal = meal_day_crud.get_MealDay_bydate(db,user_id=current_user.id,date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    mealgram = meal_hour_crud.get_user_meal(db, user_id=current_user.id, daymeal_id=daymeal.id, mealtime=mealtime)
    if mealgram is None:
        raise HTTPException(status_code=404, detail="MealHourly not found")

    meal_hour_crud.minus_daily_post(db,user_id=current_user.id,date=date,new_food=mealgram)

    old_size = mealgram.size
    if old_size == 0:
        raise HTTPException(status_code=400, detail="Original size is zero, cannot update proportionally")

    percent = size/old_size
    mealgram_fix = meal_hour_crud.update_mealgram(db, mealhour=mealgram,percent=percent,size=size)

    meal_hour_crud.plus_daily_post(db, user_id=current_user.id, date=date,new_food=mealgram_fix   )

    return mealgram_fix

@router.get("/get/daymeal/{daytime}", response_model=List[meal_hour_schema.MealHour_daymeal_get_schema])
def get_MealHour_date_all(daytime:str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    해당일 등록 식단Time, name 출력 : 13page 2-1번
     - 입력예시 : time = 2024-06-01아침
     - 출력 : 당일 식단게시글[MealHour.time, MealHour.name]
    """
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    User_Meal = meal_hour_crud.get_User_Meal_all_name_time(db,user_id=current_user.id,daymeal_id=daymeal.id)

    if User_Meal is None:
        raise HTTPException(status_code=404, detail="Comments not found")
    return User_Meal  ## TIME, NAME 열출력(전체 행) ##time에 날짜만입력


@router.patch("/update/heart/{user_id}/{times}", status_code=status.HTTP_204_NO_CONTENT)
def update_MealHour_heart(user_id: int, times: str, db:Session=Depends(get_db)):
    """
    회원들  : 16page 5-3번
     - 입력예시 : User.user_id(회원) = 1, time = 2024-06-01오후간식
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = meal_hour_crud.time_parse(time=time_part)
    daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    User_Meal = meal_hour_crud.get_user_meal(db, user_id=user_id, daymeal_id=daymeal.id, mealtime=mealtime)
    if User_Meal is None:
        raise HTTPException(status_code=404, detail="User_Meal not found")
    user_meal_fix = meal_hour_crud.update_heart(db, mealhour=User_Meal)

    if user_meal_fix.heart == True:
        user_info = user_crud.get_user(db, user_id=user_id)
        if user_info.mentor_id:
            mentor_info=mentor_crud.get_mentor_by_id(db, mentor_id=user_info.mentor_id)
            if mentor_info.user_id:
                mealtime = times[10:]
                mentor_name=user_crud.get_User_name(db,mentor_info.user_id)
                send_fcm_notification(user_id,"하트등록",f"{mentor_name}님이 {mealtime}식단을 칭찬했어요")

    return user_meal_fix

# @router.get("/get/daymeal_time/{user_id}/{daytime}", response_model=List[meal_hour_schema.MealHour_daymeal_time_get_schema])
# def get_MealHour_date_all(user_id: int, daytime:str, db: Session = Depends(get_db)):
#     User_Meal = meal_hour_crud.get_User_Meal_all_time(db,user_id=user_id,time=daytime)
#     if User_Meal is None:
#         raise HTTPException(status_code=404, detail="Comments not found")
#     return User_Meal  ## TIME ##time에 날짜만입력

@router.get("/get/track/mine/{times}", response_model=meal_hour_schema.MealHour_track_get_schema)
def get_MealHour_track_goal_user(times:str, current_user: User = Depends(get_current_user), db:Session =Depends(get_db)):
    """
    식단시간별(MealHour) track 지킴 유무 조회 : 12page 6-1번
     - 입력예시 : time = 2024-06-01아침
     - 출력 : MealHour.track_goal
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = meal_hour_crud.time_parse(time=time_part)
    daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    mealhour= meal_hour_crud.get_user_meal(db, user_id=current_user.id, daymeal_id=daymeal.id, mealtime=mealtime)
    if mealhour is None:
        raise HTTPException(status_code=404, detail="MealHour not found")
    return {"track_goal" : mealhour.track_goal}

@router.get("/get/track/formentor/{user_id}/{times}", response_model=meal_hour_schema.MealHour_track_get_schema)
def get_MealHour_track_goal_mentor(user_id: int, times:str, db:Session =Depends(get_db)):
    """
    식단시간별(MealHour) track 지킴 유무 조회 : 12page 6-1번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
     - 출력 : MealHour.track_goal
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = meal_hour_crud.time_parse(time=time_part)
    daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    mealhour= meal_hour_crud.get_user_meal(db, user_id=user_id, daymeal_id=daymeal.id, mealtime=mealtime)
    if mealhour is None:
        raise HTTPException(status_code=404, detail="MealHour not found")
    return {"track_goal" : mealhour.track_goal}

@router.patch("/update/track/mine/{times}", status_code=status.HTTP_204_NO_CONTENT)
def update_Mealhour_track_goal_user(times:str, current_user: User = Depends(get_current_user), db:Session=Depends(get_db)):
    """
    식단시간별(MealHour) track 지킴 유무 없뎃 : 12page 6-2번
     - 입력예시 : time = 2024-06-01아침
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = meal_hour_crud.time_parse(time=time_part)
    daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=current_user.id, date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    mealhour= meal_hour_crud.get_user_meal(db, user_id=current_user.id, daymeal_id=daymeal.id, mealtime=mealtime)
    if mealhour is None:
        raise HTTPException(status_code=404, detail="MealHour not found")
    meal_hour_crud.update_track_goal(db,mealhour=mealhour)
    return {"detail" : "track_goal updated successfully"}

@router.patch("/update/track/formentor/{user_id}/{times}", status_code=status.HTTP_204_NO_CONTENT)
def update_Mealhour_track_goal_mentor(user_id:int, times:str, db:Session=Depends(get_db)):
    """
    식단시간별(MealHour) track 지킴 유무 없뎃 : 17page 8번
     - 입력예시 : user_id = 1, time = 2024-06-01아침
    """
    date_part = times[:10]
    time_part = times[10:]
    try:
        date = datetime.strptime(date_part, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    mealtime = meal_hour_crud.time_parse(time=time_part)
    daymeal = meal_day_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
    if daymeal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    mealhour= meal_hour_crud.get_user_meal(db, user_id=user_id, daymeal_id=daymeal.id, mealtime=mealtime)
    if mealhour is None:
        raise HTTPException(status_code=404, detail="MealHour not found")
    meal_hour_crud.update_track_goal(db,mealhour=mealhour)
    return {"detail" : "track_goal updated successfully"}
