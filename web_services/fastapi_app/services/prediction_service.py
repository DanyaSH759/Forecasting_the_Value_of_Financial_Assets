import pandas as pd
import pickle
from utils.dataset_trunsform import transform_data, return_x_y, generate_next_dates, upgrade_dataset
from services.s3_service import download_model_from_s3
from db.database import get_engine
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor
import numpy as np

import torch
import torch.nn as nn

def predict_asset(schema: str, asset: str):
    engine = get_engine()
    query = f'SELECT * FROM "{schema}"."{asset}"'

    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        raise RuntimeError(f"Ошибка при загрузке данных: {e}")

    df_real_last_15 = df[["Date", "Цена"]].iloc[-15:]
    df_real_last_15 = df_real_last_15.rename(columns={"Date": "Дата"})
    df_real_last_15_json = df_real_last_15.to_dict(orient="records")

    # 2. Трансформация данных
    try:
        df_ready = transform_data(df)
    except Exception as e:
        return {"error": f"Ошибка при трансформации данных: {e}"}

    # # 3. Скачивание модели
    # try:
    #     model_path = download_model_from_s3(asset)
    #     with open(model_path, "rb") as f:
    #         model = pickle.load(f)
    # except Exception as e:
    #     return {"error": f"Ошибка при скачивании или загрузке модели: {e}"}

    # 4. Определение типа модели
    model_path = download_model_from_s3(asset)
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        print(f"Загружена модель типа: {type(model)}")
        if isinstance(model, LGBMRegressor):
            model_type = "LGBM"
        elif isinstance(model, GradientBoostingRegressor):
            model_type = "GradientBoosting"
        else:
            raise ValueError("Неизвестный тип модели")
    except Exception as e:
        try:
            from services.lstm_model_definitions import TunedLSTM
            df_ready_upgraded = upgrade_dataset(df_ready.copy())
            X_all, y_all = return_x_y(df_ready_upgraded)

            model = TunedLSTM(input_size=X_all.shape[1], hidden_size=219, num_layers=1, dropout=0.2908311773478998)
            state_dict = torch.load(model_path, map_location=torch.device("cpu"))
            model.load_state_dict(state_dict)
            model.eval()
            model_type = "LSTM"
        except Exception as inner_e:
            return {"error": f"Ошибка при загрузке модели как LSTM: {inner_e}"}


    if model_type == "LSTM":
        from sklearn.preprocessing import StandardScaler
        from torch.utils.data import DataLoader

        allowed_date = df_ready.index.dayofweek.unique().tolist()
        future_dates = generate_next_dates(df_ready.index.max(), allowed_date, num_days=15)

        predictions = []
        history = df_ready.copy()


        # === Гиперпараметры ===
        seq_len = 15

        # === Масштабирование ===
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()

        # === Подготовка history ===
        history = upgrade_dataset(df_ready.copy())
        X_all, y_all = return_x_y(history)

        X_scaled = pd.DataFrame(scaler_X.fit_transform(X_all), columns=X_all.columns)
        y_scaled = pd.Series(scaler_y.fit_transform(y_all.values.reshape(-1, 1)).flatten())

        # === Подготовка входной последовательности ===
        last_seq = X_scaled.iloc[-seq_len:].values
        future_dates = generate_next_dates(history.index.max(), allowed_date, num_days=15)

        allowed_date = df_ready.index.dayofweek.unique().tolist()
        future_dates = generate_next_dates(df_ready.index.max(), allowed_date, num_days=15)


        model.eval()
        with torch.no_grad():
            for i, future_date in enumerate(future_dates):
                # Прогноз
                x_tensor = torch.tensor(last_seq.reshape(1, seq_len, -1), dtype=torch.float32)
                y_pred_scaled = model(x_tensor).item()
                y_pred = scaler_y.inverse_transform([[y_pred_scaled]])[0][0]

                # Создание новой строки (аналог обычной модели)
                new_row = {
                    "Цена": y_pred,
                    "Откр.": y_pred,
                    "Макс.": y_pred,
                    "Мин.": y_pred,
                    "День недели": future_date.dayofweek,
                    "День": future_date.day,
                    "Месяц": future_date.month,
                    "Год": future_date.year,
                }

                # Лаги
                for lag in [5, 15, 30]:
                    for suf, col in zip(["_t", "_open", "_max", "_min"], ["Цена", "Откр.", "Макс.", "Мин."]):
                        new_row[f"lag_{lag}{suf}"] = history[col].iloc[-lag] if len(history) >= lag else y_pred

                # Разности
                for diff, label in zip([1, 5], ["5", "15"]):
                    for suf, col in zip(["_t", "_open", "_max", "_min"], ["Цена", "Откр.", "Макс.", "Мин."]):
                        new_row[f"diff_{label}{suf}"] = y_pred - history[col].iloc[-diff] if len(history) >= diff else 0

                # Скользящие окна
                for window in [5, 15]:
                    for suf, col in zip(["", "_open", "_max", "_min"], ["Цена", "Откр.", "Макс.", "Мин."]):
                        s = history[col].iloc[-window:] if len(history) >= window else history[col]
                        new_row[f"rol_std_{window}{suf}"] = s.std()
                        new_row[f"rol_min_{window}{suf}"] = s.min()
                        new_row[f"rol_max_{window}{suf}"] = s.max()

                # Обновление history
                new_row_df = pd.DataFrame(new_row, index=[future_date])
                history = pd.concat([history, new_row_df])

                # Пересчёт X для следующей итерации
                X_hist, _ = return_x_y(history)
                X_scaled = pd.DataFrame(scaler_X.transform(X_hist), columns=X_hist.columns)
                last_seq = X_scaled.iloc[-seq_len:].values

                # Сохраняем прогноз
                predictions.append({
                    "date": future_date.strftime("%Y-%m-%d"),
                    "price": y_pred
                })

        return {
            "predictions": predictions,
            "real_price_15_last": df_real_last_15_json,
            "model_type": model_type
        }

    # ----------------------------
    # Путь для LGBM / GBR
    # ----------------------------
    allowed_date = df_ready.index.dayofweek.unique().tolist()
    future_dates = generate_next_dates(df_ready.index.max(), allowed_date, num_days=15)

    predictions = []
    history = df_ready.copy()

    for future_date in future_dates:
        X, _ = return_x_y(history)
        if X.empty:
            raise RuntimeError("Недостаточно данных для построения признаков!")
        X_last = X.iloc[[-1]]
        y_pred = model.predict(X_last)[0]

        new_row = {
            "Цена": y_pred,
            "Откр.": y_pred,
            "Макс.": y_pred,
            "Мин.": y_pred,
            "День недели": future_date.dayofweek,
            "День": future_date.day,
            "Месяц": future_date.month,
            "Год": future_date.year,
        }

        for lag in [5, 15, 30]:
            for suf, col in zip(["_t", "_open", "_max", "_min"], ["Цена", "Откр.", "Макс.", "Мин."]):
                key = f"lag_{lag}{suf}"
                new_row[key] = history[col].iloc[-lag] if len(history) >= lag else y_pred

        for diff, label in zip([1, 5], ["5", "15"]):
            for suf, col in zip(["_t", "_open", "_max", "_min"], ["Цена", "Откр.", "Макс.", "Мин."]):
                key = f"diff_{label}{suf}"
                new_row[key] = y_pred - history[col].iloc[-diff] if len(history) >= diff else 0

        for window in [5, 15]:
            for suf, col in zip(["", "_open", "_max", "_min"], ["Цена", "Откр.", "Макс.", "Мин."]):
                s = history[col].iloc[-window:] if len(history) >= window else history[col]
                new_row[f"rol_std_{window}{suf}"] = s.std()
                new_row[f"rol_min_{window}{suf}"] = s.min()
                new_row[f"rol_max_{window}{suf}"] = s.max()

        new_row_df = pd.DataFrame(new_row, index=[future_date])
        history = pd.concat([history, new_row_df])
        predictions.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "price": y_pred
        })

    return {
        "predictions": predictions,
        "real_price_15_last": df_real_last_15_json,
        "model_type": model_type
    }

