from fastapi import APIRouter, UploadFile, File
from services.custom_predict_services import custom_predict

router = APIRouter()

@router.post("/custom_predict")
async def custom_prediction(file: UploadFile = File(...)):
    return await custom_predict(file)
