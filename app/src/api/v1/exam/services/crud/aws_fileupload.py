
import os
import boto3
from fastapi import File, UploadFile, Depends, APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from requests import Session
from datetime import datetime

from sqlalchemy import func
from app.database.database import get_db
from app.src.api.v1.exam.model.exammodel import Exam
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response
from app.config.aws_config import AWS_ACCESS_KEY_ID, AWS_BUCKET_NAME,AWS_SECRET_ACCESS_KEY,AWS_REGION
from app.src.api.v1.exam.utils.upload_file_utils import UPLOAD_DIR
from app.src.api.v1.users.model.users import User

teacher_router = APIRouter()


s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

@teacher_router.post("/teacher/add_paper/s3_bucket", status_code=status.HTTP_201_CREATED)
def add_testpaper_s3bucket(
    date: str = Query(...),
    status: str = Query(...),
    marks: int = Query(...),
    test_paper: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(authorize_user),
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add exams.")

    class_name = current_user.class_name
    subject_name = current_user.subject_name
    teacher_name = current_user.username

    if not teacher_name:
        raise HTTPException(status_code=400, detail="Teacher username is not available.")

    if current_user.class_name != class_name or current_user.subject_name != subject_name:
        raise HTTPException(status_code=403, detail="You cannot add an exam for this class or subject.")

    try:
        exam_date = datetime.strptime(date, "%d-%m-%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY.")

    if exam_date < datetime.today().date():
        raise HTTPException(status_code=400, detail="Exam date cannot be in the past.")

    status = status.lower()
    if status not in ["scheduled", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status. Choose either 'scheduled' or 'completed'.")

    existing_exam = db.query(Exam).filter(
        Exam.subject_name == subject_name,
        Exam.date == exam_date
    ).first()

    if existing_exam:
        raise HTTPException(status_code=400, detail="Exam for this subject has already been added.")

    if test_paper.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # Upload the file to S3
    file_key = f"test_papers/{subject_name}_{exam_date}.pdf"
    try:
        s3_client.upload_fileobj(
            test_paper.file,
            AWS_BUCKET_NAME,
            file_key,
            ExtraArgs={"ContentType": "application/pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")
 
    file_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_key}"

    new_exam = Exam(
        class_name=class_name,
        subject_name=subject_name,
        date=exam_date,
        status=status,
        marks=marks,
        test_paper=file_url,  
        teacher_name=teacher_name,
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
    
    
from fastapi.responses import JSONResponse

@teacher_router.get("/teacher/view_testpaper/{exam_id}")
def view_testpaper_from_s3(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authorize_user),
):
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=403, 
            detail="Only teachers can view or download files."
        )

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(
            status_code=404, 
            detail="Exam not found in the database."
        )

    if exam.teacher_name != current_user.username:
        raise HTTPException(
            status_code=403, 
            detail="You are not authorized to view this file."
        )

    s3_url = exam.test_paper
    return JSONResponse(content={"url": s3_url})
