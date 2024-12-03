import os
from fastapi import File, Request, UploadFile, Depends, APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from requests import Session
from datetime import datetime
from app.database.database import get_db
from app.src.api.v1.exam.model.exammodel import Exam
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response
from app.src.api.v1.exam.utils.upload_file_utils import UPLOAD_DIR
from app.src.api.v1.users.model.users import User


router = APIRouter()

# UPLOAD_DIR = "uploads/test_papers"  
# os.makedirs(UPLOAD_DIR, exist_ok=True) 

@router.post("/teacher/add_exam", status_code=status.HTTP_201_CREATED)
def add_exam_schedule(
    request: Request,
    date: str = Query(...),
    status: str = Query(...),
    marks: int = Query(...),
    # test_paper: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user=Depends(authorize_user),
    
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add exams.")
    
    class_name = current_user.class_name
    subject_name = current_user.subject_name
    teacher_name = current_user.username
    
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
            raise HTTPException(status_code=400, detail=f"Exam for this subject have already been added.")
   
    # if test_paper.content_type != "application/pdf":
    #     raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    # test_paper_name = f"{subject_name}_{exam_date}.pdf"
    # file_path = os.path.join(UPLOAD_DIR, test_paper_name)
    # with open(file_path, "wb") as f:
    #     f.write(test_paper.file.read())

    new_exam = Exam(
        class_name=class_name,
        subject_name=subject_name,
        date=exam_date,
        status=status,
        marks=marks,
        # test_paper=test_paper_name,  
        teacher_name=teacher_name,
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    
    # base_url = str(request.base_url).rstrip("/")
    # file_url = f"{base_url}/static/{file_name}"

    response_data = {
        "data": {
            "id": new_exam.id,
            "class_name": new_exam.class_name,  
            "subject_name": new_exam.subject_name,
            "date": new_exam.date,
            "status": new_exam.status.value,
            "marks": new_exam.marks,
            # "test_paper": test_paper_name,  
        },
        "added_by": teacher_name
    }
    return Response(
        status_code=200,
        message="New Exam added successfully",
        data=response_data
    ).send_success_response()
