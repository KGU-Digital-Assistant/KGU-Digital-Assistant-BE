from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from models import Suggestion, User
from domain.suggestion import suggestion_schema, suggestion_crud
from domain.user.user_router import get_current_user
from datetime import datetime, timedelta
from starlette import status

router = APIRouter(
    prefix="/suggest"
)


@router.delete("/remove/{suggest_id}")
async def remove_suggest(suggest_id: int,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
     등록한 의견 삭제 : 27page 2번
      - 입력예시 :id = 1
     """
    suggest = suggestion_crud.get_suggest(db, id=suggest_id)
    if suggest is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    if suggest.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="you can't remove this suggestion")
    db.delete(suggest)
    db.commit()
    return {"detail": "Suggest deleted successfully"}


@router.patch("/update/{suggest_id}", response_model=suggestion_schema.SuggestionSchema)
async def update_suggest(suggest_id: int, title: str = Form(...), content: str = Form(...),
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
     등록한 의견 수정 : 27page 2번
      - 입력예시 :id = 1, title: 집가고싶어, content: 집가고싶어
     """
    suggest = suggestion_crud.get_suggest(db, suggest_id)
    if suggest is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    if current_user.id != suggest.user_id:
        raise HTTPException(status_code=403, detail="you are not the owner of this suggestion")
    suggest.title = title
    suggest.content = content
    db.commit()
    db.refresh(suggest)
    return suggest


@router.get("/get/{suggest_id}/text", response_model=suggestion_schema.SuggestionContentSchema)
def get_Suggest_id(suggest_id: int, db: Session = Depends(get_db)):
    """
    개발자 의견제출  : 27page 1번
     - 입력예시 : Suggestion.id = 1
     - 출력 : Suggestion.title, Suggestion.content
    """
    suggest = suggestion_crud.get_Suggestion_content(db, id=suggest_id)
    if suggest is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    return suggest


@router.post("/post", response_model=suggestion_schema.SuggestionSchema)
def post_Suggest(current_user: User = Depends(get_current_user), title: str = Form(...), content: str = Form(...),
                 db: Session = Depends(get_db)):
    """
    개발자 의견제출  : 27page 3번
     - 입력예시 :  title = "치킨", content = "치킨너무비싸"
    """
    new_suggest = Suggestion(
        user_id=current_user.id,
        title=title,
        content=content,
        date=datetime.utcnow() + timedelta(hours=9)
    )
    db.add(new_suggest)
    db.commit()
    db.refresh(new_suggest)
    return new_suggest


@router.get("/get/all_title", response_model=List[suggestion_schema.SuggestionTitleSchema])
def get_Suggest_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    개발자 의견제출  : 27page 3번
     - 입력예시 :
     - 출력 : suggestion[Suggestion.id, Suggestion.title]
    """
    suggest = suggestion_crud.get_Suggestion_title_all(db, user_id=current_user.id)
    if suggest is None:
        raise HTTPException(status_code=404, detail="suggestion not found")
    return suggest
