import os
from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from datetime import datetime

BUCKET_NAME = "my-bucket-main"
TEST_FILE_KEY = "airflow-test/hello_2.txt"

def list_files():
    hook = S3Hook(aws_conn_id='s3_cloud')
    files = hook.list_keys(bucket_name=BUCKET_NAME)
    print(" Files in bucket:")
    for f in files or []:
        print(f)

def upload_dummy_file():
    hook = S3Hook(aws_conn_id='s3_cloud')
    hook.load_string(
        string_data="Hello from Airflow ",
        key=TEST_FILE_KEY,
        bucket_name=BUCKET_NAME,
        replace=True
    )
    print(f" Uploaded file: s3://{BUCKET_NAME}/{TEST_FILE_KEY}")

with DAG(
    dag_id="s3_test_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["s3", "test"]
) as dag:

    list_task = PythonOperator(
        task_id="list_files_in_s3",
        python_callable=list_files
    )

    upload_task = PythonOperator(
        task_id="upload_dummy_file",
        python_callable=upload_dummy_file
    )

    list_task >> upload_task
