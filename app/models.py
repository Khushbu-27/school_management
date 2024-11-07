

from sqlalchemy import Column, Integer, String , ForeignKey , Enum , Date , Float
# from datetime import date

from .database import Base
from sqlalchemy.orm import relationship
import enum

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone_number = Column(String(10))
    email = Column(String, unique=True)
    role = Column(String) 
    salary = Column(Integer, nullable=True)  
    attendance = Column(Integer, default=0)
    
    def set_salary(self, salary):
        if not isinstance(salary, int) or salary < 0:
            raise ValueError("Salary must be a positive integer")
        self.salary = salary

class ClassSubject(Base):
    __tablename__ = "class_subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, index=True)  
    subject_name = Column(String, index=True)  
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    student = relationship("User", backref="class_subjects", foreign_keys=[student_id])

    def __init__(self, class_name: str, subject_name: str, student_id: int):
        self.class_name = class_name
        self.subject_name = subject_name
        self.student_id = student_id

class ExamStatus(enum.Enum):
    completed = "completed"
    scheduled = "scheduled"

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(ExamStatus), nullable=False)
    marks = Column(Integer, nullable=False)
