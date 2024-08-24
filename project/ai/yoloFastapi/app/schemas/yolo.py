from pydantic import BaseModel
from typing import Set
import decimal


class ImageAnalysisResponse(BaseModel):
    id: int
    name: str
    kcal: decimal.Decimal
    labels: Set[str]