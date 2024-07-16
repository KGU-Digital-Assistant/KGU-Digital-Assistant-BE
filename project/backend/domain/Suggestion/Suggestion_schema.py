from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Suggestion_schema(BaseModel):
    id: int
    user_id: int
    title: str
    content: Optional[str] = None
    date: datetime

class Suggestion_content_schema(BaseModel):
    title: str
    content: Optional[str] = None

class Suggestion_title_schema(BaseModel):
    id: int
    title: str

