from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import datetime

def test_pg_conn():
    hook = PostgresHook(postgres_conn_id="main_postgres")
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cursor.fetchall()
    print(" Tables in public schema:")
    for table in tables:
        print(table[0])

with DAG(
    dag_id="postgres_conn_test",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["postgres", "test"]
) as dag:

    check_postgres = PythonOperator(
        task_id="list_postgres_tables",
        python_callable=test_pg_conn
    )

    check_postgres