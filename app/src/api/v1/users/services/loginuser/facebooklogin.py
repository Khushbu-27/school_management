import os
import requests
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.database import get_db
from app.src.api.v1.users.model.users import User
from app.src.api.v1.users.user_authentication.auth import create_access_token


ACCESS_TOKEN_EXPIRE_MINUTES = 60 

router = APIRouter()

@router.get(
    "/auth/facebook-login",
    tags=["facebook login"],
    summary="Login with Facebook",
    description="""
    Redirects the user to the Facebook Login page.

    **Select the link below to login with Facebook:**

    [Login with Facebook](http://localhost:8000/auth/facebook-login)
    """,
)
def facebook_login():
    facebook_oauth_url = (
        "https://www.facebook.com/v12.0/dialog/oauth"
        f"?client_id={os.getenv('FACEBOOK_APP_ID')}"
        f"&redirect_uri={os.getenv('FACEBOOK_REDIRECT_URI')}"
        "&state=your_custom_state_string"
        "&scope=email,public_profile"
    )
    return RedirectResponse(url=facebook_oauth_url)


@router.get("/auth/facebook-login/callback", tags=["facebook login"], summary="Facebook Login Callback")
def facebook_callback(code: str, db: Session = Depends(get_db)):
    token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
    token_params = {
        "client_id": os.getenv("FACEBOOK_APP_ID"),
        "redirect_uri": os.getenv("FACEBOOK_REDIRECT_URI"),
        "client_secret": os.getenv("FACEBOOK_APP_SECRET"),
        "code": code,
    }
    token_response = requests.get(token_url, params=token_params)
    token_data = token_response.json()

    if "error" in token_data:
        raise HTTPException(status_code=400, detail=token_data["error"]["message"])

    user_info_url = "https://graph.facebook.com/me"
    user_info_params = {"fields": "id,name,email", "access_token": token_data["access_token"]}
    user_info_response = requests.get(user_info_url, params=user_info_params)
    user_info = user_info_response.json()

    if "error" in user_info:
        raise HTTPException(status_code=400, detail=user_info["error"]["message"])

    user = db.query(User).filter(User.email == user_info.get("email")).first()
    if not user:
        user = User(
            username=user_info["name"].replace(" ", "_"),
            email=user_info.get("email"),
            role="student",
        )
        db.add(user)
        db.commit()

    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "Bearer",
        "user_info": user_info,
    }
