
from fastapi import Depends, APIRouter, HTTPException , status
from requests import Session
from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.schema.userschemas import StudentResponse
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()


# REQUIREMENT: Student - View Own Info
@router.get("/student/{student_id}" )
def view_own_student_info(student_id: str,  db: Session = Depends(get_db),current_user=Depends(authorize_user)):
    
    student = db.query(User).filter(User.id == student_id ,User.role == "student").first()
    
    if not student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student authorization required")
    
    response_data = {
        "id": student.id,
        "username": student.username,
        "email": student.email,
        "class": student.class_name,
    }
    return Response(
        status_code=200,
        message="Student details retrieved successfully",
        data= response_data 
    ).send_success_response()
