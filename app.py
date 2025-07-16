# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(layout="wide", page_title="Dashboard Utama")
st.title("Dashboard Portofolio Kripto 📈")

# --- Database Transaksi ---
DB_FILE = "master_transactions.csv"

# --- Fungsi untuk memuat data dari database ---
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, parse_dates=['timestamp'])
    return None

# --- Fungsi untuk mengambil harga terkini (tidak berubah) ---
def get_current_prices(coin_ids):
    if not coin_ids:
        return {}
    try:
        ids_string = ','.join(coin_ids)
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd'
        response = requests.get(url)
        response.raise_for_status()
        price_data = response.json()
        return {key: value['usd'] for key, value in price_data.items()}
    except Exception:
        return {}

# --- Logika Utama Dashboard ---
df = load_data()

if df is not None and not df.empty:
    st.header("Ringkasan Kinerja")
    
    # Ambil harga terkini untuk semua koin di portofolio
    all_coin_ids = df['id_koin'].unique().tolist()
    current_prices = get_current_prices(all_coin_ids)

    if not current_prices:
        st.error("Gagal mengambil data harga terkini dari API. Dashboard tidak dapat ditampilkan.")
    else:
        # Hanya proses transaksi 'buy' untuk kalkulasi modal dan PnL
        buy_df = df[df['tipe_transaksi'] == 'buy'].copy()
        
        buy_df['harga_terkini_usd'] = buy_df['id_koin'].map(current_prices)
        buy_df['modal_usd'] = buy_df['jumlah'] * buy_df['harga_beli_usd']
        buy_df['nilai_terkini_usd'] = buy_df['jumlah'] * buy_df['harga_terkini_usd']
        buy_df['pnl_usd'] = buy_df['nilai_terkini_usd'] - buy_df['modal_usd']

        summary_df = buy_df.groupby('id_koin').agg(
            modal_usd=('modal_usd', 'sum'),
            nilai_terkini_usd=('nilai_terkini_usd', 'sum'),
            pnl_usd=('pnl_usd', 'sum')
        ).reset_index()

        total_modal = summary_df['modal_usd'].sum()
        total_nilai_terkini = summary_df['nilai_terkini_usd'].sum()
        total_pnl = summary_df['pnl_usd'].sum()
        total_pnl_percent = (total_pnl / total_modal) * 100 if total_modal != 0 else 0

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Modal", f"${total_modal:,.2f}")
        kpi2.metric("Nilai Saat Ini", f"${total_nilai_terkini:,.2f}")
        kpi3.metric("Total PnL", f"${total_pnl:,.2f}", f"{total_pnl_percent:.2f}%")
        
        st.markdown("---")
        st.header("Analisis Aset")
        
        chart1, chart2 = st.columns(2)
        with chart1:
            st.subheader("Komposisi Portofolio")
            fig1, ax1 = plt.subplots()
            ax1.pie(summary_df['nilai_terkini_usd'], labels=summary_df['id_koin'], autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')
            st.pyplot(fig1)

        with chart2:
            st.subheader("PnL per Aset")
            fig2, ax2 = plt.subplots()
            pnl_sorted = summary_df.sort_values('pnl_usd', ascending=False)
            colors = ['#4CAF50' if x >= 0 else '#F44336' for x in pnl_sorted['pnl_usd']]
            ax2.bar(pnl_sorted['id_koin'], pnl_sorted['pnl_usd'], color=colors)
            plt.xticks(rotation=45)
            st.pyplot(fig2)
else:
    st.info("👋 Selamat Datang! Belum ada data transaksi. Silakan pergi ke halaman 'Impor Data' untuk memulai.")
