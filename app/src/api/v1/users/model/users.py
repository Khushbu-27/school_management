
from sqlalchemy import Column, Integer, String , Date
from sqlalchemy.orm import relationship
from app.database.database import Base
# from app.src.api.v1.marks.model.marksmodel import StudentMarks


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

    marks = relationship("StudentMarks", back_populates="user")
