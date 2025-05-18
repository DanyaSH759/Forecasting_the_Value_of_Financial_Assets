from fastapi import APIRouter
from models.auth_request import AuthRequest
from services.auth_services import login_user

router = APIRouter()

@router.post("/login")
def login(request: AuthRequest):
    try:
        result = login_user(request.username, request.password)
        return result
    except Exception as e:
        return {"status": "error", "detail": str(e)}