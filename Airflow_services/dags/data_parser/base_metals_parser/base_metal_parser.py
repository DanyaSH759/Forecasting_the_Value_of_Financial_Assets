import os
import yaml
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import time

CONFIG_PATH = "/opt/airflow/dags/data_parser/base_metals_parser/base_metal_parser.yaml"

# логи
_LOG = logging.getLogger()
_LOG.addHandler(logging.StreamHandler())


def test_pg_conn():
    try:
        hook = PostgresHook(postgres_conn_id="main_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        _LOG.info(f'Коннект с БД установлен')
    except:
        _LOG.info(f'Нет коннетка к БД')

def fetch_assets_from_group(group_name):
    
    # Загружаем конфиг из YAML
    with open(CONFIG_PATH, "r") as f:
        all_assets = yaml.safe_load(f)

    tickers = all_assets.get(group_name, {})
    if not tickers:
        raise ValueError(f"No tickers found for group: {group_name}")

    # Получаем SQLAlchemy engine из Airflow Connection
    hook = PostgresHook(postgres_conn_id="main_postgres")
    engine = hook.get_sqlalchemy_engine()
    with engine.begin() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS base_metals")

    start = '2016-01-01'
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')

    for ticker, table in tickers.items():
        _LOG.info(f'Загружаю {ticker}')
        for attempt in range(3):
            try:
                _LOG.info(f"[{ticker}] Попытка {attempt + 1} из 3")
                df = yf.download(ticker, start=start, end=end_date, interval="1d", progress=False, timeout=120)
                if not df.empty:
                    _LOG.info(f'Скачен датасет за период 2016-2025')
                    break
                
                if not df.empty:
                    _LOG.info(f"[{ticker}] Данные успешно получены.")
                else:
                    _LOG.warning(f"[{ticker}] Пустой DataFrame, retry через 120 сек...")

            except Exception as e:
                _LOG.warning(f"[{ticker}] Попытка скачивания не удалась: {e}")

            time.sleep(120)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(col).strip() for col in df.columns.values]

        time.sleep(120)

        # Создаём карту переименования под текущий тикер
        rename_map = {
            f"Date": "Дата",
            f"Close_{ticker}": "Цена",
            f"Open_{ticker}": "Откр.",
            f"High_{ticker}": "Макс.",
            f"Low_{ticker}": "Мин.",
            f"Volume_{ticker}": "Объём"
        }

        df = df.rename(columns=rename_map)

        df.reset_index(inplace=True)
        print(f"Writing {ticker} → schema '{group_name}', table '{table}'")
        df.to_sql(
            name=table,
            con=engine,
            schema=group_name,
            if_exists="replace",
            index=False
        )
        _LOG.info(f'Таблица загружена в БД {ticker}')


with DAG(
    dag_id="base_metal_parser",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["parser"]
) as dag:

    test_connect = PythonOperator(
        task_id="test_pg_conn",
        python_callable=test_pg_conn
    )

    upload_task = PythonOperator(
        task_id="fetch_assets_from_group",
        python_callable=fetch_assets_from_group,
        op_args=["base_metals"] 
    )

    test_connect >> upload_task