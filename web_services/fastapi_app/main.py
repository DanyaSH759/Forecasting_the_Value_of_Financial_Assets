from fastapi import FastAPI, UploadFile, File, Form
import pandas as pd
import psycopg2
from io import StringIO
import os
from sqlalchemy import create_engine

app = FastAPI()

def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "db"),
        database=os.getenv("POSTGRES_DB", "mydb"),
        user=os.getenv("POSTGRES_USER", "myuser"),
        password=os.getenv("POSTGRES_PASSWORD", "mypassword")
    )


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

def get_engine():
    return create_engine(
        f'postgresql+psycopg2://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@'
        f'{os.getenv("POSTGRES_HOST")}/{os.getenv("POSTGRES_DB")}'
    )


@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), asset: str = Form(...)):
    try:
        # Читаем CSV
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode("utf-8")))
        df = transform_data(df)
        print(df.dtypes)
        # Название таблицы на основе актива
        table_name = f"data_{asset.lower()}"

        # Запись в PostgreSQL
        engine = get_engine()

        # Загружаем в базу, если таблица есть — заменяем
        df.to_sql(table_name, engine, index=False, if_exists="replace")


        return {
                "status": "success",
                "rows": len(df),
                "dtypes": df.dtypes.astype(str).to_dict()
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    


def transform_data(data):
    '''Фнукция для трансформации текстовых строчек в числовые'''
    # Унификация неймингов датасетов
    if "Дата" not in [x for x in data.columns]: data = clean_ohlcv_dataframe(data)
    
    # перевод даты в индексы датасета
    data["Дата"] = pd.to_datetime(data["Дата"], format='mixed', dayfirst=True, errors='coerce')
    # data = data.sort_values("Дата").set_index("Дата")

    # меняем тип данных и удаляем заранее известные не информативные колонки
    for col in ["Цена", "Откр.", "Макс.", "Мин."]:
        if data[col].dtype == object or data[col].dtype.name == 'string':
            data[col] = data[col].str.replace(".", "", regex=False).str.replace(",", ".").astype(float)
        else:
            # если уже число — ничего не делаем
            data[col] = data[col].astype(float)

    data = data.drop(columns=["Объём", "Изм. %"], errors='ignore')

    #доп проверка на пустые строчки
    try:
        data.isnull().sum().sum() == 0
    except:
        print("В данных есть пустые значения!")

    # data = data.drop_duplicates()

    # создаём новые фичи
    # data = upgrade_dataset(data)
    
    return data


def clean_ohlcv_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Найти тикер по колонке Close_*
    close_col = [col for col in df.columns if col.startswith('Close_')]
    if not close_col:
        raise ValueError("Не найдена колонка с Close_")
    ticker = close_col[0].split('_')[1]  # получаем "0358.HK" и т.п.

    # Переименование колонок
    rename_map = {
        f'Date': 'Дата',
        f'Close_{ticker}': 'Цена',
        f'Open_{ticker}': 'Откр.',
        f'High_{ticker}': 'Макс.',
        f'Low_{ticker}': 'Мин.',
        f'Volume_{ticker}': 'Объём',
    }
    df = df.rename(columns=rename_map)

    # Добавим колонку "Изм. %"
    df['Изм. %'] = df['Цена'].pct_change() * 100

    # Упорядочим колонки
    desired_order = ['Дата', 'Цена', 'Откр.', 'Макс.', 'Мин.', 'Объём', 'Изм. %']
    df = df[desired_order]

    return df