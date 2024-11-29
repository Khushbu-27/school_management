
from fastapi import Depends, APIRouter, HTTPException, Query ,status
from requests import Session
from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.schema.userschemas import StudentResponse, TeacherResponse, TeacherSalary
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

# REQUIREMENT: Teacher - View Own Info
@router.get("/teacher/{teacher_id}")
def view_own_teacher_info(teacher_id: int,db: Session = Depends(get_db) , current_user=Depends(authorize_user)):

    teacher = db.query(User).filter(User.id == teacher_id ,User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    response_data = {
        "id": teacher.id,
        "username": teacher.username,
        "email": teacher.email,
        "class": teacher.class_name,
        "subject": teacher.subject_name,
    }
    return Response(
        status_code=200,
        message="Teacher details retrieved successfully",
        data= response_data 
    ).send_success_response()


# REQUIREMENT: view teacher own salary
@router.get("/teacher/view_salary/{teacher_id}")
def view_my_salary( db: Session = Depends(get_db), current_user = Depends(authorize_user)):
    
   
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized to view this salary")
    
    salary = db.query(User).filter(User.salary == current_user.salary).first()

    if current_user.salary is None:
        raise HTTPException(status_code=404, detail="Salary not set for this teacher")

    response_data = {
        "id": current_user.id,
        "username": current_user.username,
        "salary": current_user.salary,
    }
    return Response(
        status_code=200,
        message="Teacher salary details retrieved successfully",
        data= response_data 
    ).send_success_response()


# REQUIREMENT: Teacher - View Student Info (View Only)
@router.get("/teacher/view_student/{student_id}")
def teacher_view_student_info(student_id: int, current_user = Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    response_data = {
        "id": student.id,
        "username": student.username,
        "email": student.email,
        "class": student.class_name,
    }
    return Response(
        status_code=200,
        message="student details retrieved successfully",
        data= response_data 
    ).send_success_response()
