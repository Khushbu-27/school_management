
from fastapi import Depends, APIRouter, HTTPException
from requests import Session
from app.src.api.v1.users.model.users import User
from app.database.database import get_db
from app.src.api.v1.users.user_authentication.auth import authorize_user
from app.src.api.v1.users.services.utils.response_utils import Response

router = APIRouter()

# REQUIREMENT: admin can delete users
@router.delete("/admin/delete_user/{user_id}" )
async def delete_user(user_id: int, current_user=Depends(authorize_user), db: Session = Depends(get_db)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, details= 'Only admin can delete users')
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    response_data = {
        "id": user.id,
        "username": user.username,
        "email":user.email
    }
    return Response(
        status_code=200,
        message="User delete successfully",
        data= response_data 
    ).send_success_response()