import pandas as pd


def clean_ohlcv_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Найти тикер по колонке Close_*
    close_col = [col for col in df.columns if col.startswith('Close_')]
    if not close_col:
        raise ValueError("Не найдена колонка с Close_")
    ticker = close_col[0].split('_')[1]  # получаем "0358.HK" и т.п.

    # Переименование колонок
    rename_map = {
        f'Date': 'Дата',
        f'Close_{ticker}': 'Цена',
        f'Open_{ticker}': 'Откр.',
        f'High_{ticker}': 'Макс.',
        f'Low_{ticker}': 'Мин.',
        f'Volume_{ticker}': 'Объём',
    }
    df = df.rename(columns=rename_map)

    # Добавим колонку "Изм. %"
    df['Изм. %'] = df['Цена'].pct_change() * 100

    # Упорядочим колонки
    desired_order = ['Дата', 'Цена', 'Откр.', 'Макс.', 'Мин.', 'Объём', 'Изм. %']
    df = df[desired_order]

    return df


def transform_data(data):
    '''Фнукция для трансформации текстовых строчек в числовые'''
    # Унификация неймингов датасетов
    if "Дата" not in [x for x in data.columns]: data = clean_ohlcv_dataframe(data)
    
    # перевод даты в индексы датасета
    data["Дата"] = pd.to_datetime(data["Дата"], format='mixed', dayfirst=True, errors='coerce')
    data = data.sort_values("Дата").set_index("Дата")

    # меняем тип данных и удаляем заранее известные не информативные колонки
    for col in ["Цена", "Откр.", "Макс.", "Мин."]:
        if data[col].dtype == object or data[col].dtype.name == 'string':
            data[col] = data[col].str.replace(".", "", regex=False).str.replace(",", ".").astype(float)
        else:
            # если уже число — ничего не делаем
            data[col] = data[col].astype(float)

    data = data.drop(columns=["Объём", "Изм. %"], errors='ignore')

    #доп проверка на пустые строчки
    try:
        data.isnull().sum().sum() == 0
    except:
        print("В данных есть пустые значения!")

    data = data.drop_duplicates()

    # создаём новые фичи
    # data = upgrade_dataset(data)
    
    return data

def upgrade_dataset(data, mode="train"):
    data = data.copy()

    # Фичи по дате
    data["День недели"] = data.index.dayofweek
    data["День"] = data.index.day
    data["Месяц"] = data.index.month
    data["Год"] = data.index.year

    # --- 1. Лаги (всегда по сырым данным)
    for lag in [5, 15, 30]:
        data[f"lag_{lag}_t"] = data["Цена"].shift(lag)
        data[f"lag_{lag}_open"] = data["Откр."].shift(lag)
        data[f"lag_{lag}_max"] = data["Макс."].shift(lag)
        data[f"lag_{lag}_min"] = data["Мин."].shift(lag)

    # data.to_csv("data_valid_with_tail.csv", index=True)

    # --- 2. Производные фичи
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

    # Диффы
    for diff, label in zip([1, 5], ["5", "15"]):
        data[f"diff_{label}_t"] = price.diff(diff).shift(1)
        data[f"diff_{label}_open"] = open_.diff(diff).shift(1)
        data[f"diff_{label}_max"] = high.diff(diff).shift(1)
        data[f"diff_{label}_min"] = low.diff(diff).shift(1)

    # Роллинги
    for window in [5, 15]:
        for name, col in zip(["", "_open", "_max", "_min"], [price, open_, high, low]):
            data[f"rol_std_{window}{name}"] = col.rolling(window=window).std().shift(1)
            data[f"rol_min_{window}{name}"] = col.rolling(window=window).min().shift(1)
            data[f"rol_max_{window}{name}"] = col.rolling(window=window).max().shift(1)

    data = data.dropna()
    return data
