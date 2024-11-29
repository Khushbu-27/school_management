
from fastapi import Depends, APIRouter, HTTPException , status
from requests import Session
from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.schema.userschemas import AdminResponse, StudentResponse, TeacherResponse
from app.src.api.v1.users.user_authentication.auth import authorize_admin
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

# REQUIREMENT: View Admin own Info
@router.get("/admin/{admin_id}")
def view_admin_info(admin_id: int, token: dict = Depends(authorize_admin), db: Session = Depends(get_db), current_user = Depends(authorize_admin)):

    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
   
    if not admin:
        return Response(
            status_code=404,
            message="Admin not found",
            data= {}
        ).send_error_response()
        
    response_data = {
        "id": admin.id,
        "username": admin.username,
        "email": admin.email,
    }
    return Response(
        status_code=200,
        message="admin details retrieved successfully",
        data= response_data 
    ).send_success_response()
        
# REQUIREMENT: Admin - View Student Info
@router.get("/admin/view_student/{student_id}")
def admin_view_student_info(student_id: int, token: str = Depends(authorize_admin), db: Session = Depends(get_db)):

    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        return Response(
            status_code=404,
            message="Student not found",
            data= {}
        ).send_error_response()
    
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


# REQUIREMENT: Admin - View Teacher Info
@router.get("/admin/view_teacher/{teacher_id}")
def admin_view_teacher_info(teacher_id: int, token: str = Depends(authorize_admin), db: Session = Depends(get_db)):

    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()
    if not teacher:
        return Response(
            status_code=404,
            message="Teacher not found",
            data= {}
        ).send_error_response()
    
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

# REQUIREMENT: View Teacher Salary by admin
@router.get("/admin/view_teacher_salary/{teacher_id}")
def view_teacher_salary(
    teacher_id: int, db: Session = Depends(get_db), current_user: User = Depends(authorize_admin)):
  
    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()

    if teacher is None:
        return Response(
            status_code=404,
            message="teacher not found",
            data= {}
        ).send_error_response()

    if teacher.salary is None:
        return Response(
            status_code=404,
            message="Salary not set for this teacher",
            data= {}
        ).send_error_response()

    response_data = {
        "teacher_id": teacher.id, 
        "username": teacher.username,
        "salary": teacher.salary}
    
    return Response(
        status_code=200,
        message="Teacher salary details retrieved successfully",
        data= response_data 
    ).send_success_response()