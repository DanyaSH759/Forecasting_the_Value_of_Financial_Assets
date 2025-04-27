from fastapi import APIRouter
from db.database import get_engine
import psycopg2
from core.config import settings

router = APIRouter()

@router.get("/db-check")
def db_check():
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        conn.close()
        return {"db_status": "ok", "result": result}
    except Exception as e:
        return {"db_status": "error", "error": str(e)}