from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, get_db
from router.auth import create_access_token, decode_access_token, get_password_hash, verify_password 
from datetime import date, datetime
from fastapi import HTTPException, status

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

models.Base.metadata.create_all(bind=engine)


# REQUIREMENT: Registration for Admin only
@app.post("/admin/register", response_model=schemas.AdminResponse, tags=["admin"])
def admin_register(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
   
    if admin.password != admin.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm password do not match"
        )
    
    db_admin = db.query(models.User).filter(models.User.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(admin.password)  
    new_admin = models.User(username=admin.username, email=admin.email, hashed_password=hashed_password, role="admin")
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return {
        "id": new_admin.id,
        "username": new_admin.username,
        "email": new_admin.email
    }


# REQUIREMENT: Login users
@app.post('/login', tags=["login"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    today = date.today()

    if user.role == "admin":
        access_token = create_access_token(data={"sub": user.username, "role": "admin"})
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "role": "admin",
            "message": "Admin login successful"
        }

    elif user.role in ["teacher", "student"]:
        
        if user.last_login_date != today:
            user.attendance += 1
            user.last_login_date = today    
        db.commit() 

        access_token = create_access_token(data={"sub": user.username, "role": user.role})
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "role": user.role,
            "attendance": user.attendance,  
            "message": f"{user.role.capitalize()} login successful"
        }

def authorize_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    payload = decode_access_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin authorization required")
    return payload

def authorize_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    payload = decode_access_token(token)
    username = payload.get("sub")
    role = payload.get("role")
    
    if role not in ["admin", "teacher", "student"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user


#REQUIREMENT: reset password
# @app.post("/reset-password", tags=["login"])
# def reset_password(request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
   
#     user = db.query(models.User).filter(models.User.id == request.user_id).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User with this ID not found."
#         )

#     schemas.validate_password(request.new_password)
#     hashed_password = get_password_hash(request.new_password)

#     user.hashed_password = hashed_password
#     db.commit()

#     return {"message": "Password reset successful. You can now log in with your new password."}


# REQUIREMENT: View Admin own Info
@app.get("/admin/{admin_id}", response_model=schemas.AdminResponse, tags=["admin"])
def view_admin_info(admin_id: int, token: dict = Depends(authorize_admin), db: Session = Depends(get_db), current_user = Depends(authorize_admin)):

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin authorization required"
        ) 
    # if token.get("id") != admin_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Access denied for this admin ID"
    #     )
    admin = db.query(models.User).filter(models.User.id == admin_id, models.User.role == "admin").first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return admin


# REQUIREMENT: Add Student (Admin Only)
@app.post("/add_student", response_model=schemas.StudentResponse, tags=["add by admin"])
def add_student(student: schemas.StudentCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):

    db_student = db.query(models.User).filter(models.User.username == student.username).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Student already added")
    
    hashed_password = get_password_hash(student.password)
    new_student = models.User(username=student.username, email=student.email, hashed_password=hashed_password, role="student" , class_name=student.class_name)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    return new_student


# REQUIREMENT: Admin - View Student Info
@app.get("/admin/view_student/{student_id}", response_model=schemas.StudentResponse, tags=["admin"])
def admin_view_student_info(student_id: int, token: str = Depends(authorize_admin), db: Session = Depends(get_db)):

    student = db.query(models.User).filter(models.User.id == student_id, models.User.role == "student").first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


# REQUIREMENT: Student - View Own Info
@app.get("/student/me", response_model=schemas.StudentResponse, tags=["student"])
def view_own_student_info(current_user= Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student authorization required")
    
    student = db.query(models.User).filter(models.User.username == current_user.username).first()
    return student


# REQUIREMENT: Student - Update Own Info
@app.put("/student/me/update", response_model=schemas.StudentResponse, tags=["student"])
def update_own_info(update_data: schemas.UserUpdate, current_user = Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student authorization required")
    
    student = db.query(models.User).filter(models.User.username == current_user.username).first()
    # if update_data.username:
    #     student.username = update_data.username
    if update_data.password:
        student.hashed_password = get_password_hash(update_data.password)
    db.commit()
    db.refresh(student)
    return {"message": "student info updated successfully" , "student": student}


# REQUIREMENT: Add Teacher (Admin Only)
@app.post("/add_teacher", response_model=schemas.TeacherResponse, tags=["add by admin"])
def add_teacher(teacher: schemas.TeacherCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):

    db_teacher = db.query(models.User).filter(models.User.username == teacher.username).first()
    if db_teacher:
        raise HTTPException(status_code=400, detail="Teacher already added")
    
    hashed_password = get_password_hash(teacher.password)
    new_teacher = models.User(username=teacher.username, email=teacher.email, hashed_password=hashed_password, role="teacher",class_name=teacher.class_name,subject_name=teacher.subject_name)
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    
    return  new_teacher


# REQUIREMENT:Add teacher salary by admin
@app.post("/add_salary/{teacher_id}" , tags=["add by admin"])
def add_teacher_salary(teacher_id: int, salary: schemas.TeacherSalary, db: Session = Depends(get_db), current_user: models.User = Depends(authorize_admin) ):
    teacher = db.query(models.User).filter(models.User.id == teacher_id, models.User.role == "teacher").first()

    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")

    teacher.salary = salary.salary
    db.commit()
    db.refresh(teacher)

    return {"message": "Salary added successfully", "salary": teacher.salary}


# REQUIREMENT: View Teacher Salary by admin
@app.get("/view_teacher_salary/{teacher_id}", tags=["admin"])
def view_teacher_salary(
    teacher_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(authorize_admin)):
  
    teacher = db.query(models.User).filter(models.User.id == teacher_id, models.User.role == "teacher").first()

    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if teacher.salary is None:
        raise HTTPException(status_code=404, detail="Salary not set for this teacher")

    return {"teacher_id": teacher.id, "salary": teacher.salary}


# REQUIREMENT: update teacher salary by admin
@app.post("/admin/update_salary/{teacher_id}", tags=["admin"])
def update_teacher_salary(
    teacher_id: int,
    salary: schemas.TeacherSalary, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(authorize_admin)
):
    
    teacher = db.query(models.User).filter(models.User.id == teacher_id, models.User.role == "teacher").first()

    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    if teacher.salary is None:
        raise HTTPException(status_code=400, detail="Teacher salary must be set first before updating")

    teacher.salary = salary.salary
    db.commit()
    db.refresh(teacher)

    return {"message": "Teacher salary updated successfully", "teacher_id": teacher.id, "salary": teacher.salary}


# REQUIREMENT: Admin - View Teacher Info
@app.get("/admin/view_teacher/{teacher_id}", response_model=schemas.TeacherResponse, tags=["admin"])
def admin_view_teacher_info(teacher_id: int, token: str = Depends(authorize_admin), db: Session = Depends(get_db)):

    teacher = db.query(models.User).filter(models.User.id == teacher_id, models.User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return teacher


# REQUIREMENT: Teacher - View Own Info
@app.get("/teacher/me", response_model=schemas.TeacherResponse, tags=["teacher"])
def view_own_teacher_info(db: Session = Depends(get_db) , current_user=Depends(authorize_user)):

    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    teacher = db.query(models.User).filter(models.User.username == current_user.username).first()
    return teacher


# REQUIREMENT: view teacher own salary
@app.get("teacher/view_salary/{teacher_id}" , tags=["teacher"])
def view_my_salary(teacher_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(authorize_user)):
   
    if current_user.role != "teacher" or current_user.id != teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this salary")

    if current_user.salary is None:
        raise HTTPException(status_code=404, detail="Salary not set for this teacher")

    return {"teacher_id": current_user.id, "salary": current_user.salary}
 

# REQUIREMENT: Teacher - Update Own Info
@app.put("/teacher/me/update", response_model=schemas.TeacherResponse, tags=["teacher"])
def update_own_info(update_data: schemas.UserUpdate, current_user = Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    teacher = db.query(models.User).filter(models.User.username == current_user.username).first()
    # if update_data.username:
    #     teacher.username = update_data.username
    if update_data.password:
        teacher.hashed_password = get_password_hash(update_data.password)
    db.commit()
    db.refresh(teacher)
    return {"message": "Teacher info updated successfully" , "teacher": teacher}


# REQUIREMENT: Teacher - View Student Info (View Only)
@app.get("/teacher/view_student/{student_id}", response_model=schemas.StudentResponse, tags=["teacher"])
def teacher_view_student_info(student_id: int, current_user = Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    student = db.query(models.User).filter(models.User.id == student_id, models.User.role == "student").first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


# REQUIREMENT: add exam by teacher only
@app.post("/exam", status_code=status.HTTP_201_CREATED, tags=["teacher"])
def add_exam_schedule(date: str = Query(...),  status: str = Query(...),  marks: int = Query(...),  db: Session = Depends(get_db),current_user=Depends(authorize_user), ):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add exams.")
    
    class_name = current_user.class_name
    subject_name = current_user.subject_name
    
    try:
        exam_date = datetime.strptime(date, "%d-%m-%Y").date() 
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY.")

    if exam_date < datetime.today().date():
        raise HTTPException(status_code=400, detail="Exam date cannot be in the past.")
    
    status = status.lower()
    if status not in ['scheduled', 'completed']:
        raise HTTPException(status_code=400, detail="Invalid status. Choose either 'scheduled' or 'completed'.")

    new_exam = models.Exam(
        class_name=class_name,
        subject_name=subject_name,
        date=exam_date,
        status=status, 
        marks=marks 
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)

    return {"message": "Exam added successfully", "exam": new_exam}


# REQUIREMENT: update exam schedule by teacher only
@app.put("/exam/{exam_id}", status_code=status.HTTP_200_OK, tags=["teacher"])
def update_exam_schedule(exam_id: int, class_name: str = None, subject_name: str = None, date: str = Query(...),status: str = None, marks: int = None, current_user = Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update exams.")

    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add exams.")
    
    try:
        exam_date = datetime.strptime(date, "%d-%m-%Y").date()  
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY.")
    
    # if exam_date < datetime.today().date():
    #     raise HTTPException(status_code=400, detail="Exam date cannot be in the past.")

    status = status.lower()  
    if status not in ['scheduled', 'completed']:
        raise HTTPException(status_code=400, detail="Invalid status. Choose either 'scheduled' or 'completed'.")


    exam.class_name = class_name
    exam.subject_name = subject_name
    exam.date = exam_date
    exam.status = status
    exam.marks = marks

    db.commit()
    return {"message": "Exam updated successfully", "exam": exam}


#  REQUIREMENT: view exam by student & teacher 
@app.get("/exam/{class_name}", status_code=status.HTTP_200_OK, tags=["student", "teacher"])
def view_exam_schedule(class_name: str, current_user = Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role not in ["student", "teacher"]:
        raise HTTPException(status_code=403, detail="Only students and teachers can view exam schedules.")
    
    exams = db.query(models.Exam).filter(models.Exam.class_name == class_name).all()
    if not exams:
        raise HTTPException(status_code=404, detail="No exams found for this class_name.")
    
    for exam in exams:
        if exam.date <  datetime.today().date() and exam.status != "Completed":
            exam.status = "Completed"
            db.commit()
    
    return exams


# REQUIREMENT: teacher can delete exam
@app.delete("/teacher/delete_exam/{exam_id}", tags=["teacher"])
async def delete_exam(exam_id: int, current_user=Depends(authorize_user), db: Session = Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete exams")
    
    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    db.delete(exam)
    db.commit()
    
    return {"message": "Exam deleted successfully"}


# REQUIREMENT: generate marks by teacher
@app.post("/generate_marks/{exam_id}", tags=["teacher"])
def generate_marks(exam_id: int, marks_data: List[schemas.GenerateMarks],db: Session = Depends(get_db),current_user = Depends(authorize_user)):
    
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can generate marks")

    exam = (db.query(models.Exam).filter(models.Exam.id == exam_id,models.Exam.class_name == current_user.class_name,models.Exam.subject_name == current_user.subject_name).first())

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found or does not belong to the teacher")
    
    for mark in marks_data:
        
        student = db.query(models.User).filter(
            models.User.username == mark.student_name,
            models.User.class_name == exam.class_name, 
            models.User.subject_name == exam.subject_name 
        ).first()

        if student:
           
            new_marks = models.StudentMarks(

                student_name=mark.student_name, 
                class_name = exam.class_name,
                subject_name= exam.subject_name, 
                exam_id=exam.id,        
                marks=mark.student_marks        
            )
            db.add(new_marks)
    db.commit()
    return {"msg": "Marks generated successfully"}


# REQUIREMENT: student - view student own marks
@app.get("/students/{student_id}/marks", response_model=List[schemas.StudentMarks], tags=["student"])
def get_student_marks(student_id: int,db: Session = Depends(get_db),current_user=Depends(authorize_user)):
    
    if current_user.role != "student" or current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    marks_records = (
        db.query(models.StudentMarks)
        .filter(models.StudentMarks.student_name == current_user.username)
        .all()
    )

    if not marks_records:
        raise HTTPException(status_code=404, detail="Marks not found for the student")

    return marks_records


# REQUIREMENT: admin can delete users
@app.delete("/admin/delete_user/{user_id}" , tags=["admin"])
async def delete_user(user_id: int, current_user=Depends(authorize_admin)):
    user = await models.User.get(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return {"message": "User deleted successfully"}


# @router.post("/add_exam")
# async def add_exam(data: ExamCreateSchema, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
#     if current_user.role != "teacher":
#         raise HTTPException(status_code=403, detail="Only teachers can add exams")

#     # Auto-fill class_name and subject fields based on teacher's details
#     new_exam = Exam(
#         class_name=current_user.class_name,
#         subject=current_user.subject,
#         date=data.date,
#         status="Scheduled"
#     )
#     db.add(new_exam)
#     db.commit()
#     return {"msg": "Exam scheduled successfully"}


# REQUIREMENT: update exam by teacher

# @app.post("/generate_marks/{exam_id}" , tags=["teacher"])
# async def generate_marks(exam_id: int, marks_data: List[schemas.StudentMarks],db: Session = Depends(get_db),current_user = Depends(authorize_user)):

#     if current_user.role != "teacher":
#         raise HTTPException(status_code=403, detail="Only teachers can generate marks")

#     exam = (
#         db.query(models.Exam)
#         .filter(
#             models.Exam.id == exam_id,
#             models.Exam.class_name == getattr(current_user, "class_name", None),  
#             models.Exam.subject_name == getattr(current_user, "subject_name", None)  
#         )
#         .first()
#     )

#     # if not exam or exam.status != models.ExamStatus.completed.value:
#     #     raise HTTPException(status_code=400, detail="Cannot add marks. Exam is not completed or invalid.")

#     for mark in marks_data:
#         student = db.query(models.User).filter(
#             models.User.id == mark.student_id,
#             models.User.class_name == exam.class_name
#         ).first()
        
#         if student:
#             new_marks = models.StudentMarks(
#                 student_id=models.User.id,
#                 # subject_name= models.Exam.subject_name,
#                 marks=mark.marks
#             )
#             db.add(new_marks)
#             db.commit()
    
#     return {"msg": "Marks generated successfully"}