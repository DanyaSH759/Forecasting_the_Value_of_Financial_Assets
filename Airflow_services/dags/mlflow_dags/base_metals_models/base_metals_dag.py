from datetime import datetime
import os
import json
import logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

import mlflow
from mlflow.tracking import MlflowClient

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from mlflow_dags.dataset_transform_func.preprocessing import (
    split_data,
    return_x_y,
    transform_data,
    upgrade_dataset
)
from mlflow_dags.base_metals_models.lstm_model import TunedLSTM, SlidingWindowDataset

_LOG = logging.getLogger()
_LOG.addHandler(logging.StreamHandler())

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "base_metals_config.json")
with open(ASSETS_PATH, "r") as f:
    assets = json.load(f)

def create_dag(asset_name, config):

    def load_data_from_db(**context):
        hook = PostgresHook(postgres_conn_id="main_postgres")
        engine = hook.get_sqlalchemy_engine()
        if config["full_learn"]:
            query = f'SELECT * FROM {config["schema_table"]} WHERE Date >= "2022-01-01"'
        else:
            query = f'SELECT * FROM {config["schema_table"]}'
        df = pd.read_sql(query, engine)
        df["Дата"] = pd.to_datetime(df["Date"], dayfirst=True, errors='coerce')
        context['ti'].xcom_push(key="raw_df", value=df)

    def transform_data_stage(**context):
        df = context['ti'].xcom_pull(key="raw_df", task_ids="load_data")
        df_transformed = transform_data(df)
        context['ti'].xcom_push(key="df_ready", value=df_transformed)

    def learn_model(**context):
        df = context['ti'].xcom_pull(key="df_ready", task_ids="transform_data")
        train, _, test = split_data(df)
        train = upgrade_dataset(train)
        test = upgrade_dataset(test)

        X_train, y_train = return_x_y(train)
        X_test, y_test = return_x_y(test)

        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        X_train_scaled = pd.DataFrame(scaler_X.fit_transform(X_train), columns=X_train.columns)
        X_test_scaled = pd.DataFrame(scaler_X.transform(X_test), columns=X_test.columns)
        y_train_scaled = pd.Series(scaler_y.fit_transform(y_train.values.reshape(-1, 1)).flatten())
        y_test_scaled = pd.Series(scaler_y.transform(y_test.values.reshape(-1, 1)).flatten())

        seq_len = config.get("seq_len", 15)
        train_ds = SlidingWindowDataset(X_train_scaled, y_train_scaled, seq_len)
        test_ds = SlidingWindowDataset(X_test_scaled, y_test_scaled, seq_len)
        train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
        test_loader = DataLoader(test_ds, batch_size=32)

        model = TunedLSTM(
            input_size=X_train.shape[1],
            hidden_size=config["best_params"]["hidden_size"],
            num_layers=config["best_params"]["num_layers"],
            dropout=config["best_params"]["dropout"]
        )
        optimizer = torch.optim.Adam(model.parameters(), lr=config["best_params"]["lr"])
        criterion = nn.MSELoss()

        model.train()
        for _ in range(config.get("epochs", 50)):
            for x_batch, y_batch in train_loader:
                output = model(x_batch)
                loss = criterion(output, y_batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        model.eval()
        y_preds = []
        with torch.no_grad():
            for x_batch, _ in test_loader:
                pred = model(x_batch)
                y_preds.extend(pred.numpy())

        y_preds_rescaled = scaler_y.inverse_transform(np.array(y_preds).reshape(-1, 1)).flatten()
        y_test_rescaled = scaler_y.inverse_transform(y_test_scaled.values[seq_len:].reshape(-1, 1)).flatten()

        mlflow.set_tracking_uri("http://mlflow-service:5000")
        mlflow.set_experiment(f'{config["experiment_name"]}_lstm')

        with mlflow.start_run() as run:
            mlflow.log_param("model_type", "LSTM")
            mlflow.log_params(config["best_params"])
            mlflow.log_metric("rmse", np.sqrt(mean_squared_error(y_test_rescaled, y_preds_rescaled)))
            mlflow.log_metric("mae", mean_absolute_error(y_test_rescaled, y_preds_rescaled))
            mlflow.log_metric("r2", r2_score(y_test_rescaled, y_preds_rescaled))

            model_path = "/tmp/model.pt"
            torch.save(model.state_dict(), model_path)

            hook = S3Hook(aws_conn_id="s3_cloud")
            client_s3 = hook.get_conn()
            client_s3.upload_file(
                Filename=model_path,
                Bucket="my-bucket-main",
                Key=config["s3_key"]
            )

    with DAG(
        dag_id=f"train_{asset_name}_model_lstm",
        start_date=datetime(2024, 1, 1),
        schedule_interval=None,
        catchup=False,
        tags=["training", asset_name, "mlflow"]
    ) as dag:
        t1 = PythonOperator(task_id="load_data", python_callable=load_data_from_db)
        t2 = PythonOperator(task_id="transform_data", python_callable=transform_data_stage)
        t3 = PythonOperator(task_id="learn_model", python_callable=learn_model)
        t1 >> t2 >> t3

    return dag

for asset, cfg in assets.items():
    globals()[f"train_{asset}_model_lstm"] = create_dag(asset, cfg)
