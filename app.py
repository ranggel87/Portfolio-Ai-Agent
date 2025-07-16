import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# --- BAGIAN BARU: KAMUS PENERJEMAH ---
# Menerjemahkan Ticker dari Exchange ke ID CoinGecko
# Anda bisa menambahkan koin lain di sini jika diperlukan
TICKER_TO_ID_MAP = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'BNB': 'binancecoin',
    'USDT': 'tether',
    'SOL': 'solana',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'DOGE': 'dogecoin',
    # Tambahkan koin lain di sini, contoh: 'MATIC': 'matic-network'
}

st.set_page_config(layout="wide")
st.title("Dashboard Portofolio Universal 🔮")
st.write("Didesain untuk membaca berbagai format file CSV dari Binance, Bitget, dll.")

uploaded_file = st.file_uploader("Pilih file data transaksi CSV dari exchange manapun", type="csv")

if uploaded_file is not None:
    try:
        df_raw = pd.read_csv(uploaded_file)
        
        st.header("Langkah 1: Pratinjau & Pemetaan Kolom")
        st.write("Ini adalah 5 baris pertama dari data mentah Anda:")
        st.dataframe(df_raw.head())
        
        column_headers = df_raw.columns.tolist()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_coin_col = st.selectbox("Pilih kolom NAMA KOIN (contoh: 'BTC/USDT' atau 'BTC'):", column_headers)
        with col2:
            selected_jumlah_col = st.selectbox("Pilih kolom JUMLAH KOIN:", column_headers)
        with col3:
            selected_harga_col = st.selectbox("Pilih kolom HARGA BELI per koin:", column_headers)

        if st.button("Proses Data"):
            # --- BAGIAN BARU: Pembersihan dan Standarisasi Data ---
            st.header("Langkah 2: Hasil Proses & Dashboard")
            
            # 1. Buat DataFrame awal berdasarkan pemetaan pengguna
            df_mapped = pd.DataFrame({
                'pair': df_raw[selected_coin_col],
                'jumlah': df_raw[selected_jumlah_col],
                'harga_beli_usd': df_raw[selected_harga_col]
            })

            # 2. Ekstrak Ticker (mengambil 'BTC' dari 'BTC/USDT' atau 'BTCBUSD')
            df_mapped['ticker'] = df_mapped['pair'].apply(lambda x: str(x).split('/')[0].split('USDT')[0].split('BUSD')[0].upper())

            # 3. Terjemahkan Ticker ke ID CoinGecko menggunakan kamus
            df_mapped['id_koin'] = df_mapped['ticker'].map(TICKER_TO_ID_MAP)

            # 4. Bersihkan data: hapus baris yang koinnya tidak ada di kamus
            original_rows = len(df_mapped)
            df_mapped.dropna(subset=['id_koin'], inplace=True)
            cleaned_rows = len(df_mapped)
            if original_rows > cleaned_rows:
                st.warning(f"{original_rows - cleaned_rows} baris transaksi dihapus karena koinnya tidak ada dalam kamus penerjemah.")

            # 5. Konversi kolom angka, paksa error menjadi data kosong (NaN) lalu hapus
            df_mapped['jumlah'] = pd.to_numeric(df_mapped['jumlah'], errors='coerce')
            df_mapped['harga_beli_usd'] = pd.to_numeric(df_mapped['harga_beli_usd'], errors='coerce')
            df_mapped.dropna(subset=['jumlah', 'harga_beli_usd'], inplace=True)
            
            # --- Sisa skrip kalkulasi dan visualisasi (tidak berubah) ---
            if not df_mapped.empty:
                portfolio_df = df_mapped
                
                coin_ids_list = portfolio_df['id_koin'].unique().tolist()
                
                ids_string = ','.join(coin_ids_list)
                url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd'
                response = requests.get(url)
                price_data = response.json()
                current_prices = {key: value['usd'] for key, value in price_data.items()}

                portfolio_df['harga_terkini_usd'] = portfolio_df['id_koin'].map(current_prices)
                portfolio_df['modal_usd'] = portfolio_df['jumlah'] * portfolio_df['harga_beli_usd']
                portfolio_df['nilai_terkini_usd'] = portfolio_df['jumlah'] * portfolio_df['harga_terkini_usd']
                portfolio_df['pnl_usd'] = portfolio_df['nilai_terkini_usd'] - portfolio_df['modal_usd']
                
                summary_df = portfolio_df.groupby('id_koin').agg(
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
                st.error("Tidak ada data yang valid untuk ditampilkan setelah proses pembersihan.")

    except Exception as e:
        st.error(f"Terjadi error. Pastikan file yang diupload adalah CSV. Error: {e}")

else:
    st.info("Silakan upload file transaksi Anda untuk memulai.")
