from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SuggestionSchema(BaseModel):
    id: int
    user_id: int
    title: str
    content: Optional[str] = None
    date: datetime


class SuggestionContentSchema(BaseModel):
    title: str
    content: Optional[str] = None


class SuggestionTitleSchema(BaseModel):
    id: int
    title: str

