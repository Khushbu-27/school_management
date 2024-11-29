
from typing_extensions import List
from fastapi import Depends, APIRouter, HTTPException
from requests import Session
from app.database.database import get_db
from app.src.api.v1.exam.model.exammodel import Exam
from app.src.api.v1.marks.model.marksmodel import StudentMarks
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

# REQUIREMENT: student - view student own marks
@router.get("/students/{student_id}/marks")
def get_student_marks(student_id: int, db: Session = Depends(get_db), current_user=Depends(authorize_user), response_model=List[StudentMarks]):

    if current_user.role != "student" or current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    eligible_exams = db.query(Exam).filter(Exam.class_name == current_user.class_name).all()
    if not eligible_exams:
        raise HTTPException(status_code=403, detail="You are not authorized to view this exam marks.")
    
    marks_records = (
        db.query(
            StudentMarks.id,
            StudentMarks.student_name,
            StudentMarks.class_name,
            StudentMarks.subject_name,
            StudentMarks.student_marks.label("student_marks"),
            Exam.date
        )
        .join(Exam, StudentMarks.exam_id == Exam.id)
        .filter(StudentMarks.student_name == current_user.username)
        .all()
    )

    if not marks_records:
        raise HTTPException(status_code=404, detail="Marks not found for the student")

    return Response(
        data=[
            {
                "id": record.id,
                "student_name": record.student_name,
                "class_name": record.class_name,
                "subject_name": record.subject_name,
                "student_marks": record.student_marks,
                "exam_date": record.date,
            }
            for record in marks_records
        ],
        status_code=200,
        message="Student marks details retrieved successfully"
    ).send_success_response()


    
