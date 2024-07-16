from typing import List

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    owner: str
    cellphone: str
    # address: str
    certificate: bool

    class Config:
        from_attributes = True
        check_fields = False
        arbitrary_types_allowed = True


class CompanyList(BaseModel):
    total: int = 0
    CompanyList: list[CompanyCreate] = []


class CompanySchema(BaseModel):
    id: int
    name: str
    owner: str
    cellphone: str
    certificate: bool


class CompanyUpdate(BaseModel):
    name: str
    owner: str
    cellphone: str
    certificate: bool



