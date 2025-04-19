import streamlit as st
import requests

st.set_page_config(page_title="Финансовая панель", layout="wide")

# Боковая панель с навигацией
page = st.sidebar.selectbox("Выберите раздел", ["📊 Главная", "📤 Загрузка в БД"])

if page == "📊 Главная":
    st.title("📈 Добро пожаловать в Streamlit-дэшборд")
    st.write("Здесь будет основная аналитика, графики и так далее.")

elif page == "📤 Загрузка в БД":
    st.title("📤 Загрузка CSV-файла в базу данных")

    asset = st.selectbox("Выберите актив", ["Криптовалюты", "Нефтеные фьючерсы", "Акции метталургических компаний", "Акции нефтедобывающих компаний", "Спотовы цена на драгоценные металы"])
    uploaded_file = st.file_uploader("Загрузите CSV-файл", type=["csv"])

    if uploaded_file is not None:
        df_preview = uploaded_file.getvalue().decode("utf-8")
        # st.subheader("📄 Предпросмотр данных:")
        # st.dataframe(df_preview)

    if st.button("Загрузить в базу"):
        if uploaded_file is not None:
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                data = {"asset": asset}
                response = requests.post("http://api:8000/upload-csv", files=files, data=data)

                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ CSV загружен в базу данных!")
                    st.write("Загружено строк:", result.get("rows"))
                    st.write("Типы данных:", result.get("dtypes"))
                else:
                    st.error(f"❌ Ошибка: {response.status_code}")
                    st.text(response.text)
            except Exception as e:
                st.error(f"Ошибка при обращении к API: {e}")
        else:
            st.warning("⚠️ Сначала загрузите файл")

        