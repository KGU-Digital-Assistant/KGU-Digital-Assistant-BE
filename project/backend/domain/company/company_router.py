from fastapi import APIRouter, Depends, HTTPException

from domain.company import company_crud
from domain.company.company_schema import CompanyCreate, CompanyList, CompanySchema, CompanyUpdate
from sqlalchemy.orm import Session
from starlette import status
from database import get_db

router = APIRouter(
    prefix="/company",
)


@router.post("/create", status_code=status.HTTP_204_NO_CONTENT)
def create_company(_company_create: CompanyCreate,
                         db: Session = Depends(get_db)):
    return company_crud.company_create(_company_create, db)


@router.get("/list", status_code=status.HTTP_200_OK, response_model=CompanyList)
def list_company(db: Session = Depends(get_db), page: int = 0, size: int = 10):
    total, company_list = company_crud.get_company_list(db, skip=page * size, limit=size)
    return {
        "total": total,
        "company_list": company_list
    }


@router.get("/get/{company_id}", status_code=status.HTTP_200_OK, response_model=CompanySchema)
def get_company(company_id: int, db: Session = Depends(get_db)):
    return company_crud.get_company_by_id(db, company_id)


@router.patch("/update", status_code=status.HTTP_204_NO_CONTENT)
def update_company(_company_update: CompanyUpdate, db: Session = Depends(get_db)):
    db_company = company_crud.get_company_by_name(db, company_name=_company_update.name)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="company not found"
        )

    company_crud.company_update(db=db, db_company=db_company, _company_update=_company_update)


@router.delete("/delete/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    db_company = company_crud.get_company_by_id(db, company_id)
    if not db_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="company not found"
        )

    company_crud.delete_company(db=db, db_company=db_company)
