
from datetime import datetime
from fastapi import Depends, APIRouter, HTTPException, Query , status
from requests import Session
from app.database.database import get_db
from app.src.api.v1.exam.model.exammodel import Exam
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

# REQUIREMENT: update exam schedule by teacher only
@router.put("/teacher/update_exam/{exam_id}", status_code=status.HTTP_200_OK)
def update_exam_schedule(
    exam_id: int,
    date: str = Query(...),
    status: str = None,
    marks: int = None,
    current_user = Depends(authorize_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update exams.")
    
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if current_user.class_name != exam.class_name or current_user.subject_name != exam.subject_name:
        raise HTTPException(status_code=403, detail="You cannot update an exam for this class or subject.")
    
    try:
        exam_date = datetime.strptime(date, "%d-%m-%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY.")
    
    if exam_date < datetime.today().date():
        raise HTTPException(status_code=400, detail="Exam date cannot be in the past.")
    
    if status:
        status = status.lower()
        if status not in ['scheduled', 'completed']:
            raise HTTPException(status_code=400, detail="Invalid status. Choose either 'scheduled' or 'completed'.")

    if status:
        exam.status = status
    if marks is not None:
        exam.marks = marks
    exam.date = exam_date

    db.commit()
    
    response_data = {
        "id": exam.id,
        "exam_class": current_user.class_name,  
        "exam_subject": current_user.subject_name,  
        'exam_date': exam.date,
        "exam_status": exam.status,
        "exam_marks": exam.marks,
        "updated_by": current_user.username 
    }
    
    return Response(
        status_code=200,
        message="Exam updated successfully",
        data=response_data
    ).send_success_response()