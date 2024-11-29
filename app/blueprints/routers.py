from fastapi import APIRouter
from app.src.api.v1.exam.services.crud.createexam import router as create_exam_router
from app.src.api.v1.exam.services.crud.deleteexam import router as delete_exam_router
from app.src.api.v1.exam.services.crud.updateexam import router as update_exam_router
from app.src.api.v1.exam.services.crud.viewexam import router as view_exam_router
from app.src.api.v1.marks.services.crud.createmarks import router as create_marks_router
from app.src.api.v1.marks.services.crud.viewmarks import router as view_marks_router
from app.src.api.v1.users.services.crud.usercreate import router as user_create_router
from app.src.api.v1.users.services.crud.userdelete import router as user_delete_router
from app.src.api.v1.users.services.crud.userread.adminview import router as admin_view_router
from app.src.api.v1.users.services.crud.userread.studentview import router as student_view_router
from app.src.api.v1.users.services.crud.userread.teacherview import router as teacher_view_router
from app.src.api.v1.users.services.crud.userupdate.adminupdate import router as admin_update_router
from app.src.api.v1.users.services.crud.userupdate.studentupdate import router as student_update_router
from app.src.api.v1.users.services.crud.userupdate.teacherupdate import router as teacher_update_router
from app.src.api.v1.users.services.loginuser.login import router as login_router
from app.src.api.v1.users.services.loginuser.googlelogin import router as google_login_router
from app.src.api.v1.users.services.loginuser.facebooklogin import router as facebook_login_router
from app.src.api.v1.users.services.forgotpass.forgotpass import router as forgot_password_router

router = APIRouter()

router.include_router(create_exam_router, tags=["Exam"])
router.include_router(delete_exam_router, tags=["Exam"])
router.include_router(update_exam_router,tags=["Exam"])
router.include_router(view_exam_router, tags=["Exam"])
router.include_router(create_marks_router,tags=["Marks"])
router.include_router(view_marks_router, tags=["Marks"])
router.include_router(user_create_router, tags=["Admin Create"])
router.include_router(user_delete_router,  tags=["Admin Delete"])
router.include_router(admin_view_router, tags=["Admin View"])
router.include_router(student_view_router, tags=["Student View"])
router.include_router(teacher_view_router, tags=["Teacher View"])
router.include_router(admin_update_router,  tags=["Admin update"])
router.include_router(student_update_router, tags=["Student update"])
router.include_router(teacher_update_router, tags=["Teacher update"])
router.include_router(login_router, prefix="/login", tags=["Authentication"])
router.include_router(google_login_router)
router.include_router(facebook_login_router, prefix="/facebook-login")
router.include_router(forgot_password_router, tags = ["forgot password"])
