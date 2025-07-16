# pages/2_📄_Semua_Transaksi.py
import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="Semua Transaksi")
st.title("Database Semua Transaksi 🗃️")
st.write("Berikut adalah gabungan semua data transaksi Anda yang telah distandarisasi.")

DB_FILE = "master_transactions.csv"

if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE)
    st.dataframe(df)
    
    # Opsi untuk mengunduh database
    st.download_button(
        label="Unduh Semua Data sebagai CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='my_crypto_transactions.csv',
        mime='text/csv',
    )
else:
    st.info("Database masih kosong. Silakan impor data terlebih dahulu di halaman 'Impor Data'.")
