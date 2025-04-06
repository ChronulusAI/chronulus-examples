import os

from chronulus.estimator.binary_predictor import BinaryPredictor

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy import stats
import json

import streamlit as st
from streamlit_cookies_controller import CookieController
from pages._menu import menu

st.set_page_config(
    page_title="Chronulus | Tennis Prediction",
    page_icon=":gear:",
    layout="centered",
    initial_sidebar_state="auto"
)

menu()
controller = CookieController()

st.subheader("Chronulus Demo Settings")
st.markdown("""
This app requires a `CHRONULUS_API_KEY` along with an active subscription. 

To get yours, login to [console.chronulus.com](https://console.chronulus.com) and 
click [Get API Keys](https://console.chronulus.com/api-keys). 

If you have not subscribed, you can sign-up or manage your subscription on the 
[Billing](https://console.chronulus.com/billing) page.

""")

if os.environ.get('CHRONULUS_API_KEY'):
    controller.set("CHRONULUS_API_KEY", os.environ.get('CHRONULUS_API_KEY'))

api_key_cookie = controller.get('CHRONULUS_API_KEY')


api_key = st.text_input(
    label="Chronulus API Key",
    value=api_key_cookie if api_key_cookie else "",
    placeholder="Enter your Chronulus API Key here"
)

agent = None
if api_key:
    controller.set('CHRONULUS_API_KEY', api_key)
