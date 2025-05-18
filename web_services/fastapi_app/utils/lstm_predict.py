import torch
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader
from utils.dataset_transform import transform_data, upgrade_dataset, return_x_y
from utils.lstm_models import SlidingWindowDataset, TunedLSTM

def make_lstm_prediction(df: pd.DataFrame, model_path: str, forecast_horizon=15):
    df_ready = transform_data(df)
    df_ready = upgrade_dataset(df_ready)
    X_all, y_all = return_x_y(df_ready)

    scaler_X = StandardScaler()
    scaler_y = StandardScaler()

    X_scaled = pd.DataFrame(scaler_X.fit_transform(X_all), columns=X_all.columns)
    y_scaled = pd.Series(scaler_y.fit_transform(y_all.values.reshape(-1, 1)).flatten())

    seq_len = 15  # такой же как при обучении!
    dataset = SlidingWindowDataset(X_scaled, y_scaled, seq_len=seq_len)
    loader = DataLoader(dataset, batch_size=1, shuffle=False)

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    model.eval()
    predictions = []
    with torch.no_grad():
        last_seq = X_scaled.iloc[-seq_len:].values
        for _ in range(forecast_horizon):
            input_tensor = torch.tensor(last_seq.reshape(1, seq_len, -1), dtype=torch.float32)
            pred = model(input_tensor).item()
            pred_original = scaler_y.inverse_transform(np.array([[pred]])).flatten()[0]
            predictions.append(pred_original)

            # обновляем last_seq для следующего дня
            next_features = last_seq[1:]
            next_row = last_seq[-1].copy()
            next_row[0] = pred  # обновим целевую цену
            last_seq = np.vstack([next_features, next_row])

    future_dates = pd.date_range(df_ready.index.max() + pd.Timedelta(days=1), periods=forecast_horizon)
    return [{"date": str(d.date()), "price": p} for d, p in zip(future_dates, predictions)]
