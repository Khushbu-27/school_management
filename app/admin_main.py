# from fastapi import FastAPI, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from . import models, schemas
# from fastapi.security import OAuth2PasswordBearer
# from .database import get_db
# from app.app.auth import create_access_token, decode_access_token, get_password_hash, verify_password 

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8001/admin_login")

# admin_app = FastAPI()

# @admin_app.post("/admin/register", response_model=schemas.AdminResponse, tags=["admin"])
# def register(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
#     db_admin = db.query(models.User).filter(models.User.username == admin.username).first()
#     if db_admin:
#         raise HTTPException(status_code=400, detail="Username already registered")

#     hashed_password = get_password_hash(admin.password)
#     new_admin = models.User(username=admin.username, email=admin.email, hashed_password=hashed_password, role="admin")
#     db.add(new_admin)
#     db.commit()
#     db.refresh(new_admin)
    
#     return {
#         "id": new_admin.id,
#         "username": new_admin.username,
#         "email": new_admin.email
#     }

# @admin_app.post('/admin_login', tags=["admin login"], response_model=schemas.TokenResponse)
# def admin_login(credentials: schemas.AdminLogin, db: Session = Depends(get_db)):
#     admin = db.query(models.User).filter(models.User.username == credentials.username, models.User.role == "admin").first()
#     if not admin or not verify_password(credentials.password, admin.hashed_password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

#     access_token = create_access_token(data={"sub": admin.username, "role": "admin"})
#     return {"access_token": access_token, "token_type": "Bearer", "role": "admin"}

# @admin_app.get("/admin/{admin_id}", response_model=schemas.AdminResponse, tags=["get"])
# def get_admin(admin_id: int, db: Session = Depends(get_db)):
#     admin = db.query(models.User).filter(models.User.id == admin_id).first()
#     if admin is None:
#         raise HTTPException(status_code=404, detail="Admin not found")
#     return admin

# def authorize_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     payload = decode_access_token(token)
#     if payload.get("role") != "admin":
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin authorization required")
#     return payload

# # Add Student (Admin Only)
# @admin_app.post("/add_student", response_model=schemas.StudentResponse, tags=["add by admin"])
# def add_student(student: schemas.StudentCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):
#     db_student = db.query(models.User).filter(models.User.username == student.username).first()
#     if db_student:
#         raise HTTPException(status_code=400, detail="Student already registered")
    
#     hashed_password = get_password_hash(student.password)
#     new_student = models.User(username=student.username, email=student.email, hashed_password=hashed_password, role="student")
#     db.add(new_student)
#     db.commit()
#     db.refresh(new_student)
    
#     return new_student

# # Add Teacher (Admin Only)
# @admin_app.post("/add_teacher", response_model=schemas.TeacherResponse, tags=["add by admin"])
# def add_teacher(teacher: schemas.TeacherCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):
#     db_teacher = db.query(models.User).filter(models.User.username == teacher.username).first()
#     if db_teacher:
#         raise HTTPException(status_code=400, detail="Teacher already registered")
    
#     hashed_password = get_password_hash(teacher.password)
#     new_teacher = models.User(username=teacher.username, email=teacher.email, hashed_password=hashed_password, role="teacher")
#     db.add(new_teacher)
#     db.commit()
#     db.refresh(new_teacher)
    
#     return new_teacher

# @admin_app.post("/add_class", response_model=schemas.ClassResponse, tags=["add by admin"])
# def add_class(class_data: schemas.ClassCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):
#     new_class = models.ClassSubject(name=class_data.name)
#     db.add(new_class)
#     db.commit()
#     db.refresh(new_class)
#     return new_class

# @admin_app.post("/add_subject", response_model=schemas.SubjectResponse, tags=["add by admin"])
# def add_subject(subject_data: schemas.SubjectCreate, db: Session = Depends(get_db), token: str = Depends(authorize_admin)):
#     class_exists = db.query(models.ClassSubject).filter(models.ClassSubject.id == subject_data.class_id).first()
#     if not class_exists:
#         raise HTTPException(status_code=400, detail="Class not found")
    
#     new_subject = models.ClassSubject(name=subject_data.name, class_id=subject_data.class_id)
#     db.add(new_subject)
#     db.commit()
#     db.refresh(new_subject)
#     return new_subject

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("admin_app:admin_app", host="127.0.0.1", port=8001)
