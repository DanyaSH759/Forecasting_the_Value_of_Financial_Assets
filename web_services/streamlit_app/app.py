import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ВЫЗЫВАЕМ СРАЗУ
st.set_page_config(page_title="Финансовая панель", layout="wide")

# ---------------------------
# Состояния
# ---------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.current_user = None

# ---------------------------
# Формы логина и регистрации
# ---------------------------
def login_form():
    with st.form("login_form"):
        st.subheader("🔐 Вход")
        username = st.text_input("Логин")
        password = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button("Войти")
        if submitted:
            response = requests.post("http://api:8000/login/login", json={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                st.session_state.authenticated = True
                st.session_state.current_user = username
                st.success(f"Добро пожаловать, {username}!")
                st.rerun()
            else:
                st.error("Неверный логин или пароль")

def register_form():
    with st.form("register_form"):
        st.subheader("📝 Регистрация")
        username = st.text_input("Новый логин")
        password = st.text_input("Новый пароль", type="password")
        submitted = st.form_submit_button("Зарегистрироваться")
        if submitted:
            response = requests.post("http://api:8000/register/register", json={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                st.success("Успешно! Теперь вы можете войти.")
            else:
                st.error("Ошибка регистрации. Возможно, логин уже занят.")

# ---------------------------
# Навигация
# ---------------------------
page = st.sidebar.selectbox(
    "Выберите раздел",
    ["Прогноз стоимости активов", "Прогноз по своему датасету"]
)

# ---------------------------
# Раздел 1 — Прогноз стоимости активов
# ---------------------------
if page == "Прогноз стоимости активов":
    st.title("📈 Прогнозирование стоимости активов")

    schema = st.selectbox("Категория", [
        "Нефтеные фьючерсы", "Акции метталургических компаний",
        "Акции нефтедобывающих компаний", "Спотовы цена на драгоценные металы", "Криптовалюты"
    ])
    if schema == "Криптовалюты":
        schema = "crypto"
        asset = st.selectbox("Актив", ["Bitcoin", "Ethereum"])
    elif schema == "Нефтеные фьючерсы":
        schema = "oil_futures"
        asset = st.selectbox("Актив", ["Brent", "WTI"])
    elif schema == "Акции метталургических компаний":
        schema = "metals_share"
        asset = st.selectbox("Актив", ["Baoshan iron", "Jiangxi copper"])
    elif schema == "Акции нефтедобывающих компаний":
        schema = "oil_share"
        asset = st.selectbox("Актив", ["Equinor Oslo", "Petrochina HK"])
    elif schema == "Спотовы цена на драгоценные металы":
        schema = "base_metals"
        asset = st.selectbox("Актив", ["Gold", "Silver"])

    if st.button("Сделать прогноз"):
        with st.spinner("Обработка..."):
            try:
                response = requests.post("http://api:8000/predict", json={
                    "schema": schema, "asset_name": asset
                })
                if response.status_code == 200:
                    data = response.json()
                    df_pred = pd.DataFrame(data["predictions"])
                    df_pred["date"] = pd.to_datetime(df_pred["date"])
                    df_pred = df_pred.set_index("date")
                    df_pred = df_pred.rename(columns={"price": "Цена"})

                    df_real = pd.DataFrame(data["real_price_15_last"])
                    df_real["date"] = pd.to_datetime(df_real["Дата"])
                    df_real = df_real.set_index("date")[["Цена"]]

                    combined = pd.concat([df_real, df_pred])

                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.plot(df_real.index, df_real["Цена"], label="Факт", marker="o")
                    ax.plot(df_pred.index, df_pred["Цена"], label="Прогноз", linestyle="--", marker="o")
                    ax.plot(combined.index, combined["Цена"], color="black", alpha=0.2)

                    all_prices = combined["Цена"]
                    y_min, y_max = all_prices.min(), all_prices.max()
                    padding = (y_max - y_min) * 0.1
                    ax.set_ylim(y_min - padding, y_max + padding)

                    ax.set_title(f"Прогноз: {asset}", fontsize=18)
                    ax.set_xlabel("Дата")
                    ax.set_ylabel("Цена")
                    ax.legend()
                    ax.grid(True)
                    st.pyplot(fig)

                    def get_recommendation(prices: pd.Series) -> str:
                        y = prices.values
                        x = np.arange(len(y))
                        slope, _ = np.polyfit(x, y, 1)
                        threshold = 0.0005 * y.mean()
                        if slope > threshold:
                            return "📈 **Рекомендуется покупать**"
                        elif slope < -threshold:
                            return "📉 **Рекомендуется продавать**"
                        return "🔍 **Рекомендуется держать**"

                    st.subheader("💡 Рекомендация:")
                    st.markdown(get_recommendation(combined["Цена"].tail(10)))
                else:
                    st.error(f"Ошибка API: {response.text}")
            except Exception as e:
                st.error(f"Ошибка обработки: {e}")

# ---------------------------
# Раздел 2 — Пользовательский CSV
# ---------------------------
elif page == "Прогноз по своему датасету":
    st.title("📊 Ваш персональный прогноз")

    if not st.session_state.authenticated:
        action = st.radio("Авторизация", ["Войти", "Зарегистрироваться"])
        if action == "Войти":
            login_form()
        else:
            register_form()
    else:
        st.success(f"Вы вошли как **{st.session_state.current_user}**")
        if st.button("Выйти"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()


        st.subheader("Загрузка пользовательского датасета")
        uploaded_file = st.file_uploader("Загрузите CSV-файл с историческими ценами", type=["csv"])

        with st.expander("📄 Требования к CSV-файлу и пример"):
            st.markdown("""
            Для корректной загрузки данных ваш CSV-файл должен содержать **следующие колонки, обычно полачаемы при скачивания датасета с yfinance**:

            - `Date` — дата в формате `YYYY-MM-DD`
            - `Close_xxx.xx` — цена закрытия (обязательна)
            - `High_xxx.xx` — максимальная цена
            - `Low_xxx.xx` —  минимальная цена
            - `Open_xxx.xx` — цена открытия
            - `Volume_xxx.xx` — шум торгов
            
            👉 Датафрейм должен содержать **не менее 200 строк** для построения прогноза.
            """)

            # Пример данных
            example_data = pd.DataFrame({
                "Date": pd.date_range(end=pd.Timestamp.today(), periods=5).strftime("%Y-%m-%d"),
                "Close_0857.HK": [100.5, 101.2, 102.8, 103.4, 104.1],
                "Open_0857.HK": [100.0, 100.8, 101.5, 103.0, 103.9],
                "High_0857.HK": [101.0, 102.0, 103.0, 104.0, 105.0],
                "Low_0857.HK": [99.5, 100.5, 101.0, 102.5, 103.2],
            })

            st.dataframe(example_data)

            # Кнопка для скачивания CSV
            csv = example_data.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Скачать пример CSV",
                data=csv,
                file_name="example_data.csv",
                mime="text/csv"
            )

        if uploaded_file:
            try:
                if st.button("Сделать прогноз по вашему датасету"):
                    with st.spinner("Считаем..."):

                        # Отправляем CSV в API
                        response = requests.post(
                        "http://api:8000/custom_predict/custom_predict",
                        files={"file": uploaded_file.getvalue()}
                        )

                        if response.status_code == 200:
                            data = response.json()
                        if data.get("status") != "ok":
                            st.warning(f"⚠️ Ошибка: {data.get('detail')}")
                        else:
                            # Парсим данные
                            preds = pd.DataFrame(data["predictions"])
                            preds["date"] = pd.to_datetime(preds["date"])
                            preds = preds.set_index("date")

                            real = pd.DataFrame(data["real_price_15_last"])
                            real["date"] = pd.to_datetime(real["Дата"])
                            real = real.set_index("date")
                            real = real[["Цена"]]

                            # Объединяем
                            combined = pd.concat([real, preds.rename(columns={"price": "Цена"})])

                            # График
                            st.subheader("📉 Прогноз + последние реальные данные")
                            fig, ax = plt.subplots(figsize=(12, 6))
                            ax.plot(real.index, real["Цена"], label="Последние 15 дней", marker="o", color="blue")
                            ax.plot(preds.index, preds["price"], label="Прогноз на 15 дней", marker="o", color="orange")
                            ax.plot(combined.index, combined["Цена"], alpha=0.3, color="gray")

                            ax.set_title("График прогноза", fontsize=16)
                            ax.set_xlabel("Дата")
                            ax.set_ylabel("Цена")
                            ax.legend()
                            ax.grid(True)
                            st.pyplot(fig)

                            # Модель
                            model_type = data.get("model_type", "Неизвестна")
                            st.success(f"Использованная модель: **{model_type}**")

                            def get_recommendation(prices: pd.Series) -> str:
                                y = prices.values
                                x = np.arange(len(y))
                                slope, _ = np.polyfit(x, y, 1)
                                threshold = 0.0005 * y.mean()
                                if slope > threshold:
                                    return "📈 **Рекомендуется покупать**"
                                elif slope < -threshold:
                                    return "📉 **Рекомендуется продавать**"
                                return "🔍 **Рекомендуется держать**"

                            st.subheader("💡 Рекомендация:")
                            st.markdown(get_recommendation(combined["Цена"].tail(10)))


                else:
                    pass

            except Exception as e:
                st.error(f"❌ Ошибка при обращении к API: {e}")