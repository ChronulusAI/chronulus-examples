import streamlit as st
from pages._menu import menu

st.set_page_config(
    page_title="Chronulus Demos",
    page_icon="🏠",
    initial_sidebar_state="auto"
)

menu()

st.title("Demos")
st.write("Use the left sidebar menu to select your demo.")