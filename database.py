from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from passlib.context import CryptContext
import os

DB_PATH = "sqlite:///diet_mate.db"
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    height = Column(Float)
    weight = Column(Float)
    gender = Column(String)
    age = Column(Integer)

    records = relationship("DailyRecord", back_populates="user")
    goals = relationship("Goal", back_populates="user")

class DailyRecord(Base):
    __tablename__ = "daily_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String, nullable=False)  # YYYY-MM-DD
    weight = Column(Float)
    breakfast = Column(String)
    lunch = Column(String)
    dinner = Column(String)
    snack = Column(String)
    exercise_type = Column(String)
    exercise_time = Column(Integer)  # minutes
    water = Column(Float)  # liters
    sleep_time = Column(Float)  # hours

    user = relationship("User", back_populates="records")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_weight = Column(Float)
    target_date = Column(String)

    user = relationship("User", back_populates="goals")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
