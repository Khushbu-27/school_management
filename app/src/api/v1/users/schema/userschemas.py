
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
