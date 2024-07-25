
from fastapi import APIRouter, Form,Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from models import Suggestion, User
from domain.suggestion import suggestion_schema,suggestion_crud
from domain.user.user_router import get_current_user
from datetime import datetime, timedelta
from starlette import status

router=APIRouter(
    prefix="/suggest"
)

@router.get("/get/{suggest_id}/text", response_model=suggestion_schema.Suggestion_content_schema)
def get_Suggest_id(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    개발자 의견제출  : 27page 1번
     - 입력예시 : Suggestion.id = 1
     - 출력 : Suggestion.title, Suggestion.content
    """
    suggest = suggestion_crud.get_Suggestion_content(db, id=current_user.id)
    if suggest is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    return suggest

@router.post("/post/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_Suggest(current_user: User = Depends(get_current_user), title: str=Form(...), content: str=Form(...), db: Session=Depends(get_db)):
    """
    개발자 의견제출  : 27page 3번
     - 입력예시 : User.user_id(회원) = 1, title = "치킨", content = "치킨너무비싸"
    """
    new_suggest=Suggestion(
        user_id=current_user.id,
        title=title,
        content=content,
        date=datetime.utcnow()+ timedelta(hours=9)
    )
    db.add(new_suggest)
    db.commit()
    db.refresh(new_suggest)
    return {"suggest" : new_suggest}

@router.get("/get/{user_id}/all_title",response_model=List[suggestion_schema.Suggestion_title_schema])
def get_Suggest_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    개발자 의견제출  : 27page 3번
     - 입력예시 : User.user_id(회원) = 1
     - 출력 : suggestion[Suggestion.id, Suggestion.title]
    """
    suggest = suggestion_crud.get_Suggestion_title_all(db,user_id=current_user.id)
    if suggest is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    return suggest