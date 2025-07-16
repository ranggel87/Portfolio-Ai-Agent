import streamlit as st
import pandas as pd

st.header("Demonstrasi st.file_uploader")

# Membuat uploader yang bisa menerima file CSV atau PNG
my_file = st.file_uploader(
    "Upload file CSV atau Gambar (PNG/JPG)", 
    type=["csv", "png", "jpg"]
)

# Cek apakah file sudah di-upload
if my_file is not None:
    # Tampilkan informasi dasar tentang file
    st.write("--- Informasi File ---")
    st.write("Nama File:", my_file.name)
    st.write("Jenis File:", my_file.type)
    st.write("Ukuran File:", my_file.size, "bytes")
    
    # Lakukan sesuatu berdasarkan jenis filenya
    if 'csv' in my_file.type:
        st.write("--- Isi File CSV ---")
        df = pd.read_csv(my_file)
        st.dataframe(df)
    elif 'image' in my_file.type:
        st.write("--- Tampilan Gambar ---")
        st.image(my_file)
else:
    st.info("Menunggu file untuk di-upload...")
