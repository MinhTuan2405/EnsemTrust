import streamlit as st
import trino
import pandas as pd
import os

# Lấy thông tin kết nối từ biến môi trường (an toàn)
TRINO_HOST = os.environ.get("TRINO_HOST", "trino")
TRINO_USER = os.environ.get("TRINO_USER", "trino")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "admin")
POSTGRES_PASS = os.environ.get("POSTGRES_PASSWORD", "admin")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "dagster_db")

st.set_page_config(layout="wide")
st.title("My Data Stack Dashboard 🚀")

st.header("Query Trino (Delta Lake / Hive)")

try:
    # Kết nối tới Trino
    conn = trino.dbapi.connect(
        host=TRINO_HOST,
        port=8080, # Port nội bộ của Trino
        user=TRINO_USER,
        catalog='delta', # Catalog bạn đã tạo
        schema='gold'    # Schema bạn đã tạo
    )
    
    st.success(f"Connected to Trino at {TRINO_HOST}!")

    # Ví dụ query
    query = st.text_area("Trino Query:", "SELECT * FROM delta.gold.my_first_delta_table LIMIT 10")
    
    if st.button("Run Trino Query"):
        df = pd.read_sql(query, conn)
        st.dataframe(df)

except Exception as e:
    st.error(f"Error connecting to Trino: {e}")

st.header("Query Postgres (Dagster DB)")

try:
    # Kết nối tới Postgres (ví dụ: xem run metadata của Dagster)
    from sqlalchemy import create_engine
    engine = create_engine(f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:5432/{POSTGRES_DB}")
    
    query_pg = st.text_area("Postgres Query:", "SELECT * FROM dagster.runs LIMIT 5")

    if st.button("Run Postgres Query"):
        df_pg = pd.read_sql(query_pg, engine)
        st.dataframe(df_pg)

except Exception as e:
    st.error(f"Error connecting to Postgres: {e}")