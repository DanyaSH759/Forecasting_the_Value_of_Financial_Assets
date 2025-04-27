from fastapi import APIRouter
from models.predict_request import PredictRequest
from services.prediction_service import predict_asset

router = APIRouter()

@router.post("")
def predict(request: PredictRequest):
    try:
        result = predict_asset(request.schema, request.asset_name)
        return result
    except Exception as e:
        return {"status": "error", "detail": str(e)}
