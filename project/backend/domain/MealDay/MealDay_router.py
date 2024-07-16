import datetime

from fastapi import APIRouter,  Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from starlette import status
from database import get_db
from domain.MealDay import MealDay_schema, MealDay_crud
from models import MealDay, MealHour
from datetime import datetime,timedelta
from firebase_config import bucket

router=APIRouter(
    prefix="/mealDay"
)

@router.get("/get/{user_id}/{daytime}", response_model=List[MealDay_schema.MealDay_schema])
def get_MealDay_date(user_id: int, daytime: str, db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    MealDaily = MealDay_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if not MealDaily:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return [MealDaily] ##전체 열 출력

@router.get("/get/{user_id}/{daytime}/cheating", response_model=MealDay_schema.MealDay_cheating_get_schema)
def get_MealDay_date_cheating(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    cheating = MealDay_crud.get_MealDay_bydate_cheating(db,user_id=user_id,date=date)
    if cheating is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return cheating  ## cheating 열만 출력

@router.patch("/update/{user_id}/{daytime}/cheating", status_code=status.HTTP_204_NO_CONTENT)
async def update_MealDay_date_cheating(user_id: int, daytime: str,
                                  mealdaily_cheating_update: MealDay_schema.MealDay_cheating_update_schema,
                                  db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealcheating = MealDay_crud.get_MealDay_bydate(db, user_id=user_id, date=date)
    if mealcheating is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")

    MealDay_crud.update_cheating(db=db, db_MealPosting_Daily=mealcheating,
                                           cheating_update=mealdaily_cheating_update)

    return {"detail": "cheating updated successfully"}

@router.get("/get/{user_id}/{daytime}/wca", response_model=MealDay_schema.MealDay_wca_get_schema)
def get_MealDay_date_wca(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    wca = MealDay_crud.get_MealDay_bydate_wca(db,user_id=user_id,date=date)
    if wca is None:
        raise HTTPException(status_code=404, detail="Meal posting not found")
    return wca ## water, coffee, alcohol 열만 출력

@router.patch("/update/{user_id}/{daytime}/wca", status_code=status.HTTP_204_NO_CONTENT)
def update_Daymeal_date_wca(user_id: int,daytime: str,
                       mealdaily_wca_update: MealDay_schema.Mealday_wca_update_schema, db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    mealwca = MealDay_crud.get_MealDay_bydate(db,user_id=user_id,date=date)

    if mealwca is None:
        raise HTTPException(status_code=404, detail="MealDaily not found")
    MealDay_crud.update_wca(db=db,db_MealPosting_Daily=mealwca,wca_update=mealdaily_wca_update)

    return {"detail": "wca updated successfully"}

@router.post("/post/{user_id}/{daytime}",status_code=status.HTTP_204_NO_CONTENT)
def post_MealDay_date(user_id: int, daytime: str, db: Session=Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    meal=MealDay_crud.get_MealDay_bydate(db,user_id=user_id,date=date)
    if meal:
        return
    else:
        new_meal = MealDay(
            user_id=user_id,
            water=0.0,
            coffee=0.0,
            alcohol=0.0,
            carb=0.0,
            protein=0.0,
            fat=0.0,
            cheating=0,
            goalcalorie=0.0,
            nowcalorie=0.0,
            gb_carb = None,
            gb_protein = None,
            gb_fat = None,
            date = date,
            track_id = None ## 트랙 user사용중일때 안할때 이거 변경해야할거같은데
        )
        db.add(new_meal)
        db.commit()
        db.refresh(new_meal)

@router.get("/get/{user_id}/{daytime}/calorie", response_model=MealDay_schema.MealDay_calorie_get_schema)
def get_MealDay_date_calorie(user_id: int, daytime: str ,db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    calorie = MealDay_crud.get_MealDay_bydate_calorie(db,user_id=user_id,date=date)
    if calorie is None:
        raise HTTPException(status_code=404, detail="Calorie posting not found")
    return calorie ## goal,now calorie 열만 출력


@router.get("/get/{id}/{daytime}/track", response_model=MealDay_schema.MealDay_track_today_schema)
def get_Track_Mealhour(id: int, daytime: str, db: Session = Depends(get_db)):
    try:
        date = datetime.strptime(daytime, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    meal_today = db.query(MealDay).filter(MealDay.user_id == id, MealDay.date == date).first()
    if meal_today is None or meal_today.track_id is None:
        raise HTTPException(status_code=404, detail="Track not using")

    result = []
    date_part = daytime[:10]
    meal_hours = db.query(MealHour).filter(
        MealHour.user_id == id,
        MealHour.time.like(f"{date_part}%")
    ).all()

    for meal in meal_hours:
        try:
            # 서명된 URL 생성 (URL은 1시간 동안 유효)
            blob = bucket.blob(meal.picture)
            signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        meal_info = MealDay_schema.MealDay_track_hour_schema(
            name=meal.name,
            calorie=meal.calorie,
            date=meal.date,
            heart=meal.heart,
            picture=signed_url,
            track_id=meal_today.track_id
        )
        result.append(meal_info)

    return MealDay_schema.MealDay_track_today_schema(mealday=result)