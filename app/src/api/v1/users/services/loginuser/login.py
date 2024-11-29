from datetime import date
from fastapi.security import OAuth2PasswordRequestForm
from requests import Session

from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.schema.userschemas import AdminCreate, AdminResponse
from app.src.api.v1.users.user_authentication.auth import create_access_token, get_password_hash, verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()


# REQUIREMENT: Registration for Admin only
@router.post("/admin/register")
def admin_register(admin: AdminCreate, db: Session = Depends(get_db)):
    """
    Register an admin after validating email and ensuring it is valid.
    """
    if admin.password != admin.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirm password do not match"
        )
    
    if db.query(User).filter(User.username == admin.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.query(User).filter(User.email == admin.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(admin.password)
    new_admin = User(
        username=admin.username,
        email=admin.email,
        hashed_password=hashed_password,
        role="admin"
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return{
            "data": {
                "data" : new_admin
            },
            "meta": {
                "message": "Admin registered successfully", 
                "status_code": 201
            }
    }
        # "message": "Your email has been verify. You can login with your username",
        # "id": new_admin.id,
        # "username": new_admin.username,
        # "email": new_admin.email
    
# REQUIREMENT: Login users
@router.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):   
        return Response(
            status_code=401,
            message="User not found",
            data= {}
        ).send_error_response()

    today = date.today()

    if user.role == "admin":
        access_token = create_access_token(data={"sub": user.username, "role": "admin"})
        
        response_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "access_token": access_token,
            "token_type": "Bearer",
        }
        return Response(
            status_code=201,
            message="Admin login successfully",
            data= response_data 
        ).send_success_response()

    elif user.role in ["teacher", "student"]:
        
        if user.last_login_date != today:
            user.attendance += 1
            user.last_login_date = today    
        db.commit() 

        access_token = create_access_token(data={"sub": user.username})
        
        response_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "access_token": access_token,
            "token_type": "Bearer",
        }
        return Response(
            status_code=201,
            message=f"{user.role.capitalize()} login successful",
            data= response_data 
        ).send_success_response()
        