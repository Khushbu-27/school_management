
from datetime import datetime, time, timedelta
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request , status
from passlib.context import CryptContext
from requests import Session
from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.services.utils.response_utils import Response

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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authorize_admin(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin authorization required")
    return payload

# def authorize_user(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
#     payload = decode_access_token(token)
#     username = payload.get("sub")
#     role = payload.get("role")

#     if role not in ["admin", "teacher", "student"]:
#         return Response(
#             status_code=403,
#             message="Invalid role",
#             data= {}
#         ).send_error_response()

#     user = db.query(User).filter(User.username == username).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
#     return user

def authorize_user(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    user_email = payload.get("user_email")
    username = payload.get("sub")
    
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    # user_email = db.query(User).filter(User.email == user_email).first()
    
    # if  not user_email:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User email not found")  
    
    if user.role not in ["admin", "teacher", "student"]:
        return Response(
            status_code=403,
            message="Invalid role",
            data={}
        ).send_error_response()

    return user

# def authorize_user(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
#     try:
        
#         payload = decode_access_token(token)
#         user_email = payload.get("sub")
#         username = payload.get("username")
#         user.role = payload.get("role")

        
#         if not user_email and not username:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED, 
#                 detail="Invalid authentication credentials"
#             )
#         if user.role not in ["admin", "teacher", "student"]:
#             return Response(
#                 status_code=403,
#                 message="Invalid role",
#                 data={}
#             ).send_error_response()
            
#         user = db.query(User).filter(
#             (User.email == user_email) | (User.username == username)).first()
        
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, 
#                 detail="User not found"
#             )

#         return user

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred during authentication"
#         )

