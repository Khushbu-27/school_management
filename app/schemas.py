
from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime
import re

# Admin Registration Schema 
class AdminCreate(BaseModel):
    username: str = Field(..., pattern="^[a-zA-Z0-9_]+$", max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str
    phone_number: int  

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if len(str(v)) != 10:
            raise ValueError('Phone number must be exactly 10 digits.')
        return v

    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit.')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter.')
        return v

#  Response Schema for Admin
class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None

    class Config:
        orm_mode = True

# Login Schema
class UserLogin(BaseModel):
    username: str
    password: str
    role: str = Field(..., pattern="^(admin|teacher|student)$")  

#  Response Schema after Login (Common for All Roles)
class UserLoginResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    access_token: Optional[str] = None  
    token_type: Optional[str] = None

    class Config:
        orm_mode = True

# Create and Response Schemas for Student and Teacher 
class StudentCreate(BaseModel):
    username: str = Field(..., pattern="^[a-zA-Z0-9_]+$", max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)
    class_name: int = Field(..., ge=0, le=12, description="Marks must be between 0 and 12.") 

    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit.')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter.')
        return v

class StudentResponse(BaseModel):
    id: int
    username: str
    email: str
    class_name: int = Field(..., ge=0, le=12, description="Marks must be between 0 and 12.") 

    class Config:
        orm_mode = True

class TeacherCreate(BaseModel):
    username: str = Field(..., pattern="^[a-zA-Z0-9_]+$", max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)
    class_name: int = Field(..., ge=0, le=12, description="Marks must be between 0 and 12.") 
    subject_name: str 

    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit.')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter.')
        return v

class TeacherResponse(BaseModel):
    id: int
    username: str
    email: str
    class_name: int = Field(..., ge=0, le=12, description="Marks must be between 0 and 12.") 
    subject_name: str

    class Config:
        orm_mode = True

# Exam and ExamStatus Schemas
class ExamStatus(str, Enum):
    completed = "completed"
    scheduled = "scheduled"

class ExamCreate(BaseModel):
    class_name: int = Field(..., ge=0, le=12, description="Marks must be between 0 and 12.") 
    subject_name: str
    date: date
    status: ExamStatus = ExamStatus.scheduled 
    marks: int = Field(..., ge=0, le=100, description="Marks must be between 0 and 100.") 

    @validator("date")
    def check_future_date(cls, v):
        if v < date.today():
            raise ValueError("Exam date cannot be in the past.")
        return v

    @validator("status", pre=True, always=True)
    def set_status(cls, v, values):
       
        if 'date' in values and values['date'] < datetime.today().date():
            return ExamStatus.completed
        return v or ExamStatus.scheduled
    
class ExamResponse(BaseModel):
    id: int
    class_name: int = Field(..., ge=0, le=12, description="Marks must be between 0 and 12.") 
    subject_name: str
    date: date
    status: ExamStatus

    class Config:
        orm_mode = True

# Teacher Generate Marks for Students
class GenerateMarks(BaseModel):
    # student_id: int
    student_name: str
    student_marks: int = Field(..., ge=0, le=100)

    class Config:
        orm_mode = True 

class GeneratedMarkResponse(BaseModel):
    exam_id: int
    student_name: str
    class_name: int
    subject_name: str
    marks: int

    class Config:
        orm_mode = True  

class MarksGenerationResponse(BaseModel):
    msg: str
    data: List[GeneratedMarkResponse]
    
    class Config:
        orm_mode = True 

# # Password Reset Request
# class PasswordResetRequest(BaseModel):
#     user_id: int
#     new_password: str = Field(..., min_length=8, max_length=128)

#     @validator('new_password')
#     def validate_password(cls, v):
#         if not any(char.isdigit() for char in v) or not any(char.isupper() for char in v):
#             raise ValueError('Password must include at least one digit and one uppercase letter.')
#         return v

class TeacherSalary(BaseModel):
    salary: float = Field(..., gt=0, description="Salary must be a positive number")

class UserUpdate(BaseModel):
    # username: str = Field(None, pattern="^[a-zA-Z0-9_]+$", max_length=20)
    password: str = Field(None, min_length=8)

    @validator('password', pre=True, always=True)
    def validate_password(cls, v):
        if v:
            if not any(char.isdigit() for char in v):
                raise ValueError('Password must contain at least one digit.')
            if not any(char.isupper() for char in v):
                raise ValueError('Password must contain at least one uppercase letter.')
        return v
class TeacherUpdate(UserUpdate):
    pass

class StudentUpdate(UserUpdate):
    pass

class StudentMarks(BaseModel):
    student_name: str
    class_name: int = Field(..., ge=0, le=12, description="Marks must be between 0 and 12.") 
    subject_name: str
    student_marks: int 
    exam_date: date

    class Config:
        orm_mode = True