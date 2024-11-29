
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from sqlalchemy import Enum

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