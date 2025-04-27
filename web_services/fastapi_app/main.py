from fastapi import FastAPI
from routers.predict_router import router as predict_router
from routers.healthcheck_router import router as healthcheck_router

app = FastAPI()

app.include_router(predict_router, prefix="/predict", tags=["Predict"])
app.include_router(healthcheck_router, prefix="/health", tags=["HealthCheck"])
