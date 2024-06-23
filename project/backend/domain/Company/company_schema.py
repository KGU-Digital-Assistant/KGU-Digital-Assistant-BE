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


