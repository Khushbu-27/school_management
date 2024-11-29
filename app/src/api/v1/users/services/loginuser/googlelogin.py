
from datetime import timedelta
from fastapi import Depends, APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import os
from requests import Session
from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.user_authentication.auth import ACCESS_TOKEN_EXPIRE_MINUTES, JWTBearer, create_access_token, decode_access_token 
import requests
from dotenv import load_dotenv
router = APIRouter()

load_dotenv()
# Login with Google
@router.get(
    "/auth/login",  
    tags=["Google login"],
    summary="Login with Google",
    description="""
    Redirects the user to the Google Login page.

    **Select the link below to login with Google:**

    [Login with Google](http://127.0.0.1:8000/auth/login)
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

@router.get("/auth/login/callback", tags=["Google login"], summary="Google Login Callback")
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

    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        user = User(
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

@router.get("/protected-endpoint", tags=["Google login"])
def protected_endpoint(current_user: str = Depends(get_current_user)):
  
    return {"message": "Access granted", "user": current_user}