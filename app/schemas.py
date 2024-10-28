

from pydantic import BaseModel

class AdminCreate(BaseModel):
    username: str
    email: str
    password: str

class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    access_token: str
    token_type: str

    class Config:
        orm_mode = True

class AdminLogin(BaseModel):
    
    username: str
    password: str


class StudentCreate(BaseModel):
    username: str
    email: str
    password: str

class StudentResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True


class TeacherCreate(BaseModel):
    username: str
    email: str
    password: str

class TeacherResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True
