from fastapi import FastAPI
import psycopg2

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is running"}

@app.get("/db-check")
def db_check():
    try:
        conn = psycopg2.connect(
            host="db",
            database="mydb",
            user="myuser",
            password="mypassword"
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        conn.close()
        return {"db_status": "ok", "result": result}
    except Exception as e:
        return {"db_status": "error", "error": str(e)}
