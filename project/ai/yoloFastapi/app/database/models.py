from sqlalchemy import Column, TEXT, INT, VARCHAR, DECIMAL
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Nutritions(Base):
    __tablename__ = "nutritions"

    id = Column(INT, nullable=False, primary_key=True, unique=True)
    name = Column(VARCHAR(25), nullable=False, unique=True)
    weight = Column(DECIMAL(6, 2), nullable=False)
    kcal = Column(DECIMAL(6, 2), nullable=False)
    carbonate = Column(DECIMAL(6, 2), nullable=False)
    sugar = Column(DECIMAL(6, 2), nullable=False)
    fat = Column(DECIMAL(6, 2), nullable=False)
    protein = Column(DECIMAL(6, 2), nullable=False)
    calcium = Column(DECIMAL(6, 2), nullable=False)
    p = Column(DECIMAL(6, 2), nullable=False)
    salt = Column(DECIMAL(6, 2), nullable=False)
    mg = Column(DECIMAL(6, 2), nullable=False)
    iron = Column(DECIMAL(6, 2), nullable=False)
    zinc = Column(DECIMAL(6, 2), nullable=False)
    cholesterol = Column(DECIMAL(6, 2), nullable=False)
    trans = Column(DECIMAL(6, 2), nullable=False)
