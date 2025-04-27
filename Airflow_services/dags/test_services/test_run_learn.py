from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import mlflow
import pandas as pd
import numpy as np
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from mlflow.models import infer_signature

def train_and_log_models():
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

    models = {
        "linear_regression": LinearRegression(),
    }

    housing = fetch_california_housing(as_frame=True)
    X_train, X_test, y_train, y_test = train_test_split(housing['data'], housing['target'])
    X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, test_size=0.15)


    try:
        mlflow.create_experiment("danila_shulyak")
    except:
        pass
    exp_id = mlflow.set_experiment("danila_shulyak").experiment_id

    with mlflow.start_run(run_name="shulyakds", experiment_id=exp_id, description="parent") as parent_run:
        for model_name, model in models.items():
            with mlflow.start_run(run_name=model_name, experiment_id=exp_id, nested=True) as child_run:
                model.fit(X_train, y_train)
                prediction = model.predict(X_val)

                eval_df = X_val.copy()
                eval_df["target"] = y_val

                # Логгируем модель
                signature = infer_signature(X_train, prediction)
                mlflow.sklearn.log_model(model, model_name, signature=signature)

                # Ручной логгинг метрик
                mlflow.log_metric("r2_score", r2_score(y_val, prediction))
                mlflow.log_metric("mae", mean_absolute_error(y_val, prediction))
                rmse = np.sqrt(mean_squared_error(y_val, prediction))
                mlflow.log_metric("rmse", rmse)


with DAG(
    dag_id="test_train_regression_models",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["mlflow", "training", "test"]
) as dag:

    train_models_task = PythonOperator(
        task_id="train_and_log_models",
        python_callable=train_and_log_models
    )
