
from fastapi import Depends, APIRouter, HTTPException , status
from requests import Session
from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.schema.userschemas import TeacherResponse, UserUpdate
from app.src.api.v1.users.user_authentication.auth import authorize_user, get_password_hash
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

# REQUIREMENT: Teacher - Update Own Info
@router.put("/teacher/{teacher_id}/update", response_model=TeacherResponse)
def update_own_info(update_data: UserUpdate, current_user = Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    teacher = db.query(User).filter(User.username == current_user.username).first()
    # if update_data.username:
    #     teacher.username = update_data.username
    if update_data.password:
        teacher.hashed_password = get_password_hash(update_data.password)
    db.commit()
    db.refresh(teacher)
    response_data = {
        "id": teacher.id,
        "username": teacher.username,
        "email":teacher.email,
        "password": teacher.hased_password
    }
    return Response(
        status_code=200,
        message="Teacher detail updated successfully",
        data= response_data 
    ).send_success_response()