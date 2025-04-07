import streamlit as st


def menu():
    st.sidebar.page_link("sports_main.py", label="Home")
    st.sidebar.page_link("pages/Tennis.py", label="Tennis")
    st.sidebar.page_link("pages/Basketball.py", label="Basketball")
    st.sidebar.page_link("pages/Visualize.py", label="Visualize Prediction Sets")
    st.sidebar.page_link("pages/Settings.py", label="Settings")