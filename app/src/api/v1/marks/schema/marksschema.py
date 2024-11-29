
from datetime import date
from typing import List
from pydantic import BaseModel, Field


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

class StudentMarks(BaseModel):
    student_name: str
    class_name: int = Field(..., ge=0, le=12, description="Marks must be between 0 and 12.") 
    subject_name: str
    student_marks: int 
    exam_date: date

    class Config:
        orm_mode = True