
from fastapi import Depends, APIRouter, HTTPException, status
from requests import Session
from app.database.database import get_db
from app.src.api.v1.exam.model.exammodel import Exam
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()


#REQUIREMENT: teacher and student view exam schedule
@router.get("/teacher-student/view_exam/{exam_id}", status_code=status.HTTP_200_OK)
def view_exam_schedule(
    exam_id: int,
    current_user=Depends(authorize_user),  
    db: Session = Depends(get_db)
):
    
    if current_user.role not in ["student", "teacher"]:
        raise HTTPException(status_code=403, detail="Only students and teachers can view exam schedules.")

    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == "teacher":
        if exam.class_name != current_user.class_name or exam.subject_name != current_user.subject_name:
            raise HTTPException(status_code=403, detail="You are not authorized to view this exam schedule.")
    
    elif current_user.role == "student":
        if exam.class_name != current_user.class_name:
            raise HTTPException(status_code=403, detail="You are not authorized to view this exam schedule.")

    response_data = {
        
        "id": exam.id,
        "exam_class": exam.class_name,
        "exam_subject":exam.subject_name,
        'exam_date': exam.date,
        "exam_marks": exam.marks,
    }
    return Response(
        status_code=200,
        message="Exam details retrieved successfully",
        data= response_data 
    ).send_success_response()