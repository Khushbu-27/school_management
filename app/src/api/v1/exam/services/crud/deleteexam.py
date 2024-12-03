import os
from fastapi import Depends, APIRouter, HTTPException
from requests import Session
from app.database.database import get_db
from app.src.api.v1.exam.model.exammodel import Exam
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response
from app.src.api.v1.exam.utils.upload_file_utils import UPLOAD_DIR

router = APIRouter()

@router.delete("/teacher/delete_exam/{exam_id}")
def delete_exam(exam_id: int, current_user=Depends(authorize_user), db: Session = Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete exams")
    
    teacher_name = current_user.username
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if exam.teacher_name != current_user.username:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this exam schedule.")

    if exam.class_name != current_user.class_name or exam.subject_name != current_user.subject_name:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this exam schedule for this class/subject.")

    # Construct the file path to the test paper
    # file_path = os.path.join(UPLOAD_DIR, exam.test_paper)
    
    # Ensure the file exists before trying to delete
    # if os.path.exists(file_path):
    #     os.remove(file_path)  # Delete the file
    # else:
    #     # If the file does not exist, raise an error indicating it's missing
    #     raise HTTPException(status_code=404, detail="Test paper file not found in storage")

    db.delete(exam)
    db.commit()
    
    response_data = {
        "id": exam.id,
        "exam_class": exam.class_name,
        "exam_subject": exam.subject_name,
        "exam_date": exam.date,
        "marks": exam.marks,
        "added_by": teacher_name
    }
    
    return Response(
        status_code=200,
        message="Exam deleted successfully, including the test paper file",
        data=response_data
    ).send_success_response()
