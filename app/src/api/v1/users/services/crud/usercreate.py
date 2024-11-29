
from fastapi import Depends,APIRouter, HTTPException
from requests import Session
from app.src.api.v1.users.model.users import User
from app.database.database import get_db
from app.src.api.v1.users.schema.userschemas import StudentCreate, StudentResponse, TeacherCreate, TeacherResponse, TeacherSalary
from app.src.api.v1.users.user_authentication.auth import authorize_admin, get_password_hash
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

# REQUIREMENT: Add Student (Admin Only)
@router.post("/add_student")
def add_student(student: StudentCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):

    db_student = db.query(User).filter(User.username == student.username).first()
    if db_student:
        raise HTTPException(status_code=400, detail="User already added")

    
    hashed_password = get_password_hash(student.password)
    new_student = User(username=student.username, email=student.email, hashed_password=hashed_password, role="student" , class_name=student.class_name)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    response_data = {
        "id": new_student.id,
        "username": new_student.username,
        "email": new_student.email,
        "class": new_student.class_name
    }
    return Response(
        status_code=200,
        message="Student added successfully",
        data= response_data 
    ).send_success_response()


# REQUIREMENT: Add Teacher (Admin Only)
@router.post("/add_teacher")
def add_teacher(teacher: TeacherCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):

    db_teacher = db.query(User).filter(User.username == teacher.username).first()
    if db_teacher:
        raise HTTPException(status_code=400, detail="User already added")
    
    hashed_password = get_password_hash(teacher.password)
    new_teacher = User(username=teacher.username, email=teacher.email, hashed_password=hashed_password, role="teacher",class_name=teacher.class_name,subject_name=teacher.subject_name)
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    
    response_data = {
        "id": new_teacher.id,
        "username": new_teacher.username,
        "email": new_teacher.email,
        "class": new_teacher.class_name,
        "subject": new_teacher.subject_name
    }
    return Response(
        status_code=200,
        message="Teacher added successfully",
        data= response_data 
    ).send_success_response()


# REQUIREMENT:Add teacher salary by admin
@router.post("/add_salary/{teacher_id}" )
def add_teacher_salary(teacher_id: int, salary: TeacherSalary, db: Session = Depends(get_db), current_user: User = Depends(authorize_admin) ):
    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()

    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")

    teacher.salary = salary.salary
    db.commit()
    db.refresh(teacher)

    response_data = {
        "id": teacher.id,
        "username": teacher.username,
        "salary":teacher.salary
    }
    return Response(
        status_code=200,
        message="Teacher salary added successfully",
        data= response_data 
    ).send_success_response()