
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
# from .. import schemas, models, database , main
# from app.models import Admin

# app = APIapp()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# @app.post("/auth/admin/login")
# async def authenticate_admin(
#     username: str,
#     password: str,
#     role: str,
#     db: Session = Depends(database.get_db) 
# ):
#     admin = db.query(Admin).filter(Admin.username == username).first()

#     if admin is None or not verify_password(password, admin.hashed_password):
#         raise HTTPException(status_code=400, detail="Invalid credentials")

#     if role != "admin":
#         raise HTTPException(status_code=403, detail="Access restricted to admin")


#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": admin.username, "role": role},
#         expires_delta=access_token_expires
#     )

#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "id": admin.id,
#         "username": admin.username,
#         "email": admin.email
#     }