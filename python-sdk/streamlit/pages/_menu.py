import os
import streamlit as st

entry = os.environ.get("ENTRY", st.secrets.to_dict().get("ENTRY"))


def menu():

    if entry and entry == 'fin':
        st.sidebar.page_link("fin_main.py", label="Home")
        st.sidebar.page_link("pages/RegretPrediction.py", label="Missed Opportunity Prediction")
        st.sidebar.page_link("pages/FinVisualize.py", label="Visualize Prediction Sets")

    if entry and entry == 'sports':
        st.sidebar.page_link("sports_main.py", label="Home")
        st.sidebar.page_link("pages/Tennis.py", label="Tennis")
        st.sidebar.page_link("pages/Basketball.py", label="Basketball")
        st.sidebar.page_link("pages/Visualize.py", label="Visualize Prediction Sets")

    st.sidebar.page_link("pages/FAQs.py", label="FAQs")
    st.sidebar.page_link("pages/Settings.py", label="Settings")
