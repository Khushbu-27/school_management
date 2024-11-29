
from fastapi import Depends, APIRouter, HTTPException , status
from requests import Session
from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.schema.userschemas import TeacherSalary, UserUpdate
from app.src.api.v1.users.user_authentication.auth import authorize_admin, get_password_hash
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

# REQUIREMENT: Admin- Update Own Info
@router.put("/admin/{admin_id}/update")
def update_own_info(update_data: UserUpdate, current_user = Depends(authorize_admin), db: Session = Depends(get_db)):

    admin = db.query(User).filter(User.username == current_user.username).first()
    
    if not admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin authorization required")
    
    if update_data.password:
        admin.hashed_password = get_password_hash(update_data.password)
    db.commit()
    db.refresh(admin)
    response_data = {
        "id": admin.id,
        "username": admin.username,
        "email": admin.email,
        "password": admin.hased_password
    }
    return Response(
        status_code=200,
        message="Admin detail updated successfully",
        data= response_data 
    ).send_success_response()


# REQUIREMENT: update teacher salary by admin
@router.put("/admin/{teacher_id}/update_salary")
def update_teacher_salary(
    teacher_id: int,
    salary: TeacherSalary, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(authorize_admin)
):
    
    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()

    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    if teacher.salary is None:
        raise HTTPException(status_code=400, detail="Teacher salary must be set first before updating")

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
        message="Teacher salary updated successfully",
        data= response_data 
    ).send_success_response()