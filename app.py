# 1. IMPORT PUSTAKA YANG DIBUTUHKAN
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# 2. KONFIGURASI HALAMAN APLIKASI
st.set_page_config(
    page_title="Dashboard Portofolio Kripto",
    page_icon="📈",
    layout="wide"
)

# 3. JUDUL UTAMA APLIKASI
st.title("Dashboard Portofolio Kripto Anda 📈")

# 4. FUNGSI UNTUK MENGAMBIL HARGA TERKINI DARI API
def get_current_prices(coin_ids):
    """Mengambil harga terkini dari daftar ID koin menggunakan API CoinGecko."""
    try:
        ids_string = ','.join(coin_ids)
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd'
        response = requests.get(url)
        response.raise_for_status()  # Error jika request gagal
        price_data = response.json()
        return {key: value['usd'] for key, value in price_data.items()}
    except requests.exceptions.RequestException as e:
        st.error(f"Gagal mengambil data harga dari API: {e}")
        return None

# 5. FITUR UPLOAD FILE
uploaded_file = st.file_uploader("Upload file data transaksi Anda (format .csv)", type=["csv"])

# --- SEMUA PROSES DI BAWAH HANYA AKAN BERJALAN JIKA FILE SUDAH DI-UPLOAD ---
if uploaded_file is not None:
    try:
        # 6. BACA DAN PROSES DATA AWAL
        portfolio_df = pd.read_csv(uploaded_file)
        coin_ids_list = portfolio_df['id_koin'].unique().tolist()
        
        # 7. AMBIL HARGA TERKINI
        current_prices = get_current_prices(coin_ids_list)

        # --- SEMUA KALKULASI DI BAWAH HANYA AKAN BERJALAN JIKA HARGA BERHASIL DIAMBIL ---
        if current_prices:
            # 8. KALKULASI UTAMA (MODAL, NILAI, PNL)
            portfolio_df['harga_terkini_usd'] = portfolio_df['id_koin'].map(current_prices)
            portfolio_df['modal_usd'] = portfolio_df['jumlah'] * portfolio_df['harga_beli_usd']
            portfolio_df['nilai_terkini_usd'] = portfolio_df['jumlah'] * portfolio_df['harga_terkini_usd']
            portfolio_df['pnl_usd'] = portfolio_df['nilai_terkini_usd'] - portfolio_df['modal_usd']
            
            # Membuat 'summary_df' dengan mengelompokkan data
            summary_df = portfolio_df.groupby('id_koin').agg(
                modal_usd=('modal_usd', 'sum'),
                nilai_terkini_usd=('nilai_terkini_usd', 'sum'),
                pnl_usd=('pnl_usd', 'sum')
            ).reset_index()

            # 9. TAMPILKAN RINGKASAN KINERJA (KPI)
            st.header("Ringkasan Kinerja")
            total_modal = summary_df['modal_usd'].sum()
            total_nilai_terkini = summary_df['nilai_terkini_usd'].sum()
            total_pnl = summary_df['pnl_usd'].sum()
            total_pnl_percent = (total_pnl / total_modal) * 100 if total_modal != 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Modal", f"${total_modal:,.2f}")
            col2.metric("Nilai Saat Ini", f"${total_nilai_terkini:,.2f}")
            col3.metric("Total PnL", f"${total_pnl:,.2f}", f"{total_pnl_percent:.2f}%")

            st.markdown("---")

            # 10. TAMPILKAN VISUALISASI DATA (GRAFIK)
            st.header("Analisis Aset")
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                # Membuat Pie Chart
                st.subheader("Komposisi Portofolio")
                fig1, ax1 = plt.subplots()
                ax1.pie(summary_df['nilai_terkini_usd'], labels=summary_df['id_koin'], autopct='%1.1f%%', startangle=90)
                ax1.axis('equal')
                st.pyplot(fig1)

            with col_chart2:
                # Membuat Bar Chart
                st.subheader("Profit & Loss (PnL) per Aset")
                fig2, ax2 = plt.subplots()
                pnl_sorted = summary_df.sort_values('pnl_usd', ascending=False)
                colors = ['#4CAF50' if x >= 0 else '#F44336' for x in pnl_sorted['pnl_usd']]
                ax2.bar(pnl_sorted['id_koin'], pnl_sorted['pnl_usd'], color=colors)
                plt.xticks(rotation=45)
                st.pyplot(fig2)

            # 11. TAMPILKAN TABEL DATA RINCI
            st.header("Data Rinci")
            st.dataframe(summary_df)

    except Exception as e:
        st.error(f"Terjadi error saat memproses file Anda: {e}")
else:
    # Pesan yang akan muncul saat belum ada file yang di-upload
    st.info("Silakan upload file data transaksi Anda untuk memulai analisis.")
