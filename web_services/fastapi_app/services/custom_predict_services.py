from fastapi import UploadFile, File
import pandas as pd
import tempfile
from sklearn.metrics import mean_absolute_percentage_error
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor
from utils.dataset_trunsform import *


async def custom_predict(file: UploadFile = File(...)):
    
    # 1. Чтение файла
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        df = pd.read_csv(tmp_path)
        df = clean_ohlcv_dataframe(df)
        df_transformed = transform_data(df)
    except Exception as e:
        return {"status": "error", "detail": f"Ошибка обработки CSV: {e}"}

    # 2. Разделение
    train, test = split_data(df_transformed, validation=False)
    train_upgraded = upgrade_dataset(train)
    test_upgraded = upgrade_dataset(test)

    if test_upgraded.empty:
        return {"status": "error", "detail": "Недостаточно данных для построения тестовых признаков"}

    X_train, y_train = return_x_y(train_upgraded)
    X_test, y_test = return_x_y(test_upgraded)

    if X_test.empty or y_test.empty:
        return {"status": "error", "detail": "X_test или y_test пусты после преобразования"}

    # 3. Обучение и оценка
    results = []
    for model_class in [LGBMRegressor, GradientBoostingRegressor]:
        model = model_class()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mape = mean_absolute_percentage_error(y_test, y_pred)
        results.append((model, model_class.__name__, mape))

    # 4. Выбор лучшей модели
    best_model, model_name, _ = min(results, key=lambda x: x[2])

    # 5. Построение прогноза
    history = upgrade_dataset(df_transformed.copy())
    future_dates = generate_next_dates(history.index.max(), history.index.dayofweek.unique(), num_days=15)

    predictions = []
    for future_date in future_dates:
        X_hist, _ = return_x_y(history)
        if X_hist.empty:
            break
        X_last = X_hist.iloc[[-1]]
        y_pred = best_model.predict(X_last)[0]

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
                new_row[f"lag_{lag}{suf}"] = history[col].iloc[-lag] if len(history) >= lag else y_pred

        for diff, label in zip([1, 5], ["5", "15"]):
            for suf, col in zip(["_t", "_open", "_max", "_min"], ["Цена", "Откр.", "Макс.", "Мин."]):
                new_row[f"diff_{label}{suf}"] = y_pred - history[col].iloc[-diff] if len(history) >= diff else 0

        for window in [5, 15]:
            for suf, col in zip(["", "_open", "_max", "_min"], ["Цена", "Откр.", "Макс.", "Мин."]):
                s = history[col].iloc[-window:] if len(history) >= window else history[col]
                new_row[f"rol_std_{window}{suf}"] = s.std()
                new_row[f"rol_min_{window}{suf}"] = s.min()
                new_row[f"rol_max_{window}{suf}"] = s.max()

        history = pd.concat([history, pd.DataFrame(new_row, index=[future_date])])
        predictions.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "price": y_pred
        })

    # 6. Последние 15 дат из исходного df
    df_real_last_15 = df[["Дата", "Цена"]].iloc[-15:]
    df_real_last_15 = df_real_last_15.rename(columns={"Date": "Дата"})
    df_real_last_15_json = df_real_last_15.to_dict(orient="records")

    return {
        "status": "ok",
        "predictions": predictions,
        "real_price_15_last": df_real_last_15_json,
        "model_type": model_name
    }
