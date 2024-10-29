

from pydantic import BaseModel

class AdminCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str

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
    role: str

class UserLoginResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    access_token: str
    token_type: str

    class Config:
        orm_mode = True
        
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


# class StudentLoginResponse(BaseModel):
#     id: int
#     username: str
#     email: str
#     access_token: str
#     token_type: str

#     class Config:
#         orm_mode = True


# class TeacherLoginResponse(BaseModel):
#     id: int
#     username: str
#     email: str
#     access_token: str
#     token_type: str

#     class Config:
#         orm_mode = True

class ClassCreate(BaseModel):
    name: str

class ClassResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class SubjectCreate(BaseModel):
    name: str
    class_id: int

class SubjectResponse(BaseModel):
    id: int
    name: str
    class_id: int

    class Config:
        orm_mode = True