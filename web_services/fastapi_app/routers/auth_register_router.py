from fastapi import APIRouter
from models.auth_request import AuthRequest
from services.auth_services import register_user

router = APIRouter()

@router.post("/register")
def register(request: AuthRequest):
    try:
        result = register_user(request.username, request.password)
        return result
    except Exception as e:
        return {"status": "error", "detail": str(e)}