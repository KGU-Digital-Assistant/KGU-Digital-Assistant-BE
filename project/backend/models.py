from sqlalchemy import Column, Integer, DateTime, String, ForeignKey

from database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    address = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    birthday = Column(DateTime, nullable=False)
    create_date = Column(DateTime, nullable=False)

class Payment(Base):
    __tablename__ = "payment"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    create_date = Column(DateTime, nullable=False)

class Trainer(Base):
    __tablename__ = "trainer"

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    company = Column(String, nullable=False)
    specialized_field = Column(String, nullable=False)
    registration_date = Column(DateTime, nullable=False)

class Management(Base):
    __tablename__ = "management"

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("trainer.id"), nullable=False)


