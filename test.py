import streamlit as st
import pandas as pd


with st.sidebar:
    st.subheader("Выберите опцию") # заголовок меню
    direct_file_button = st.sidebar.button(label='Upload files for analysis')

if direct_file_button:
    upload_file = st.file_uploader('insert file')
    if upload_file is not None:
        bytes_data = upload_file.getvalue()
        st.write(bytes_data)
