
from sqlalchemy import Column, Date, Enum, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from app.database.database import Base
from sqlalchemy.orm import relationship 
import enum


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
    test_paper = Column(String, nullable=True)

    marks_received = relationship("StudentMarks", back_populates="exam")
