import os
from fastapi import File, UploadFile, Depends, APIRouter, HTTPException, Query, status
from requests import Session
from datetime import datetime
from app.database.database import get_db
from app.src.api.v1.exam.model.exammodel import Exam
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

UPLOAD_DIR = "uploads/test_papers"  
os.makedirs(UPLOAD_DIR, exist_ok=True) 

@router.post("/teacher/add_exam", status_code=status.HTTP_201_CREATED)
def add_exam_schedule(
    date: str = Query(...),
    status: str = Query(...),
    marks: int = Query(...),
    test_paper: UploadFile = File(...),  
    db: Session = Depends(get_db),
    current_user=Depends(authorize_user)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add exams.")

    class_name = current_user.class_name
    subject_name = current_user.subject_name
    teacher_name = current_user.username

    if current_user.class_name != class_name or current_user.subject_name != subject_name:
        raise HTTPException(status_code=403, detail="You cannot add an exam for this class or subject.")

    try:
        exam_date = datetime.strptime(date, "%d-%m-%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY.")

    if exam_date < datetime.today().date():
        raise HTTPException(status_code=400, detail="Exam date cannot be in the past.")

    status = status.lower()
    if status not in ['scheduled', 'completed']:
        raise HTTPException(status_code=400, detail="Invalid status. Choose either 'scheduled' or 'completed'.")

    existing_exam = db.query(Exam).filter(
        Exam.subject_name == subject_name,
        Exam.date == exam_date
    ).first()

    if existing_exam:
        raise HTTPException(status_code=400, detail="Exam for this subject has already been added.")
    
    if test_paper.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    file_path = os.path.join(UPLOAD_DIR, f"{subject_name}_{exam_date}.pdf")
    with open(file_path, "wb") as f: 
        f.write(test_paper.file.read())
    
    new_exam = Exam(
        class_name=class_name,
        subject_name=subject_name,
        date=exam_date,
        status=status,
        marks=marks,
        test_paper=file_path  
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)

    response_data = {
        "data": {
            "id": new_exam.id,
            "class_name": new_exam.class_name,
            "subject_name": new_exam.subject_name,
            "date": new_exam.date,
            "status": new_exam.status,
            "marks": new_exam.marks,
            "test_paper": new_exam.test_paper,
        },
        "added_by": teacher_name
    }
    return Response(
        status_code=200,
        message="New Exam added successfully",
        data=response_data
    ).send_success_response()
