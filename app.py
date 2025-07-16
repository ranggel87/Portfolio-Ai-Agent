import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Dashboard Portofolio Kripto Fleksibel ⚙️")

uploaded_file = st.file_uploader("Pilih file data transaksi CSV dari exchange manapun", type="csv")

if uploaded_file is not None:
    try:
        # Baca file CSV yang diunggah
        df = pd.read_csv(uploaded_file)
        
        st.header("1. Pemetaan Kolom")
        st.write("Beri tahu kami kolom mana yang harus digunakan dari file Anda.")
        
        # Ambil semua nama kolom dari file
        column_headers = df.columns.tolist()
        
        # Buat 3 kolom untuk pilihan dropdown
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Dropdown untuk memilih kolom ID Koin
            # PENTING: ID koin harus sesuai dengan API CoinGecko (e.g., 'bitcoin', 'ethereum')
            selected_id_col = st.selectbox("Pilih kolom untuk NAMA KOIN:", column_headers)
        
        with col2:
            # Dropdown untuk memilih kolom Jumlah
            selected_jumlah_col = st.selectbox("Pilih kolom untuk JUMLAH:", column_headers)
            
        with col3:
            # Dropdown untuk memilih kolom Harga Beli
            selected_harga_col = st.selectbox("Pilih kolom untuk HARGA BELI:", column_headers)

        st.info("Pastikan kolom 'NAMA KOIN' berisi ID yang dikenali CoinGecko (contoh: 'bitcoin', bukan 'BTC').")

        # Tombol untuk memulai proses setelah pemetaan selesai
        if st.button("Proses Data & Tampilkan Dashboard"):
            # Buat DataFrame baru dengan nama kolom standar
            try:
                portfolio_df = pd.DataFrame({
                    'id_koin': df[selected_id_col],
                    'jumlah': df[selected_jumlah_col],
                    'harga_beli_usd': df[selected_harga_col]
                })

                # Hapus baris dimana ada data yang kosong
                portfolio_df.dropna(inplace=True)
                
                # --- Sisa skrip sama persis seperti sebelumnya ---
                coin_ids_list = portfolio_df['id_koin'].unique().tolist()
                
                ids_string = ','.join(coin_ids_list)
                url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd'
                response = requests.get(url)
                price_data = response.json()
                current_prices = {key: value['usd'] for key, value in price_data.items()}

                portfolio_df['harga_terkini_usd'] = portfolio_df['id_koin'].map(current_prices)
                portfolio_df['modal_usd'] = portfolio_df['jumlah'].astype(float) * portfolio_df['harga_beli_usd'].astype(float)
                portfolio_df['nilai_terkini_usd'] = portfolio_df['jumlah'].astype(float) * portfolio_df['harga_terkini_usd'].astype(float)
                portfolio_df['pnl_usd'] = portfolio_df['nilai_terkini_usd'] - portfolio_df['modal_usd']
                
                summary_df = portfolio_df.groupby('id_koin').agg(
                    modal_usd=('modal_usd', 'sum'),
                    nilai_terkini_usd=('nilai_terkini_usd', 'sum'),
                    pnl_usd=('pnl_usd', 'sum')
                ).reset_index()

                st.header("2. Ringkasan Kinerja")
                # ... (Sisa kode untuk menampilkan KPI dan Grafik sama persis)
                total_modal = summary_df['modal_usd'].sum()
                total_nilai_terkini = summary_df['nilai_terkini_usd'].sum()
                total_pnl = summary_df['pnl_usd'].sum()
                total_pnl_percent = (total_pnl / total_modal) * 100 if total_modal != 0 else 0

                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("Total Modal", f"${total_modal:,.2f}")
                kpi2.metric("Nilai Saat Ini", f"${total_nilai_terkini:,.2f}")
                kpi3.metric("Total PnL", f"${total_pnl:,.2f}", f"{total_pnl_percent:.2f}%")
                
                st.markdown("---")

                st.header("3. Analisis Aset")
                chart1, chart2 = st.columns(2)
                with chart1:
                    st.subheader("Komposisi Portofolio")
                    fig1, ax1 = plt.subplots()
                    ax1.pie(summary_df['nilai_terkini_usd'], labels=summary_df['id_koin'], autopct='%1.1f%%', startangle=90)
                    ax1.axis('equal')
                    st.pyplot(fig1)

                with chart2:
                    st.subheader("Profit & Loss (PnL) per Aset")
                    fig2, ax2 = plt.subplots()
                    pnl_sorted = summary_df.sort_values('pnl_usd', ascending=False)
                    colors = ['#4CAF50' if x >= 0 else '#F44336' for x in pnl_sorted['pnl_usd']]
                    ax2.bar(pnl_sorted['id_koin'], pnl_sorted['pnl_usd'], color=colors)
                    plt.xticks(rotation=45)
                    st.pyplot(fig2)

            except Exception as e:
                st.error(f"Gagal memproses data setelah pemetaan. Pastikan kolom yang dipilih sesuai. Error: {e}")

    except Exception as e:
        st.error(f"Tidak dapat membaca file CSV. Error: {e}")
else:
    st.info("Silakan upload file transaksi Anda untuk memulai.")
