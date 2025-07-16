# pages/1_⬇️_Impor_Data.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Konfigurasi ---
DB_FILE = "master_transactions.csv"
TICKER_TO_ID_MAP = {
    'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin', 'USDT': 'tether',
    'SOL': 'solana', 'XRP': 'ripple', 'ADA': 'cardano', 'DOGE': 'dogecoin',
    'AVAX': 'avalanche-2', 'DOT': 'polkadot', 'MATIC': 'matic-network', 'SHIB': 'shiba-inu',
    'TRX': 'tron', 'LTC': 'litecoin', 'FTM': 'fantom', 'LINK': 'chainlink',
    'NEAR': 'near', 'ATOM': 'cosmos', 'TIA': 'celestia', 'PYTH': 'pyth-network', 'JUP': 'jupiter-aggregator'
}

# --- Fungsi untuk menyimpan data ---
def save_data(df_new):
    if df_new.empty:
        st.warning("Tidak ada data baru untuk disimpan.")
        return
    
    if os.path.exists(DB_FILE):
        df_master = pd.read_csv(DB_FILE, parse_dates=['timestamp'])
        df_combined = pd.concat([df_master, df_new], ignore_index=True)
    else:
        df_combined = df_new
    
    # Standarisasi tipe data sebelum menghapus duplikat
    df_combined['jumlah'] = pd.to_numeric(df_combined['jumlah'])
    df_combined['harga_beli_usd'] = pd.to_numeric(df_combined['harga_beli_usd'])

    # Hapus duplikat berdasarkan semua kolom relevan
    df_combined.drop_duplicates(subset=['timestamp', 'pair', 'tipe_transaksi', 'harga_beli_usd', 'jumlah'], inplace=True)
    df_combined.sort_values(by='timestamp', ascending=False, inplace=True)
    df_combined.to_csv(DB_FILE, index=False)
    st.success(f"{len(df_new)} baris data baru berhasil diproses dan disimpan!")

# --- Fungsi Parser untuk setiap Exchange ---
def parse_binance(df):
    df_std = pd.DataFrame()
   df_std['timestamp'] = pd.to_datetime(df['Date(UTC)'])
    df_std['pair'] = df['Pair']
    df_std['tipe_transaksi'] = df['Side'].str.lower()
    df_std['harga_beli_usd'] = pd.to_numeric(df['Price'])
    df_std['jumlah'] = pd.to_numeric(df['Executed'])
    return df_std

def parse_bitget(df):
    df_std = pd.DataFrame()
    df_std['timestamp'] = pd.to_datetime(df['Date(UTC)'])
    df_std['pair'] = df['symbol']
    df_std['tipe_transaksi'] = df['trade side'].str.lower()
    df_std['harga_beli_usd'] = pd.to_numeric(df['order price'])
    df_std['jumlah'] = pd.to_numeric(df['volume(coin)'])
    return df_std

def parse_bybit(df):
    df_std = pd.DataFrame()
    df_std['timestamp'] = pd.to_datetime(df['orderTime'])
    df_std['pair'] = df['symbol']
    # 'side' di Bybit bisa Buy/Sell
    df_std['tipe_transaksi'] = df['side'].str.lower()
    df_std['harga_beli_usd'] = pd.to_numeric(df['avgPrice'])
    df_std['jumlah'] = pd.to_numeric(df['qty'])
    return df_std
    
def parse_kucoin(df):
    df_std = pd.DataFrame()
    df_std['timestamp'] = pd.to_datetime(df['Waktu order'])
    df_std['pair'] = df['Simbol']
    df_std['tipe_transaksi'] = df['Jual/Beli'].str.lower()
    df_std['harga_beli_usd'] = pd.to_numeric(df['Harga rata-rata'])
    df_std['jumlah'] = pd.to_numeric(df['Jumlah dieksekusi'])
    return df_std

# --- Tampilan Halaman ---
st.title("Impor & Tambah Data Transaksi")

# Membuat TABS untuk setiap sumber data
tab_binance, tab_bitget, tab_bybit, tab_kucoin, tab_manual = st.tabs(["Binance", "Bitget", "Bybit", "Kucoin", "Entri Manual"])

# Kamus parser untuk mempermudah
parsers = {
    "Binance": parse_binance,
    "Bitget": parse_bitget,
    "Bybit": parse_bybit,
    "Kucoin": parse_kucoin
}

# Fungsi untuk membuat UI upload file
def create_upload_ui(exchange_name):
    with st.container(border=True):
        st.subheader(f"Impor dari {exchange_name}")
        uploaded_file = st.file_uploader(f"Upload file CSV {exchange_name}", type="csv", key=f"upload_{exchange_name}")
        if uploaded_file:
            try:
                df_raw = pd.read_csv(uploaded_file)
                st.write("Pratinjau Data Mentah:")
                st.dataframe(df_raw.head())
                if st.button(f"Proses Data {exchange_name}", key=f"btn_{exchange_name}"):
                    # Memanggil parser yang sesuai
                    df_parsed = parsers[exchange_name](df_raw)
                    
                    # Proses standarisasi (sama untuk semua)
                    df_parsed['ticker'] = df_parsed['pair'].apply(lambda x: str(x).split('/')[0].split('USDT')[0].split('BUSD')[0].upper())
                    df_parsed['id_koin'] = df_parsed['ticker'].map(TICKER_TO_ID_MAP)
                    df_parsed.dropna(subset=['id_koin'], inplace=True)
                    
                    save_data(df_parsed[['timestamp', 'pair', 'tipe_transaksi', 'harga_beli_usd', 'jumlah', 'id_koin']])

            except Exception as e:
                st.error(f"Gagal memproses file {exchange_name}: {e}")

# Membuat UI untuk setiap tab
with tab_binance:
    create_upload_ui("Binance")
with tab_bitget:
    create_upload_ui("Bitget")
with tab_bybit:
    create_upload_ui("Bybit")
with tab_kucoin:
    create_upload_ui("Kucoin")

# Tab untuk Entri Manual
with tab_manual:
    with st.form("manual_entry_form"):
        st.subheader("Entri Manual (untuk DEX/Dompet)")
        
        # Menggunakan kolom untuk tata letak yang lebih rapi
        col1, col2 = st.columns(2)
        with col1:
            manual_date = st.date_input("Tanggal Transaksi", value=datetime.now())
            manual_coin = st.selectbox("Pilih Koin", options=list(TICKER_TO_ID_MAP.keys()))
        with col2:
            manual_amount = st.number_input("Jumlah Koin", min_value=0.0, format="%.6f")
            manual_price = st.number_input("Harga Beli per Koin (USD)", min_value=0.0, format="%.6f")
        
        submitted = st.form_submit_button("Simpan Transaksi Manual")
        if submitted:
            if manual_amount > 0 and manual_price > 0:
                manual_id = TICKER_TO_ID_MAP.get(manual_coin, "unknown")
                
                # Buat DataFrame satu baris
                df_manual = pd.DataFrame([{
                    "timestamp": pd.to_datetime(manual_date),
                    "pair": f"{manual_coin}/USD",
                    "tipe_transaksi": "buy",
                    "harga_beli_usd": manual_price,
                    "jumlah": manual_amount,
                    "id_koin": manual_id
                }])
                
                save_data(df_manual)
            else:
                st.warning("Jumlah dan Harga harus lebih besar dari nol.")
