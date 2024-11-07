from enum import Enum
from os import stat
import re
from fastapi import HTTPException
from pydantic import BaseModel, Field, EmailStr, validator , constr
from typing import Optional
from datetime import date
# 1. Schema for Admin Registration with Validations
class AdminCreate(BaseModel):
    username: str = Field(..., pattern="^[a-zA-Z0-9_]+$", max_length=20)  # Alphanumeric with optional underscores
    email: EmailStr  # Ensures valid email format (e.g., test@example.com)
    password: str = Field(min_length=8)  # At least 8 characters
    phone_number: str = Field(..., pattern="^[0-9]{10}$")  # Exactly 10 digits

    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit.')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter.')
        return v

# 2. Response Schema for Admin
class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None

    class Config:
        orm_mode = True

# 3. Schema for Unified Login
class UserLogin(BaseModel):
    username: str
    password: str
    role: str = Field(..., pattern="^(admin|teacher|student)$")  # Restricts role to admin, teacher, or student

# 4. Response Schema after Login (Common for All Roles)
class UserLoginResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    access_token: str = None  # JWT token only included if the role is admin
    token_type: str = None

    class Config:
        orm_mode = True

# 5. Create and Response Schemas for Student and Teacher
class StudentCreate(BaseModel):
    username: str = Field(..., pattern="^[a-zA-Z0-9_]+$", max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)

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

    class Config:
        orm_mode = True

class TeacherCreate(BaseModel):
    username: str = Field(..., pattern="^[a-zA-Z0-9_]+$", max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)

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

    class Config:
        orm_mode = True

class ClassSubjectCreate(BaseModel):
    class_name: str
    subject_name: str

class ClassSubjectUpdate(BaseModel):
    class_name: str
    subject_name: str

# 7. Token Response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# 8. Update Schemas for Teacher and Student
class UserUpdate(BaseModel):
    username: str = Field(None, pattern="^[a-zA-Z0-9_]+$", max_length=20)
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

class ExamStatus(str, Enum):
    completed = "completed"
    scheduled = "scheduled"
class ExamResponse(BaseModel):
    id: int
    class_name: str
    subject: str
    date: str
    status: str
    marks: int

    class Config:
        orm_mode = True

class TeacherSalary(BaseModel):
    salary: float = Field(..., gt=0, description="Salary must be a positive number")

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[int] = None
    # Add other class fields here

class SubjectUpdate(BaseModel):
    name: Optional[str] = None

class PasswordResetRequest(BaseModel):
    user_id: int
    new_password: str = Field(..., min_length=8, max_length=128)

# Password validation function
def validate_password(password: str):
    if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=stat.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long, include a number, and a capital letter."
        )
    
