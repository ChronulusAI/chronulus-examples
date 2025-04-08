import os
import streamlit as st

entry = os.environ.get("ENTRY", st.secrets.to_dict().get("ENTRY"))

def menu():

    if entry and entry == 'fin':
        st.sidebar.page_link("fin_main.py", label="Home")
        st.sidebar.page_link("pages/VC_Regret_Min.py", label="Missed Opportunity Prediction")
        st.sidebar.page_link("pages/FinVisualize.py", label="Visualize Prediction Sets")
        st.sidebar.page_link("pages/Settings.py", label="Settings")

    if entry and entry == 'sports':
        st.sidebar.page_link("sports_main.py", label="Home")
        st.sidebar.page_link("pages/Tennis.py", label="Tennis")
        st.sidebar.page_link("pages/Basketball.py", label="Basketball")
        st.sidebar.page_link("pages/Visualize.py", label="Visualize Prediction Sets")
        st.sidebar.page_link("pages/Settings.py", label="Settings")
