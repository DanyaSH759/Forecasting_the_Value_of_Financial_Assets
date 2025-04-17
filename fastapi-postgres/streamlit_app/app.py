import streamlit as st
import pandas as pd
import psycopg2

st.title("📈 PostgreSQL + Streamlit")

try:
    conn = psycopg2.connect(
        host="db",
        database="mydb",
        user="myuser",
        password="mypassword"
    )
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cur.fetchall()
    st.success("Connected to PostgreSQL!")
    st.write("Tables in DB:", tables)
    conn.close()
except Exception as e:
    st.error(f"Database error: {e}")
