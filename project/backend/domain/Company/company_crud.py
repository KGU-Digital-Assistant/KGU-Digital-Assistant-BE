from sqlalchemy.orm import Session

from domain.Company.company_schema import CompanyCreate, CompanyUpdate
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


def get_company_list(db: Session, skip: int = 0, limit: int = 10):
    _company_list = db.query(Company).order_by(Company.name.desc())

    total = _company_list.count()
    company_list = _company_list.offset(skip).limit(limit).all()
    return total, company_list


def get_company_by_id(db: Session, company_id: int):
    return db.query(Company).filter(Company.id == company_id).first()


def company_update(db: Session, db_company: Company, _company_update: CompanyUpdate):
    db_company.name = _company_update.name
    db_company.owner = _company_update.owner
    db_company.cellphone = _company_update.cellphone
    db_company.certificate = _company_update.certificate
    db.add(db_company)
    db.commit()


def get_company_by_name(db: Session, company_name: str):
    return db.query(Company).filter(Company.name == company_name).first()


def delete_company(db: Session, db_company: Company):
    db.delete(db_company)
    db.commit()