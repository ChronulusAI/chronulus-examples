import streamlit as st
from pages._sports_menu import menu

st.set_page_config(
    page_title="Chronulus Demos",
    page_icon="🏠",
    initial_sidebar_state="auto"
)

menu()

st.title("Sports Prediction Demos")

st.markdown("""
#### Usage

1. Go to [Settings](/Settings) and enter your `CHRONULUS_API_KEY`
2. Select one of the demos from the sidebar:
    * [Basketball](/Basketball)
    * [Tennis](/Tennis)
3. Enter the information about the match up that you would like to predict and click `Predict`.
4. Toggle `Reverse Order of Sides` and `Predict` again to collect a de-biasing framing.
5. [Visualize](/Visualized) and explore your Original and Reversed Prediction Sets
""")
