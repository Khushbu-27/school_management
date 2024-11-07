from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, get_db
from app.router.auth import create_access_token, decode_access_token, get_password_hash, verify_password 
from datetime import datetime

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

models.Base.metadata.create_all(bind=engine)

# Registration Endpoint for Admin
@app.post("/admin/register", response_model=schemas.AdminResponse, tags=["admin"])
def admin_register(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    db_admin = db.query(models.User).filter(models.User.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(admin.password)
    new_admin = models.User(username=admin.username, email=admin.email, hashed_password=hashed_password, role="admin")
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
<<<<<<< HEAD
=======

    access_token = create_access_token(data={"sub": new_admin.username})
    return schemas.AdminResponse(
        id=new_admin.id,     
        username=new_admin.username,  
        email=new_admin.email,  
        access_token=access_token,
        token_type="bearer"
    )


@app.post('/login', tags=["login"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.Admin).filter(models.Admin.username == form_data.username).first()
    role = form_data.scopes[0]  # Assuming `role` is passed in `scopes` for simplicity

  
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or role",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Allow token generation only if the role is admin
    if role == "admin":
        access_token = create_access_token(data={"sub": user.username, "role": role})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can generate tokens."
        )

def authorize_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
  
    payload = auth.decode_access_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin authorization required"
        )
    return payload

def get_current_admin_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    user = db.query(models.User).filter(models.User.username == payload.get("sub")).first()
    
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Operation allowed only for admin")
    return user

@app.get("/admin/{admin_id}", response_model=schemas.AdminResponse, tags=["admin"])
def get_admin(admin_id: int, db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
>>>>>>> 969ee0e1dc26f5c25855a4b3fa52767dcc94ad34
    
    return {
        "id": new_admin.id,
        "username": new_admin.username,
        "email": new_admin.email
    }

#  Login users
@app.post('/login', tags=["login"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.role == "admin":
        access_token = create_access_token(data={"sub": user.username, "role": "admin"})
        return {"access_token": access_token, "token_type": "Bearer", "role": "admin", "message": "Admin login successful"}
    
    elif user.role in ["teacher", "student"]:
        user.attendance += 1  
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


# Retrieve Admin Info
@app.get("/admin/{admin_id}", response_model=schemas.AdminResponse, tags=["admin"])
def view_admin_info(token: str = Depends(authorize_admin),  db: Session = Depends(get_db)):
    if token.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin authorization required")
    
    student = db.query(models.User).filter(models.User.username == token["sub"]).first()
    return student

# Authorization for Any User Role
# def authorize_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     payload = decode_access_token(token)
#     role = payload.get("role")
#     if role not in ["admin", "teacher", "student"]:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role")
#     return payload

def authorize_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    username = payload.get("sub")
    role = payload.get("role")
    
    if role not in ["admin", "teacher", "student"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role")

    # Fetch the user from the database
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user

# Add Student (Admin Only)
@app.post("/add_student", response_model=schemas.StudentResponse, tags=["add by admin"])
def add_student(student: schemas.StudentCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):
    db_student = db.query(models.User).filter(models.User.username == student.username).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Student already registered")
    
    hashed_password = get_password_hash(student.password)
    new_student = models.User(username=student.username, email=student.email, hashed_password=hashed_password, role="student")
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    return new_student

# Add Teacher (Admin Only)
@app.post("/add_teacher", response_model=schemas.TeacherResponse, tags=["add by admin"])
def add_teacher(teacher: schemas.TeacherCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):
    db_teacher = db.query(models.User).filter(models.User.username == teacher.username).first()
    if db_teacher:
        raise HTTPException(status_code=400, detail="Teacher already registered")
    
    hashed_password = get_password_hash(teacher.password)
    new_teacher = models.User(username=teacher.username, email=teacher.email, hashed_password=hashed_password, role="teacher")
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    
    return new_teacher

@app.post("/add_salary/{teacher_id}" , tags=["add by admin"])
def add_teacher_salary(teacher_id: int, salary: schemas.TeacherSalary, db: Session = Depends(get_db), current_user: models.User = Depends(authorize_admin) ):
    teacher = db.query(models.User).filter(models.User.id == teacher_id, models.User.role == "teacher").first()

    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")

    teacher.salary = salary.salary
    db.commit()
    db.refresh(teacher)

    return {"message": "Salary updated successfully", "salary": teacher.salary}


@app.get("/view_teacher_salary/{teacher_id}", tags=["admin"])
def view_teacher_salary(
    teacher_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(authorize_admin)):
  
    teacher = db.query(models.User).filter(models.User.id == teacher_id, models.User.role == "teacher").first()

    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if teacher.salary is None:
        raise HTTPException(status_code=404, detail="Salary not set for this teacher")

    return {"teacher_id": teacher.id, "salary": teacher.salary}


@app.get("/admin/view_teacher/{teacher_id}", response_model=schemas.TeacherResponse, tags=["admin"])
def admin_view_teacher_info(teacher_id: int, token: str = Depends(authorize_admin), db: Session = Depends(get_db)):
    teacher = db.query(models.User).filter(models.User.id == teacher_id, models.User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return teacher

# Admin - View Student Info
@app.get("/admin/view_student/{student_id}", response_model=schemas.StudentResponse, tags=["admin"])
def admin_view_student_info(student_id: int, token: str = Depends(authorize_admin), db: Session = Depends(get_db)):
    student = db.query(models.User).filter(models.User.id == student_id, models.User.role == "student").first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

# # Retrieve Teacher Info
# @app.get("/teacher/{teacher_id}", response_model=schemas.TeacherResponse, tags=["get"])
# def view_teacher_info(token: str = Depends(authorize_user), db: Session = Depends(get_db)):
#     if token.get("role") != "teacher":
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
#     teacher = db.query(models.User).filter(models.User.username == token["sub"]).first()
#     return teacher

# # Retrieve Student Info
# @app.get("/student/{student_id}", response_model=schemas.StudentResponse, tags=["get"])
# def view_student_info(token: str = Depends(authorize_user), db: Session = Depends(get_db)):
#     if token.get("role") != "student":
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student authorization required")
    
#     student = db.query(models.User).filter(models.User.username == token["sub"]).first()
#     return student

# Add Subject (Admin Only)
@app.post("/class-subject/", response_model=schemas.ClassSubjectCreate , tags=["add by admin"])
async def add_class_subject(request: schemas.ClassSubjectCreate, db: Session = Depends(get_db)):
    # Check if user exists and is a student
    student = db.query(models.User).filter(models.User.id == request.student_id, models.User.role == "student").first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    # Create new class-subject entry
    class_subject = models.ClassSubject(
        class_name=request.class_name,
        subject_name=request.subject_name,
        student_id=request.student_id
    )
    
    db.add(class_subject)
    db.commit()

    return {"message": "Class and subject added successfully."}

# Teacher - View Own Info
@app.get("/teacher/me", response_model=schemas.TeacherResponse, tags=["teacher"])
def view_own_teacher_info(token: str = Depends(authorize_user), db: Session = Depends(get_db)):
    if token.get("role") != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    teacher = db.query(models.User).filter(models.User.username == token["sub"]).first()
    return teacher

# Teacher - Update Own Info
@app.put("/teacher/me/update", response_model=schemas.TeacherResponse, tags=["teacher"])
def update_own_info(update_data: schemas.UserUpdate, token: str = Depends(authorize_user), db: Session = Depends(get_db)):
    if token.get("role") != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    teacher = db.query(models.User).filter(models.User.username == token["sub"]).first()
    if update_data.username:
        teacher.username = update_data.username
    if update_data.password:
        teacher.hashed_password = get_password_hash(update_data.password)
    db.commit()
    db.refresh(teacher)
    return teacher

# Teacher - View Student Info (View Only)
@app.get("/teacher/view_student/{student_id}", response_model=schemas.StudentResponse, tags=["teacher"])
def teacher_view_student_info(student_id: int, token: str = Depends(authorize_user), db: Session = Depends(get_db)):
    if token.get("role") != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    student = db.query(models.User).filter(models.User.id == student_id, models.User.role == "student").first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

# Student - View Own Info
@app.get("/student/me", response_model=schemas.StudentResponse, tags=["student"])
def view_own_student_info(token: str = Depends(authorize_user), db: Session = Depends(get_db)):
    if token.get("role") != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student authorization required")
    
    student = db.query(models.User).filter(models.User.username == token["sub"]).first()
    return student


# Student - Update Own Info
@app.put("/student/me/update", response_model=schemas.StudentResponse, tags=["student"])
def update_own_info(update_data: schemas.UserUpdate, token: str = Depends(authorize_user), db: Session = Depends(get_db)):
    if token.get("role") != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student authorization required")
    
    student = db.query(models.User).filter(models.User.username == token["sub"]).first()
    if update_data.username:
        student.username = update_data.username
    if update_data.password:
        student.hashed_password = get_password_hash(update_data.password)
    db.commit()
    db.refresh(student)
    return student

#add exam by teacher only
@app.post("/exam", status_code=status.HTTP_201_CREATED , tags=["teacher"])
def add_exam_schedule(class_name: str, subject: str, date: str, status: str, marks: int, 
                            current_user = Depends(authorize_user), db: Session = Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add exams.")
    
    try:
        exam_date = datetime.strptime(date, "%d-%m-%Y").date()  # Converts string to date object
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY.")
    
    # Validate status input
    status = status.lower()  # Convert to lowercase
    if status not in ['scheduled', 'completed']:
        raise HTTPException(status_code=400, detail="Invalid status. Choose either 'scheduled' or 'completed'.")

    
    new_exam = models.Exam(class_name=class_name, subject=subject, date=exam_date, status=status, marks=marks)
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)

    return new_exam

#update exam by teacher
@app.put("/exam/{exam_id}", status_code=status.HTTP_200_OK, tags=["teacher"])
def update_exam_schedule(exam_id: int, class_name: str = None, subject: str = None, date: str = None,status: str = None, marks: int = None, current_user = Depends(authorize_user), db: Session = Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update exams.")

    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add exams.")
    
    try:
        exam_date = datetime.strptime(date, "%d-%m-%Y").date()  # Converts string to date object
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY.")
    
    # Validate status input
    status = status.lower()  # Convert to lowercase
    if status not in ['scheduled', 'completed']:
        raise HTTPException(status_code=400, detail="Invalid status. Choose either 'scheduled' or 'completed'.")


    exam.class_name = class_name
    exam.subject = subject
    exam.date = exam_date
    exam.status = status
    exam.marks = marks

    db.commit()
    return {"message": "Exam updated successfully", "exam": exam}

#view exam by student & teacher 
@app.get("/exam/{class_name}", status_code=status.HTTP_200_OK, tags=["student", "teacher"])
async def view_exam_schedule(class_name: str, current_user = Depends(authorize_user), db: Session = Depends(get_db)):
    if current_user.role not in ["student", "teacher"]:
        raise HTTPException(status_code=403, detail="Only students and teachers can view exam schedules.")
    
    exams = db.query(models.Exam).filter(models.Exam.class_name == class_name).all()
    if not exams:
        raise HTTPException(status_code=404, detail="No exams found for this class.")
    
    return exams

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

    teacher.salary = salary.salary 
    db.commit()
    db.refresh(teacher)

    return {"message": "Teacher salary updated successfully", "teacher_id": teacher.id, "salary": teacher.salary}


@app.get("teacher/view_salary/{teacher_id}" , tags=["teacher"])
def view_my_salary(teacher_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(authorize_user)):
   
    if current_user.role != "teacher" or current_user.id != teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this salary")

    if current_user.salary is None:
        raise HTTPException(status_code=404, detail="Salary not set for this teacher")

    return {"teacher_id": current_user.id, "salary": current_user.salary}

#admin can delete users
@app.delete("/admin/delete_user/{user_id}" , tags=["admin"])
async def delete_user(user_id: int, current_user=Depends(authorize_admin)):
    user = await models.User.get(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return {"message": "User deleted successfully"}


@app.delete("/teacher/delete_exam/{exam_id}", tags=["teacher"])
async def delete_exam(exam_id: int, current_user=Depends(authorize_user)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete exams")
    
    exam = await models.Exam.get(exam_id=exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    await exam.delete()
    return {"message": "Exam deleted successfully"}

@app.put("/class-subject/{class_subject_id}", response_model=schemas.ClassSubjectUpdate , tags=["admin"])
def update_class_subject(class_subject_id: int, class_subject: schemas.ClassSubjectUpdate, db: Session = Depends(get_db), current_user: str = Depends(authorize_admin)):
    db_class_subject = db.query(models.ClassSubject).filter(models.ClassSubject.id == class_subject_id).first()
    if db_class_subject is None:
        raise HTTPException(status_code=404, detail="Class and Subject not found")
    
    db_class_subject.class_name = class_subject.class_name
    db_class_subject.subject_name = class_subject.subject_name
    db.commit()
    db.refresh(db_class_subject)
    return db_class_subject

@app.delete("/class-subject/{class_subject_id}", status_code=status.HTTP_204_NO_CONTENT , tags=["admin"])
def delete_class_subject(class_subject_id: int, db: Session = Depends(get_db), current_user: str = Depends(authorize_admin)):
    db_class_subject = db.query(models.ClassSubject).filter(models.ClassSubject.id == class_subject_id).first()
    if db_class_subject is None:
        raise HTTPException(status_code=404, detail="Class and Subject not found")
    
    db.delete(db_class_subject)
    db.commit()
    return {"detail": "Class and Subject deleted successfully"}
    
@app.post("/reset-password", tags=["login"])
def reset_password(request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
   
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this ID not found."
        )

    schemas.validate_password(request.new_password)
    hashed_password = get_password_hash(request.new_password)

    user.hashed_password = hashed_password
    db.commit()

    return {"message": "Password reset successful. You can now log in with your new password."}