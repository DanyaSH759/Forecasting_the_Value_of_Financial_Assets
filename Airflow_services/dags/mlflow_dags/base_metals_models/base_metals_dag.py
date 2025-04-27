from datetime import datetime
import os
import json
import logging
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from lightgbm import LGBMRegressor

import mlflow
from mlflow.tracking import MlflowClient

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from mlflow_dags.dataset_transform_func.preprocessing import (
    split_data,
    return_x_y,
    clean_ohlcv_dataframe,
    transform_data,
    upgrade_dataset
)

_LOG = logging.getLogger()
_LOG.addHandler(logging.StreamHandler())

# Загружаем конфигурацию активов из JSON-файла
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "base_metals_config.json")

with open(ASSETS_PATH, "r") as f:
    assets = json.load(f)

def create_dag(asset_name, config):

    def load_data_from_db(**context):

        """Загружает данные из таблицы в PostgreSQL и передаёт их в XCom."""
        
        hook = PostgresHook(postgres_conn_id="main_postgres")
        engine = hook.get_sqlalchemy_engine()
        query = f'SELECT * FROM {config["schema_table"]}'
        df = pd.read_sql(query, engine)

        _LOG.info(f'Данные загружены из таблицы {config["schema_table"]}')

        # сразу изменим дату на стандартную для нашего обучения
        df["Дата"] = pd.to_datetime(df["Date"], dayfirst=True, errors='coerce')
        context['ti'].xcom_push(key="raw_df", value=df)

    def transform_data_stage(**context):

        """Трансформирует сырые данные: парсинг, очистка, фичи."""

        df = context['ti'].xcom_pull(key="raw_df", task_ids="load_data")
        df_transformed = transform_data(df)

        _LOG.info(f'Подготовка датасета завершена')

        context['ti'].xcom_push(key="df_ready", value=df_transformed)

    def learn_model(**context):

        """
        1. Делит данные на train/test
        2. Обучает модель
        3. Логирует метрики и модель в MLflow
        4. Сохраняет model.pkl из артефактов
        5. Загружает model.pkl в S3
        """

        df = context['ti'].xcom_pull(key="df_ready", task_ids="transform_data")
        train, _, test = split_data(df)
        X_train, y_train = return_x_y(train)
        X_test, y_test = return_x_y(test)

        model = LGBMRegressor(**config["best_params"], verbose=-1)
        model.fit(X_train, y_train)
        prediction = model.predict(X_test)

        mlflow.set_tracking_uri("http://mlflow-service:5000")
        mlflow.set_experiment(config["experiment_name"])

        with mlflow.start_run() as run:
            mlflow.log_param("model_type", "LGBMRegressor")
            mlflow.log_metric("r2", r2_score(y_test, prediction))
            mlflow.log_metric("mae", mean_absolute_error(y_test, prediction))
            mlflow.log_metric("rmse", np.sqrt(mean_squared_error(y_test, prediction)))
            mlflow.sklearn.log_model(model, artifact_path=config["artifact_path"])

            #  Скачиваем model.pkl из артефактов этого run-а
            client = MlflowClient()
            artifact_full_path = f'{config["artifact_path"]}/model.pkl'
            local_dir = "/tmp/mlflow_model"
            os.makedirs(local_dir, exist_ok=True)
            local_model_path = client.download_artifacts(run.info.run_id, artifact_full_path, dst_path=local_dir)

            #  Загружаем в фиксированное место S3
            hook = S3Hook(aws_conn_id="s3_cloud")
            client_s3 = hook.get_conn()
            client_s3.upload_file(
                Filename=local_model_path,
                Bucket="my-bucket-main",
                Key=config["s3_key"]
            )

        _LOG.info(f'Обучения завершено. Модель сохранена в бакете')

    with DAG(
        dag_id=f"train_{asset_name}_model",
        start_date=datetime(2024, 1, 1),
        schedule_interval=None,
        catchup=False,
        tags=["training", asset_name, "mlflow"]
    ) as dag:

        t1 = PythonOperator(
            task_id="load_data",
            python_callable=load_data_from_db,
            provide_context=True
        )

        t2 = PythonOperator(
            task_id="transform_data",
            python_callable=transform_data_stage,
            provide_context=True
        )

        t3 = PythonOperator(
            task_id="learn_model",
            python_callable=learn_model,
            provide_context=True
        )

        t1 >> t2 >> t3

    return dag

# Генерируем DAG-и автоматически
for asset, cfg in assets.items():
    globals()[f"train_{asset}_model"] = create_dag(asset, cfg)
