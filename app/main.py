

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, schemas, database
from .database import engine, get_db
from .router import auth
from .router.auth import create_access_token, decode_access_token, get_password_hash, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from app.models import Admin  
from app.database import SessionLocal 

app = FastAPI()

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

models.Base.metadata.create_all(bind=engine)

@app.post("/admin/register", response_model=schemas.AdminResponse, tags=["admin"])
def register(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    
    db_admin = db.query(models.Admin).filter(models.Admin.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(admin.password)
    new_admin = models.Admin(username=admin.username, email=admin.email, hashed_password=hashed_password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

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

    # Check user role and existence
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
    # Decodes token to confirm admin role
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
    
    return {
        "id": admin.id,
        "username": admin.username,
        "email": admin.email,
        "access_token": "", 
        "token_type": "bearer"
    }


@app.post("/add_student", response_model=schemas.StudentResponse , tags=["admin"])
def add_student(student: schemas.StudentCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    db_student = db.query(models.Student).filter(models.Student.username == student.username).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Student already registered")
    
    hashed_password = get_password_hash(student.password)
    new_student = models.Student(username=student.username, email=student.email, hashed_password=hashed_password , role="student")
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student

@app.get("/student/{student_id}", response_model=schemas.StudentResponse , tags=["student"])
async def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    return {
        "id": student.id,
        "username": student.username,
        "email": student.email
    }

@app.post("/add_teacher",response_model=schemas.TeacherResponse , tags=["admin"])
def add_teacher(teacher: schemas.TeacherCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    db_teacher = db.query(models.Teacher).filter(models.Teacher.username == teacher.username).first()
    if db_teacher:
        raise HTTPException(status_code=400, detail="Teacher already registered")

    hashed_password = get_password_hash(teacher.password)
    new_teacher = models.Teacher(username=teacher.username, email=teacher.email, hashed_password=hashed_password , role="teacher")
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    return new_teacher

@app.get("/teacher/{teacher_id}", response_model=schemas.TeacherResponse, tags=["teacher"])
async def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    return {
        "id": teacher.id,
        "username": teacher.username,
        "email": teacher.email
    }

# @app.post("/teacher login", response_model=schemas.TeacherLoginResponse, tags=["teacher"])
# async def teacher_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     teacher = db.query(models.Teacher).filter(models.Teacher.username == form_data.username).first()

#     if not teacher or not verify_password(form_data.password, teacher.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     access_token = create_access_token(data={"sub": teacher.username})
#     return {
#         "id": teacher.id,
#         "username": teacher.username,
#         "email": teacher.email,
#         "access_token": access_token,
#         "token_type": "bearer"
#     }

# @app.post("/student login", response_model=schemas.StudentLoginResponse , tags=["student"])
# async def student_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     student = db.query(models.Student).filter(models.Student.username == form_data.username).first()

#     if not student or not verify_password(form_data.password, student.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     access_token = create_access_token(data={"sub": student.username})
#     return {
#         "id": student.id,
#         "username": student.username,
#         "email": student.email,
#         "access_token": access_token,
#         "token_type": "bearer"
#     }

@app.post("/add_class", response_model=schemas.ClassResponse, tags=["admin"])
def add_class(class_data: schemas.ClassCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    new_class = models.Class(name=class_data.name)
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    return new_class


@app.post("/add_subject", response_model=schemas.SubjectResponse, tags=["admin"])
def add_subject(subject_data: schemas.SubjectCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Check if class exists
    class_exists = db.query(models.Class).filter(models.Class.id == subject_data.class_id).first()
    if not class_exists:
        raise HTTPException(status_code=400, detail="Class not found")

    new_subject = models.Subject(name=subject_data.name, class_id=subject_data.class_id)
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    return new_subject
