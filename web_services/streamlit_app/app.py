import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Финансовая панель", layout="wide")

# Боковая панель с навигацией
page = st.sidebar.selectbox("Выберите раздел", ["Главная", "Прогноз стоимости активов"])


if page == "Главная":
    st.title("📈 Добро пожаловать в Streamlit-дэшборд")
    st.write("Здесь будет основная информация о проекте")

elif page == "Прогноз стоимости активов":
    st.title("Прогнозирование стоимости финансовых активов")

    schema = st.selectbox("Выберите ", ["Криптовалюты", "Нефтеные фьючерсы", "Акции метталургических компаний", "Акции нефтедобывающих компаний", "Спотовы цена на драгоценные металы"])
    if schema == "Криптовалюты":
        schema = "crypto"
        asset = st.selectbox("Выберите", ["bitcoin", "ethereum"])
    if schema == "Нефтеные фьючерсы":
        schema = "oil_futures"
        asset = st.selectbox("Выберите", ["brent_futures", "wti_futures"])
    if schema == "Акции метталургических компаний":
        schema = "metals_share"
        asset = st.selectbox("Выберите", ["baoshan_iron", "jiangxi_copper"])
    if schema == "Акции нефтедобывающих компаний":
        schema = "oil_share"
        asset = st.selectbox("Выберите", ["equinor", "petrochina"])
    if schema == "Спотовы цена на драгоценные металы":
        schema = "base_metals"
        asset = st.selectbox("Выберите", ["gold", "silver"])

    if st.button("Сделать прогноз"):
        with st.spinner("Считаем..."):
            response = requests.post(
                "http://api:8000/predict",
                json={"schema": schema,
                    "asset_name": asset}
            )

            try:
                if response.status_code == 200:
                    data = response.json()  # <--- читаем один раз!

                    predictions = data["predictions"]
                    df_pred = pd.DataFrame(predictions)
                    df_pred["date"] = pd.to_datetime(df_pred["date"])
                    df_pred = df_pred.set_index("date")

                    last_15_price = pd.DataFrame(data["real_price_15_last"])  # <--- читаем из data
                    last_15_price["date"] = pd.to_datetime(last_15_price["Дата"])
                    last_15_price = last_15_price.set_index("date")
                    last_15_price = last_15_price[["Цена"]]

                    # Объединяем реальные и прогнозные данные
                    df_pred = df_pred.rename(columns={"price": "Цена"})
                    combined = pd.concat([last_15_price, df_pred])

                    # Строим график
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.plot(last_15_price.index, last_15_price["Цена"], label="Цена за прошедшие 15 дней", color="blue", marker="o")
                    ax.plot(df_pred.index, df_pred["Цена"], label="Прогноз на 15 дней", color="orange", linestyle="--", marker="o")
                    ax.plot(combined.index, combined["Цена"], color="black", alpha=0.2)

                    ax.set_title(f"Прогноз стоимости актива: {asset}", fontsize=18)
                    ax.set_xlabel("Дата", fontsize=14)
                    ax.set_ylabel("Цена", fontsize=14)
                    ax.legend()
                    ax.grid(True)

                    st.pyplot(fig)

                else:
                    st.error(f"Ошибка от API: {response.text}")

            except Exception as e:
                st.error(f"Ошибка при обработке данных: {e}")