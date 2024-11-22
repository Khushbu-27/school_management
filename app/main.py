from logging import config
import os
import random
import time
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, Request, requests, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from authlib.integrations.starlette_client import OAuth
from jose import JWTError
import jwt
from sqlalchemy.orm import Session
from uvicorn import Config
from . import  models, schemas
from  . import email_utils  
from .database import engine, get_db
from router.auth import  get_password_hash, verify_password
from datetime import date, datetime, timedelta
from fastapi import HTTPException, status
from email_validator import validate_email, EmailNotValidError
import smtplib
import requests
# ACCESS_TOKEN_EXPIRE_MINUTES,create_access_token, decode_access_token,
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

models.Base.metadata.create_all(bind=engine)


# REQUIREMENT: Registration for Admin only
@app.post("/admin/register", response_model=schemas.AdminResponse, tags=["admin"])
def admin_register(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    """
    Register an admin after validating email and ensuring it is valid.
    """
    if admin.password != admin.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm password do not match"
        )
    
    if db.query(models.User).filter(models.User.username == admin.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.query(models.User).filter(models.User.email == admin.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(admin.password)
    new_admin = models.User(
        username=admin.username,
        email=admin.email,
        hashed_password=hashed_password,
        role="admin"
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return {
        "message": "Your email has been verify. You can login with your username",
        "id": new_admin.id,
        "username": new_admin.username,
        "email": new_admin.email
    }


# Login with Google
@app.get(
    "/auth/login",
    tags=["login"],
    summary="Login with Google",
    description="""
    Redirects the user to the Google Login page.

    **Select the link below to login with Google:**

    [Login with Google](http://localhost:8000/auth/login)
    """,
)
def google_login():
   
    google_oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={os.getenv('GOOGLE_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}"
        "&scope=email%20profile"
    )
    return RedirectResponse(url=google_oauth_url)

print(os.getenv("GOOGLE_REDIRECT_URI"))

@app.get("/auth/login/callback", tags=["login"], summary="Google Login Callback")
def google_callback(code: str, db: Session = Depends(get_db)):
   
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code",
    }
    token_response = requests.post(token_url, data=token_data)
    token_response_data = token_response.json()

    if "error" in token_response_data:
        raise HTTPException(status_code=400, detail=token_response_data["error"])

    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    user_info_headers = {"Authorization": f"Bearer {token_response_data['access_token']}"}
    user_info_response = requests.get(user_info_url, headers=user_info_headers)
    user_info = user_info_response.json()

    user = db.query(models.User).filter(models.User.email == user_info["email"]).first()
    if not user:
        user = models.User(
            username=user_info["email"].split("@")[0],
            email=user_info["email"],
            role="student",
        )
        db.add(user)
        db.commit()

    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "Bearer",
        "user_info": user_info,
    }

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login/callback")

JWT_SECRET = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or has expired")

def token_response(token: str):
    return {
        "access_token": token
    }

def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}
    
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if not credentials or credentials.scheme != "Bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
        
        if not self.verify_jwt(credentials.credentials):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")
        return credentials.credentials

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            decode_access_token(jwtoken)
            return True
        except HTTPException:
            return False


def get_current_user(token: str = Depends(JWTBearer())):
  
    try:
        payload = decode_access_token(token)
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_email
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
@app.get("/protected-endpoint", tags=["login"])
def protected_endpoint(current_user: str = Depends(get_current_user)):
  
    return {"message": "Access granted", "user": current_user}


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

def authorize_admin(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin authorization required")
    return payload

def authorize_user(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    username = payload.get("sub")
    role = payload.get("role")

    if role not in ["admin", "teacher", "student"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


otp_store = {}
otp_expiry_time = 300 

#forgot password
@app.post("/forgot-password/" , tags=["login"])
def forgot_password(email: str , db: Session = Depends(get_db)):
    """Generate OTP and send it to the email."""
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user email")

    otp = str(random.randint(100000, 999999))  
    otp_store[email] = {"otp": otp, "timestamp": time.time()}
    
    email_utils.send_otp_email(email, otp)  
    return {"message": "OTP sent to email"}

#reset password
@app.post("/reset-password/", tags=["login"])
def reset_password(user_id: int, email: str, otp: str, new_password: str, db: Session = Depends(get_db)):
    """Verify user ID, OTP and reset password."""
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user ID or email")

    if email not in otp_store:
        raise HTTPException(status_code=400, detail="OTP not requested")
    
    otp_data = otp_store[email]

    if time.time() - otp_data["timestamp"] > otp_expiry_time:
        del otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if otp_data["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.commit()

    del otp_store[email]
    
    return {"message": "Password reset successful"}


# REQUIREMENT: View Admin own Info
@app.get("/admin/{admin_id}", response_model=schemas.AdminResponse, tags=["admin"])
def view_admin_info(admin_id: int, token: dict = Depends(authorize_admin), db: Session = Depends(get_db), current_user = Depends(authorize_admin)):

    # if current_user.role != "admin":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin authorization required"
    #     ) 
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
@app.get("/student/{student_id}", response_model=schemas.StudentResponse, tags=["student"])
def view_own_student_info(current_user= Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student authorization required")
    
    student = db.query(models.User).filter(models.User.username == current_user.username).first()
    return student


# REQUIREMENT: Student - Update Own Info
@app.put("/student/{student-id}/update", response_model=schemas.StudentResponse, tags=["student"])
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
@app.get("/teacher/{teacher_id}", response_model=schemas.TeacherResponse, tags=["teacher"])
def view_own_teacher_info(db: Session = Depends(get_db) , current_user=Depends(authorize_user)):

    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher authorization required")
    
    teacher = db.query(models.User).filter(models.User.username == current_user.username).first()
    return teacher


# REQUIREMENT: view teacher own salary
@app.get("/teacher/view_salary/{teacher_id}" , tags=["teacher"],response_model=schemas.TeacherSalary)
def view_my_salary( db: Session = Depends(get_db), current_user = Depends(authorize_user)):
   
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Not authorized to view this salary")
    
    salary = db.query(models.User).filter(models.User.salary == current_user.salary).first()

    if current_user.salary is None:
        raise HTTPException(status_code=404, detail="Salary not set for this teacher")

    return {"teacher_id": current_user.id, "salary": salary}
 

# REQUIREMENT: Teacher - Update Own Info
@app.put("/teacher/{teacher_id}/update", response_model=schemas.TeacherResponse, tags=["teacher"])
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
def add_exam_schedule(
    date: str = Query(...),
    status: str = Query(...),
    marks: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(authorize_user)
):
   
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add exams.")
    
    class_name = current_user.class_name
    subject_name = current_user.subject_name
    
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
    
    existing_exam = db.query(models.Exam).filter(
            models.Exam.subject_name == subject_name,
            models.Exam.date == exam_date
        ).first()
    
    if existing_exam:
            raise HTTPException(status_code=400, detail=f"Exam for this subject have already been added.")

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
    
    if current_user.class_name != class_name or current_user.subject_name != subject_name:
        raise HTTPException(status_code=403, detail="You cannot update an exam for this class or subject.")
    
    try:
        exam_date = datetime.strptime(date, "%d-%m-%Y").date()  
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY.")
    
    if exam_date < datetime.today().date():
        raise HTTPException(status_code=400, detail="Exam date cannot be in the past.")

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


#REQUIREMENT: teacher and student view exam schedule
@app.get("/exam/{exam_id}", status_code=status.HTTP_200_OK, tags=["student", "teacher"])
def view_exam_schedule(
    exam_id: int,
    current_user=Depends(authorize_user),  
    db: Session = Depends(get_db)
):
    
    if current_user.role not in ["student", "teacher"]:
        raise HTTPException(status_code=403, detail="Only students and teachers can view exam schedules.")

    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if current_user.role == "teacher":
        if exam.class_name != current_user.class_name or exam.subject_name != current_user.subject_name:
            raise HTTPException(status_code=403, detail="You are not authorized to view this exam schedule.")
    
    elif current_user.role == "student":
        if exam.class_name != current_user.class_name:
            raise HTTPException(status_code=403, detail="You are not authorized to view this exam schedule.")

    return exam


# REQUIREMENT: teacher can delete exam
@app.delete("/teacher/delete_exam/{exam_id}", tags=["teacher"])
def delete_exam(exam_id: int, current_user=Depends(authorize_user), db: Session = Depends(get_db)):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete exams")
    
    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    if current_user.role == "teacher":
        if exam.class_name != current_user.class_name or exam.subject_name != current_user.subject_name:
            raise HTTPException(status_code=403, detail="You are not authorized to delete this exam schedule.")

    db.delete(exam)
    db.commit()
    
    return {"message": "Exam deleted successfully"}


# REQUIREMENT: generate marks by teacher
@app.post("/generate_marks/{exam_id}", tags=["teacher"])
def generate_marks(
    exam_id: int, 
    marks_data: List[schemas.GenerateMarks],
    db: Session = Depends(get_db),
    current_user = Depends(authorize_user)
):

    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can generate marks")

    exam = db.query(models.Exam).filter(
        models.Exam.id == exam_id
    ).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    if exam.class_name != current_user.class_name :
        raise HTTPException(status_code=403, detail="You cannot generate marks for this class or subject.")
    response_data = []  

    for mark in marks_data:
        
        student = db.query(models.User).filter(
            models.User.username == mark.student_name,
            models.User.class_name == exam.class_name,
            # models.User.subject_name == exam.subject_name
        ).first()

        if not student:
            raise HTTPException(status_code=404, detail=f"Student '{mark.student_name}' not found in class {exam.class_name}.")

        existing_marks = db.query(models.StudentMarks).filter(
            models.StudentMarks.student_name == mark.student_name,
            models.StudentMarks.exam_id == exam.id
        ).first()

        if existing_marks:
            raise HTTPException(status_code=400, detail=f"Marks for student '{mark.student_name}' have already been added for this exam.")
        
        if exam.date >= datetime.today().date():
            raise HTTPException(status_code=400, detail="Exam is not completed yet.You can not add marks")

        if mark.student_marks > exam.marks:
            raise HTTPException(status_code=400, detail=f"Marks cannot be greater than the maximum marks ({exam.marks}) for this exam.")

        new_marks = models.StudentMarks(
            student_name=mark.student_name, 
            class_name=exam.class_name,
            subject_name=exam.subject_name, 
            exam_id=exam.id,        
            student_marks=mark.student_marks        
        )
        db.add(new_marks)

        response_data.append(schemas.GeneratedMarkResponse(
            exam_id=exam.id,
            student_name=mark.student_name,
            class_name=exam.class_name,
            subject_name=exam.subject_name,
            marks=mark.student_marks
        ))

    db.commit()

    return schemas.MarksGenerationResponse(msg="Marks generated successfully", data=response_data)


# REQUIREMENT: student - view student own marks
@app.get("/students/{student_id}/marks", response_model=List[schemas.StudentMarks], tags=["student"])
def get_student_marks(student_id: int, db: Session = Depends(get_db), current_user=Depends(authorize_user)):

    if current_user.role != "student" or current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    eligible_exams = db.query(models.Exam).filter(models.Exam.class_name == current_user.class_name).all()
    if not eligible_exams:
        raise HTTPException(status_code=403, detail="You are not authorized to view this exam marks.")
    
    marks_records = (
        db.query(
            models.StudentMarks.id,
            models.StudentMarks.student_name,
            models.StudentMarks.class_name,
            models.StudentMarks.subject_name,
            models.StudentMarks.student_marks.label("student_marks"),
            models.Exam.date
        )
        .join(models.Exam, models.StudentMarks.exam_id == models.Exam.id)
        .filter(models.StudentMarks.student_name == current_user.username)
        .all()
    )

    if not marks_records:
        raise HTTPException(status_code=404, detail="Marks not found for the student")

    return [
        schemas.StudentMarks(
            id=record.id,
            student_name=record.student_name,
            class_name=record.class_name,
            subject_name=record.subject_name,
            student_marks=record.student_marks,
            exam_date=record.date  
        )
        for record in marks_records
    ]


# REQUIREMENT: admin can delete users
@app.delete("/admin/delete_user/{user_id}" , tags=["admin"])
async def delete_user(user_id: int, current_user=Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, details= 'Only admin can delete users')
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
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