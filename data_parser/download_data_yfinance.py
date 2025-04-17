import yfinance as yf
import pandas as pd

# Список тикеров Yahoo и названия файлов
companies = {
    "0358.HK": "jiangxi_copper_hk.csv",      # Jiangxi Copper (Hong Kong)
    "600019.SS": "baoshan_iron_sh.csv",      # Baoshan Iron & Steel (Shanghai)
    "0857.HK": "petrochina_hk.csv",          # PetroChina (Hong Kong)
    "EQNR.OL": "equinor_oslo.csv",           # Equinor ASA (Oslo)
}

start_date = "2016-01-01"
end_date = pd.Timestamp.today().strftime('%Y-%m-%d')

# Загрузка и сохранение в CSV
for ticker, filename in companies.items():
    print(f"Загружаю: {ticker}")
    data = yf.download(ticker, start=start_date, end=end_date, interval="1d")
    
    # Убираем multiindex, если он есть
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join(col).strip() for col in data.columns.values]

    # Сохраняем с обычным индексом (датой)
    data.reset_index(inplace=True)
    data.to_csv(filename, index=False)

    print(f"Сохранено в: {filename}\n")