import streamlit as st


def menu():
    st.sidebar.page_link("main.py", label="Home")
    st.sidebar.page_link("pages/Tennis.py", label="Tennis")
    st.sidebar.page_link("pages/Visualize.py", label="Visualize Prediction Sets")
