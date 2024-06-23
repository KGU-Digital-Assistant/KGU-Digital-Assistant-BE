from fastapi import APIRouter, Depends, HTTPException

from domain.Company.company_schema import CompanyCreate
from domain.Company.company_crud import company_create
from sqlalchemy.orm import Session
from starlette import status
from database import get_db

router = APIRouter(
    prefix="/api/company",
)

@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def create_company(_company_create: CompanyCreate,
                         db: Session = Depends(get_db)):
    return company_create(_company_create, db)
