import streamlit as st
import requests
import os

st.title("📈 PostgreSQL + FastAPI + Streamlit")

api_host = os.getenv("API_HOST", "api")

try:
    response = requests.get(f"http://{api_host}:8000/db-check")
    if response.status_code == 200:
        data = response.json()
        if data.get("db_status") == "ok":
            st.success("✅ Connected to PostgreSQL!")
            st.write("Result:", data.get("result"))
        else:
            st.warning("⚠️ DB connection failed.")
            st.write(data)
    else:
        st.error(f"API returned error status: {response.status_code}")
except Exception as e:
    st.error(f"❌ Error contacting FastAPI: {e}")