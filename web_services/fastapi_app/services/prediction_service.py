import pandas as pd
import pickle
from utils.dataset_trunsform import transform_data, return_x_y, generate_next_dates, upgrade_dataset
from services.s3_service import download_model_from_s3
from db.database import get_engine
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor

def predict_asset(schema: str, asset: str):
    engine = get_engine()
    query = f'SELECT * FROM "{schema}"."{asset}"'

    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        raise RuntimeError(f"Ошибка при загрузке данных: {e}")

    df_real_last_15 = df[["Date", "Цена"]].iloc[-15:] # Берем и дату, и цену
    df_real_last_15 = df_real_last_15.rename(columns={"Date": "Дата"}) # Переименуем красиво
    df_real_last_15_json = df_real_last_15.to_dict(orient="records")

    # 2. Трансформация данных
    try:
        df_ready = transform_data(df)
    except Exception as e:
        return {"error": f"Ошибка при трансформации данных: {e}"}

    # 3. Скачивание модели
    try:
        model_path = download_model_from_s3(asset)
        with open(model_path, "rb") as f:
            model = pickle.load(f)
    except Exception as e:
        return {"error": f"Ошибка при скачивании или загрузке модели: {e}"}

    # 🛠️ Определяем тип модели
    print(f"Загружена модель типа: {type(model)}")

    model_type = None
    if isinstance(model, LGBMRegressor):
        model_type = "LGBM"
    elif isinstance(model, GradientBoostingRegressor):
        model_type = "GradientBoosting"
    else:
        model_type = "Unknown"

    # 4. Генерация новых дат
    allowed_date = df_ready.index.dayofweek.unique().tolist()
    future_dates = generate_next_dates(df_ready.index.max(), allowed_date, num_days=15)

    predictions = []
    history = df_ready.copy()

    for future_date in future_dates:
        # Подготовка X для модели
        X, _ = return_x_y(history)
        if X.empty:
            raise RuntimeError("Недостаточно данных для построения признаков!")

        X_last = X.iloc[[-1]]

        # # 🛠️ Фиксим NaN только для GradientBoostingRegressor
        # if model_type == "GradientBoosting":
        #     X_last = X_last.fillna(0)

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

        # Проставляем лаги
        for lag in [5, 15, 30]:
            if len(history) >= lag:
                new_row[f"lag_{lag}_t"] = history["Цена"].iloc[-lag]
                new_row[f"lag_{lag}_open"] = history["Откр."].iloc[-lag]
                new_row[f"lag_{lag}_max"] = history["Макс."].iloc[-lag]
                new_row[f"lag_{lag}_min"] = history["Мин."].iloc[-lag]
            else:
                new_row[f"lag_{lag}_t"] = y_pred
                new_row[f"lag_{lag}_open"] = y_pred
                new_row[f"lag_{lag}_max"] = y_pred
                new_row[f"lag_{lag}_min"] = y_pred

        # Проставляем разности
        for diff, label in zip([1, 5], ["5", "15"]):
            if len(history) >= diff:
                new_row[f"diff_{label}_t"] = y_pred - history["Цена"].iloc[-diff]
                new_row[f"diff_{label}_open"] = y_pred - history["Откр."].iloc[-diff]
                new_row[f"diff_{label}_max"] = y_pred - history["Макс."].iloc[-diff]
                new_row[f"diff_{label}_min"] = y_pred - history["Мин."].iloc[-diff]
            else:
                new_row[f"diff_{label}_t"] = 0
                new_row[f"diff_{label}_open"] = 0
                new_row[f"diff_{label}_max"] = 0
                new_row[f"diff_{label}_min"] = 0

        # Проставляем скользящие окна
        for window in [5, 15]:
            recent_prices = history["Цена"].iloc[-window:] if len(history) >= window else history["Цена"]
            new_row[f"rol_std_{window}"] = recent_prices.std()
            new_row[f"rol_min_{window}"] = recent_prices.min()
            new_row[f"rol_max_{window}"] = recent_prices.max()

            for col_suffix, col_name in [("", "Цена"), ("_open", "Откр."), ("_max", "Макс."), ("_min", "Мин.")]:
                recent_values = history[col_name].iloc[-window:] if len(history) >= window else history[col_name]
                new_row[f"rol_std_{window}{col_suffix}"] = recent_values.std()
                new_row[f"rol_min_{window}{col_suffix}"] = recent_values.min()
                new_row[f"rol_max_{window}{col_suffix}"] = recent_values.max()

        # Добавляем новую строку
        new_row_df = pd.DataFrame(new_row, index=[future_date])
        history = pd.concat([history, new_row_df])

        # Сохраняем прогноз
        predictions.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "price": y_pred
        })
    # 6. Возвращаем результаты
    return {
        "predictions": predictions,
        "real_price_15_last": df_real_last_15_json,
        "model_type": model_type
    }
