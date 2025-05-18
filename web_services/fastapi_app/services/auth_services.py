import pandas as pd
from db.database import get_engine
from sqlalchemy import text

def login_user(username: str, password: str):
    engine = get_engine()
    # Важно: используйте параметризованные запросы для безопасности!
    query = """
    select case 
        when (select true from users where username = %s and password_hash = %s) is true 
        then 'user in database' 
        else 'not find user in db' 
    end as request;
    """
    
    try:
        # Используйте параметры вместо форматирования строки
        df = pd.read_sql(query, engine, params=(username, password))
    except Exception as e:
        raise RuntimeError(f"Ошибка при запросе данных пользователя: {e}")

    if not df.empty and df.iloc[0, 0] == "user in database":
        return {"status": "ok"}
    else: 
        return {"status": "Пользователь не найден в базе"}


def register_user(username: str, password: str):
    engine = get_engine()
    check_query = text("SELECT 1 FROM users WHERE username = :username")
    insert_query = text("""
        INSERT INTO users (username, password_hash) 
        VALUES (:username, :password_hash)
    """)

    password_hash = password  # todo: hashing later

    try:
        with engine.begin() as conn:
            existing = conn.execute(check_query, {"username": username}).fetchall()
            if existing:
                raise ValueError("Пользователь с таким именем уже существует")

            conn.execute(insert_query, {
                "username": username,
                "password_hash": password_hash
            })

        return {"status": "ok", "message": "Пользователь успешно зарегистрирован"}

    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Ошибка при регистрации пользователя: {e}")