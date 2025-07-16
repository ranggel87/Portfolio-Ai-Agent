import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# Judul utama aplikasi
st.title("Dashboard Portofolio Kripto 📈")

# Widget untuk mengunggah file
uploaded_file = st.file_uploader("Pilih file data transaksi CSV Anda", type="csv")

# Semua proses hanya berjalan jika file sudah berhasil diunggah
if uploaded_file is not None:
    try:
        # --- Proses Data ---
        # Baca file CSV yang diunggah
        portfolio_df = pd.read_csv(uploaded_file)

        # Ambil daftar ID koin yang unik
        coin_ids_list = portfolio_df['id_koin'].unique().tolist()
        
        # Ambil harga terkini dari API
        ids_string = ','.join(coin_ids_list)
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd'
        response = requests.get(url)
        price_data = response.json()
        current_prices = {key: value['usd'] for key, value in price_data.items()}

        # --- Kalkulasi ---
        portfolio_df['harga_terkini_usd'] = portfolio_df['id_koin'].map(current_prices)
        portfolio_df['modal_usd'] = portfolio_df['jumlah'] * portfolio_df['harga_beli_usd']
        portfolio_df['nilai_terkini_usd'] = portfolio_df['jumlah'] * portfolio_df['harga_terkini_usd']
        portfolio_df['pnl_usd'] = portfolio_df['nilai_terkini_usd'] - portfolio_df['modal_usd']
        
        # Buat tabel ringkasan
        summary_df = portfolio_df.groupby('id_koin').agg(
            modal_usd=('modal_usd', 'sum'),
            nilai_terkini_usd=('nilai_terkini_usd', 'sum'),
            pnl_usd=('pnl_usd', 'sum')
        ).reset_index()

        # --- Tampilkan Dashboard ---
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

        st.header("Analisis Aset")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("Komposisi Portofolio")
            fig1, ax1 = plt.subplots()
            ax1.pie(summary_df['nilai_terkini_usd'], labels=summary_df['id_koin'], autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')
            st.pyplot(fig1)

        with col_chart2:
            st.subheader("Profit & Loss (PnL) per Aset")
            fig2, ax2 = plt.subplots()
            pnl_sorted = summary_df.sort_values('pnl_usd', ascending=False)
            colors = ['#4CAF50' if x >= 0 else '#F44336' for x in pnl_sorted['pnl_usd']]
            ax2.bar(pnl_sorted['id_koin'], pnl_sorted['pnl_usd'], color=colors)
            plt.xticks(rotation=45)
            st.pyplot(fig2)

        st.header("Data Rinci")
        st.dataframe(summary_df)

    except Exception as e:
        st.error(f"Terjadi error saat memproses file. Pastikan format file dan nama kolom sudah benar. Error: {e}")
else:
    st.info("Silakan upload file CSV Anda untuk memulai.")
