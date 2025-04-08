import streamlit as st

from pages._menu import menu

st.set_page_config(
    page_title="Finance & Markets Demos | Chronulus",
    page_icon="🏠",
    initial_sidebar_state="auto"
)

menu()

st.title("Finance & Markets Demos")

st.markdown("""
#### Usage

1. Go to [Settings](/Settings) and enter your `CHRONULUS_API_KEY`
2. Select one of the demos from the sidebar:
    * [VC Regret Minimization](/VC_Regret_Min)
3. Enter the information about the match up that you would like to predict and click `Predict`.
5. [Visualize](/Visualize) and explore your Prediction Sets
""")
