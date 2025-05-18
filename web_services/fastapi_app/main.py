from fastapi import FastAPI
from routers.predict_router import router as predict_router
from routers.healthcheck_router import router as healthcheck_router
from routers.auth_login_router import router as auth_login_router
from routers.auth_register_router import router as auth_register_router
from routers.custom_predict_router import router as custom_predict_router

app = FastAPI()

app.include_router(predict_router, prefix="/predict", tags=["Predict"])
app.include_router(healthcheck_router, prefix="/health", tags=["HealthCheck"])
app.include_router(auth_login_router, prefix="/login", tags=["auth_login"])
app.include_router(auth_register_router, prefix="/register", tags=["auth_register"])
app.include_router(custom_predict_router, prefix="/custom_predict", tags=["custom_predict"])