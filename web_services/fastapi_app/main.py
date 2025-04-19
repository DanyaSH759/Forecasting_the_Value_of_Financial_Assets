import os
from fastapi import FastAPI
import psycopg2

app = FastAPI()

@app.get("/db-check")
def db_check():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        conn.close()
        return {"db_status": "ok", "result": result}
    except Exception as e:
        return {"db_status": "error", "error": str(e)}
