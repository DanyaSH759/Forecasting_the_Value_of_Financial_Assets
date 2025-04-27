import pandas as pd
import numpy as np

def split_data(data, train_ratio=0.85, val_ratio=0.1, test_ratio=0.05, validation=True):
    data = data.sort_index()
    if validation:
        n = len(data)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train = data.iloc[:train_end]
        val = data.iloc[train_end:val_end]
        test = data.iloc[val_end:]

        return train, val, test
    else:
        train_ratio = 0.9
        n = len(data)
        train_end = int(n * train_ratio)

        train = data.iloc[:train_end]
        test = data.iloc[train_end:]

        return train, test

def return_x_y(data):
    x = data.drop(["Цена", "Откр.", "Макс.", "Мин."], axis=1)
    y = data["Цена"]
    return x, y

def clean_ohlcv_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    close_col = [col for col in df.columns if col.startswith('Close_')]
    if not close_col:
        raise ValueError("Не найдена колонка с Close_")
    ticker = close_col[0].split('_')[1]

    rename_map = {
        f'Date': 'Дата',
        f'Close_{ticker}': 'Цена',
        f'Open_{ticker}': 'Откр.',
        f'High_{ticker}': 'Макс.',
        f'Low_{ticker}': 'Мин.',
        f'Volume_{ticker}': 'Объём',
    }
    df = df.rename(columns=rename_map)
    df['Изм. %'] = df['Цена'].pct_change() * 100
    desired_order = ['Дата', 'Цена', 'Откр.', 'Макс.', 'Мин.', 'Объём', 'Изм. %']
    df = df[desired_order]
    return df

def transform_data(data):
    from .preprocessing import clean_ohlcv_dataframe, upgrade_dataset

    rename_map = { 'Date': 'Дата' }
    data = data.rename(columns=rename_map)
    if "Дата" not in data.columns:
        data = clean_ohlcv_dataframe(data)

    data = data.copy()
    if data.columns.duplicated().any():
        data = data.loc[:, ~data.columns.duplicated()]
    data["Дата"] = pd.to_datetime(data["Дата"], format='mixed', dayfirst=True, errors='coerce')

    if "Дата" in data.columns:
        data = data.sort_values("Дата").set_index("Дата")

    for col in ["Цена", "Откр.", "Макс.", "Мин."]:
        if data[col].dtype == object or data[col].dtype.name == 'string':
            data[col] = data[col].str.replace(".", "", regex=False).str.replace(",", ".").astype(float)
        else:
            data[col] = data[col].astype(float)

    data = data.drop(columns=["Объём", "Изм. %"], errors='ignore')
    data = data.drop_duplicates()
    data = upgrade_dataset(data)
    return data

def upgrade_dataset(data, mode="train"):
    data = data.copy()
    data["День недели"] = data.index.dayofweek
    data["День"] = data.index.day
    data["Месяц"] = data.index.month
    data["Год"] = data.index.year

    for lag in [5, 15, 30]:
        data[f"lag_{lag}_t"] = data["Цена"].shift(lag)
        data[f"lag_{lag}_open"] = data["Откр."].shift(lag)
        data[f"lag_{lag}_max"] = data["Макс."].shift(lag)
        data[f"lag_{lag}_min"] = data["Мин."].shift(lag)

    if mode == "train":
        price = data["Цена"]
        open_ = data["Откр."]
        high = data["Макс."]
        low = data["Мин."]
    else:
        price = data["lag_5_t"]
        open_ = data["lag_5_open"]
        high = data["lag_5_max"]
        low = data["lag_5_min"]

    for diff, label in zip([1, 5], ["5", "15"]):
        data[f"diff_{label}_t"] = price.diff(diff).shift(1)
        data[f"diff_{label}_open"] = open_.diff(diff).shift(1)
        data[f"diff_{label}_max"] = high.diff(diff).shift(1)
        data[f"diff_{label}_min"] = low.diff(diff).shift(1)

    for window in [5, 15]:
        for name, col in zip(["", "_open", "_max", "_min"], [price, open_, high, low]):
            data[f"rol_std_{window}{name}"] = col.rolling(window=window).std().shift(1)
            data[f"rol_min_{window}{name}"] = col.rolling(window=window).min().shift(1)
            data[f"rol_max_{window}{name}"] = col.rolling(window=window).max().shift(1)

    data = data.dropna()
    return data
