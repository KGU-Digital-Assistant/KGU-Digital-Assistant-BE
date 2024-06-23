from sqlalchemy.orm import Session

from .company_schema import CompanyCreate
from models import Company

def company_create(_company_create: CompanyCreate, db: Session):
    db_company = Company(
        name=_company_create.name,
        owner=_company_create.owner,
        cellphone=_company_create.cellphone,
        certificate=_company_create.certificate
        )
    db.add(db_company)
    db.commit()