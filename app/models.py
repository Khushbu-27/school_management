

from sqlalchemy import Column, Integer, String , ForeignKey , Enum , Date , Float
# from datetime import date

from app.database import Base
from sqlalchemy.orm import relationship
import enum

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone_number = Column(Integer ,nullable=True)
    email = Column(String, unique=True)
    role = Column(String) 
    salary = Column(Integer, nullable=True)  
    class_name = Column(Integer, nullable=True)  
    subject_name = Column(String, nullable=True)
    attendance = Column(Integer, default=0)
    last_login_date = Column(Date, nullable=True)
    
    def set_salary(self, salary):
        if not isinstance(salary, int) or salary < 0:
            raise ValueError("Salary must be a positive integer")
        self.salary = salary

    marks = relationship(
        "StudentMarks",
        primaryjoin="foreign(StudentMarks.student_name) == remote(User.username)",
        back_populates="student",
        viewonly=True,
    )

class ExamStatus(enum.Enum):
    completed = "completed"
    scheduled = "scheduled"

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(Integer, nullable=False)
    subject_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(ExamStatus), nullable=False , default=ExamStatus.scheduled)
    marks = Column(Integer, nullable=False)

    marks_received = relationship(
        "StudentMarks",
        primaryjoin="foreign(StudentMarks.exam_id) == Exam.id",
        back_populates="exam",
        viewonly=True,
    )

class StudentMarks(Base):
    __tablename__ = "student_marks"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, nullable=False)  
    class_name = Column(Integer, nullable=False)    
    subject_name = Column(String, nullable=False) 
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)   
    student_marks = Column(Integer, nullable=False) 

    student = relationship(
         "User",
        primaryjoin="foreign(StudentMarks.student_name) == remote(User.username)",
        back_populates="marks",
        viewonly=True,
    )
    exam = relationship(
        "Exam",
        primaryjoin="StudentMarks.exam_id == remote(Exam.id)",
        back_populates="marks_received",
        viewonly=True,
    )